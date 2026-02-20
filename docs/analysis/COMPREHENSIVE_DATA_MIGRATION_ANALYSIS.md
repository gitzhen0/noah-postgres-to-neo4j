# NOAH 数据迁移综合分析报告

**Date:** 2026-02-20
**Author:** Based on First-Hand Resources Analysis
**Purpose:** 确定从 PostgreSQL 迁移到 Neo4j 的完整数据策略

---

## 📋 Executive Summary

基于对 Yue Yu 和 Chaoou Zhang 的 NOAH 项目最终报告以及 Capstone 项目规范的分析，本文档提供了完整的数据迁移策略。核心原则是：

1. **在 PostgreSQL 中计算空间关系** - 利用 PostGIS 的强大空间计算能力
2. **在 Neo4j 中存储图关系** - 利用 Neo4j 的图遍历和查询优势
3. **全面迁移** - 尽可能保留所有数据和关系
4. **最大化 Neo4j 优势** - 设计以关系遍历为中心的图模型

---

## 🎯 项目需求分析

### Capstone 项目核心要求

根据项目规范文档，必须满足：

1. ✅ **Zero data loss** - 完整迁移 NOAH 数据库，零数据丢失
2. ✅ **Text2Cypher >75% accuracy** - 自然语言查询准确率 >75%
3. ✅ **Performance benchmarks** - SQL JOIN vs Cypher traversal 性能对比
4. ✅ **Full documentation** - 完整文档和教学材料

### NOAH 数据库规模

根据 Yue Yu 和 Chaoou Zhang 的报告：

- **177 NYC ZIP codes/ZCTAs**
- **~100,000 residential buildings** (来自 PLUTO 数据集)
- **12+ tables** with complex relationships
- **PostgreSQL + PostGIS** database
- **Key data sources:**
  - American Community Survey (ACS) - 人口统计数据
  - NYC PLUTO - 建筑和地块数据
  - StreetEasy - 市场租金数据
  - HUD - 住房政策数据
  - NYC Open Data - 多种开放数据

---

## 📊 完整数据分类和迁移策略

### 分类 1: 核心地理实体 (Entity Tables → Nodes)

这些表应该转换为 Neo4j 节点。

#### 1.1 Zipcode/ZCTA 表

**PostgreSQL Schema (推测):**
```sql
CREATE TABLE zipcodes (
    zipcode_id SERIAL PRIMARY KEY,
    zip_code VARCHAR(5) NOT NULL UNIQUE,
    zcta_geoid VARCHAR(10),
    borough VARCHAR(50),
    geometry GEOMETRY(MULTIPOLYGON, 4326),
    -- 以下字段将在 PostgreSQL 中计算后存入 Neo4j
    centroid_lat DOUBLE PRECISION,
    centroid_lon DOUBLE PRECISION,
    area_km2 DOUBLE PRECISION
);
```

**Neo4j 节点设计:**
```cypher
CREATE (z:Zipcode {
    zipcode: '10001',
    zcta_geoid: '10001',
    borough: 'Manhattan',

    -- Neo4j Point 类型 (WGS-84)
    location: point({
        latitude: 40.7506,
        longitude: -73.9971,
        crs: 'WGS-84'
    }),

    -- 冗余存储坐标 (方便查询)
    centerLat: 40.7506,
    centerLon: -73.9971,

    -- 空间属性
    areaKm2: 2.45,

    -- WKT geometry (用于外部 GIS 工具)
    geometryWKT: 'MULTIPOLYGON(((...)))'
})
```

**数据来源和计算:**
- ✅ `zipcode`, `borough` - 直接从 PostgreSQL
- ✅ `location` (Point) - 从 PostGIS 计算: `ST_Centroid(geometry)`
- ✅ `areaKm2` - 从 PostGIS 计算: `ST_Area(geometry::geography) / 1000000`
- ✅ `geometryWKT` - 从 PostGIS 计算: `ST_AsText(geometry)`

---

#### 1.2 Building 表

**PostgreSQL Schema (基于 PLUTO):**
```sql
CREATE TABLE buildings (
    building_id SERIAL PRIMARY KEY,
    bbl VARCHAR(10) NOT NULL UNIQUE,  -- Borough-Block-Lot
    bin VARCHAR(7),  -- Building Identification Number
    address TEXT,
    zipcode_id INTEGER REFERENCES zipcodes(zipcode_id),

    -- 建筑属性
    year_built INTEGER,
    num_floors INTEGER,
    units_residential INTEGER,
    units_total INTEGER,
    landuse_code VARCHAR(4),
    landuse_category VARCHAR(50),
    building_class VARCHAR(4),

    -- 空间数据
    geometry GEOMETRY(POINT, 4326),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);
```

**Neo4j 节点设计:**
```cypher
CREATE (b:Building {
    bbl: '1000010101',
    bin: '1000001',
    address: '350 5th Avenue, Manhattan',

    -- 建筑属性
    yearBuilt: 1931,
    numFloors: 102,
    unitsResidential: 0,
    unitsTotal: 0,
    landuseCode: '05',
    landuseCategory: 'Commercial',
    buildingClass: 'O4',

    -- 空间位置
    location: point({
        latitude: 40.7484,
        longitude: -73.9857,
        crs: 'WGS-84'
    }),

    latitude: 40.7484,
    longitude: -73.9857
})
```

