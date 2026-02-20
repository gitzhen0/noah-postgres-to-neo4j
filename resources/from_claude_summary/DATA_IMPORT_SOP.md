# NOAH Database Data Import SOP

**目的：** 完整还原 Yue Yu (Becky0713/NOAH) 的 PostgreSQL 数据库到本地环境，零 mock/placeholder 数据。
**原则：** 该空着的空着，该真实的一定真实，绝不用假数据填充。

---

## 0. 环境前置条件

| 依赖 | 版本 | 说明 |
|------|------|------|
| Docker | any | 运行 PostgreSQL + Neo4j |
| postgis/postgis image | 14-3.3 | PostGIS 支持 |
| Neo4j | 5.15.0 | 图数据库 |
| Python | 3.10+ | 数据加载脚本 |
| psycopg2 | any | PG 驱动 |
| requests / pandas | any | HTTP + 数据处理 |
| geopandas | 1.1.2+ | 加载 TIGER shapefile |
| shapely | 2.1.2+ | 几何计算 |

**Docker 启动命令：**

```bash
# PostgreSQL + PostGIS
docker run -d \
  --name noah-postgres \
  -e POSTGRES_DB=noah_housing \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password123 \
  -p 5432:5432 \
  postgis/postgis:14-3.3

# Neo4j
docker run -d \
  --name noah-neo4j \
  -e NEO4J_AUTH=neo4j/password123 \
  -p 7474:7474 -p 7687:7687 \
  neo4j:5.15.0
```

---

## 1. 数据库 Schema 建立

**来源：** `https://github.com/Becky0713/NOAH` (branch: master)
**关键文件：** `database_schema.sql` + `backend/migrations/001_create_housing_projects_table.sql`

### 1.1 执行顺序

```sql
-- Step 1: 启用 PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- Step 2: 创建核心表（按依赖顺序）
-- 见下方各小节
```

### 1.2 表结构（与 Yue 的 schema 对齐）

#### `housing_projects` (核心表)

```sql
CREATE TABLE housing_projects (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(50) NOT NULL,   -- 注意：NOT UNIQUE（见 §5 Trade-offs）
    project_name TEXT,
    building_id VARCHAR(50),
    house_number VARCHAR(50),          -- Yue 原始 VARCHAR(20)，但 Socrata 数据有超长值，需扩展
    street_name VARCHAR(100),
    borough VARCHAR(50),
    postcode VARCHAR(10),
    bbl VARCHAR(50),                   -- 扩展自 VARCHAR(20)
    bin VARCHAR(50),                   -- 扩展自 VARCHAR(20)
    community_board VARCHAR(100),      -- 扩展自 VARCHAR(20)
    council_district INTEGER,
    census_tract VARCHAR(50),          -- 扩展自 VARCHAR(20)
    neighborhood_tabulation_area VARCHAR(50),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    latitude_internal DECIMAL(10,8),
    longitude_internal DECIMAL(11,8),
    geom GEOMETRY(POINT, 4326),        -- 由 trigger 自动从 lat/lon 生成
    project_start_date DATE,
    project_completion_date DATE,
    building_completion_date DATE,
    reporting_construction_type VARCHAR(200),
    extended_affordability_status VARCHAR(100),
    prevailing_wage_status VARCHAR(100),
    extremely_low_income_units INTEGER DEFAULT 0,
    very_low_income_units INTEGER DEFAULT 0,
    low_income_units INTEGER DEFAULT 0,
    moderate_income_units INTEGER DEFAULT 0,
    middle_income_units INTEGER DEFAULT 0,
    other_income_units INTEGER DEFAULT 0,
    studio_units INTEGER DEFAULT 0,
    _1_br_units INTEGER DEFAULT 0,
    _2_br_units INTEGER DEFAULT 0,
    _3_br_units INTEGER DEFAULT 0,
    _4_br_units INTEGER DEFAULT 0,
    _5_br_units INTEGER DEFAULT 0,
    _6_br_units INTEGER DEFAULT 0,
    unknown_br_units INTEGER DEFAULT 0,
    counted_rental_units INTEGER DEFAULT 0,
    counted_homeownership_units INTEGER DEFAULT 0,
    all_counted_units INTEGER DEFAULT 0,
    total_units INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(50) DEFAULT 'socrata'
);
```

