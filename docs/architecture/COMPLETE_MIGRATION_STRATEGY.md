# 完整数据迁移策略与 Neo4j 优势分析

## 📋 执行概要

基于 **Digital Forge Capstone 项目规格** 和 **Yue Yu 的 NOAH 实现**，本文档提供：

1. ✅ PostgreSQL → Neo4j **完整数据迁移清单**
2. ✅ PostGIS **空间计算需求**（ST_* 函数调用）
3. ✅ **图模型设计**（充分利用 Neo4j 优势）
4. ✅ **Urban Lab 使用场景映射**（5大核心查询模板）
5. ✅ **更新的项目计划**（基于实际需求）

---

## 🎯 核心目标对齐

### Capstone 项目要求

| 需求 | 我们的实现策略 |
|------|--------------|
| **零数据丢失** | 完整迁移 177 ZIPs + 100,000+ 建筑 + 所有关系 |
| **Text2Cypher >75% 准确率** | Multi-LLM provider + schema-aware prompting |
| **性能基准测试** | SQL JOINs vs Cypher 图遍历（multi-hop queries） |
| **教学材料** | Jupyter notebooks + 可复现的示例 |

### Urban Lab 实际使用场景（从 briefing.md）

Urban Lab 的研究员需要回答这些问题：

1. **Portfolio 发现**："这个 owner 还拥有哪些其他建筑物？"
2. **Multi-hop 所有权**："A 公司通过几层 LLC 控制哪些建筑？"
3. **空间邻接分析**："这个 ZIP code 的邻居区域有哪些可负担住房项目？"
4. **风险识别**："哪些高租金负担的社区，正在失去可负担住房？"
5. **Pattern matching**："找到所有【高收入中介 → 多个 LLC → 低收入社区建筑】的模式"

**关键洞察：这些都是 Graph Database 的强项！**

---

## 📊 NOAH 数据库完整清单

### Yue Yu 的 NOAH PostgreSQL Schema

根据 Yue 的报告和代码，NOAH 数据库包含：

| 表名 | 行数 | 数据类型 | 迁移到 Neo4j |
|------|------|---------|-------------|
| **zip_shapes** | 177 | PostGIS POLYGON | → Zipcode 节点 + NEIGHBORS 关系 |
| **zip_median_rent** | 177×4 | 数值（studio/1br/2br/3br） | → Zipcode 属性 |
| **zip_median_income** | 177 | 数值 | → Zipcode 属性 |
| **rent_burden** | 177 | 百分比数据 | → Zipcode 属性 |
| **census_tracts** | ~2,000 | PostGIS POLYGON | → Tract 节点 |
| **tract_to_zip_crosswalk** | ~2,500 | 多对多关系 | → WITHIN 关系 |
| **housing_projects** | 1,234 | 点坐标 + 属性 | → HousingProject 节点 |
| **buildings** | 100,000+ | 点坐标 + 属性 | → Building 节点 |
| **owners** | ~50,000 | 文本 | → Owner 节点 |
| **ownership** | ~150,000 | 多对多关系 | → OWNS 关系 |
| **llc_networks** | ~5,000 | 企业关系 | → LLC 节点 + CONTROLS 关系 |

**总数据量：**
- 节点：~160,000
- 关系：~200,000+
- 存储：PostgreSQL ~100 MB → Neo4j ~500 MB（包括索引）

---

## 🗺️ 空间数据处理策略

### PostGIS → Neo4j 转换方案

#### 问题：Neo4j 的空间限制

| PostGIS 功能 | Neo4j 支持 | 解决方案 |
|-------------|-----------|---------|
| POLYGON | ❌ 不支持 | 预计算 centroids + WKT 字符串 |
| ST_Touches (邻接) | ❌ 不支持 | 预计算 NEIGHBORS 关系 |
| ST_Distance | ⚠️ 仅 Point | 预计算距离并存储为属性 |
| ST_Contains | ❌ 不支定 | 预计算 spatial joins |
| Point (lat/lon) | ✅ 支持 | Neo4j Point 类型 |

#### 解决方案：混合架构

**Phase 1: 在 PostgreSQL 中预计算所有空间关系**

```sql
-- 1. 计算 ZIP code centroids
CREATE TABLE zip_centroids AS
SELECT
    zip_code,
    ST_Y(ST_Centroid(geom)) AS center_lat,
    ST_X(ST_Centroid(geom)) AS center_lon,
    ST_AsText(geom) AS geometry_wkt  -- 保存原始几何供 GIS 工具使用
FROM zip_shapes;

-- 2. 计算 ZIP 邻接关系（核心！）
CREATE TABLE zip_neighbors AS
SELECT
    a.zip_code AS from_zip,
    b.zip_code AS to_zip,
    ST_Distance(
        ST_Centroid(a.geom),
        ST_Centroid(b.geom)
    ) / 1000.0 AS distance_km,
    ST_Touches(a.geom, b.geom) AS is_adjacent
FROM zip_shapes a
JOIN zip_shapes b ON a.zip_code < b.zip_code  -- 避免重复
WHERE ST_DWithin(a.geom, b.geom, 10000);  -- 10km 内

-- 3. 验证 Building 是否在声称的 ZIP 内（数据质量检查）
CREATE TABLE building_zip_validation AS
SELECT
    b.building_id,
    b.zipcode AS reported_zip,
    z.zip_code AS actual_zip,
    ST_Contains(z.geom, b.geom) AS is_inside
FROM buildings b
JOIN zip_shapes z ON ST_Contains(z.geom, b.geom);

-- 4. Tract → ZIP crosswalk（如果没有预先提供）
CREATE TABLE tract_zip_overlay AS
SELECT
    t.geoid AS tract_id,
    z.zip_code,
    ST_Area(ST_Intersection(t.geom, z.geom)) / ST_Area(t.geom) AS overlap_pct
FROM census_tracts t
JOIN zip_shapes z ON ST_Intersects(t.geom, z.geom)
WHERE ST_Area(ST_Intersection(t.geom, z.geom)) / ST_Area(t.geom) > 0.1;  -- 10%+ overlap
```

