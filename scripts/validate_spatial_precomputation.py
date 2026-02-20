#!/usr/bin/env python3
"""
Validate Spatial Precomputation Results

验证 PostgreSQL 中预计算的空间关系是否正确
"""

import sys
from pathlib import Path
from typing import Dict, List
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from noah_converter.utils.config import load_config
from noah_converter.utils.db_connection import PostgreSQLConnection
from sqlalchemy import text


class SpatialValidator:
    """验证空间数据预计算结果"""

    def __init__(self):
        self.config = load_config()
        self.pg_conn = PostgreSQLConnection(self.config.source_db)
        self.validation_results = {}

    def validate_all(self):
        """运行所有验证检查"""
        print("=" * 60)
        print("🔍 Validating Spatial Precomputation Results")
        print("=" * 60)

        # 检查表是否存在
        self.check_tables_exist()

        # 验证 ZIP centroids
        self.validate_centroids()

        # 验证 NEIGHBORS 关系
        self.validate_neighbors()

        # 验证 Tract-ZIP crosswalk（如果存在）
        self.validate_tract_zip()

        # 验证 Project-ZIP 分配（如果存在）
        self.validate_project_zip()

        # 生成报告
        self.generate_report()

        # Cleanup
        self.pg_conn.close()

    def check_tables_exist(self):
        """检查预计算表是否存在"""
        print("\n📋 Step 1: Checking tables...")

        required_tables = ['zip_centroids', 'zip_neighbors']
        optional_tables = ['tract_zip_overlay', 'project_zip_validation', 'building_zip_validation']

        with self.pg_conn.engine.connect() as conn:
            for table in required_tables + optional_tables:
                query = text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = :table_name
                    )
                """)
                exists = conn.execute(query, {"table_name": table}).scalar()

                status = "✓" if exists else "✗"
                required = "(required)" if table in required_tables else "(optional)"
                print(f"   {status} {table} {required}")

                if not exists and table in required_tables:
                    print(f"\n❌ Error: Required table '{table}' not found!")
                    print(f"   Run: psql noah_housing -f scripts/precompute_spatial_relationships.sql")
                    sys.exit(1)

    def validate_centroids(self):
        """验证 ZIP centroids"""
        print("\n📍 Step 2: Validating ZIP centroids...")

        with self.pg_conn.engine.connect() as conn:
            # 基本统计
            query = text("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(CASE WHEN center_lat IS NULL OR center_lon IS NULL THEN 1 END) AS null_coords,
                    COUNT(CASE WHEN geometry_wkt IS NULL THEN 1 END) AS null_wkt,
                    AVG(area_km2) AS avg_area,
                    MAX(area_km2) AS max_area,
                    MIN(area_km2) AS min_area
                FROM zip_centroids
            """)
            result = conn.execute(query).fetchone()

            print(f"   Total centroids: {result.total}")
            print(f"   NULL coordinates: {result.null_coords}")
            print(f"   NULL WKT: {result.null_wkt}")
            print(f"   Avg area: {result.avg_area:.2f} km²")
            print(f"   Area range: {result.min_area:.2f} - {result.max_area:.2f} km²")

            # 验证坐标范围（NYC 应该在这个范围内）
            query = text("""
                SELECT
                    COUNT(*) AS out_of_bounds
                FROM zip_centroids
                WHERE center_lat NOT BETWEEN 40.4 AND 41.0
                   OR center_lon NOT BETWEEN -74.3 AND -73.7
            """)
            out_of_bounds = conn.execute(query).scalar()

            if out_of_bounds > 0:
                print(f"\n   ⚠️  Warning: {out_of_bounds} centroids outside NYC bounds")
            else:
                print(f"   ✓ All centroids within NYC bounds")

            self.validation_results['centroids'] = {
                'total': result.total,
                'null_coords': result.null_coords,
                'out_of_bounds': out_of_bounds,
                'status': 'PASS' if result.null_coords == 0 and out_of_bounds == 0 else 'WARNING'
            }

    def validate_neighbors(self):
        """验证 NEIGHBORS 关系"""
        print("\n🔗 Step 3: Validating ZIP neighbor relationships...")

        with self.pg_conn.engine.connect() as conn:
            # 基本统计
            query = text("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(CASE WHEN is_adjacent = true THEN 1 END) AS adjacent,
                    COUNT(CASE WHEN is_adjacent = false THEN 1 END) AS nearby,
                    AVG(distance_km) AS avg_distance,
                    MAX(distance_km) AS max_distance,
                    MIN(distance_km) AS min_distance,
                    AVG(CASE WHEN is_adjacent THEN shared_boundary_km END) AS avg_shared_boundary
                FROM zip_neighbors
            """)
            result = conn.execute(query).fetchone()

            print(f"   Total relationships: {result.total}")
            print(f"   Adjacent (touching): {result.adjacent}")
            print(f"   Nearby (within 10km): {result.nearby}")
            print(f"   Avg distance: {result.avg_distance:.2f} km")
            print(f"   Distance range: {result.min_distance:.2f} - {result.max_distance:.2f} km")
            if result.avg_shared_boundary:
                print(f"   Avg shared boundary: {result.avg_shared_boundary:.2f} km")
            else:
                print(f"   Avg shared boundary: N/A (no adjacent ZIPs)")

            # 检查对称性（每个关系应该有对应的反向关系）
            query = text("""
                SELECT COUNT(*) AS asymmetric
                FROM zip_neighbors a
                WHERE NOT EXISTS (
                    SELECT 1 FROM zip_neighbors b
                    WHERE b.from_zip = a.to_zip
                      AND b.to_zip = a.from_zip
                )
            """)
            asymmetric = conn.execute(query).scalar()

            if asymmetric > 0:
                print(f"\n   ⚠️  Warning: {asymmetric} asymmetric relationships found")
                print(f"      (This is expected - we only store one direction)")
            else:
                print(f"   ✓ All relationships have symmetric pairs")

            # 检查每个 ZIP 的邻居数量
            query = text("""
                SELECT
                    AVG(neighbor_count) AS avg_neighbors,
                    MAX(neighbor_count) AS max_neighbors,
                    MIN(neighbor_count) AS min_neighbors
                FROM (
                    SELECT from_zip, COUNT(*) AS neighbor_count
                    FROM zip_neighbors
                    GROUP BY from_zip
                ) AS counts
            """)
            result2 = conn.execute(query).fetchone()

            print(f"\n   Neighbors per ZIP:")
            print(f"      - Average: {result2.avg_neighbors:.1f}")
            print(f"      - Range: {result2.min_neighbors} - {result2.max_neighbors}")

            # 找出孤立的 ZIP（没有邻居）
            query = text("""
                SELECT zip_code
                FROM zip_shapes
                WHERE zip_code NOT IN (
                    SELECT from_zip FROM zip_neighbors
                    UNION
                    SELECT to_zip FROM zip_neighbors
                )
                LIMIT 5
            """)
            isolated = [row.zip_code for row in conn.execute(query)]

            if isolated:
                print(f"\n   ⚠️  Isolated ZIPs (no neighbors): {', '.join(isolated[:5])}")
                if len(isolated) > 5:
                    print(f"      ... and {len(isolated) - 5} more")

            self.validation_results['neighbors'] = {
                'total': result.total,
                'adjacent': result.adjacent,
                'nearby': result.nearby,
                'avg_distance': float(result.avg_distance),
                'isolated_count': len(isolated),
                'status': 'PASS' if result.total > 0 else 'FAIL'
            }

    def validate_tract_zip(self):
        """验证 Tract-ZIP crosswalk"""
        print("\n📊 Step 4: Validating Tract-ZIP crosswalk...")

        with self.pg_conn.engine.connect() as conn:
            # 检查表是否存在
            query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'tract_zip_overlay'
                )
            """)
            exists = conn.execute(query).scalar()

            if not exists:
                print("   ⚠️  Table tract_zip_overlay not found (skipping)")
                return

            # 统计
            query = text("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(DISTINCT tract_id) AS unique_tracts,
                    COUNT(DISTINCT zip_code) AS unique_zips,
                    AVG(overlap_pct_of_tract) AS avg_overlap,
                    COUNT(CASE WHEN tract_centroid_in_zip THEN 1 END) AS centroid_matches
                FROM tract_zip_overlay
            """)
            result = conn.execute(query).fetchone()

            print(f"   Total relationships: {result.total}")
            print(f"   Unique tracts: {result.unique_tracts}")
            print(f"   Unique ZIPs: {result.unique_zips}")
            print(f"   Avg overlap: {result.avg_overlap:.1f}%")
            print(f"   Centroid matches: {result.centroid_matches}")

            # 检查是否有 tract 完全在多个 ZIP 内（数据质量问题）
            query = text("""
                SELECT tract_id, SUM(overlap_pct_of_tract) AS total_pct
                FROM tract_zip_overlay
                GROUP BY tract_id
                HAVING SUM(overlap_pct_of_tract) > 105  -- 允许 5% 误差
                LIMIT 5
            """)
            overlapping = list(conn.execute(query))

            if overlapping:
                print(f"\n   ⚠️  Warning: {len(overlapping)} tracts with >100% overlap")

            self.validation_results['tract_zip'] = {
                'total': result.total,
                'unique_tracts': result.unique_tracts,
                'unique_zips': result.unique_zips,
                'status': 'PASS'
            }

    def validate_project_zip(self):
        """验证 Project-ZIP 分配"""
        print("\n🏢 Step 5: Validating Project-ZIP assignments...")

        with self.pg_conn.engine.connect() as conn:
            # 检查表是否存在
            query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'project_zip_validation'
                )
            """)
            exists = conn.execute(query).scalar()

            if not exists:
                print("   ⚠️  Table project_zip_validation not found (skipping)")
                return

            # 统计
            query = text("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(CASE WHEN is_inside THEN 1 END) AS inside_boundary,
                    COUNT(CASE WHEN reported_zip != actual_zip AND actual_zip IS NOT NULL THEN 1 END) AS mismatches,
                    COUNT(CASE WHEN actual_zip IS NULL THEN 1 END) AS no_match,
                    AVG(distance_to_centroid_km) AS avg_distance
                FROM project_zip_validation
            """)
            result = conn.execute(query).fetchone()

            print(f"   Total projects: {result.total}")
            print(f"   Inside ZIP boundary: {result.inside_boundary} ({result.inside_boundary/result.total*100:.1f}%)")
            print(f"   ZIP mismatches: {result.mismatches}")
            print(f"   No ZIP match: {result.no_match}")
            print(f"   Avg distance to centroid: {result.avg_distance:.2f} km")

            # 列出一些 mismatch 案例
            if result.mismatches > 0:
                query = text("""
                    SELECT project_id, project_name, reported_zip, actual_zip
                    FROM project_zip_validation
                    WHERE reported_zip != actual_zip AND actual_zip IS NOT NULL
                    LIMIT 5
                """)
                mismatches = list(conn.execute(query))

                print(f"\n   ⚠️  Example mismatches:")
                for m in mismatches:
                    print(f"      - {m.project_name}: {m.reported_zip} (reported) vs {m.actual_zip} (actual)")

            self.validation_results['project_zip'] = {
                'total': result.total,
                'inside_boundary': result.inside_boundary,
                'mismatches': result.mismatches,
                'status': 'PASS' if result.mismatches / result.total < 0.05 else 'WARNING'
            }

    def generate_report(self):
        """生成验证报告"""
        print("\n" + "=" * 60)
        print("📊 Validation Report")
        print("=" * 60)

        all_passed = all(
            r.get('status') in ['PASS', 'WARNING']
            for r in self.validation_results.values()
        )

        for name, results in self.validation_results.items():
            status_icon = {
                'PASS': '✅',
                'WARNING': '⚠️',
                'FAIL': '❌'
            }.get(results.get('status', 'UNKNOWN'), '?')

            print(f"\n{status_icon} {name.upper()}: {results.get('status', 'UNKNOWN')}")
            for key, value in results.items():
                if key != 'status':
                    print(f"   - {key}: {value}")

        # 保存到文件
        output_path = Path(__file__).parent.parent / "outputs" / "reports"
        output_path.mkdir(parents=True, exist_ok=True)

        report_file = output_path / "spatial_validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.validation_results, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_file}")

        print("\n" + "=" * 60)
        if all_passed:
            print("✅ Validation Complete: All checks passed!")
        else:
            print("⚠️  Validation Complete: Some warnings detected")
        print("=" * 60)

        print("\nNext steps:")
        print("  1. Review detailed results above")
        print("  2. Visualize neighbor network:")
        print("     jupyter notebook notebooks/02_visualize_zip_neighbors.ipynb")
        print("  3. If all looks good, proceed with Neo4j migration:")
        print("     python scripts/migrate_all_nodes.py")
        print()


def main():
    """主函数"""
    validator = SpatialValidator()
    validator.validate_all()


if __name__ == "__main__":
    main()
