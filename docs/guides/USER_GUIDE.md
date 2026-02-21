# User Guide — NOAH Knowledge Graph Interface

This guide covers everything you need to use the NOAH Knowledge Graph web application and CLI tool.

---

## Table of Contents

1. [Starting the Application](#starting-the-application)
2. [Ask Page — Natural-Language Queries](#ask-page)
3. [Explore Page — Cypher Editor, Graph View & Saved Queries](#explore-page)
4. [Templates Page — Parameterized Queries](#templates-page)
5. [Exporting Results (CSV and GeoJSON)](#exporting-results)
6. [Understanding the Graph Model](#understanding-the-graph-model)
7. [Cypher Quick Reference](#cypher-quick-reference)
8. [Troubleshooting](#troubleshooting)

---

## Starting the Application

### Option A: Streamlit (recommended for non-technical users)

```bash
streamlit run app/Home.py --server.port 8505
```

Open http://localhost:8505 in your browser.

You will see a sidebar on the left. Enter your **Anthropic API key** in the sidebar field to enable the Ask (natural-language) page. If you don't have an API key, you can still use the Explore (Cypher editor) page.

### Option B: Docker

```bash
docker compose up -d
```

The app will be available at http://localhost:8505.

---

## Ask Page

The Ask page lets you query the housing graph in plain English.

### How to Use

1. Navigate to **Ask** in the left sidebar.
2. Click one of the **example chips** (e.g., "Most affordable neighborhoods") to pre-fill a question, or type your own question in the text box.
3. Click **Search**.
4. The system will:
   - Translate your question into a Cypher query (shown below the results)
   - Execute the query against Neo4j
   - Display the results as a table

### Example Questions

**Simple (no hops):**
- "How many housing projects are in each borough?"
- "Which ZIP codes have rent burden rate above 40%?"
- "What is the average median household income by borough?"

**One-hop (one relationship traversal):**
- "Which housing projects are in Brooklyn ZIP codes?"
- "Show census tracts with severe rent burden above 45%"

**Two-hop:**
- "What is the rent burden rate for ZIP codes where there are housing projects?"

**Spatial (neighbor queries):**
- "Find housing projects in ZIP codes neighboring ZIP code 10001"
- "Compare the rent burden of ZIP code 10451 with its neighboring ZIP codes"

### Tips

- Use borough names: **Manhattan, Brooklyn, Queens, Bronx, Staten Island**
- Rent burden is a decimal: "35%" means filtering `> 0.35` in the graph
- ZIP codes are 5-digit strings: "10001", "11201"
- If you get no results, try rephrasing or simplifying the question
- The generated Cypher is shown for transparency — you can copy it into the Explore page to modify it

---

## Explore Page

The Explore page gives you direct access to the Cypher query editor.

### How to Use

1. Navigate to **Explore** in the left sidebar.
2. Either:
   - Select a query from the **Load example** dropdown and click **Load →**, or
   - Type your own Cypher query in the editor
3. Click **Run ▶**
4. Results appear below as a table with a **Download CSV** button

### Tabs in Explore

| Tab | What it does |
|---|---|
| **Query Editor** | Write and run any Cypher query; results in table + CSV/GeoJSON download |
| **Graph View** | Visual network rendering of node-and-relationship queries (pyvis) |
| **Saved Queries** | Load or delete your saved queries |
| **Schema Reference** | Full reference of node labels, properties, relationship types, and Cypher tips |

### Graph View

Select a graph example (or write your own query that returns node and relationship variables, e.g. `RETURN p, r, z`), then click **Render Graph ▶**. Hover over nodes for property details, drag to rearrange, scroll to zoom.

### Saved Queries

In the **Query Editor** tab, give your query a name in the "Query name…" field and click **Save ★**. Saved queries appear in the **Saved Queries** tab and can be reloaded into the editor at any time.

---

## Templates Page

The **Templates** page provides 5 parameterized query templates for non-Cypher users:

| Template | Parameters |
|---|---|
| ① Rent Burden by Borough | Borough selectbox + rent burden threshold slider |
| ② Neighbor Projects | ZIP code input + 1-hop / 2-hop radio |
| ③ High-Burden Tracts | Borough + severe burden threshold slider |
| ④ Borough Comparison | Indicator dropdown (rent burden / income / severe burden) |
| ⑤ Top Projects | Borough + metric (total units, low-income units…) + Top N |

All templates display results as a table with auto bar chart and CSV download.

---

## Exporting Results

### CSV Export

Available on the Ask and Explore pages after a query runs. Click **↓ CSV** to download all result rows.

### GeoJSON Export

Available when the query result contains `center_lat` and `center_lon` columns. Click **↓ GeoJSON** to download a GeoJSON FeatureCollection compatible with:
- **QGIS** — open directly as a vector layer
- **Mapbox / Leaflet** — load via `fetch()` + `addSource()`
- **ArcGIS Online** — upload as a hosted feature layer

**Queries that produce GeoJSON-compatible results:**

```cypher
-- ZIP centroids with rent burden
MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
RETURN z.zip_code, z.center_lat, z.center_lon, z.borough,
       a.rent_burden_rate, a.median_income_usd

-- Housing project locations
MATCH (p:HousingProject)
WHERE p.center_lat IS NOT NULL
RETURN p.project_name, p.borough, p.total_units,
       p.center_lat, p.center_lon
```

---

## Understanding the Graph Model

The NOAH graph has 4 node types and 5 relationship types:

```
(HousingProject) ──[LOCATED_IN_ZIP]──────▶ (ZipCode)
(HousingProject) ──[IN_CENSUS_TRACT]─────▶ (RentBurden)
(ZipCode) ─────────[HAS_AFFORDABILITY_DATA]▶ (AffordabilityAnalysis)
(ZipCode) ─────────[NEIGHBORS]────────────  (ZipCode)   ← undirected
(ZipCode) ─────────[CONTAINS_TRACT]───────▶ (RentBurden)
```

### Node Properties

**HousingProject**
- `project_name` — building name
- `borough` — Manhattan / Brooklyn / Queens / Bronx / Staten Island
- `postcode` — 5-digit ZIP code (links to ZipCode)
- `total_units` — total residential units
- `low_income_units`, `moderate_income_units`, `middle_income_units`
- `project_start_date`, `project_completion_date`
- `center_lat`, `center_lon` — centroid coordinates
- `census_tract` — census tract number (links to RentBurden)

**ZipCode**
- `zip_code` — 5-digit string, e.g. `'10001'`
- `borough` — borough name
- `center_lat`, `center_lon`, `area_km2`

**AffordabilityAnalysis**
- `zip_code` — links to ZipCode
- `rent_burden_rate` — fraction of income spent on rent (e.g. 0.35 = 35%)
- `severe_burden_rate` — fraction spending >50% income on rent
- `median_income_usd` — median household income in USD

**RentBurden**
- `geo_id` — Census GEOID (e.g. `'36005010100'`)
- `rent_burden_rate` — tract-level rent burden
- `severe_burden_rate`
- `center_lat`, `center_lon`, `area_km2`

### Relationship Properties

**NEIGHBORS** (ZipCode ↔ ZipCode)
- `shared_boundary_km` — length of shared boundary in kilometers
- `is_touching` — boolean (true for physical adjacency)

**CONTAINS_TRACT** (ZipCode → RentBurden)
- `overlap_area_km2` — intersection area
- `tract_coverage_ratio` — fraction of tract area inside the ZIP

---

## Cypher Quick Reference

### Basic MATCH

```cypher
-- All housing projects in Manhattan
MATCH (p:HousingProject)
WHERE p.borough = 'Manhattan'
RETURN p.project_name, p.total_units
ORDER BY p.total_units DESC
LIMIT 20
```

### One-Hop Traversal

```cypher
-- Projects with their ZIP code info
MATCH (p:HousingProject)-[:LOCATED_IN_ZIP]->(z:ZipCode)
RETURN p.project_name, z.zip_code, z.borough
LIMIT 20
```

### Filter on Related Node

```cypher
-- Projects in high rent-burden areas
MATCH (p:HousingProject)-[:IN_CENSUS_TRACT]->(r:RentBurden)
WHERE r.severe_burden_rate > 0.40
RETURN p.project_name, p.borough, r.severe_burden_rate
ORDER BY r.severe_burden_rate DESC
LIMIT 20
```

### Two-Hop (Aggregation)

```cypher
-- Average rent burden by borough (via ZIP)
MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WHERE a.rent_burden_rate IS NOT NULL
RETURN z.borough,
       avg(a.rent_burden_rate) AS avg_rent_burden,
       count(z)                AS zip_count
ORDER BY avg_rent_burden DESC
```

### Neighbor Queries

```cypher
-- Projects in ZIP codes neighboring 10001
-- Note: use -[:NEIGHBORS]- without arrow (undirected)
MATCH (z:ZipCode {zip_code: '10001'})-[:NEIGHBORS]-(n:ZipCode)
      <-[:LOCATED_IN_ZIP]-(p:HousingProject)
RETURN p.project_name, p.borough, p.total_units, n.zip_code
ORDER BY p.total_units DESC
```

### Optional MATCH (left join equivalent)

```cypher
-- Neighboring ZIPs with optional affordability data
MATCH (z:ZipCode {zip_code: '10451'})-[:NEIGHBORS]-(n:ZipCode)
OPTIONAL MATCH (n)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
RETURN n.zip_code, a.rent_burden_rate, a.median_income_usd
ORDER BY a.rent_burden_rate DESC
```

### Common Gotchas

| Issue | Solution |
|---|---|
| Filter returns no results | Check decimal format: `> 0.35` not `> 35` |
| NEIGHBORS returns nothing | Omit arrow: `-[:NEIGHBORS]-` not `-[:NEIGHBORS]->` |
| Too many results | Add `LIMIT 20` |
| Postcode vs zip_code mismatch | `HousingProject.postcode` links to `ZipCode.zip_code` |

---

## Troubleshooting

### "Cannot connect to Neo4j"

1. Check that Neo4j is running: open http://localhost:7474 in your browser
2. Verify credentials in `config/config.yaml` (or `.env` file)
3. Check the Neo4j bolt port (default: 7687) is not blocked by firewall

### "API key not valid" on Ask page

1. Make sure you entered the full key starting with `sk-ant-`
2. The key is stored only in your browser session and is not saved to disk
3. Check your Anthropic account has available credits

### "No results" from a natural-language question

1. Try clicking **Run ▶** in Explore with the generated Cypher to confirm data exists
2. Check borough/ZIP spelling: use exact names (Manhattan, not NYC)
3. Try a simpler version of the question first

### Cypher syntax error in Explore

1. Check the Schema Reference tab for correct label and property names
2. Labels are case-sensitive: `HousingProject` not `housingproject`
3. Relationship types are uppercase: `LOCATED_IN_ZIP` not `located_in_zip`
4. String values need quotes: `WHERE p.borough = 'Brooklyn'`

---

*User Guide v1.0 · Spring 2026*