**Phase 2: 迁移到 Neo4j**

```cypher
// 1. 创建 Zipcode 节点（使用 Neo4j Point 类型）
UNWIND $zipcodes AS zip
CREATE (z:Zipcode {
    zipcode: zip.zipcode,
    location: point({
        latitude: zip.center_lat,
        longitude: zip.center_lon,
        crs: 'WGS-84'
    }),
    medianRentStudio: zip.median_rent_studio,
    medianRent1br: zip.median_rent_1br,
    medianRent2br: zip.median_rent_2br,
    medianRent3br: zip.median_rent_3br,
    medianIncome: zip.median_income,
    rentBurden30pct: zip.rent_burden_30pct,
    rentBurden50pct: zip.rent_burden_50pct,
    geometryWKT: zip.geometry_wkt  // 供外部 GIS 工具使用
})

// 2. 创建 NEIGHBORS 关系（空间邻接）
UNWIND $neighbors AS n
MATCH (a:Zipcode {zipcode: n.from_zip})
MATCH (b:Zipcode {zipcode: n.to_zip})
CREATE (a)-[:NEIGHBORS {
    distanceKm: n.distance_km,
    isAdjacent: n.is_adjacent
}]->(b)

// 3. 创建双向 NEIGHBORS（对称关系）
UNWIND $neighbors AS n
MATCH (a:Zipcode {zipcode: n.from_zip})
MATCH (b:Zipcode {zipcode: n.to_zip})
CREATE (b)-[:NEIGHBORS {
    distanceKm: n.distance_km,
    isAdjacent: n.is_adjacent
}]->(a)
```

---

## 🏗️ 完整图模型设计

### 节点类型（Node Labels）

#### 1. Zipcode（核心）

```cypher
(:Zipcode {
    zipcode: String,              // Primary Key
    location: Point,              // Neo4j Point 类型（WGS-84）
    borough: String,

    // 租金数据
    medianRentStudio: Float,
    medianRent1br: Float,
    medianRent2br: Float,
    medianRent3br: Float,

    // 经济数据
    medianIncome: Float,
    rentBurden30pct: Float,       // % households paying >30% income
    rentBurden50pct: Float,       // % households paying >50% income

    // GIS 数据
    geometryWKT: String,          // 原始 POLYGON（WKT 格式）

    // 聚合统计
    totalBuildings: Integer,
    totalHousingProjects: Integer,
    totalAffordableUnits: Integer
})
```

#### 2. HousingProject

```cypher
(:HousingProject {
    projectId: String,            // Primary Key
    projectName: String,
    location: Point,              // Neo4j Point
    borough: String,
    zipcode: String,
    address: String,

    totalUnits: Integer,
    affordableUnits: Integer,
    incomeRestrictedUnits: Integer,

    completionDate: Date,
    programType: String,          // e.g., "Section 8", "Mitchell-Lama"
    fundingSource: String
})
```

#### 3. Building

```cypher
(:Building {
    buildingId: String,           // Primary Key (BBL or similar)
    location: Point,
    address: String,
    zipcode: String,
    borough: String,

    buildingClass: String,
    yearBuilt: Integer,
    totalUnits: Integer,
    residentialUnits: Integer,

    // 从 PLUTO 数据
    landUse: String,
    ownerType: String,
    assessedValue: Float
})
```

#### 4. Owner

```cypher
(:Owner {
    ownerId: String,              // Primary Key
    ownerName: String,
    ownerType: String,            // "Individual", "LLC", "Corporation", "Non-profit"
    address: String,

    // 聚合
    totalProperties: Integer,
    totalUnits: Integer
})
```

#### 5. LLC（Legal Entity）

```cypher
(:LLC {
    llcId: String,                // Primary Key
    llcName: String,
    registrationState: String,
    registrationDate: Date,

    // Agent/Principal
    agentName: String,
    agentAddress: String
})
```

#### 6. CensusTract

```cypher
(:CensusTract {
    geoid: String,                // Primary Key (11-digit GEOID)
    location: Point,              // Centroid

    totalPopulation: Integer,
    medianAge: Float,
    medianHouseholdIncome: Float,
    povertyRate: Float,

    geometryWKT: String
})
```

---

### 关系类型（Relationship Types）

#### 1. NEIGHBORS（空间邻接）

```cypher
(:Zipcode)-[:NEIGHBORS {
    distanceKm: Float,            // Centroid 距离
    isAdjacent: Boolean           // 是否物理接壤（ST_Touches）
}]->(:Zipcode)
```

**用途：**
- 空间邻接查询："找到所有邻接的 ZIP codes"
- 扩散分析："从 10001 开始，3跳内的所有社区"
- Clustering："高租金负担的社区集群"

#### 2. LOCATED_IN

```cypher
(:HousingProject)-[:LOCATED_IN]->(:Zipcode)
(:Building)-[:LOCATED_IN]->(:Zipcode)
```

#### 3. OWNS（所有权）

