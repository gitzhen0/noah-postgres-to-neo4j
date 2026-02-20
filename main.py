#!/usr/bin/env python3
"""
NOAH PostgreSQL to Neo4j Converter - Main Entry Point

This is the main CLI interface for the NOAH database conversion tool.
"""

import sys
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table as RichTable

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from noah_converter.utils.config import load_config
from noah_converter.utils.logger import setup_logger
from noah_converter.utils.db_connection import PostgreSQLConnection, Neo4jConnection
from noah_converter.schema_analyzer import SchemaAnalyzer
from noah_converter.mapping_engine import MappingEngine, CypherDDLGenerator, SpatialConfig

console = Console()


@click.group()
@click.option("--config", type=click.Path(exists=True), help="Path to config file")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx, config, verbose):
    """NOAH PostgreSQL to Neo4j Converter CLI"""
    ctx.ensure_object(dict)

    # Load configuration
    config_path = Path(config) if config else None
    ctx.obj["config"] = load_config(config_path)

    # Setup logging
    log_level = "DEBUG" if verbose else ctx.obj["config"].logging.level
    setup_logger(
        log_file=ctx.obj["config"].logging.file,
        level=log_level,
        console=ctx.obj["config"].logging.console,
    )


@cli.command()
@click.option("--schema", default="public", help="PostgreSQL schema to analyze")
@click.option("--export", type=click.Path(), help="Export schema to JSON file")
@click.pass_context
def analyze(ctx, schema, export):
    """Analyze PostgreSQL database schema"""
    config = ctx.obj["config"]

    console.print("[bold blue]Starting schema analysis...[/bold blue]")

    # Connect to PostgreSQL
    pg_conn = PostgreSQLConnection(config.source_db)

    # Create analyzer
    analyzer = SchemaAnalyzer(pg_conn, config.schema_analyzer)

    # Analyze schema
    tables = analyzer.analyze(schema)

    # Display results
    _display_schema_summary(tables)

    # Export if requested
    if export:
        analyzer.export_schema(export)
        console.print(f"[green]✓[/green] Schema exported to: {export}")

    pg_conn.close()


@cli.command()
@click.option("--schema", default="public", help="PostgreSQL schema to analyze")
@click.option("--config-file", type=click.Path(), help="YAML config file (optional, auto-generates if not provided)")
@click.option("--output-dir", default="outputs/cypher", help="Output directory for generated files")
@click.pass_context
def generate_mapping(ctx, schema, config_file, output_dir):
    """Generate RDBMS to graph mapping"""
    config = ctx.obj["config"]

    console.print("[bold blue]🗺️  Generating Graph Mapping...[/bold blue]\n")

    # Step 1: Analyze PostgreSQL schema
    console.print("[cyan]Step 1:[/cyan] Analyzing PostgreSQL schema...")
    pg_conn = PostgreSQLConnection(config.source_db)
    analyzer = SchemaAnalyzer(pg_conn, config.schema_analyzer)
    tables = analyzer.analyze(schema)
    console.print(f"[green]✓[/green] Found {len(tables)} tables\n")

    # Step 2: Generate graph schema
    console.print("[cyan]Step 2:[/cyan] Generating graph schema...")

    # PostGIS 100% 零损耗迁移：所有空间数据全部保留
    spatial_config = SpatialConfig(
        compute_centroids=True,
        compute_area=True,
        use_neo4j_point=True,
        preserve_wkt=True,
        preserve_geojson=True,
        compute_metrics=True,
        compute_bbox=True,
        neighbors_threshold_km=5.0
    )

    mapper = MappingEngine(
        tables=tables,
        spatial_config=spatial_config,
        config_file=config_file
    )

    graph_schema = mapper.generate_graph_schema()

    # Display summary
    summary = mapper.get_summary()
    console.print(f"[green]✓[/green] Generated graph schema:")
    console.print(f"  • Nodes: {summary['total_nodes']}")
    console.print(f"  • Relationships: {summary['total_relationships']}")
    console.print(f"  • Properties: {summary['total_properties']}")
    console.print(f"  • Spatial nodes: {summary['spatial_nodes']}")
    console.print(f"  • Spatial relationships: {summary['spatial_relationships']}\n")

    # Step 3: Export files
    console.print("[cyan]Step 3:[/cyan] Exporting schema files...")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Export JSON schema
    json_file = output_path / "graph_schema.json"
    mapper.export_schema(str(json_file))

    # Export YAML config
    yaml_file = output_path / "mapping_config.yaml"
    mapper.export_yaml_config(str(yaml_file))

    # Export Cypher DDL
    constraints_file = output_path / "01_create_constraints.cypher"
    CypherDDLGenerator.export_constraints_script(graph_schema, str(constraints_file))

    indexes_file = output_path / "02_create_indexes.cypher"
    CypherDDLGenerator.export_indexes_script(graph_schema, str(indexes_file))

    # Export post-migration script (Neo4j Point + spatial indexes)
    post_migration_file = output_path / "03_post_migration_spatial.cypher"
    CypherDDLGenerator.export_post_migration_script(graph_schema, str(post_migration_file))

    console.print(f"\n[green]✅ Mapping generation complete![/green]")
    console.print(f"[dim]Output directory: {output_dir}[/dim]")

    # Display node labels
    console.print("\n[bold]Generated Node Labels:[/bold]")
    for label in summary['node_labels']:
        console.print(f"  • {label}")

    pg_conn.close()


