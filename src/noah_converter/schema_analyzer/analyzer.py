"""PostgreSQL schema analyzer"""

from typing import List, Dict, Optional
from loguru import logger

from ..utils.db_connection import PostgreSQLConnection
from ..utils.config import SchemaAnalyzerConfig
from .models import Table, Column, ForeignKey, PrimaryKey, Index, TableType


class SchemaAnalyzer:
    """
    Analyzes PostgreSQL database schema to extract table structures,
    relationships, and metadata for graph conversion
    """

    def __init__(
        self,
        pg_connection: PostgreSQLConnection,
        config: SchemaAnalyzerConfig,
    ):
        self.pg = pg_connection
        self.config = config
        self.tables: Dict[str, Table] = {}

    def analyze(self, schema: str = "public") -> Dict[str, Table]:
        """
        Perform full schema analysis

        Args:
            schema: Database schema name

        Returns:
            Dictionary of table_name -> Table objects
        """
        logger.info(f"Starting schema analysis for schema: {schema}")

        # Get all table names
        table_names = self._get_table_names(schema)
        logger.info(f"Found {len(table_names)} tables")

        # Analyze each table
        for table_name in table_names:
            if self._should_exclude_table(table_name):
                logger.debug(f"Skipping excluded table: {table_name}")
                continue

            logger.debug(f"Analyzing table: {table_name}")
            table = self._analyze_table(table_name, schema)
            self.tables[table_name] = table

        # Classify table types
        self._classify_tables()

        logger.info(f"Schema analysis complete. Analyzed {len(self.tables)} tables")
        self._log_summary()

        return self.tables

    def _get_table_names(self, schema: str) -> List[str]:
        """Get all table names in schema"""
        return self.pg.get_table_names(schema)

    def _should_exclude_table(self, table_name: str) -> bool:
        """Check if table should be excluded from analysis"""
        return table_name in self.config.exclude_tables

    def _analyze_table(self, table_name: str, schema: str) -> Table:
        """Analyze a single table"""
        table = Table(name=table_name, schema=schema)

        # Get columns
        table.columns = self._get_columns(table_name, schema)

        # Get primary key
        table.primary_key = self._get_primary_key(table_name, schema)
        self._mark_primary_key_columns(table)

        # Get foreign keys
        table.foreign_keys = self._get_foreign_keys(table_name, schema)
        self._mark_foreign_key_columns(table)

        # Get indexes
        table.indexes = self._get_indexes(table_name, schema)

        # Get row count
        table.row_count = self._get_row_count(table_name, schema)

        return table

    def _get_columns(self, table_name: str, schema: str) -> List[Column]:
        """Get column information for a table"""
        columns_data = self.pg.get_table_schema(table_name, schema)

        columns = []
        for col_data in columns_data:
            column = Column(
                name=col_data["column_name"],
                data_type=col_data["data_type"],
                is_nullable=col_data["is_nullable"] == "YES",
                default_value=col_data["column_default"],
                max_length=col_data["character_maximum_length"],
                numeric_precision=col_data["numeric_precision"],
                numeric_scale=col_data["numeric_scale"],
            )
            columns.append(column)

        return columns

    def _get_primary_key(self, table_name: str, schema: str) -> Optional[PrimaryKey]:
        """Get primary key information"""
        query = """
            SELECT
                tc.constraint_name,
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_schema = :schema
                AND tc.table_name = :table_name
            ORDER BY kcu.ordinal_position;
        """
        results = self.pg.execute_query(query, {"schema": schema, "table_name": table_name})

        if not results:
            return None

        return PrimaryKey(
            name=results[0]["constraint_name"],
            columns=[row["column_name"] for row in results],
        )

    def _get_foreign_keys(self, table_name: str, schema: str) -> List[ForeignKey]:
        """Get foreign key information"""
        query = """
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS referenced_table,
                ccu.column_name AS referenced_column,
                rc.update_rule,
                rc.delete_rule
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            JOIN information_schema.referential_constraints rc
                ON rc.constraint_name = tc.constraint_name
                AND rc.constraint_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = :schema
                AND tc.table_name = :table_name;
        """
        results = self.pg.execute_query(query, {"schema": schema, "table_name": table_name})

        foreign_keys = []
        for row in results:
            fk = ForeignKey(
                name=row["constraint_name"],
                column=row["column_name"],
                referenced_table=row["referenced_table"],
                referenced_column=row["referenced_column"],
                on_update=row["update_rule"],
                on_delete=row["delete_rule"],
            )
            foreign_keys.append(fk)

        return foreign_keys

    def _get_indexes(self, table_name: str, schema: str) -> List[Index]:
        """Get index information"""
        query = """
            SELECT
                i.relname AS index_name,
                a.attname AS column_name,
                ix.indisunique AS is_unique,
                am.amname AS index_type
            FROM pg_class t
            JOIN pg_index ix ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_am am ON i.relam = am.oid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
            JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE n.nspname = :schema
                AND t.relname = :table_name
                AND NOT ix.indisprimary;
        """
        results = self.pg.execute_query(query, {"schema": schema, "table_name": table_name})

        # Group by index name
        indexes_dict: Dict[str, Index] = {}
        for row in results:
            index_name = row["index_name"]
            if index_name not in indexes_dict:
                indexes_dict[index_name] = Index(
                    name=index_name,
                    columns=[],
                    is_unique=row["is_unique"],
                    index_type=row["index_type"],
                )
            indexes_dict[index_name].columns.append(row["column_name"])

        return list(indexes_dict.values())

    def _get_row_count(self, table_name: str, schema: str) -> Optional[int]:
        """Get approximate row count"""
        try:
            query = f'SELECT COUNT(*) as count FROM "{schema}"."{table_name}"'
            result = self.pg.execute_query(query)
            return result[0]["count"] if result else None
        except Exception as e:
            logger.warning(f"Could not get row count for {table_name}: {e}")
            return None

    def _mark_primary_key_columns(self, table: Table):
        """Mark columns that are part of primary key"""
        if not table.primary_key:
            return

        pk_columns = set(table.primary_key.columns)
        for column in table.columns:
            if column.name in pk_columns:
                column.is_primary_key = True

    def _mark_foreign_key_columns(self, table: Table):
        """Mark columns that are foreign keys"""
        fk_columns = {fk.column for fk in table.foreign_keys}
        for column in table.columns:
            if column.name in fk_columns:
                column.is_foreign_key = True

    def _classify_tables(self):
        """Classify all tables into types"""
        for table in self.tables.values():
            table.table_type = table.classify_table_type()

    def _log_summary(self):
        """Log summary statistics"""
        type_counts = {}
        for table in self.tables.values():
            table_type = table.table_type.value
            type_counts[table_type] = type_counts.get(table_type, 0) + 1

        logger.info("Table classification summary:")
        for table_type, count in type_counts.items():
            logger.info(f"  {table_type}: {count} tables")

    def export_schema(self, output_path: str):
        """Export analyzed schema to JSON"""
        import json
        from pathlib import Path

        schema_data = {
            table_name: table.to_dict()
            for table_name, table in self.tables.items()
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(schema_data, f, indent=2)

        logger.info(f"Schema exported to: {output_path}")
