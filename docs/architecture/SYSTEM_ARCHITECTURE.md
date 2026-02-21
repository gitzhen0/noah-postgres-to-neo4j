# System Architecture

## Overview

The NOAH Conversion Bot is a six-stage automated pipeline that transforms a PostgreSQL/PostGIS relational database into a Neo4j property graph, then exposes the result through both a CLI and a Streamlit web application.

```
PostgreSQL (NOAH DB)
        │
        ▼
┌───────────────────┐
│  Stage 1          │
│  Schema Analyzer  │  ← introspects tables, PKs, FKs, data types
└───────────────────┘
        │ schema_report.json
        ▼
┌───────────────────┐
│  Stage 2          │
│  LLM Interpreter  │  ← AI-enriched mapping suggestions
└───────────────────┘
        │ enriched_mapping.json
        ▼
┌───────────────────┐
│  Stage 3          │
│  Mapping Engine   │  ← applies mapping_rules.yaml
└───────────────────┘
        │ NodeSpec[], RelSpec[]
        ▼
┌───────────────────┐
│  Stage 4          │
│  Cypher Generator │  ← emits MERGE / CREATE Cypher
└───────────────────┘
        │ batched Cypher
        ▼
┌───────────────────┐
│  Stage 5          │
│  Data Migrator    │  ← executes against Neo4j, batch 1000
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  Stage 6          │
│  Post-Audit       │  ← node counts, FK integrity, property coverage
└───────────────────┘
        │
        ▼
     Neo4j KG
        │
        ▼
┌───────────────────┐
│  Text2Cypher      │  ← English → Cypher via LLM + schema context
└───────────────────┘
        │
        ▼
  Streamlit UI
```

---

## Stage 1: Schema Analyzer (`src/noah_converter/schema_analyzer/`)

**Input:** PostgreSQL connection credentials
**Output:** `schema_report.json`

Responsibilities:
- `information_schema.tables` → discover all tables
- `information_schema.columns` → data types, nullability
- `information_schema.table_constraints` + `key_column_usage` → primary and foreign keys
- PostGIS `geometry_columns` → identify spatial columns and SRID
- Row count estimation via `pg_stat_user_tables`

The schema report is a JSON document with one entry per table, containing columns, constraints, and estimated row counts. This feeds into both the LLM Interpreter and the Mapping Engine.

---

## Stage 2: LLM Schema Interpreter (`src/noah_converter/mapping_engine/`)

**Input:** `schema_report.json`
**Output:** Enriched mapping suggestions

Uses a large language model (Claude Sonnet or GPT-4) to:
- Suggest semantic relationship names from FK column names (e.g., `postcode → LOCATED_IN_ZIP`)
- Identify join/bridge tables that should become direct relationships
- Recommend which string columns encode categorical vs. free-text data
- Flag columns that are likely foreign keys even without explicit constraints

This stage is advisory: the suggestions are merged with the authoritative `config/mapping_rules.yaml` rules.

---

## Stage 3: Mapping Engine (`src/noah_converter/mapping_engine/`)

**Input:** `config/mapping_rules.yaml` + schema report
**Output:** `NodeSpec[]` and `RelSpec[]` lists

### NodeSpec

```python
@dataclass
class NodeSpec:
    label: str           # Neo4j node label, e.g. "HousingProject"
    source_table: str    # PostgreSQL table name
    merge_key: str       # Property used for MERGE (unique identifier)
    properties: list[str]  # Columns to include as properties
    computed: dict       # Derived properties (e.g., center_lat from geom)
```

### RelSpec

```python
@dataclass
class RelSpec:
    rel_type: str          # Relationship type, e.g. "LOCATED_IN_ZIP"
    from_label: str        # Source node label
    to_label: str          # Target node label
    from_key: str          # Property on source node
    to_key: str            # Property on target node
    properties: list[str]  # Optional relationship properties
```

### Conversion Patterns (De Virgilio Framework)

| Relational Pattern | Graph Pattern |
|---|---|
| Table with PK | Node label |
| Row | Individual node |
| Column | Node property |
| Foreign key | Directed relationship |
| Join table (2 FKs) | Direct relationship between endpoint nodes |
| Spatial column (PostGIS) | Extracted lat/lon/area properties |

---

## Stage 4: Cypher Generator (`src/noah_converter/mapping_engine/cypher_generator.py`)

**Input:** `NodeSpec[]`, source data rows
**Output:** Cypher `MERGE` / `CREATE` statements

For nodes:
```cypher
MERGE (n:HousingProject {db_id: $db_id})
SET n += {project_name: $project_name, borough: $borough, total_units: $total_units, ...}
```

For relationships:
```cypher
MATCH (a:HousingProject {db_id: $from_id})
MATCH (b:ZipCode {zip_code: $to_id})
MERGE (a)-[:LOCATED_IN_ZIP]->(b)
```

