## 项目状态：✅ 已完成（2026-02-20）

这是 Zhen Yang 的 NYU SPS MASY Capstone 毕设项目，已全部完成并提交。

---

## 项目是什么

把纽约市保障性住房 PostgreSQL 数据库（NOAH）自动转换成 Neo4j 知识图谱，并提供一个自然语言查询的 Web 界面。

**源数据库（PostgreSQL）：** Yue Yu 的 NOAH 实现，8,604 条住房项目记录
**目标数据库（Neo4j）：** 11,183 个节点，~16,900 条关系边

---

## 已完成的功能

| 功能 | 状态 | 关键文件 |
|------|------|---------|
| Schema 自动分析 | ✅ | `src/noah_converter/schema_analyzer/` |
| 映射引擎（YAML 规则驱动） | ✅ | `src/noah_converter/mapping_engine/` |
| 数据迁移（MERGE，可幂等重跑） | ✅ | `python main.py migrate` |
| 迁移后审计 | ✅ | `python main.py audit` |
| Text2Cypher（Claude API，95% 准确率） | ✅ | `src/noah_converter/text2cypher/` |
| Streamlit Web UI（5个页面） | ✅ | `app/` |
| GeoJSON 导出 | ✅ | `app/utils/geojson_export.py` |
| 图可视化（pyvis） | ✅ | Explore 页 → Graph View 标签 |
| Saved Queries | ✅ | `app/utils/saved_queries.py` |
| 参数化查询模板 | ✅ | `app/pages/3_Templates.py` |
| Explain 面板（Graphviz 路径图） | ✅ | `app/utils/explain.py` |
| 教育用 Jupyter Notebook + 答案 | ✅ | `notebooks/03_graph_vs_sql_tutorial.ipynb` |

---

## 如何运行

```bash
# 激活虚拟环境（每次都要）
source venv/bin/activate

# 检查数据库连接状态
python main.py status

# 启动 Web 界面
streamlit run app/Home.py --server.port 8505
# 然后打开 http://localhost:8505
```

**数据库凭证（本地）：**
- PostgreSQL: `localhost:5432`, db=`noah_housing`, user=`postgres`, password=`password123`
- Neo4j: `bolt://localhost:7687`, user=`neo4j`, password=`password123`

---

## 关键数据情况

| 表/节点 | 数量 | 备注 |
|--------|------|------|
| housing_projects (PG) | 8,604 | 建筑级数据，serial id 为主键 |
| zip_shapes (PG) | 177 | NYC Open Data，PostGIS geometry |
| rent_burden (PG) | 2,225 | ACS 2022 B25070 + TIGER shapefile |
| HousingProject (Neo4j) | 8,604 | merge key: db_id |
| ZipCode (Neo4j) | 177 | merge key: zip_code |
| AffordabilityAnalysis (Neo4j) | 177 | merge key: zip_code |
| RentBurden (Neo4j) | 2,225 | merge key: geo_id |

**已知数据缺口：**
- `AffordabilityAnalysis.median_rent_usd` 和 `rent_to_income_ratio` 为 NULL（StreetEasy 私有数据无法获取，用 ACS 租金负担率替代）

---

## 文档

| 文件 | 用途 |
|------|------|
| `README.md` | 项目总览、快速开始、benchmark 结果 |
| `docs/CAPSTONE_REPORT.md/pdf` | 完整毕设报告（~4,000 字，含 Ethical Considerations） |
| `docs/guides/USER_GUIDE.md` | 终端用户使用指南 |
| `docs/guides/SETUP_GUIDE_CN.md/pdf` | 中文安装配置指南（小白友好） |
| `docs/architecture/SYSTEM_ARCHITECTURE.md` | 系统架构说明 |
| `docs/api/API_REFERENCE.md` | Python API 文档 |
| `resources/questions_for_yue_and_prof.md` | 待确认问题（v2，含已解决存档） |

---

## 待教授确认的事项

见 `resources/questions_for_yue_and_prof.md`，主要三点：
1. **Q7**：StreetEasy 数据缺失（`median_rent_usd` 为 NULL）是否影响评分？
2. **Q9**：Text2Cypher 的 4-标准 20 题评估方法论是否符合预期？
3. **Q10**：答辩形式（demo/slides）、是否需要 live 部署？

---

## 代码风格

- Black 格式化，Ruff linting，MyPy 类型检查，PEP 8
