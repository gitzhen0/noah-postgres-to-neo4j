"""
LLM-powered Schema Interpreter: PostgreSQL schema → mapping_rules.yaml

Pipeline:
  1. Serialize TableInfo objects into compact LLM-readable text
  2. Build a structured prompt asking Claude to produce a JSON mapping plan
  3. Call Claude API, extract JSON from response
  4. Validate the JSON decisions against actual column names
  5. Assemble a complete mapping_rules.yaml from the validated decisions

Usage:
    from noah_converter.schema_interpreter import SchemaInterpreter

    interpreter = SchemaInterpreter(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = interpreter.interpret(tables, user_hints="NYC housing database")
    Path("config/mapping_draft.yaml").write_text(result.mapping_yaml)
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from loguru import logger

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from noah_converter.schema_analyzer.models import Table, TableType, Column
from .models import (
    NodeDecision, RelationshipDecision, TransformationDecision,
    RelationshipPropertyDecision, SkippedTable, InterpretationResult,
)


# ─────────────────────────────────────────────────────────────
# SQL type → Neo4j YAML type mapping
# ─────────────────────────────────────────────────────────────

_SQL_TO_YAML_TYPE: Dict[str, str] = {
    "integer": "integer",
    "int": "integer",
    "int4": "integer",
    "int2": "integer",
    "int8": "integer",
    "bigint": "integer",
    "smallint": "integer",
    "serial": "integer",
    "bigserial": "integer",
    "numeric": "float",
    "decimal": "float",
    "real": "float",
    "float4": "float",
    "float8": "float",
    "double precision": "float",
    "money": "float",
    "character varying": "string",
    "varchar": "string",
    "char": "string",
    "bpchar": "string",
    "text": "string",
    "citext": "string",
    "boolean": "boolean",
    "bool": "boolean",
    "date": "date",
    "timestamp": "datetime",
    "timestamp without time zone": "datetime",
    "timestamp with time zone": "datetime",
    "timestamptz": "datetime",
    "json": "string",
    "jsonb": "string",
    "uuid": "string",
    "inet": "string",
    "cidr": "string",
    "macaddr": "string",
}

_SPATIAL_TYPES = {"geometry", "geography", "point", "polygon", "linestring", "multipolygon"}


def _normalize_type(data_type: str) -> str:
    """Normalize a PostgreSQL type string to a canonical form."""
    # Strip precision/scale: "character varying(50)" → "character varying"
    base = re.sub(r"\(.*\)", "", data_type).strip().lower()
    return _SQL_TO_YAML_TYPE.get(base, "string")


def _is_spatial(data_type: str) -> bool:
    return any(s in data_type.lower() for s in _SPATIAL_TYPES)


# ─────────────────────────────────────────────────────────────
# LLM Prompts
# ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are an expert database architect specializing in converting PostgreSQL relational \
databases to Neo4j property graph schemas.

Your job: analyze a PostgreSQL schema and output a JSON mapping plan.

## Key Concepts

**Nodes** (from ENTITY tables):
- One row → one Neo4j node.  Label: PascalCase (housing_projects → HousingProject)
- Choose a merge_key (property used for MERGE uniqueness):
    - Prefer a natural business key (zip_code, geo_id) over a serial PK
    - If serial PK (id, table_id, etc.) is the only option, rename it: {"id": "db_id"}
- include_all_columns: true → all non-spatial columns become properties
- exclude_columns: list columns that add no graph value (internal audit fields, raw FK cols if you rename them)
- rename_columns: {"old_pg_name": "new_graph_name"} — use to rename PK to db_id, fix underscores, etc.
- transformations: extra computed properties from PostGIS expressions

**PostGIS spatial columns** (geometry / geography):
- has_geometry: true, geometry_column: "geom" (or whatever the column is named)
- Always generate these transformations:
    {"name": "center_lat", "source_column": "<geom_col>", "transformation": "ST_Y(ST_Centroid(<geom_col>))", "neo4j_type": "float"}
    {"name": "center_lon", "source_column": "<geom_col>", "transformation": "ST_X(ST_Centroid(<geom_col>))", "neo4j_type": "float"}
    {"name": "area_km2",   "source_column": "<geom_col>", "transformation": "ST_Area(<geom_col>::geography) / 1000000.0", "neo4j_type": "float"}

**Relationships** (from FKs and logical connections):
- Name using verb phrases (SCREAMING_SNAKE_CASE): LOCATED_IN, IN_CENSUS_TRACT, HAS_DATA, WORKS_ON
- For foreign_key type: provide source_table + from_id_column + to_id_column
    - from_id_column: column in source_table whose value equals from_label's merge_key
    - to_id_column:   column in source_table whose value equals to_label's merge_key
    Example: HousingProject→ZipCode via housing_projects.postcode → zip_shapes.zip_code
        source_table=housing_projects, from_id_column="id", to_id_column="postcode"
        (id maps to HousingProject's merge_key db_id; postcode matches ZipCode's zip_code)
- For computed/spatial type: provide computation_query returning from_id, to_id columns
    Example for self-referencing spatial adjacency:
        SELECT a.zip_code AS from_id, b.zip_code AS to_id,
               ST_Distance(...) / 1000.0 AS distance_km,
               ST_Touches(a.geom, b.geom) AS is_adjacent
        FROM zip_shapes a JOIN zip_shapes b
            ON a.zip_code < b.zip_code AND (ST_Touches(a.geom,b.geom) OR ST_Intersects(a.geom,b.geom))

**Skip** these:
- PostGIS system tables: spatial_ref_sys, geography_columns, geometry_columns
- Pure config / internal tables with no business value

Output ONLY valid JSON (no markdown, no explanation outside JSON).\
"""