Key design decisions:
- `MERGE` (not `CREATE`) makes the pipeline idempotent — re-runs are safe
- Batching at 1,000 rows reduces round-trips and Neo4j lock contention
- Parameterized queries prevent Cypher injection

---

## Stage 5: Data Migrator (`src/noah_converter/mapping_engine/mapper.py`)

**Input:** NodeSpec[], RelSpec[], database connections
**Output:** Populated Neo4j graph

`GenericMigrator.migrate()` sequence:
1. Create constraints and indexes (from `outputs/cypher/01_create_constraints.cypher`)
2. For each NodeSpec: fetch all rows from PostgreSQL, batch-MERGE into Neo4j
3. For each RelSpec: fetch join pairs from PostgreSQL, batch-MERGE relationships
4. Spatial relationships: run `NEIGHBORS` and `CONTAINS_TRACT` from precomputed SQL table

Progress is tracked with `tqdm`. The migrator logs per-batch success/failure counts.

---

## Stage 6: Post-Migration Audit

**Input:** Both database connections
**Output:** Audit report (pass/fail per check)

Checks:
1. **Node count parity** — `COUNT(*)` in PG matches `MATCH (n:Label) RETURN count(n)` in Neo4j
2. **Relationship count** — expected rel counts from FK sizes
3. **Orphan detection** — `MATCH (n) WHERE NOT (n)--() RETURN count(n)` should be 0 for required relationships
4. **Property coverage** — fraction of non-null properties ≥ threshold (default 95%)
5. **Sample spot-check** — random 10 rows compared property-by-property

---

## Text2Cypher (`src/noah_converter/text2cypher/`)

### Request Flow

```
User English question
        │
        ▼
SchemaContext.build_prompt()
  ├── Node labels + properties
  ├── Relationship types + directions
  └── Example Cypher patterns
        │
        ▼
LLM API (Claude / GPT-4)
        │ raw Cypher string
        ▼
Cypher validation (syntax check)
        │
        ▼
Neo4j execution
        │
        ▼
Result rows → JSON
```

### SchemaContext

Dynamically builds the system prompt from the live graph schema:
- Calls `CALL db.labels()`, `CALL db.relationshipTypes()`, `CALL db.propertyKeys()`
- Injects concrete examples to ground the LLM

### Provider Abstraction

```python
class LLMProvider(Protocol):
    def translate(self, question: str, schema_context: str) -> str: ...

class AnthropicProvider:  # uses claude-sonnet-4-6
    ...

class OpenAIProvider:     # uses gpt-4o
    ...
```

---

## Streamlit Dashboard (`app/`)

Three pages:

| Page | File | Purpose |
|---|---|---|
| Home | `app/Home.py` | Project overview, live Neo4j metrics, pipeline diagram |
| Ask | `app/pages/1_Ask.py` | NL query → Cypher → results table |
| Explore | `app/pages/2_Explore.py` | Raw Cypher editor + schema reference |

**State management** (Streamlit session_state):
- `ask_question` — persists the question text across reruns
- `_result` — stores last query result (rows, elapsed, error)
- `cypher_editor` — persists Cypher text across Load/Run clicks

**Connection** (`app/utils/connection.py`):
- Reads Neo4j credentials from `st.secrets` or environment variables
- Returns results as `list[dict]` — Streamlit-friendly

---

## Data Flow Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│ Source: PostgreSQL / PostGIS                                           │
│                                                                        │
│  housing_projects (8,604) ──────────────────────────────────────────┐ │
│  zip_shapes       (177)   ──────────────────────────────────────────┤ │
│  noah_affordability_analysis (177) ─────────────────────────────────┤ │
│  rent_burden      (180)   ──────────────────────────────────────────┤ │
│  zip_tract_crosswalk  (join table) ─────────────────────────────────┘ │
└──────────────────────────────────────────────┬─────────────────────────┘
                                               │ ETL (GenericMigrator)
                                               ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Target: Neo4j Knowledge Graph                                          │
│                                                                        │
│  (HousingProject) ──[LOCATED_IN_ZIP]──▶ (ZipCode)                     │
│  (HousingProject) ──[IN_CENSUS_TRACT]──▶ (RentBurden)                 │
│  (ZipCode) ────────[HAS_AFFORDABILITY_DATA]──▶ (AffordabilityAnalysis) │
│  (ZipCode) ────────[NEIGHBORS]─────────── (ZipCode)  [undirected]      │
│  (ZipCode) ────────[CONTAINS_TRACT]────▶ (RentBurden)                 │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Concurrency and Scalability Notes

- Current target: 8,604 housing projects — fits in single Neo4j transaction chain
- Batch size of 1,000 is conservative; can increase to 5,000 for datasets > 100K rows
- For millions of nodes, replace Python-mediated migration with `neo4j-admin import` (bulk CSV load, ~10× faster)
- Text2Cypher latency is LLM-bound (~2-5 seconds per query); cache common questions with Redis

---

*Document version: 1.0 · Spring 2026*
