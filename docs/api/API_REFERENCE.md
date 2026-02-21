# API Reference

**noah-postgres-to-neo4j** — Automated RDBMS-to-Knowledge Graph Conversion Bot

This reference covers the public Python API for all major modules. Internal helpers (prefixed `_`) are excluded.

---

## Table of Contents

1. [Schema Analyzer](#1-schema-analyzer)
2. [Mapping Engine](#2-mapping-engine)
3. [Data Migrator](#3-data-migrator)
4. [Text2Cypher Translator](#4-text2cypher-translator)
5. [Connection Utilities](#5-connection-utilities)
6. [Streamlit Utilities](#6-streamlit-utilities)

---

## 1. Schema Analyzer

**Module:** `src/noah_converter/schema_analyzer/`

### `SchemaAnalyzer`

Introspects a PostgreSQL database and extracts table structures, primary keys, foreign keys, and indexes.

```python
from noah_converter.schema_analyzer.analyzer import SchemaAnalyzer
```

#### Constructor

```python
SchemaAnalyzer(
    pg_connection: PostgreSQLConnection,
    config: SchemaAnalyzerConfig,
)
```

| Parameter | Type | Description |
|---|---|---|
| `pg_connection` | `PostgreSQLConnection` | Active PostgreSQL connection |
| `config` | `SchemaAnalyzerConfig` | Analyzer settings (exclude patterns, etc.) |

#### Methods

| Method | Returns | Description |
|---|---|---|
| `analyze(schema="public")` | `Dict[str, Table]` | Run full schema analysis; returns table dict keyed by table name |

#### Example

```python
from noah_converter.utils.db_connection import PostgreSQLConnection
from noah_converter.utils.config import DatabaseConfig, SchemaAnalyzerConfig
from noah_converter.schema_analyzer.analyzer import SchemaAnalyzer

pg = PostgreSQLConnection(DatabaseConfig(host="localhost", database="noah_housing", ...))
config = SchemaAnalyzerConfig()
analyzer = SchemaAnalyzer(pg, config)
tables = analyzer.analyze()
print(f"Found {len(tables)} tables")
```

### Data Models

| Class | Key Fields | Description |
|---|---|---|
| `Table` | `name`, `columns`, `primary_key`, `foreign_keys`, `indexes`, `table_type` | Represents one PostgreSQL table |
| `Column` | `name`, `data_type`, `nullable`, `default` | Represents one column |
| `ForeignKey` | `column`, `ref_table`, `ref_column` | FK constraint |
| `TableType` | `REGULAR`, `JOIN`, `LOOKUP` | Enum used by mapping rules |

---

## 2. Mapping Engine

**Module:** `src/noah_converter/mapping_engine/`

### `MappingEngine`

Converts a `Dict[str, Table]` (from `SchemaAnalyzer`) into a `GraphSchema` defining Neo4j nodes and relationships.

```python
from noah_converter.mapping_engine.mapper import MappingEngine
```

#### Constructor

```python
MappingEngine(
    tables: Dict[str, Table],
    spatial_config: Optional[SpatialConfig] = None,
    config_file: Optional[str] = None,
)
```

| Parameter | Type | Description |
|---|---|---|
| `tables` | `Dict[str, Table]` | Output of `SchemaAnalyzer.analyze()` |
| `spatial_config` | `SpatialConfig` | Spatial handling options (centroids, WKT, bbox) |
| `config_file` | `str` | Path to YAML override file; if provided, auto-rules are skipped |

#### Methods

| Method | Returns | Description |
|---|---|---|
| `generate_graph_schema()` | `GraphSchema` | Build node specs and relationship specs from tables |
| `export_schema(output_path)` | `None` | Serialize `GraphSchema` to JSON file |
| `export_yaml_config(output_path)` | `None` | Serialize `GraphSchema` as a YAML mapping config |
| `get_summary()` | `Dict` | Statistics: node count, relationship count, spatial node count, etc. |

#### Example

```python
engine = MappingEngine(tables, config_file="config/mapping_rules.yaml")
schema = engine.generate_graph_schema()
print(engine.get_summary())
# {'total_nodes': 4, 'total_relationships': 5, 'spatial_nodes': 2, ...}

engine.export_schema("outputs/cypher/graph_schema.json")
engine.export_yaml_config("outputs/cypher/mapping_config.yaml")
```

### `SpatialConfig`

Controls how PostGIS geometry columns are handled during mapping.

```python
from noah_converter.mapping_engine.models import SpatialConfig

config = SpatialConfig(
    compute_centroids=True,      # Extract center_lat / center_lon
    preserve_wkt=False,          # Exclude WKT polygon strings
    preserve_geojson=False,      # Exclude GeoJSON strings
    compute_metrics=True,        # Compute area_km2
    compute_bbox=False,          # Skip bounding box
    use_neo4j_point=False,       # Use scalar floats, not neo4j.Point
    neighbors_threshold_km=0.1,  # Distance threshold for NEIGHBORS edges
)
```

### Data Models

| Class | Key Fields | Description |
|---|---|---|
| `GraphSchema` | `nodes: List[NodeSpec]`, `relationships: List[RelSpec]` | Full graph schema |
| `NodeSpec` | `label`, `source_table`, `primary_property`, `properties`, `merge_keys`, `has_geometry` | One node type |
| `RelSpec` | `type`, `from_label`, `to_label`, `source_type`, `from_column`, `to_column`, `properties` | One relationship type |
| `PropertySpec` | `name`, `type`, `nullable`, `source_column`, `transformation` | One node/relationship property |

---

## 3. Data Migrator

**Module:** `src/noah_converter/data_migrator/`

### `DataMigrator`

Executes the NOAH-specific ETL: reads from PostgreSQL, writes batched `UNWIND … MERGE` Cypher to Neo4j.

```python
from noah_converter.data_migrator.migrator import DataMigrator
```

#### Constructor

```python
DataMigrator(batch_size: int = 500)
```

Connects to the databases defined in module-level constants (`PG`, `NEO4J_URI`, `NEO4J_AUTH`).

#### Methods

| Method | Returns | Description |
|---|---|---|
| `setup_schema()` | `None` | Create uniqueness constraints and indexes |
| `migrate_zipcodes()` | `int` | Migrate `zip_shapes` → `:ZipCode` nodes |
| `migrate_affordability_zones()` | `int` | Migrate `noah_affordability_analysis` → `:AffordabilityAnalysis` nodes |
| `migrate_census_tracts()` | `int` | Migrate `rent_burden` → `:RentBurden` nodes |
| `migrate_housing_projects()` | `int` | Migrate `housing_projects` → `:HousingProject` nodes (8,604 rows, batched) |
| `migrate_has_affordability_data()` | `int` | Create `[:HAS_AFFORDABILITY_DATA]` edges |
| `migrate_located_in()` | `int` | Create `[:LOCATED_IN_ZIP]` edges via `postcode` FK |
| `migrate_in_census_tract()` | `int` | Create `[:IN_CENSUS_TRACT]` edges using borough-FIPS join key |
| `migrate_neighbors()` | `int` | Compute and create `[:NEIGHBORS]` edges via `ST_Touches` |
| `migrate_all(clear=False)` | `Dict` | Run full migration in correct order; returns counts dict |
| `close()` | `None` | Close Neo4j driver |

#### Return value of `migrate_all()`

```python
{
    "nodes": {
        "ZipCode": 177,
        "AffordabilityAnalysis": 177,
        "RentBurden": 2225,
        "HousingProject": 8604,
    },
    "relationships": {
        "HAS_AFFORDABILITY_DATA": 177,
        "LOCATED_IN_ZIP": 8527,
        "IN_CENSUS_TRACT": 6712,
        "NEIGHBORS": 432,
    },
}
```

#### Example

```python
migrator = DataMigrator(batch_size=500)
try:
    results = migrator.migrate_all(clear=False)
    print(f"Migrated {sum(results['nodes'].values())} nodes")
finally:
    migrator.close()
```

---

## 4. Text2Cypher Translator

**Module:** `src/noah_converter/text2cypher/`

### `Text2CypherTranslator`

Translates natural language questions into Cypher queries using a pluggable LLM provider, executes against Neo4j, and optionally generates an explanation.

```python
from noah_converter.text2cypher import Text2CypherTranslator
```

#### Constructor

```python
Text2CypherTranslator(
    neo4j_conn: Neo4jConnection,
    llm_provider: str,
    api_key: str,
    model: Optional[str] = None,
    **kwargs,
)
```

| Parameter | Type | Description |
|---|---|---|
| `neo4j_conn` | `Neo4jConnection` | Active Neo4j connection |
| `llm_provider` | `str` | `"claude"`, `"openai"`, or `"gemini"` |
| `api_key` | `str` | API key for the chosen provider |
| `model` | `str` | Model ID, e.g. `"claude-sonnet-4-6"` (optional, uses provider default) |

#### Methods

| Method | Returns | Description |
|---|---|---|
| `query(question, execute=True, explain=True)` | `Dict` | Translate, execute, and explain a natural language question |
| `get_schema_summary()` | `str` | Return a human-readable summary of the loaded Neo4j schema |
| `test_connection()` | `bool` | Verify Neo4j connectivity (returns `True` on success) |

#### `query()` return value

```python
{
    "question": "Which ZIP codes have the highest rent burden?",
    "cypher":   "MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis) ...",
    "results":  [{"zip_code": "10453", "rent_burden": 0.52}, ...],   # None if execute=False
    "explanation": "The five ZIP codes with the highest rent burden are ...",  # None if explain=False
    "error":    None,  # str if any step failed
}
```

#### LLM Providers

| Provider string | Class | Default model |
|---|---|---|
| `"claude"` | `ClaudeProvider` | `claude-sonnet-4-6` |
| `"openai"` | `OpenAIProvider` | `gpt-4o` |
| `"gemini"` | `GeminiProvider` | `gemini-1.5-pro` |

All providers implement `BaseLLMProvider`:

```python
class BaseLLMProvider:
    def generate_cypher(self, question: str, schema_context: str) -> str: ...
    def validate_cypher(self, cypher: str) -> bool: ...
    def explain_results(self, question: str, cypher: str, results: list) -> str: ...
```

#### Example

```python
from noah_converter.text2cypher import Text2CypherTranslator
from noah_converter.utils.db_connection import Neo4jConnection
from noah_converter.utils.config import Neo4jConfig

conn = Neo4jConnection(Neo4jConfig(uri="bolt://localhost:7687", ...))
translator = Text2CypherTranslator(
    neo4j_conn=conn,
    llm_provider="claude",
    api_key="sk-ant-...",
)

result = translator.query("How many housing projects are in each borough?")
if not result["error"]:
    print(result["cypher"])
    for row in result["results"]:
        print(row)
```

---

## 5. Connection Utilities

**Module:** `src/noah_converter/utils/db_connection.py`

### `PostgreSQLConnection`

```python
PostgreSQLConnection(config: DatabaseConfig)
```

| Method | Returns | Description |
|---|---|---|
| `engine` (property) | `sqlalchemy.Engine` | Lazy-initialized SQLAlchemy engine |
| `get_connection()` | `psycopg2 connection` | Raw psycopg2 connection |
| `execute_query(query, params=None)` | `list[dict]` | Execute SQL via SQLAlchemy and return rows as dicts |
| `execute_raw(query, fetch=True)` | `list` or `None` | Execute raw psycopg2 query |

### `Neo4jConnection`

```python
Neo4jConnection(config: Neo4jConfig)
```

| Method | Returns | Description |
|---|---|---|
| `driver` (property) | `neo4j.Driver` | Lazy-initialized Neo4j driver |
| `close()` | `None` | Close the driver connection |

### `DatabaseConfig` / `Neo4jConfig`

Configuration models (Pydantic `BaseSettings`):

```python
# DatabaseConfig
DatabaseConfig(
    host="localhost",
    port=5432,
    database="noah_housing",
    user="postgres",
    password="...",
)

# Neo4jConfig
Neo4jConfig(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="...",
)
```

Both read from environment variables (`.env` file) by default.

---

## 6. Streamlit Utilities

**Module:** `app/utils/`

### `run_query(cypher, params=None)` — `app/utils/connection.py`

Execute a Cypher query against the configured Neo4j database and return results as a list of dicts.

```python
from utils.connection import run_query

rows = run_query("MATCH (p:HousingProject) RETURN p.borough AS borough LIMIT 5")
# [{"borough": "Bronx"}, {"borough": "Manhattan"}, ...]
```

### `get_config()` — `app/utils/connection.py`

Return the active `AppConfig` (parsed from `.env` / environment variables).

### `cypher_to_dot(cypher)` — `app/utils/explain.py`

Parse Cypher `MATCH` patterns and return a Graphviz DOT string for path visualization, or `None` if no node–relationship–node patterns are found.

```python
from utils.explain import cypher_to_dot

dot = cypher_to_dot("MATCH (p:HousingProject)-[:LOCATED_IN_ZIP]->(z:ZipCode) RETURN p, z")
# Returns DOT string suitable for st.graphviz_chart()
```

### `list_saved()`, `save_query()`, `delete_query()` — `app/utils/saved_queries.py`

Persist named Cypher queries in `app/saved_queries.json`.

```python
from utils.saved_queries import list_saved, save_query, delete_query

save_query("My query", "MATCH (p:HousingProject) RETURN count(p)")
queries = list_saved()   # [{"name": "My query", "cypher": "...", "saved_at": "2026-02-20 ..."}]
delete_query("My query")
```

### `rows_to_geojson(rows, lat_col, lon_col, props_cols=None)` — `app/utils/geojson_export.py`

Convert a list of result dicts (containing latitude/longitude) to a GeoJSON `FeatureCollection` string.

```python
from utils.geojson_export import rows_to_geojson

geojson = rows_to_geojson(rows, lat_col="center_lat", lon_col="center_lon")
```

Returns `None` if no rows contain valid coordinates.

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `PG_HOST` | PostgreSQL host | `localhost` |
| `PG_PORT` | PostgreSQL port | `5432` |
| `PG_DATABASE` | PostgreSQL database name | `noah_housing` |
| `PG_USER` | PostgreSQL user | `postgres` |
| `PG_PASSWORD` | PostgreSQL password | *(required)* |
| `NEO4J_URI` | Neo4j Bolt URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | *(required)* |
| `ANTHROPIC_API_KEY` | Anthropic API key for Text2Cypher | *(required for Ask page)* |
| `OPENAI_API_KEY` | OpenAI API key (optional provider) | — |
| `GEMINI_API_KEY` | Google Gemini API key (optional provider) | — |

---

*API Reference v1.1 · Spring 2026*
