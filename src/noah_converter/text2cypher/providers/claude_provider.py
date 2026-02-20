"""
Claude (Anthropic) LLM Provider

使用 Claude API 进行 Text2Cypher 翻译
"""

from typing import Optional
from .base import BaseLLMProvider

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class ClaudeProvider(BaseLLMProvider):
    """Claude (Anthropic) provider for Text2Cypher"""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5-20250929",
        **kwargs
    ):
        """
        初始化 Claude provider

        Args:
            api_key: Anthropic API key
            model: Claude model ID (default: Sonnet 4.5)
            **kwargs: Additional config (temperature, max_tokens, etc.)
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )

        super().__init__(api_key, model, **kwargs)
        self.client = Anthropic(api_key=api_key)
        self.temperature = kwargs.get('temperature', 0)
        self.max_tokens = kwargs.get('max_tokens', 2000)

    def generate_cypher(
        self,
        question: str,
        schema_context: str,
        examples: Optional[str] = None
    ) -> str:
        """
        使用 Claude 生成 Cypher 查询

        Args:
            question: 用户问题
            schema_context: Neo4j schema 描述
            examples: Few-shot examples

        Returns:
            Cypher query string
        """
        # 构建 prompt
        prompt = self._build_cypher_prompt(question, schema_context, examples)

        # 调用 Claude API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # 提取 Cypher
        cypher = response.content[0].text
        cypher = self.clean_cypher(cypher)

        return cypher

    def explain_results(
        self,
        question: str,
        cypher: str,
        results: list
    ) -> str:
        """
        使用 Claude 解释查询结果

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

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            temperature=0.3,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.content[0].text.strip()

    def _build_cypher_prompt(
        self,
        question: str,
        schema_context: str,
        examples: Optional[str] = None
    ) -> str:
        """构建完整的 Cypher 生成 prompt"""

        prompt = f"""You are an expert Neo4j Cypher query generator for a NYC housing affordability database.

{schema_context}

IMPORTANT INSTRUCTIONS:
1. Generate ONLY valid Cypher queries
2. Use MATCH for read operations, CREATE for write operations
3. Always include RETURN clause
4. Use proper property names from the schema
5. Use WHERE for filtering
6. Return ONLY the Cypher query, no explanations
7. Do not use markdown code blocks in your response

"""

        # 添加 few-shot examples
        if examples:
            prompt += f"\n{examples}\n\n"

        # 添加用户问题
        prompt += f"""User Question: {question}

Generate the Cypher query:"""

        return prompt
