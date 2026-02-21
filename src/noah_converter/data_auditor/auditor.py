"""
Post-Migration Auditor

Schema-driven validation: compares PostgreSQL source data against the
migrated Neo4j graph. Works with any mapping_rules.yaml — not NOAH-specific.
"""

import random
from datetime import datetime
from typing import List, Optional, Any

import psycopg2
import psycopg2.extras
from neo4j import GraphDatabase
from loguru import logger

from ..mapping_engine.models import GraphSchema, RelationshipSourceType
from .models import (
    AuditReport,
    NodeCountResult,
    RelCountResult,
    NodePropertyCoverageResult,
    PropertyCoverage,
    SampleCheckResult,
    SampleMismatch,
)


class MigrationAuditor:
    """
    Validates a completed migration by comparing PostgreSQL source data
    against Neo4j graph data, driven entirely by the mapping schema.
    """

    def __init__(
        self,
        pg_dsn: dict,
        neo4j_uri: str,
        neo4j_auth: tuple,
        schema: GraphSchema,
        sample_size: int = 20,
    ):
        self.pg_dsn = pg_dsn
        self.schema = schema
        self.sample_size = sample_size
        self.driver = GraphDatabase.driver(neo4j_uri, auth=neo4j_auth)

    def close(self):
        self.driver.close()

    def run_audit(self, mapping_source: str = "") -> AuditReport:
        """Run all audit checks and return a consolidated report."""
        logger.info("Starting post-migration audit")

        logger.info("Checking node counts...")
        node_counts = self._audit_node_counts()

        logger.info("Checking relationship counts...")
        rel_counts = self._audit_relationship_counts()

        logger.info("Checking property coverage...")
        coverage = self._audit_property_coverage()

        logger.info("Running data sample checks...")
        samples = self._audit_samples()

        issues = self._collect_issues(node_counts, rel_counts, samples)

        return AuditReport(
            timestamp=datetime.now().isoformat(),
            mapping_source=mapping_source,
            node_counts=node_counts,
            rel_counts=rel_counts,
            property_coverage=coverage,
            sample_checks=samples,
            issues=issues,
        )

    # ------------------------------------------------------------------
    # Node count audit
    # ------------------------------------------------------------------

    def _audit_node_counts(self) -> List[NodeCountResult]:
        results = []
        with psycopg2.connect(**self.pg_dsn) as pg:
            with pg.cursor() as cur:
                for node in self.schema.nodes:
                    cur.execute(f"SELECT COUNT(*) FROM {node.source_table}")
                    pg_count = cur.fetchone()[0]

                    with self.driver.session() as session:
                        r = session.run(
                            f"MATCH (n:{node.label}) RETURN count(n) AS cnt"
                        )
                        neo4j_count = r.single()["cnt"]

                    results.append(
                        NodeCountResult(
                            label=node.label,
                            source_table=node.source_table,
                            pg_count=pg_count,
                            neo4j_count=neo4j_count,
                        )
                    )
                    logger.debug(
                        f"{node.label}: PG={pg_count}, Neo4j={neo4j_count}"
                    )
        return results

    # ------------------------------------------------------------------
    # Relationship count audit
    # ------------------------------------------------------------------

    def _audit_relationship_counts(self) -> List[RelCountResult]:
        results = []
        with psycopg2.connect(**self.pg_dsn) as pg:
            with pg.cursor() as cur:
                for rel in self.schema.relationships:
                    with self.driver.session() as session:
                        r = session.run(
                            f"MATCH ()-[r:{rel.type}]->() RETURN count(r) AS cnt"
                        )
                        neo4j_count = r.single()["cnt"]

                    # For FK relationships we can estimate expected count from PG
                    pg_expected = None
                    if (
                        rel.source_type == RelationshipSourceType.FOREIGN_KEY
                        and rel.source_table
                        and rel.from_id_column
                        and rel.to_id_column
                    ):
                        try:
                            cur.execute(
                                f"SELECT COUNT(*) FROM {rel.source_table} "
                                f"WHERE {rel.from_id_column} IS NOT NULL "
                                f"AND {rel.to_id_column} IS NOT NULL"
                            )
                            pg_expected = cur.fetchone()[0]
                        except Exception as e:
                            logger.warning(f"Could not count PG rows for {rel.type}: {e}")

                    results.append(
                        RelCountResult(
                            rel_type=rel.type,
                            source_type=rel.source_type.value,
                            neo4j_count=neo4j_count,
                            pg_expected=pg_expected,
                        )
                    )
        return results

    # ------------------------------------------------------------------
    # Property coverage audit
    # ------------------------------------------------------------------

    def _audit_property_coverage(self) -> List[NodePropertyCoverageResult]:
        results = []
        with self.driver.session() as session:
            for node in self.schema.nodes:
                r = session.run(
                    f"MATCH (n:{node.label}) RETURN count(n) AS cnt"
                )
                total = r.single()["cnt"]

                coverages = []
                for prop in node.properties:
                    r = session.run(
                        f"MATCH (n:{node.label}) "
                        f"WHERE n.`{prop.name}` IS NOT NULL "
                        f"RETURN count(n) AS cnt"
                    )
                    populated = r.single()["cnt"]
                    coverages.append(
                        PropertyCoverage(
                            property_name=prop.name,
                            total_nodes=total,
                            populated=populated,
                        )
                    )

                results.append(
                    NodePropertyCoverageResult(
                        label=node.label,
                        total_nodes=total,
                        properties=coverages,
                    )
                )
        return results

    # ------------------------------------------------------------------
    # Data sample check
    # ------------------------------------------------------------------

    def _audit_samples(self) -> List[SampleCheckResult]:
        """
        For each node type:
        1. Sample N merge-key values from Neo4j
        2. Look up each in PostgreSQL
        3. Compare directly-mapped properties (no transformations)
        """
        results = []

        for node in self.schema.nodes:
            if not node.merge_keys:
                continue
            merge_key = node.merge_keys[0]

            # Find the PG source column for the merge key
            merge_key_pg_col = merge_key  # default: same name
            for prop in node.properties:
                if prop.name == merge_key and prop.source_column:
                    merge_key_pg_col = prop.source_column
                    break

            # Sample merge-key values from Neo4j
            with self.driver.session() as session:
                r = session.run(
                    f"MATCH (n:{node.label}) "
                    f"RETURN n.`{merge_key}` AS mk "
                    f"LIMIT {self.sample_size * 5}"  # fetch extra, pick random subset
                )
                all_keys = [
                    rec["mk"] for rec in r if rec["mk"] is not None
                ]

            if not all_keys:
                logger.warning(f"{node.label}: no merge-key values found in Neo4j")
                continue

            sample_keys = random.sample(
                all_keys, min(self.sample_size, len(all_keys))
            )

            # Properties to compare: direct mappings only (no SQL transformations)
            comparable_props = [
                p
                for p in node.properties
                if p.source_column
                and not p.transformation
                and p.name != merge_key
            ][:10]  # cap at 10 properties per node

            checked = 0
            matched = 0
            missing_in_pg = 0
            mismatches: List[SampleMismatch] = []

            with psycopg2.connect(**self.pg_dsn) as pg:
                with pg.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor
                ) as cur:
                    for key_val in sample_keys:
                        # Fetch from PostgreSQL
                        try:
                            cur.execute(
                                f"SELECT * FROM {node.source_table} "
                                f"WHERE {merge_key_pg_col} = %s",
                                (key_val,),
                            )
                            pg_row = cur.fetchone()
                        except Exception as e:
                            logger.warning(f"PG lookup failed for {node.label} key={key_val}: {e}")
                            continue

                        if pg_row is None:
                            missing_in_pg += 1
                            continue

                        # Fetch from Neo4j
                        with self.driver.session() as session:
                            r = session.run(
                                f"MATCH (n:{node.label} {{{merge_key}: $val}}) "
                                f"RETURN n",
                                val=key_val,
                            )
                            rec = r.single()
                            if not rec:
                                missing_in_pg += 1
                                continue
                            neo4j_node = dict(rec["n"])

                        checked += 1
                        row_ok = True

                        for prop in comparable_props:
                            neo4j_val = neo4j_node.get(prop.name)
                            pg_val = pg_row.get(prop.source_column)

                            if not _values_match(neo4j_val, pg_val):
                                row_ok = False
                                if len(mismatches) < 5:  # keep first 5 examples
                                    mismatches.append(
                                        SampleMismatch(
                                            merge_key_value=str(key_val),
                                            property_name=prop.name,
                                            neo4j_value=neo4j_val,
                                            pg_value=pg_val,
                                        )
                                    )

                        if row_ok:
                            matched += 1

            results.append(
                SampleCheckResult(
                    label=node.label,
                    sample_size=self.sample_size,
                    checked=checked,
                    matched=matched,
                    missing_in_neo4j=missing_in_pg,
                    mismatches=mismatches,
                )
            )
            logger.info(
                f"{node.label}: {matched}/{checked} samples matched "
                f"({missing_in_pg} not found in PG)"
            )

        return results

    # ------------------------------------------------------------------
    # Issue collection
    # ------------------------------------------------------------------

    def _collect_issues(
        self,
        node_counts: List[NodeCountResult],
        rel_counts: List[RelCountResult],
        samples: List[SampleCheckResult],
    ) -> List[str]:
        issues = []

        for nc in node_counts:
            if not nc.match:
                severity = "ERROR" if nc.diff_pct > 5 else "WARN"
                issues.append(
                    f"{severity}: {nc.label} count mismatch — "
                    f"PG={nc.pg_count:,}, Neo4j={nc.neo4j_count:,} "
                    f"({nc.diff:+,}, {nc.diff_pct:.1f}%)"
                )

        for rc in rel_counts:
            if rc.neo4j_count == 0:
                issues.append(
                    f"WARN: {rc.rel_type} has 0 relationships in Neo4j"
                )
            elif rc.pg_expected is not None and not rc.match:
                diff = rc.neo4j_count - rc.pg_expected
                issues.append(
                    f"WARN: {rc.rel_type} count mismatch — "
                    f"PG expected={rc.pg_expected:,}, Neo4j={rc.neo4j_count:,} ({diff:+,})"
                )

        for sc in samples:
            if sc.match_rate < 95.0 and sc.checked > 0:
                issues.append(
                    f"WARN: {sc.label} sample match rate {sc.match_rate:.1f}% "
                    f"(threshold: 95%)"
                )

        return issues


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _values_match(neo4j_val: Any, pg_val: Any) -> bool:
    """
    Fuzzy equality between a Neo4j property value and a PostgreSQL column value.
    Handles None, numeric types, strings, and dates.
    """
    if neo4j_val is None and pg_val is None:
        return True
    if neo4j_val is None or pg_val is None:
        return False

    # Numeric: compare with small tolerance for floats
    try:
        if isinstance(neo4j_val, (int, float)) or isinstance(pg_val, (int, float)):
            return abs(float(neo4j_val) - float(pg_val)) < 1e-6
    except (ValueError, TypeError):
        pass

    # Fall back to string comparison (handles dates, booleans, etc.)
    return str(neo4j_val).strip() == str(pg_val).strip()
