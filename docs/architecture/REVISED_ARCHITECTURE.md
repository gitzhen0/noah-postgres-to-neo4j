# NOAH Converter - Revised Architecture (Tool-Based)

## Philosophy: 站在巨人的肩膀上

> "好的程序员知道写什么代码，伟大的程序员知道重用什么代码。"

我们的核心原则：**尽可能使用现成的、经过验证的开源工具，只在必要时编写胶水代码。**

---

## 工具栈选择

### ✅ 选中的开源工具

| Layer | Tool | Version | Purpose | License |
|-------|------|---------|---------|---------|
| **ETL Core** | Neo4j APOC | v2026.01.0 | JDBC data loading, transformations | Apache 2.0 |
| **Schema Mapping** | Data2Neo | v1.4.3 | YAML-based schema → graph mapping | Apache 2.0 |
| **Text2Cypher** | LangChain + Claude | Latest | Natural language → Cypher translation | MIT |
| **Validation** | Great Expectations | Latest | Data quality validation | Apache 2.0 |
| **Spatial Data** | Custom (PostGIS → WKT) | - | Handle geometry columns | - |

### ❌ 不使用的工具

- **Neo4j ETL Tool** - 2022年后停止维护
- **Rel2Graph** - 只是研究原型，活跃度低
- **手撸 ORM** - 没必要重新发明轮子

---

## 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    NOAH Converter System                     │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  PostgreSQL  │────▶│  APOC JDBC   │────▶│    Neo4j     │
│  + PostGIS   │     │  Load Data   │     │   Graph DB   │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    ▲                      │
       │                    │                      │
       ▼                    │                      ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Schema       │────▶│  Data2Neo    │     │  LangChain   │
│ Analyzer     │     │  YAML Config │     │ Text2Cypher  │
│ (existing)   │     └──────────────┘     └──────────────┘
└──────────────┘            │                      │
                            │                      ▼
                            │              ┌──────────────┐
                            │              │   Claude     │
                            │              │  Sonnet 4.5  │
                            │              └──────────────┘
                            ▼
                     ┌──────────────┐
                     │ Great        │
                     │ Expectations │
                     │ Validation   │
                     └──────────────┘
```

---

## Phase-by-Phase 工具使用

### Phase 0: ✅ Setup (已完成)
- **工具**: Docker, PostgreSQL, Neo4j
- **代码**: 100% 现成工具，0% 手撸

### Phase 1: Design Graph Model
- **工具**: Data2Neo examples, Neo4j Bloom (可视化)
- **产出**: YAML配置文件（不是代码！）
- **代码量**: ~50 行 YAML

### Phase 2: Mapping Engine
- **工具**: Data2Neo + Custom PostgreSQL Iterator
- **代码量**: ~100 行 Python（只写 Iterator 适配器）
- **重用**: Data2Neo 的整个映射引擎

### Phase 3: Data Migration
- **工具**: APOC `apoc.load.jdbc()` + Data2Neo
- **代码量**: ~200 行（主要是配置和调用）
- **重用**: APOC 的批量加载、事务管理

**核心 Cypher 示例（使用 APOC）：**
```cypher
// 直接从 PostgreSQL 加载数据创建节点
CALL apoc.load.jdbc(
  'jdbc:postgresql://localhost:5432/noah_housing?user=postgres&password=password123',
  'SELECT * FROM housing_projects'
) YIELD row
CREATE (p:HousingProject {
  projectId: row.project_id,
  name: row.project_name,
  totalUnits: row.total_units,
  location: point({latitude: row.latitude, longitude: row.longitude})
})
```

### Phase 4: Text2Cypher
- **工具**: LangChain + Anthropic Claude
- **代码量**: ~150 行（集成和配置）
- **重用**: LangChain 的 schema-aware prompting

**示例代码：**
```python
from langchain.chains import GraphCypherQAChain
from langchain_anthropic import ChatAnthropic
from langchain.graphs import Neo4jGraph

# 使用现成的 GraphCypherQAChain
graph = Neo4jGraph(url="bolt://localhost:7687", username="neo4j", password="password123")
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929", temperature=0)

chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True
)

# 直接使用，不需要自己写 prompt engineering
result = chain.invoke("Which ZIP codes have the most affordable housing projects?")
```

### Phase 5: Validation
- **工具**: Great Expectations + Custom Neo4j validator
- **代码量**: ~100 行（配置 expectations）
- **重用**: Great Expectations 的整个验证框架

---

## 我们实际要写的代码

### 总代码量估计：~600-800 行

#### 1. PostgreSQL Iterator for Data2Neo (~100 lines)
```python
# src/noah_converter/adapters/postgres_iterator.py
from data2neo import Iterator
import psycopg2

class PostgreSQLIterator(Iterator):
    """Adapter to make PostgreSQL work with Data2Neo"""
    def __init__(self, conn_string, table_name):
        self.conn = psycopg2.connect(conn_string)
        self.table = table_name

    def __iter__(self):
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {self.table}")
        for row in cursor:
            yield dict(zip([desc[0] for desc in cursor.description], row))
```

#### 2. APOC Migration Scripts (~200 lines)
```python
# src/noah_converter/migration/apoc_migrator.py
from neo4j import GraphDatabase