**数据量:**
- ~100,000 nodes

---

#### 1.3 Demographic/Socioeconomic 指标

**PostgreSQL Schema (基于 ACS):**
```sql
CREATE TABLE demographics (
    demographic_id SERIAL PRIMARY KEY,
    zipcode_id INTEGER REFERENCES zipcodes(zipcode_id),

    -- 人口统计
    total_population INTEGER,
    median_age DOUBLE PRECISION,
    pct_renter_occupied DOUBLE PRECISION,
    pct_owner_occupied DOUBLE PRECISION,

    -- 种族统计
    pct_white DOUBLE PRECISION,
    pct_black DOUBLE PRECISION,
    pct_asian DOUBLE PRECISION,
    pct_hispanic DOUBLE PRECISION,

    -- 数据来源
    source VARCHAR(50),  -- 'ACS 5-Year 2019-2023'
    year_range VARCHAR(20)
);

CREATE TABLE income_metrics (
    income_id SERIAL PRIMARY KEY,
    zipcode_id INTEGER REFERENCES zipcodes(zipcode_id),

    median_household_income DOUBLE PRECISION,
    median_family_income DOUBLE PRECISION,
    per_capita_income DOUBLE PRECISION,

    -- 收入分布
    pct_below_poverty DOUBLE PRECISION,
    pct_50k_to_75k DOUBLE PRECISION,
    pct_above_100k DOUBLE PRECISION,

    source VARCHAR(50),
    year_range VARCHAR(20)
);

CREATE TABLE rent_metrics (
    rent_id SERIAL PRIMARY KEY,
    zipcode_id INTEGER REFERENCES zipcodes(zipcode_id),

    -- 市场租金 (StreetEasy)
    median_rent_studio DOUBLE PRECISION,
    median_rent_1br DOUBLE PRECISION,
    median_rent_2br DOUBLE PRECISION,
    median_rent_3br DOUBLE PRECISION,

    -- Rent Burden (ACS)
    pct_rent_burden_30 DOUBLE PRECISION,  -- 30%+ of income
    pct_rent_burden_50 DOUBLE PRECISION,  -- 50%+ of income (severe)
    median_gross_rent DOUBLE PRECISION,

    source VARCHAR(50),
    year_range VARCHAR(20)
);

CREATE TABLE housing_stock (
    stock_id SERIAL PRIMARY KEY,
    zipcode_id INTEGER REFERENCES zipcodes(zipcode_id),

    total_units INTEGER,
    occupied_units INTEGER,
    vacant_units INTEGER,
    renter_occupied_units INTEGER,
    owner_occupied_units INTEGER,

    vacancy_rate DOUBLE PRECISION,

    source VARCHAR(50),
    year_range VARCHAR(20)
);
```

**Neo4j 设计选择: Properties vs Separate Nodes**

**选项 A: 作为 Zipcode 节点的属性 (推荐)**

优点:
- 简化查询 (不需要额外的遍历)
- 更快的性能 (所有数据在一个节点)
- 更直观的 Text2Cypher 查询

```cypher
CREATE (z:Zipcode {
    zipcode: '10001',
    borough: 'Manhattan',

    -- Demographics
    totalPopulation: 21102,
    medianAge: 36.5,
    pctRenterOccupied: 82.3,

    -- Income
    medianHouseholdIncome: 66912,
    perCapitaIncome: 48213,
    pctBelowPoverty: 18.2,

    -- Rent Metrics
    medianRentStudio: 2500,
    medianRent1br: 3200,
    medianRent2br: 4500,
    pctRentBurden30: 45.2,
    pctRentBurden50: 22.1,

    -- Housing Stock
    totalUnits: 12453,
    vacancyRate: 5.2,

    -- Metadata
    dataSource: 'ACS 5-Year 2019-2023, StreetEasy 2023',
    lastUpdated: date('2024-01-15')
})
```

**选项 B: 作为独立节点**

仅在需要时间序列数据或多数据源时使用。

```cypher
// 如果需要跟踪历史数据
CREATE (z:Zipcode {zipcode: '10001'})
CREATE (d:Demographics {
    year: 2023,
    totalPopulation: 21102,
    source: 'ACS 5-Year 2019-2023'
})
CREATE (z)-[:HAS_DEMOGRAPHICS {validFrom: date('2019-01-01'), validTo: date('2023-12-31')}]->(d)
```

**推荐: 选项 A** (作为属性) - 除非项目需要时间序列分析

---

#### 1.4 Affordable Housing Projects

