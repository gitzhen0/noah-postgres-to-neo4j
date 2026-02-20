"""
Schema Context Builder

从 Neo4j 中动态提取 schema 并构建 LLM 上下文
"""

from typing import Dict, List
from ..utils.db_connection import Neo4jConnection


class SchemaContextBuilder:
    """构建 Neo4j schema 上下文，供 LLM 使用"""

    def __init__(self, neo4j_conn: Neo4jConnection):
        self.neo4j_conn = neo4j_conn
        self._schema_cache = None

    def build_context(self, include_examples: bool = True) -> str:
        """
        构建完整的 schema 上下文

        Args:
            include_examples: 是否包含示例查询

        Returns:
            Formatted schema context string
        """
        schema = self._get_schema()
        context = self._format_schema(schema)
        if include_examples:
            context += "\n\n" + self._get_example_queries()
        return context

    def _get_schema(self) -> Dict:
        """从 Neo4j 动态提取完整 schema 信息"""

        if self._schema_cache:
            return self._schema_cache

        schema = {
            'node_labels': [],
            'relationship_types': [],
            'node_properties': {},
            'relationship_patterns': [],   # [{from, type, to}]
            'relationship_properties': {}, # {rel_type: [prop_names]}
        }

        with self.neo4j_conn.driver.session() as session:
            # 节点标签
            result = session.run("CALL db.labels()")
            schema['node_labels'] = [record[0] for record in result]

            # 关系类型
            result = session.run("CALL db.relationshipTypes()")
            schema['relationship_types'] = [record[0] for record in result]

            # 每个标签的属性（取一个样本节点）
            for label in schema['node_labels']:
                result = session.run(
                    f"MATCH (n:{label}) RETURN keys(n) AS properties LIMIT 1"
                )
                record = result.single()
                if record:
                    schema['node_properties'][label] = sorted(record['properties'])

            # 关系模式：(fromLabel)-[type]->(toLabel)
            result = session.run("""
                MATCH (a)-[r]->(b)
                RETURN DISTINCT
                    labels(a)[0] AS from_label,
                    type(r)      AS rel_type,
                    labels(b)[0] AS to_label
                LIMIT 200
            """)
            schema['relationship_patterns'] = [
                {'from': r['from_label'], 'type': r['rel_type'], 'to': r['to_label']}
                for r in result
            ]

            # 每种关系的属性（取一个样本边）
            for rel_type in schema['relationship_types']:
                result = session.run(
                    f"MATCH ()-[r:{rel_type}]->() RETURN keys(r) AS properties LIMIT 1"
                )
                record = result.single()
                if record and record['properties']:
                    schema['relationship_properties'][rel_type] = sorted(record['properties'])

        self._schema_cache = schema
        return schema

    def _format_schema(self, schema: Dict) -> str:
        """格式化 schema 为 LLM 可读的文本"""

        context = "# NYC Housing Affordability Knowledge Graph – Schema\n\n"
        context += "## Node Types\n\n"

        for label in schema['node_labels']:
            context += f"### (:{label})\n"
            props = schema['node_properties'].get(label, [])
            if props:
                context += "Properties:\n"
                for prop in sorted(props):
                    context += f"  - {prop}\n"
            context += "\n"

        context += "## Relationships\n\n"

        # Group patterns by relationship type
        by_type: Dict[str, List[str]] = {}
        for pat in schema['relationship_patterns']:
            t = pat['type']
            by_type.setdefault(t, []).append(
                f"(:{pat['from']})-[:{t}]->(:{pat['to']})"
            )

        for rel_type in schema['relationship_types']:
            patterns = by_type.get(rel_type, [f"[:{rel_type}]"])
            context += f"### [:{rel_type}]\n"
            for p in patterns:
                context += f"  Pattern: {p}\n"
            props = schema['relationship_properties'].get(rel_type, [])
            if props:
                context += "  Properties:\n"
                for prop in props:
                    context += f"    - {prop}\n"
            context += "\n"

        context += """## Key Notes

- Use snake_case for all property names (e.g., zip_code, total_units, center_lat)
- ZipCode.zip_code is a 5-digit string (e.g., '10001')
- HousingProject.postcode links to ZipCode.zip_code
- HousingProject.db_id is the unique integer merge key
- AffordabilityAnalysis rates (rent_burden_rate, severe_burden_rate, rent_to_income_ratio) are decimals (e.g., 0.35 = 35%)
- RentBurden.geo_id is a Census tract GEOID string
- NEIGHBORS is undirected (use -[:NEIGHBORS]- without arrow for traversal)
- CONTAINS_TRACT has overlap_area_km2 and tract_coverage_ratio properties
"""
        return context

    def _get_example_queries(self) -> str:
        """返回示例查询（Few-shot learning for current schema）"""

        return """## Example Queries

### Example 1: Neighbors of a ZIP code
Question: "Which ZIP codes neighbor 10001?"
```cypher
MATCH (z:ZipCode {zip_code: '10001'})-[:NEIGHBORS]-(neighbor:ZipCode)
RETURN neighbor.zip_code, neighbor.borough
ORDER BY neighbor.zip_code
```

### Example 2: Housing projects in a ZIP code
Question: "Show all housing projects in ZIP code 11106"
```cypher
MATCH (p:HousingProject)-[:LOCATED_IN_ZIP]->(z:ZipCode {zip_code: '11106'})
RETURN p.project_name, p.total_units, p.borough
ORDER BY p.total_units DESC
```

### Example 3: Affordability data by borough
Question: "What are the rent burden rates in Queens ZIP codes?"
```cypher
MATCH (z:ZipCode {borough: 'Queens'})-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
RETURN z.zip_code, a.median_income_usd, a.median_rent_usd, a.rent_burden_rate
ORDER BY a.rent_burden_rate DESC
```

### Example 4: Projects in neighboring ZIP codes
Question: "Find housing projects in ZIP codes neighboring 10001"
```cypher
MATCH (start:ZipCode {zip_code: '10001'})-[:NEIGHBORS]-(neighbor:ZipCode)
MATCH (p:HousingProject)-[:LOCATED_IN_ZIP]->(neighbor)
RETURN neighbor.zip_code, count(p) AS project_count, sum(p.total_units) AS total_units
ORDER BY project_count DESC
```

### Example 5: Count projects by borough
Question: "How many housing projects are in each borough?"
```cypher
MATCH (p:HousingProject)
RETURN p.borough AS borough, count(p) AS project_count, sum(p.total_units) AS total_units
ORDER BY project_count DESC
```

### Example 6: Census tracts with high rent burden
Question: "Show census tracts with severe rent burden over 30%"
```cypher
MATCH (r:RentBurden)
WHERE r.severe_burden_rate > 0.30
RETURN r.geo_id, r.tract_name, r.severe_burden_rate, r.rent_burden_rate
ORDER BY r.severe_burden_rate DESC
LIMIT 20
```

### Example 7: ZIP codes with high burden and low income
Question: "Find ZIP codes with high rent burden and low median income"
```cypher
MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WHERE a.rent_burden_rate > 0.35 AND a.median_income_usd < 50000
RETURN z.zip_code, z.borough, a.median_income_usd, a.rent_burden_rate, a.median_rent_usd
ORDER BY a.rent_burden_rate DESC
```

### Example 8: Projects in high-burden census tracts
Question: "Find housing projects in census tracts with severe rent burden above 40%"
```cypher
MATCH (p:HousingProject)-[:IN_CENSUS_TRACT]->(r:RentBurden)
WHERE r.severe_burden_rate > 0.40
RETURN p.project_name, p.borough, p.postcode, r.geo_id, r.severe_burden_rate
ORDER BY r.severe_burden_rate DESC
LIMIT 20
```

### Example 9: Most affordable ZIP codes by rent burden
Question: "Which ZIP codes have the lowest rent burden rate?"
```cypher
MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WHERE a.rent_burden_rate IS NOT NULL
RETURN z.zip_code, z.borough, a.rent_burden_rate, a.severe_burden_rate, a.median_income_usd
ORDER BY a.rent_burden_rate ASC
LIMIT 10
```"""

    def get_schema_summary(self) -> str:
        """返回简短的 schema 摘要"""
        schema = self._get_schema()
        return (
            f"Schema: {len(schema['node_labels'])} node types "
            f"({', '.join(schema['node_labels'])}), "
            f"{len(schema['relationship_types'])} relationship types "
            f"({', '.join(schema['relationship_types'])})"
        )
