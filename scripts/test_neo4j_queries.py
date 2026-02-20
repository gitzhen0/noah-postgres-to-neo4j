#!/usr/bin/env python3
"""
Test Neo4j Queries - Demonstrate Graph Advantages

测试 Neo4j 图查询，展示相对于 SQL 的优势
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from noah_converter.utils.config import load_config
from noah_converter.utils.db_connection import Neo4jConnection

print("=" * 70)
print("🧪 Testing Neo4j Graph Queries")
print("=" * 70)

config = load_config()
neo4j_conn = Neo4jConnection(config.target_db)

# ============================================================
# Query 1: 找到 ZIP 10001 的所有邻居
# ============================================================
print("\n📍 Query 1: Find all neighbors of ZIP 10001")
print("-" * 70)

cypher = """
MATCH (z:Zipcode {zipcode: '10001'})-[n:NEIGHBORS]-(neighbor)
RETURN neighbor.zipcode AS zipcode,
       neighbor.borough AS borough,
       n.distanceKm AS distanceKm,
       n.isAdjacent AS isAdjacent
ORDER BY n.distanceKm
LIMIT 10
"""

with neo4j_conn.driver.session() as session:
    result = session.run(cypher)
    print(f"\n{'ZIP Code':<10} {'Borough':<15} {'Distance (km)':<15} {'Adjacent':<10}")
    print("-" * 70)
    for record in result:
        adjacent = "Yes" if record['isAdjacent'] else "No"
        print(f"{record['zipcode']:<10} {record['borough']:<15} {record['distanceKm']:<15.2f} {adjacent:<10}")

# ============================================================
# Query 2: 使用 Neo4j Point 距离查询
# ============================================================
print("\n\n🗺️  Query 2: Find ZIPs within 5km using Neo4j Point distance")
print("-" * 70)

cypher = """
MATCH (center:Zipcode {zipcode: '10001'})
MATCH (other:Zipcode)
WHERE center <> other
WITH center, other, point.distance(center.location, other.location) / 1000.0 AS distanceKm
WHERE distanceKm < 5.0
RETURN other.zipcode AS zipcode,
       other.borough AS borough,
       distanceKm
ORDER BY distanceKm
"""

with neo4j_conn.driver.session() as session:
    result = session.run(cypher)
    print(f"\n{'ZIP Code':<10} {'Borough':<15} {'Distance (km)':<15}")
    print("-" * 70)
    for record in result:
        print(f"{record['zipcode']:<10} {record['borough']:<15} {record['distanceKm']:<15.2f}")

# ============================================================
# Query 3: Multi-hop 邻居查询（2-hop）
# ============================================================
print("\n\n🔗 Query 3: Find ZIPs within 2 hops of 10001")
print("-" * 70)

cypher = """
MATCH path = (start:Zipcode {zipcode: '10001'})-[:NEIGHBORS*1..2]-(end:Zipcode)
WITH DISTINCT end, min(length(path)) AS hops
RETURN end.zipcode AS zipcode,
       end.borough AS borough,
       hops
ORDER BY hops, end.zipcode
"""

with neo4j_conn.driver.session() as session:
    result = session.run(cypher)
    print(f"\n{'ZIP Code':<10} {'Borough':<15} {'Hops':<10}")
    print("-" * 70)

    hop1_count = 0
    hop2_count = 0
    for record in result:
        print(f"{record['zipcode']:<10} {record['borough']:<15} {record['hops']:<10}")
        if record['hops'] == 1:
            hop1_count += 1
        else:
            hop2_count += 1

    print(f"\nSummary: {hop1_count} ZIPs at 1-hop, {hop2_count} ZIPs at 2-hops")

# ============================================================
# Query 4: 找到某个 ZIP 内的所有住房项目
# ============================================================
print("\n\n🏘️  Query 4: Find all housing projects in ZIP 11106")
print("-" * 70)

cypher = """
MATCH (p:HousingProject)-[:LOCATED_IN]->(z:Zipcode {zipcode: '11106'})
RETURN p.name AS projectName,
       p.address AS address,
       p.totalUnits AS totalUnits,
       p.affordableUnits AS affordableUnits
ORDER BY p.totalUnits DESC
"""

with neo4j_conn.driver.session() as session:
    result = session.run(cypher)
    print(f"\n{'Project Name':<30} {'Total Units':<12} {'Affordable':<12}")
    print("-" * 70)
    total_projects = 0
    total_units = 0
    total_affordable = 0

    for record in result:
        print(f"{record['projectName'][:28]:<30} {record['totalUnits']:<12} {record['affordableUnits']:<12}")
        total_projects += 1
        total_units += record['totalUnits']
        total_affordable += record['affordableUnits']

    if total_projects > 0:
        print(f"\nSummary: {total_projects} projects, {total_units} total units, {total_affordable} affordable units")
    else:
        print("\nNo projects found in this ZIP")

# ============================================================
# Query 5: 找到邻近 ZIP 的项目（Graph Traversal）
# ============================================================
print("\n\n🌐 Query 5: Find projects in ZIPs neighboring 10001")
print("-" * 70)

cypher = """
MATCH (start:Zipcode {zipcode: '10001'})-[:NEIGHBORS]-(neighbor:Zipcode)
MATCH (p:HousingProject)-[:LOCATED_IN]->(neighbor)
RETURN neighbor.zipcode AS zipcode,
       count(p) AS projectCount,
       sum(p.totalUnits) AS totalUnits,
       sum(p.affordableUnits) AS affordableUnits
ORDER BY projectCount DESC
"""

with neo4j_conn.driver.session() as session:
    result = session.run(cypher)
    print(f"\n{'Neighbor ZIP':<12} {'Projects':<10} {'Total Units':<12} {'Affordable':<12}")
    print("-" * 70)

    for record in result:
        print(f"{record['zipcode']:<12} {record['projectCount']:<10} {record['totalUnits']:<12} {record['affordableUnits']:<12}")

# ============================================================
# Query 6: 图统计
# ============================================================
print("\n\n📊 Query 6: Graph Statistics")
print("-" * 70)

cypher = """
MATCH (z:Zipcode)
WITH count(z) AS zipCount
MATCH (p:HousingProject)
WITH zipCount, count(p) AS projectCount
MATCH ()-[n:NEIGHBORS]->()
WITH zipCount, projectCount, count(n) AS neighborCount
MATCH ()-[l:LOCATED_IN]->()
RETURN zipCount, projectCount, neighborCount, count(l) AS locatedInCount
"""

with neo4j_conn.driver.session() as session:
    result = session.run(cypher).single()
    print(f"\nNodes:")
    print(f"  - Zipcodes: {result['zipCount']}")
    print(f"  - HousingProjects: {result['projectCount']}")
    print(f"  - Total: {result['zipCount'] + result['projectCount']}")
    print(f"\nRelationships:")
    print(f"  - NEIGHBORS: {result['neighborCount']}")
    print(f"  - LOCATED_IN: {result['locatedInCount']}")
    print(f"  - Total: {result['neighborCount'] + result['locatedInCount']}")

neo4j_conn.close()

print("\n" + "=" * 70)
print("✅ All queries completed successfully!")
print("=" * 70)
print("\nKey Advantages Demonstrated:")
print("  ✓ Multi-hop traversal (Query 3)")
print("  ✓ Neo4j Point distance queries (Query 2)")
print("  ✓ Relationship-based filtering (Query 4, 5)")
print("  ✓ Simple, readable Cypher syntax")
print("=" * 70)
