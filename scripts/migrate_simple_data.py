#!/usr/bin/env python3
"""
Complete Migration Script: PostgreSQL → Neo4j
Migrates all simplified NOAH data (20 projects, 16 ZIPs, 4 boroughs)
"""

import sys
from pathlib import Path
from typing import List, Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from noah_converter.utils.config import load_config
from noah_converter.utils.db_connection import PostgreSQLConnection, Neo4jConnection
from sqlalchemy import text


class SimpleDataMigrator:
    """Migrator for simplified NOAH data"""

    def __init__(self):
        self.config = load_config()
        self.pg_conn = PostgreSQLConnection(self.config.source_db)
        self.neo4j_conn = Neo4jConnection(self.config.target_db)

    def migrate_all(self):
        """Run complete migration pipeline"""
        print("=" * 60)
        print("🚀 NOAH Simple Data Migration")
        print("=" * 60)

        # Step 0: Clear Neo4j
        self.clear_neo4j()

        # Step 1: Migrate Boroughs
        self.migrate_boroughs()

        # Step 2: Migrate ZIP Codes
        self.migrate_zipcodes()

        # Step 3: Migrate Housing Projects
        self.migrate_housing_projects()

        # Step 4: Create Relationships
        self.create_relationships()

        # Step 5: Validate
        self.validate()

        print("\n" + "=" * 60)
        print("✅ Migration Complete!")
        print("=" * 60)

        # Cleanup
        self.pg_conn.close()
        self.neo4j_conn.close()

    def clear_neo4j(self):
        """Clear all data from Neo4j"""
        print("\n🧹 Step 0: Clearing Neo4j database...")

        with self.neo4j_conn.driver.session() as session:
            # Delete all nodes and relationships
            session.run("MATCH (n) DETACH DELETE n")
            print("   ✓ Cleared all existing data")

    def migrate_boroughs(self):
        """Migrate borough data to Neo4j"""
        print("\n📍 Step 1: Migrating Boroughs...")

        # Read from PostgreSQL
        query = """
        SELECT
            borough,
            total_zipcodes,
            total_projects,
            total_units,
            total_affordable_units
        FROM borough_summary
        ORDER BY borough
        """

        with self.pg_conn.engine.connect() as conn:
            result = conn.execute(text(query))
            boroughs = []
            for row in result:
                row_dict = dict(row._mapping)
                # Convert Decimal to float/int
                for key, value in row_dict.items():
                    if hasattr(value, '__float__'):
                        row_dict[key] = float(value) if '.' in str(value) else int(value)
                boroughs.append(row_dict)

        print(f"   📖 Read {len(boroughs)} boroughs from PostgreSQL")

        # Write to Neo4j
        cypher = """
        UNWIND $boroughs AS borough
        CREATE (b:Borough {
            name: borough.borough,
            totalZipcodes: borough.total_zipcodes,
            totalProjects: borough.total_projects,
            totalUnits: borough.total_units,
            totalAffordableUnits: borough.total_affordable_units
        })
        """

        with self.neo4j_conn.driver.session() as session:
            session.run(cypher, boroughs=boroughs)

        print(f"   ✓ Created {len(boroughs)} Borough nodes")
        for b in boroughs:
            print(f"      - {b['borough']}: {b['total_projects']} projects")

    def migrate_zipcodes(self):
        """Migrate ZIP code data to Neo4j"""
        print("\n📮 Step 2: Migrating ZIP Codes...")

        # Read from PostgreSQL
        query = """
        SELECT
            zipcode,
            borough,
            total_projects,
            total_units,
            total_affordable_units,
            avg_units_per_project,
            center_lat,
            center_lon
        FROM zip_summary
        ORDER BY zipcode
        """

        with self.pg_conn.engine.connect() as conn:
            result = conn.execute(text(query))
            zipcodes = []
            for row in result:
                row_dict = dict(row._mapping)
                # Convert Decimal to float
                for key, value in row_dict.items():
                    if hasattr(value, '__float__'):  # Decimal has __float__
                        row_dict[key] = float(value)
                zipcodes.append(row_dict)

        print(f"   📖 Read {len(zipcodes)} ZIP codes from PostgreSQL")

        # Write to Neo4j
        cypher = """
        UNWIND $zipcodes AS zip
        CREATE (z:Zipcode {
            zipcode: zip.zipcode,
            borough: zip.borough,
            totalProjects: zip.total_projects,
            totalUnits: zip.total_units,
            totalAffordableUnits: zip.total_affordable_units,
            avgUnitsPerProject: zip.avg_units_per_project,
            centerLat: zip.center_lat,
            centerLon: zip.center_lon
        })
        """

        with self.neo4j_conn.driver.session() as session:
            session.run(cypher, zipcodes=zipcodes)

        print(f"   ✓ Created {len(zipcodes)} Zipcode nodes")

    def migrate_housing_projects(self):
        """Migrate housing project data to Neo4j"""
        print("\n🏢 Step 3: Migrating Housing Projects...")

        # Read from PostgreSQL
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
        ORDER BY project_id
        """

        with self.pg_conn.engine.connect() as conn:
            result = conn.execute(text(query))
            projects = []
            for row in result:
                row_dict = dict(row._mapping)
                # Convert date to string
                if row_dict.get('completion_date'):
                    row_dict['completion_date'] = str(row_dict['completion_date'])
                # Convert Decimal to float
                for key, value in row_dict.items():
                    if hasattr(value, '__float__') and key != 'completion_date':
                        row_dict[key] = float(value)
                projects.append(row_dict)

        print(f"   📖 Read {len(projects)} housing projects from PostgreSQL")

        # Write to Neo4j in batches
        cypher = """
        UNWIND $projects AS project
        CREATE (p:HousingProject {
            projectId: project.project_id,
            name: project.project_name,
            borough: project.borough,
            zipcode: project.zipcode,
            address: project.street_address,
            latitude: project.latitude,
            longitude: project.longitude,
            totalUnits: project.total_units,
            affordableUnits: project.affordable_units,
            completionDate: project.completion_date
        })
        """

        with self.neo4j_conn.driver.session() as session:
            session.run(cypher, projects=projects)

        print(f"   ✓ Created {len(projects)} HousingProject nodes")

        # Show summary by borough
        by_borough = {}
        for p in projects:
            borough = p['borough']
            by_borough[borough] = by_borough.get(borough, 0) + 1

        for borough, count in sorted(by_borough.items()):
            print(f"      - {borough}: {count} projects")

    def create_relationships(self):
        """Create relationships between nodes"""
        print("\n🔗 Step 4: Creating Relationships...")

        with self.neo4j_conn.driver.session() as session:
            # Relationship 1: HousingProject -[:LOCATED_IN]-> Zipcode
            result = session.run("""
                MATCH (p:HousingProject)
                MATCH (z:Zipcode {zipcode: p.zipcode})
                CREATE (p)-[:LOCATED_IN]->(z)
                RETURN count(*) as count
            """)
            count = result.single()['count']
            print(f"   ✓ Created {count} LOCATED_IN relationships (Project → ZIP)")

            # Relationship 2: Zipcode -[:PART_OF]-> Borough
            result = session.run("""
                MATCH (z:Zipcode)
                MATCH (b:Borough {name: z.borough})
                CREATE (z)-[:PART_OF]->(b)
                RETURN count(*) as count
            """)
            count = result.single()['count']
            print(f"   ✓ Created {count} PART_OF relationships (ZIP → Borough)")

    def validate(self):
        """Validate migration results"""
        print("\n✅ Step 5: Validating Migration...")

        # Check PostgreSQL counts
        with self.pg_conn.engine.connect() as conn:
            pg_projects = conn.execute(text("SELECT COUNT(*) FROM housing_projects")).scalar()
            pg_zips = conn.execute(text("SELECT COUNT(*) FROM zip_summary")).scalar()
            pg_boroughs = conn.execute(text("SELECT COUNT(*) FROM borough_summary")).scalar()

        # Check Neo4j counts
        with self.neo4j_conn.driver.session() as session:
            result = session.run("""
                MATCH (p:HousingProject) WITH count(p) as projects
                MATCH (z:Zipcode) WITH projects, count(z) as zips
                MATCH (b:Borough) WITH projects, zips, count(b) as boroughs
                MATCH ()-[r:LOCATED_IN]->() WITH projects, zips, boroughs, count(r) as located_in
                MATCH ()-[r2:PART_OF]->() WITH projects, zips, boroughs, located_in, count(r2) as part_of
                RETURN projects, zips, boroughs, located_in, part_of
            """).single()

            neo4j_projects = result['projects']
            neo4j_zips = result['zips']
            neo4j_boroughs = result['boroughs']
            neo4j_located_in = result['located_in']
            neo4j_part_of = result['part_of']

        # Validation checks
        print("\n   📊 Validation Results:")
        print("   " + "-" * 56)
        print(f"   {'Entity':<25} {'PostgreSQL':<15} {'Neo4j':<15}")
        print("   " + "-" * 56)

        # Housing Projects
        status = "✅" if pg_projects == neo4j_projects else "❌"
        print(f"   {status} {'Housing Projects':<23} {pg_projects:<15} {neo4j_projects:<15}")

        # ZIP Codes
        status = "✅" if pg_zips == neo4j_zips else "❌"
        print(f"   {status} {'ZIP Codes':<23} {pg_zips:<15} {neo4j_zips:<15}")

        # Boroughs
        status = "✅" if pg_boroughs == neo4j_boroughs else "❌"
        print(f"   {status} {'Boroughs':<23} {pg_boroughs:<15} {neo4j_boroughs:<15}")

        print("   " + "-" * 56)

        # Relationships
        print(f"\n   🔗 Relationships Created:")
        print(f"      - LOCATED_IN (Project → ZIP): {neo4j_located_in}")
        print(f"      - PART_OF (ZIP → Borough): {neo4j_part_of}")

        # Calculate percentages
        if pg_projects > 0:
            coverage = (neo4j_located_in / pg_projects) * 100
            print(f"      - Coverage: {coverage:.1f}% of projects linked to ZIPs")

        # Final verdict
        all_match = (
            pg_projects == neo4j_projects and
            pg_zips == neo4j_zips and
            pg_boroughs == neo4j_boroughs
        )

        if all_match:
            print("\n   🎉 SUCCESS! All data migrated correctly!")
        else:
            print("\n   ⚠️  WARNING: Some counts don't match!")

        # Show graph stats
        print(f"\n   📈 Final Graph Statistics:")
        total_nodes = neo4j_projects + neo4j_zips + neo4j_boroughs
        total_rels = neo4j_located_in + neo4j_part_of
        print(f"      - Total Nodes: {total_nodes}")
        print(f"      - Total Relationships: {total_rels}")
        print(f"      - Graph Density: {total_rels / total_nodes:.2f} edges/node")


def main():
    """Main entry point"""
    migrator = SimpleDataMigrator()
    migrator.migrate_all()

    print("\n" + "=" * 60)
    print("Next steps:")
    print("  1. Open Neo4j Browser: http://localhost:7474")
    print("  2. Run: MATCH (n) RETURN n LIMIT 100")
    print("  3. Test Text2Cypher queries")
    print("=" * 60)


if __name__ == "__main__":
    main()