**关键 Trigger（自动生成 geom）：**
```sql
CREATE OR REPLACE FUNCTION update_housing_geometry()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.geom = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    END IF;
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER trigger_update_housing_geometry
    BEFORE INSERT OR UPDATE ON housing_projects
    FOR EACH ROW EXECUTE FUNCTION update_housing_geometry();
```

#### ACS 数据表（Census Bureau）

```sql
-- 从 ACS B19013 加载
CREATE TABLE median_household_income (
    geo_id TEXT PRIMARY KEY,          -- 11-char GEOID, e.g. "36061000100"
    tract_name TEXT,
    median_household_income NUMERIC(12,2),
    county TEXT,
    borough TEXT
);

-- 从 ACS B25070 加载
CREATE TABLE rent_burden (
    geo_id TEXT PRIMARY KEY,
    tract_name TEXT,
    rent_burden_rate NUMERIC,         -- 小数形式 0-1 (e.g. 0.42 = 42%)
    severe_burden_rate NUMERIC,
    geometry GEOMETRY(Geometry, 4326) -- 注意：不限 Polygon/MultiPolygon（见 §5）
);

-- 从 ACS B25074 加载
CREATE TABLE rent_income_distribution (
    id SERIAL PRIMARY KEY,
    geo_id TEXT,
    tract_name TEXT,
    income_bracket TEXT,
    rent_bracket TEXT,
    household_count INTEGER,
    variable_code TEXT
);
```

#### 空间关联表

```sql
-- HUD/Census ZCTA-to-Tract 权重表
CREATE TABLE zip_tract_crosswalk (
    zip_code VARCHAR(10),
    tract VARCHAR(15),
    tot_ratio NUMERIC(8,6),
    PRIMARY KEY (zip_code, tract)
);

-- NYC ZIP 边界（来自 NYC Open Data）
CREATE TABLE zip_shapes (
    zip_code VARCHAR(10) PRIMARY KEY,
    geom GEOMETRY(MultiPolygon, 4326),
    borough VARCHAR(50)
);
```

#### ZIP 级别聚合表（Yue 的命名）

```sql
CREATE TABLE noah_zip_income (
    zip_code VARCHAR(5) PRIMARY KEY,
    median_income_usd NUMERIC(10,2)
);

CREATE TABLE noah_zip_rentburden (
    zip_code VARCHAR(5) PRIMARY KEY,
    rent_burden_rate NUMERIC(5,2),
    severe_burden_rate NUMERIC(5,2)
);

CREATE TABLE noah_streeteasy_medianrent_2025_10 (
    id SERIAL PRIMARY KEY,
    zip_code VARCHAR(15),
    bedroom_type TEXT,
    median_rent_usd NUMERIC(10,2),
    year INTEGER,
    month INTEGER,
    UNIQUE (zip_code, bedroom_type, year, month)
);

CREATE TABLE noah_zip_medianrent (
    zip_code VARCHAR(10) PRIMARY KEY,
    bedroom_type TEXT,
    median_rent_usd NUMERIC(10,2)
);

CREATE TABLE noah_affordability_analysis (
    zip_code VARCHAR(5) PRIMARY KEY,
    median_income_usd NUMERIC(10,2),
    rent_burden_rate NUMERIC(5,2),
    severe_burden_rate NUMERIC(5,2),
    median_rent_usd NUMERIC(10,2),       -- NULL if no StreetEasy data
    rent_to_income_ratio NUMERIC(5,3)    -- NULL if no StreetEasy data
);
```

---

## 2. 数据导入步骤（SOP）

### Step 1 — `housing_projects`：从 Socrata API

**API 端点：** `https://data.cityofnewyork.us/resource/hg8x-zxpr.json`
**数据集：** NYC Affordable Housing Production by Building
**总行数：** 8,604（2025年2月）