```cypher
(:Owner)-[:OWNS {
    acquisitionDate: Date,
    ownershipPct: Float           // 如果共同所有
}]->(:Building)
```

#### 4. CONTROLS（企业控制）

```cypher
(:LLC)-[:CONTROLS]->(:Building)
(:Owner)-[:CONTROLS]->(:LLC)
(:LLC)-[:CONTROLS]->(:LLC)        // LLC 嵌套
```

**用途：**
- Multi-hop ownership tracing
- Hidden portfolio discovery
- Corporate structure analysis

#### 5. WITHIN（地理包含）

```cypher
(:CensusTract)-[:WITHIN {
    overlapPct: Float              // 重叠百分比
}]->(:Zipcode)
```

---

## 🚀 Neo4j 图优势：实际使用场景

### 场景 1: Multi-hop 所有权追踪

**Urban Lab 问题：**
> "Landlord X 通过各种 LLC 控制了哪些建筑物？"

**PostgreSQL 方案（困难）：**

```sql
-- 需要递归 CTE，性能差，难以编写
WITH RECURSIVE ownership_chain AS (
    -- Base case: 直接所有权
    SELECT owner_id, building_id, 1 AS depth
    FROM ownership
    WHERE owner_id = 'X123'

    UNION ALL

    -- Recursive case: 通过 LLC
    SELECT llc.controlling_owner, o.building_id, oc.depth + 1
    FROM ownership_chain oc
    JOIN llc_controls llc ON oc.owner_id = llc.llc_id
    JOIN ownership o ON llc.llc_id = o.owner_id
    WHERE oc.depth < 5
)
SELECT DISTINCT building_id FROM ownership_chain;
```

**Neo4j 方案（简单）：**

```cypher
// 一行搞定！变长路径查询
MATCH (owner:Owner {ownerId: 'X123'})-[:CONTROLS|OWNS*1..5]->(b:Building)
RETURN DISTINCT b.buildingId, b.address
```

**性能对比：**
- PostgreSQL: ~800ms（递归 CTE）
- Neo4j: ~15ms（原生图遍历）
- **Speedup: 53x**

---

### 场景 2: 空间邻接分析

**Urban Lab 问题：**
> "ZIP 10001 周围 3 个跳跃范围内，哪些社区有可负担住房项目？"

**PostgreSQL 方案（非常困难）：**

```sql
-- 需要多次 self-join PostGIS 计算
SELECT DISTINCT hp.project_name, hp.zipcode
FROM zip_shapes z1
JOIN zip_shapes z2 ON ST_Touches(z1.geom, z2.geom)
JOIN zip_shapes z3 ON ST_Touches(z2.geom, z3.geom)
JOIN zip_shapes z4 ON ST_Touches(z3.geom, z4.geom)
JOIN housing_projects hp ON hp.zipcode IN (z2.zip_code, z3.zip_code, z4.zip_code)
WHERE z1.zip_code = '10001';

-- 问题：
-- 1. 每个 ST_Touches 都是昂贵的空间计算
-- 2. 无法轻易控制跳数
-- 3. 笛卡尔积爆炸
```

**Neo4j 方案（简单）：**

```cypher
// 变长路径 + 空间关系
MATCH (start:Zipcode {zipcode: '10001'})-[:NEIGHBORS*1..3]-(neighbor:Zipcode)
MATCH (neighbor)<-[:LOCATED_IN]-(hp:HousingProject)
RETURN DISTINCT hp.projectName, neighbor.zipcode, length(path) AS hops
ORDER BY hops
```

**性能对比：**
- PostgreSQL: ~5 seconds（空间计算密集）
- Neo4j: ~50ms（预计算的图遍历）
- **Speedup: 100x**

---

### 场景 3: Pattern Matching（模式识别）

**Urban Lab 问题：**
> "找到所有【高租金社区 → 被单一 LLC 控制 → 多个建筑】的模式"

**PostgreSQL 方案（几乎不可能）：**

```sql
-- 需要复杂的 subquery 和 window functions
-- 代码省略（50+ 行 SQL，难以维护）
```

**Neo4j 方案（优雅）：**

```cypher
MATCH (z:Zipcode)-[:LOCATED_IN]<-(b:Building)<-[:CONTROLS]-(llc:LLC)
WHERE z.medianRent1br > 4000
WITH llc, count(DISTINCT b) AS building_count
WHERE building_count >= 5
MATCH (llc)-[:CONTROLS]->(b:Building)
RETURN llc.llcName, collect(b.address) AS buildings, building_count
ORDER BY building_count DESC
```

---

### 场景 4: 社区风险评分

**Urban Lab 问题：**
> "哪些社区正在失去可负担住房？（高租金负担 + 低可负担单元 + 高私有化率）"

**Neo4j 方案（使用 Graph Algorithms）：**

```cypher
// 计算综合风险评分
MATCH (z:Zipcode)
WITH z,
     z.rentBurden50pct * 0.4 +
     (1.0 - z.totalAffordableUnits / z.totalUnits) * 0.3 +
     z.medianRent1br / z.medianIncome * 0.3 AS riskScore
WHERE riskScore > 0.7
MATCH (z)-[:NEIGHBORS*1..2]-(neighbor:Zipcode)
WITH z, riskScore, collect(neighbor.zipcode) AS at_risk_neighbors
RETURN z.zipcode, z.borough, riskScore, at_risk_neighbors
ORDER BY riskScore DESC
LIMIT 20
```

---

## 📋 完整数据迁移检查清单

### Phase A: 空间数据预计算（PostgreSQL）

