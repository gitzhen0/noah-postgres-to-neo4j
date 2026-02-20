"""
Mapping Rules Engine

Applies intelligent mapping rules to convert PostgreSQL schema to Neo4j graph schema.
"""

from typing import Dict, List, Optional
from ..schema_analyzer.models import Table, Column, ForeignKey
from .models import (
    NodeType, RelationshipType, Property, PropertyType,
    RelationshipSourceType, GraphSchema
)
import re


class MappingRules:
    """Intelligent mapping rules for RDBMS to Graph conversion"""

    # PostgreSQL to Neo4j type mapping
    TYPE_MAPPING = {
        'integer': PropertyType.INTEGER,
        'bigint': PropertyType.INTEGER,
        'smallint': PropertyType.INTEGER,
        'numeric': PropertyType.FLOAT,
        'decimal': PropertyType.FLOAT,
        'real': PropertyType.FLOAT,
        'double precision': PropertyType.FLOAT,
        'money': PropertyType.FLOAT,
        'varchar': PropertyType.STRING,
        'char': PropertyType.STRING,
        'text': PropertyType.STRING,
        'boolean': PropertyType.BOOLEAN,
        'date': PropertyType.DATE,
        'timestamp': PropertyType.DATETIME,
        'timestamptz': PropertyType.DATETIME,
        'geometry': PropertyType.STRING,  # WKT
        'geography': PropertyType.STRING,  # WKT
    }

    @staticmethod
    def table_to_node_label(table_name: str) -> str:
        """
        Convert table name to node label

        Examples:
            zipcodes -> Zipcode
            housing_projects -> HousingProject
            rent_burden -> RentBurden
        """
        # Remove trailing 's' if plural
        name = table_name.rstrip('s')

        # Convert snake_case to PascalCase
        parts = name.split('_')
        label = ''.join(word.capitalize() for word in parts)

        return label

    @staticmethod
    def column_to_property_name(column_name: str) -> str:
        """
        Convert column name to property name

        Examples:
            median_rent_1br -> median_rent_1br (keep snake_case)
            project_id -> project_id
        """
        # Keep snake_case for Neo4j properties
        return column_name.lower()

    @staticmethod
    def postgres_type_to_neo4j_type(pg_type: str) -> PropertyType:
        """Map PostgreSQL type to Neo4j property type"""
        pg_type_lower = pg_type.lower()

        # Handle array types
        if '[]' in pg_type_lower:
            base_type = pg_type_lower.replace('[]', '').strip()
            if base_type in ['integer', 'bigint', 'smallint']:
                return PropertyType.LIST_INTEGER
            elif base_type in ['numeric', 'decimal', 'real', 'double precision']:
                return PropertyType.LIST_FLOAT
            else:
                return PropertyType.LIST_STRING

        # Direct mapping
        for pg_pattern, neo4j_type in MappingRules.TYPE_MAPPING.items():
            if pg_pattern in pg_type_lower:
                return neo4j_type

        # Default to STRING
        return PropertyType.STRING

    @staticmethod
    def column_to_property(column: Column) -> Property:
        """Convert PostgreSQL column to Neo4j property"""
        return Property(
            name=MappingRules.column_to_property_name(column.name),
            type=MappingRules.postgres_type_to_neo4j_type(column.data_type),
            nullable=column.is_nullable,
            source_column=column.name,
            source_type=column.data_type,
            default_value=column.default_value
        )

    @staticmethod
    def detect_primary_property(table: Table) -> str:
        """
        Detect the primary property for a node

        Priority:
        1. Primary key column
        2. Column ending with '_id'
        3. First column
        """
        # Check primary key
        if table.primary_key:
            return MappingRules.column_to_property_name(table.primary_key[0])

        # Check for *_id columns
        for col in table.columns:
            if col.name.endswith('_id') or col.name == 'id':
                return MappingRules.column_to_property_name(col.name)

        # Fallback to first column
        if table.columns:
            return MappingRules.column_to_property_name(table.columns[0].name)

        return "id"

    @staticmethod
    def detect_geometry_column(table: Table) -> Optional[str]:
        """Detect geometry/geography column in table"""
        for col in table.columns:
            if col.data_type.lower() in ['geometry', 'geography']:
                return col.name
        return None

    @staticmethod
    def table_to_node_type(table: Table) -> NodeType:
        """Convert PostgreSQL table to Neo4j node type"""
        label = MappingRules.table_to_node_label(table.name)
        primary_property = MappingRules.detect_primary_property(table)
        geometry_column = MappingRules.detect_geometry_column(table)

        # Convert all non-geometry columns to properties
        properties = []
        for col in table.columns:
            # Skip geometry columns (will be handled by spatial handler)
            if col.data_type.lower() not in ['geometry', 'geography']:
                properties.append(MappingRules.column_to_property(col))

        # Detect index candidates (commonly queried fields)
        indexes = []
        for col in table.columns:
            col_lower = col.name.lower()
            if any(keyword in col_lower for keyword in [
                'name', 'type', 'status', 'code', 'date', 'borough', 'city'
            ]):
                indexes.append(MappingRules.column_to_property_name(col.name))

        return NodeType(
            label=label,
            primary_property=primary_property,
            properties=properties,
            source_table=table.name,
            has_geometry=geometry_column is not None,
            geometry_column=geometry_column,
            indexes=indexes[:5],  # Limit to 5 indexes
            merge_keys=[primary_property]
        )

    @staticmethod
    def foreign_key_to_relationship(
        fk: ForeignKey,
        from_table_name: str,
        tables: Dict[str, Table]
    ) -> RelationshipType:
        """Convert foreign key to relationship"""
        from_table = tables.get(from_table_name)
        to_table = tables.get(fk.referenced_table)

        if not from_table or not to_table:
            raise ValueError(f"Missing table for FK: {from_table_name} -> {fk.referenced_table}")

        from_label = MappingRules.table_to_node_label(from_table_name)
        to_label = MappingRules.table_to_node_label(fk.referenced_table)

        # Generate relationship type name
        # e.g., buildings -> zipcodes = LOCATED_IN
        rel_type = MappingRules.generate_relationship_type(
            from_label, to_label, fk.column
        )

        return RelationshipType(
            type=rel_type,
            from_label=from_label,
            to_label=to_label,
            properties=[],
            source_type=RelationshipSourceType.FOREIGN_KEY,
            source_table=from_table_name,
            from_column=fk.column,
            to_column=fk.referenced_column
        )

    @staticmethod
    def generate_relationship_type(
        from_label: str,
        to_label: str,
        fk_column: str
    ) -> str:
        """
        Generate relationship type name

        Examples:
            Building -> Zipcode (zipcode_id) = LOCATED_IN
            HousingProject -> Zipcode (zipcode) = LOCATED_IN
            Building -> Owner (owner_id) = OWNED_BY
        """
        fk_lower = fk_column.lower()

        # Common patterns
        if 'zipcode' in fk_lower or 'zip' in fk_lower:
            return 'LOCATED_IN'
        elif 'owner' in fk_lower:
            return 'OWNED_BY'
        elif 'project' in fk_lower:
            return 'HAS_PROJECT'
        elif 'parent' in fk_lower:
            return 'CHILD_OF'
        elif 'manager' in fk_lower or 'managed' in fk_lower:
            return 'MANAGED_BY'

        # Generic pattern: HAS_<TO_LABEL>
        return f'HAS_{to_label.upper()}'

    @staticmethod
    def generate_graph_schema(tables: Dict[str, Table]) -> GraphSchema:
        """
        Generate complete graph schema from PostgreSQL tables

        Args:
            tables: Dictionary of table_name -> Table

        Returns:
            GraphSchema with nodes and relationships
        """
        nodes = []
        relationships = []

        # Convert tables to nodes
        for table in tables.values():
            node = MappingRules.table_to_node_type(table)
            nodes.append(node)

        # Convert foreign keys to relationships
        for table in tables.values():
            for fk in table.foreign_keys:
                try:
                    rel = MappingRules.foreign_key_to_relationship(fk, table.name, tables)
                    relationships.append(rel)
                except ValueError as e:
                    print(f"Warning: Skipping FK {fk.column}: {e}")

        metadata = {
            'num_tables': len(tables),
            'num_nodes': len(nodes),
            'num_relationships': len(relationships),
            'auto_generated': True
        }

        return GraphSchema(
            nodes=nodes,
            relationships=relationships,
            metadata=metadata
        )
