# NOAH Knowledge Graph — PostgreSQL to Neo4j Conversion Bot

**NYU SPS MASY Capstone · Spring 2026 · Advisor: Dr. Andres Fortino · Sponsor: The Digital Forge Lab**

An automated tool that converts the NOAH (Naturally Occurring Affordable Housing) PostgreSQL database into a Neo4j knowledge graph, with a natural-language query interface for non-technical users.

---

## Results at a Glance

| Metric | Result |
|---|---|
| Housing projects migrated | **8,604** (100% of source rows) |
| Graph nodes created | **11,360** across 5 labels (incl. 177 `Demographic`) |
| Graph relationships created | **~17,080** across 6 types (incl. 177 `HAS_DEMOGRAPHICS`) |
| Migration relationship integrity | **100%** of resolvable FKs (35 `LOCATED_IN_ZIP` rows legitimately skipped: postcode outside NYC ZIP set; documented in `outputs/audit_report.json`) |
| Text2Cypher accuracy | **95%** (19/20 benchmark questions) |
| Code complexity reduction | **20% fewer lines** than equivalent SQL (avg across 10 queries) |
| Neo4j faster on multi-hop / variable-length paths | Pre-computed `NEIGHBORS`, `IN_CENSUS_TRACT` edges avoid recursive CTEs — see Benchmarks table below for per-category breakdown |

---

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 14+ with PostGIS (source database)
- Neo4j 5.x (target database)
- An Anthropic API key (for Text2Cypher)

### Installation

```bash
git clone <repo-url>
cd noah_postgres_to_neo4j
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Create your config files:

```bash
cp config/config.example.yaml config/config.yaml
# Edit config/config.yaml with your PostgreSQL and Neo4j credentials
```

### Run the Streamlit UI

```bash
streamlit run app/Home.py --server.port 8505
```

Then open http://localhost:8505 in your browser. Enter your Anthropic API key in the sidebar and start querying in plain English.

### Run the CLI

```bash
python main.py --help          # Show all commands
python main.py analyze         # Introspect PostgreSQL schema
python main.py status          # Check migration status
python main.py migrate         # Run full migration pipeline
python main.py audit           # Post-migration integrity audit
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     NOAH Conversion Bot                             │
│                                                                     │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────────────────┐  │
│  │   Schema    │   │   Mapping    │   │    Data Migrator        │  │
│  │  Analyzer   │──▶│   Engine     │──▶│  (ETL Pipeline)         │  │
│  │             │   │              │   │                         │  │
│  │ • table scan│   │ • FK→edges   │   │ • MERGE nodes           │  │
│  │ • FK detect │   │ • PK→nodeids │   │ • CREATE rels           │  │
│  │ • type map  │   │ • col→props  │   │ • batch commit          │  │
│  └─────────────┘   └──────────────┘   └─────────────────────────┘  │
│         │                                          │                │
│         ▼                                          ▼                │
│  ┌─────────────┐                       ┌──────────────────────────┐ │
│  │  LLM Schema │                       │  Post-Migration Audit    │ │
│  │ Interpreter │                       │                          │ │
│  │             │                       │ • node counts match      │ │
│  │ • enriches  │                       │ • FK integrity check     │ │
│  │   mapping   │                       │ • orphan detection       │ │
│  │   with AI   │                       │ • property coverage      │ │
│  └─────────────┘                       └──────────────────────────┘ │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │               Text2Cypher Interface                         │    │
│  │                                                             │    │
│  │  Natural English → Schema Context → LLM → Cypher → Neo4j   │    │
│  │  Providers: Claude (Anthropic), GPT-4 (OpenAI)             │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
        │                                          │
        ▼                                          ▼
 ┌─────────────┐                         ┌─────────────────┐
 │ PostgreSQL  │                         │     Neo4j       │
 │  (NOAH DB)  │                         │  Knowledge Graph│
 │  8,604 rows │                         │  11,183 nodes   │
 └─────────────┘                         └─────────────────┘