```python
import requests, psycopg2

SOCRATA_URL = "https://data.cityofnewyork.us/resource/hg8x-zxpr.json"
BATCH = 1000

offset = 0
while True:
    data = requests.get(SOCRATA_URL, params={"$limit": BATCH, "$offset": offset}).json()
    if not data:
        break
    for row in data:
        # 使用 SAVEPOINT 实现逐行错误处理，不让单行失败影响整批
        cur.execute("SAVEPOINT sp")
        try:
            cur.execute("INSERT INTO housing_projects (...) VALUES (...)", (...))
            cur.execute("RELEASE SAVEPOINT sp")
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT sp")
            cur.execute("RELEASE SAVEPOINT sp")
    conn.commit()
    offset += BATCH
```

**注意事项：**
- 用 SAVEPOINT 逐行保护，不要用 try/except + `conn.rollback()` 批量回滚
- VARCHAR 字段需要比 Yue 原始 schema 更宽（见 §5）
- geom 由 trigger 自动生成，只要 lat/lon 有值即可
- **1,718 行没有 lat/lon/postcode**：这是 Socrata 源数据本身的缺失，不是 bug，保留 NULL

---

### Step 2 — `zip_shapes`：NYC ZIP 边界

**来源：** NYC Open Data ZIP Code GeoJSON
**真实 ZIP 数量：** 177（删除占位符 `99999`）

```python
# 从 NYC Open Data 或预处理 GeoJSON 加载
# 确保删除 zip_code = '99999' 这类占位符
gdf = gpd.read_file("nyc_zip_codes.geojson").to_crs("EPSG:4326")
gdf = gdf[gdf['zip_code'] != '99999']  # 过滤假 ZIP
```

---

### Step 3 — ACS 数据：Census API

**API Key 所需：** 是
**Base URL：** `https://api.census.gov/data/2022/acs/acs5`
**纽约五个县代码：** Manhattan=061, Bronx=005, Brooklyn=047, Queens=081, Staten Island=085

#### B19013 → `median_household_income`

```python
vars_ = ["B19013_001E", "NAME"]
for county in ["061","005","047","081","085"]:
    data = census_get({"get": ",".join(vars_), "for": "tract:*", "in": f"state:36+county:{county}"})
    # geo_id = f"36{county}{tract}"  # 11-char GEOID
    # median_income = float(B19013_001E) if > 0 else NULL
```

**注意：** Census API 返回 `-666666666` 表示数据不可用，需过滤为 NULL。
**结果：** 2,201 条 tract 记录

#### B25070 → `rent_burden`（rates only，geometry 后续补）

```python
# B25070_001E: total renter-occupied
# B25070_007E ~ B25070_010E: 30%+ rent burden households
# rent_burden_rate = (007+008+009+010) / 001
# severe_burden_rate = 010 / 001  (50%+ of income)
```

**结果：** 2,225 条 tract 记录，值域 0-1 小数格式

#### B25074 → `rent_income_distribution`

```python
# 约 7×7 = 49 个变量的交叉分布表
# 每个 tract × 49 变量 = 约 130,312 行
```

**结果：** 130,312 行（最大表）

---

### Step 4 — `rent_burden.geometry`：Census TIGER

**来源：** `https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_36_tract_500k.zip`
**说明：** 纽约州所有 census tract 的多边形边界

```python
# 1. 先将 rent_burden.geometry 列改为接受任意几何类型
# ALTER TABLE rent_burden ALTER COLUMN geometry TYPE geometry(Geometry, 4326)
# （原因：部分 tract 是 MultiPolygon，不能用 POLYGON 约束）

gdf = gpd.read_file("cb_2022_36_tract_500k.shp").to_crs("EPSG:4326")
gdf['geoid11'] = gdf['GEOID'].str.zfill(11)
for _, row in gdf.iterrows():
    cur.execute("UPDATE rent_burden SET geometry = ST_GeomFromText(%s, 4326) WHERE geo_id = %s",
                (row['geometry'].wkt, row['geoid11']))
```

**结果：** 2,225/2,225 行全部有 geometry

---

### Step 5 — `zip_tract_crosswalk`：Census 面积权重

