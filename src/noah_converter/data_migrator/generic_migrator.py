"""
Generic Config-Driven Migrator: PostgreSQL → Neo4j

Reads migration rules from a GraphSchema (loaded from mapping_rules.yaml) and
executes the full migration without any hardcoded table or column names.

Supports three relationship source types:
  FOREIGN_KEY  – uses from_id_column / to_id_column to build a SQL pair query
  COMPUTED     – runs computation_query (must return from_id, to_id columns)
  SPATIAL      – same as COMPUTED
"""

import math
from datetime import date
from typing import Any, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from neo4j import GraphDatabase
from loguru import logger

from noah_converter.mapping_engine.models import (
    GraphSchema,
    NodeType,
    RelationshipType,
    RelationshipSourceType,
)


# ─────────────────────────────────────────────────────────────
# Helpers (shared with hardcoded migrator)
# ─────────────────────────────────────────────────────────────

def _clean(val: Any) -> Any:
    """Convert Python types to Neo4j-safe values."""
    if val is None:
        return None
    if isinstance(val, date):
        return val.isoformat()
    if hasattr(val, "__float__"):          # Decimal → float
        f = float(val)
        return None if math.isnan(f) or math.isinf(f) else f
    return val


def _row_to_props(row: dict, exclude: Optional[set] = None) -> dict:
    """Convert a RealDictRow to a clean props dict, skipping nulls."""
    exclude = exclude or set()
    return {
        k: _clean(v)
        for k, v in row.items()
        if k not in exclude and _clean(v) is not None
    }


def _batches(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i: i + size]


# ─────────────────────────────────────────────────────────────
# GenericMigrator
# ─────────────────────────────────────────────────────────────