**PostgreSQL Schema:**
```sql
CREATE TABLE housing_projects (
    project_id SERIAL PRIMARY KEY,
    project_name TEXT,
    zipcode_id INTEGER REFERENCES zipcodes(zipcode_id),

    -- 项目属性
    completion_date DATE,
    total_units INTEGER,
    affordable_units INTEGER,
    income_restricted_units INTEGER,

    -- AMI (Area Median Income) 限制
    ami_30_units INTEGER,  -- 30% AMI
    ami_50_units INTEGER,  -- 50% AMI
    ami_60_units INTEGER,  -- 60% AMI
    ami_80_units INTEGER,  -- 80% AMI

    -- 项目类型
    program_type VARCHAR(50),  -- 'HPD Preservation', 'LIHTC', etc.
    funding_source VARCHAR(100),

    -- 空间数据
    geometry GEOMETRY(POINT, 4326),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);
```

**Neo4j 节点设计:**
```cypher
CREATE (p:HousingProject {
    projectId: 'HPD-2023-001',
    projectName: 'Affordable Housing Complex A',

    completionDate: date('2023-06-15'),
    totalUnits: 150,
    affordableUnits: 120,
    incomeRestrictedUnits: 120,

    ami30Units: 30,
    ami50Units: 40,
    ami60Units: 30,
    ami80Units: 20,

    programType: 'HPD Preservation',
    fundingSource: 'City Capital + LIHTC',

    location: point({
        latitude: 40.7500,
        longitude: -73.9900,
        crs: 'WGS-84'
    })
})
```

**数据量:**
- 实际项目数量取决于 NOAH 数据库的完整性
- 估计: 1,000 - 5,000 projects across NYC

---

### 分类 2: 空间关系 (Computed in PostgreSQL → Relationships in Neo4j)

#### 2.1 NEIGHBORS 关系 (ZIP 邻接)

**PostgreSQL 计算 (PostGIS):**

```sql
-- 方法 1: 基于空间邻接 (ST_Touches)
CREATE TABLE zip_neighbors AS
SELECT
    a.zip_code AS from_zip,
    b.zip_code AS to_zip,
    ST_Distance(
        ST_Centroid(a.geometry)::geography,
        ST_Centroid(b.geometry)::geography
    ) / 1000.0 AS distance_km,
    ST_Touches(a.geometry, b.geometry) AS is_adjacent
FROM zipcodes a
CROSS JOIN zipcodes b
WHERE a.zip_code < b.zip_code  -- 避免重复
  AND ST_DWithin(a.geometry, b.geometry, 10000);  -- 10km 范围内

-- 方法 2: 基于距离阈值
CREATE TABLE zip_proximity AS
SELECT
    a.zip_code AS from_zip,
    b.zip_code AS to_zip,
    ST_Distance(
        ST_Centroid(a.geometry)::geography,
        ST_Centroid(b.geometry)::geography
    ) / 1000.0 AS distance_km
FROM zipcodes a
CROSS JOIN zipcodes b
WHERE a.zip_code <> b.zip_code
  AND ST_DWithin(
      ST_Centroid(a.geometry)::geography,
      ST_Centroid(b.geometry)::geography,
      5000  -- 5km radius
  );
```

**Neo4j 关系设计:**

```cypher
// 双向关系 (重要: 保证遍历对称性)
MATCH (a:Zipcode {zipcode: '10001'})
MATCH (b:Zipcode {zipcode: '10002'})
CREATE (a)-[:NEIGHBORS {
    distanceKm: 2.34,
    isAdjacent: true,
    computedDate: date('2024-01-15')
}]->(b)
CREATE (b)-[:NEIGHBORS {
    distanceKm: 2.34,
    isAdjacent: true,
    computedDate: date('2024-01-15')
}]->(a)
```

**数据量估算:**
- 177 ZIPs × 平均 8 neighbors = ~1,400 relationships
- 双向存储 = ~2,800 relationships total

**Neo4j 优势:**

```cypher
// 查询 1: 查找 10001 的所有邻居
MATCH (z:Zipcode {zipcode: '10001'})-[:NEIGHBORS]->(neighbor)
RETURN neighbor.zipcode, neighbor.borough
ORDER BY neighbor.zipcode

// 查询 2: 2-hop neighbors (邻居的邻居)
MATCH path = (z:Zipcode {zipcode: '10001'})-[:NEIGHBORS*1..2]->(neighbor)
WITH DISTINCT neighbor, min(length(path)) AS hops
RETURN neighbor.zipcode, hops
ORDER BY hops, neighbor.zipcode

// 查询 3: 查找 5km 范围内的所有 ZIPs
MATCH (z:Zipcode {zipcode: '10001'})-[r:NEIGHBORS]->(neighbor)
WHERE r.distanceKm < 5.0
RETURN neighbor.zipcode, r.distanceKm
ORDER BY r.distanceKm
```

---

#### 2.2 LOCATED_IN 关系 (Building → Zipcode)

**PostgreSQL FK (已存在):**
```sql
ALTER TABLE buildings
ADD CONSTRAINT fk_building_zipcode
FOREIGN KEY (zipcode_id) REFERENCES zipcodes(zipcode_id);
```

**Neo4j 关系设计:**

```cypher
MATCH (b:Building {bbl: '1000010101'})
MATCH (z:Zipcode {zipcode: '10001'})
CREATE (b)-[:LOCATED_IN]->(z)
```

**数据量:**
- ~100,000 relationships (每个 building 一个)

**Neo4j 优势:**