**来源：** `https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_tract20_natl.txt`
**编码：** UTF-8-BOM，需用 `r.content.decode('utf-8-sig')`
**分隔符：** pipe (`|`)

```python
df = pd.read_csv(io.StringIO(content), sep='|', dtype=str)
# 过滤 NY state（GEOID_TRACT_20 以 "36" 开头）
df_ny = df[df['GEOID_TRACT_20'].str.startswith('36')]
# 计算面积权重
df_ny['tot_ratio'] = df_ny['AREALAND_PART'].astype(float) / df_ny['AREALAND_TRACT_20'].astype(float)
# 只保留在我们 zip_shapes 里的 ZIP
```

**关键字段：**
- `AREALAND_PART`：ZIP∩Tract 交叉区域的陆地面积
- `AREALAND_TRACT_20`：该 Tract 的总陆地面积
- `tot_ratio = AREALAND_PART / AREALAND_TRACT_20`：表示该 Tract 有多少比例属于这个 ZIP

**结果：** 3,071 行，avg_ratio=0.7464（之前用 1.0 占位符时是错的）

---

### Step 6 — ZIP 级别聚合

```sql
-- noah_zip_income (weighted average)
INSERT INTO noah_zip_income (zip_code, median_income_usd)
SELECT c.zip_code,
       ROUND(SUM(m.median_household_income * c.tot_ratio) / NULLIF(SUM(c.tot_ratio), 0), 2)
FROM zip_tract_crosswalk c
JOIN median_household_income m ON m.geo_id = c.tract
WHERE m.median_household_income IS NOT NULL
GROUP BY c.zip_code;

-- noah_zip_rentburden (weighted average)
INSERT INTO noah_zip_rentburden (zip_code, rent_burden_rate, severe_burden_rate)
SELECT c.zip_code,
       ROUND(SUM(rb.rent_burden_rate * c.tot_ratio) / NULLIF(SUM(c.tot_ratio), 0), 4),
       ROUND(SUM(rb.severe_burden_rate * c.tot_ratio) / NULLIF(SUM(c.tot_ratio), 0), 4)
FROM zip_tract_crosswalk c
JOIN rent_burden rb ON rb.geo_id = c.tract
WHERE rb.rent_burden_rate IS NOT NULL
GROUP BY c.zip_code;

-- noah_affordability_analysis
INSERT INTO noah_affordability_analysis (zip_code, median_income_usd, rent_burden_rate,
                                         severe_burden_rate, median_rent_usd, rent_to_income_ratio)
SELECT i.zip_code, i.median_income_usd, b.rent_burden_rate, b.severe_burden_rate,
       NULL, NULL  -- StreetEasy 数据不可获取，保留 NULL
FROM noah_zip_income i
LEFT JOIN noah_zip_rentburden b ON b.zip_code = i.zip_code;
```

---

### Step 7 — StreetEasy 数据（⚠️ 当前不可用）

`noah_streeteasy_medianrent_2025_10` 是 Yue 手动从 StreetEasy 收集的私有数据（ZIP × bedroom_type 的 median rent），**无法通过公开 API 获取**。

表保留为空（0 行）。`noah_affordability_analysis.median_rent_usd` 和 `rent_to_income_ratio` 同样为 NULL。

**候选替代方案（需讨论）：**
- Zillow Research ZORI（ZIP级别，公开下载）
- ACS B25031（Census median rent by bedrooms，tract级别）
- 直接联系 Yue/Prof 获取原始数据

---

## 3. 最终数据库状态

| 表名 | 行数 | 数据来源 | 完整性 |
|------|------|----------|--------|
| `housing_projects` | 8,604 | Socrata API hg8x-zxpr | ✅ 完整 |
| `zip_shapes` | 177 | NYC Open Data | ✅ 完整 |
| `rent_burden` | 2,225 | ACS B25070 + TIGER geometry | ✅ 完整 |
| `median_household_income` | 2,201 | ACS B19013 | ✅ 完整 |
| `rent_income_distribution` | 130,312 | ACS B25074 | ✅ 完整 |
| `zip_tract_crosswalk` | 3,071 | Census ZCTA-Tract Rel. file | ✅ 真实面积权重 |
| `noah_zip_income` | 177 | 从 median_household_income 聚合 | ✅ 完整 |
| `noah_zip_rentburden` | 177 | 从 rent_burden 聚合 | ✅ 完整 |
| `noah_affordability_analysis` | 177 | 综合分析 | ✅ 但 median_rent=NULL |
| `noah_streeteasy_medianrent_2025_10` | **0** | StreetEasy（私有）| ⚠️ 不可获取 |
| `noah_zip_medianrent` | **0** | 依赖 StreetEasy | ⚠️ 不可获取 |

