"""
NOAH Data Migrator: PostgreSQL → Neo4j

Migrates all NOAH tables to Neo4j graph structure:

Nodes:
  ZipCode          (177)   ← zip_shapes
  AffordabilityZone (177)  ← noah_affordability_analysis
  CensusTract      (2225)  ← rent_burden
  HousingProject   (8604)  ← housing_projects

Relationships:
  ZipCode -[HAS_AFFORDABILITY_DATA]-> AffordabilityZone
  ZipCode -[NEIGHBORS]-> ZipCode  (spatial adjacency)
  HousingProject -[LOCATED_IN]-> ZipCode
  HousingProject -[IN_CENSUS_TRACT]-> CensusTract
"""

import math
from datetime import date
from typing import Any, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from neo4j import GraphDatabase
from loguru import logger

PG = dict(host="localhost", port=5432, dbname="noah_housing",
          user="postgres", password="password123")
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "password123")

BATCH = 500   # rows per UNWIND batch

BOROUGH_TO_COUNTY = {
    "Manhattan": "36061",
    "Bronx": "36005",
    "Brooklyn": "36047",
    "Queens": "36081",
    "Staten Island": "36085",
}


# ─────────────────────────────────────────────────────────────
# Helpers
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
        yield items[i : i + size]


def pg_cursor():
    conn = psycopg2.connect(**PG)
    return conn, conn.cursor(cursor_factory=RealDictCursor)


# ─────────────────────────────────────────────────────────────
# Main Migrator
# ─────────────────────────────────────────────────────────────