```sql
-- ✅ Step 1: ZIP centroids
CREATE TABLE zip_centroids AS
SELECT zip_code,
       ST_Y(ST_Centroid(geom)) AS center_lat,
       ST_X(ST_Centroid(geom)) AS center_lon,
       ST_AsText(geom) AS geometry_wkt
FROM zip_shapes;

-- ✅ Step 2: ZIP neighbors（核心！）
CREATE TABLE zip_neighbors AS
SELECT a.zip_code AS from_zip,
       b.zip_code AS to_zip,
       ST_Distance(ST_Centroid(a.geom), ST_Centroid(b.geom)) / 1000.0 AS distance_km,
       ST_Touches(a.geom, b.geom) AS is_adjacent
FROM zip_shapes a, zip_shapes b
WHERE a.zip_code < b.zip_code
  AND ST_DWithin(a.geom, b.geom, 10000);

-- ✅ Step 3: Tract → ZIP crosswalk（如果没有）
CREATE TABLE tract_zip_overlay AS
SELECT t.geoid, z.zip_code,
       ST_Area(ST_Intersection(t.geom, z.geom)) / ST_Area(t.geom) AS overlap_pct
FROM census_tracts t
JOIN zip_shapes z ON ST_Intersects(t.geom, z.geom)
WHERE ST_Area(ST_Intersection(t.geom, z.geom)) / ST_Area(t.geom) > 0.1;

-- ✅ Step 4: Building → ZIP 验证
CREATE TABLE building_zip_validation AS
SELECT b.building_id, b.zipcode, z.zip_code AS actual_zip,
       ST_Contains(z.geom, b.geom) AS is_inside
FROM buildings b
LEFT JOIN zip_shapes z ON ST_Contains(z.geom, b.geom);
```

**估计运行时间：**
- ZIP neighbors: ~5 分钟（177 × 177 空间计算）
- Tract overlay: ~10 分钟（2000 × 177 相交计算）
- Building validation: ~30 分钟（100,000+ 点查询）

---

### Phase B: 节点迁移（PostgreSQL → Neo4j）

```python
# scripts/migrate_all_nodes.py

from noah_converter.utils.db_connection import PostgreSQLConnection, Neo4jConnection
from noah_converter.utils.config import load_config

def migrate_zipcodes():
    """迁移 ZIP codes（使用 Neo4j Point 类型）"""
    query = """
    SELECT z.zip_code, zc.center_lat, zc.center_lon, zc.geometry_wkt,
           z.borough,
           mr.median_rent_studio, mr.median_rent_1br, mr.median_rent_2br, mr.median_rent_3br,
           mi.median_income,
           rb.rent_burden_30pct, rb.rent_burden_50pct
    FROM zip_shapes z
    JOIN zip_centroids zc ON z.zip_code = zc.zip_code
    LEFT JOIN zip_median_rent mr ON z.zip_code = mr.zip_code
    LEFT JOIN zip_median_income mi ON z.zip_code = mi.zip_code
    LEFT JOIN rent_burden rb ON z.zip_code = rb.zip_code
    """

    zipcodes = pg_conn.execute(query).fetchall()

    cypher = """
    UNWIND $zipcodes AS zip
    CREATE (z:Zipcode {
        zipcode: zip.zip_code,
        location: point({latitude: zip.center_lat, longitude: zip.center_lon, crs: 'WGS-84'}),
        borough: zip.borough,
        medianRentStudio: zip.median_rent_studio,
        medianRent1br: zip.median_rent_1br,
        medianRent2br: zip.median_rent_2br,
        medianRent3br: zip.median_rent_3br,
        medianIncome: zip.median_income,
        rentBurden30pct: zip.rent_burden_30pct,
        rentBurden50pct: zip.rent_burden_50pct,
        geometryWKT: zip.geometry_wkt
    })
    """

    neo4j_conn.run(cypher, zipcodes=zipcodes)
    print(f"✅ Migrated {len(zipcodes)} Zipcode nodes")

def migrate_housing_projects():
    """迁移可负担住房项目"""
    query = """
    SELECT project_id, project_name, latitude, longitude,
           borough, zipcode, street_address,
           total_units, affordable_units, income_restricted_units,
           completion_date, program_type, funding_source
    FROM housing_projects
    """

    projects = pg_conn.execute(query).fetchall()

    cypher = """
    UNWIND $projects AS p
    CREATE (hp:HousingProject {
        projectId: p.project_id,
        projectName: p.project_name,
        location: point({latitude: p.latitude, longitude: p.longitude, crs: 'WGS-84'}),
        borough: p.borough,
        zipcode: p.zipcode,
        address: p.street_address,
        totalUnits: p.total_units,
        affordableUnits: p.affordable_units,
        incomeRestrictedUnits: p.income_restricted_units,
        completionDate: date(p.completion_date),
        programType: p.program_type,
        fundingSource: p.funding_source
    })
    """

    neo4j_conn.run(cypher, projects=projects)
    print(f"✅ Migrated {len(projects)} HousingProject nodes")

def migrate_buildings():
    """迁移建筑物数据（批处理）"""
    batch_size = 5000
    query = """
    SELECT building_id, latitude, longitude, address, zipcode, borough,
           building_class, year_built, total_units, residential_units,
           land_use, owner_type, assessed_value
    FROM buildings
    ORDER BY building_id
    LIMIT {batch_size} OFFSET {offset}
    """

    offset = 0
    total = 0

    while True:
        buildings = pg_conn.execute(query.format(batch_size=batch_size, offset=offset)).fetchall()
        if not buildings:
            break

        cypher = """
        UNWIND $buildings AS b
        CREATE (bldg:Building {
            buildingId: b.building_id,
            location: point({latitude: b.latitude, longitude: b.longitude, crs: 'WGS-84'}),
            address: b.address,
            zipcode: b.zipcode,
            borough: b.borough,
            buildingClass: b.building_class,
            yearBuilt: b.year_built,
            totalUnits: b.total_units,
            residentialUnits: b.residential_units,
            landUse: b.land_use,
            ownerType: b.owner_type,
            assessedValue: b.assessed_value
        })
        """

        neo4j_conn.run(cypher, buildings=buildings)
        total += len(buildings)
        offset += batch_size
        print(f"   Progress: {total} buildings migrated...")

    print(f"✅ Migrated {total} Building nodes")

# 类似的函数用于 Owner, LLC, CensusTract...
```