**Views：** `housing_summary`，`housing_projects_summary`

---

## 4. 注意事项（Gotchas）

### 4.1 VARCHAR 长度问题
Yue 的 schema 中有几列长度不够容纳真实数据：

| 列 | Yue 原始 | 需要改为 | 原因 |
|----|---------|---------|------|
| `house_number` | VARCHAR(20) | VARCHAR(50) | 部分地址含方向/前缀 |
| `bbl` | VARCHAR(20) | VARCHAR(50) | 某些格式含分隔符 |
| `bin` | VARCHAR(20) | VARCHAR(50) | 同上 |
| `community_board` | VARCHAR(20) | VARCHAR(100) | 包含全称文字 |
| `census_tract` | VARCHAR(20) | VARCHAR(50) | 带前缀格式 |
| `reporting_construction_type` | VARCHAR(50) | VARCHAR(200) | 有较长枚举值 |

### 4.2 SAVEPOINT 逐行保护
不要这样做：
```python
for row in batch:
    try:
        cur.execute("INSERT ...")
    except:
        conn.rollback()  # ❌ 会回滚整个未提交的批次！
```
要这样做：
```python
for row in batch:
    cur.execute("SAVEPOINT sp")
    try:
        cur.execute("INSERT ...")
        cur.execute("RELEASE SAVEPOINT sp")
    except:
        cur.execute("ROLLBACK TO SAVEPOINT sp")
        cur.execute("RELEASE SAVEPOINT sp")
```

### 4.3 Census API 返回格式
- 返回 `text/plain` 不是 `application/json`，用 `json.loads(r.text)` 而不是 `r.json()`
- 第一行是 header，从 `data[1:]` 开始取数据
- `-666666666` 表示数据不可用，必须过滤为 NULL

### 4.4 Census 关系文件编码
```python
r.content.decode('utf-8-sig')  # BOM 编码，不是普通 utf-8
```

### 4.5 GEOID 格式
所有 tract GEOID 必须是 11 位字符串（state 2 + county 3 + tract 6）：
```python
geo_id = f"36{county_code}{tract_code}"  # e.g. "36061000100"
```

### 4.6 rent_burden geometry 列类型
TIGER shapefile 中有些 tract 是 MultiPolygon，有些是 Polygon。列类型必须用通用 `geometry(Geometry, 4326)`，不能用 `geometry(Polygon, 4326)`。

### 4.7 ZIP 99999 占位符
某些来源会产生 `zip_code = '99999'`，这不是真实 ZIP，必须过滤删除。

---

## 5. Assumptions、Choices 和 Trade-offs

### Assumption 1：project_id 不唯一
- **Yue 的 schema：** `project_id VARCHAR(50) UNIQUE NOT NULL`
- **实际情况：** 同一 project_id 对应多栋楼（如 project 75173 = 114 栋楼）
- **我们的选择：** `id SERIAL PRIMARY KEY`，project_id 只建普通 index，不加 UNIQUE 约束
- **Rationale：** Socrata 数据集是建筑级别（building-level）记录，一个 housing project 可以跨多栋楼。强制 UNIQUE 会导致丢失 3,352 条真实记录（8,604 → 5,252）
- **Trade-off：** 偏离 Yue 的 schema 定义，但保留了更完整的真实数据

### Assumption 2：rent_burden_rate 存为小数（0-1 格式）
- **我们的格式：** 0.42（代表 42%）
- **Yue 的 build_zip_level_tables.py：** 代码里有 `if max < 1: multiply by 100`，暗示她存为百分比（42.xx）
- **我们的选择：** 保持 ACS 原始计算结果的小数格式，更符合统计学惯例
- **Trade-off：** 如果直接运行 Yue 的脚本，她会把我们的 0.42 变成 42.xx；但两者语义相同

