"""Database connection utilities"""

from typing import Optional, Any, Dict
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from neo4j import GraphDatabase, Driver, Session
from loguru import logger

from .config import DatabaseConfig, Neo4jConfig


class PostgreSQLConnection:
    """PostgreSQL database connection manager"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._engine: Optional[Engine] = None
        self._connection = None

    @property
    def engine(self) -> Engine:
        """Get SQLAlchemy engine"""
        if self._engine is None:
            connection_string = (
                f"postgresql://{self.config.user}:{self.config.password}"
                f"@{self.config.host}:{self.config.port}/{self.config.database}"
            )
            self._engine = create_engine(connection_string, pool_pre_ping=True)
            logger.info(f"Connected to PostgreSQL: {self.config.host}:{self.config.port}/{self.config.database}")
        return self._engine

    def get_connection(self):
        """Get psycopg2 connection"""
        if self._connection is None or self._connection.closed:
            self._connection = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
            )
        return self._connection

    def execute_query(self, query: str, params: Optional[Dict] = None) -> list:
        """Execute SQL query and return results"""
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            return [dict(row._mapping) for row in result]

    def execute_raw(self, query: str, fetch: bool = True):
        """Execute raw SQL query using psycopg2"""
        conn = self.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            if fetch:
                return cursor.fetchall()
            conn.commit()
            return None

    def get_table_names(self, schema: str = "public") -> list[str]:
        """Get all table names in schema"""
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :schema
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """
        results = self.execute_query(query, {"schema": schema})
        return [row["table_name"] for row in results]

    def get_table_schema(self, table_name: str, schema: str = "public") -> list[Dict]:
        """Get column information for a table"""
        query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns
            WHERE table_schema = :schema
            AND table_name = :table_name
            ORDER BY ordinal_position;
        """
        return self.execute_query(query, {"schema": schema, "table_name": table_name})

    def close(self):
        """Close connections"""
        if self._connection and not self._connection.closed:
            self._connection.close()
        if self._engine:
            self._engine.dispose()
        logger.info("PostgreSQL connection closed")


class Neo4jConnection:
    """Neo4j database connection manager"""

    def __init__(self, config: Neo4jConfig):
        self.config = config
        self._driver: Optional[Driver] = None

    @property
    def driver(self) -> Driver:
        """Get Neo4j driver"""
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.user, self.config.password),
            )
            # Verify connectivity
            self._driver.verify_connectivity()
            logger.info(f"Connected to Neo4j: {self.config.uri}")
        return self._driver

    def execute_query(self, query: str, parameters: Optional[Dict] = None) -> list:
        """Execute Cypher query and return results"""
        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]

    def execute_write(self, query: str, parameters: Optional[Dict] = None):
        """Execute write transaction"""
        with self.driver.session(database=self.config.database) as session:
            return session.execute_write(
                lambda tx: tx.run(query, parameters or {}).consume()
            )

    def clear_database(self):
        """Clear all nodes and relationships (use with caution!)"""
        logger.warning("Clearing Neo4j database...")
        self.execute_write("MATCH (n) DETACH DELETE n")
        logger.info("Neo4j database cleared")

    def get_node_count(self) -> int:
        """Get total node count"""
        result = self.execute_query("MATCH (n) RETURN count(n) as count")
        return result[0]["count"] if result else 0

    def get_relationship_count(self) -> int:
        """Get total relationship count"""
        result = self.execute_query("MATCH ()-[r]->() RETURN count(r) as count")
        return result[0]["count"] if result else 0

    def create_constraints(self, constraints: list[str]):
        """Create constraints in Neo4j"""
        for constraint in constraints:
            try:
                self.execute_write(constraint)
                logger.info(f"Created constraint: {constraint}")
            except Exception as e:
                logger.warning(f"Constraint creation failed (may already exist): {e}")

    def create_indexes(self, indexes: list[str]):
        """Create indexes in Neo4j"""
        for index in indexes:
            try:
                self.execute_write(index)
                logger.info(f"Created index: {index}")
            except Exception as e:
                logger.warning(f"Index creation failed (may already exist): {e}")

    def close(self):
        """Close driver"""
        if self._driver:
            self._driver.close()
            logger.info("Neo4j connection closed")
