#!/usr/bin/env python3
"""
POC: Load data from PostgreSQL to Neo4j using Python
This is simpler and more flexible than APOC JDBC
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from noah_converter.utils.config import load_config
from noah_converter.utils.db_connection import PostgreSQLConnection, Neo4jConnection
from sqlalchemy import text


def test_python_etl():
    """Test loading 1 housing project from PostgreSQL to Neo4j"""

    # Load config
    config = load_config()

    print("🔌 Connecting to PostgreSQL...")
    pg_conn = PostgreSQLConnection(config.source_db)

    print("🔌 Connecting to Neo4j...")
    neo4j_conn = Neo4jConnection(config.target_db)

    # Step 1: Read ONE housing project from PostgreSQL
    print("\n📖 Reading 1 housing project from PostgreSQL...")
    query = """
    SELECT
        project_id,
        project_name,
        borough,
        zipcode,
        street_address,
        latitude,
        longitude,
        total_units,
        affordable_units,
        completion_date
    FROM housing_projects
    LIMIT 1
    """

    with pg_conn.engine.connect() as conn:
        result = conn.execute(text(query))
        row = result.fetchone()

        if row:
            # Convert to dict
            project_data = {
                'projectId': row.project_id,
                'name': row.project_name,
                'borough': row.borough,
                'zipcode': row.zipcode,
                'address': row.street_address,
                'latitude': float(row.latitude) if row.latitude else None,
                'longitude': float(row.longitude) if row.longitude else None,
                'totalUnits': row.total_units,
                'affordableUnits': row.affordable_units,
                'completionDate': str(row.completion_date) if row.completion_date else None
            }

            print(f"✅ Found project: {project_data['name']}")
            print(f"   Location: {project_data['borough']}, ZIP {project_data['zipcode']}")
            print(f"   Units: {project_data['totalUnits']} total, {project_data['affordableUnits']} affordable")

            # Step 2: Write to Neo4j
            print("\n💾 Writing to Neo4j...")

            cypher = """
            CREATE (p:HousingProject {
                projectId: $projectId,
                name: $name,
                borough: $borough,
                zipcode: $zipcode,
                address: $address,
                latitude: $latitude,
                longitude: $longitude,
                totalUnits: $totalUnits,
                affordableUnits: $affordableUnits,
                completionDate: $completionDate
            })
            RETURN p.projectId as id, p.name as name
            """

            with neo4j_conn.driver.session() as session:
                result = session.run(cypher, **project_data)
                record = result.single()

                if record:
                    print(f"✅ Created node in Neo4j!")
                    print(f"   ID: {record['id']}")
                    print(f"   Name: {record['name']}")

            # Step 3: Verify
            print("\n🔍 Verifying in Neo4j...")
            verify_query = "MATCH (p:HousingProject) RETURN count(p) as count"

            with neo4j_conn.driver.session() as session:
                result = session.run(verify_query)
                count = result.single()['count']
                print(f"✅ Total HousingProject nodes in Neo4j: {count}")

            print("\n🎉 POC Success! Python ETL works perfectly!")
            print("\nThis proves we can:")
            print("  ✅ Read from PostgreSQL")
            print("  ✅ Transform data")
            print("  ✅ Write to Neo4j")
            print("  ✅ Verify results")

        else:
            print("❌ No data found in housing_projects table")

    # Cleanup
    pg_conn.close()
    neo4j_conn.close()


if __name__ == "__main__":
    test_python_etl()