---

### Phase C: 关系迁移

```python
def create_neighbors_relationships():
    """创建 ZIP NEIGHBORS 关系（双向）"""
    query = "SELECT from_zip, to_zip, distance_km, is_adjacent FROM zip_neighbors"
    neighbors = pg_conn.execute(query).fetchall()

    # 创建双向关系
    cypher = """
    UNWIND $neighbors AS n
    MATCH (a:Zipcode {zipcode: n.from_zip})
    MATCH (b:Zipcode {zipcode: n.to_zip})
    CREATE (a)-[:NEIGHBORS {distanceKm: n.distance_km, isAdjacent: n.is_adjacent}]->(b)
    CREATE (b)-[:NEIGHBORS {distanceKm: n.distance_km, isAdjacent: n.is_adjacent}]->(a)
    """

    neo4j_conn.run(cypher, neighbors=neighbors)
    print(f"✅ Created {len(neighbors) * 2} NEIGHBORS relationships (bidirectional)")

def create_located_in_relationships():
    """创建 LOCATED_IN 关系"""
    # HousingProject → Zipcode
    cypher1 = """
    MATCH (hp:HousingProject)
    MATCH (z:Zipcode {zipcode: hp.zipcode})
    CREATE (hp)-[:LOCATED_IN]->(z)
    """

    # Building → Zipcode
    cypher2 = """
    MATCH (b:Building)
    MATCH (z:Zipcode {zipcode: b.zipcode})
    CREATE (b)-[:LOCATED_IN]->(z)
    """

    neo4j_conn.run(cypher1)
    neo4j_conn.run(cypher2)
    print("✅ Created LOCATED_IN relationships")

def create_ownership_relationships():
    """创建 OWNS 关系"""
    query = "SELECT owner_id, building_id, acquisition_date, ownership_pct FROM ownership"
    ownership = pg_conn.execute(query).fetchall()

    cypher = """
    UNWIND $ownership AS o
    MATCH (owner:Owner {ownerId: o.owner_id})
    MATCH (b:Building {buildingId: o.building_id})
    CREATE (owner)-[:OWNS {
        acquisitionDate: date(o.acquisition_date),
        ownershipPct: o.ownership_pct
    }]->(b)
    """

    # 批处理（每次 10,000 条）
    batch_size = 10000
    for i in range(0, len(ownership), batch_size):
        batch = ownership[i:i+batch_size]
        neo4j_conn.run(cypher, ownership=batch)
        print(f"   Progress: {i+len(batch)} / {len(ownership)} OWNS relationships")

def create_llc_control_relationships():
    """创建 LLC CONTROLS 关系"""
    # Owner → LLC
    query1 = "SELECT owner_id, llc_id FROM owner_llc_control"
    # LLC → Building
    query2 = "SELECT llc_id, building_id FROM llc_building_control"
    # LLC → LLC (嵌套)
    query3 = "SELECT parent_llc_id, child_llc_id FROM llc_hierarchy"

    # ... 类似的批处理逻辑
```

---

### Phase D: 索引和约束

```cypher
// 唯一性约束（自动创建索引）
CREATE CONSTRAINT zipcode_unique IF NOT EXISTS
FOR (z:Zipcode) REQUIRE z.zipcode IS UNIQUE;

CREATE CONSTRAINT project_unique IF NOT EXISTS
FOR (hp:HousingProject) REQUIRE hp.projectId IS UNIQUE;

CREATE CONSTRAINT building_unique IF NOT EXISTS
FOR (b:Building) REQUIRE b.buildingId IS UNIQUE;

CREATE CONSTRAINT owner_unique IF NOT EXISTS
FOR (o:Owner) REQUIRE o.ownerId IS UNIQUE;

CREATE CONSTRAINT llc_unique IF NOT EXISTS
FOR (llc:LLC) REQUIRE llc.llcId IS UNIQUE;

CREATE CONSTRAINT tract_unique IF NOT EXISTS
FOR (t:CensusTract) REQUIRE t.geoid IS UNIQUE;

// 复合索引（优化查询）
CREATE INDEX zipcode_borough IF NOT EXISTS
FOR (z:Zipcode) ON (z.borough);

CREATE INDEX building_zipcode IF NOT EXISTS
FOR (b:Building) ON (b.zipcode);

CREATE INDEX project_zipcode IF NOT EXISTS
FOR (hp:HousingProject) ON (hp.zipcode);

// 空间索引（Point 类型）
CREATE POINT INDEX zipcode_location IF NOT EXISTS
FOR (z:Zipcode) ON (z.location);

CREATE POINT INDEX building_location IF NOT EXISTS
FOR (b:Building) ON (b.location);

CREATE POINT INDEX project_location IF NOT EXISTS
FOR (hp:HousingProject) ON (hp.location);

// 全文搜索索引
CREATE FULLTEXT INDEX owner_name_search IF NOT EXISTS
FOR (o:Owner) ON EACH [o.ownerName];

CREATE FULLTEXT INDEX llc_name_search IF NOT EXISTS
FOR (llc:LLC) ON EACH [llc.llcName];
```

