# Text2Cypher 使用指南

## 🎯 概述

Text2Cypher 允许用户用自然语言查询 Neo4j 数据库，无需了解 Cypher 语法。

**核心功能：**
- ✅ 自然语言 → Cypher 自动翻译
- ✅ 支持多个 LLM providers（Claude, OpenAI, Gemini）
- ✅ 自动执行查询并返回结果
- ✅ 生成自然语言解释

---

## 🚀 快速开始

### 1. 设置 API Key

首先设置你的 LLM provider API key：

```bash
# Claude (Anthropic)
export ANTHROPIC_API_KEY='your-api-key-here'

# 或者 OpenAI
export OPENAI_API_KEY='your-api-key-here'

# 或者添加到 .env 文件
echo "ANTHROPIC_API_KEY=your-api-key-here" >> .env
```

### 2. Python API 使用

```python
from noah_converter.utils.config import load_config
from noah_converter.utils.db_connection import Neo4jConnection
from noah_converter.text2cypher import Text2CypherTranslator
import os

# 加载配置
config = load_config()
neo4j_conn = Neo4jConnection(config.target_db)

# 创建 translator
translator = Text2CypherTranslator(
    neo4j_conn=neo4j_conn,
    llm_provider="claude",  # 或 "openai", "gemini"
    api_key=os.getenv('ANTHROPIC_API_KEY'),
    model="claude-sonnet-4-5-20250929"  # 可选
)

# 查询
result = translator.query(
    question="Which ZIP codes are neighbors of 10001?",
    execute=True,
    explain=True
)

print(f"Generated Cypher: {result['cypher']}")
print(f"Results: {result['results']}")
print(f"Explanation: {result['explanation']}")
```

### 3. 命令行使用

```bash
# 运行测试脚本
python scripts/test_text2cypher.py

# 或者交互模式（TODO）
python main.py chat
```

---

## 📝 支持的查询类型

### 1. 简单查询
```
"Which ZIP codes are in Manhattan?"
"Show me all housing projects in ZIP code 11106"
"How many housing projects are there?"
```

### 2. 邻接查询
```
"Which ZIP codes are neighbors of 10001?"
"Find all ZIP codes connected to 11106"
```

### 3. 空间距离查询
```
"Find ZIP codes within 5km of 10001"
"Which ZIP codes are closest to 10002?"
```

### 4. Multi-hop 遍历
```
"Find all ZIP codes within 2 hops of 10001"
"Show me the neighborhood network of 11106"
```

### 5. 聚合查询
```
"How many housing projects are in each borough?"
"Which borough has the most affordable housing units?"
"What's the total number of affordable units across all projects?"
```

### 6. 组合查询
```
"Find housing projects in ZIP codes neighboring 10001"
"Show me affordable housing projects within 3km of Manhattan"
```

---

## 🔧 高级配置

### 切换 LLM Provider

```python
# 使用 Claude (推荐)
translator = Text2CypherTranslator(
    neo4j_conn=neo4j_conn,
    llm_provider="claude",
    api_key=os.getenv('ANTHROPIC_API_KEY')
)

# 使用 OpenAI
translator = Text2CypherTranslator(
    neo4j_conn=neo4j_conn,
    llm_provider="openai",
    api_key=os.getenv('OPENAI_API_KEY'),
    model="gpt-4-turbo-preview"
)

# 使用 Gemini
translator = Text2CypherTranslator(
    neo4j_conn=neo4j_conn,
    llm_provider="gemini",
    api_key=os.getenv('GOOGLE_API_KEY'),
    model="gemini-1.5-pro"
)
```

### 调整参数

```python
translator = Text2CypherTranslator(
    neo4j_conn=neo4j_conn,
    llm_provider="claude",
    api_key=api_key,
    temperature=0,      # 0 = 确定性，1 = 创造性
    max_tokens=2000     # 最大响应长度
)
```

---

## 📊 示例输出

**输入：**
```python
result = translator.query("Which ZIP codes are neighbors of 10001?")
```

