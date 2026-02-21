# Questions for Prof / Yue Yu

## 中文摘要

在本地完整还原 Yue 的 NOAH 数据库过程中，我们发现了若干需要确认的问题，主要分为四类：

1. **数据可获取性**：StreetEasy 私有数据无法获取，目前 `noah_streeteasy_medianrent_2025_10` 为空表；租金相关分析（`rent_to_income_ratio`）全部为 NULL。需要 Yue 提供原始数据文件，或给出可接受的替代方案。

2. **Schema 设计歧义**：`project_id` 在 Yue 的两个 SQL 文件中定义冲突（一个用 `UNIQUE`，一个用 `PRIMARY KEY`），但 Socrata 真实数据显示同一 project_id 对应多栋楼（8,604 条记录，只有 5,252 个唯一 ID）。我们选择了 serial `id` 作为主键，但需要确认这是否符合 Yue 的原始设计意图。

3. **数据时效性**：Yue 的 StreetEasy 数据是 2025 年 10 月，我们的 Census ACS 数据是 2022 年，年份不对齐。请问 Yue 用的 Census 数据是哪一年？

4. **项目范围与 Capstone 评分**：StreetEasy 数据缺失会影响对 NOAH 图谱"租金可负担性分析"的演示效果。教授是否接受"核心功能展示 + 数据缺口说明"的方式？还是必须要有完整的租金数据？

---

## Q1 — StreetEasy Data: Can We Get the Raw File?

**Context:**
`noah_streeteasy_medianrent_2025_10` is the core rent data table in NOAH. It contains median rent by ZIP code and bedroom type, collected manually by Yue from StreetEasy (October 2025). This table is referenced in `build_zip_level_tables.py` and feeds directly into `noah_affordability_analysis.median_rent_usd` and `rent_to_income_ratio`.

**Current status:**
The table exists in our local database but has 0 rows. Without it:
- `noah_affordability_analysis.median_rent_usd` = NULL for all 177 ZIPs
- `noah_affordability_analysis.rent_to_income_ratio` = NULL for all 177 ZIPs
- The affordability analysis is effectively incomplete

**Questions:**
1. Yue, can you share the raw StreetEasy CSV/Excel file you used to populate `noah_streeteasy_medianrent_2025_10`? Even a snapshot would be sufficient.
2. If the original file isn't available, what is the expected schema of this table? (Which bedroom types? What ZIP granularity? What time range?)
3. Would a publicly available substitute be acceptable for the capstone? Candidates:
   - **Zillow ZORI** (ZIP-level, free download): `https://www.zillow.com/research/data/`
   - **ACS B25031** (Census median rent by bedrooms, tract-level, 2022): available via Census API but is 2022 data, not 2025 market rates
   - **NYC DHCR data**: available through NYC Open Data but covers only rent-stabilized units

---

## Q2 — `project_id` Uniqueness: Schema Conflict

**Context:**
Yue's two SQL files define the primary key of `housing_projects` differently:

| File | Definition |
|------|-----------|
| `database_schema.sql` | `id SERIAL PRIMARY KEY` + `project_id VARCHAR(50) UNIQUE NOT NULL` |
| `backend/migrations/001_create_housing_projects_table.sql` | `project_id VARCHAR(50) PRIMARY KEY` (no separate `id`) |

**The real data problem:**
When loading all 8,604 rows from Socrata (`hg8x-zxpr`), we find:
- Total rows: **8,604**
- Unique `project_id` values: **5,252**
- Rows sharing a `project_id`: **3,352** (e.g., project_id `75173` = 114 buildings, `53017` = 83 buildings)

This means Socrata's "Housing Production by Building" dataset uses project_id at the building level — **one housing project can have many buildings**.

**Our current decision:**
We use `id SERIAL PRIMARY KEY` and do NOT enforce UNIQUE on `project_id`. This preserves all 8,604 building-level records.

**Questions:**
1. Which schema definition was the final intended one? (`database_schema.sql` or the migration file?)
2. Was NOAH's production database actually storing only 5,252 de-duplicated records, or all 8,604?
3. In Yue's Streamlit app, were queries written against `project_id` (one-per-project) or `id` (one-per-building)?
4. If UNIQUE is required, should we de-duplicate by keeping the first occurrence, the most recent, or aggregating unit counts?

---

## Q3 — Census Data Year Alignment

**Context:**
The NOAH system combines two data sources with different time periods:
- **StreetEasy rent data:** October 2025 (table name `noah_streeteasy_medianrent_2025_10`)
- **Census ACS data (our load):** 2022 5-Year Estimates (most recent fully released as of early 2025)

**Potential misalignment:**
- ACS 2022 median income vs. 2025 market rent — a 3-year gap during which NYC rents increased significantly (post-COVID rent surge)
- The computed `rent_to_income_ratio` would be inflated by using 2022 incomes against 2025 rents

**Questions:**
1. Yue, which ACS year did you use? 2022? 2023?
2. Was the mismatch between ACS and StreetEasy years intentional (using latest available for each), or an oversight?
3. For the capstone, should we prioritize temporal consistency (use same year for both) or recency (latest available for each)?
4. Is ACS 2023 data available and preferable? (2023 5-year estimates were released in December 2024)

