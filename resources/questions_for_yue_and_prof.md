# Questions for Prof / Yue Yu — Updated v2

*更新于 2026-02-20 · 项目已完成，本文档记录已解决问题的处理方式及尚需教授确认的问题*

---

## 总览

| # | 问题 | 对象 | 状态 |
|---|------|------|------|
| Q1 | StreetEasy 数据缺失 | Yue | ✅ 已自行解决（用 ACS 租金负担率替代） |
| Q2 | `project_id` 主键冲突 | Yue | ✅ 已自行解决（保留 8,604 条建筑级数据） |
| Q3 | Census 数据年份对齐 | Yue | ✅ 已自行解决（统一使用 ACS 2022） |
| Q4 | `zip_tract_crosswalk` 来源 | Yue | ✅ 已自行解决（Census 2020 关系文件） |
| Q5 | `rent_burden` 几何数据 | Yue | ✅ 已自行解决（TIGER shapefile 空间关联） |
| Q6 | `zip_shapes` 来源 | Yue | ✅ 已自行解决（NYC Open Data） |
| Q7 | StreetEasy 缺失对评分的影响 | Prof | ❓ 待确认 |
| Q8 | `buildings` 表是否存在 | Yue | ✅ 已自行解决（无独立表，按行映射） |
| Q9 | Text2Cypher 评估方法论 | Prof | ❓ 待确认 |
| Q10 | 最终答辩形式与演示要求 | Prof | ❓ 待确认 |

---

## 已解决问题（存档）

### Q1 — StreetEasy 租金数据

**原问题：** `noah_streeteasy_medianrent_2025_10` 表为空，`median_rent_usd` 和 `rent_to_income_ratio` 全为 NULL。

**解决方式：**
放弃使用私有 StreetEasy 数据。改用 ACS B25070（Census 人口普查）提供的 `rent_burden_rate` 和 `severe_burden_rate` 作为核心可负担性指标。这两个字段已全部填充（177 个 ZIP 码均有数据）。

`median_rent_usd` 和 `rent_to_income_ratio` 字段在 `AffordabilityAnalysis` 节点中仍为 NULL，但在演示中未影响核心功能展示。

**遗留问题（见 Q7）：** 教授是否认为这是可接受的数据缺口？

---

### Q2 — `project_id` 主键冲突

**原问题：** Yue 的两个 SQL 文件对主键定义不一致；Socrata 真实数据显示同一 project_id 对应多栋楼。

**解决方式：**
- 使用 `id SERIAL PRIMARY KEY`，不对 `project_id` 施加 UNIQUE 约束
- 保留全部 8,604 条建筑级（per-building）记录
- Neo4j 中每行映射为一个独立的 `HousingProject` 节点，使用 `db_id`（即 serial `id`）作为合并键

**数据说明：**
- 总记录数：8,604
- 唯一 project_id：5,252
- 同一 project_id 对应多栋楼的情况：3,352 条

---

### Q3 — Census 数据年份

**原问题：** StreetEasy 数据为 2025 年 10 月，Census ACS 数据年份不确定。

**解决方式：**
由于 StreetEasy 数据未使用，年份对齐问题自动消除。统一采用 **ACS 2022 五年估计数**（截至 2025 年初发布的最新完整数据集）。

---

### Q4 — `zip_tract_crosswalk` 来源

**原问题：** HUD API 返回 401，无法获取 HUD 版本的跨表数据。

**解决方式：**
使用 Census Bureau 2020 ZCTA-to-Tract 关系文件（`tab20_zcta520_tract20_natl.txt`），以 `tot_ratio = AREALAND_PART / AREALAND_TRACT_20` 进行面积加权。

**当前 crosswalk 规模：** 3,071 行，覆盖纽约市 177 个 ZIP 码。

---

### Q5 — `rent_burden` 几何数据

**原问题：** Census API 不返回几何数据，所有行 `geometry` 为 NULL。

**解决方式：**
下载 Census TIGER `cb_2022_36_tract_500k.zip` shapefile，与 `rent_burden` 表按 GEOID 做空间关联，完整填充了 2,225 行的几何字段（POLYGON, EPSG:4326）。

---

### Q6 — `zip_shapes` 来源

**原问题：** Yue 的 `create_zip_shapes_nyc.sql` 引用了不存在于 public repo 的 `zip_shapes_geojson` 表。

**解决方式：**
从 NYC Open Data（`nyc_community_districts` + ZCTA shapefile）获取 177 个纽约市 ZIP 边界多边形，导入 `zip_shapes` 表，SRID = 4326。

---

### Q8 — `buildings` 独立表

**原问题：** `mapping_rules.yaml` 原来设计了一个独立的 `Building` 节点，但 Yue 的 repo 中没有 `buildings` 表。

**解决方式：**
确认 `housing_projects` 即为建筑级表（每行 = 一栋楼）。不再创建独立 `Building` 节点，改为直接将 `housing_projects` 的每行映射为 `HousingProject` 节点。

---

## 待确认问题

### Q7 — 教授：StreetEasy 数据缺失对评分的影响

**背景：**
项目演示中，`AffordabilityAnalysis` 节点的以下字段值为 NULL：
- `median_rent_usd`
- `rent_to_income_ratio`

有数据的字段：
- ✅ `rent_burden_rate`（租金负担率）
- ✅ `severe_burden_rate`（严重负担率）
- ✅ `median_income_usd`（中位收入）

Text2Cypher 的 20 题基准测试中，所有涉及可负担性分析的题目均基于 `rent_burden_rate` 和 `severe_burden_rate`，不依赖缺失字段，准确率达 95%（19/20）。

**请教授确认：**
1. 核心转换工具链（Schema 分析 → 图映射 → Cypher 生成 → 迁移）是否是首要评估标准，而非数据集的完整性？
2. `median_rent_usd` 字段为 NULL 是否需要在答辩时主动说明并解释来源限制？
3. 是否接受以 Zillow ZORI 数据作为 StreetEasy 的公开替代数据填充？（改动约 1 天工作量）

---

### Q9 — 教授：Text2Cypher 评估方法论

**背景：**
我们设计了一套 20 题基准测试（Easy 6 题 / Medium 7 题 / Hard 7 题），每题按 4 个标准打分（语法正确、有结果、计数匹配、首行匹配），得分 95%（19/20）。

唯一失败题：Q19（Hard）—— LLM 省略了 LIMIT 子句，返回 100 行而非预期的 20 行。

**请教授确认：**
1. 这套 4-标准评分方法是否符合您对 Text2Cypher 评估的预期？
2. "Hard" 难度的定义（3 跳图遍历 + 空间邻居查询）是否合理？
3. 95% 这个数字是否需要与 baseline（如 direct GPT-4 without schema context）对比才有说服力？

---

### Q10 — 教授：最终答辩形式与演示要求

**请教授确认：**
1. 答辩是 demo-based 还是 slides-based，还是两者结合？
2. 是否需要现场演示 Streamlit UI？如需要，演示时 Neo4j 和 PostgreSQL 需要 live connection，请问是在本地运行还是需要部署到可公开访问的服务器？
3. 是否需要提交 GitHub repo 链接或代码压缩包？
4. `docs/CAPSTONE_REPORT.md`（~4,000 字）是否符合书面报告要求的格式？

---

*文档版本：v2.0 · 2026-02-20 · 作者：Zhen Yang*