_USER_PROMPT_TEMPLATE = """\
## PostgreSQL Schema to Convert

{schema_text}

{hints_section}

## Required JSON Output

Return a single JSON object with this exact structure:

{{
  "nodes": [
    {{
      "label": "PascalCase",
      "source_table": "exact_pg_table_name",
      "confidence": "high|medium|low",
      "reasoning": "brief explanation",
      "merge_keys": ["graph_property_name"],
      "has_geometry": false,
      "geometry_column": null,
      "include_all_columns": true,
      "exclude_columns": [],
      "rename_columns": {{}},
      "transformations": [],
      "indexes": []
    }}
  ],
  "relationships": [
    {{
      "type": "RELATIONSHIP_TYPE",
      "from_label": "NodeLabel",
      "to_label": "NodeLabel",
      "source_type": "foreign_key|computed|spatial",
      "confidence": "high|medium|low",
      "reasoning": "brief explanation",
      "bidirectional": false,
      "source_table": null,
      "from_id_column": null,
      "to_id_column": null,
      "computation_query": null,
      "properties": []
    }}
  ],
  "skipped_tables": [
    {{"table": "table_name", "reason": "why skipped"}}
  ]
}}\
"""


# ─────────────────────────────────────────────────────────────
# Schema Serializer  (Table objects → compact text)
# ─────────────────────────────────────────────────────────────

def _serialize_tables(tables: Dict[str, Table]) -> str:
    """Convert TableInfo objects to a compact, LLM-readable text block."""
    lines: List[str] = []

    for name, table in sorted(tables.items()):
        row_str = f"{table.row_count:,}" if table.row_count else "?"
        lines.append(
            f"TABLE: {name}  [{table.table_type.value.upper()}, {row_str} rows]"
        )

        # Columns
        for col in table.columns:
            flags: List[str] = []
            if col.is_primary_key:  flags.append("PK")
            if col.is_foreign_key:  flags.append("FK")
            if not col.is_nullable: flags.append("NOT NULL")
            if col.is_unique:       flags.append("UNIQUE")
            if _is_spatial(col.data_type): flags.append("SPATIAL")

            # Normalize type for display
            dtype = re.sub(r"\(.*\)", "", col.data_type).strip()
            flag_str = "  ".join(flags)
            lines.append(f"    {col.name:<35} {dtype:<30} {flag_str}")

        # FK references
        if table.foreign_keys:
            lines.append("  Foreign Keys:")
            for fk in table.foreign_keys:
                lines.append(
                    f"    {fk.column} → {fk.referenced_table}.{fk.referenced_column}"
                )

        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# YAML Assembler  (decisions + tables → mapping_rules.yaml)
# ─────────────────────────────────────────────────────────────

