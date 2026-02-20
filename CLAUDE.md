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

## 代码风格
* 使用 Black 格式化代码
* 使用 Ruff 进行 linting
* 使用 MyPy 进行类型检查
* 遵循 PEP 8 规范