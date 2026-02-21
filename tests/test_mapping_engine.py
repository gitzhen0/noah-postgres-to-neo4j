#!/usr/bin/env python3
"""
Quick test of the Mapping Engine without dependencies
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from noah_converter.mapping_engine import (
    MappingEngine,
    MappingRules,
    SpatialConfig,
    CypherDDLGenerator
)
from noah_converter.schema_analyzer.models import Table, Column, ForeignKey, TableType

def create_test_tables():
    """Create test tables for mapping"""

    # Zipcode table with geometry
    zipcode_table = Table(
        name="zipcodes",
        schema="public",
        table_type=TableType.ENTITY,
        columns=[
            Column(name="zipcode", data_type="varchar", is_nullable=False),
            Column(name="borough", data_type="varchar", is_nullable=True),
            Column(name="median_rent_1br", data_type="numeric", is_nullable=True),
            Column(name="median_income", data_type="numeric", is_nullable=True),
            Column(name="geometry", data_type="geometry", is_nullable=True),
        ],
        primary_key=["zipcode"],
        foreign_keys=[],
        row_count=177
    )

    # Buildings table
    buildings_table = Table(
        name="buildings",
        schema="public",
        table_type=TableType.ENTITY,
        columns=[
            Column(name="bbl", data_type="varchar", is_nullable=False),
            Column(name="address", data_type="text", is_nullable=True),
            Column(name="zipcode", data_type="varchar", is_nullable=True),
            Column(name="year_built", data_type="integer", is_nullable=True),
            Column(name="num_floors", data_type="integer", is_nullable=True),
            Column(name="geom", data_type="geometry", is_nullable=True),
        ],
        primary_key=["bbl"],
        foreign_keys=[
            ForeignKey(
                name="buildings_zipcode_fkey",
                column="zipcode",
                referenced_table="zipcodes",
                referenced_column="zipcode"
            )
        ],
        row_count=100000
    )

    # Housing Projects table
    projects_table = Table(
        name="housing_projects",
        schema="public",
        table_type=TableType.ENTITY,
        columns=[
            Column(name="project_id", data_type="varchar", is_nullable=False),
            Column(name="project_name", data_type="text", is_nullable=True),
            Column(name="total_units", data_type="integer", is_nullable=True),
            Column(name="postcode", data_type="varchar", is_nullable=True),
        ],
        primary_key=["project_id"],
        foreign_keys=[
            ForeignKey(
                name="housing_projects_postcode_fkey",
                column="postcode",
                referenced_table="zipcodes",
                referenced_column="zipcode"
            )
        ],
        row_count=2000
    )

    return {
        "zipcodes": zipcode_table,
        "buildings": buildings_table,
        "housing_projects": projects_table
    }


def main():
    print("=" * 60)
    print("Testing Mapping Engine")
    print("=" * 60)
    print()

    # Create test tables
    print("Step 1: Creating test schema...")
    tables = create_test_tables()
    print(f"✓ Created {len(tables)} tables")
    print()

    # PostGIS 100% 零损耗：所有空间数据全部迁移
    print("Step 2: Creating spatial config (100% zero-loss)...")
    spatial_config = SpatialConfig(
        compute_centroids=True,
        compute_area=True,
        use_neo4j_point=True,
        preserve_wkt=True,
        preserve_geojson=True,
        compute_metrics=True,
        compute_bbox=True,
        neighbors_threshold_km=5.0
    )
    print("✓ Spatial config created (100% zero-loss mode)")
    print()

    # Create mapping engine
    print("Step 3: Initializing Mapping Engine...")
    mapper = MappingEngine(
        tables=tables,
        spatial_config=spatial_config
    )
    print("✓ Mapping Engine initialized")
    print()

    # Generate graph schema
    print("Step 4: Generating graph schema...")
    graph_schema = mapper.generate_graph_schema()
    print("✓ Graph schema generated")
    print()

    # Display summary
    summary = mapper.get_summary()
    print("=" * 60)
    print("Mapping Summary")
    print("=" * 60)
    print(f"Total Nodes:              {summary['total_nodes']}")
    print(f"Spatial Nodes:            {summary['spatial_nodes']}")
    print(f"Total Relationships:      {summary['total_relationships']}")
    print(f"FK Relationships:         {summary['fk_relationships']}")
    print(f"Spatial Relationships:    {summary['spatial_relationships']}")
    print(f"Total Properties:         {summary['total_properties']}")
    print()
    print("Node Labels:")
    for label in summary['node_labels']:
        print(f"  • {label}")
    print()

    # Show node details
    print("=" * 60)
    print("Node Details")
    print("=" * 60)
    for node in graph_schema.nodes:
        print(f"\n{node.label}:")
        print(f"  Source Table:      {node.source_table}")
        print(f"  Primary Property:  {node.primary_property}")
        print(f"  Has Geometry:      {node.has_geometry}")
        print(f"  Total Properties:  {len(node.properties)}")
        if node.has_geometry:
            spatial_props = [p.name for p in node.properties if 'center' in p.name or 'geometry' in p.name or 'bbox' in p.name or 'area' in p.name]
            print(f"  Spatial Props:     {', '.join(spatial_props[:5])}...")
    print()

    # Show relationship details
    print("=" * 60)
    print("Relationship Details")
    print("=" * 60)
    for rel in graph_schema.relationships:
        print(f"\n({rel.from_label})-[:{rel.type}]->({rel.to_label})")
        print(f"  Source Type:       {rel.source_type.value}")
        if rel.source_type.value == 'FK':
            print(f"  Source Table:      {rel.source_table}")
            print(f"  From Column:       {rel.from_column}")
            print(f"  To Column:         {rel.to_column}")
        elif rel.source_type.value == 'SPATIAL':
            print(f"  Bidirectional:     {rel.bidirectional}")
            print(f"  Properties:        {[p.name for p in rel.properties]}")
    print()

    # Generate Cypher DDL
    print("=" * 60)
    print("Generated Cypher DDL")
    print("=" * 60)
    print("\nConstraints:")
    constraints = CypherDDLGenerator.generate_all_constraints(graph_schema)
    for i, constraint in enumerate(constraints[:3], 1):
        print(f"\n{i}. {constraint}")

    print("\n\nIndexes:")
    indexes = CypherDDLGenerator.generate_all_indexes(graph_schema)
    for i, index in enumerate(indexes[:3], 1):
        print(f"\n{i}. {index}")
    print()

    # Export files
    print("=" * 60)
    print("Exporting Files")
    print("=" * 60)

    output_dir = Path("outputs/cypher")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export JSON
    json_file = output_dir / "graph_schema.json"
    mapper.export_schema(str(json_file))

    # Export YAML
    yaml_file = output_dir / "mapping_config.yaml"
    mapper.export_yaml_config(str(yaml_file))

    # Export Cypher DDL
    constraints_file = output_dir / "01_create_constraints.cypher"
    CypherDDLGenerator.export_constraints_script(graph_schema, str(constraints_file))

    indexes_file = output_dir / "02_create_indexes.cypher"
    CypherDDLGenerator.export_indexes_script(graph_schema, str(indexes_file))

    # Export post-migration script (Neo4j Point + spatial indexes)
    post_migration_file = output_dir / "03_post_migration_spatial.cypher"
    CypherDDLGenerator.export_post_migration_script(graph_schema, str(post_migration_file))

    print()
    print("=" * 60)
    print("Post-Migration Cypher (Neo4j Point + Spatial Index)")
    print("=" * 60)
    post_cypher = CypherDDLGenerator.generate_post_migration_cypher(graph_schema)
    for stmt in post_cypher:
        print(stmt.strip())
        print()

    print("=" * 60)
    print("✅ Test Complete!")
    print("=" * 60)
    print(f"\nAll files exported to: {output_dir}")
    print("\nNext steps:")
    print("  1. Review generated files in outputs/cypher/")
    print("  2. Verify spatial property generation")
    print("  3. Check NEIGHBORS relationship computation query")
    print("  4. Test with real NOAH database")


if __name__ == "__main__":
    main()
