# Mapping Engine 实现计划

**日期:** 2026-02-20
**目标:** 实现完全自动化的 PostgreSQL → Neo4j 转换引擎
**核心要求:** Zero data loss，包括 PostGIS 所有数据（WKT, geometry, etc.）

---

## 📋 需求分析

### 1. Capstone 项目核心要求

基于规范文档分析：
- ✅ **Automated schema introspection** - 自动分析 schema
- ✅ **Intelligent mapping** - 智能映射 Tables→Nodes, FKs→Relationships
- ✅ **Data migration with validation** - 数据迁移和验证
- ✅ **Zero data loss** - 零数据丢失
- ✅ **Handle spatial data** - 处理 PostGIS 空间数据

### 2. NOAH 数据库结构分析

**核心表（从 Yue Yu 报告）：**
- `zipcodes` - 177 rows, PostGIS geometry (MULTIPOLYGON)
- `buildings` - ~100,000 rows, PostGIS point
- `housing_projects` - 1,000-5,000 rows, PostGIS point
- `demographics` - ZIP-level 人口统计
- `income_metrics` - ZIP-level 收入指标
- `rent_metrics` - ZIP-level 租金指标
- `housing_stock` - ZIP-level 住房存量

**关系：**
- FK: building.zipcode_id → zipcodes.zipcode_id
- FK: housing_project.zipcode_id → zipcodes.zipcode_id
- FK: demographics.zipcode_id → zipcodes.zipcode_id
- FK: income_metrics.zipcode_id → zipcodes.zipcode_id
- Spatial: ST_Touches(zipcode.geometry, zipcode.geometry) → NEIGHBORS

**PostGIS 数据类型：**
- `geometry(MULTIPOLYGON, 4326)` - ZIP 边界
- `geometry(POINT, 4326)` - 建筑/项目位置
- Computed: centroids, areas, distances, adjacency

### 3. 完整数据保留要求

**必须保留的 PostGIS 数据：**
1. **原始 Geometry (WKT)**
   - 用途：外部 GIS 工具（QGIS, ArcGIS）
   - 格式：`ST_AsText(geometry)` → WKT string
   - 存储：Neo4j node property `geometryWKT`

2. **Centroids (Lat/Lon)**
   - 用途：Neo4j Point type, 地图显示
   - 计算：`ST_Centroid(geometry)`
   - 存储：Neo4j Point + 冗余 lat/lon properties

3. **Computed Metrics**
   - Area (km²): `ST_Area(geometry::geography) / 1000000`
   - Distance (km): `ST_Distance(a.geom, b.geom) / 1000`
   - Adjacency: `ST_Touches(a.geom, b.geom)`

4. **Spatial Relationships**
   - NEIGHBORS: 从 ST_Touches 计算
   - WITHIN_DISTANCE: 从 ST_DWithin 计算

---

## 🏗️ Mapping Engine 架构设计

### 核心组件

```
┌─────────────────────────────────────────────────────────┐
│                   MAPPING ENGINE                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐      ┌─────────────────┐            │
│  │  Schema      │ ───> │  Mapping Rules  │            │
│  │  Analyzer    │      │  Configurator   │            │
│  └──────────────┘      └─────────────────┘            │
│         │                       │                      │
│         ▼                       ▼                      │
│  ┌────────────────────────────────────┐               │
│  │      Graph Schema Builder          │               │
│  │  • Table → Node Type               │               │
│  │  • FK → Relationship Type          │               │
│  │  • Column → Property               │               │
│  │  • PostGIS → Spatial Handler       │               │
│  └────────────────────────────────────┘               │
│         │                                               │
│         ▼                                               │
│  ┌────────────────────────────────────┐               │
│  │    Cypher DDL Generator            │               │
│  │  • CREATE CONSTRAINT               │               │
│  │  • CREATE INDEX                    │               │
│  └────────────────────────────────────┘               │
│                                                         │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                   DATA MIGRATOR                         │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Extractor   │→ │ Transformer  │→ │   Loader     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         │                  │                  │         │
│    PostgreSQL         Type Conv         Neo4j          │
│    + PostGIS          Spatial           Batch          │
│                       Handling          Import          │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                    VALIDATOR                            │
├─────────────────────────────────────────────────────────┤
│  • Row count validation                                 │
│  • Relationship integrity                               │
│  • Data quality checks                                  │
│  • Spatial data verification                            │
└─────────────────────────────────────────────────────────┘
```

