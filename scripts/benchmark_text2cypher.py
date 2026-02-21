"""
Text2Cypher Benchmark — 20 representative questions on the NOAH graph.

Scoring per question:
  - syntax_ok   (1 pt)  : LLM Cypher executed without error
  - has_results (1 pt)  : returned ≥1 row (when ground truth also has rows)
  - count_match (1 pt)  : row count within 40% of ground truth
  - top_match   (1 pt)  : at least one expected "key value" appears in results

Pass threshold: score ≥ 3 / 4  → "correct"
Overall accuracy = # correct / 20

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python scripts/benchmark_text2cypher.py
    python scripts/benchmark_text2cypher.py --output outputs/benchmark_report.json
"""

import sys
import os
import json
import time
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from noah_converter.utils.config import load_config
from noah_converter.utils.db_connection import Neo4jConnection
from noah_converter.text2cypher import Text2CypherTranslator


# ── Ground-truth benchmark questions ─────────────────────────────────────────

@dataclass
class BenchmarkQuestion:
    id: int
    level: str          # easy / medium / hard
    question: str
    ground_truth_cypher: str
    expected_keys: list[str]   # key values that should appear somewhere in results
    min_rows: int = 1          # minimum expected result rows


QUESTIONS: list[BenchmarkQuestion] = [
    # ── Level 1: Simple aggregations / lookups (Q1–Q6) ───────────────────
    BenchmarkQuestion(
        id=1, level="easy",
        question="How many housing projects are in each borough?",
        ground_truth_cypher="""
MATCH (p:HousingProject)
RETURN p.borough AS borough, count(p) AS project_count
ORDER BY project_count DESC""",
        expected_keys=["Brooklyn", "Bronx", "Manhattan"],
        min_rows=5,
    ),
    BenchmarkQuestion(
        id=2, level="easy",
        question="What is the total number of housing units per borough?",
        ground_truth_cypher="""
MATCH (p:HousingProject)
RETURN p.borough AS borough, sum(p.total_units) AS total_units
ORDER BY total_units DESC""",
        expected_keys=["Brooklyn", "Bronx"],
        min_rows=5,
    ),
    BenchmarkQuestion(
        id=3, level="easy",
        question="Which ZIP codes have rent burden rate above 40%?",
        ground_truth_cypher="""
MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WHERE a.rent_burden_rate > 0.40
RETURN z.zip_code AS zip_code, z.borough AS borough, a.rent_burden_rate AS rent_burden_rate
ORDER BY a.rent_burden_rate DESC""",
        expected_keys=["Bronx", "Brooklyn"],
        min_rows=1,
    ),
    BenchmarkQuestion(
        id=4, level="easy",
        question="What is the average median household income by borough?",
        ground_truth_cypher="""
MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WHERE a.median_income_usd IS NOT NULL
RETURN z.borough AS borough, avg(a.median_income_usd) AS avg_income
ORDER BY avg_income DESC""",
        expected_keys=["Manhattan", "Staten Island"],
        min_rows=5,
    ),
    BenchmarkQuestion(
        id=5, level="easy",
        question="List the top 10 ZIP codes with the most housing projects.",
        ground_truth_cypher="""
MATCH (p:HousingProject)-[:LOCATED_IN_ZIP]->(z:ZipCode)
RETURN z.zip_code AS zip_code, z.borough AS borough, count(p) AS project_count
ORDER BY project_count DESC
LIMIT 10""",
        expected_keys=["11221", "Brooklyn"],
        min_rows=10,
    ),
    BenchmarkQuestion(
        id=6, level="easy",
        question="How many housing projects have more than 100 total units?",
        ground_truth_cypher="""
MATCH (p:HousingProject)
WHERE p.total_units > 100
RETURN count(p) AS project_count""",
        expected_keys=[],
        min_rows=1,
    ),

    # ── Level 2: Filtered / joined queries (Q7–Q13) ──────────────────────
    BenchmarkQuestion(
        id=7, level="medium",
        question="Which ZIP codes in Brooklyn have the highest rent burden rate?",
        ground_truth_cypher="""
MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WHERE z.borough = 'Brooklyn' AND a.rent_burden_rate IS NOT NULL
RETURN z.zip_code AS zip_code, a.rent_burden_rate AS rent_burden_rate
ORDER BY a.rent_burden_rate DESC
LIMIT 10""",
        expected_keys=["Brooklyn", "11212", "11233"],
        min_rows=5,
    ),
    BenchmarkQuestion(
        id=8, level="medium",
        question="Show census tracts with severe rent burden above 45%.",
        ground_truth_cypher="""
MATCH (r:RentBurden)
WHERE r.severe_burden_rate > 0.45
RETURN r.geo_id AS geo_id, r.severe_burden_rate AS severe_burden_rate
ORDER BY r.severe_burden_rate DESC
LIMIT 20""",
        expected_keys=[],
        min_rows=1,
    ),
    BenchmarkQuestion(
        id=9, level="medium",
        question="Which ZIP code in Manhattan has the highest median income?",
        ground_truth_cypher="""
MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WHERE z.borough = 'Manhattan' AND a.median_income_usd IS NOT NULL
RETURN z.zip_code AS zip_code, a.median_income_usd AS median_income
ORDER BY median_income DESC
LIMIT 1""",
        expected_keys=["Manhattan", "10013"],
        min_rows=1,
    ),
    BenchmarkQuestion(
        id=10, level="medium",
        question="What is the total number of low-income units per borough?",
        ground_truth_cypher="""
MATCH (p:HousingProject)
WHERE p.low_income_units IS NOT NULL
RETURN p.borough AS borough, sum(p.low_income_units) AS total_low_income_units
ORDER BY total_low_income_units DESC""",
        expected_keys=["Brooklyn", "Bronx"],
        min_rows=5,
    ),
    BenchmarkQuestion(
        id=11, level="medium",
        question="Find ZIP codes where median income is below $50,000.",
        ground_truth_cypher="""
MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WHERE a.median_income_usd < 50000
RETURN z.zip_code AS zip_code, z.borough AS borough, a.median_income_usd AS median_income
ORDER BY median_income ASC""",
        expected_keys=["Bronx", "Brooklyn"],
        min_rows=1,
    ),
    BenchmarkQuestion(
        id=12, level="medium",
        question="How many housing projects were completed after January 1, 2015?",
        ground_truth_cypher="""
MATCH (p:HousingProject)
WHERE p.project_completion_date >= date('2015-01-01')
RETURN count(p) AS project_count""",
        expected_keys=[],
        min_rows=1,
    ),
    BenchmarkQuestion(
        id=13, level="medium",
        question="Which ZIP codes have both high rent burden (above 45%) and more than 20 housing projects?",
        ground_truth_cypher="""
MATCH (p:HousingProject)-[:LOCATED_IN_ZIP]->(z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WITH z, count(p) AS project_count, a.rent_burden_rate AS rent_burden
WHERE project_count > 20 AND rent_burden > 0.45
RETURN z.zip_code AS zip_code, z.borough AS borough, project_count, rent_burden
ORDER BY rent_burden DESC""",
        expected_keys=["Bronx", "Brooklyn"],
        min_rows=1,
    ),

    # ── Level 3: Multi-hop graph traversal (Q14–Q20) ─────────────────────
    BenchmarkQuestion(
        id=14, level="hard",
        question="Find housing projects in ZIP codes neighboring ZIP code 10001.",
        ground_truth_cypher="""
MATCH (z:ZipCode {zip_code: '10001'})-[:NEIGHBORS]-(n:ZipCode)<-[:LOCATED_IN_ZIP]-(p:HousingProject)
RETURN p.project_name AS project_name, n.zip_code AS zip_code, p.total_units AS total_units
ORDER BY p.total_units DESC
LIMIT 20""",
        expected_keys=["10011", "10036"],
        min_rows=1,
    ),
    BenchmarkQuestion(
        id=15, level="hard",
        question="How many housing projects are located in census tracts with severe rent burden above 40%?",
        ground_truth_cypher="""
MATCH (p:HousingProject)-[:IN_CENSUS_TRACT]->(r:RentBurden)
WHERE r.severe_burden_rate > 0.40
RETURN count(DISTINCT p) AS project_count""",
        expected_keys=[],
        min_rows=1,
    ),
    BenchmarkQuestion(
        id=16, level="hard",
        question="Which ZIP codes are neighbors of ZIP codes with rent burden above 50%?",
        ground_truth_cypher="""
MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WHERE a.rent_burden_rate > 0.50
WITH collect(z) AS high_burden_zips
UNWIND high_burden_zips AS z
MATCH (z)-[:NEIGHBORS]-(neighbor:ZipCode)
WHERE NOT neighbor IN high_burden_zips
RETURN DISTINCT neighbor.zip_code AS zip_code, neighbor.borough AS borough
ORDER BY zip_code
LIMIT 20""",
        expected_keys=[],
        min_rows=1,
    ),
    BenchmarkQuestion(
        id=17, level="hard",
        question="Compare the rent burden of ZIP code 10451 with its neighboring ZIP codes.",
        ground_truth_cypher="""
MATCH (z:ZipCode {zip_code: '10451'})-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WITH z, a.rent_burden_rate AS target_burden
MATCH (z)-[:NEIGHBORS]-(n:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(na:AffordabilityAnalysis)
RETURN n.zip_code AS neighbor_zip, na.rent_burden_rate AS rent_burden, target_burden AS zip_10451_burden
ORDER BY rent_burden DESC""",
        expected_keys=["10451", "10452", "10453"],
        min_rows=1,
    ),
    BenchmarkQuestion(
        id=18, level="hard",
        question="What census tracts are contained within ZIP code 11201?",
        ground_truth_cypher="""
MATCH (z:ZipCode {zip_code: '11201'})-[:CONTAINS_TRACT]->(r:RentBurden)
RETURN r.geo_id AS geo_id, r.rent_burden_rate AS rent_burden_rate
ORDER BY r.rent_burden_rate DESC""",
        expected_keys=["11201"],
        min_rows=1,
    ),
    BenchmarkQuestion(
        id=19, level="hard",
        question="Find housing projects in the Bronx that are in census tracts with severe rent burden above 35%, and show the tract's severe burden rate.",
        ground_truth_cypher="""
MATCH (p:HousingProject)-[:IN_CENSUS_TRACT]->(r:RentBurden)
WHERE p.borough = 'Bronx' AND r.severe_burden_rate > 0.35
RETURN p.project_name AS project_name, p.total_units AS total_units, r.severe_burden_rate AS severe_burden
ORDER BY r.severe_burden_rate DESC
LIMIT 20""",
        expected_keys=["Bronx"],
        min_rows=1,
    ),
    BenchmarkQuestion(
        id=20, level="hard",
        question="For each borough, what is the average rent burden of ZIP codes that contain at least one housing project with more than 200 units?",
        ground_truth_cypher="""
MATCH (p:HousingProject)-[:LOCATED_IN_ZIP]->(z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WHERE p.total_units > 200
RETURN z.borough AS borough,
       avg(a.rent_burden_rate) AS avg_rent_burden,
       count(DISTINCT z) AS zip_count
ORDER BY avg_rent_burden DESC""",
        expected_keys=["Bronx", "Brooklyn", "Manhattan"],
        min_rows=3,
    ),
]