```cypher
// 查询 1: 某 ZIP 内的所有建筑
MATCH (b:Building)-[:LOCATED_IN]->(z:Zipcode {zipcode: '10001'})
RETURN count(b) AS totalBuildings,
       avg(b.yearBuilt) AS avgYearBuilt,
       sum(b.unitsResidential) AS totalUnits

// 查询 2: 高租金负担 ZIP 内的老建筑
MATCH (b:Building)-[:LOCATED_IN]->(z:Zipcode)
WHERE z.pctRentBurden50 > 25.0  -- 严重租金负担
  AND b.yearBuilt < 1960
RETURN z.zipcode, count(b) AS oldBuildings
ORDER BY oldBuildings DESC

// 查询 3: 邻近 ZIP 内的所有建筑
MATCH (start:Zipcode {zipcode: '10001'})-[:NEIGHBORS]-(neighbor)-[:LOCATED_IN]-(b:Building)
WHERE b.yearBuilt < 1980
RETURN neighbor.zipcode, count(b) AS oldBuildings
```

---

#### 2.3 HAS_PROJECT 关系 (Zipcode → HousingProject)

**Neo4j 关系设计:**

```cypher
MATCH (z:Zipcode {zipcode: '10001'})
MATCH (p:HousingProject {projectId: 'HPD-2023-001'})
CREATE (z)-[:HAS_PROJECT]->(p)

// 或反向 (取决于查询模式)
CREATE (p)-[:LOCATED_IN]->(z)
```

**推荐:** 使用 `(HousingProject)-[:LOCATED_IN]->(Zipcode)` - 与 Building 保持一致

**Neo4j 优势:**

```cypher
// 查询 1: 某 ZIP 的所有保障房项目
MATCH (p:HousingProject)-[:LOCATED_IN]->(z:Zipcode {zipcode: '10001'})
RETURN p.projectName, p.totalUnits, p.affordableUnits

// 查询 2: 高租金负担 ZIP 的保障房缺口
MATCH (z:Zipcode)
WHERE z.pctRentBurden50 > 20.0
OPTIONAL MATCH (p:HousingProject)-[:LOCATED_IN]->(z)
RETURN z.zipcode,
       z.pctRentBurden50,
       count(p) AS numProjects,
       sum(p.affordableUnits) AS totalAffordableUnits
ORDER BY z.pctRentBurden50 DESC

// 查询 3: 邻近 ZIP 的保障房项目
MATCH (start:Zipcode {zipcode: '10001'})-[:NEIGHBORS]-(neighbor)
MATCH (p:HousingProject)-[:LOCATED_IN]->(neighbor)
RETURN neighbor.zipcode, collect(p.projectName) AS projects
```

---

### 分类 3: 派生和计算字段 (Computed → Properties)

以下字段应在 PostgreSQL 中计算后作为节点属性存储：

#### 3.1 Affordability Score (租金可负担性评分)

**PostgreSQL 计算:**
```sql
ALTER TABLE zipcodes
ADD COLUMN affordability_score DOUBLE PRECISION;

UPDATE zipcodes
SET affordability_score =
    CASE
        WHEN median_household_income = 0 THEN NULL
        ELSE (median_rent_1br * 12) / median_household_income * 100
    END;
```

**Neo4j 属性:**
```cypher
// 在 Zipcode 节点中
{
    affordabilityScore: 45.2,  -- 租金占收入的百分比
    affordabilityCategory: CASE
        WHEN affordabilityScore < 30 THEN 'Affordable'
        WHEN affordabilityScore < 50 THEN 'Moderate'
        ELSE 'Unaffordable'
    END
}
```

#### 3.2 Building Age Category

**PostgreSQL 计算:**
```sql
ALTER TABLE buildings
ADD COLUMN age_category VARCHAR(20);

UPDATE buildings
SET age_category =
    CASE
        WHEN year_built < 1950 THEN 'Pre-War'
        WHEN year_built < 1980 THEN 'Post-War'
        WHEN year_built < 2000 THEN 'Modern'
        ELSE 'Contemporary'
    END;
```

**Neo4j 属性:**
```cypher
// 在 Building 节点中
{
    yearBuilt: 1935,
    ageCategory: 'Pre-War',
    buildingAge: 2024 - 1935  // 89 years
}
```

#### 3.3 Neighborhood Risk Score

**PostgreSQL 计算 (多因素):**
```sql
ALTER TABLE zipcodes
ADD COLUMN risk_score DOUBLE PRECISION;

UPDATE zipcodes
SET risk_score = (
    (pct_rent_burden_50 * 0.4) +
    (CASE WHEN median_household_income < 50000 THEN 30 ELSE 0 END) +
    (CASE WHEN vacancy_rate > 10 THEN 20 ELSE 0 END) +
    ((median_rent_1br / 3000.0) * 10)
);
```

**Neo4j 属性:**
```cypher
{
    riskScore: 67.5,
    riskCategory: CASE
        WHEN riskScore > 70 THEN 'High Risk'
        WHEN riskScore > 50 THEN 'Moderate Risk'
        ELSE 'Low Risk'
    END
}
```

