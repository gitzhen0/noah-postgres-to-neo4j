"""
Audit report status / relationship-count semantics.

These are the invariants the post-migration auditor must preserve:
  1. A FK relationship where Neo4j count equals (source rows − orphans) is a MATCH.
  2. Orphan FK rows — source rows whose target doesn't exist in the target table —
     are not a WARNing; they are an expected consequence of MERGE semantics
     (no target node → no relationship created).
  3. Overall status:  WARN iff any issue starts with "WARN"; FAIL iff any
     starts with "ERROR"; otherwise PASS — INFO-only issue lists must PASS.
"""

from __future__ import annotations

import pytest

from noah_converter.data_auditor.models import (
    AuditReport,
    RelCountResult,
    NodeCountResult,
)


def _empty_report(issues: list[str]) -> AuditReport:
    return AuditReport(
        timestamp="2026-04-22T00:00:00",
        mapping_source="test",
        node_counts=[],
        rel_counts=[],
        property_coverage=[],
        sample_checks=[],
        issues=issues,
    )


class TestRelCountResult:
    def test_fk_match_with_orphans(self):
        """The canonical LOCATED_IN_ZIP story: 35 orphan postcodes, but
        every resolvable FK did produce an edge → MATCH."""
        r = RelCountResult(
            rel_type="LOCATED_IN_ZIP",
            source_type="FK",
            neo4j_count=6851,
            pg_expected=6851,
            pg_orphans=35,
            pg_fk_rows=6886,
        )
        assert r.match is True
        d = r.to_dict()
        assert d["pg_orphans"] == 35
        assert d["pg_fk_rows"] == 6886
        assert d["match"] is True

    def test_fk_mismatch_fails(self):
        """Neo4j count < pg_expected (after orphans excluded) means the
        migration lost data → MATCH is False."""
        r = RelCountResult(
            rel_type="LOCATED_IN_ZIP",
            source_type="FK",
            neo4j_count=6800,
            pg_expected=6851,
            pg_orphans=35,
            pg_fk_rows=6886,
        )
        assert r.match is False

    def test_computed_rel_no_pg_expected(self):
        """Computed/spatial rels can't be audited against PG row count →
        match defaults to True (no false alarms)."""
        r = RelCountResult(
            rel_type="NEIGHBORS",
            source_type="SPATIAL",
            neo4j_count=392,
            pg_expected=None,
        )
        assert r.match is True


class TestAuditReportStatus:
    def test_empty_issues_pass(self):
        assert _empty_report([]).overall_status == "PASS"

    def test_info_only_passes(self):
        """INFO-level issues (e.g. documented orphan FKs) must not
        demote status to WARN — they're diagnostic, not actionable."""
        r = _empty_report(["INFO: LOCATED_IN_ZIP — 35 rows skipped (expected)"])
        assert r.overall_status == "PASS"

    def test_warn_demotes(self):
        r = _empty_report(["WARN: LOCATED_IN_ZIP count mismatch"])
        assert r.overall_status == "WARN"

    def test_error_dominates(self):
        """ERROR beats WARN beats INFO in the ordering."""
        r = _empty_report(
            [
                "INFO: something minor",
                "WARN: medium concern",
                "ERROR: critical mismatch",
            ]
        )
        assert r.overall_status == "FAIL"

    def test_mixed_info_and_warn_is_warn(self):
        r = _empty_report(
            [
                "INFO: orphan FKs documented",
                "WARN: one node count off by 3",
            ]
        )
        assert r.overall_status == "WARN"


class TestNodeCountResult:
    def test_diff_pct(self):
        n = NodeCountResult(
            label="HousingProject",
            source_table="housing_projects",
            pg_count=8604,
            neo4j_count=8600,
        )
        assert n.match is False
        assert n.diff == -4
        assert round(n.diff_pct, 3) == round(4 / 8604 * 100, 3)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