---

## Q4 — `zip_tract_crosswalk`: HUD vs. Census Weights

**Context:**
The crosswalk table maps ZIP codes to census tracts with a `tot_ratio` weight for area-weighted aggregation (ZIP_value = SUM(tract_value × tot_ratio)).

**What we found:**
- Yue's `build_zip_level_tables.py` uses `zip_tract_crosswalk` but doesn't document where this table's data comes from
- The HUD ZIP-to-Tract crosswalk API (`https://www.huduser.gov/hudapi/public/usps`) returned HTTP 401 (unauthorized)
- We used the **Census 2020 ZCTA-to-Tract relationship file** with `tot_ratio = AREALAND_PART / AREALAND_TRACT_20`

**Our current crosswalk:**
- 3,071 rows covering 177 NYC ZIPs
- Average tot_ratio = 0.7464 (not 1.0 — many tracts are only partially in a ZIP)
- Source: `tab20_zcta520_tract20_natl.txt` from Census Bureau

**Questions:**
1. What was the original source of `zip_tract_crosswalk` in NOAH's production database? Was it from HUD, Census, or another provider?
2. Were HUD crosswalk weights used? If so, can you share the HUD API token or the pre-downloaded crosswalk file?
3. Is area-based weighting (`AREALAND_PART / AREALAND_TRACT_20`) the correct approach, or did NOAH use population-weighted or housing-unit-weighted aggregation?

---

## Q5 — `rent_burden` Geometry: Was It Ever Populated?

**Context:**
`rent_burden` is a census-tract level table with a `geometry` column of type `GEOMETRY(POLYGON, 4326)`. When we loaded ACS B25070 data via the Census API, all 2,225 rows had NULL geometry — the Census API does not return geometries, only tabular data.

**We fixed this** by downloading the Census TIGER `cb_2022_36_tract_500k.zip` shapefile and spatially joining it. All 2,225 rows now have geometry.

**Questions:**
1. Was the `geometry` column in NOAH's production `rent_burden` table ever populated? How?
2. If it was populated, was it from TIGER shapefiles, or from another source (e.g., NYC DCP, Bytes of the Big Apple)?
3. The TIGER shapefile we used (`cb_2022_36_tract_500k`) uses cartographic generalization (simplified polygons). Was this the level of precision used in NOAH's Streamlit map visualization?

---

## Q6 — `zip_shapes` Table Origin

**Context:**
Our `zip_shapes` table (177 NYC ZIPs) was loaded from NYC Open Data. Yue's repo contains `scripts/create_zip_shapes_nyc.sql` which references a table `zip_shapes_geojson` that doesn't exist in the public repo.

**Questions:**
1. Where did the original `zip_shapes` / `zip_shapes_geojson` data come from in NOAH? NYC DOF? NYC DOITT? ESRI? Census ZCTA shapefile?
2. Was `zip_shapes_geojson` a separate raw import table, or is it the same as `zip_shapes` with a different schema?
3. Are ZCTAs (Census ZIP Code Tabulation Areas) used, or actual USPS ZIP boundaries? They differ slightly.

---

## Q7 — Capstone Scope: Is Incomplete StreetEasy Data Acceptable?

**Context:**
Our converter tool is designed to demonstrate automated PostgreSQL-to-Neo4j migration. The NOAH database is the source. However, the most analytically interesting part of NOAH — rent affordability analysis — depends on StreetEasy data we cannot obtain.

**Current state of our demo:**
- ✅ Full housing_projects data (8,604 buildings with geometry)
- ✅ Full ACS demographic/burden data (income, rent burden by tract)
- ✅ Spatial relationships (ZIP neighborhoods, building clustering)
- ✅ Text2Cypher natural language query interface
- ⚠️ `rent_to_income_ratio` = NULL (no StreetEasy data)

**Questions:**
1. Prof: Is demonstrating the **conversion pipeline** (schema analysis → graph mapping → Cypher generation → migration) sufficient for full marks, even if the affordability analysis has NULL rent values?
2. Prof: Should we use a publicly available rent substitute (Zillow ZORI) to make the demo more complete, or is that considered out of scope?
3. Prof: Is the primary evaluation criterion the **tooling/automation quality** or the **analytical quality of the resulting knowledge graph**?

---

## Q8 — Buildings Table: Is There a Separate `buildings` Table?

**Context:**
Our current `mapping_rules.yaml` was designed to include a `Building` node in the Neo4j graph, sourced from a `buildings` table. However, Yue's schema files only show `housing_projects` — there is no separate `buildings` table in the public repo.

The `housing_projects` table contains building-level attributes (BBL, BIN, address) as well as project-level attributes (income unit counts, affordability status).

**Questions:**
1. Was there a separate `buildings` table in NOAH's production database that is not in the public GitHub repo?
2. Should `housing_projects` be mapped as a single `HousingProject` node per row (building-level), or should we denormalize/aggregate to project-level?
3. For the Neo4j graph, what would be the most useful node granularity: per-building or per-project?

---

*Document prepared: 2026-02-20*
*Author: Zhen Yang (based on local NOAH database reconstruction)*