def _assemble_yaml(
    nodes: List[NodeDecision],
    relationships: List[RelationshipDecision],
    tables: Dict[str, Table],
    metadata: Optional[Dict[str, str]] = None,
) -> str:
    """Build a complete mapping_rules.yaml string from LLM decisions."""

    doc: Dict[str, Any] = {}

    # Metadata
    doc["metadata"] = {
        "version": "2.0",
        "description": "Auto-generated by SchemaInterpreter",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        **(metadata or {}),
    }

    # Spatial config (sensible defaults)
    doc["spatial"] = {
        "preserve_wkt": False,
        "preserve_geojson": False,
        "compute_centroids": True,
        "compute_metrics": False,
        "compute_bbox": False,
        "use_neo4j_point": True,
        "neighbors_threshold_km": 5.0,
    }

    # Nodes
    doc["nodes"] = []
    for nd in nodes:
        table = tables.get(nd.source_table)
        if table is None:
            continue
        doc["nodes"].append(_build_node_yaml(nd, table))

    # Relationships
    doc["relationships"] = []
    for rd in relationships:
        doc["relationships"].append(_build_rel_yaml(rd))

    return yaml.dump(doc, default_flow_style=False, allow_unicode=True, sort_keys=False)


def _build_node_yaml(nd: NodeDecision, table: Table) -> Dict[str, Any]:
    """Build the YAML dict for one node type."""

    # --- Property list ---
    props: List[Dict[str, Any]] = []

    # Determine which columns to include
    if nd.include_all_columns:
        include_cols = [
            col for col in table.columns
            if col.name not in nd.exclude_columns
            and not _is_spatial(col.data_type)
        ]
    else:
        include_cols = []

    # Build graph_name → pg_col mapping (apply renames)
    reverse_rename = {v: k for k, v in nd.rename_columns.items()}  # graph_name → pg_col

    # Columns already accounted for by renames
    renamed_pg_cols = set(nd.rename_columns.keys())

    # 1. Renamed columns first (so merge_keys appear first)
    for pg_col, graph_name in nd.rename_columns.items():
        col = table.get_column(pg_col)
        if col is None:
            continue
        props.append({
            "name": graph_name,
            "type": _normalize_type(col.data_type),
            "nullable": col.is_nullable,
            "source_column": pg_col,
            "source_type": re.sub(r"\(.*\)", "", col.data_type).strip(),
        })

    # 2. Regular columns (not renamed, not spatial)
    for col in include_cols:
        if col.name in renamed_pg_cols:
            continue   # already added above
        props.append({
            "name": col.name,
            "type": _normalize_type(col.data_type),
            "nullable": col.is_nullable,
            "source_column": col.name,
            "source_type": re.sub(r"\(.*\)", "", col.data_type).strip(),
        })

    # 3. Transformations (computed / spatial)
    for tr in nd.transformations:
        props.append({
            "name": tr.name,
            "type": tr.neo4j_type,
            "nullable": True,
            "source_column": tr.source_column,
            "transformation": tr.transformation,
        })

    node_yaml: Dict[str, Any] = {
        "label": nd.label,
        "source_table": nd.source_table,
        "primary_property": nd.merge_keys[0] if nd.merge_keys else "id",
        "has_geometry": nd.has_geometry,
        "merge_keys": nd.merge_keys,
        "indexes": nd.indexes,
        "properties": props,
    }
    if nd.has_geometry and nd.geometry_column:
        node_yaml["geometry_column"] = nd.geometry_column

    return node_yaml


def _build_rel_yaml(rd: RelationshipDecision) -> Dict[str, Any]:
    """Build the YAML dict for one relationship type."""
    rel_yaml: Dict[str, Any] = {
        "type": rd.type,
        "from_label": rd.from_label,
        "to_label": rd.to_label,
        "source_type": rd.source_type,
        "bidirectional": rd.bidirectional,
    }

    if rd.source_type == "foreign_key":
        rel_yaml["source_table"] = rd.source_table
        rel_yaml["from_column"] = rd.to_id_column   # kept for mapping engine compat
        rel_yaml["to_column"] = rd.to_id_column
        rel_yaml["from_id_column"] = rd.from_id_column
        rel_yaml["to_id_column"] = rd.to_id_column
    elif rd.computation_query:
        rel_yaml["computation_query"] = rd.computation_query

    if rd.properties:
        rel_yaml["properties"] = [
            {
                "name": p.name,
                "type": p.neo4j_type,
                "nullable": True,
                "source_column": p.name,
            }
            for p in rd.properties
        ]
    else:
        rel_yaml["properties"] = []

    return rel_yaml


