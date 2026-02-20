"""
Data models for Mapping Engine

Defines the structure for graph schema, node types, relationships, and properties.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class PropertyType(Enum):
    """Neo4j property types"""
    STRING = "String"
    INTEGER = "Integer"
    FLOAT = "Float"
    BOOLEAN = "Boolean"
    POINT = "Point"
    DATE = "Date"
    DATETIME = "DateTime"
    LIST_STRING = "List<String>"
    LIST_INTEGER = "List<Integer>"
    LIST_FLOAT = "List<Float>"


class RelationshipSourceType(Enum):
    """Source of relationship data"""
    FOREIGN_KEY = "FK"
    COMPUTED = "COMPUTED"
    SPATIAL = "SPATIAL"


@dataclass
class Property:
    """Property definition for nodes or relationships"""
    name: str
    type: PropertyType
    nullable: bool = True
    source_column: Optional[str] = None
    source_type: Optional[str] = None  # PostgreSQL type
    transformation: Optional[str] = None  # SQL expression for transformation
    default_value: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.value,
            "nullable": self.nullable,
            "source_column": self.source_column,
            "source_type": self.source_type,
            "transformation": self.transformation,
            "default_value": self.default_value
        }


@dataclass
class NodeType:
    """Node type definition"""
    label: str
    primary_property: str
    properties: List[Property]
    source_table: str
    has_geometry: bool = False
    geometry_column: Optional[str] = None
    indexes: List[str] = field(default_factory=list)
    merge_keys: List[str] = field(default_factory=list)  # For MERGE operations

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "primary_property": self.primary_property,
            "properties": [p.to_dict() for p in self.properties],
            "source_table": self.source_table,
            "has_geometry": self.has_geometry,
            "geometry_column": self.geometry_column,
            "indexes": self.indexes,
            "merge_keys": self.merge_keys
        }


@dataclass
class RelationshipType:
    """Relationship type definition"""
    type: str
    from_label: str
    to_label: str
    properties: List[Property] = field(default_factory=list)
    source_type: RelationshipSourceType = RelationshipSourceType.FOREIGN_KEY

    # For FK-based relationships
    source_table: Optional[str] = None
    from_column: Optional[str] = None
    to_column: Optional[str] = None

    # For FK relationships: which columns in source_table supply the node merge-key values
    # from_id_column: column whose value equals from_label's merge key
    # to_id_column:   column whose value equals to_label's merge key
    from_id_column: Optional[str] = None
    to_id_column: Optional[str] = None

    # For computed relationships (e.g., spatial)
    computation_query: Optional[str] = None

    # Relationship direction
    bidirectional: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "from_label": self.from_label,
            "to_label": self.to_label,
            "properties": [p.to_dict() for p in self.properties],
            "source_type": self.source_type.value,
            "source_table": self.source_table,
            "from_column": self.from_column,
            "to_column": self.to_column,
            "from_id_column": self.from_id_column,
            "to_id_column": self.to_id_column,
            "computation_query": self.computation_query,
            "bidirectional": self.bidirectional
        }


@dataclass
class GraphSchema:
    """Complete graph schema definition"""
    nodes: List[NodeType]
    relationships: List[RelationshipType]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "relationships": [r.to_dict() for r in self.relationships],
            "metadata": self.metadata
        }

    def get_node_by_label(self, label: str) -> Optional[NodeType]:
        """Find node type by label"""
        for node in self.nodes:
            if node.label == label:
                return node
        return None

    def get_relationships_for_node(self, label: str) -> List[RelationshipType]:
        """Get all relationships connected to a node"""
        return [r for r in self.relationships
                if r.from_label == label or r.to_label == label]


@dataclass
class SpatialConfig:
    """
    Configuration for spatial data handling.

    Design principle (from Gemini conversation):
    - CORE (always on): centroids, area, Neo4j Point
    - OPTIONAL (off by default): WKT, GeoJSON, bbox, perimeter
    - "建议每个节点只保留 5-10 个最核心的信息属性"
    """
    compute_centroids: bool = True       # center_lat, center_lon
    compute_area: bool = True            # area_km2
    use_neo4j_point: bool = True         # location: point({...})
    preserve_wkt: bool = True            # geometry_wkt — 100% 零损耗
    preserve_geojson: bool = True        # geometry_geojson — 100% 零损耗
    compute_metrics: bool = True         # perimeter_km — 100% 零损耗
    compute_bbox: bool = True            # bbox_xmin/ymin/xmax/ymax — 100% 零损耗
    neighbors_threshold_km: Optional[float] = None
    target_srid: Optional[int] = None    # ST_Transform target SRID (e.g., 4326)
