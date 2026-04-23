"""
PostgreSQL (JOIN) vs Neo4j (graph-traversal) Performance Comparison.

Measures:
  - Execution time  : median over N runs (ms)
  - Code complexity : lines of code + JOIN/MATCH count + condition count

Queries span 5 categories, chosen so the benchmark tells an honest story
instead of cherry-picking:
  1. Simple aggregation       (no joins)                     — PG typically wins
  2. 1-hop traversal          (1 JOIN / 1 MATCH hop)         — PG typically wins
  3. 2-hop traversal          (2 JOINs / 2 MATCH hops)       — close
  4. Neighbor / 3-hop         (spatial ST_Touches vs NEIGHBORS edge)  — Neo4j wins
  5. Variable-length path     (recursive CTE vs *1..n hops)  — Neo4j wins big

The design goal is "right tool for the right query" — relational is excellent
at flat aggregations on indexed columns; graphs win when the query shape is a
path. The benchmark is intentionally balanced across both sides.

Usage:
    python scripts/performance_comparison.py
    python scripts/performance_comparison.py --runs 20 --output outputs/performance_report.json
"""

import sys, os, json, time, statistics, textwrap, argparse
from pathlib import Path
from dataclasses import dataclass, asdict

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

import psycopg2
from noah_converter.utils.config import load_config
from noah_converter.utils.db_connection import Neo4jConnection


# ── Query definitions ─────────────────────────────────────────────────────────

@dataclass
class QueryPair:
    id: int
    category: str      # simple / 1-hop / 2-hop / neighbor
    description: str
    sql: str
    cypher: str


