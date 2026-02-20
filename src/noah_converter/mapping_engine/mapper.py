"""
Mapping Engine

Main orchestrator for PostgreSQL to Neo4j schema mapping.
"""

import json
from pathlib import Path
from typing import Dict, Optional, List
from ..schema_analyzer.models import Table
from ..utils.db_connection import PostgreSQLConnection
from .models import GraphSchema, NodeType, SpatialConfig
from .mapping_rules import MappingRules
from .spatial_handler import SpatialDataHandler
from .config import MappingConfigLoader


class MappingEngine:
    """
    Main mapping engine that converts PostgreSQL schema to Neo4j graph schema
    """

    def __init__(
        self,
        tables: Dict[str, Table],
        spatial_config: Optional[SpatialConfig] = None,
        config_file: Optional[str] = None
    ):
        """
        Initialize mapping engine

        Args:
            tables: Dictionary of table_name -> Table objects
            spatial_config: Spatial data handling configuration
            config_file: Optional YAML config file to override auto-generation
        """
        self.tables = tables
        self.spatial_config = spatial_config or SpatialConfig()
        self.config_file = config_file
        self.graph_schema: Optional[GraphSchema] = None

    def generate_graph_schema(self) -> GraphSchema:
        """
        Generate graph schema from PostgreSQL tables

        Returns:
            GraphSchema with nodes and relationships
        """
        if self.config_file:
            # Load from YAML config
            self.graph_schema = MappingConfigLoader.load_graph_schema(self.config_file)
        else:
            # Auto-generate using mapping rules
            self.graph_schema = MappingRules.generate_graph_schema(self.tables)

            # Add spatial properties to nodes with geometry
            self._add_spatial_properties()

            # Add spatial relationships (NEIGHBORS)
            self._add_spatial_relationships()

        return self.graph_schema

    def _add_spatial_properties(self):
        """
        Add spatial properties to nodes with geometry columns.

        Follows Gemini guidance: only CORE properties by default,
        WKT/GeoJSON/bbox are optional.
        """
        if not self.spatial_config.compute_centroids:
            return

        for node in self.graph_schema.nodes:
            if node.has_geometry and node.geometry_column:
                # Generate spatial properties with config-driven filtering
                spatial_props = SpatialDataHandler.generate_spatial_properties(
                    geometry_column=node.geometry_column,
                    table_name=node.source_table,
                    include_wkt=self.spatial_config.preserve_wkt,
                    include_geojson=self.spatial_config.preserve_geojson,
                    include_metrics=self.spatial_config.compute_metrics,
                    include_bbox=self.spatial_config.compute_bbox,
                    target_srid=self.spatial_config.target_srid
                )

                # Add to node properties
                node.properties.extend(spatial_props)

    def _add_spatial_relationships(self):
        """Add spatial NEIGHBORS relationships for geometry tables"""
        # Detect spatial tables
        spatial_tables = SpatialDataHandler.detect_spatial_tables(self.tables)

        for spatial_info in spatial_tables:
            table_name = spatial_info['table_name']
            node = self.graph_schema.get_node_by_label(
                MappingRules.table_to_node_label(table_name)
            )

            if node:
                # Create NEIGHBORS relationship
                neighbors_rel = SpatialDataHandler.create_neighbors_relationship(
                    from_label=node.label,
                    threshold_km=self.spatial_config.neighbors_threshold_km
                )

                # Store computation query in metadata
                neighbors_rel.computation_query = SpatialDataHandler.generate_neighbors_query(
                    table_name=table_name,
                    geometry_column=spatial_info['geometry_column'],
                    id_column=spatial_info['id_column'],
                    threshold_km=self.spatial_config.neighbors_threshold_km
                )

                self.graph_schema.relationships.append(neighbors_rel)

    def export_schema(self, output_path: str):
        """
        Export graph schema to JSON file

        Args:
            output_path: Path to output JSON file
        """
        if not self.graph_schema:
            raise ValueError("Graph schema not generated yet. Call generate_graph_schema() first.")

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.graph_schema.to_dict(), f, indent=2, ensure_ascii=False)

        print(f"✅ Graph schema exported to {output_path}")

    def export_yaml_config(self, output_path: str):
        """
        Export graph schema as YAML mapping config

        Args:
            output_path: Path to output YAML file
        """
        if not self.graph_schema:
            raise ValueError("Graph schema not generated yet. Call generate_graph_schema() first.")

        import yaml

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert to YAML-friendly format
        config = {
            'metadata': self.graph_schema.metadata,
            'spatial': {
                'preserve_wkt': self.spatial_config.preserve_wkt,
                'preserve_geojson': self.spatial_config.preserve_geojson,
                'compute_centroids': self.spatial_config.compute_centroids,
                'compute_metrics': self.spatial_config.compute_metrics,
                'compute_bbox': self.spatial_config.compute_bbox,
                'use_neo4j_point': self.spatial_config.use_neo4j_point,
                'neighbors_threshold_km': self.spatial_config.neighbors_threshold_km,
            },
            'nodes': [
                {
                    'label': node.label,
                    'source_table': node.source_table,
                    'primary_property': node.primary_property,
                    'has_geometry': node.has_geometry,
                    'geometry_column': node.geometry_column,
                    'indexes': node.indexes,
                    'merge_keys': node.merge_keys,
                    'properties': [
                        {
                            'name': p.name,
                            'type': p.type.value.lower(),
                            'nullable': p.nullable,
                            'source_column': p.source_column,
                            'source_type': p.source_type,
                            'transformation': p.transformation,
                            'default_value': p.default_value
                        }
                        for p in node.properties
                    ]
                }
                for node in self.graph_schema.nodes
            ],
            'relationships': [
                {
                    'type': rel.type,
                    'from_label': rel.from_label,
                    'to_label': rel.to_label,
                    'source_type': rel.source_type.value.lower(),
                    'source_table': rel.source_table,
                    'from_column': rel.from_column,
                    'to_column': rel.to_column,
                    'computation_query': rel.computation_query,
                    'bidirectional': rel.bidirectional,
                    'properties': [
                        {
                            'name': p.name,
                            'type': p.type.value.lower(),
                            'nullable': p.nullable,
                            'source_column': p.source_column
                        }
                        for p in rel.properties
                    ]
                }
                for rel in self.graph_schema.relationships
            ]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        print(f"✅ YAML config exported to {output_path}")

    def get_summary(self) -> Dict[str, any]:
        """
        Get summary statistics of the mapping

        Returns:
            Dictionary with summary stats
        """
        if not self.graph_schema:
            return {}

        spatial_nodes = sum(1 for n in self.graph_schema.nodes if n.has_geometry)
        fk_rels = sum(1 for r in self.graph_schema.relationships
                      if r.source_type.value == 'FK')
        spatial_rels = sum(1 for r in self.graph_schema.relationships
                          if r.source_type.value == 'SPATIAL')

        return {
            'total_nodes': len(self.graph_schema.nodes),
            'spatial_nodes': spatial_nodes,
            'total_relationships': len(self.graph_schema.relationships),
            'fk_relationships': fk_rels,
            'spatial_relationships': spatial_rels,
            'total_properties': sum(len(n.properties) for n in self.graph_schema.nodes),
            'node_labels': [n.label for n in self.graph_schema.nodes]
        }