@cli.command()
@click.option("--schema", default="public", help="PostgreSQL schema to analyze")
@click.option("--hints", default="", help="Free-text context about the database domain")
@click.option(
    "--output",
    default="outputs/mapping_draft.yaml",
    type=click.Path(),
    help="Output path for the draft mapping YAML",
)
@click.option(
    "--save-raw",
    is_flag=True,
    help="Also save the raw LLM JSON response alongside the YAML",
)
@click.pass_context
def interpret(ctx, schema, hints, output, save_raw):
    """[Stage 2] Use LLM to analyze PostgreSQL schema and generate draft mapping_rules.yaml"""
    import os
    from rich.panel import Panel
    from rich.text import Text
    from noah_converter.schema_interpreter import SchemaInterpreter

    config = ctx.obj["config"]

    # Step 1: Analyze schema
    console.print("\n[bold blue]Stage 2: LLM Schema Interpreter[/bold blue]\n")
    console.print("[cyan]Step 1:[/cyan] Analyzing PostgreSQL schema...")

    pg_conn = PostgreSQLConnection(config.source_db)
    from noah_converter.utils.config import SchemaAnalyzerConfig
    analyzer = SchemaAnalyzer(pg_conn, config.schema_analyzer)
    tables = analyzer.analyze(schema)
    console.print(f"[green]✓[/green] Found {len(tables)} tables\n")

    # Step 2: Call LLM
    api_key = config.text2cypher.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or api_key.startswith("${"):
        console.print(
            "[red]✗[/red] ANTHROPIC_API_KEY not set. "
            "Export it or add to config.yaml under text2cypher.api_key"
        )
        return

    console.print(f"[cyan]Step 2:[/cyan] Calling LLM ({config.text2cypher.model})...")
    interpreter = SchemaInterpreter(
        api_key=api_key,
        model=config.text2cypher.model,
        max_tokens=6000,
    )
    result = interpreter.interpret(
        tables=tables,
        user_hints=hints,
        metadata={"database": config.source_db.database},
    )
    console.print(
        f"[green]✓[/green] LLM produced "
        f"{len(result.nodes)} nodes, "
        f"{len(result.relationships)} relationships, "
        f"{len(result.skipped_tables)} skipped tables\n"
    )

    # Step 3: Show summary with confidence levels
    _display_interpretation_summary(result)

    # Step 4: Validation warnings
    if result.validation_warnings:
        console.print("\n[bold yellow]⚠ Validation Warnings:[/bold yellow]")
        for w in result.validation_warnings:
            console.print(f"  [yellow]•[/yellow] {w}")

    # Step 5: Save output
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.mapping_yaml)
    console.print(f"\n[green]✅ Draft mapping saved:[/green] {output_path}")

    if save_raw:
        raw_path = output_path.with_suffix(".llm_response.json")
        raw_path.write_text(result.raw_llm_response)
        console.print(f"[dim]Raw LLM response: {raw_path}[/dim]")

    console.print(
        "\n[dim]Review the draft, then copy to config/mapping_rules.yaml "
        "and run: python main.py migrate[/dim]"
    )

    pg_conn.close()


def _display_interpretation_summary(result):
    """Display a confidence-colored summary of LLM decisions."""
    from rich.table import Table as RichTable

    CONF_COLOR = {"high": "green", "medium": "yellow", "low": "red"}

    # Nodes table
    node_table = RichTable(title="Proposed Node Types", show_header=True, header_style="bold")
    node_table.add_column("Label", style="cyan")
    node_table.add_column("Source Table", style="dim")
    node_table.add_column("Merge Key(s)", style="magenta")
    node_table.add_column("Confidence")
    node_table.add_column("Reasoning", max_width=50)

    for nd in result.nodes:
        color = CONF_COLOR.get(nd.confidence, "white")
        node_table.add_row(
            nd.label,
            nd.source_table,
            ", ".join(nd.merge_keys),
            f"[{color}]{nd.confidence}[/{color}]",
            nd.reasoning,
        )
    console.print(node_table)
    console.print()

    # Relationships table
    rel_table = RichTable(title="Proposed Relationships", show_header=True, header_style="bold")
    rel_table.add_column("Type", style="cyan")
    rel_table.add_column("From → To", style="dim")
    rel_table.add_column("Source", style="dim")
    rel_table.add_column("Confidence")
    rel_table.add_column("Reasoning", max_width=45)

    for rd in result.relationships:
        color = CONF_COLOR.get(rd.confidence, "white")
        rel_table.add_row(
            rd.type,
            f"{rd.from_label} → {rd.to_label}",
            rd.source_type,
            f"[{color}]{rd.confidence}[/{color}]",
            rd.reasoning,
        )
    console.print(rel_table)
    console.print()

    # Skipped tables
    if result.skipped_tables:
        console.print("[dim]Skipped tables:[/dim]")
        for s in result.skipped_tables:
            console.print(f"  [dim]• {s.table}: {s.reason}[/dim]")