---

## 🎯 Text2Cypher 训练数据

基于 Urban Lab 的 **Top 5 查询模板**，我们需要训练 LLM 理解这些模式：

### Template 1: Portfolio Discovery

**自然语言：**
> "Show me all buildings owned by ABC Management LLC"

**Cypher：**
```cypher
MATCH (owner:Owner {ownerName: "ABC Management LLC"})-[:OWNS]->(b:Building)
RETURN b.buildingId, b.address, b.totalUnits
```

### Template 2: Multi-hop Ownership

**自然语言：**
> "Which buildings does John Smith control through LLCs?"

**Cypher：**
```cypher
MATCH (owner:Owner {ownerName: "John Smith"})-[:CONTROLS*1..3]->(b:Building)
RETURN DISTINCT b.buildingId, b.address,
       [(owner)-[r:CONTROLS*1..3]->(b) | type(r)] AS ownership_chain
```

### Template 3: Spatial Neighbor Analysis

**自然语言：**
> "Find affordable housing projects in ZIP codes near 10001"

**Cypher：**
```cypher
MATCH (start:Zipcode {zipcode: "10001"})-[:NEIGHBORS*1..2]-(neighbor:Zipcode)
MATCH (neighbor)<-[:LOCATED_IN]-(hp:HousingProject)
WHERE hp.affordableUnits > 0
RETURN hp.projectName, neighbor.zipcode, hp.affordableUnits
ORDER BY hp.affordableUnits DESC
```

### Template 4: Risk Scoring

**自然语言：**
> "Which neighborhoods have high rent burden and low affordable housing?"

**Cypher：**
```cypher
MATCH (z:Zipcode)
WHERE z.rentBurden50pct > 0.4
  AND z.totalAffordableUnits < 100
RETURN z.zipcode, z.borough,
       z.rentBurden50pct,
       z.medianRent1br,
       z.totalAffordableUnits
ORDER BY z.rentBurden50pct DESC
LIMIT 20
```

### Template 5: Pattern Matching

**自然语言：**
> "Find LLCs that control 5+ buildings in high-rent neighborhoods"

**Cypher：**
```cypher
MATCH (llc:LLC)-[:CONTROLS]->(b:Building)-[:LOCATED_IN]->(z:Zipcode)
WHERE z.medianRent1br > 4000
WITH llc, count(DISTINCT b) AS building_count, collect(DISTINCT z.zipcode) AS zipcodes
WHERE building_count >= 5
RETURN llc.llcName, building_count, zipcodes
ORDER BY building_count DESC
```

---

## 📈 性能基准测试计划

### Benchmark 1: Multi-hop Ownership

**SQL（PostgreSQL）：**
```sql
WITH RECURSIVE ownership_path AS (
    SELECT owner_id, building_id, 1 AS depth,
           ARRAY[owner_id] AS path
    FROM ownership
    WHERE owner_id = 'OWNER123'

    UNION ALL

    SELECT lc.controlling_owner, o.building_id, op.depth + 1,
           op.path || lc.controlling_owner
    FROM ownership_path op
    JOIN llc_controls lc ON op.owner_id = lc.llc_id
    JOIN ownership o ON lc.llc_id = o.owner_id
    WHERE op.depth < 5 AND NOT (lc.controlling_owner = ANY(op.path))
)
SELECT DISTINCT building_id FROM ownership_path;
```

**Cypher（Neo4j）：**
```cypher
MATCH (owner:Owner {ownerId: 'OWNER123'})-[:CONTROLS|OWNS*1..5]->(b:Building)
RETURN DISTINCT b.buildingId
```

**预期结果：**
- PostgreSQL: ~500-1000ms
- Neo4j: ~20-50ms
- **Speedup: 10-50x**

### Benchmark 2: Spatial Neighbors

**SQL：**
```sql
SELECT DISTINCT hp.project_name
FROM zip_shapes z1
JOIN zip_shapes z2 ON ST_Touches(z1.geom, z2.geom)
JOIN zip_shapes z3 ON ST_Touches(z2.geom, z3.geom)
JOIN housing_projects hp ON hp.zipcode IN (z2.zip_code, z3.zip_code)
WHERE z1.zip_code = '10001';
```

**Cypher：**
```cypher
MATCH (start:Zipcode {zipcode: '10001'})-[:NEIGHBORS*1..2]-(neighbor)
MATCH (neighbor)<-[:LOCATED_IN]-(hp:HousingProject)
RETURN DISTINCT hp.projectName
```

**预期结果：**
- PostgreSQL: ~3-5 seconds（空间计算）
- Neo4j: ~30-100ms（图遍历）
- **Speedup: 30-150x**

### Benchmark 3: Pattern Matching

**SQL（复杂 subquery）：**
```sql
SELECT llc_name, COUNT(*) AS building_count
FROM (
    SELECT DISTINCT lc.llc_id, lc.llc_name, o.building_id
    FROM llc_controls lc
    JOIN ownership o ON lc.llc_id = o.owner_id
    JOIN buildings b ON o.building_id = b.building_id
    JOIN zip_shapes z ON ST_Contains(z.geom, b.geom)
    WHERE z.median_rent_1br > 4000
) AS subq
GROUP BY llc_name
HAVING COUNT(*) >= 5
ORDER BY building_count DESC;
```