```

### Graph Model

**Nodes (5 labels)**

| Label | Count | Merge Key | Description |
|---|---|---|---|
| `HousingProject` | 8,604 | `db_id` | Affordable housing development |
| `ZipCode` | 177 | `zip_code` | NYC ZIP/ZCTA geographic unit |
| `Demographic` | 177 | `zip_code` | ACS 2022 population / age / tenure (B01003, B01002, B25003) |
| `AffordabilityAnalysis` | 177 | `zip_code` | ZIP-level rent burden + income |
| `RentBurden` | 2,225 | `geo_id` | Census-tract-level rent burden |

**Relationships (6 types)**

| Type | From → To | Properties | Source |
|---|---|---|---|
| `LOCATED_IN_ZIP` | HousingProject → ZipCode | — | FK: postcode → zip_code |
| `HAS_DEMOGRAPHICS` | ZipCode → Demographic | — | FK: zip_code → zip_code (matches original spec schema) |
| `HAS_AFFORDABILITY_DATA` | ZipCode → AffordabilityAnalysis | — | FK: zip_code → zip_code |
| `IN_CENSUS_TRACT` | HousingProject → RentBurden | — | Computed: borough+census_tract → geo_id |
| `NEIGHBORS` | ZipCode ↔ ZipCode | `distance_km`, `is_adjacent` | Spatial: ST_Touches |
| `CONTAINS_TRACT` | ZipCode → RentBurden | `overlap_area_km2`, `tract_coverage_ratio` | Spatial intersection |

---

## Features

### 1. Automated Schema Analysis

The schema analyzer introspects the PostgreSQL database and produces a structured report:
- Table discovery and row counts
- Primary key and foreign key detection
- Data type mapping (PostgreSQL → Neo4j property types)
- PostGIS geometry column identification

### 2. Config-Driven Mapping Engine

Mapping rules are defined in `config/mapping_rules.yaml`, following De Virgilio's formal conversion framework:
- Tables with meaningful identity → Node labels
- Foreign keys → Directed relationships
- Join/crosswalk tables → Direct relationships (no intermediate node)
- Spatial columns → Extracted lat/lon/area properties

### 3. LLM Schema Interpreter

An AI-powered pass enriches the base mapping:
- Suggests human-readable relationship names (e.g., `LOCATED_IN_ZIP` vs `FK_postcode`)
- Identifies semantically meaningful join patterns
- Recommends which columns to include vs. exclude as properties

### 4. Data Migration Engine

- Batch MERGE operations (1,000 rows/batch) for idempotent re-runs
- Transaction rollback on failure
- Progress tracking with tqdm

### 5. Post-Migration Audit

Automated integrity checks after migration:
- Node count matches source table row counts
- All foreign-key relationships resolved (no orphaned nodes)
- Property coverage ≥ 95% (no unexpected nulls)
- Spatial relationship completeness

### 6. Text2Cypher Interface

Plain-English querying of the graph:
- **95% accuracy** on 20-question benchmark (Easy 100%, Medium 100%, Hard 86%)
- Schema-aware prompting — injects node labels, property names, relationship types
- Multi-provider: Anthropic Claude, OpenAI GPT-4
- Graceful error handling with retry logic

### 7. Streamlit Dashboard

Five-page web app:
- **Home** — Project overview, key metrics, live graph stats
- **Ask** — Natural-language query interface; auto bar chart; Explain panel (traversal diagram + LLM summary); CSV and GeoJSON export
- **Explore** — Cypher editor with 4 tabs: Query Editor, Graph View (pyvis network), Saved Queries, Schema Reference; CSV and GeoJSON export
- **Templates** — 5 parameterized query templates with dropdowns and sliders (no Cypher required)
- **Insights** — Pre-built visualizations: borough breakdown, rent burden distribution, income vs. burden scatter

### 8. GeoJSON Export

Any query result containing `center_lat` / `center_lon` columns can be exported as a GeoJSON FeatureCollection (`.geojson`) from both the Ask and Explore pages. Compatible with QGIS, Mapbox, Leaflet, and ArcGIS.

### 9. Educational Notebook

`notebooks/03_graph_vs_sql_tutorial.ipynb` — classroom-ready Jupyter notebook:
- SQL vs Cypher side-by-side comparisons for 4 query patterns
- Full benchmark visualization (8 queries, PG vs Neo4j)
- 3 graded lab exercises (easy/medium/hard) with answer keys and rubric
- Instructor notes with timing guide and assessment options

---

## Benchmarks

### Text2Cypher Accuracy

20 questions across 3 difficulty levels, graded on 4 criteria each (syntax OK, has results, count match, top-row match):

```
Easy   (Q1-6):  6/6  = 100%
Medium (Q7-13): 7/7  = 100%
Hard   (Q14-20): 6/7  =  86%
─────────────────────────────
Total:          19/20 =  95%   (spec target: >75%)
```

Only failure: Q19 — LLM omitted LIMIT clause, returning 100 rows vs expected 20.

### PostgreSQL vs Neo4j Performance

**10 queries** across 5 categories, 10 runs each (2 warmup). The benchmark is
intentionally balanced — PostgreSQL is genuinely excellent at flat queries
over indexed columns, while Neo4j wins the path-shaped queries. The goal is
to document *where each tool fits*, not to cherry-pick wins.

| Category | Queries | Representative workload | Expected winner |
|---|---|---|---|
| `simple` | Q1, Q2 | Single-table aggregation with filter | PostgreSQL |
| `1-hop` | Q3, Q4 | One FK join / one relationship hop | close; pre-computed edges flip to Neo4j |
| `2-hop` | Q5, Q6 | Two-table join / two-hop traversal | close |
| `neighbor` | Q7, Q8 | Spatial `ST_Touches` on-the-fly **vs** pre-computed `NEIGHBORS` edge | **Neo4j** |
| `var-path` | Q9, Q10 | Recursive CTE **vs** `-[:NEIGHBORS*1..2]-` / 4-label pattern | **Neo4j** |

Concrete timings regenerate each run via:

```bash
python scripts/performance_comparison.py --runs 10
# → outputs/performance_report.json (includes category_summary)
```

**Key findings (narrative for the report):**
- PostgreSQL wins simple aggregations — its B-tree indexes + low protocol overhead beat Neo4j at 8,604-row scale. This is the *expected* outcome of the baseline category.
- Neo4j wins path-shaped queries — pre-computed `NEIGHBORS`, `IN_CENSUS_TRACT`, and `HAS_DEMOGRAPHICS` edges eliminate the recursive self-JOINs and spatial computations that dominate the SQL plan.
- Average code reduction is **~20% fewer lines** in Cypher across all 10 queries; on variable-length paths (Q9) the recursive CTE is 15 lines vs. 4-line Cypher — a 75% reduction.
- The Neo4j advantage grows roughly linearly with hop depth and quadratically with graph density; at current scale it's visible on 3+ hops and on variable-length patterns.

---

## Project Structure

```
noah_postgres_to_neo4j/
├── app/                          # Streamlit dashboard
│   ├── Home.py                   # Landing page with metrics
│   ├── pages/
│   │   ├── 1_Ask.py              # Natural-language query page (+ GeoJSON export)
│   │   ├── 2_Explore.py          # Cypher editor, Graph View, Saved Queries, Schema
│   │   ├── 3_Templates.py        # Parameterized query templates
│   │   ├── 4_Insights.py         # Pre-built visualizations
│   │   └── 5_Settings.py         # API key management
│   └── utils/
│       ├── connection.py         # Neo4j driver wrapper
│       ├── explain.py            # Cypher → Graphviz DOT parser
│       ├── geojson_export.py     # GeoJSON FeatureCollection export
│       ├── saved_queries.py      # Saved query persistence
│       └── theme.py              # CSS theme injection
├── src/noah_converter/           # Core library
│   ├── schema_analyzer/          # PostgreSQL introspection
│   ├── mapping_engine/           # RDBMS → Graph mapping
│   │   ├── config.py             # MappingConfig dataclass
│   │   ├── mapper.py             # Main GenericMigrator class
│   │   ├── mapping_rules.py      # YAML rule loader
│   │   ├── models.py             # NodeSpec / RelSpec models
│   │   ├── cypher_generator.py   # MERGE/CREATE Cypher builder
│   │   └── spatial_handler.py    # PostGIS geometry extraction
│   ├── text2cypher/              # NL → Cypher translation
│   │   ├── translator.py         # Main Text2Cypher class
│   │   ├── schema_context.py     # Dynamic schema injection
│   │   └── providers/            # LLM provider adapters
│   └── utils/                    # Shared utilities
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── test_mapping_engine.py    # Mapping engine tests
├── scripts/                      # Standalone scripts
│   ├── docker_init/              # Ordered init for docker compose (01_bootstrap.sql)
│   ├── performance_comparison.py # PG vs Neo4j benchmark (10 queries, 5 categories)
│   ├── benchmark_text2cypher.py  # 20-question accuracy test
│   ├── fetch_acs_demographics.py # Refresh ACS 2022 CSV seed from Census API
│   ├── load_demographics.py      # Load zip_demographic table into PG
│   ├── load_demographics.sql     # Equivalent SQL loader (\copy, for psql)
│   ├── migrate_to_neo4j_with_spatial.py  # Spatial migration
│   └── precompute_spatial_relationships.sql
├── outputs/                      # Generated artifacts
│   ├── cypher/                   # Constraint + index scripts
│   ├── performance_report.json   # PG vs Neo4j results
│   └── benchmark_report.json     # Text2Cypher accuracy results
├── config/
│   ├── config.example.yaml       # Template — copy to config.yaml
│   └── mapping_rules.yaml        # Graph mapping rules
├── notebooks/                    # Educational Jupyter notebooks
├── docs/                         # Extended documentation
├── resources/                    # Reference materials
├── docker-compose.yml            # Docker deployment
├── Dockerfile.streamlit          # Streamlit container image
├── main.py                       # CLI entry point
└── requirements.txt
```

---

## Configuration

`config/config.yaml` (copy from `config.example.yaml`):

```yaml
postgresql:
  host: localhost
  port: 5432
  database: noah_db
  user: postgres
  password: your_password