---

## 🔄 完整迁移流程

### Phase 1: PostgreSQL 预计算 (在现有数据库中)

```sql
-- 1. 计算 ZIP 中心点
CREATE TABLE zip_centroids AS
SELECT
    zipcode_id,
    zip_code,
    ST_Y(ST_Centroid(geometry)) AS center_lat,
    ST_X(ST_Centroid(geometry)) AS center_lon,
    ST_AsText(geometry) AS geometry_wkt,
    ST_Area(geometry::geography) / 1000000.0 AS area_km2
FROM zipcodes;

-- 2. 计算 NEIGHBORS 关系
CREATE TABLE zip_neighbors AS
SELECT
    a.zip_code AS from_zip,
    b.zip_code AS to_zip,
    ST_Distance(
        ST_Centroid(a.geometry)::geography,
        ST_Centroid(b.geometry)::geography
    ) / 1000.0 AS distance_km,
    ST_Touches(a.geometry, b.geometry) AS is_adjacent
FROM zipcodes a
CROSS JOIN zipcodes b
WHERE a.zip_code < b.zip_code
  AND ST_DWithin(a.geometry, b.geometry, 10000);

-- 3. 验证 Building-Zipcode 关系
CREATE TABLE building_zip_validation AS
SELECT
    b.building_id,
    b.bbl,
    b.zipcode_id AS declared_zipcode,
    z.zip_code AS spatial_zipcode
FROM buildings b
LEFT JOIN zipcodes z ON ST_Contains(z.geometry, b.geometry)
WHERE b.zipcode_id IS NOT NULL;

-- 4. 计算派生字段
UPDATE zipcodes SET affordability_score = ...;
UPDATE buildings SET age_category = ...;
UPDATE zipcodes SET risk_score = ...;
```

### Phase 2: 提取数据到 Neo4j

**Python ETL Script:**

```python
from sqlalchemy import create_engine
from neo4j import GraphDatabase
import pandas as pd

# 连接数据库
pg_engine = create_engine('postgresql://...')
neo4j_driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))

def migrate_zipcodes():
    """迁移 Zipcode 节点"""
    query = """
    SELECT
        z.zip_code,
        z.borough,
        c.center_lat,
        c.center_lon,
        c.area_km2,
        c.geometry_wkt,
        z.median_household_income,
        z.median_rent_1br,
        z.median_rent_2br,
        z.pct_rent_burden_30,
        z.pct_rent_burden_50,
        z.total_population,
        z.vacancy_rate,
        z.affordability_score,
        z.risk_score
    FROM zipcodes z
    JOIN zip_centroids c ON z.zipcode_id = c.zipcode_id
    """

    df = pd.read_sql(query, pg_engine)

    with neo4j_driver.session() as session:
        for _, row in df.iterrows():
            session.run("""
                CREATE (z:Zipcode {
                    zipcode: $zipcode,
                    borough: $borough,
                    location: point({
                        latitude: $lat,
                        longitude: $lon,
                        crs: 'WGS-84'
                    }),
                    centerLat: $lat,
                    centerLon: $lon,
                    areaKm2: $area,
                    geometryWKT: $wkt,
                    medianHouseholdIncome: $income,
                    medianRent1br: $rent1br,
                    medianRent2br: $rent2br,
                    pctRentBurden30: $burden30,
                    pctRentBurden50: $burden50,
                    totalPopulation: $pop,
                    vacancyRate: $vacancy,
                    affordabilityScore: $affScore,
                    riskScore: $riskScore
                })
            """,
            zipcode=row['zip_code'],
            borough=row['borough'],
            lat=row['center_lat'],
            lon=row['center_lon'],
            area=row['area_km2'],
            wkt=row['geometry_wkt'],
            income=row['median_household_income'],
            rent1br=row['median_rent_1br'],
            rent2br=row['median_rent_2br'],
            burden30=row['pct_rent_burden_30'],
            burden50=row['pct_rent_burden_50'],
            pop=row['total_population'],
            vacancy=row['vacancy_rate'],
            affScore=row['affordability_score'],
            riskScore=row['risk_score']
            )

def migrate_neighbors():
    """创建 NEIGHBORS 关系"""
    query = "SELECT * FROM zip_neighbors"
    df = pd.read_sql(query, pg_engine)

    with neo4j_driver.session() as session:
        # 批量创建 (使用 UNWIND)
        session.run("""
            UNWIND $neighbors AS n
            MATCH (a:Zipcode {zipcode: n.from_zip})
            MATCH (b:Zipcode {zipcode: n.to_zip})
            CREATE (a)-[:NEIGHBORS {
                distanceKm: n.distance_km,
                isAdjacent: n.is_adjacent
            }]->(b)
            CREATE (b)-[:NEIGHBORS {
                distanceKm: n.distance_km,
                isAdjacent: n.is_adjacent
            }]->(a)
        """, neighbors=df.to_dict('records'))

def migrate_buildings():
    """迁移 Building 节点 (批量处理)"""
    batch_size = 1000
    offset = 0

    while True:
        query = f"""
        SELECT
            bbl, bin, address, year_built, num_floors,
            units_residential, landuse_category,
            latitude, longitude, zip_code
        FROM buildings b
        JOIN zipcodes z ON b.zipcode_id = z.zipcode_id
        LIMIT {batch_size} OFFSET {offset}
        """

        df = pd.read_sql(query, pg_engine)
        if df.empty:
            break

        with neo4j_driver.session() as session:
            session.run("""
                UNWIND $buildings AS b
                CREATE (bldg:Building {
                    bbl: b.bbl,
                    bin: b.bin,
                    address: b.address,
                    yearBuilt: b.year_built,
                    numFloors: b.num_floors,
                    unitsResidential: b.units_residential,
                    landuseCategory: b.landuse_category,
                    location: point({
                        latitude: b.latitude,
                        longitude: b.longitude,
                        crs: 'WGS-84'
                    })
                })
            """, buildings=df.to_dict('records'))

        offset += batch_size
        print(f"Migrated {offset} buildings...")

# 执行迁移
migrate_zipcodes()
migrate_neighbors()
migrate_buildings()
# ... 其他迁移函数
```