---

## 📐 数据模型设计

### 1. GraphSchema Model

```python
@dataclass
class Property:
    name: str
    type: str  # String, Integer, Float, Point, etc.
    nullable: bool
    source_column: str
    source_type: str  # PostgreSQL type

@dataclass
class NodeType:
    label: str
    primary_property: str
    properties: List[Property]
    source_table: str

    # Spatial data
    has_geometry: bool = False
    geometry_column: Optional[str] = None
    geometry_type: Optional[str] = None  # POINT, MULTIPOLYGON

@dataclass
class RelationshipType:
    type: str
    from_label: str
    to_label: str
    properties: List[Property]

    # Source
    source_type: str  # FK or COMPUTED
    source_fk: Optional[str] = None  # 如果是 FK
    source_query: Optional[str] = None  # 如果是 COMPUTED (spatial)

@dataclass
class GraphSchema:
    nodes: List[NodeType]
    relationships: List[RelationshipType]
    metadata: Dict[str, Any]
```

### 2. MappingRules Configuration

```yaml
# config/mapping_rules.yaml

# 全局规则
global:
  # 默认 table → node label 转换
  table_to_label_case: PascalCase  # zipcodes → Zipcode

  # FK 命名规则
  fk_to_relationship: true
  relationship_name_pattern: "{source_table}_TO_{target_table}"

  # 属性命名
  property_case: camelCase  # median_rent → medianRent

# 表特定映射
tables:
  zipcodes:
    node_label: Zipcode
    primary_property: zipcode
    merge_related:
      - demographics
      - income_metrics
      - rent_metrics
      - housing_stock
    spatial:
      geometry_column: geometry
      preserve_wkt: true
      compute_centroid: true
      compute_area: true

  buildings:
    node_label: Building
    primary_property: bbl
    spatial:
      geometry_column: geometry
      point_to_neo4j: true

  housing_projects:
    node_label: HousingProject
    primary_property: project_id
    spatial:
      geometry_column: geometry
      point_to_neo4j: true

# 空间关系计算
spatial_relationships:
  - type: NEIGHBORS
    from: Zipcode
    to: Zipcode
    computation:
      method: ST_Touches
      bidirectional: true
      properties:
        - name: distanceKm
          compute: ST_Distance(a.geom, b.geom) / 1000.0
        - name: isAdjacent
          compute: ST_Touches(a.geom, b.geom)
    filters:
      - ST_DWithin(a.geometry, b.geometry, 10000)

# 类型映射
type_mappings:
  # PostgreSQL → Neo4j
  integer: Integer
  bigint: Integer
  numeric: Float
  double precision: Float
  varchar: String
  text: String
  date: Date
  timestamp: DateTime
  boolean: Boolean
  geometry: String  # WKT format
```

---

## 🔄 PostGIS → Neo4j 完整转换策略

### Phase 1: PostgreSQL 预计算 (自动生成 SQL)

**由 SpatialDataHandler 自动生成：**

