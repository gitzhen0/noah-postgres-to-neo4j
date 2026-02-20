# Text2Cypher: Multi-LLM Provider Architecture

## 设计目标

**让非技术人员用自然语言查询 Neo4j，支持任意 LLM provider**

### 用户故事
- 用户只需提供 API key（Claude / OpenAI / etc.）
- 自动翻译自然语言 → Cypher
- 执行查询并返回结果
- 用自然语言解释结果

---

## 架构设计

### 1. LLM Provider 抽象层

```python
# src/noah_converter/text2cypher/providers/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseLLMProvider(ABC):
    """抽象基类：所有 LLM provider 必须实现这个接口"""

    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model
        self.config = kwargs

    @abstractmethod
    def generate_cypher(self, question: str, schema_context: str) -> str:
        """生成 Cypher 查询"""
        pass

    @abstractmethod
    def explain_results(self, question: str, cypher: str, results: list) -> str:
        """解释查询结果"""
        pass
```

### 2. 具体 Provider 实现

#### Claude Provider (推荐)
```python
# src/noah_converter/text2cypher/providers/claude_provider.py
from anthropic import Anthropic
from .base import BaseLLMProvider

class ClaudeProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.client = Anthropic(api_key=api_key)

    def generate_cypher(self, question: str, schema_context: str) -> str:
        prompt = f"""You are a Neo4j Cypher expert for a NYC housing database.

{schema_context}

User question: {question}

Generate a Cypher query to answer this question. Return ONLY the Cypher query, no explanations.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    def explain_results(self, question: str, cypher: str, results: list) -> str:
        prompt = f"""Explain these query results in simple English:

Question: {question}
Cypher: {cypher}
Results: {results}

Provide a brief, non-technical explanation for a business user."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()
```

#### OpenAI Provider
```python
# src/noah_converter/text2cypher/providers/openai_provider.py
from openai import OpenAI
from .base import BaseLLMProvider

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.client = OpenAI(api_key=api_key)

    def generate_cypher(self, question: str, schema_context: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {"role": "system", "content": f"You are a Neo4j Cypher expert.\n\n{schema_context}"},
                {"role": "user", "content": f"Generate Cypher for: {question}"}
            ]
        )

        return response.choices[0].message.content.strip()

    def explain_results(self, question: str, cypher: str, results: list) -> str:
        # Similar implementation
        pass
```

#### Google Gemini Provider
```python
# src/noah_converter/text2cypher/providers/gemini_provider.py
import google.generativeai as genai
from .base import BaseLLMProvider

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro", **kwargs):
        super().__init__(api_key, model, **kwargs)
        genai.configure(api_key=api_key)
        self.model_instance = genai.GenerativeModel(model)

    def generate_cypher(self, question: str, schema_context: str) -> str:
        prompt = f"{schema_context}\n\nQuestion: {question}\n\nCypher:"
        response = self.model_instance.generate_content(prompt)
        return response.text.strip()

    def explain_results(self, question: str, cypher: str, results: list) -> str:
        # Similar implementation
        pass
```

---

### 3. Provider Factory (工厂模式)

```python
# src/noah_converter/text2cypher/providers/factory.py
from typing import Type
from .base import BaseLLMProvider
from .claude_provider import ClaudeProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider

class LLMProviderFactory:
    """工厂类：根据配置创建对应的 LLM provider"""

    _providers: Dict[str, Type[BaseLLMProvider]] = {
        "claude": ClaudeProvider,
        "anthropic": ClaudeProvider,  # Alias
        "openai": OpenAIProvider,
        "gpt": OpenAIProvider,  # Alias
        "gemini": GeminiProvider,
        "google": GeminiProvider,  # Alias
    }

    @classmethod
    def create(cls, provider_name: str, api_key: str, model: str = None, **kwargs) -> BaseLLMProvider:
        """创建 LLM provider 实例"""
        provider_name = provider_name.lower()

        if provider_name not in cls._providers:
            raise ValueError(
                f"Unknown provider: {provider_name}. "
                f"Supported: {', '.join(cls._providers.keys())}"
            )

        provider_class = cls._providers[provider_name]

        # 使用默认 model 如果没有指定
        if model is None:
            if provider_name in ["claude", "anthropic"]:
                model = "claude-sonnet-4-5-20250929"
            elif provider_name in ["openai", "gpt"]:
                model = "gpt-4-turbo-preview"
            elif provider_name in ["gemini", "google"]:
                model = "gemini-1.5-pro"

        return provider_class(api_key=api_key, model=model, **kwargs)

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[BaseLLMProvider]):
        """注册自定义 provider（可扩展性）"""
        cls._providers[name] = provider_class
```

---

### 4. Text2Cypher 主类 (使用 LangChain)

