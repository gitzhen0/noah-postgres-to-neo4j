"""Configuration management"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """Database connection configuration"""
    type: str
    host: str
    port: int
    database: str
    user: str
    password: str
    schema: Optional[str] = "public"


class Neo4jConfig(BaseModel):
    """Neo4j connection configuration"""
    type: str = "neo4j"
    uri: str
    user: str
    password: str
    database: str = "neo4j"


class SchemaAnalyzerConfig(BaseModel):
    """Schema analyzer configuration"""
    detect_join_tables: bool = True
    fk_depth: int = 3
    analyze_geometry: bool = True
    exclude_tables: list[str] = Field(default_factory=list)


class MappingConfig(BaseModel):
    """Mapping engine configuration"""
    rules: Dict[str, Any] = Field(default_factory=dict)
    node_label_format: str = "PascalCase"
    relationship_type_format: str = "SCREAMING_SNAKE_CASE"
    property_format: str = "snake_case"


class MigrationConfig(BaseModel):
    """Data migration configuration"""
    batch_size: int = 1000
    parallel: bool = True
    workers: int = 4
    skip_validation: bool = False
    create_indexes: bool = True
    null_handling: str = "skip"


class ValidationConfig(BaseModel):
    """Validation configuration"""
    validate_counts: bool = True
    validate_relationships: bool = True
    sample_percentage: int = 10
    generate_report: bool = True


class Text2CypherConfig(BaseModel):
    """Text2Cypher configuration"""
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-5-20250929"
    api_key: Optional[str] = None
    temperature: float = 0.0
    max_tokens: int = 2000
    schema_aware: bool = True


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "logs/noah_converter.log"
    console: bool = True


class OutputConfig(BaseModel):
    """Output configuration"""
    cypher_dir: str = "outputs/cypher"
    reports_dir: str = "outputs/reports"
    validation_dir: str = "outputs/validation"
    export_format: str = "json"


class PerformanceConfig(BaseModel):
    """Performance configuration"""
    cache_queries: bool = True
    pool_size: int = 10
    timeout: int = 300


class Config(BaseSettings):
    """Main configuration class"""
    source_db: DatabaseConfig
    target_db: Neo4jConfig
    schema_analyzer: SchemaAnalyzerConfig = Field(default_factory=SchemaAnalyzerConfig)
    mapping: MappingConfig = Field(default_factory=MappingConfig)
    migration: MigrationConfig = Field(default_factory=MigrationConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    text2cypher: Text2CypherConfig = Field(default_factory=Text2CypherConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load configuration from YAML file

    Args:
        config_path: Path to config file. If None, looks for config/config.yaml

    Returns:
        Config object
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Please copy config/config.example.yaml to config/config.yaml and update it."
        )

    with open(config_path, "r") as f:
        config_dict = yaml.safe_load(f)

    # Resolve environment variables
    config_dict = _resolve_env_vars(config_dict)

    return Config(**config_dict)


def _resolve_env_vars(data: Any) -> Any:
    """Recursively resolve environment variables in config"""
    if isinstance(data, dict):
        return {k: _resolve_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_resolve_env_vars(item) for item in data]
    elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
        env_var = data[2:-1]
        return os.getenv(env_var, data)
    return data