```sql
-- 1. Extract centroids
CREATE TABLE _neo4j_zipcodes_spatial AS
SELECT
    zipcode_id,
    zip_code,
    -- Centroid
    ST_Y(ST_Centroid(geometry)) AS center_lat,
    ST_X(ST_Centroid(geometry)) AS center_lon,
    -- WKT (完整保留)
    ST_AsText(geometry) AS geometry_wkt,
    -- GeoJSON (可选)
    ST_AsGeoJSON(geometry) AS geometry_geojson,
    -- Metrics
    ST_Area(geometry::geography) / 1000000.0 AS area_km2,
    ST_Perimeter(geometry::geography) / 1000.0 AS perimeter_km,
    -- Bounding box
    ST_XMin(geometry) AS bbox_xmin,
    ST_YMin(geometry) AS bbox_ymin,
    ST_XMax(geometry) AS bbox_xmax,
    ST_YMax(geometry) AS bbox_ymax
FROM zipcodes;

-- 2. Compute spatial relationships
CREATE TABLE _neo4j_zipcode_neighbors AS
SELECT
    a.zip_code AS from_zip,
    b.zip_code AS to_zip,
    ST_Distance(
        ST_Centroid(a.geometry)::geography,
        ST_Centroid(b.geometry)::geography
    ) / 1000.0 AS distance_km,
    ST_Touches(a.geometry, b.geometry) AS is_adjacent,
    -- Shared border length
    ST_Length(
        ST_Intersection(a.geometry, b.geometry)::geography
    ) / 1000.0 AS shared_border_km
FROM zipcodes a
CROSS JOIN zipcodes b
WHERE a.zip_code < b.zip_code
  AND ST_DWithin(a.geometry, b.geometry, 10000);

-- 3. Extract building points
CREATE TABLE _neo4j_buildings_spatial AS
SELECT
    building_id,
    bbl,
    ST_Y(geometry) AS latitude,
    ST_X(geometry) AS longitude,
    ST_AsText(geometry) AS geometry_wkt
FROM buildings
WHERE geometry IS NOT NULL;
```

### Phase 2: Neo4j 导入 (完整保留所有数据)

```python
# Zipcode nodes - 包含所有 PostGIS 数据
CREATE (z:Zipcode {
    zipcode: row.zip_code,
    borough: row.borough,

    // Neo4j Point (for spatial queries)
    location: point({
        latitude: row.center_lat,
        longitude: row.center_lon,
        crs: 'WGS-84'
    }),

    // 冗余坐标 (for display/export)
    centerLat: row.center_lat,
    centerLon: row.center_lon,

    // 完整保留 WKT (zero loss!)
    geometryWKT: row.geometry_wkt,
    geometryGeoJSON: row.geometry_geojson,

    // Computed metrics
    areaKm2: row.area_km2,
    perimeterKm: row.perimeter_km,

    // Bounding box
    bboxXMin: row.bbox_xmin,
    bboxYMin: row.bbox_ymin,
    bboxXMax: row.bbox_xmax,
    bboxYMax: row.bbox_ymax,

    // Other properties
    medianRent1br: row.median_rent_1br,
    medianIncome: row.median_household_income,
    // ... etc
})
```

**数据完整性保证：**
- ✅ 原始 WKT geometry 完整保存
- ✅ GeoJSON 格式保存（可选）
- ✅ Neo4j Point 用于查询
- ✅ 所有计算指标保存
- ✅ Bounding box 保存
- ✅ 可以从 Neo4j 导出回 GIS 工具

---

## 📅 实施计划 (分阶段)

### Phase 1: 数据模型和配置 (30分钟)

**文件创建：**
1. `src/noah_converter/mapping_engine/models.py`
   - GraphSchema, NodeType, RelationshipType, Property

2. `src/noah_converter/mapping_engine/config.py`
   - MappingConfig, SpatialConfig

3. `config/mapping_rules.yaml`
   - 配置文件

**实现内容：**
- 完整的数据模型类
- 配置加载器
- 验证器

### Phase 2: Mapping Rules Engine (30分钟)

**文件创建：**
1. `src/noah_converter/mapping_engine/rules.py`
   - MappingRules class
   - table_to_node_label()
   - column_to_property()
   - fk_to_relationship()

2. `src/noah_converter/mapping_engine/spatial_handler.py`
   - SpatialDataHandler class
   - detect_geometry_columns()
   - generate_spatial_precomputation_sql()
   - generate_spatial_relationships()

**实现内容：**
- 自动映射规则
- PostGIS 自动检测和处理
- SQL 生成器

### Phase 3: MappingEngine 主类 (30分钟)

**文件创建：**
1. `src/noah_converter/mapping_engine/mapper.py`
   - MappingEngine class
   - analyze_and_map()
   - generate_graph_schema()

2. `src/noah_converter/mapping_engine/cypher_generator.py`
   - CypherDDLGenerator class
   - generate_constraints()
   - generate_indexes()

**实现内容：**
- 主控制逻辑
- Graph schema 生成
- Cypher DDL 生成

### Phase 4: 通用 Data Migrator (30分钟)

**文件创建：**
1. `src/noah_converter/data_migrator/extractor.py`
   - DataExtractor class (通用)