QUERIES: list[QueryPair] = [

    # ── 1. Simple aggregation (no joins) ─────────────────────────────────
    QueryPair(
        id=1, category="simple",
        description="Count housing projects per borough",
        sql="""
SELECT   borough,
         COUNT(*)          AS project_count,
         SUM(total_units)  AS total_units
FROM     housing_projects
GROUP BY borough
ORDER BY project_count DESC""",
        cypher="""
MATCH (p:HousingProject)
RETURN p.borough          AS borough,
       count(p)            AS project_count,
       sum(p.total_units)  AS total_units
ORDER BY project_count DESC""",
    ),

    # ── 2. Simple filter aggregation ─────────────────────────────────────
    QueryPair(
        id=2, category="simple",
        description="ZIP codes with rent burden above 35%",
        sql="""
SELECT   zip_code,
         rent_burden_rate,
         severe_burden_rate
FROM     noah_affordability_analysis
WHERE    rent_burden_rate > 0.35
ORDER BY rent_burden_rate DESC""",
        cypher="""
MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WHERE a.rent_burden_rate > 0.35
RETURN z.zip_code          AS zip_code,
       a.rent_burden_rate  AS rent_burden_rate,
       a.severe_burden_rate AS severe_burden_rate
ORDER BY a.rent_burden_rate DESC""",
    ),

    # ── 3. 1-hop: project → ZIP ───────────────────────────────────────────
    QueryPair(
        id=3, category="1-hop",
        description="Join housing projects with their ZIP code borough",
        sql="""
SELECT   p.project_name,
         p.total_units,
         z.zip_code,
         z.borough
FROM     housing_projects  p
JOIN     zip_shapes        z  ON p.postcode = z.zip_code
ORDER BY p.total_units DESC
LIMIT    100""",
        cypher="""
MATCH (p:HousingProject)-[:LOCATED_IN_ZIP]->(z:ZipCode)
RETURN p.project_name  AS project_name,
       p.total_units   AS total_units,
       z.zip_code      AS zip_code,
       z.borough       AS borough
ORDER BY p.total_units DESC
LIMIT 100""",
    ),

    # ── 4. 1-hop: project → census tract ─────────────────────────────────
    QueryPair(
        id=4, category="1-hop",
        description="Housing projects in high-burden census tracts (severe > 40%)",
        sql="""
SELECT   p.project_name,
         p.borough,
         p.total_units,
         r.geo_id,
         r.severe_burden_rate
FROM     housing_projects  p
JOIN     zip_tract_crosswalk ztc ON p.postcode     = ztc.zip_code
JOIN     rent_burden         r   ON ztc.tract      = r.geo_id
WHERE    r.severe_burden_rate > 0.40
ORDER BY r.severe_burden_rate DESC
LIMIT    50""",
        cypher="""
MATCH (p:HousingProject)-[:IN_CENSUS_TRACT]->(r:RentBurden)
WHERE r.severe_burden_rate > 0.40
RETURN p.project_name        AS project_name,
       p.borough              AS borough,
       p.total_units          AS total_units,
       r.geo_id               AS geo_id,
       r.severe_burden_rate   AS severe_burden_rate
ORDER BY r.severe_burden_rate DESC
LIMIT 50""",
    ),

    # ── 5. 2-hop: project → ZIP → affordability ───────────────────────────
    QueryPair(
        id=5, category="2-hop",
        description="Projects with their ZIP-level affordability metrics",
        sql="""
SELECT   p.project_name,
         p.borough,
         p.total_units,
         z.zip_code,
         a.rent_burden_rate,
         a.median_income_usd
FROM     housing_projects          p
JOIN     zip_shapes                z  ON p.postcode  = z.zip_code
JOIN     noah_affordability_analysis a ON z.zip_code = a.zip_code
WHERE    a.rent_burden_rate > 0.40
ORDER BY a.rent_burden_rate DESC""",
        cypher="""
MATCH (p:HousingProject)-[:LOCATED_IN_ZIP]->(z:ZipCode)
      -[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WHERE a.rent_burden_rate > 0.40
RETURN p.project_name       AS project_name,
       p.borough             AS borough,
       p.total_units         AS total_units,
       z.zip_code            AS zip_code,
       a.rent_burden_rate    AS rent_burden_rate,
       a.median_income_usd   AS median_income_usd
ORDER BY a.rent_burden_rate DESC""",
    ),

    # ── 6. 2-hop: borough-level rent burden aggregation ───────────────────
    QueryPair(
        id=6, category="2-hop",
        description="Average rent burden and income per borough (via ZIP)",
        sql="""
SELECT   z.borough,
         AVG(a.rent_burden_rate)   AS avg_rent_burden,
         AVG(a.median_income_usd)  AS avg_income,
         COUNT(z.zip_code)         AS zip_count
FROM     zip_shapes                z
JOIN     noah_affordability_analysis a ON z.zip_code = a.zip_code
WHERE    a.rent_burden_rate IS NOT NULL
GROUP BY z.borough
ORDER BY avg_rent_burden DESC""",
        cypher="""
MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WHERE a.rent_burden_rate IS NOT NULL
RETURN z.borough                     AS borough,
       avg(a.rent_burden_rate)        AS avg_rent_burden,
       avg(a.median_income_usd)       AS avg_income,
       count(z)                       AS zip_count
ORDER BY avg_rent_burden DESC""",
    ),

    # ── 7. Neighbor query (THE KEY COMPARISON) ────────────────────────────
    # SQL must compute spatial adjacency on-the-fly (ST_Touches).
    # Neo4j uses pre-computed NEIGHBORS edges — O(1) lookup.
    QueryPair(
        id=7, category="neighbor",
        description="Housing projects in ZIP codes neighboring 10001 "
                    "(SQL: spatial ST_Touches  vs  Neo4j: pre-computed NEIGHBORS)",
        sql="""
SELECT   p.project_name,
         p.borough,
         p.total_units,
         neighbor.zip_code  AS neighbor_zip
FROM     zip_shapes   target
JOIN     zip_shapes   neighbor
           ON  ST_Touches(target.geom::geometry, neighbor.geom::geometry)
           AND neighbor.zip_code <> target.zip_code
JOIN     housing_projects p
           ON  p.postcode = neighbor.zip_code
WHERE    target.zip_code = '10001'
ORDER BY p.total_units DESC""",
        cypher="""
MATCH (z:ZipCode {zip_code: '10001'})-[:NEIGHBORS]-(n:ZipCode)
      <-[:LOCATED_IN_ZIP]-(p:HousingProject)
RETURN p.project_name  AS project_name,
       p.borough        AS borough,
       p.total_units    AS total_units,
       n.zip_code       AS neighbor_zip
ORDER BY p.total_units DESC""",
    ),

    # ── 8. 3-hop neighbor + affordability ────────────────────────────────
    QueryPair(
        id=8, category="neighbor",
        description="Affordability of ZIPs neighboring 10451 + their projects "
                    "(3-hop: ZIP→NEIGHBORS→ZIP→AFFORDABILITY + ZIP←PROJECT)",
        sql="""
SELECT   p.project_name,
         p.total_units,
         neighbor.zip_code      AS neighbor_zip,
         a.rent_burden_rate,
         a.median_income_usd
FROM     zip_shapes   target
JOIN     zip_shapes   neighbor
           ON  ST_Touches(target.geom::geometry, neighbor.geom::geometry)
           AND neighbor.zip_code <> target.zip_code
LEFT JOIN noah_affordability_analysis a
           ON  a.zip_code = neighbor.zip_code
LEFT JOIN housing_projects p
           ON  p.postcode  = neighbor.zip_code
WHERE    target.zip_code = '10451'
ORDER BY a.rent_burden_rate DESC NULLS LAST""",
        cypher="""
MATCH (z:ZipCode {zip_code: '10451'})-[:NEIGHBORS]-(n:ZipCode)
OPTIONAL MATCH (n)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
OPTIONAL MATCH (p:HousingProject)-[:LOCATED_IN_ZIP]->(n)
RETURN n.zip_code           AS neighbor_zip,
       a.rent_burden_rate   AS rent_burden_rate,
       a.median_income_usd  AS median_income_usd,
       p.project_name       AS project_name,
       p.total_units        AS total_units
ORDER BY a.rent_burden_rate DESC""",
    ),

    # ── 9. Variable-length path: ZIPs within 2 hops ──────────────────────
    # Classic graph use-case: "reach within N hops". SQL needs a recursive
    # CTE and grows in plan complexity with each hop; Neo4j handles it with
    # a single quantified path pattern.
    QueryPair(
        id=9, category="var-path",
        description="All ZIPs within 2 hops of 10001 (recursive CTE vs *1..2)",
        sql="""
WITH RECURSIVE reachable(zip_code, depth) AS (
    SELECT zip_code, 0 AS depth
    FROM   zip_shapes
    WHERE  zip_code = '10001'
    UNION
    SELECT CASE
              WHEN a.zip_code = r.zip_code THEN b.zip_code
              ELSE a.zip_code
           END,
           r.depth + 1
    FROM   reachable r
    JOIN   zip_shapes a
    JOIN   zip_shapes b ON a.zip_code < b.zip_code
           AND ST_Touches(a.geom, b.geom)
        ON r.zip_code IN (a.zip_code, b.zip_code)
    WHERE  r.depth < 2
)
SELECT DISTINCT zip_code, MIN(depth) AS min_depth
FROM   reachable
GROUP BY zip_code
ORDER BY min_depth, zip_code""",
        cypher="""
MATCH path = (start:ZipCode {zip_code: '10001'})-[:NEIGHBORS*0..2]-(z:ZipCode)
WITH z.zip_code AS zip_code, min(length(path)) AS min_depth
RETURN zip_code, min_depth
ORDER BY min_depth, zip_code""",
    ),

    # ── 10. Multi-label traversal: demographic + affordability + project ──
    # Joins four node types via three relationship hops. SQL version needs
    # four table JOINs plus the spatial crosswalk for census tracts; Neo4j
    # walks the pattern in one MATCH.
    QueryPair(
        id=10, category="var-path",
        description="Demographic + affordability pattern per borough "
                    "(4-table JOIN vs 3-hop MATCH)",
        sql="""
SELECT   z.borough,
         COUNT(DISTINCT z.zip_code)            AS zip_count,
         AVG(d.total_population)::int          AS avg_population,
         AVG(d.pct_renter_occupied)::numeric(5,2) AS avg_pct_renter,
         AVG(a.rent_burden_rate)::numeric(5,3) AS avg_rent_burden,
         COUNT(p.id)                           AS project_count
FROM     zip_shapes               z
JOIN     zip_demographic          d  ON z.zip_code = d.zip_code
JOIN     noah_affordability_analysis a ON z.zip_code = a.zip_code
LEFT JOIN housing_projects         p  ON p.postcode  = z.zip_code
WHERE    d.pct_renter_occupied > 60
  AND    a.rent_burden_rate    > 0.35
GROUP BY z.borough
ORDER BY avg_rent_burden DESC""",
        cypher="""
MATCH (z:ZipCode)-[:HAS_DEMOGRAPHICS]->(d:Demographic),
      (z)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WHERE d.pct_renter_occupied > 60
  AND a.rent_burden_rate    > 0.35
OPTIONAL MATCH (p:HousingProject)-[:LOCATED_IN_ZIP]->(z)
RETURN z.borough                   AS borough,
       count(DISTINCT z)           AS zip_count,
       avg(d.total_population)     AS avg_population,
       avg(d.pct_renter_occupied)  AS avg_pct_renter,
       avg(a.rent_burden_rate)     AS avg_rent_burden,
       count(p)                    AS project_count
ORDER BY avg_rent_burden DESC""",
    ),
]


