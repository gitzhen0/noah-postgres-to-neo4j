"""
Text2Cypher Translator

主要的翻译器类，整合 LLM provider 和 Neo4j 执行
"""

from typing import Dict, Optional, Any
from loguru import logger

from ..utils.db_connection import Neo4jConnection
from .providers.factory import LLMProviderFactory
from .providers.base import BaseLLMProvider
from .schema_context import SchemaContextBuilder


class Text2CypherTranslator:
    """Text2Cypher 翻译器 - 支持多种 LLM"""

    def __init__(
        self,
        neo4j_conn: Neo4jConnection,
        llm_provider: str,
        api_key: str,
        model: Optional[str] = None,
        **kwargs
    ):
        """
        初始化 Text2Cypher translator

        Args:
            neo4j_conn: Neo4j database connection
            llm_provider: LLM provider name (claude, openai, gemini)
            api_key: API key for the LLM provider
            model: Model ID (optional, uses default if not specified)
            **kwargs: Additional provider-specific config
        """
        self.neo4j_conn = neo4j_conn

        # 创建 LLM provider
        self.llm_provider = LLMProviderFactory.create(
            provider_name=llm_provider,
            api_key=api_key,
            model=model,
            **kwargs
        )

        # 创建 schema context builder
        self.schema_builder = SchemaContextBuilder(neo4j_conn)

        # 获取 schema context (缓存)
        self.schema_context = self.schema_builder.build_context(include_examples=True)

        logger.info(f"Text2Cypher initialized with {llm_provider} provider")

    def query(
        self,
        question: str,
        execute: bool = True,
        explain: bool = True
    ) -> Dict[str, Any]:
        """
        执行自然语言查询

        Args:
            question: 用户的自然语言问题
            execute: 是否执行 Cypher 查询
            explain: 是否生成结果解释

        Returns:
            Dict containing:
                - question: Original question
                - cypher: Generated Cypher query
                - results: Query results (if execute=True)
                - explanation: Natural language explanation (if explain=True)
                - error: Error message (if any)
        """
        result = {
            'question': question,
            'cypher': None,
            'results': None,
            'explanation': None,
            'error': None
        }

        try:
            # Step 1: 生成 Cypher
            logger.info(f"Generating Cypher for question: {question}")
            cypher = self.llm_provider.generate_cypher(
                question=question,
                schema_context=self.schema_context
            )

            result['cypher'] = cypher
            logger.debug(f"Generated Cypher: {cypher}")

            # Step 2: 验证 Cypher
            if not self.llm_provider.validate_cypher(cypher):
                result['error'] = "Generated Cypher failed validation"
                logger.warning(f"Invalid Cypher: {cypher}")
                return result

            # Step 3: 执行 Cypher（如果需要）
            if execute:
                logger.info("Executing Cypher query...")
                query_results = self._execute_cypher(cypher)
                result['results'] = query_results
                logger.info(f"Query returned {len(query_results)} results")

                # Step 4: 生成解释（如果需要）
                if explain and query_results:
                    logger.info("Generating explanation...")
                    explanation = self.llm_provider.explain_results(
                        question=question,
                        cypher=cypher,
                        results=query_results
                    )
                    result['explanation'] = explanation

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error in Text2Cypher: {e}")

        return result

    def _execute_cypher(self, cypher: str, limit: int = 100) -> list:
        """
        执行 Cypher 查询

        Args:
            cypher: Cypher query string
            limit: Maximum number of results to return

        Returns:
            List of query results
        """
        with self.neo4j_conn.driver.session() as session:
            # 添加 LIMIT 防止返回过多结果
            if 'LIMIT' not in cypher.upper():
                cypher = cypher.rstrip(';') + f" LIMIT {limit}"

            result = session.run(cypher)

            # 转换为 list of dicts
            records = []
            for record in result:
                record_dict = dict(record)
                records.append(record_dict)

            return records

    def get_schema_summary(self) -> str:
        """获取 schema 摘要"""
        return self.schema_builder.get_schema_summary()

    def test_connection(self) -> bool:
        """测试 Neo4j 连接"""
        try:
            with self.neo4j_conn.driver.session() as session:
                result = session.run("RETURN 1 AS test")
                return result.single()['test'] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
