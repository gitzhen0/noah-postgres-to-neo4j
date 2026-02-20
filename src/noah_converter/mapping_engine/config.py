"""
Configuration loader for Mapping Engine

Loads mapping rules from YAML configuration files.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from .models import (
    GraphSchema, NodeType, RelationshipType, Property,
    PropertyType, RelationshipSourceType, SpatialConfig
)


class MappingConfigLoader:
    """Load mapping configuration from YAML"""

    @staticmethod
    def load_from_file(config_path: str) -> Dict[str, Any]:
        """Load raw YAML configuration"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    @staticmethod
    def parse_property(prop_config: Dict[str, Any]) -> Property:
        """Parse property configuration"""
        return Property(
            name=prop_config['name'],
            type=PropertyType[prop_config['type'].upper()],
            nullable=prop_config.get('nullable', True),
            source_column=prop_config.get('source_column'),
            source_type=prop_config.get('source_type'),
            transformation=prop_config.get('transformation'),
            default_value=prop_config.get('default_value')
        )

    @staticmethod
    def parse_node_type(node_config: Dict[str, Any]) -> NodeType:
        """Parse node type configuration"""
        properties = [
            MappingConfigLoader.parse_property(p)
            for p in node_config['properties']
        ]

        return NodeType(
            label=node_config['label'],
            primary_property=node_config['primary_property'],
            properties=properties,
            source_table=node_config['source_table'],
            has_geometry=node_config.get('has_geometry', False),
            geometry_column=node_config.get('geometry_column'),
            indexes=node_config.get('indexes', []),
            merge_keys=node_config.get('merge_keys', [])
        )

    @staticmethod
    def parse_relationship_type(rel_config: Dict[str, Any]) -> RelationshipType:
        """Parse relationship type configuration"""
        properties = [
            MappingConfigLoader.parse_property(p)
            for p in rel_config.get('properties', [])
        ]

        source_type = RelationshipSourceType[rel_config['source_type'].upper()]

        return RelationshipType(
            type=rel_config['type'],
            from_label=rel_config['from_label'],
            to_label=rel_config['to_label'],
            properties=properties,
            source_type=source_type,
            source_table=rel_config.get('source_table'),
            from_column=rel_config.get('from_column'),
            to_column=rel_config.get('to_column'),
            from_id_column=rel_config.get('from_id_column'),
            to_id_column=rel_config.get('to_id_column'),
            computation_query=rel_config.get('computation_query'),
            bidirectional=rel_config.get('bidirectional', False)
        )

    @staticmethod
    def parse_spatial_config(spatial_config: Dict[str, Any]) -> SpatialConfig:
        """Parse spatial configuration"""
        return SpatialConfig(
            preserve_wkt=spatial_config.get('preserve_wkt', True),
            preserve_geojson=spatial_config.get('preserve_geojson', True),
            compute_centroids=spatial_config.get('compute_centroids', True),
            compute_metrics=spatial_config.get('compute_metrics', True),
            compute_bbox=spatial_config.get('compute_bbox', True),
            use_neo4j_point=spatial_config.get('use_neo4j_point', True),
            neighbors_threshold_km=spatial_config.get('neighbors_threshold_km')
        )

    @staticmethod
    def load_graph_schema(config_path: str) -> GraphSchema:
        """Load complete graph schema from YAML"""
        config = MappingConfigLoader.load_from_file(config_path)

        nodes = [
            MappingConfigLoader.parse_node_type(n)
            for n in config.get('nodes', [])
        ]

        relationships = [
            MappingConfigLoader.parse_relationship_type(r)
            for r in config.get('relationships', [])
        ]

        metadata = config.get('metadata', {})

        return GraphSchema(
            nodes=nodes,
            relationships=relationships,
            metadata=metadata
        )