# ── Complexity metrics ────────────────────────────────────────────────────────

def code_metrics(code: str, lang: str) -> dict:
    lines   = len([l for l in code.strip().splitlines() if l.strip()])
    if lang == "sql":
        joins   = code.upper().count(" JOIN ")
        wheres  = code.upper().count(" WHERE ") + code.upper().count(" AND ") + code.upper().count(" OR ")
        hops    = joins
    else:  # cypher
        joins   = code.upper().count("MATCH ") + code.upper().count("-[:")
        wheres  = code.upper().count(" WHERE ") + code.upper().count(" AND ") + code.upper().count(" OR ")
        hops    = code.upper().count("-[:")   # relationship traversals
    return {"lines": lines, "joins_or_matches": joins,
            "conditions": wheres, "hops": hops}


# ── Timing helpers ────────────────────────────────────────────────────────────

def time_sql(pg_conn, sql: str, runs: int) -> tuple[list[float], int, str]:
    """Return (times_ms, row_count, error)."""
    times, nrows, err = [], 0, ""
    for i in range(runs):
        try:
            t0  = time.perf_counter()
            cur = pg_conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            cur.close()
            elapsed = (time.perf_counter() - t0) * 1000
            times.append(elapsed)
            nrows = len(rows)
        except Exception as e:
            err = str(e)[:120]
            break
    return times, nrows, err


