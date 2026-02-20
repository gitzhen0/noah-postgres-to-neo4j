"""
NOAH PostgreSQL to Neo4j Converter

Automated RDBMS-to-Knowledge Graph conversion tool for the NOAH database.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@nyu.edu"

from .schema_analyzer import SchemaAnalyzer
# TODO: Import when implemented in Phase 2
# from .mapping_engine import MappingEngine
# TODO: Import when implemented in Phase 3
# from .data_migrator import DataMigrator

__all__ = [
    "SchemaAnalyzer",
    # "MappingEngine",  # Phase 2
    # "DataMigrator",   # Phase 3
]