class GenericMigrator:
    """
    Config-driven PostgreSQL → Neo4j migrator.

    Reads a GraphSchema (from mapping_rules.yaml) and migrates all nodes
    and relationships without any hardcoded logic.

    Usage:
        schema = MappingConfigLoader.load_graph_schema("config/mapping_rules.yaml")
        migrator = GenericMigrator(pg_dsn, neo4j_uri, neo4j_auth, schema)
        result = migrator.migrate_all(clear=True)
        migrator.close()
    """

    def __init__(
        self,
        pg_dsn: dict,
        neo4j_uri: str,
        neo4j_auth: tuple,
        schema: GraphSchema,
        batch_size: int = 500,
    ):
        self.pg_dsn = pg_dsn
        self.schema = schema
        self.batch_size = batch_size
        self.driver = GraphDatabase.driver(neo4j_uri, auth=neo4j_auth)
        self.driver.verify_connectivity()
        logger.info("GenericMigrator: connected to Neo4j")

    def close(self):
        self.driver.close()

    def _pg_cursor(self):
        conn = psycopg2.connect(**self.pg_dsn)
        return conn, conn.cursor(cursor_factory=RealDictCursor)

    def _run(self, cypher: str, params: dict = None):
        with self.driver.session() as s:
            result = s.run(cypher, params or {})
            return result.consume().counters

    # ── Schema setup ────────────────────────────────────────────────────────

    def setup_schema(self):
        """Create UNIQUE constraints and indexes from schema definition."""
        logger.info("Setting up constraints and indexes...")
        for node in self.schema.nodes:
            for key in node.merge_keys:
                self._run(
                    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{node.label}) "
                    f"REQUIRE n.{key} IS UNIQUE"
                )
            for idx in node.indexes:
                self._run(
                    f"CREATE INDEX IF NOT EXISTS FOR (n:{node.label}) ON (n.{idx})"
                )
        logger.success("Schema ready")

    # ── Node migration ───────────────────────────────────────────────────────

    def _build_select(self, node: NodeType) -> str:
        """Build a SELECT statement from the node's property definitions.

        Handles:
          - transformation  → "EXPR AS name"
          - column alias    → "source_column AS name"
          - direct column   → "column_name"
        """
        parts = []
        for prop in node.properties:
            if prop.transformation:
                parts.append(f"{prop.transformation} AS {prop.name}")
            elif prop.source_column and prop.source_column != prop.name:
                parts.append(f"{prop.source_column} AS {prop.name}")
            else:
                col = prop.source_column or prop.name
                parts.append(col)
        return f"SELECT {', '.join(parts)} FROM {node.source_table}"

    def _build_merge_cypher(self, node: NodeType) -> str:
        merge_props = ", ".join(f"{k}: row.{k}" for k in node.merge_keys)
        return f"""
        UNWIND $rows AS row
        MERGE (n:{node.label} {{{merge_props}}})
        SET n += row
        """

    def migrate_node(self, node: NodeType) -> int:
        """Migrate all rows of one node type. Returns row count."""
        logger.info(f"Migrating {node.label} from {node.source_table}...")
        sql = self._build_select(node)

        conn, cur = self._pg_cursor()
        cur.execute(sql)
        rows = [_row_to_props(dict(r)) for r in cur.fetchall()]
        conn.close()

        cypher = self._build_merge_cypher(node)
        created = 0
        for batch in _batches(rows, self.batch_size):
            c = self._run(cypher, {"rows": batch})
            created += c.nodes_created
        logger.success(f"{node.label}: {len(rows)} rows → {created} nodes created/merged")
        return len(rows)

    # ── Relationship migration ───────────────────────────────────────────────

    def _get_node(self, label: str) -> NodeType:
        node = self.schema.get_node_by_label(label)
        if node is None:
            raise ValueError(f"Node label '{label}' not found in schema")
        return node

    def migrate_relationship(self, rel: RelationshipType) -> int:
        """Dispatch to the appropriate relationship migration method."""
        if rel.source_type == RelationshipSourceType.FOREIGN_KEY:
            return self._migrate_rel_fk(rel)
        else:
            return self._migrate_rel_computed(rel)

    def _migrate_rel_fk(self, rel: RelationshipType) -> int:
        """
        Foreign-key relationship.

        Requires rel.from_id_column and rel.to_id_column — the columns in
        rel.source_table whose values match the merge keys of from_label and
        to_label respectively.

        Example (LOCATED_IN):
            source_table:   housing_projects
            from_id_column: id       → HousingProject.db_id
            to_id_column:   postcode → ZipCode.zip_code
        """
        if not rel.from_id_column or not rel.to_id_column:
            raise ValueError(
                f"FK relationship '{rel.type}' requires from_id_column and "
                f"to_id_column in mapping_rules.yaml"
            )

        from_node = self._get_node(rel.from_label)
        to_node = self._get_node(rel.to_label)
        from_key = from_node.merge_keys[0]
        to_key = to_node.merge_keys[0]

        logger.info(f"Migrating {rel.type} relationships (FK)...")

        if rel.from_id_column == rel.to_id_column:
            sql = (
                f"SELECT {rel.from_id_column} AS from_id, "
                f"{rel.to_id_column} AS to_id "
                f"FROM {rel.source_table}"
            )
        else:
            sql = (
                f"SELECT {rel.from_id_column} AS from_id, "
                f"{rel.to_id_column} AS to_id "
                f"FROM {rel.source_table} "
                f"WHERE {rel.to_id_column} IS NOT NULL"
            )

        conn, cur = self._pg_cursor()
        cur.execute(sql)
        pairs = [{"from_id": r["from_id"], "to_id": r["to_id"]} for r in cur.fetchall()]
        conn.close()

        cypher = f"""
        UNWIND $rows AS row
        MATCH (a:{rel.from_label} {{{from_key}: row.from_id}})
        MATCH (b:{rel.to_label} {{{to_key}: row.to_id}})
        MERGE (a)-[r:{rel.type}]->(b)
        """

        total = 0
        for batch in _batches(pairs, self.batch_size):
            c = self._run(cypher, {"rows": batch})
            total += c.relationships_created
        logger.success(f"{rel.type}: {total} relationships created")
        return total

    def _migrate_rel_computed(self, rel: RelationshipType) -> int:
        """
        Computed or spatial relationship.

        computation_query must SELECT at minimum:
          - from_id  (value matching from_label's merge key)
          - to_id    (value matching to_label's merge key)
        Plus any relationship property columns declared in rel.properties.
        """
        if not rel.computation_query:
            raise ValueError(
                f"Computed relationship '{rel.type}' has no computation_query"
            )

        from_node = self._get_node(rel.from_label)
        to_node = self._get_node(rel.to_label)
        from_key = from_node.merge_keys[0]
        to_key = to_node.merge_keys[0]

        logger.info(f"Migrating {rel.type} relationships (computed)...")

        conn, cur = self._pg_cursor()
        cur.execute(rel.computation_query)
        raw_rows = [dict(r) for r in cur.fetchall()]
        conn.close()

        # Clean any Decimal/date values in property columns
        prop_names = [p.name for p in rel.properties]
        rows = []
        for r in raw_rows:
            cleaned = {"from_id": r["from_id"], "to_id": r["to_id"]}
            for p in prop_names:
                if p in r:
                    cleaned[p] = _clean(r[p])
            rows.append(cleaned)

        # Build SET clause for relationship properties
        set_clause = ""
        if prop_names:
            set_parts = [f"r.{p} = row.{p}" for p in prop_names]
            set_clause = "SET " + ", ".join(set_parts)

        # Undirected MERGE for bidirectional (e.g. NEIGHBORS)
        if rel.bidirectional:
            merge_pattern = f"(a)-[r:{rel.type}]-(b)"
        else:
            merge_pattern = f"(a)-[r:{rel.type}]->(b)"

        cypher = f"""
        UNWIND $rows AS row
        MATCH (a:{rel.from_label} {{{from_key}: row.from_id}})
        MATCH (b:{rel.to_label} {{{to_key}: row.to_id}})
        MERGE {merge_pattern}
        {set_clause}
        """

        total = 0
        for batch in _batches(rows, self.batch_size):
            c = self._run(cypher, {"rows": batch})
            total += c.relationships_created
        logger.success(f"{rel.type}: {total} relationships created")
        return total

    # ── Full migration ───────────────────────────────────────────────────────

    def migrate_all(self, clear: bool = False) -> dict:
        """Run the complete migration.

        Returns a dict with:
            {"nodes": {label: count}, "relationships": {type: count}}
        """
        if clear:
            logger.warning("Clearing Neo4j database...")
            self._run("MATCH (n) DETACH DELETE n")

        logger.info("=" * 55)
        logger.info("Generic PostgreSQL → Neo4j Migration")
        logger.info(
            f"Schema: {len(self.schema.nodes)} node types, "
            f"{len(self.schema.relationships)} relationship types"
        )
        logger.info("=" * 55)

        # Schema (constraints + indexes)
        self.setup_schema()

        # Nodes
        node_counts: dict = {}
        for node_type in self.schema.nodes:
            node_counts[node_type.label] = self.migrate_node(node_type)

        # Relationships
        rel_counts: dict = {}
        for rel in self.schema.relationships:
            rel_counts[rel.type] = self.migrate_relationship(rel)

        # Summary
        logger.info("=" * 55)
        logger.info("Migration complete!")
        logger.info(f"  Nodes total:         {sum(node_counts.values()):,}")
        for label, count in node_counts.items():
            logger.info(f"    {label:<30} {count:>6,}")
        logger.info(f"  Relationships total: {sum(rel_counts.values()):,}")
        for rel_type, count in rel_counts.items():
            logger.info(f"    {rel_type:<30} {count:>6,}")
        logger.info("=" * 55)

        return {"nodes": node_counts, "relationships": rel_counts}
