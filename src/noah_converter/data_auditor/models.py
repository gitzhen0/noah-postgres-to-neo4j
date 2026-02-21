"""
Post-Migration Audit Models

Data classes for audit results and report generation.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict


@dataclass
class NodeCountResult:
    label: str
    source_table: str
    pg_count: int
    neo4j_count: int

    @property
    def match(self) -> bool:
        return self.pg_count == self.neo4j_count

    @property
    def diff(self) -> int:
        return self.neo4j_count - self.pg_count

    @property
    def diff_pct(self) -> float:
        if self.pg_count == 0:
            return 0.0
        return abs(self.diff) / self.pg_count * 100

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "source_table": self.source_table,
            "pg_count": self.pg_count,
            "neo4j_count": self.neo4j_count,
            "match": self.match,
            "diff": self.diff,
            "diff_pct": round(self.diff_pct, 2),
        }


@dataclass
class RelCountResult:
    rel_type: str
    source_type: str
    neo4j_count: int
    pg_expected: Optional[int] = None  # None if can't compute from PG

    @property
    def match(self) -> bool:
        if self.pg_expected is None:
            return True
        return self.neo4j_count == self.pg_expected

    def to_dict(self) -> dict:
        return {
            "rel_type": self.rel_type,
            "source_type": self.source_type,
            "neo4j_count": self.neo4j_count,
            "pg_expected": self.pg_expected,
            "match": self.match,
        }


@dataclass
class PropertyCoverage:
    property_name: str
    total_nodes: int
    populated: int

    @property
    def coverage_pct(self) -> float:
        if self.total_nodes == 0:
            return 0.0
        return self.populated / self.total_nodes * 100

    def to_dict(self) -> dict:
        return {
            "property_name": self.property_name,
            "populated": self.populated,
            "total": self.total_nodes,
            "coverage_pct": round(self.coverage_pct, 1),
        }


@dataclass
class NodePropertyCoverageResult:
    label: str
    total_nodes: int
    properties: List[PropertyCoverage] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "total_nodes": self.total_nodes,
            "properties": [p.to_dict() for p in self.properties],
        }


@dataclass
class SampleMismatch:
    merge_key_value: str
    property_name: str
    neo4j_value: Any
    pg_value: Any

    def to_dict(self) -> dict:
        return {
            "merge_key_value": self.merge_key_value,
            "property_name": self.property_name,
            "neo4j_value": str(self.neo4j_value),
            "pg_value": str(self.pg_value),
        }


@dataclass
class SampleCheckResult:
    label: str
    sample_size: int
    checked: int
    matched: int
    missing_in_neo4j: int
    mismatches: List[SampleMismatch] = field(default_factory=list)

    @property
    def match_rate(self) -> float:
        if self.checked == 0:
            return 0.0
        return self.matched / self.checked * 100

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "checked": self.checked,
            "matched": self.matched,
            "missing_in_neo4j": self.missing_in_neo4j,
            "match_rate_pct": round(self.match_rate, 1),
            "mismatches": [m.to_dict() for m in self.mismatches],
        }


@dataclass
class AuditReport:
    timestamp: str
    mapping_source: str
    node_counts: List[NodeCountResult]
    rel_counts: List[RelCountResult]
    property_coverage: List[NodePropertyCoverageResult]
    sample_checks: List[SampleCheckResult]
    issues: List[str]

    @property
    def overall_status(self) -> str:
        if not self.issues:
            return "PASS"
        if any(i.startswith("ERROR") for i in self.issues):
            return "FAIL"
        return "WARN"

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "mapping_source": self.mapping_source,
            "overall_status": self.overall_status,
            "issues": self.issues,
            "node_counts": [n.to_dict() for n in self.node_counts],
            "rel_counts": [r.to_dict() for r in self.rel_counts],
            "property_coverage": [c.to_dict() for c in self.property_coverage],
            "sample_checks": [s.to_dict() for s in self.sample_checks],
        }