**输出：**
```python
{
    'question': 'Which ZIP codes are neighbors of 10001?',
    'cypher': '''
        MATCH (z:Zipcode {zipcode: '10001'})-[:NEIGHBORS]-(neighbor)
        RETURN neighbor.zipcode, neighbor.borough
        ORDER BY neighbor.zipcode
    ''',
    'results': [
        {'neighbor.zipcode': '10002', 'neighbor.borough': 'Manhattan'},
        {'neighbor.zipcode': '10003', 'neighbor.borough': 'Manhattan'},
        {'neighbor.zipcode': '11101', 'neighbor.borough': 'Queens'},
        ...
    ],
    'explanation': 'ZIP code 10001 has 10 neighboring ZIP codes, including 10002 and 10003 in Manhattan, and 11101 in Queens...'
}
```

---

## 🧪 测试和验证

### 运行基准测试

```bash
# 运行预定义的测试问题
python scripts/test_text2cypher.py

# 查看准确率报告
cat outputs/reports/text2cypher_accuracy.json
```

### 自定义测试问题

创建 `tests/text2cypher_questions.txt`：
```
Which ZIP codes are in Brooklyn?
Show me all housing projects in Manhattan
Find ZIP codes within 10km of 10001
...
```

运行测试：
```bash
python scripts/benchmark_text2cypher.py --questions tests/text2cypher_questions.txt
```

---

## ⚠️ 常见问题

### 1. API Key 未设置
```
Error: ANTHROPIC_API_KEY environment variable not set
```

**解决：**
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

### 2. 生成的 Cypher 无效
```
Error: Generated Cypher failed validation
```

**原因：**
- LLM 可能生成了错误的语法
- Schema 上下文不够清晰

**解决：**
- 降低 temperature (设为 0)
- 检查 schema context
- 尝试重新表述问题

### 3. 查询超时
```
Error: Query execution timeout
```

**解决：**
- 添加 LIMIT 限制结果数量
- 优化 Cypher 查询
- 检查 Neo4j 索引

---

## 📈 性能优化

### 1. 缓存 Schema Context
```python
# Schema context 会自动缓存，不会重复调用 Neo4j
translator = Text2CypherTranslator(...)
# 首次调用：获取 schema
# 后续调用：使用缓存
```

### 2. 批量查询
```python
questions = [
    "Which ZIP codes are in Manhattan?",
    "Show me all housing projects in Brooklyn",
    ...
]

results = []
for question in questions:
    result = translator.query(question)
    results.append(result)
```

### 3. 只生成 Cypher（不执行）
```python
result = translator.query(
    question="...",
    execute=False  # 只生成 Cypher，不执行
)
print(result['cypher'])  # 手动审核后再执行
```

---

## 🎯 准确率目标

**Capstone 项目要求：>75% 准确率**

**评估标准：**
1. Cypher 语法正确
2. 查询逻辑符合问题意图
3. 返回结果正确

**当前状态：**
- ✅ 架构实现完成
- ⏳ 基准测试待运行
- ⏳ 准确率待评估

**提升准确率的方法：**
1. 增加 few-shot examples
2. 优化 schema description
3. 使用更强的 LLM model（Claude Opus）
4. 实现 query validation 和 auto-correction

---

## 🔮 未来功能

- [ ] 交互式 chat 模式
- [ ] Query 历史记录
- [ ] 自动 query 优化
- [ ] Multi-turn conversations
- [ ] Query explanation with visualization
- [ ] Support for write operations (CREATE, UPDATE, DELETE)

---

## 📚 参考资料

- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)
- [Claude API Documentation](https://docs.anthropic.com/)
- [LangChain GraphCypherQAChain](https://python.langchain.com/docs/use_cases/graph/graph_cypher_qa)

---

## 💡 最佳实践

1. **问题清晰明确**
   - 好："Which ZIP codes are neighbors of 10001?"
   - 差："Tell me about 10001"

2. **使用正确的术语**
   - 使用 "ZIP code" 而不是 "postal code"
   - 使用 "housing project" 而不是 "building"

3. **从简单到复杂**
   - 先测试简单查询
   - 再尝试 multi-hop 和聚合查询

4. **验证结果**
   - 总是检查生成的 Cypher
   - 对比预期结果

5. **迭代优化**
   - 收集失败案例
   - 改进 schema context
   - 添加更多 examples

---

## 🤝 贡献

如果你发现 Text2Cypher 生成了错误的 Cypher，请：

1. 记录问题和生成的查询
2. 手动修正 Cypher
3. 将案例添加到 examples
4. 提交 PR 或 issue

这将帮助提高整体准确率！