class APOCMigrator:
    """Wrapper around APOC procedures for data loading"""
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, pg_jdbc_url):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.jdbc_url = pg_jdbc_url

    def load_table(self, table_name, node_label, mapping):
        """Load table as nodes using APOC"""
        cypher = f"""
        CALL apoc.load.jdbc(
          '{self.jdbc_url}',
          'SELECT * FROM {table_name}'
        ) YIELD row
        CREATE (n:{node_label})
        SET n = apoc.map.clean(row, [], [])
        """
        with self.driver.session() as session:
            session.run(cypher)
```

#### 3. Data2Neo YAML Configs (~100 lines total)
```yaml
# config/data2neo/housing_projects.yaml
nodes:
  - label: HousingProject
    source:
      iterator: PostgreSQLIterator
      table: housing_projects
    properties:
      projectId: project_id
      name: project_name
      totalUnits: total_units
      borough: borough
      zipcode: zipcode
      location:
        type: point
        latitude: latitude
        longitude: longitude
```

#### 4. LangChain Text2Cypher Integration (~150 lines)
```python
# src/noah_converter/text2cypher/langchain_translator.py
from langchain.chains import GraphCypherQAChain
from langchain_anthropic import ChatAnthropic
from langchain.graphs import Neo4jGraph

class Text2CypherTranslator:
    """Wrapper around LangChain's GraphCypherQAChain"""
    def __init__(self, config):
        self.graph = Neo4jGraph(
            url=config.neo4j_uri,
            username=config.neo4j_user,
            password=config.neo4j_password
        )
        self.llm = ChatAnthropic(
            model=config.text2cypher.model,
            temperature=config.text2cypher.temperature
        )
        self.chain = GraphCypherQAChain.from_llm(
            llm=self.llm,
            graph=self.graph,
            verbose=True
        )

    def translate(self, question: str):
        """Convert natural language to Cypher and execute"""
        return self.chain.invoke(question)
```

#### 5. CLI & Orchestration (~150 lines)
保留现有的 `main.py` 框架，只是调用上述工具。

#### 6. Validation (~100 lines)
使用 Great Expectations 进行数据质量检查。

---

## 依赖更新

### 新增到 requirements.txt

```txt
# Existing dependencies
python-dotenv>=1.0.0
pyyaml>=6.0
...

# New: Open-source tools
data2neo>=1.4.3              # Schema mapping engine
langchain>=0.3.14            # Text2Cypher framework
langchain-anthropic>=0.4.0   # Claude integration
langchain-neo4j>=0.2.0       # Neo4j integration
great-expectations>=1.4.0    # Data validation
```

---

## 工作分配

| 我们写的代码 | 开源工具提供的功能 |
|-------------|------------------|
| PostgreSQL Iterator (~100 lines) | Data2Neo 映射引擎 (10,000+ lines) |
| APOC 调用脚本 (~200 lines) | APOC 核心库 (100,000+ lines) |
| LangChain 集成 (~150 lines) | LangChain框架 (50,000+ lines) |
| CLI 命令 (~150 lines) | Click框架 |
| YAML 配置 (~100 lines) | Data2Neo解析器 |
| 验证脚本 (~100 lines) | Great Expectations (30,000+ lines) |
| **总计：~800 lines** | **总计：~200,000+ lines 重用** |

**代码重用率：99.6%！**

---

## 开发时间重新估算

| Phase | 原计划时间 | 使用工具后时间 | 节省 |
|-------|----------|--------------|------|
| Phase 2: Mapping Engine | 3-4 days | **0.5-1 day** | 75% |
| Phase 3: Data Migration | 9-11 days | **1-2 days** | 85% |
| Phase 4: Text2Cypher | 4-5 days | **0.5-1 day** | 80% |
| **Total** | **16-20 days** | **2-4 days** | **85% faster** |

---

## 优势总结

### ✅ 技术优势
1. **稳定性**: 使用经过验证的生产级工具
2. **可维护性**: 依赖活跃维护的开源项目
3. **学习曲线**: 工具有完整文档和社区支持
4. **性能**: APOC 优化过的批量加载
5. **扩展性**: 工具支持复杂场景

### ✅ 学术优势
1. **引用价值**: 使用论文中提到的工具（Data2Neo）
2. **最佳实践**: 展示工程中的工具选型能力
3. **创新点**: 工具的组合和集成方式
4. **可复现**: 所有工具开源，容易复现

### ✅ 工程优势
1. **快速开发**: 85% 的时间节省
2. **低风险**: 减少自己写的 bug
3. **易调试**: 工具有完善的日志和错误处理
4. **社区支持**: 遇到问题可以查文档、提 issue

---

## Next Steps

1. ✅ **安装工具**
   ```bash
   pip install data2neo langchain langchain-anthropic langchain-neo4j great-expectations
   ```

2. ✅ **测试 APOC 连接**
   ```cypher
   CALL apoc.load.jdbc(
     'jdbc:postgresql://localhost:5432/noah_housing?user=postgres&password=password123',
     'SELECT COUNT(*) as count FROM housing_projects'
   ) YIELD row
   RETURN row.count
   ```

3. ✅ **创建 Data2Neo 配置**
   - 为 housing_projects 创建 YAML 映射
   - 定义节点和关系类型

4. ✅ **验证端到端流程**
   - 小批量测试（10 rows）
   - 验证数据正确性
   - 扩展到全量

---

## References

- [Data2Neo Documentation](https://github.com/jkminder/data2neo)
- [APOC User Guide](https://neo4j.com/labs/apoc/5/)
- [LangChain Neo4j Integration](https://python.langchain.com/docs/integrations/graphs/neo4j_cypher)
- [Great Expectations Docs](https://docs.greatexpectations.io/)