# ─────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────

def _validate_decisions(
    nodes: List[NodeDecision],
    relationships: List[RelationshipDecision],
    tables: Dict[str, Table],
) -> List[str]:
    """Check LLM decisions against actual schema. Returns warning strings."""
    warnings: List[str] = []
    node_labels = {nd.label for nd in nodes}

    for nd in nodes:
        table = tables.get(nd.source_table)
        if table is None:
            warnings.append(
                f"[Node {nd.label}] source_table '{nd.source_table}' not found in schema"
            )
            continue

        col_names = {col.name for col in table.columns}

        # Check merge_keys exist in actual PG table
        for mk in nd.merge_keys:
            # merge_key is a *graph* property name; find its source PG column.
            # It may be a rename target: rename_columns = {"id": "db_id"} → "db_id"→"id"
            reverse_lookup = {v: k for k, v in nd.rename_columns.items()}
            source_col = reverse_lookup.get(mk, mk)   # graph_name → pg_col (or same if not renamed)
            if source_col not in col_names:
                warnings.append(
                    f"[Node {nd.label}] merge_key '{mk}' source column '{source_col}' "
                    f"not found in {nd.source_table}"
                )

        # Check rename_columns source cols exist
        for pg_col in nd.rename_columns:
            if pg_col not in col_names:
                warnings.append(
                    f"[Node {nd.label}] rename_columns key '{pg_col}' "
                    f"not found in {nd.source_table}"
                )

        # Check exclude_columns exist
        for ex_col in nd.exclude_columns:
            if ex_col not in col_names:
                warnings.append(
                    f"[Node {nd.label}] exclude_columns '{ex_col}' "
                    f"not found in {nd.source_table} (harmless)"
                )

    for rd in relationships:
        # Check referenced labels exist
        if rd.from_label not in node_labels:
            warnings.append(
                f"[Rel {rd.type}] from_label '{rd.from_label}' not in node list"
            )
        if rd.to_label not in node_labels:
            warnings.append(
                f"[Rel {rd.type}] to_label '{rd.to_label}' not in node list"
            )

        if rd.source_type == "foreign_key":
            table = tables.get(rd.source_table or "")
            if table is None:
                warnings.append(
                    f"[Rel {rd.type}] source_table '{rd.source_table}' not found"
                )
                continue
            col_names = {col.name for col in table.columns}

            for col_field, col_val in [
                ("from_id_column", rd.from_id_column),
                ("to_id_column", rd.to_id_column),
            ]:
                if col_val and col_val not in col_names:
                    warnings.append(
                        f"[Rel {rd.type}] {col_field} '{col_val}' "
                        f"not found in {rd.source_table}"
                    )

    return warnings


# ─────────────────────────────────────────────────────────────
# JSON Parser
# ─────────────────────────────────────────────────────────────

def _extract_json(text: str) -> str:
    """Extract JSON object from LLM response, stripping markdown if present."""
    # Try to find ```json ... ``` block
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return match.group(1).strip()
    # Otherwise assume the whole response is JSON
    return text.strip()


def _parse_llm_response(raw: str) -> Tuple[
    List[NodeDecision], List[RelationshipDecision], List[SkippedTable]
]:
    """Parse LLM JSON response into decision objects."""
    json_str = _extract_json(raw)
    data = json.loads(json_str)

    nodes: List[NodeDecision] = []
    for n in data.get("nodes", []):
        transformations = [
            TransformationDecision(
                name=t["name"],
                source_column=t["source_column"],
                transformation=t["transformation"],
                neo4j_type=t.get("neo4j_type", "float"),
            )
            for t in n.get("transformations", [])
        ]
        nodes.append(NodeDecision(
            label=n["label"],
            source_table=n["source_table"],
            confidence=n.get("confidence", "medium"),
            reasoning=n.get("reasoning", ""),
            merge_keys=n.get("merge_keys", []),
            has_geometry=n.get("has_geometry", False),
            geometry_column=n.get("geometry_column"),
            include_all_columns=n.get("include_all_columns", True),
            exclude_columns=n.get("exclude_columns", []),
            rename_columns=n.get("rename_columns", {}),
            transformations=transformations,
            indexes=n.get("indexes", []),
        ))

    relationships: List[RelationshipDecision] = []
    for r in data.get("relationships", []):
        properties = [
            RelationshipPropertyDecision(
                name=p["name"],
                neo4j_type=p.get("neo4j_type", "float"),
            )
            for p in r.get("properties", [])
        ]
        relationships.append(RelationshipDecision(
            type=r["type"],
            from_label=r["from_label"],
            to_label=r["to_label"],
            source_type=r.get("source_type", "foreign_key"),
            confidence=r.get("confidence", "medium"),
            reasoning=r.get("reasoning", ""),
            bidirectional=r.get("bidirectional", False),
            properties=properties,
            source_table=r.get("source_table"),
            from_id_column=r.get("from_id_column"),
            to_id_column=r.get("to_id_column"),
            computation_query=r.get("computation_query"),
        ))

    skipped: List[SkippedTable] = [
        SkippedTable(table=s["table"], reason=s.get("reason", ""))
        for s in data.get("skipped_tables", [])
    ]

    return nodes, relationships, skipped