neo4j:
  uri: bolt://localhost:7687
  user: neo4j
  password: your_password
  database: neo4j

llm:
  provider: anthropic          # anthropic | openai
  model: claude-sonnet-4-6     # or gpt-4o
  api_key: ${ANTHROPIC_API_KEY}  # or set OPENAI_API_KEY

migration:
  batch_size: 1000
  dry_run: false
```

---

## Deployment (Docker)

### Clean-environment quickstart

From a fresh clone with no services running:

```bash
# 1. Bring up PostgreSQL (+PostGIS) and Neo4j
docker compose up -d postgres neo4j

# 2. Wait ~20s for both to become healthy
docker compose ps
# Expect: noah-postgres (healthy), noah-neo4j (healthy)

# 3. Load ACS 2022 demographic data (Demographic nodes in the graph)
#    Needs Python env set up; fetches from the bundled CSV seed.
python scripts/load_demographics.py

# 4. Run the migration (uses config/mapping_rules.yaml by default)
python main.py migrate --clear

# 5. Audit — expect overall_status: PASS
python main.py audit
#    → outputs/audit_report.json (INFO-level note on any orphan FK rows)

# 6. Launch the full stack (builds the Streamlit image on first run)
docker compose up -d streamlit
open http://localhost:8501
```

### Services and ports

| Service | Image | Ports | Override env var |
|---|---|---|---|
| `postgres` | `postgis/postgis:15-3.3` | `5432 → 5432` | `POSTGRES_HOST_PORT` |
| `neo4j` | `neo4j:5.15.0` + APOC | `7474 → 7474`, `7687 → 7687` | `NEO4J_HTTP_PORT`, `NEO4J_BOLT_PORT` |
| `streamlit` | built from `Dockerfile.streamlit` | `8501 → 8501` | — |

### If you already run PostgreSQL locally

Homebrew's `postgresql` shadows the Docker container on port 5432. Either stop
the local service (`brew services stop postgresql@15`) or remap the Docker
host port:

```bash
POSTGRES_HOST_PORT=15432 docker compose up -d postgres neo4j
# then point your Python config at port 15432, or use a docker-compose.override.yml
```

### First-time initialization

On the first `docker compose up -d postgres`, the container auto-runs
`scripts/docker_init/01_bootstrap.sql`, which sources (in order):

1. `scripts/create_simple_schema.sql` — PostGIS + `housing_projects` schema
2. `scripts/load_sample_data.sql` — 20 sample projects across 4 boroughs
3. `scripts/create_mock_zip_shapes.sql` — 16 derived ZIP polygons
4. `scripts/precompute_spatial_relationships.sql` — centroids + neighbor edges

This produces a **minimum-viable** PG suitable for end-to-end smoke testing.
The full 8,604-row NOAH ingest + 2,225-row rent_burden + 177-row
zip_demographic dataset loads separately via `scripts/load_demographics.py`
and whichever ingestion path you follow for `housing_projects` (Socrata API,
CSV dump, etc. — see `docs/guides/DATA_SETUP.md`).

---

## Reproducing the Benchmark Results

```bash
# Text2Cypher accuracy (requires ANTHROPIC_API_KEY)
python scripts/benchmark_text2cypher.py
# → outputs/benchmark_report.json