class DataMigrator:
    def __init__(self, batch_size: int = BATCH):
        self.batch_size = batch_size
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
        self.driver.verify_connectivity()
        logger.info("Connected to Neo4j")

    def close(self):
        self.driver.close()

    def _run(self, cypher: str, params: dict = None):
        with self.driver.session() as s:
            result = s.run(cypher, params or {})
            return result.consume().counters

    def _run_batch(self, cypher: str, rows: list):
        counters_created = 0
        for batch in _batches(rows, self.batch_size):
            c = self._run(cypher, {"rows": batch})
            counters_created += c.nodes_created + c.relationships_created
        return counters_created

    # ── Schema setup ────────────────────────────────────────

    def setup_schema(self):
        logger.info("Setting up constraints and indexes...")
        stmts = [
            # Constraints
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:ZipCode) REQUIRE n.zip_code IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:HousingProject) REQUIRE n.db_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:CensusTract) REQUIRE n.geo_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:AffordabilityZone) REQUIRE n.zip_code IS UNIQUE",
            # Indexes
            "CREATE INDEX IF NOT EXISTS FOR (n:HousingProject) ON (n.project_id)",
            "CREATE INDEX IF NOT EXISTS FOR (n:HousingProject) ON (n.borough)",
            "CREATE INDEX IF NOT EXISTS FOR (n:HousingProject) ON (n.postcode)",
            "CREATE INDEX IF NOT EXISTS FOR (n:HousingProject) ON (n.total_units)",
            "CREATE INDEX IF NOT EXISTS FOR (n:ZipCode) ON (n.borough)",
            "CREATE INDEX IF NOT EXISTS FOR (n:CensusTract) ON (n.rent_burden_rate)",
            "CREATE INDEX IF NOT EXISTS FOR (n:AffordabilityZone) ON (n.median_income_usd)",
        ]
        for stmt in stmts:
            self._run(stmt)
        logger.success("Schema ready")

    # ── Node migrations ──────────────────────────────────────

    def migrate_zipcodes(self):
        logger.info("Migrating ZipCode nodes...")
        conn, cur = pg_cursor()
        cur.execute("""
            SELECT
                zip_code, borough,
                ST_Y(ST_Centroid(geom)) AS center_lat,
                ST_X(ST_Centroid(geom)) AS center_lon,
                ST_Area(geom::geography) / 1000000.0 AS area_km2
            FROM zip_shapes
            ORDER BY zip_code
        """)
        rows = [_row_to_props(dict(r)) for r in cur.fetchall()]
        conn.close()

        cypher = """
        UNWIND $rows AS row
        MERGE (z:ZipCode {zip_code: row.zip_code})
        SET z += row
        """
        n = self._run_batch(cypher, rows)
        logger.success(f"ZipCode: {len(rows)} nodes merged")
        return len(rows)

    def migrate_affordability_zones(self):
        logger.info("Migrating AffordabilityZone nodes...")
        conn, cur = pg_cursor()
        cur.execute("""
            SELECT zip_code, median_income_usd, rent_burden_rate,
                   severe_burden_rate, median_rent_usd, rent_to_income_ratio
            FROM noah_affordability_analysis
            ORDER BY zip_code
        """)
        rows = [_row_to_props(dict(r)) for r in cur.fetchall()]
        conn.close()

        cypher = """
        UNWIND $rows AS row
        MERGE (a:AffordabilityZone {zip_code: row.zip_code})
        SET a += row
        """
        self._run_batch(cypher, rows)
        logger.success(f"AffordabilityZone: {len(rows)} nodes merged")
        return len(rows)

    def migrate_census_tracts(self):
        logger.info("Migrating CensusTract nodes...")
        conn, cur = pg_cursor()
        cur.execute("""
            SELECT
                geo_id, tract_name, rent_burden_rate, severe_burden_rate,
                ST_Y(ST_Centroid(geometry)) AS center_lat,
                ST_X(ST_Centroid(geometry)) AS center_lon,
                ST_Area(geometry::geography) / 1000000.0 AS area_km2
            FROM rent_burden
            ORDER BY geo_id
        """)
        rows = [_row_to_props(dict(r)) for r in cur.fetchall()]
        conn.close()

        cypher = """
        UNWIND $rows AS row
        MERGE (t:CensusTract {geo_id: row.geo_id})
        SET t += row
        """
        self._run_batch(cypher, rows)
        logger.success(f"CensusTract: {len(rows)} nodes merged")
        return len(rows)

    def migrate_housing_projects(self):
        logger.info("Migrating HousingProject nodes (8604 rows, batched)...")
        conn, cur = pg_cursor()
        cur.execute("""
            SELECT
                id                          AS db_id,
                project_id, project_name, building_id,
                house_number, street_name, borough, postcode,
                bbl, bin, community_board, council_district,
                census_tract, neighborhood_tabulation_area,
                CAST(latitude AS float)     AS latitude,
                CAST(longitude AS float)    AS longitude,
                project_start_date, project_completion_date,
                building_completion_date,
                reporting_construction_type,
                extended_affordability_status,
                prevailing_wage_status,
                extremely_low_income_units, very_low_income_units,
                low_income_units, moderate_income_units, middle_income_units,
                other_income_units, studio_units,
                _1_br_units AS units_1br,
                _2_br_units AS units_2br,
                _3_br_units AS units_3br,
                _4_br_units AS units_4br,
                _5_br_units AS units_5br,
                _6_br_units AS units_6br,
                unknown_br_units,
                counted_rental_units, counted_homeownership_units,
                all_counted_units, total_units
            FROM housing_projects
            ORDER BY id
        """)
        rows = [_row_to_props(dict(r)) for r in cur.fetchall()]
        conn.close()

        cypher = """
        UNWIND $rows AS row
        MERGE (p:HousingProject {db_id: row.db_id})
        SET p += row
        """
        self._run_batch(cypher, rows)
        logger.success(f"HousingProject: {len(rows)} nodes merged")
        return len(rows)

    # ── Relationship migrations ──────────────────────────────

    def migrate_has_affordability_data(self):
        """ZipCode -[HAS_AFFORDABILITY_DATA]-> AffordabilityZone (1:1 on zip_code)"""
        logger.info("Migrating HAS_AFFORDABILITY_DATA relationships...")
        cypher = """
        MATCH (z:ZipCode)
        MATCH (a:AffordabilityZone {zip_code: z.zip_code})
        MERGE (z)-[:HAS_AFFORDABILITY_DATA]->(a)
        """
        c = self._run(cypher)
        n = c.relationships_created
        logger.success(f"HAS_AFFORDABILITY_DATA: {n} relationships created")
        return n

    def migrate_located_in(self):
        """HousingProject -[LOCATED_IN]-> ZipCode (via postcode)"""
        logger.info("Migrating LOCATED_IN relationships...")
        cypher = """
        MATCH (p:HousingProject)
        WHERE p.postcode IS NOT NULL
        MATCH (z:ZipCode {zip_code: p.postcode})
        MERGE (p)-[:LOCATED_IN]->(z)
        """
        c = self._run(cypher)
        n = c.relationships_created
        logger.success(f"LOCATED_IN: {n} relationships created")
        return n

    def migrate_in_census_tract(self):
        """HousingProject -[IN_CENSUS_TRACT]-> CensusTract
        Match: borough + census_tract → geo_id (state+county+tract×100)
        Match rate: ~78% of projects that have census_tract set.
        """
        logger.info("Migrating IN_CENSUS_TRACT relationships...")

        conn, cur = pg_cursor()
        cur.execute("""
            SELECT
                h.id AS db_id,
                CASE h.borough
                    WHEN 'Manhattan'    THEN '36061'
                    WHEN 'Bronx'        THEN '36005'
                    WHEN 'Brooklyn'     THEN '36047'
                    WHEN 'Queens'       THEN '36081'
                    WHEN 'Staten Island' THEN '36085'
                END || LPAD(
                    (CAST(h.census_tract AS numeric) * 100)::bigint::text,
                    6, '0'
                ) AS geo_id
            FROM housing_projects h
            JOIN rent_burden rb ON rb.geo_id = (
                CASE h.borough
                    WHEN 'Manhattan'    THEN '36061'
                    WHEN 'Bronx'        THEN '36005'
                    WHEN 'Brooklyn'     THEN '36047'
                    WHEN 'Queens'       THEN '36081'
                    WHEN 'Staten Island' THEN '36085'
                END || LPAD(
                    (CAST(h.census_tract AS numeric) * 100)::bigint::text,
                    6, '0'
                ))
            WHERE h.census_tract IS NOT NULL
              AND h.census_tract <> ''
              AND h.census_tract ~ '^[0-9]+(\\.[0-9]+)?$'
        """)
        pairs = [{"db_id": r["db_id"], "geo_id": r["geo_id"]} for r in cur.fetchall()]
        conn.close()

        cypher = """
        UNWIND $rows AS row
        MATCH (p:HousingProject {db_id: row.db_id})
        MATCH (t:CensusTract {geo_id: row.geo_id})
        MERGE (p)-[:IN_CENSUS_TRACT]->(t)
        """
        total = 0
        for batch in _batches(pairs, self.batch_size):
            c = self._run(cypher, {"rows": batch})
            total += c.relationships_created
        logger.success(f"IN_CENSUS_TRACT: {total} relationships created (from {len(pairs)} matched pairs)")
        return total

    def migrate_neighbors(self):
        """ZipCode -[NEIGHBORS {distance_km}]-> ZipCode (spatial adjacency)"""
        logger.info("Computing ZIP spatial adjacency (ST_Touches / ST_Intersects)...")

        conn, cur = pg_cursor()
        cur.execute("""
            SELECT
                a.zip_code AS from_zip,
                b.zip_code AS to_zip,
                ROUND(
                    (ST_Distance(
                        ST_Centroid(a.geom::geography),
                        ST_Centroid(b.geom::geography)
                    ) / 1000.0)::numeric, 3
                ) AS distance_km,
                ST_Touches(a.geom, b.geom) AS is_adjacent
            FROM zip_shapes a
            JOIN zip_shapes b
              ON a.zip_code < b.zip_code
             AND (ST_Touches(a.geom, b.geom) OR ST_Intersects(a.geom, b.geom))
            ORDER BY a.zip_code, distance_km
        """)
        pairs = [
            {
                "from_zip": r["from_zip"],
                "to_zip": r["to_zip"],
                "distance_km": float(r["distance_km"]) if r["distance_km"] is not None else None,
                "is_adjacent": bool(r["is_adjacent"]) if r["is_adjacent"] is not None else False,
            }
            for r in cur.fetchall()
        ]
        conn.close()

        cypher = """
        UNWIND $rows AS row
        MATCH (a:ZipCode {zip_code: row.from_zip})
        MATCH (b:ZipCode {zip_code: row.to_zip})
        MERGE (a)-[r:NEIGHBORS]-(b)
        SET r.distance_km = row.distance_km,
            r.is_adjacent = row.is_adjacent
        """
        total = 0
        for batch in _batches(pairs, self.batch_size):
            c = self._run(cypher, {"rows": batch})
            total += c.relationships_created
        logger.success(f"NEIGHBORS: {total} relationships created from {len(pairs)} ZIP pairs")
        return total

    # ── Full migration ───────────────────────────────────────

    def migrate_all(self, clear: bool = False):
        if clear:
            logger.warning("Clearing Neo4j database...")
            self._run("MATCH (n) DETACH DELETE n")

        logger.info("=" * 55)
        logger.info("NOAH PostgreSQL → Neo4j Migration")
        logger.info("=" * 55)

        # Schema
        self.setup_schema()

        # Nodes (order matters: ZipCode before HAS_AFFORDABILITY_DATA)
        n_zip       = self.migrate_zipcodes()
        n_aff       = self.migrate_affordability_zones()
        n_tract     = self.migrate_census_tracts()
        n_proj      = self.migrate_housing_projects()

        # Relationships
        r_aff       = self.migrate_has_affordability_data()
        r_located   = self.migrate_located_in()
        r_tract     = self.migrate_in_census_tract()
        r_neighbors = self.migrate_neighbors()

        logger.info("=" * 55)
        logger.info("Migration complete!")
        logger.info(f"  Nodes:         {n_zip + n_aff + n_tract + n_proj:,}")
        logger.info(f"    ZipCode:          {n_zip}")
        logger.info(f"    AffordabilityZone:{n_aff}")
        logger.info(f"    CensusTract:      {n_tract}")
        logger.info(f"    HousingProject:   {n_proj}")
        logger.info(f"  Relationships: {r_aff + r_located + r_tract + r_neighbors:,}")
        logger.info(f"    HAS_AFFORDABILITY_DATA: {r_aff}")
        logger.info(f"    LOCATED_IN:             {r_located}")
        logger.info(f"    IN_CENSUS_TRACT:        {r_tract}")
        logger.info(f"    NEIGHBORS:              {r_neighbors}")
        logger.info("=" * 55)

        return {
            "nodes": {
                "ZipCode": n_zip,
                "AffordabilityZone": n_aff,
                "CensusTract": n_tract,
                "HousingProject": n_proj,
            },
            "relationships": {
                "HAS_AFFORDABILITY_DATA": r_aff,
                "LOCATED_IN": r_located,
                "IN_CENSUS_TRACT": r_tract,
                "NEIGHBORS": r_neighbors,
            },
        }