```python
# src/noah_converter/text2cypher/translator.py
from langchain.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from .providers.factory import LLMProviderFactory

class Text2CypherTranslator:
    """Text2Cypher 翻译器 - 支持多种 LLM"""

    def __init__(self, neo4j_config, llm_provider: str, api_key: str, model: str = None):
        # Connect to Neo4j
        self.graph = Neo4jGraph(
            url=neo4j_config.uri,
            username=neo4j_config.user,
            password=neo4j_config.password
        )

        # Create LLM instance using LangChain
        self.llm = self._create_langchain_llm(llm_provider, api_key, model)

        # Create chain
        self.chain = GraphCypherQAChain.from_llm(
            llm=self.llm,
            graph=self.graph,
            verbose=True,
            return_intermediate_steps=True
        )

    def _create_langchain_llm(self, provider: str, api_key: str, model: str):
        """创建 LangChain LLM 实例"""
        provider = provider.lower()

        if provider in ["claude", "anthropic"]:
            return ChatAnthropic(
                anthropic_api_key=api_key,
                model=model or "claude-sonnet-4-5-20250929",
                temperature=0
            )

        elif provider in ["openai", "gpt"]:
            return ChatOpenAI(
                openai_api_key=api_key,
                model=model or "gpt-4-turbo-preview",
                temperature=0
            )

        else:
            raise ValueError(f"Unsupported provider for LangChain: {provider}")

    def query(self, question: str) -> dict:
        """执行自然语言查询"""
        result = self.chain.invoke({"query": question})

        return {
            "question": question,
            "cypher": result.get("intermediate_steps", [{}])[0].get("query", ""),
            "answer": result["result"],
            "raw_results": result.get("intermediate_steps", [{}])[0].get("context", [])
        }
```

---

### 5. 配置文件支持

```yaml
# config/config.yaml
text2cypher:
  # Provider: claude, openai, gemini
  provider: "claude"

  # API Key (可以从环境变量读取)
  api_key: ${ANTHROPIC_API_KEY}

  # Model (可选，不指定则使用默认)
  model: "claude-sonnet-4-5-20250929"

  # Temperature
  temperature: 0.0

  # Max tokens
  max_tokens: 2000

  # Schema-aware prompting
  schema_aware: true

# Alternative providers
alternative_providers:
  openai:
    api_key: ${OPENAI_API_KEY}
    model: "gpt-4-turbo-preview"

  gemini:
    api_key: ${GOOGLE_API_KEY}
    model: "gemini-1.5-pro"
```

---

### 6. CLI 使用示例

```bash
# 使用默认 provider (Claude)
python main.py query "Which ZIP codes have the most affordable housing?"

# 指定 OpenAI
python main.py query --provider openai "Show me projects in Brooklyn"

# 指定 Gemini
python main.py query --provider gemini --model gemini-1.5-flash "List all boroughs"

# 交互模式
python main.py chat --provider claude
```

---

### 7. Python API 使用示例

```python
from noah_converter.text2cypher import Text2CypherTranslator
from noah_converter.utils.config import load_config

# 加载配置
config = load_config()

# 方式 1: 使用配置文件中的 provider
translator = Text2CypherTranslator(
    neo4j_config=config.target_db,
    llm_provider=config.text2cypher.provider,
    api_key=config.text2cypher.api_key
)

# 方式 2: 动态指定 provider
translator = Text2CypherTranslator(
    neo4j_config=config.target_db,
    llm_provider="openai",  # 或 "claude", "gemini"
    api_key="sk-your-openai-key"
)

# 查询
result = translator.query("Which ZIP codes have median rent above $4000?")

print(f"Question: {result['question']}")
print(f"Cypher: {result['cypher']}")
print(f"Answer: {result['answer']}")
```

---

## 优势

### ✅ 灵活性
- 用户可以选择任何 LLM provider
- 只需要提供 API key
- 随时切换 provider

### ✅ 可扩展性
- 抽象层设计，易于添加新 provider
- Factory pattern 统一创建接口
- 可以注册自定义 provider

### ✅ 成本优化
- 不同 provider 价格不同
- 用户可以根据预算选择
- OpenAI 便宜，Claude 质量高，Gemini 免费额度大

### ✅ 容错性
- 一个 provider 失败可以切换到另一个
- 支持 fallback 机制

---

## Provider 比较

| Provider | 优势 | 劣势 | 推荐场景 |
|----------|------|------|---------|
| **Claude Sonnet 4.5** | 最强推理能力，代码质量高 | 稍贵 | 生产环境，复杂查询 |
| **GPT-4 Turbo** | 便宜，速度快 | 推理稍弱 | 简单查询，高频使用 |
| **Gemini 1.5 Pro** | 免费额度大，速度快 | 代码生成稍弱 | 开发测试，预算有限 |

---

## 实现计划

### Phase 4A: 核心实现 (2-3 days)
1. ✅ 创建抽象基类 `BaseLLMProvider`
2. ✅ 实现 Claude、OpenAI、Gemini providers
3. ✅ 创建 Factory pattern
4. ✅ 集成 LangChain GraphCypherQAChain
5. ✅ 配置文件支持

### Phase 4B: CLI 集成 (0.5 day)
1. ✅ 添加 `query` 命令
2. ✅ 添加 `chat` 交互模式
3. ✅ Provider 选择参数

### Phase 4C: 测试 & 优化 (1 day)
1. ✅ 测试 20 个基准问题
2. ✅ 优化 prompts
3. ✅ 错误处理

---

## 总结

这个架构的核心思想是：

> **"用户只需要提供任意 LLM 的 API key，系统自动翻译自然语言到 Cypher"**

- 🎯 **用户友好**: 非技术人员可以用自然语言查询
- 🔌 **Provider 无关**: 支持多种 LLM，用户自由选择
- 🚀 **易于扩展**: 添加新 provider 只需实现接口
- 💰 **成本可控**: 用户根据预算选择 provider

这就是**真正的工程化设计** - 不绑定特定技术，给用户最大的灵活性！
