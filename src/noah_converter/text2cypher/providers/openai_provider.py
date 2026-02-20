"""
OpenAI LLM Provider

使用 OpenAI API 进行 Text2Cypher 翻译
"""

from typing import Optional
from .base import BaseLLMProvider

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider for Text2Cypher"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",  # 免费模型
        **kwargs
    ):
        """
        初始化 OpenAI provider

        Args:
            api_key: OpenAI API key
            model: OpenAI model ID (default: gpt-3.5-turbo)
            **kwargs: Additional config (temperature, max_tokens, etc.)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai package not installed. "
                "Install with: pip install openai"
            )

        super().__init__(api_key, model, **kwargs)
        self.client = OpenAI(api_key=api_key)
        self.temperature = kwargs.get('temperature', 0)
        self.max_tokens = kwargs.get('max_tokens', 2000)

    def generate_cypher(
        self,
        question: str,
        schema_context: str,
        examples: Optional[str] = None
    ) -> str:
        """
        使用 OpenAI 生成 Cypher 查询

        Args:
            question: 用户问题
            schema_context: Neo4j schema 描述
            examples: Few-shot examples

        Returns:
            Cypher query string
        """
        # 构建 prompt
        system_prompt = self._build_system_prompt(schema_context, examples)
        user_prompt = f"Generate a Cypher query for this question:\n\n{question}"

        # 调用 OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        # 提取 Cypher
        cypher = response.choices[0].message.content
        cypher = self.clean_cypher(cypher)

        return cypher

    def explain_results(
        self,
        question: str,
        cypher: str,
        results: list
    ) -> str:
        """
        使用 OpenAI 解释查询结果

        Args:
            question: 原始问题
            cypher: 生成的 Cypher
            results: 查询结果

        Returns:
            Natural language explanation
        """
        prompt = f"""You are a helpful assistant explaining database query results.

Original Question: {question}

Cypher Query:
{cypher}

Query Results:
{results}

Provide a brief, non-technical explanation of what these results mean in answer to the original question. Be concise and clear.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.3,
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content.strip()

    def _build_system_prompt(
        self,
        schema_context: str,
        examples: Optional[str] = None
    ) -> str:
        """构建 system prompt"""

        prompt = f"""You are an expert Neo4j Cypher query generator for a NYC housing affordability database.

{schema_context}

IMPORTANT INSTRUCTIONS:
1. Generate ONLY valid Cypher queries
2. Use MATCH for read operations
3. Always include RETURN clause
4. Use proper property names from the schema
5. Use WHERE for filtering
6. Return ONLY the Cypher query without explanations or markdown
7. Do not wrap the query in code blocks

"""

        # 添加 few-shot examples
        if examples:
            prompt += f"\n{examples}\n\n"

        return prompt