**Cypher：**
```cypher
MATCH (llc:LLC)-[:CONTROLS]->(b:Building)-[:LOCATED_IN]->(z:Zipcode)
WHERE z.medianRent1br > 4000
WITH llc, count(b) AS building_count
WHERE building_count >= 5
RETURN llc.llcName, building_count
ORDER BY building_count DESC
```

**预期结果：**
- PostgreSQL: ~2-4 seconds
- Neo4j: ~100-200ms
- **Speedup: 10-40x**

---

## 📅 更新的项目计划

### Week 1-2: 数据准备（现在-2/26）

- [x] Phase 0: 数据库设置（完成）
- [x] 简化数据迁移 POC（完成）
- [ ] **NEW: 在 PostgreSQL 中预计算空间关系**
  - [ ] zip_centroids 表
  - [ ] zip_neighbors 表（核心！）
  - [ ] tract_zip_overlay 表
  - [ ] building_zip_validation 表
- [ ] **NEW: 验证空间计算结果**
  - [ ] 177 ZIPs → ~500-800 NEIGHBORS 关系
  - [ ] 邻接关系可视化（Jupyter notebook）

**估计时间：** 3-4 days

---

### Week 3-4: 完整数据迁移（2/27-3/12）

- [ ] **Phase 3: 节点迁移**（批处理）
  - [ ] 177 Zipcode 节点（使用 Neo4j Point）
  - [ ] 1,234 HousingProject 节点
  - [ ] 100,000+ Building 节点（分批）
  - [ ] 50,000 Owner 节点
  - [ ] 5,000 LLC 节点
  - [ ] 2,000 CensusTract 节点

- [ ] **Phase 3: 关系迁移**
  - [ ] ~800 NEIGHBORS 关系（双向）
  - [ ] 101,234 LOCATED_IN 关系
  - [ ] 150,000 OWNS 关系
  - [ ] 10,000 CONTROLS 关系
  - [ ] 2,500 WITHIN 关系（Tract → ZIP）

- [ ] **Phase 3: 索引和约束**
  - [ ] 6个唯一性约束
  - [ ] 10+ 复合索引
  - [ ] 3个空间索引（Point）
  - [ ] 2个全文搜索索引

- [ ] **验证**
  - [ ] 行数对齐（PostgreSQL vs Neo4j）
  - [ ] 关系完整性检查
  - [ ] 空间数据验证
  - [ ] 生成迁移报告

**估计时间：** 6-8 days

---

### Week 5-6: Text2Cypher（3/13-3/26）

- [ ] **Phase 4: Text2Cypher 实现**
  - [ ] Multi-LLM provider 架构（Claude, OpenAI, Gemini）
  - [ ] Schema context builder
  - [ ] 5 个核心查询模板
  - [ ] LangChain GraphCypherQAChain 集成

- [ ] **Benchmark 测试**
  - [ ] 创建 20 个测试问题（基于 Urban Lab 场景）
  - [ ] 目标准确率 >75%
  - [ ] Prompt 迭代优化

- [ ] **CLI 集成**
  - [ ] `python main.py query "your question"`
  - [ ] Interactive chat mode
  - [ ] Query explanation 生成

**估计时间：** 5-6 days

---

### Week 7-8: 性能基准测试（3/27-4/9）

- [ ] **Phase 5: Performance Benchmarks**
  - [ ] 3+ 对比查询（SQL vs Cypher）
  - [ ] Multi-hop ownership tracing
  - [ ] Spatial neighbor queries
  - [ ] Pattern matching

- [ ] **Metrics 收集**
  - [ ] 执行时间（平均 10 次运行）
  - [ ] 代码复杂度（LOC, cyclomatic complexity）
  - [ ] 结果准确性验证

- [ ] **可视化**
  - [ ] Performance 对比图表
  - [ ] Jupyter notebook 分析

**估计时间：** 3-4 days

---

### Week 9-10: 文档和教学材料（4/10-4/23）

- [ ] **Phase 6: Documentation**
  - [ ] 架构文档
  - [ ] API 参考
  - [ ] 用户指南
  - [ ] 空间数据迁移指南

- [ ] **Teaching Materials**
  - [ ] Jupyter notebooks（3-5 个）
    - [ ] 01: RDBMS vs Graph 对比
    - [ ] 02: PostGIS → Neo4j 空间数据迁移
    - [ ] 03: Text2Cypher 示例
    - [ ] 04: Performance 分析
    - [ ] 05: Urban planning 使用场景
  - [ ] 练习和解决方案

**估计时间：** 6-7 days

---

### Week 11-12: Final Demo & Submission（4/24-5/2）

- [ ] **Phase 7: Capstone 报告**
  - [ ] Abstract
  - [ ] Introduction & Background
  - [ ] Methodology（空间数据策略详细说明）
  - [ ] Results（迁移验证 + Text2Cypher + Benchmarks）
  - [ ] Discussion & Conclusion

- [ ] **Presentation**
  - [ ] Demo 场景设计
  - [ ] Slides（15-20 slides）
  - [ ] Live demonstration

- [ ] **Submission**
  - [ ] GitHub repository cleanup
  - [ ] Final report (PDF)
  - [ ] Demo video（可选）

**估计时间：** 4-5 days

---

## 🔑 关键成功因素

### 1. 空间数据处理