### Phase 3: 验证

```cypher
// 验证节点数量
MATCH (z:Zipcode) RETURN count(z) AS zipcodes;  // 应该是 177
MATCH (b:Building) RETURN count(b) AS buildings;  // 应该是 ~100,000
MATCH (p:HousingProject) RETURN count(p) AS projects;

// 验证关系数量
MATCH ()-[r:NEIGHBORS]->() RETURN count(r) AS neighbors;
MATCH ()-[r:LOCATED_IN]->() RETURN count(r) AS locatedIn;

// 验证数据完整性
MATCH (z:Zipcode)
WHERE z.medianHouseholdIncome IS NULL
RETURN count(z) AS missingIncome;

// 抽样验证
MATCH (z:Zipcode {zipcode: '10001'})
RETURN z;

MATCH (z:Zipcode {zipcode: '10001'})-[:NEIGHBORS]->(n)
RETURN n.zipcode, n.borough
ORDER BY n.zipcode;
```

---

## 📈 Neo4j 图模型优势示例

### 优势 1: Multi-Hop 查询 (邻居的邻居)

**PostgreSQL (复杂 self-join):**
```sql
-- 查找 10001 的 2-hop neighbors
SELECT DISTINCT z3.zip_code,
    CASE
        WHEN z2.zip_code IS NULL THEN 1
        ELSE 2
    END AS hops
FROM zipcodes z1
LEFT JOIN zip_neighbors n1 ON z1.zip_code = n1.from_zip
LEFT JOIN zipcodes z2 ON n1.to_zip = z2.zip_code
LEFT JOIN zip_neighbors n2 ON z2.zip_code = n2.from_zip
LEFT JOIN zipcodes z3 ON n2.to_zip = z3.zip_code
WHERE z1.zip_code = '10001'
  AND z3.zip_code <> '10001';
```

**Neo4j (简洁):**
```cypher
MATCH path = (z:Zipcode {zipcode: '10001'})-[:NEIGHBORS*1..2]->(neighbor)
WITH DISTINCT neighbor, min(length(path)) AS hops
RETURN neighbor.zipcode, neighbor.borough, hops
ORDER BY hops, neighbor.zipcode
```

---

### 优势 2: 路径分析

**查询: 查找连接两个 ZIP 的最短路径**

**Neo4j:**
```cypher
MATCH path = shortestPath(
    (start:Zipcode {zipcode: '10001'})-[:NEIGHBORS*]-(end:Zipcode {zipcode: '11201'})
)
RETURN [n IN nodes(path) | n.zipcode] AS path,
       length(path) AS hops,
       reduce(dist = 0.0, r IN relationships(path) | dist + r.distanceKm) AS totalDistance
```

**PostgreSQL:** 需要递归 CTE，非常复杂

---

### 优势 3: 模式匹配

**查询: 查找"保障房沙漠" - 高租金负担但缺乏保障房的区域**

**Neo4j:**
```cypher
MATCH (z:Zipcode)
WHERE z.pctRentBurden50 > 25.0  -- 严重租金负担
  AND z.medianHouseholdIncome < 60000
OPTIONAL MATCH (p:HousingProject)-[:LOCATED_IN]->(z)
WITH z, count(p) AS numProjects, sum(p.affordableUnits) AS affordableUnits
WHERE numProjects < 2  -- 少于 2 个项目
RETURN z.zipcode, z.borough,
       z.pctRentBurden50,
       z.medianHouseholdIncome,
       coalesce(affordableUnits, 0) AS affordableUnits
ORDER BY z.pctRentBurden50 DESC
```

---

### 优势 4: 聚合跨关系

**查询: 邻近 ZIP 的老建筑统计**

**Neo4j:**
```cypher
MATCH (center:Zipcode {zipcode: '10001'})-[:NEIGHBORS]-(neighbor)
MATCH (b:Building)-[:LOCATED_IN]->(neighbor)
WHERE b.yearBuilt < 1960
RETURN neighbor.zipcode,
       count(b) AS oldBuildings,
       avg(b.numFloors) AS avgFloors,
       sum(b.unitsResidential) AS totalUnits
ORDER BY oldBuildings DESC
```

