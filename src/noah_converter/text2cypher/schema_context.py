"""
Schema Context Builder

从 Neo4j 中提取 schema 并构建 LLM 上下文
"""

from typing import Dict, List
from ..utils.db_connection import Neo4jConnection


class SchemaContextBuilder:
    """构建 Neo4j schema 上下文，供 LLM 使用"""

    def __init__(self, neo4j_conn: Neo4jConnection):
        """
        初始化 schema context builder

        Args:
            neo4j_conn: Neo4j database connection
        """
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
        # 获取 schema 信息
        schema = self._get_schema()

        # 构建上下文
        context = self._format_schema(schema)

        # 添加示例查询
        if include_examples:
            context += "\n\n" + self._get_example_queries()

        return context

    def _get_schema(self) -> Dict:
        """从 Neo4j 提取 schema 信息"""

        if self._schema_cache:
            return self._schema_cache

        schema = {
            'node_labels': [],
            'relationship_types': [],
            'properties': {}
        }

        with self.neo4j_conn.driver.session() as session:
            # 获取节点标签
            result = session.run("CALL db.labels()")
            schema['node_labels'] = [record[0] for record in result]

            # 获取关系类型
            result = session.run("CALL db.relationshipTypes()")
            schema['relationship_types'] = [record[0] for record in result]

            # 获取每个标签的属性
            for label in schema['node_labels']:
                result = session.run(
                    f"MATCH (n:{label}) "
                    "RETURN keys(n) AS properties LIMIT 1"
                )
                record = result.single()
                if record:
                    schema['properties'][label] = record['properties']

        self._schema_cache = schema
        return schema

    def _format_schema(self, schema: Dict) -> str:
        """格式化 schema 为 LLM 可读的文本"""

        context = """# NYC Housing Affordability Database Schema

## Node Types

"""

        # Format node labels with properties
        for label in schema['node_labels']:
            context += f"### (:){label}\n"
            if label in schema['properties']:
                props = schema['properties'][label]
                context += "Properties:\n"
                for prop in props:
                    context += f"  - {prop}\n"
            context += "\n"

        # Format relationships
        context += "## Relationship Types\n\n"
        for rel_type in schema['relationship_types']:
            context += f"- [:{rel_type}]\n"

        # Add specific schema details for NOAH database
        context += """
## Important Schema Details

### Zipcode Node
- zipcode: String (unique identifier, e.g., "10001")
- borough: String (Manhattan, Brooklyn, Queens, Bronx, Staten Island)
- location: Point (Neo4j Point type with latitude/longitude)
- centerLat: Float
- centerLon: Float
- geometryWKT: String (WKT format polygon)
- areaKm2: Float
- perimeterKm: Float

### HousingProject Node
- projectId: String (unique identifier)
- name: String (project name)
- borough: String
- zipcode: String
- address: String
- location: Point (Neo4j Point type)
- latitude: Float
- longitude: Float
- totalUnits: Integer
- affordableUnits: Integer
- completionDate: String

### NEIGHBORS Relationship
- Connects Zipcode nodes that are geographically adjacent or nearby
- Properties:
  - distanceKm: Float (distance between centroids in kilometers)
  - isAdjacent: Boolean (whether they physically touch)
  - sharedBoundaryKm: Float (length of shared boundary if adjacent)

### LOCATED_IN Relationship
- Connects HousingProject to Zipcode
- No properties

## Spatial Queries

You can use Neo4j's Point distance function:
```
point.distance(point1, point2)  // Returns distance in meters
```

Example:
```
MATCH (z1:Zipcode), (z2:Zipcode)
WHERE point.distance(z1.location, z2.location) < 5000  // Within 5km
RETURN z1.zipcode, z2.zipcode
```
"""

        return context

    def _get_example_queries(self) -> str:
        """返回示例查询（Few-shot learning）"""

        examples = """## Example Queries

### Example 1: Find all neighbors of a ZIP code
Question: "Which ZIP codes are neighbors of 10001?"
```cypher
MATCH (z:Zipcode {zipcode: '10001'})-[:NEIGHBORS]-(neighbor)
RETURN neighbor.zipcode, neighbor.borough
ORDER BY neighbor.zipcode
```

### Example 2: Find projects in a ZIP code
Question: "Show me all housing projects in ZIP code 11106"
```cypher
MATCH (p:HousingProject)-[:LOCATED_IN]->(z:Zipcode {zipcode: '11106'})
RETURN p.name, p.totalUnits, p.affordableUnits
ORDER BY p.totalUnits DESC
```

### Example 3: Multi-hop neighbor traversal
Question: "Find all ZIP codes within 2 hops of 10001"
```cypher
MATCH path = (start:Zipcode {zipcode: '10001'})-[:NEIGHBORS*1..2]-(end:Zipcode)
WITH DISTINCT end, min(length(path)) AS hops
RETURN end.zipcode, end.borough, hops
ORDER BY hops, end.zipcode
```

### Example 4: Spatial distance query
Question: "Find ZIP codes within 5km of 10001 using coordinates"
```cypher
MATCH (center:Zipcode {zipcode: '10001'})
MATCH (other:Zipcode)
WHERE center <> other
WITH center, other, point.distance(center.location, other.location) / 1000.0 AS distanceKm
WHERE distanceKm < 5.0
RETURN other.zipcode, distanceKm
ORDER BY distanceKm
```

### Example 5: Aggregate by borough
Question: "How many housing projects are in each borough?"
```cypher
MATCH (p:HousingProject)
RETURN p.borough AS borough,
       count(p) AS projectCount,
       sum(p.totalUnits) AS totalUnits,
       sum(p.affordableUnits) AS affordableUnits
ORDER BY projectCount DESC
```

### Example 6: Projects in neighboring ZIPs
Question: "Find housing projects in ZIP codes neighboring 10001"
```cypher
MATCH (start:Zipcode {zipcode: '10001'})-[:NEIGHBORS]-(neighbor)
MATCH (p:HousingProject)-[:LOCATED_IN]->(neighbor)
RETURN neighbor.zipcode,
       count(p) AS projectCount,
       sum(p.totalUnits) AS totalUnits
ORDER BY projectCount DESC
```
"""

        return examples

    def get_schema_summary(self) -> str:
        """返回简短的 schema 摘要"""
        schema = self._get_schema()

        summary = f"""Schema Summary:
- Node Types: {len(schema['node_labels'])} ({', '.join(schema['node_labels'])})
- Relationship Types: {len(schema['relationship_types'])} ({', '.join(schema['relationship_types'])})
"""
        return summary
