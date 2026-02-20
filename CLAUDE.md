## 背景
* 我要从 0 开始完成这个 capstone 毕设项目, 你可以去 resources 文件夹里看, 里面有 first hand 和 second hand 资料
* first hand 是直接从教授获取的, 你以 first hand 为准
* second hand 是我依靠 first hand 资料 用 gemini 生成出来的, 你也可以参考

## 项目目标
* 开发一个自动化的 PostgreSQL 到 Neo4j 知识图谱转换工具
* 使用 Yue Yu 的 NOAH 数据库实现作为源数据库（更复杂的schema和数据关系）
* 核心功能：
  1. Schema 自动分析和智能映射
  2. 数据迁移和验证
  3. Text2Cypher 自然语言查询界面

## 项目结构说明
* `src/noah_converter/` - 主要源代码
  * `schema_analyzer/` - PostgreSQL schema 分析模块
  * `mapping_engine/` - RDBMS到Graph的映射引擎
  * `data_migrator/` - 数据迁移模块
  * `text2cypher/` - 自然语言转Cypher查询
  * `utils/` - 通用工具类
* `tests/` - 测试代码
* `data/` - 数据文件（schemas, samples, crosswalks）
* `outputs/` - 生成的输出（cypher scripts, reports）
* `config/` - 配置文件
* `notebooks/` - Jupyter notebooks用于探索和原型
* `docs/` - 文档
* `resources/` - 参考资料

## 开发指南
* 配置文件：`config/config.yaml`（从 config.example.yaml 复制）
* 环境变量：`.env`（从 .env.example 复制）
* 主入口：`python main.py`
* 查看帮助：`python main.py --help`
* 分析schema：`python main.py analyze`
* 检查状态：`python main.py status`

## 数据库凭证
* Census API Key: `e1840402fd3183c71e5a783fd086364eed69776d`
* PostgreSQL: localhost:5432, db=noah_housing, user=postgres, password=password123
* Neo4j: bolt://localhost:7687, user=neo4j, password=password123

## 待解决的数据缺口
* **StreetEasy 数据缺失**: `noah_streeteasy_medianrent_2025_10` 表是 Yue 手动从 StreetEasy 收集的私有数据，无法直接获取。
  * 替代方案候选：Zillow Research ZORI（公开下载）或 ACS B25031（中位租金按卧室数，Census API 可获取）
  * 当前状态：表存在但为空（0行）
  * 后续决策：确认用 ACS B25031 替代还是找 Zillow ZORI CSV

## 代码风格
* 使用 Black 格式化代码
* 使用 Ruff 进行 linting
* 使用 MyPy 进行类型检查
* 遵循 PEP 8 规范