**PostgreSQL:** 需要多个 JOIN

---

## 🎯 Text2Cypher 查询示例 (>75% 目标)

为了达到 >75% 准确率，需要提供以下 Few-Shot Examples:

### Example Set 1: 简单过滤

**Q1:** "Which ZIP codes have median rent above $4000?"
```cypher
MATCH (z:Zipcode)
WHERE z.medianRent1br > 4000
RETURN z.zipcode, z.borough, z.medianRent1br
ORDER BY z.medianRent1br DESC
```

**Q2:** "Show me all ZIPs in Brooklyn with high rent burden"
```cypher
MATCH (z:Zipcode)
WHERE z.borough = 'Brooklyn'
  AND z.pctRentBurden50 > 20.0
RETURN z.zipcode, z.pctRentBurden50, z.medianHouseholdIncome
ORDER BY z.pctRentBurden50 DESC
```

### Example Set 2: 空间查询

**Q3:** "Find ZIPs within 5km of 10001"
```cypher
MATCH (center:Zipcode {zipcode: '10001'})-[r:NEIGHBORS]->(nearby)
WHERE r.distanceKm < 5.0
RETURN nearby.zipcode, r.distanceKm
ORDER BY r.distanceKm
```

**Q4:** "Which ZIPs are neighbors of 10001?"
```cypher
MATCH (z:Zipcode {zipcode: '10001'})-[:NEIGHBORS]->(neighbor)
RETURN neighbor.zipcode, neighbor.borough
ORDER BY neighbor.zipcode
```

### Example Set 3: Multi-Hop

**Q5:** "Find all ZIPs within 2 hops of 10001"
```cypher
MATCH path = (start:Zipcode {zipcode: '10001'})-[:NEIGHBORS*1..2]->(end)
WITH DISTINCT end, min(length(path)) AS hops
RETURN end.zipcode, end.borough, hops
ORDER BY hops, end.zipcode
```

### Example Set 4: 聚合

**Q6:** "How many affordable housing projects are in each borough?"
```cypher
MATCH (p:HousingProject)-[:LOCATED_IN]->(z:Zipcode)
RETURN z.borough,
       count(p) AS numProjects,
       sum(p.totalUnits) AS totalUnits,
       sum(p.affordableUnits) AS affordableUnits
ORDER BY numProjects DESC
```

### Example Set 5: 组合查询

**Q7:** "Find affordable housing projects in ZIPs neighboring 10001"
```cypher
MATCH (start:Zipcode {zipcode: '10001'})-[:NEIGHBORS]-(neighbor)
MATCH (p:HousingProject)-[:LOCATED_IN]->(neighbor)
RETURN neighbor.zipcode,
       count(p) AS numProjects,
       sum(p.affordableUnits) AS affordableUnits
ORDER BY numProjects DESC
```

**Q8:** "Show old buildings in high rent burden neighborhoods"
```cypher
MATCH (b:Building)-[:LOCATED_IN]->(z:Zipcode)
WHERE b.yearBuilt < 1960
  AND z.pctRentBurden50 > 25.0
RETURN z.zipcode, count(b) AS oldBuildings
ORDER BY oldBuildings DESC
```

---

## 📊 完整数据清单

### 需要迁移的数据

| 数据类型 | PostgreSQL 来源 | Neo4j 目标 | 数量估算 | 优先级 |
|---------|----------------|-----------|---------|--------|
| **节点** |
| Zipcode | `zipcodes` 表 | `:Zipcode` 节点 | 177 | P0 (必须) |
| Building | `buildings` 表 | `:Building` 节点 | ~100,000 | P0 (必须) |
| HousingProject | `housing_projects` 表 | `:HousingProject` 节点 | 1,000-5,000 | P1 (重要) |
| **关系** |
| ZIP 邻接 | PostGIS 计算 | `:NEIGHBORS` | ~2,800 (双向) | P0 (必须) |
| Building → ZIP | FK | `:LOCATED_IN` | ~100,000 | P0 (必须) |
| Project → ZIP | FK | `:LOCATED_IN` | 1,000-5,000 | P1 (重要) |
| **属性** |
| 人口统计 | `demographics` 表 | Zipcode properties | 177 × 10+ fields | P0 (必须) |
| 收入指标 | `income_metrics` 表 | Zipcode properties | 177 × 5+ fields | P0 (必须) |
| 租金指标 | `rent_metrics` 表 | Zipcode properties | 177 × 8+ fields | P0 (必须) |
| 住房存量 | `housing_stock` 表 | Zipcode properties | 177 × 6+ fields | P0 (必须) |
| 空间数据 | PostGIS 计算 | Point properties | 177 + 100,000 | P0 (必须) |

### 需要在 PostgreSQL 中预计算