# ── Scoring ───────────────────────────────────────────────────────────────────

@dataclass
class QuestionResult:
    id: int
    level: str
    question: str
    ground_truth_rows: int
    llm_cypher: str = ""
    llm_rows: int = 0
    syntax_ok: bool = False
    has_results: bool = False
    count_match: bool = False
    top_match: bool = False
    score: float = 0.0
    passed: bool = False
    error: str = ""
    elapsed_s: float = 0.0


def run_cypher(driver, cypher: str) -> tuple[list[dict], str]:
    """Execute cypher, return (rows, error_msg)."""
    try:
        with driver.session() as session:
            result = session.run(cypher)
            rows = [dict(r) for r in result]
        return rows, ""
    except Exception as e:
        return [], str(e)


def values_flat(rows: list[dict]) -> set[str]:
    """Flatten all values in result rows to a set of strings."""
    out = set()
    for row in rows:
        for v in row.values():
            if v is not None:
                out.add(str(v))
    return out


def score_result(q: BenchmarkQuestion, gt_rows: list[dict],
                 llm_rows: list[dict], error: str) -> QuestionResult:
    res = QuestionResult(id=q.id, level=q.level, question=q.question,
                         ground_truth_rows=len(gt_rows))
    res.error = error

    # syntax_ok
    res.syntax_ok = error == ""

    # has_results
    if q.min_rows == 0:
        res.has_results = True
    else:
        res.has_results = len(llm_rows) >= 1

    # count_match: within 40% of ground truth (or both zero)
    gt_n = len(gt_rows)
    llm_n = len(llm_rows)
    if gt_n == 0:
        res.count_match = llm_n == 0
    else:
        res.count_match = abs(llm_n - gt_n) / gt_n <= 0.40

    # top_match: expected key values appear in result
    if not q.expected_keys:
        res.top_match = res.syntax_ok  # no keys to check → pass if ran
    else:
        flat = values_flat(llm_rows)
        hits = sum(1 for k in q.expected_keys if k in flat)
        res.top_match = hits >= max(1, len(q.expected_keys) // 2)

    # aggregate
    criteria = [res.syntax_ok, res.has_results, res.count_match, res.top_match]
    res.score = sum(criteria) / 4
    res.passed = res.score >= 0.75
    res.llm_rows = llm_n
    return res


# ── Main runner ───────────────────────────────────────────────────────────────

def run_benchmark(api_key: str, output_path: Optional[str] = None, verbose: bool = True):
    config = load_config()
    conn = Neo4jConnection(config.target_db)
    driver = conn.driver

    translator = Text2CypherTranslator(
        neo4j_conn=conn,
        llm_provider="claude",
        api_key=api_key,
        model=config.text2cypher.model,
    )

    results: list[QuestionResult] = []

    print(f"\n{'='*70}")
    print(f"  Text2Cypher Benchmark  —  {len(QUESTIONS)} questions")
    print(f"  Model: {config.text2cypher.model}")
    print(f"{'='*70}\n")

    for q in QUESTIONS:
        print(f"[Q{q.id:02d}/{len(QUESTIONS)}] ({q.level:6s}) {q.question[:60]}...")

        # Ground truth
        gt_rows, gt_err = run_cypher(driver, q.ground_truth_cypher)
        if gt_err:
            print(f"  ⚠  Ground truth error: {gt_err}")

        # LLM translation + execution
        t0 = time.time()
        try:
            tr = translator.query(question=q.question, execute=True, explain=False)
            elapsed = round(time.time() - t0, 2)
            llm_cypher = tr.get("cypher", "")
            llm_rows   = tr.get("results") or []
            llm_error  = tr.get("error", "") or ""
        except Exception as e:
            elapsed = round(time.time() - t0, 2)
            llm_cypher, llm_rows, llm_error = "", [], str(e)

        res = score_result(q, gt_rows, llm_rows, llm_error)
        res.llm_cypher = llm_cypher
        res.elapsed_s  = elapsed

        status = "✅ PASS" if res.passed else "❌ FAIL"
        print(f"  {status}  score={res.score:.2f}  gt={len(gt_rows)}r  llm={len(llm_rows)}r  {elapsed}s")
        if not res.syntax_ok and verbose:
            print(f"  error: {llm_error[:120]}")

        results.append(res)
        time.sleep(0.5)   # gentle rate-limit

    conn.close()

    # ── Summary ───────────────────────────────────────────────────────────
    passed    = [r for r in results if r.passed]
    accuracy  = len(passed) / len(results) * 100

    by_level  = {}
    for r in results:
        by_level.setdefault(r.level, []).append(r)

    print(f"\n{'='*70}")
    print(f"  RESULTS")
    print(f"{'='*70}")
    print(f"  Overall accuracy:  {len(passed)}/{len(results)} = {accuracy:.1f}%")
    for lvl in ["easy", "medium", "hard"]:
        grp = by_level.get(lvl, [])
        p   = sum(1 for r in grp if r.passed)
        print(f"  {lvl.capitalize():8s}:  {p}/{len(grp)} = {p/len(grp)*100:.0f}%")
    print()

    # Markdown table
    print("  | # | Level  | Question (short) | GT | LLM | Score | Pass |")
    print("  |---|--------|------------------|----|-----|-------|------|")
    for r in results:
        short = r.question[:40] + ("…" if len(r.question) > 40 else "")
        tick  = "✅" if r.passed else "❌"
        print(f"  | {r.id:2d} | {r.level:6s} | {short:42s} | {r.ground_truth_rows:3d} | {r.llm_rows:3d} | {r.score:.2f} | {tick} |")

    # JSON export
    report = {
        "model": config.text2cypher.model,
        "total": len(results),
        "passed": len(passed),
        "accuracy_pct": round(accuracy, 1),
        "by_level": {
            lvl: {
                "passed": sum(1 for r in grp if r.passed),
                "total":  len(grp),
                "accuracy_pct": round(sum(1 for r in grp if r.passed) / len(grp) * 100, 1),
            }
            for lvl, grp in by_level.items()
        },
        "questions": [asdict(r) for r in results],
    }

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n  Report saved → {output_path}")

    return report


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Text2Cypher benchmark (20 questions)")
    parser.add_argument("--output", "-o", default="outputs/benchmark_report.json",
                        help="Path for JSON report (default: outputs/benchmark_report.json)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Less verbose output")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("Error: set ANTHROPIC_API_KEY environment variable first.")
        sys.exit(1)

    run_benchmark(api_key=api_key, output_path=args.output, verbose=not args.quiet)