2. `src/noah_converter/data_migrator/transformer.py`
   - DataTransformer class (基于 GraphSchema)

3. `src/noah_converter/data_migrator/loader.py`
   - Neo4jLoader class (批量导入)

4. `src/noah_converter/data_migrator/migrator.py`
   - DataMigrator class (orchestrator)

**实现内容：**
- 通用的 ETL 管道
- 基于 GraphSchema 的转换
- 不硬编码任何表名

### Phase 5: Validator (15分钟)

**文件创建：**
1. `src/noah_converter/data_migrator/validator.py`
   - MigrationValidator class
   - validate_counts()
   - validate_relationships()
   - validate_spatial_data()

### Phase 6: CLI 集成 (15分钟)

**更新文件：**
1. `main.py`
   - 新增 `map` command
   - 新增 `migrate-auto` command
   - 新增 `validate` command

**命令示例：**
```bash
# 生成 mapping
python main.py map --config config/mapping_rules.yaml --export outputs/graph_schema.json

# 自动迁移
python main.py migrate-auto --schema outputs/graph_schema.json

# 验证
python main.py validate --report outputs/validation_report.html
```

---

## ✅ 验证清单

### 功能验证

- [ ] 自动分析 PostgreSQL schema
- [ ] 生成正确的 GraphSchema
- [ ] 生成正确的 Cypher DDL
- [ ] 自动检测 PostGIS columns
- [ ] 生成空间预计算 SQL
- [ ] 迁移所有 node types
- [ ] 迁移所有 relationships
- [ ] 保留所有 PostGIS 数据（WKT, GeoJSON）
- [ ] Row count 匹配
- [ ] Relationship integrity 验证

### PostGIS 数据完整性

- [ ] WKT geometry 完整保存
- [ ] Centroids 正确计算
- [ ] Area, perimeter 正确
- [ ] NEIGHBORS relationships 正确
- [ ] Neo4j Point type 正确
- [ ] 可以从 Neo4j 导出回 GIS 工具

### 通用性测试

- [ ] 可以处理不同的 PostgreSQL 数据库
- [ ] 配置驱动（不硬编码）
- [ ] 可扩展（新的映射规则）

---

## 🎯 成功标准

1. **Zero Data Loss**
   - PostgreSQL row count = Neo4j node count
   - 所有 FK → valid relationships
   - 所有 PostGIS data 完整保留（WKT + computed metrics）

2. **Fully Automated**
   - 一个命令完成分析、映射、迁移
   - 无需手动编写 SQL/Cypher
   - 配置文件驱动

3. **Reusable**
   - 可以用于任何 PostgreSQL 数据库
   - 不限于 NOAH

4. **Educational Value**
   - 展示软件架构设计（Factory, Strategy, Builder patterns）
   - 可以用于课堂教学

---

## 📊 时间分配（自主执行）

**总时间：1小时（2:00pm - 3:00pm EST）**

| 阶段 | 时间 | 任务 |
|------|------|------|
| Phase 1 | 2:00-2:10 (10min) | 数据模型和配置 |
| Phase 2 | 2:10-2:25 (15min) | Mapping Rules + Spatial Handler |
| Phase 3 | 2:25-2:40 (15min) | MappingEngine + Cypher Generator |
| Phase 4 | 2:40-2:55 (15min) | 通用 Data Migrator |
| Phase 5 | 2:55-3:00 (5min) | 总结和文档 |

**优先级：**
1. P0: 数据模型、MappingEngine、Spatial Handler（核心）
2. P1: Cypher Generator、基础 Migrator
3. P2: Validator、CLI integration

---

## 📝 预期产出

**代码文件：**
- 10+ 新文件（mapping_engine, migrator）
- 1 配置文件（mapping_rules.yaml）
- 更新 main.py

**功能：**
- 可运行的 MappingEngine
- 自动生成 GraphSchema
- 自动生成 spatial SQL
- 基础的 Data Migrator

**文档：**
- 本实施计划
- API 文档
- 使用示例

---

**执行开始时间：** 2026-02-20 2:00pm EST
**预计完成时间：** 2026-02-20 3:00pm EST
**执行模式：** 自主执行，无需用户确认