# ─────────────────────────────────────────────────────────────
# Main Class
# ─────────────────────────────────────────────────────────────

class SchemaInterpreter:
    """
    Uses Claude to convert a PostgreSQL schema into a draft mapping_rules.yaml.

    Args:
        api_key:    Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
        model:      Claude model ID (default: claude-sonnet-4-6).
        max_tokens: Max tokens for LLM response (default: 4096).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 4096,
    ):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package not installed. Run: pip install anthropic"
            )
        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not resolved_key:
            raise ValueError(
                "Anthropic API key required. Pass api_key= or set ANTHROPIC_API_KEY."
            )
        self.client = Anthropic(api_key=resolved_key)
        self.model = model
        self.max_tokens = max_tokens

    def interpret(
        self,
        tables: Dict[str, Table],
        user_hints: str = "",
        metadata: Optional[Dict[str, str]] = None,
    ) -> InterpretationResult:
        """
        Analyze a PostgreSQL schema and produce a draft mapping_rules.yaml.

        Args:
            tables:      Dict of table_name → Table from SchemaAnalyzer.analyze()
            user_hints:  Optional free-text context about the database domain,
                         e.g. "NYC housing database with PostGIS geometry columns"
            metadata:    Optional metadata to embed in the YAML header

        Returns:
            InterpretationResult with mapping_yaml ready to write to a file
        """
        logger.info(
            f"SchemaInterpreter: analyzing {len(tables)} tables with {self.model}"
        )

        # Step 1: Serialize schema
        schema_text = _serialize_tables(tables)

        # Step 2: Build prompt
        prompt = self._build_prompt(schema_text, user_hints)

        # Step 3: Call LLM (with one retry on parse failure)
        raw_response = self._call_llm(prompt)

        # Step 4: Parse JSON → decision objects
        try:
            nodes, relationships, skipped = _parse_llm_response(raw_response)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse LLM response: {e}. Retrying...")
            retry_prompt = (
                "Your previous response could not be parsed as valid JSON. "
                "Return ONLY a valid JSON object with no markdown, no text before or after. "
                f"Original task:\n\n{prompt}"
            )
            raw_response = self._call_llm(retry_prompt)
            nodes, relationships, skipped = _parse_llm_response(raw_response)

        logger.info(
            f"LLM produced: {len(nodes)} nodes, {len(relationships)} relationships, "
            f"{len(skipped)} skipped tables"
        )

        # Step 5: Validate
        warnings = _validate_decisions(nodes, relationships, tables)
        if warnings:
            for w in warnings:
                logger.warning(f"Validation: {w}")

        # Step 6: Assemble YAML
        mapping_yaml = _assemble_yaml(nodes, relationships, tables, metadata)

        return InterpretationResult(
            nodes=nodes,
            relationships=relationships,
            skipped_tables=skipped,
            validation_warnings=warnings,
            mapping_yaml=mapping_yaml,
            raw_llm_response=raw_response,
        )

    def _build_prompt(self, schema_text: str, user_hints: str) -> str:
        hints_section = (
            f"## User Context\n{user_hints}\n"
            if user_hints.strip()
            else ""
        )
        return _USER_PROMPT_TEMPLATE.format(
            schema_text=schema_text,
            hints_section=hints_section,
        )

    def _call_llm(self, prompt: str) -> str:
        """Call Claude API and return raw text response."""
        logger.debug(f"Calling {self.model} (max_tokens={self.max_tokens})...")
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=0,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