@cli.command()
@click.option("--clear", is_flag=True, help="Clear Neo4j before migrating")
@click.option(
    "--mapping-rules",
    default="config/mapping_rules.yaml",
    type=click.Path(),
    help="Path to mapping_rules.yaml (default: config/mapping_rules.yaml)",
)
@click.pass_context
def migrate(ctx, clear, mapping_rules):
    """Migrate data from PostgreSQL to Neo4j (config-driven via mapping_rules.yaml)"""
    from noah_converter.data_migrator import GenericMigrator
    from noah_converter.mapping_engine.config import MappingConfigLoader

    config = ctx.obj["config"]

    if clear:
        console.print("[bold red]Warning: Neo4j will be cleared before migration[/bold red]")

    # Load graph schema from YAML
    rules_path = Path(mapping_rules)
    if not rules_path.exists():
        console.print(f"[red]✗[/red] Mapping rules not found: {rules_path}")
        return

    console.print(f"[bold blue]Starting NOAH data migration...[/bold blue]")
    console.print(f"[dim]Mapping rules: {rules_path}[/dim]")

    schema = MappingConfigLoader.load_graph_schema(str(rules_path))
    console.print(
        f"[green]✓[/green] Loaded schema: "
        f"{len(schema.nodes)} node types, {len(schema.relationships)} relationship types"
    )

    # Build connection params from config
    pg_dsn = {
        "host": config.source_db.host,
        "port": config.source_db.port,
        "dbname": config.source_db.database,
        "user": config.source_db.user,
        "password": config.source_db.password,
    }
    neo4j_uri = config.target_db.uri
    neo4j_auth = (config.target_db.user, config.target_db.password)

    migrator = GenericMigrator(
        pg_dsn=pg_dsn,
        neo4j_uri=neo4j_uri,
        neo4j_auth=neo4j_auth,
        schema=schema,
        batch_size=config.migration.batch_size,
    )
    result = migrator.migrate_all(clear=clear)
    migrator.close()

    total_nodes = sum(result["nodes"].values())
    total_rels  = sum(result["relationships"].values())
    console.print(f"\n[green]✅ Migration complete![/green]")
    console.print(f"   Nodes created:         [bold]{total_nodes:,}[/bold]")
    console.print(f"   Relationships created: [bold]{total_rels:,}[/bold]")


@cli.command()
@click.pass_context
def validate(ctx):
    """Validate migrated data"""
    console.print("[bold yellow]Validation not yet implemented[/bold yellow]")


@cli.command()
@click.pass_context
def status(ctx):
    """Show connection status and database info"""
    config = ctx.obj["config"]

    console.print("[bold blue]Database Connection Status[/bold blue]\n")

    # Test PostgreSQL connection
    try:
        pg_conn = PostgreSQLConnection(config.source_db)
        tables = pg_conn.get_table_names()
        console.print(f"[green]✓[/green] PostgreSQL: Connected ({len(tables)} tables)")
        pg_conn.close()
    except Exception as e:
        console.print(f"[red]✗[/red] PostgreSQL: Connection failed - {e}")

    # Test Neo4j connection
    try:
        neo4j_conn = Neo4jConnection(config.target_db)
        node_count = neo4j_conn.get_node_count()
        rel_count = neo4j_conn.get_relationship_count()
        console.print(f"[green]✓[/green] Neo4j: Connected ({node_count} nodes, {rel_count} relationships)")
        neo4j_conn.close()
    except Exception as e:
        console.print(f"[red]✗[/red] Neo4j: Connection failed - {e}")


def _display_schema_summary(tables: dict):
    """Display schema analysis summary"""
    table = RichTable(title="Schema Analysis Summary")
    table.add_column("Table Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Columns", justify="right", style="green")
    table.add_column("Rows", justify="right", style="yellow")
    table.add_column("FKs", justify="right", style="blue")

    for table_name, table_obj in tables.items():
        table.add_row(
            table_name,
            table_obj.table_type.value,
            str(len(table_obj.columns)),
            str(table_obj.row_count or "N/A"),
            str(len(table_obj.foreign_keys)),
        )

    console.print(table)


if __name__ == "__main__":
    cli(obj={})
