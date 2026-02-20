#!/usr/bin/env python3
"""
Complete Migration: PostgreSQL → Neo4j with Spatial Data

迁移所有数据到 Neo4j，包括：
1. Zipcode 节点（使用 Neo4j Point 类型）
2. HousingProject 节点（使用 Neo4j Point 类型）
3. NEIGHBORS 关系（空间邻接）
4. LOCATED_IN 关系
5. 索引和约束
"""

import sys
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from noah_converter.utils.config import load_config
from noah_converter.utils.db_connection import PostgreSQLConnection, Neo4jConnection
from sqlalchemy import text


class SpatialMigrator:
    """完整的空间数据迁移器"""

    def __init__(self):
        self.config = load_config()
        self.pg_conn = PostgreSQLConnection(self.config.source_db)
        self.neo4j_conn = Neo4jConnection(self.config.target_db)
        self.stats = {
            'zipcodes': 0,
            'projects': 0,
            'neighbors': 0,
            'located_in': 0
        }

    def migrate_all(self):
        """运行完整迁移流程"""
        print("=" * 70)
        print("🚀 Complete PostgreSQL → Neo4j Migration with Spatial Data")
        print("=" * 70)

        start_time = datetime.now()

        # Step 0: 清空 Neo4j
        self.clear_neo4j()

        # Step 1: 创建约束和索引
        self.create_constraints_and_indexes()

        # Step 2: 迁移 Zipcode 节点
        self.migrate_zipcodes()

        # Step 3: 迁移 HousingProject 节点
        self.migrate_housing_projects()

        # Step 4: 创建 NEIGHBORS 关系
        self.create_neighbors_relationships()

        # Step 5: 创建 LOCATED_IN 关系
        self.create_located_in_relationships()

        # Step 6: 验证
        self.validate_migration()

        # 计算耗时
        elapsed = datetime.now() - start_time

        print("\n" + "=" * 70)
        print(f"✅ Migration Complete! (took {elapsed.total_seconds():.2f}s)")
        print("=" * 70)

        # 清理
        self.pg_conn.close()
        self.neo4j_conn.close()

    def clear_neo4j(self):
        """清空 Neo4j 数据库"""
        print("\n🧹 Step 0: Clearing Neo4j database...")

        with self.neo4j_conn.driver.session() as session:
            # 删除所有节点和关系
            result = session.run("MATCH (n) DETACH DELETE n RETURN count(n) as deleted")
            deleted = result.single()['deleted']
            print(f"   ✓ Deleted {deleted} existing nodes")

    def create_constraints_and_indexes(self):
        """创建约束和索引"""
        print("\n🔧 Step 1: Creating constraints and indexes...")

        with self.neo4j_conn.driver.session() as session:
            # 唯一性约束（自动创建索引）
            constraints = [
                "CREATE CONSTRAINT zipcode_unique IF NOT EXISTS FOR (z:Zipcode) REQUIRE z.zipcode IS UNIQUE",
                "CREATE CONSTRAINT project_unique IF NOT EXISTS FOR (p:HousingProject) REQUIRE p.projectId IS UNIQUE"
            ]

            for constraint in constraints:
                session.run(constraint)
                print(f"   ✓ {constraint.split('FOR')[1].split('REQUIRE')[0].strip()}")

            # 空间索引（Neo4j Point 类型）
            spatial_indexes = [
                "CREATE POINT INDEX zipcode_location IF NOT EXISTS FOR (z:Zipcode) ON (z.location)",
                "CREATE POINT INDEX project_location IF NOT EXISTS FOR (p:HousingProject) ON (p.location)"
            ]

            for index in spatial_indexes:
                session.run(index)
                print(f"   ✓ Spatial index: {index.split('FOR')[1].split('ON')[0].strip()}")

            # 常规索引
            regular_indexes = [
                "CREATE INDEX zipcode_borough IF NOT EXISTS FOR (z:Zipcode) ON (z.borough)",
                "CREATE INDEX project_zipcode IF NOT EXISTS FOR (p:HousingProject) ON (p.zipcode)"
            ]

            for index in regular_indexes:
                session.run(index)
                print(f"   ✓ {index.split('FOR')[1].split('ON')[0].strip()}")

    def migrate_zipcodes(self):
        """迁移 Zipcode 节点（使用 Neo4j Point 类型）"""
        print("\n📍 Step 2: Migrating Zipcode nodes...")

        # 从 PostgreSQL 读取数据
        query = """
        SELECT
            zc.zip_code,
            zc.center_lat,
            zc.center_lon,
            zc.geometry_wkt,
            zc.area_km2,
            zc.perimeter_km,
            zs.borough
        FROM zip_centroids zc
        LEFT JOIN zip_shapes zs ON zc.zip_code = zs.zip_code
        ORDER BY zc.zip_code
        """

        with self.pg_conn.engine.connect() as conn:
            result = conn.execute(text(query))
            zipcodes = []
            for row in result:
                row_dict = dict(row._mapping)
                # 转换 Decimal 到 float
                for key, value in row_dict.items():
                    if hasattr(value, '__float__'):
                        row_dict[key] = float(value)
                zipcodes.append(row_dict)

        print(f"   📖 Read {len(zipcodes)} ZIP codes from PostgreSQL")

        # 写入 Neo4j（使用 Neo4j Point 类型）
        cypher = """
        UNWIND $zipcodes AS zip
        CREATE (z:Zipcode {
            zipcode: zip.zip_code,
            borough: zip.borough,

            // Neo4j Point 类型（核心！）
            location: point({
                latitude: zip.center_lat,
                longitude: zip.center_lon,
                crs: 'WGS-84'
            }),

            // 保留原始坐标（供兼容）
            centerLat: zip.center_lat,
            centerLon: zip.center_lon,

            // 几何信息
            geometryWKT: zip.geometry_wkt,
            areaKm2: zip.area_km2,
            perimeterKm: zip.perimeter_km
        })
        """

        with self.neo4j_conn.driver.session() as session:
            session.run(cypher, zipcodes=zipcodes)

        self.stats['zipcodes'] = len(zipcodes)
        print(f"   ✓ Created {len(zipcodes)} Zipcode nodes with Neo4j Point type")

    def migrate_housing_projects(self):
        """迁移 HousingProject 节点（使用 Neo4j Point 类型）"""
        print("\n🏢 Step 3: Migrating HousingProject nodes...")

        # 从 PostgreSQL 读取数据
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
                # 转换日期为字符串
                if row_dict.get('completion_date'):
                    row_dict['completion_date'] = str(row_dict['completion_date'])
                # 转换 Decimal 到 float
                for key, value in row_dict.items():
                    if hasattr(value, '__float__') and key != 'completion_date':
                        row_dict[key] = float(value)
                projects.append(row_dict)

        print(f"   📖 Read {len(projects)} housing projects from PostgreSQL")

        # 写入 Neo4j（使用 Neo4j Point 类型）
        cypher = """
        UNWIND $projects AS project
        CREATE (p:HousingProject {
            projectId: project.project_id,
            name: project.project_name,
            borough: project.borough,
            zipcode: project.zipcode,
            address: project.street_address,

            // Neo4j Point 类型（核心！）
            location: point({
                latitude: project.latitude,
                longitude: project.longitude,
                crs: 'WGS-84'
            }),

            // 保留原始坐标
            latitude: project.latitude,
            longitude: project.longitude,

            // 其他属性
            totalUnits: project.total_units,
            affordableUnits: project.affordable_units,
            completionDate: project.completion_date
        })
        """

        with self.neo4j_conn.driver.session() as session:
            session.run(cypher, projects=projects)

        self.stats['projects'] = len(projects)
        print(f"   ✓ Created {len(projects)} HousingProject nodes with Neo4j Point type")

    def create_neighbors_relationships(self):
        """创建 NEIGHBORS 关系（双向）"""
        print("\n🔗 Step 4: Creating NEIGHBORS relationships...")

        # 从 PostgreSQL 读取邻接关系
        query = """
        SELECT
            from_zip,
            to_zip,
            distance_km,
            is_adjacent,
            shared_boundary_km
        FROM zip_neighbors
        ORDER BY from_zip, to_zip
        """

        with self.pg_conn.engine.connect() as conn:
            result = conn.execute(text(query))
            neighbors = []
            for row in result:
                row_dict = dict(row._mapping)
                # 转换 Decimal 到 float
                for key, value in row_dict.items():
                    if hasattr(value, '__float__'):
                        row_dict[key] = float(value)
                neighbors.append(row_dict)

        print(f"   📖 Read {len(neighbors)} neighbor relationships from PostgreSQL")

        # 创建双向关系
        cypher = """
        UNWIND $neighbors AS n
        MATCH (a:Zipcode {zipcode: n.from_zip})
        MATCH (b:Zipcode {zipcode: n.to_zip})

        // 创建双向关系
        CREATE (a)-[:NEIGHBORS {
            distanceKm: n.distance_km,
            isAdjacent: n.is_adjacent,
            sharedBoundaryKm: n.shared_boundary_km
        }]->(b)

        CREATE (b)-[:NEIGHBORS {
            distanceKm: n.distance_km,
            isAdjacent: n.is_adjacent,
            sharedBoundaryKm: n.shared_boundary_km
        }]->(a)
        """

        with self.neo4j_conn.driver.session() as session:
            session.run(cypher, neighbors=neighbors)

        # 每个关系变成双向，所以总数翻倍
        total_relationships = len(neighbors) * 2
        self.stats['neighbors'] = total_relationships

        print(f"   ✓ Created {total_relationships} NEIGHBORS relationships (bidirectional)")
        print(f"      - Original pairs: {len(neighbors)}")
        print(f"      - Each pair → 2 directed edges")

    def create_located_in_relationships(self):
        """创建 LOCATED_IN 关系"""
        print("\n🏘️  Step 5: Creating LOCATED_IN relationships...")

        with self.neo4j_conn.driver.session() as session:
            # HousingProject → Zipcode
            cypher = """
            MATCH (p:HousingProject)
            MATCH (z:Zipcode {zipcode: p.zipcode})
            CREATE (p)-[:LOCATED_IN]->(z)
            """
            result = session.run(cypher)
            summary = result.consume()
            located_in_count = summary.counters.relationships_created

            self.stats['located_in'] = located_in_count
            print(f"   ✓ Created {located_in_count} LOCATED_IN relationships")

    def validate_migration(self):
        """验证迁移结果"""
        print("\n✅ Step 6: Validating migration...")

        # PostgreSQL 计数
        with self.pg_conn.engine.connect() as conn:
            pg_zips = conn.execute(text("SELECT COUNT(*) FROM zip_centroids")).scalar()
            pg_projects = conn.execute(text("SELECT COUNT(*) FROM housing_projects")).scalar()
            pg_neighbors = conn.execute(text("SELECT COUNT(*) FROM zip_neighbors")).scalar()

        # Neo4j 计数
        with self.neo4j_conn.driver.session() as session:
            result = session.run("""
                MATCH (z:Zipcode) WITH count(z) as zips
                MATCH (p:HousingProject) WITH zips, count(p) as projects
                MATCH ()-[n:NEIGHBORS]->() WITH zips, projects, count(n) as neighbors
                MATCH ()-[l:LOCATED_IN]->() WITH zips, projects, neighbors, count(l) as located_in
                RETURN zips, projects, neighbors, located_in
            """).single()

            neo4j_zips = result['zips']
            neo4j_projects = result['projects']
            neo4j_neighbors = result['neighbors']
            neo4j_located_in = result['located_in']

        # 打印对比表格
        print("\n   📊 Validation Results:")
        print("   " + "-" * 66)
        print(f"   {'Entity':<30} {'PostgreSQL':<15} {'Neo4j':<15} {'Status':<6}")
        print("   " + "-" * 66)

        # Zipcodes
        status = "✅" if pg_zips == neo4j_zips else "❌"
        print(f"   {status} {'Zipcode nodes':<28} {pg_zips:<15} {neo4j_zips:<15}")

        # Projects
        status = "✅" if pg_projects == neo4j_projects else "❌"
        print(f"   {status} {'HousingProject nodes':<28} {pg_projects:<15} {neo4j_projects:<15}")

        # Neighbors (注意：Neo4j 是双向的，所以应该是 PostgreSQL 的 2 倍)
        expected_neighbors = pg_neighbors * 2
        status = "✅" if neo4j_neighbors == expected_neighbors else "❌"
        print(f"   {status} {'NEIGHBORS relationships':<28} {pg_neighbors} (pairs){' ':<4} {neo4j_neighbors:<15}")

        # Located_in
        status = "✅" if neo4j_located_in == pg_projects else "❌"
        print(f"   {status} {'LOCATED_IN relationships':<28} {pg_projects:<15} {neo4j_located_in:<15}")

        print("   " + "-" * 66)

        # 最终判断
        all_match = (
            pg_zips == neo4j_zips and
            pg_projects == neo4j_projects and
            neo4j_neighbors == expected_neighbors and
            neo4j_located_in == pg_projects
        )

        if all_match:
            print("\n   🎉 SUCCESS! All data migrated correctly!")
        else:
            print("\n   ⚠️  WARNING: Some counts don't match!")

        # 显示图统计
        print(f"\n   📈 Neo4j Graph Statistics:")
        total_nodes = neo4j_zips + neo4j_projects
        total_rels = neo4j_neighbors + neo4j_located_in
        print(f"      - Total Nodes: {total_nodes}")
        print(f"      - Total Relationships: {total_rels}")
        print(f"      - Graph Density: {total_rels / total_nodes:.2f} edges/node")

        # 测试 Neo4j Point 类型
        print(f"\n   🗺️  Testing Neo4j Point type queries...")
        with self.neo4j_conn.driver.session() as session:
            # 测试距离查询
            result = session.run("""
                MATCH (z1:Zipcode {zipcode: '10001'})
                MATCH (z2:Zipcode)
                WHERE z1 <> z2
                WITH z1, z2, point.distance(z1.location, z2.location) / 1000.0 AS distanceKm
                RETURN z2.zipcode AS zipcode, distanceKm
                ORDER BY distanceKm
                LIMIT 5
            """)

            print(f"      Top 5 nearest ZIPs to 10001:")
            for record in result:
                print(f"         - {record['zipcode']}: {record['distanceKm']:.2f} km")


def main():
    """主函数"""
    migrator = SpatialMigrator()
    migrator.migrate_all()

    print("\n" + "=" * 70)
    print("Next steps:")
    print("  1. Open Neo4j Browser: http://localhost:7474")
    print("  2. Test spatial query:")
    print("     MATCH (z:Zipcode {zipcode: '10001'})-[:NEIGHBORS]-(neighbor)")
    print("     RETURN neighbor.zipcode, neighbor.borough")
    print("  3. Test distance query:")
    print("     MATCH (z1:Zipcode), (z2:Zipcode)")
    print("     WHERE point.distance(z1.location, z2.location) < 5000")
    print("     RETURN z1.zipcode, z2.zipcode")
    print("=" * 70)


if __name__ == "__main__":
    main()
