"""Data models for schema analysis"""

from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum


class ColumnType(Enum):
    """Column data types"""
    INTEGER = "integer"
    BIGINT = "bigint"
    SMALLINT = "smallint"
    NUMERIC = "numeric"
    REAL = "real"
    DOUBLE = "double precision"
    VARCHAR = "character varying"
    TEXT = "text"
    BOOLEAN = "boolean"
    DATE = "date"
    TIMESTAMP = "timestamp"
    TIMESTAMPTZ = "timestamp with time zone"
    JSON = "json"
    JSONB = "jsonb"
    UUID = "uuid"
    GEOMETRY = "geometry"
    GEOGRAPHY = "geography"
    ARRAY = "ARRAY"
    OTHER = "other"


class TableType(Enum):
    """Classification of table types for graph conversion"""
    ENTITY = "entity"          # Becomes a node type
    JUNCTION = "junction"      # Becomes a relationship
    LOOKUP = "lookup"          # Reference/enum table
    SPATIAL = "spatial"        # PostGIS system tables
    UNKNOWN = "unknown"


@dataclass
class Column:
    """Database column representation"""
    name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool = False
    is_foreign_key: bool = False
    default_value: Optional[str] = None
    max_length: Optional[int] = None
    numeric_precision: Optional[int] = None
    numeric_scale: Optional[int] = None
    is_unique: bool = False
    description: Optional[str] = None

    def is_spatial(self) -> bool:
        """Check if column is a spatial type"""
        return self.data_type.lower() in ['geometry', 'geography', 'point', 'polygon', 'linestring']

    def is_array(self) -> bool:
        """Check if column is an array type"""
        return 'ARRAY' in self.data_type or '[]' in self.data_type


@dataclass
class ForeignKey:
    """Foreign key relationship"""
    name: str
    column: str
    referenced_table: str
    referenced_column: str
    on_delete: Optional[str] = None
    on_update: Optional[str] = None


@dataclass
class Index:
    """Database index"""
    name: str
    columns: List[str]
    is_unique: bool = False
    index_type: str = "btree"


@dataclass
class PrimaryKey:
    """Primary key constraint"""
    name: str
    columns: List[str]


@dataclass
class Table:
    """Database table representation"""
    name: str
    schema: str
    columns: List[Column] = field(default_factory=list)
    primary_key: Optional[PrimaryKey] = None
    foreign_keys: List[ForeignKey] = field(default_factory=list)
    indexes: List[Index] = field(default_factory=list)
    row_count: Optional[int] = None
    table_type: TableType = TableType.UNKNOWN
    description: Optional[str] = None

    def get_column(self, name: str) -> Optional[Column]:
        """Get column by name"""
        for col in self.columns:
            if col.name == name:
                return col
        return None

    def get_primary_key_columns(self) -> List[Column]:
        """Get primary key columns"""
        if not self.primary_key:
            return []
        return [self.get_column(col) for col in self.primary_key.columns if self.get_column(col)]

    def get_foreign_key_columns(self) -> List[Column]:
        """Get foreign key columns"""
        fk_column_names = {fk.column for fk in self.foreign_keys}
        return [col for col in self.columns if col.name in fk_column_names]

    def is_junction_table(self) -> bool:
        """
        Heuristic to detect junction/join tables:
        - Has exactly 2 foreign keys
        - Primary key is composite of those 2 foreign keys
        - Has minimal additional columns (< 3)
        """
        if len(self.foreign_keys) != 2:
            return False

        if not self.primary_key or len(self.primary_key.columns) != 2:
            return False

        fk_columns = {fk.column for fk in self.foreign_keys}
        pk_columns = set(self.primary_key.columns)

        if fk_columns != pk_columns:
            return False

        # Check for minimal additional columns
        non_pk_columns = [col for col in self.columns if col.name not in pk_columns]
        return len(non_pk_columns) <= 2

    def is_lookup_table(self) -> bool:
        """
        Detect lookup/reference tables:
        - Small row count (< 1000)
        - Has 'code', 'name', 'type', 'category' columns
        - No foreign keys or only self-referencing
        """
        if self.row_count and self.row_count > 1000:
            return False

        column_names = {col.name.lower() for col in self.columns}
        lookup_indicators = {'code', 'name', 'type', 'category', 'description', 'value'}

        has_lookup_pattern = len(column_names & lookup_indicators) >= 2

        # Check if has external foreign keys
        has_external_fks = any(
            fk.referenced_table != self.name
            for fk in self.foreign_keys
        )

        return has_lookup_pattern and not has_external_fks

    def classify_table_type(self) -> TableType:
        """Classify the table type for graph conversion"""
        # Check for spatial system tables
        if self.schema in ['public', 'tiger'] and self.name in [
            'spatial_ref_sys', 'geography_columns', 'geometry_columns'
        ]:
            return TableType.SPATIAL

        # Check for junction table
        if self.is_junction_table():
            return TableType.JUNCTION

        # Check for lookup table
        if self.is_lookup_table():
            return TableType.LOOKUP

        # Default to entity table
        return TableType.ENTITY

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "schema": self.schema,
            "table_type": self.table_type.value,
            "row_count": self.row_count,
            "columns": [
                {
                    "name": col.name,
                    "data_type": col.data_type,
                    "is_nullable": col.is_nullable,
                    "is_primary_key": col.is_primary_key,
                    "is_foreign_key": col.is_foreign_key,
                }
                for col in self.columns
            ],
            "primary_key": {
                "name": self.primary_key.name,
                "columns": self.primary_key.columns,
            } if self.primary_key else None,
            "foreign_keys": [
                {
                    "name": fk.name,
                    "column": fk.column,
                    "referenced_table": fk.referenced_table,
                    "referenced_column": fk.referenced_column,
                }
                for fk in self.foreign_keys
            ],
        }