| 计算内容 | 输入 | 输出 | 存储位置 |
|---------|-----|------|---------|
| ZIP 中心点 | `geometry` | `center_lat`, `center_lon` | `zip_centroids` 表 |
| ZIP 面积 | `geometry` | `area_km2` | `zip_centroids` 表 |
| ZIP 邻接 | `geometry` (ST_Touches) | `from_zip`, `to_zip`, `is_adjacent` | `zip_neighbors` 表 |
| ZIP 距离 | `geometry` (ST_Distance) | `distance_km` | `zip_neighbors` 表 |
| Building 位置 | `geometry` | `latitude`, `longitude` | `buildings` 表 |
| 可负担性评分 | `median_rent`, `median_income` | `affordability_score` | `zipcodes` 表 |
| 风险评分 | 多因素 | `risk_score` | `zipcodes` 表 |

---

## ⚡ 性能优化建议

### Neo4j 索引和约束

```cypher
// 唯一性约束 (自动创建索引)
CREATE CONSTRAINT zipcode_unique IF NOT EXISTS
FOR (z:Zipcode) REQUIRE z.zipcode IS UNIQUE;

CREATE CONSTRAINT building_bbl_unique IF NOT EXISTS
FOR (b:Building) REQUIRE b.bbl IS UNIQUE;

CREATE CONSTRAINT project_id_unique IF NOT EXISTS
FOR (p:HousingProject) REQUIRE p.projectId IS UNIQUE;

// 复合索引 (用于常见查询)
CREATE INDEX zipcode_borough IF NOT EXISTS
FOR (z:Zipcode) ON (z.borough);

CREATE INDEX zipcode_burden IF NOT EXISTS
FOR (z:Zipcode) ON (z.pctRentBurden50);

CREATE INDEX building_year IF NOT EXISTS
FOR (b:Building) ON (b.yearBuilt);

// 全文搜索索引 (用于地址搜索)
CREATE FULLTEXT INDEX building_address IF NOT EXISTS
FOR (b:Building) ON EACH [b.address];
```

### 批量导入优化

```python
# 使用 batch 导入 (UNWIND)
def batch_import(session, query, data, batch_size=1000):
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        session.run(query, {'batch': batch})
```

---

## ✅ 验证清单

### 数据完整性

- [ ] 节点数量匹配 PostgreSQL 行数
- [ ] 关系数量正确 (双向关系 = 2x 单向)
- [ ] 所有 Building 都有 LOCATED_IN 关系
- [ ] 所有 HousingProject 都有 LOCATED_IN 关系
- [ ] 没有孤立节点 (orphan nodes)

### 空间数据

- [ ] 所有 Zipcode 都有 location Point
- [ ] Point 坐标在 NYC 范围内 (lat: 40.5-40.9, lon: -74.3--73.7)
- [ ] NEIGHBORS 关系的 distanceKm > 0
- [ ] NEIGHBORS 关系是双向的

### 属性数据

- [ ] 关键属性不为 NULL (zipcode, borough, etc.)
- [ ] 数值范围合理 (medianRent > 0, pctRentBurden <= 100)
- [ ] 数据类型正确 (Integer, Float, Date, Point)

### Text2Cypher

- [ ] 至少 15/20 测试问题正确 (>75%)
- [ ] 简单查询 100% 正确
- [ ] 空间查询 >80% 正确
- [ ] Multi-hop 查询 >70% 正确

---

## 🎯 总结和建议

### 推荐迁移策略

1. **全面迁移** - 迁移所有 177 ZIPs, ~100,000 Buildings, 所有保障房项目
2. **空间关系优先** - NEIGHBORS 关系是 Neo4j 优势的核心
3. **属性扁平化** - Demographics/Income/Rent 作为 Zipcode 属性 (除非需要时间序列)
4. **双向关系** - 所有 NEIGHBORS 关系双向存储
5. **批量导入** - 使用 UNWIND 批量创建节点和关系

### 项目成功关键

1. ✅ **PostgreSQL 预计算完整** - 所有空间关系提前计算好
2. ✅ **验证每个步骤** - 节点、关系、属性逐步验证
3. ✅ **Few-shot Examples 丰富** - 至少 20 个高质量示例
4. ✅ **性能基准测试** - SQL vs Cypher 对比清晰
5. ✅ **文档齐全** - 每个步骤都有文档

### 下一步行动

1. **Phase 1:** 在 PostgreSQL 中执行所有预计算 SQL (1-2 天)
2. **Phase 2:** 实现 Python ETL 脚本 (2-3 天)
3. **Phase 3:** 迁移 Zipcode 和 NEIGHBORS (MVP 验证) (1 天)
4. **Phase 4:** 迁移 Buildings (批量处理) (1-2 天)
5. **Phase 5:** 迁移 HousingProjects (1 天)
6. **Phase 6:** Text2Cypher 测试和优化 (2-3 天)
7. **Phase 7:** 性能基准测试 (1-2 天)

---

**总数据量估算:**
- **节点:** 177 + 100,000 + 3,000 = ~103,177 nodes
- **关系:** 2,800 + 100,000 + 3,000 = ~105,800 relationships
- **属性:** 每个 Zipcode ~30 properties, 每个 Building ~10 properties

**迁移时间估算:** 2-3 周 (包括测试和验证)

---

**文档版本:** 1.0
**最后更新:** 2026-02-20
**状态:** Ready for Implementation