def time_neo4j(driver, cypher: str, runs: int) -> tuple[list[float], int, str]:
    """Return (times_ms, row_count, error)."""
    times, nrows, err = [], 0, ""
    for i in range(runs):
        try:
            t0 = time.perf_counter()
            with driver.session() as s:
                rows = list(s.run(cypher))
            elapsed = (time.perf_counter() - t0) * 1000
            times.append(elapsed)
            nrows = len(rows)
        except Exception as e:
            err = str(e)[:120]
            break
    return times, nrows, err


# ── Main ──────────────────────────────────────────────────────────────────────

def run_comparison(runs: int = 10, warmup: int = 2,
                   output_path: str | None = None):
    config  = load_config()
    src     = config.source_db
    pg_conn = psycopg2.connect(
        host=src.host, port=src.port,
        dbname=src.database, user=src.user, password=src.password,
    )
    neo4j   = Neo4jConnection(config.target_db)
    driver  = neo4j.driver

    print(f"\n{'='*72}")
    print(f"  PostgreSQL vs Neo4j Performance Comparison")
    print(f"  Runs: {warmup} warmup + {runs} timed   |   Metric: median (ms)")
    print(f"{'='*72}\n")

    results = []

    for q in QUERIES:
        print(f"[Q{q.id}] ({q.category})  {q.description[:55]}…")

        # ── warmup ───────────────────────────────────────────────────────
        time_sql(pg_conn,  q.sql,    warmup)
        time_neo4j(driver, q.cypher, warmup)

        # ── timed runs ───────────────────────────────────────────────────
        pg_times,  pg_rows,  pg_err  = time_sql(pg_conn,  q.sql,    runs)
        n4j_times, n4j_rows, n4j_err = time_neo4j(driver, q.cypher, runs)

        pg_med  = round(statistics.median(pg_times),  2) if pg_times  else None
        n4j_med = round(statistics.median(n4j_times), 2) if n4j_times else None

        sql_m   = code_metrics(q.sql,    "sql")
        cyp_m   = code_metrics(q.cypher, "cypher")

        speedup = round(pg_med / n4j_med, 2) if (pg_med and n4j_med) else None

        pg_label  = f"{pg_med:7.1f} ms" if pg_med  else f"  ERROR"
        n4j_label = f"{n4j_med:7.1f} ms" if n4j_med else f"  ERROR"
        sp_label  = f"{speedup:+.1f}×"   if speedup else "  N/A"
        faster    = "Neo4j" if (speedup and speedup > 1) else ("PG" if speedup else "?")

        print(f"  PostgreSQL : {pg_label}  ({pg_rows} rows)  "
              f"[{sql_m['lines']} lines, {sql_m['joins_or_matches']} JOINs]"
              + (f"  ⚠ {pg_err}" if pg_err else ""))
        print(f"  Neo4j      : {n4j_label}  ({n4j_rows} rows)  "
              f"[{cyp_m['lines']} lines, {cyp_m['hops']} hops]"
              + (f"  ⚠ {n4j_err}" if n4j_err else ""))
        print(f"  Speedup    : {sp_label}  → {faster} faster\n")

        results.append({
            "id": q.id, "category": q.category, "description": q.description,
            "sql":    {"query": q.sql.strip(),    "median_ms": pg_med,
                       "rows": pg_rows, "error": pg_err,  **{f"sql_{k}": v for k, v in sql_m.items()}},
            "cypher": {"query": q.cypher.strip(), "median_ms": n4j_med,
                       "rows": n4j_rows, "error": n4j_err, **{f"cyp_{k}": v for k, v in cyp_m.items()}},
            "speedup_x": speedup,
            "faster": faster,
        })

    neo4j.close()
    pg_conn.close()

    # ── Summary table ─────────────────────────────────────────────────────
    print(f"\n{'='*72}")
    print("  SUMMARY")
    print(f"{'='*72}")
    hdr = (f"  {'#':>2}  {'Category':10}  {'Description':42}  "
           f"{'PG (ms)':>9}  {'N4j (ms)':>9}  {'Speedup':>8}  {'Lines PG/N4j':>12}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for r in results:
        pg_ms  = f"{r['sql']['median_ms']:.1f}"    if r['sql']['median_ms']    else "ERR"
        n4j_ms = f"{r['cypher']['median_ms']:.1f}" if r['cypher']['median_ms'] else "ERR"
        sp     = f"{r['speedup_x']:+.1f}×"         if r['speedup_x']           else "N/A"
        lines  = f"{r['sql']['sql_lines']}/{r['cypher']['cyp_lines']}"
        print(f"  {r['id']:>2}  {r['category']:10}  {r['description'][:42]:42}  "
              f"{pg_ms:>9}  {n4j_ms:>9}  {sp:>8}  {lines:>12}")

    neo4j_faster = sum(1 for r in results if r["faster"] == "Neo4j")
    avg_speedup  = statistics.mean(
        [r["speedup_x"] for r in results if r["speedup_x"] and r["speedup_x"] > 0]
    )
    avg_line_reduction = statistics.mean(
        [(r["sql"]["sql_lines"] - r["cypher"]["cyp_lines"]) / r["sql"]["sql_lines"] * 100
         for r in results if r["sql"]["sql_lines"] > 0]
    )
    print(f"\n  Neo4j faster in {neo4j_faster}/{len(results)} queries")
    print(f"  Average speedup (all queries): {avg_speedup:.2f}×")
    print(f"  Average code reduction (lines): {avg_line_reduction:.0f}%")

    # Per-category breakdown — the honest-story view. Graph wins on paths,
    # loses on flat aggregations.
    print(f"\n  Per-category (where Neo4j wins):")
    by_cat: dict[str, list] = {}
    for r in results:
        by_cat.setdefault(r["category"], []).append(r)
    category_summary = {}
    for cat, items in by_cat.items():
        wins = sum(1 for x in items if x["faster"] == "Neo4j")
        positive_speedups = [x["speedup_x"] for x in items if x["speedup_x"]]
        cat_avg = (
            round(statistics.mean(positive_speedups), 2)
            if positive_speedups else None
        )
        category_summary[cat] = {
            "queries": len(items),
            "neo4j_faster_count": wins,
            "avg_speedup_x": cat_avg,
        }
        print(f"    {cat:10}  Neo4j wins {wins}/{len(items)}  avg {cat_avg}×")

    # ── JSON export ───────────────────────────────────────────────────────
    report = {
        "runs": runs, "warmup": warmup,
        "neo4j_faster_count": neo4j_faster,
        "total_queries": len(results),
        "avg_speedup_x": round(avg_speedup, 2),
        "avg_line_reduction_pct": round(avg_line_reduction, 1),
        "category_summary": category_summary,
        "queries": results,
    }
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n  Report saved → {output_path}")

    return report


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs",   type=int, default=10)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--output", "-o", default="outputs/performance_report.json")
    args = parser.parse_args()
    run_comparison(runs=args.runs, warmup=args.warmup, output_path=args.output)
