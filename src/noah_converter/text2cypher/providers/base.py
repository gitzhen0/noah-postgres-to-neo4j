"""
Base LLM Provider Interface

所有 LLM providers 必须实现这个接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseLLMProvider(ABC):
    """抽象基类：所有 LLM provider 必须实现这个接口"""

    def __init__(self, api_key: str, model: str, **kwargs):
        """
        初始化 LLM provider

        Args:
            api_key: API key for the LLM service
            model: Model name/ID to use
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.model = model
        self.config = kwargs

    @abstractmethod
    def generate_cypher(
        self,
        question: str,
        schema_context: str,
        examples: Optional[str] = None
    ) -> str:
        """
        生成 Cypher 查询

        Args:
            question: 用户的自然语言问题
            schema_context: Neo4j schema 描述
            examples: Few-shot examples（可选）

        Returns:
            Cypher query string
        """
        pass

    @abstractmethod
    def explain_results(
        self,
        question: str,
        cypher: str,
        results: list
    ) -> str:
        """
        用自然语言解释查询结果

        Args:
            question: 原始问题
            cypher: 生成的 Cypher 查询
            results: 查询结果

        Returns:
            Natural language explanation
        """
        pass

    def validate_cypher(self, cypher: str) -> bool:
        """
        基本的 Cypher 语法验证

        Args:
            cypher: Cypher query string

        Returns:
            True if valid, False otherwise
        """
        # 基本检查
        cypher = cypher.strip()

        if not cypher:
            return False

        # 检查是否包含 Cypher 关键字
        cypher_keywords = ['MATCH', 'RETURN', 'WHERE', 'CREATE', 'WITH', 'OPTIONAL']
        has_keyword = any(keyword in cypher.upper() for keyword in cypher_keywords)

        return has_keyword

    def clean_cypher(self, cypher: str) -> str:
        """
        清理 LLM 返回的 Cypher（移除 markdown 代码块等）

        Args:
            cypher: Raw response from LLM

        Returns:
            Cleaned Cypher query
        """
        # 移除 markdown 代码块
        if '```' in cypher:
            # Extract from ```cypher ... ```
            lines = cypher.split('\n')
            in_code_block = False
            cleaned_lines = []

            for line in lines:
                if line.strip().startswith('```'):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    cleaned_lines.append(line)

            cypher = '\n'.join(cleaned_lines)

        # 移除注释
        lines = [line for line in cypher.split('\n')
                 if not line.strip().startswith('//')]
        cypher = '\n'.join(lines)

        return cypher.strip()