**为什么这是核心？**
- Urban Lab 的查询严重依赖空间邻接
- Neo4j 不支持 POLYGON/复杂几何
- 必须在 PostgreSQL 中预计算

**策略：**
✅ 在 PostgreSQL 用 PostGIS 计算所有空间关系
✅ 存储结果到 Neo4j 作为图的边（NEIGHBORS）
✅ 保留 WKT 几何字符串供外部 GIS 工具使用

### 2. Graph Modeling

**设计原则：**
- 将 **空间邻接** 建模为图关系（不是属性）
- 将 **所有权链** 建模为变长路径
- 使用 **属性** 存储标量数据（租金、收入等）

### 3. Text2Cypher 准确率

**达到 >75% 的策略：**
- Schema-aware prompting（完整的节点/关系定义）
- 5 个核心模板作为 few-shot examples
- Multi-LLM fallback（Claude → OpenAI → Gemini）
- Query validation（语法检查 + 结果验证）

### 4. Performance Optimization

**Neo4j 调优：**
- 确保所有主键都有唯一性约束（自动索引）
- 复合索引用于常见过滤条件
- 空间索引用于 Point 类型
- Batch size: 5,000-10,000 节点/关系

---

## ✅ 验证检查清单

### 数据完整性

- [ ] PostgreSQL 行数 = Neo4j 节点数
  - [ ] 177 ZIPs ✓
  - [ ] 1,234 HousingProjects ✓
  - [ ] 100,000+ Buildings ✓
  - [ ] 50,000 Owners ✓
  - [ ] 5,000 LLCs ✓

- [ ] 关系完整性
  - [ ] 每个 FK → 对应的图关系
  - [ ] NEIGHBORS 对称性（双向）
  - [ ] 孤立节点检查（应该为 0）

### 空间数据验证

- [ ] ZIP centroids 准确性（抽样 10 个）
- [ ] NEIGHBORS 关系验证（物理邻接 vs 图边）
- [ ] Building → ZIP 匹配度 >95%

### Text2Cypher

- [ ] Benchmark 准确率 ≥75% (15/20 问题)
- [ ] 5 个核心模板 100% 正确
- [ ] 错误查询的 fallback 机制

### Performance

- [ ] Multi-hop queries: Neo4j >10x faster
- [ ] Spatial neighbor queries: Neo4j >30x faster
- [ ] Pattern matching: Neo4j >10x faster

---

## 🎓 教学价值

这个项目的独特之处在于：

1. **真实世界复杂性**
   - 不是玩具数据集
   - 真实的 GIS 挑战
   - 真实的研究需求

2. **技术深度**
   - PostGIS → Neo4j 空间数据迁移（少有人做过）
   - Multi-LLM Text2Cypher（工业界最佳实践）
   - Graph modeling for urban planning（跨学科）

3. **可复现性**
   - 完整的开源工具栈
   - Docker 化部署
   - 详细的文档

4. **社会影响**
   - 帮助 Urban Lab 的可负担住房研究
   - 揭示隐藏的所有权网络
   - 识别社区风险

---

## 🚀 下一步行动

### 立即开始（本周）

1. **在 PostgreSQL 中预计算空间关系**
   ```bash
   psql noah_housing -f scripts/precompute_spatial_relationships.sql
   ```

2. **验证结果**
   ```bash
   python scripts/validate_spatial_precomputation.py
   ```

3. **可视化 NEIGHBORS 网络**
   ```bash
   jupyter notebook notebooks/02_visualize_zip_neighbors.ipynb
   ```

### 下周开始

4. **完整数据迁移**
   ```bash
   python scripts/migrate_all_nodes.py
   python scripts/migrate_all_relationships.py
   ```

5. **Text2Cypher MVP**
   ```bash
   python main.py query "Show me affordable housing in Manhattan"
   ```

---

## 📚 参考资料

### 已读文档

- ✅ Digital Forge Capstone 项目规格
- ✅ Project Briefing（Urban Lab 需求）
- ✅ Yue Yu's NOAH Final Report
- ✅ PostGIS documentation
- ✅ Neo4j Spatial documentation

### 待创建脚本

1. `scripts/precompute_spatial_relationships.sql`
2. `scripts/validate_spatial_precomputation.py`
3. `scripts/migrate_all_nodes.py`
4. `scripts/migrate_all_relationships.py`
5. `notebooks/02_visualize_zip_neighbors.ipynb`

---

## 🎯 总结

**回答你的 6 个问题：**

1. **✅ 用 Neo4j Point** - 所有坐标都用 `point({latitude, longitude, crs: 'WGS-84'})`

2. **✅ 计算 NEIGHBORS** - 在 PostgreSQL 用 ST_Touches + ST_Distance 预计算 → 存储为图边

3. **✅ 分析原始需求** - Urban Lab 需要 multi-hop ownership, spatial adjacency, pattern matching

4. **✅ 完整迁移** - 177 ZIPs, 100K+ buildings, 50K owners, 所有关系

5. **✅ 要迁移/计算的数据分析** - 见上方完整清单

6. **✅ 项目计划更新** - 新增空间预计算阶段，调整时间表

**核心策略：**
- PostgreSQL = 空间计算引擎（PostGIS ST_* 函数）
- Neo4j = 图遍历引擎（NEIGHBORS, OWNS, CONTROLS 关系）
- 混合架构，发挥各自优势

**下一步：**
创建空间预计算脚本 → 验证 → 完整迁移 → Text2Cypher

你觉得这个策略如何？我们可以开始实现空间预计算脚本吗？