# PostgreSQL vs Neo4j performance (requires both databases running)
python scripts/performance_comparison.py
# → outputs/performance_report.json
```

---

## Academic References

| Paper | Description |
|---|---|
| Zhao et al. (2023) — ArXiv:2310.01080 | Rel2Graph: automated KG construction from relational DBs |
| De Virgilio et al. (2013) — ACM GRADES | Formal RDBMS-to-graph conversion framework |
| Minder et al. (2024) — ArXiv:2406.04995 | Data2Neo: open-source Neo4j integration library |
| Ozsoy et al. (2024) — ArXiv:2412.10064 | Text2Cypher: NL querying of graph databases |

---

## Documentation

| Document | Description |
|---|---|
| `docs/CAPSTONE_REPORT.md` | Full capstone report (NYU SPS MASY format, ~4,000 words) |
| `docs/api/API_REFERENCE.md` | Public Python API reference for all modules |
| `docs/architecture/SYSTEM_ARCHITECTURE.md` | 6-stage pipeline, data flow, design decisions |
| `docs/guides/USER_GUIDE.md` | End-user guide (Ask, Explore, Templates pages) |
| `docs/guides/DEPLOYMENT.md` | Local, Docker, and classroom deployment |
| `notebooks/03_graph_vs_sql_tutorial.ipynb` | Educational notebook with exercises and answer keys |

---

## Related Projects

- [Chaoou Zhang's NOAH Dashboard](https://github.com/cz3275/urbanlab-noah-dashboard) — Source database (Phase 0)
- [Yue Yu's NOAH Implementation](https://github.com/Becky0713/NOAH) — Reference PostGIS implementation
- [NYC Open Data: NOAH Housing](https://data.cityofnewyork.us/Housing-Development/Affordable-Housing-Production-by-Building/hg8x-zxpr) — Primary data source (Socrata `hg8x-zxpr`)

---

**Student:** Zhen Yang · **Advisor:** Dr. Andres Fortino · **Program:** NYU SPS MASY · **Spring 2026**
