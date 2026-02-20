"""
Data models for Schema Interpreter results.

These are the LLM's decisions about how to map a relational schema to a graph.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Literal


Confidence = Literal["high", "medium", "low"]


@dataclass
class TransformationDecision:
    """A computed/derived graph property using a SQL expression."""
    name: str                     # graph property name, e.g. "center_lat"
    source_column: str            # PG column being transformed, e.g. "geom"
    transformation: str           # SQL expression, e.g. "ST_Y(ST_Centroid(geom))"
    neo4j_type: str = "float"     # "string" | "integer" | "float" | "boolean"


@dataclass
class RelationshipPropertyDecision:
    """A property on a relationship (from computation_query result columns)."""
    name: str
    neo4j_type: str = "float"


@dataclass
class NodeDecision:
    """LLM's decision for one table → node type mapping."""
    label: str                    # PascalCase node label
    source_table: str             # PostgreSQL table name
    confidence: Confidence
    reasoning: str

    merge_keys: List[str]         # graph property names used for MERGE (must be unique)
    has_geometry: bool = False
    geometry_column: Optional[str] = None

    include_all_columns: bool = True   # include every non-spatial column
    exclude_columns: List[str] = field(default_factory=list)
    rename_columns: dict = field(default_factory=dict)  # {pg_col: graph_prop_name}
    transformations: List[TransformationDecision] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)   # graph property names to index


@dataclass
class RelationshipDecision:
    """LLM's decision for one FK / computed / spatial relationship."""
    type: str                     # SCREAMING_SNAKE_CASE relationship type
    from_label: str
    to_label: str
    source_type: str              # "foreign_key" | "computed" | "spatial"
    confidence: Confidence
    reasoning: str
    bidirectional: bool = False
    properties: List[RelationshipPropertyDecision] = field(default_factory=list)

    # For foreign_key relationships
    source_table: Optional[str] = None
    from_id_column: Optional[str] = None   # col in source_table = from_label merge key
    to_id_column: Optional[str] = None     # col in source_table = to_label merge key

    # For computed / spatial relationships
    computation_query: Optional[str] = None


@dataclass
class SkippedTable:
    table: str
    reason: str


@dataclass
class InterpretationResult:
    """Complete output from SchemaInterpreter.interpret()."""
    nodes: List[NodeDecision]
    relationships: List[RelationshipDecision]
    skipped_tables: List[SkippedTable]
    validation_warnings: List[str]
    mapping_yaml: str         # Ready-to-write mapping_rules.yaml content
    raw_llm_response: str     # Raw JSON string from LLM (for debugging)
