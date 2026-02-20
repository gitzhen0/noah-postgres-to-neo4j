"""
Spatial Data Handler

Handles PostGIS geometry/geography data conversion to Neo4j.

Design principles (from Gemini conversation analysis):
1. Only migrate data that produces "relationship dividends"
2. ST_Touches/ST_Contains → Relationships (edges)
3. Centroids → Neo4j native Point type (essential for spatial indexing)
4. Raw WKT/GeoJSON → Optional, only when frontend map rendering is needed
5. Keep properties per node to 5-10 core attributes
6. "先 SQL 计算, 后 Graph 写入" — compute in PostGIS, store results in Neo4j
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .models import Property, PropertyType, RelationshipType, RelationshipSourceType


@dataclass
class SpatialRelationship:
    """Computed spatial relationship"""
    type: str
    from_id: str
    to_id: str
    properties: Dict[str, Any]


class SpatialDataHandler:
    """Handle PostGIS spatial data conversion to Neo4j"""

    # =====================================================
    # CORE spatial properties (always migrated)
    # These produce "relationship dividends" in Neo4j
    # =====================================================
    CORE_SPATIAL_PROPERTIES = [
        ('center_lat', 'ST_Y(ST_Centroid({geom}))', PropertyType.FLOAT),
        ('center_lon', 'ST_X(ST_Centroid({geom}))', PropertyType.FLOAT),
        ('area_km2', 'ST_Area({geom}::geography) / 1000000.0', PropertyType.FLOAT),
    ]

    # =====================================================
    # OPTIONAL spatial properties (off by default)
    # Only enable when frontend rendering or GIS tools need them
    # Gemini: "除非你要在前端绘制复杂的面/区边界多边形，
    #          否则不要把千千万万字符的 POLYGON 全部搬过去"
    # =====================================================
    OPTIONAL_SPATIAL_PROPERTIES = [
        ('geometry_wkt', 'ST_AsText({geom})', PropertyType.STRING),
        ('geometry_geojson', 'ST_AsGeoJSON({geom})', PropertyType.STRING),
        ('perimeter_km', 'ST_Perimeter({geom}::geography) / 1000.0', PropertyType.FLOAT),
        ('bbox_xmin', 'ST_XMin({geom})', PropertyType.FLOAT),
        ('bbox_ymin', 'ST_YMin({geom})', PropertyType.FLOAT),
        ('bbox_xmax', 'ST_XMax({geom})', PropertyType.FLOAT),
        ('bbox_ymax', 'ST_YMax({geom})', PropertyType.FLOAT),
    ]

    @staticmethod
    def generate_spatial_properties(
        geometry_column: str,
        table_name: str,
        include_wkt: bool = False,
        include_geojson: bool = False,
        include_metrics: bool = False,
        include_bbox: bool = False,
        target_srid: Optional[int] = None
    ) -> List[Property]:
        """
        Generate properties for spatial data extraction.

        By default, only generates CORE properties (centroid + area).
        Optional properties (WKT, GeoJSON, bbox) must be explicitly enabled.

        Args:
            geometry_column: Name of geometry/geography column
            table_name: Source table name
            include_wkt: Include WKT representation (large strings)
            include_geojson: Include GeoJSON representation (large strings)
            include_metrics: Include perimeter
            include_bbox: Include bounding box coordinates
            target_srid: If set, apply ST_Transform to this SRID before extraction

        Returns:
            List of Property objects for spatial data
        """
        properties = []

        # Apply ST_Transform if SRID conversion needed
        geom_expr = geometry_column
        if target_srid:
            geom_expr = f"ST_Transform({geometry_column}, {target_srid})"

        # Always include CORE properties
        for prop_name, transformation, prop_type in SpatialDataHandler.CORE_SPATIAL_PROPERTIES:
            sql_expr = transformation.replace('{geom}', geom_expr)
            properties.append(Property(
                name=prop_name,
                type=prop_type,
                nullable=True,
                source_column=geometry_column,
                transformation=sql_expr
            ))

        # Conditionally include OPTIONAL properties
        for prop_name, transformation, prop_type in SpatialDataHandler.OPTIONAL_SPATIAL_PROPERTIES:
            include = False
            if 'wkt' in prop_name and include_wkt:
                include = True
            elif 'geojson' in prop_name and include_geojson:
                include = True
            elif 'perimeter' in prop_name and include_metrics:
                include = True
            elif 'bbox' in prop_name and include_bbox:
                include = True

            if include:
                sql_expr = transformation.replace('{geom}', geom_expr)
                properties.append(Property(
                    name=prop_name,
                    type=prop_type,
                    nullable=True,
                    source_column=geometry_column,
                    transformation=sql_expr
                ))

        return properties

    @staticmethod
    def generate_extraction_query(
        table_name: str,
        geometry_column: str,
        id_column: str,
        include_wkt: bool = False,
        include_geojson: bool = False,
        include_metrics: bool = False,
        include_bbox: bool = False,
        target_srid: Optional[int] = None
    ) -> str:
        """
        Generate SQL query to extract spatial data.

        Args:
            table_name: Source table
            geometry_column: Geometry column name
            id_column: ID column for joining
            include_wkt: Include WKT (large strings, off by default)
            include_geojson: Include GeoJSON (large strings, off by default)
            include_metrics: Include perimeter
            include_bbox: Include bounding box
            target_srid: SRID to transform to (handles mixed SRID cases)

        Returns:
            SQL query for extraction
        """
        geom_expr = geometry_column
        if target_srid:
            geom_expr = f"ST_Transform({geometry_column}, {target_srid})"

        # Always extract core properties
        props = list(SpatialDataHandler.CORE_SPATIAL_PROPERTIES)

        # Add optional properties based on flags
        for prop_name, transformation, prop_type in SpatialDataHandler.OPTIONAL_SPATIAL_PROPERTIES:
            if 'wkt' in prop_name and include_wkt:
                props.append((prop_name, transformation, prop_type))
            elif 'geojson' in prop_name and include_geojson:
                props.append((prop_name, transformation, prop_type))
            elif 'perimeter' in prop_name and include_metrics:
                props.append((prop_name, transformation, prop_type))
            elif 'bbox' in prop_name and include_bbox:
                props.append((prop_name, transformation, prop_type))

        spatial_selects = []
        for prop_name, transformation, _ in props:
            sql_expr = transformation.replace('{geom}', geom_expr)
            spatial_selects.append(f"{sql_expr} AS {prop_name}")

        query = f"""
        SELECT
            {id_column},
            {',\n            '.join(spatial_selects)}
        FROM {table_name}
        WHERE {geometry_column} IS NOT NULL
        """

        return query.strip()

    @staticmethod
    def generate_neighbors_query(
        table_name: str,
        geometry_column: str,
        id_column: str,
        threshold_km: Optional[float] = None,
        target_srid: Optional[int] = None
    ) -> str:
        """
        Generate SQL query to compute spatial NEIGHBORS relationships.
        Uses ST_Touches for adjacency and ST_Distance for distance.

        Gemini: "(:Zipcode)-[:NEIGHBORS]->(:Zipcode)：通过运行 ST_Touches 生成，
                 这是关键的'邻区关系遍历的基础'"

        Args:
            table_name: Source table
            geometry_column: Geometry column name
            id_column: ID column
            threshold_km: Distance threshold (optional)
            target_srid: SRID to transform to before computing

        Returns:
            SQL query for computing neighbors
        """
        geom_a = f"a.{geometry_column}"
        geom_b = f"b.{geometry_column}"

        if target_srid:
            geom_a = f"ST_Transform(a.{geometry_column}, {target_srid})"
            geom_b = f"ST_Transform(b.{geometry_column}, {target_srid})"

        distance_condition = ""
        if threshold_km:
            distance_condition = f"""
            AND ST_Distance(
                ST_Centroid({geom_a}),
                ST_Centroid({geom_b})
            )::numeric / 1000.0 <= {threshold_km}
            """

        query = f"""
        SELECT
            a.{id_column} AS from_id,
            b.{id_column} AS to_id,
            ST_Distance(
                ST_Centroid({geom_a})::geography,
                ST_Centroid({geom_b})::geography
            ) / 1000.0 AS distance_km,
            ST_Touches({geom_a}, {geom_b}) AS is_adjacent
        FROM {table_name} a
        JOIN {table_name} b
            ON a.{id_column} < b.{id_column}
            AND ST_DWithin(
                {geom_a}::geography,
                {geom_b}::geography,
                {threshold_km * 1000 if threshold_km else 10000}
            )
        WHERE a.{geometry_column} IS NOT NULL
          AND b.{geometry_column} IS NOT NULL
          {distance_condition}
        ORDER BY a.{id_column}, distance_km
        """

        return query.strip()

    @staticmethod
    def generate_contains_query(
        container_table: str,
        container_geom: str,
        container_id: str,
        contained_table: str,
        contained_geom: str,
        contained_id: str,
        target_srid: Optional[int] = None
    ) -> str:
        """
        Generate SQL query to compute LOCATED_IN relationships via ST_Contains.

        Gemini: "(:Building)-[:LOCATED_IN]->(:Zipcode)：通过外键域，ST_Contains 生成"

        This validates/creates spatial containment relationships,
        complementing FK-based relationships.

        Args:
            container_table: Table with containing polygons (e.g., zipcodes)
            container_geom: Geometry column of container
            container_id: ID column of container
            contained_table: Table with contained points/polygons (e.g., buildings)
            contained_geom: Geometry column of contained
            contained_id: ID column of contained
            target_srid: SRID to transform to

        Returns:
            SQL query for computing containment
        """
        c_geom = f"c.{container_geom}"
        p_geom = f"p.{contained_geom}"

        if target_srid:
            c_geom = f"ST_Transform(c.{container_geom}, {target_srid})"
            p_geom = f"ST_Transform(p.{contained_geom}, {target_srid})"

        query = f"""
        SELECT
            p.{contained_id} AS contained_id,
            c.{container_id} AS container_id
        FROM {contained_table} p
        JOIN {container_table} c
            ON ST_Contains({c_geom}, {p_geom})
        WHERE p.{contained_geom} IS NOT NULL
          AND c.{container_geom} IS NOT NULL
        """

        return query.strip()

    @staticmethod
    def create_neighbors_relationship(
        from_label: str,
        threshold_km: Optional[float] = None
    ) -> RelationshipType:
        """Create NEIGHBORS relationship definition"""
        properties = [
            Property(
                name='distance_km',
                type=PropertyType.FLOAT,
                nullable=True,
                source_column='distance_km'
            ),
            Property(
                name='is_adjacent',
                type=PropertyType.BOOLEAN,
                nullable=True,
                source_column='is_adjacent'
            )
        ]

        return RelationshipType(
            type='NEIGHBORS',
            from_label=from_label,
            to_label=from_label,
            properties=properties,
            source_type=RelationshipSourceType.SPATIAL,
            bidirectional=True
        )

    @staticmethod
    def detect_spatial_tables(tables: Dict[str, Any]) -> List[Dict[str, str]]:
        """Detect tables with spatial columns"""
        spatial_tables = []

        for table_name, table in tables.items():
            for column in table.columns:
                if column.data_type.lower() in ['geometry', 'geography']:
                    id_column = None
                    if table.primary_key:
                        id_column = table.primary_key[0]
                    else:
                        for col in table.columns:
                            if 'id' in col.name.lower():
                                id_column = col.name
                                break

                    if id_column:
                        spatial_tables.append({
                            'table_name': table_name,
                            'geometry_column': column.name,
                            'id_column': id_column
                        })
                    break

        return spatial_tables

    @staticmethod
    def generate_neo4j_point_cypher(node_label: str) -> str:
        """
        Generate Cypher to add Neo4j native Point property to existing nodes.

        Gemini: "使用 Cypher 的 point({longitude: ..., latitude: ...})
                 函数来创建节点中的原生性，这样你才能在数据新增存真实'空间节点的'信息"

        Args:
            node_label: Node label (e.g., 'Zipcode')

        Returns:
            Cypher query to set location Point property
        """
        return f"""
MATCH (n:{node_label})
WHERE n.center_lat IS NOT NULL AND n.center_lon IS NOT NULL
SET n.location = point({{
    latitude: n.center_lat,
    longitude: n.center_lon,
    crs: 'WGS-84'
}});"""

    @staticmethod
    def generate_spatial_index_cypher(node_label: str) -> str:
        """
        Generate Cypher to create spatial index on Point property.

        Args:
            node_label: Node label

        Returns:
            Cypher CREATE INDEX statement for spatial index
        """
        return f"""CREATE POINT INDEX {node_label.lower()}_location IF NOT EXISTS
FOR (n:{node_label})
ON (n.location);"""