### Assumption 3：StreetEasy 数据用 NULL 代替
- **实际情况：** `noah_streeteasy_medianrent_2025_10` 是 Yue 手动收集的私有数据
- **我们的选择：** 表结构保留，行数为 0，不用 ACS B25031 或其他数据填充
- **Rationale：** 使用 ACS 数据替代会扭曲语义（ACS 是 tract 级别，StreetEasy 是真实市场租金）
- **Trade-off：** `noah_affordability_analysis.rent_to_income_ratio` 全部为 NULL，降低了分析价值

### Assumption 4：Census 2022 ACS 5-Year Estimates
- 使用 2022 年度的 ACS 数据（Yue 的 StreetEasy 数据是 2025-10）
- 两者年份不完全匹配，但这是能获取的最接近的公开数据
- 如果 Yue 的代码也用 Census 数据，她用的也应该是 2022 或 2023

### Assumption 5：ZCTA-to-Tract 权重方法
- **原来（错误）：** HUD API 返回 401，用 Census 关系文件但 tot_ratio 全设为 1.0
- **修正后：** `tot_ratio = AREALAND_PART / AREALAND_TRACT_20`（面积比例权重）
- **Rationale：** 一个 Tract 可能被多个 ZIP 覆盖，面积权重能正确分配 Tract 数据到 ZIP
- **Known limitation：** 面积权重假设数据在 Tract 内均匀分布，实际并非如此，但这是业界标准做法

### Choice：crosswalk 保留 3,071 行（仅 NYC ZIP）
- 从 171,480 行全国数据过滤到仅包含我们 zip_shapes 中 177 个 NYC ZIP 对应的条目
- 确保聚合时不会混入非 NYC 地区的 tract 数据

---

## 6. 快速验证命令

```sql
-- 验证行数
SELECT 'housing_projects' as t, COUNT(*) FROM housing_projects
UNION ALL SELECT 'zip_shapes', COUNT(*) FROM zip_shapes
UNION ALL SELECT 'rent_burden', COUNT(*) FROM rent_burden
UNION ALL SELECT 'median_household_income', COUNT(*) FROM median_household_income;

-- 验证 geometry 完整性
SELECT COUNT(*) as has_geom FROM housing_projects WHERE geom IS NOT NULL;  -- 6,886
SELECT COUNT(*) as has_geom FROM rent_burden WHERE geometry IS NOT NULL;   -- 2,225

-- 验证 crosswalk 权重
SELECT AVG(tot_ratio), MIN(tot_ratio), MAX(tot_ratio) FROM zip_tract_crosswalk;
-- 应该是 avg≈0.75, min>0, max=1.0

-- 验证 income 范围合理
SELECT MIN(median_income_usd), MAX(median_income_usd) FROM noah_zip_income;
-- 应该在 $40,000 ~ $250,000 之间

-- 确认无假数据
SELECT COUNT(*) FROM noah_streeteasy_medianrent_2025_10;  -- 0
SELECT COUNT(*) FROM noah_zip_medianrent;                   -- 0
SELECT COUNT(*) FROM zip_shapes WHERE zip_code = '99999';  -- 0
```

---

## 7. 已知缺口（Known Gaps）

| 数据项 | 状态 | 说明 |
|--------|------|------|
| StreetEasy 租金数据 | ❌ 缺失 | 私有数据，需直接联系 Yue 获取 |
| 1,718 条无坐标的 housing_projects | ⚠️ 正常缺失 | Socrata 源数据本身没有这些行的坐标 |
| rent_to_income_ratio | ⚠️ NULL | 依赖 StreetEasy 数据，目前无法计算 |
| buildings 表 | ❌ 未实现 | Yue 的 NOAH 是否有独立的 buildings 表？需确认 |

---

*文档生成时间：2026-02-20*
*基于 Claude 与 Zhen Yang 的多轮对话整理*
