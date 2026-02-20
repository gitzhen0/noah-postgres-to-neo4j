"""
Gemini (Google) LLM Provider

使用 Google Gemini API 进行 Text2Cypher 翻译
"""

from typing import Optional
from .base import BaseLLMProvider

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiProvider(BaseLLMProvider):
    """Gemini provider for Text2Cypher"""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-pro",
        **kwargs
    ):
        """
        初始化 Gemini provider

        Args:
            api_key: Google API key
            model: Gemini model ID (default: gemini-1.5-pro)
            **kwargs: Additional config (temperature, max_tokens, etc.)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )

        super().__init__(api_key, model, **kwargs)

        # Configure Gemini
        genai.configure(api_key=api_key)

        # Create model instance
        generation_config = {
            "temperature": kwargs.get('temperature', 0),
            "max_output_tokens": kwargs.get('max_tokens', 2000),
        }

        self.model_instance = genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config
        )

        self.temperature = kwargs.get('temperature', 0)
        self.max_tokens = kwargs.get('max_tokens', 2000)

    def generate_cypher(
        self,
        question: str,
        schema_context: str,
        examples: Optional[str] = None
    ) -> str:
        """
        使用 Gemini 生成 Cypher 查询

        Args:
            question: 用户问题
            schema_context: Neo4j schema 描述
            examples: Few-shot examples

        Returns:
            Cypher query string
        """
        # 构建 prompt
        prompt = self._build_prompt(question, schema_context, examples)

        # 调用 Gemini API
        response = self.model_instance.generate_content(prompt)

        # 提取 Cypher
        cypher = response.text
        cypher = self.clean_cypher(cypher)

        return cypher

    def explain_results(
        self,
        question: str,
        cypher: str,
        results: list
    ) -> str:
        """
        使用 Gemini 解释查询结果

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

        response = self.model_instance.generate_content(prompt)

        return response.text.strip()

    def _build_prompt(
        self,
        question: str,
        schema_context: str,
        examples: Optional[str] = None
    ) -> str:
        """构建完整的 prompt"""

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

        prompt += f"Generate a Cypher query for this question:\n\n{question}\n\nCypher:"

        return prompt
