"""
NYC Housing Graph — Templates (Parameterized Question Library)
"""

import sys
import time
from pathlib import Path

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.theme import inject_theme
from utils.connection import run_query

st.set_page_config(
    page_title="Templates — NYC Housing Graph",
    page_icon="📋",
    layout="wide",
)
inject_theme()

with st.sidebar:
    st.markdown(
        '<span class="sidebar-brand">NYC Housing <span>Graph</span></span>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.caption("Run parameterized queries without writing Cypher.")

st.markdown(
    """
    <div class="page-header">
      <div class="page-title">Templates</div>
      <div class="page-sub">Parameterized query library — choose geography, indicator, and depth</div>
    </div>
    """,
    unsafe_allow_html=True,
)

BOROUGHS = ["All", "Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]

# ─── Helper ───────────────────────────────────────────────────────────────────

def _run(cypher: str, params: dict) -> tuple[list[dict], float, str]:
    """Execute query, return (rows, elapsed_s, cypher_shown)."""
    t0 = time.time()
    rows = run_query(cypher, params)
    return rows, round(time.time() - t0, 3), cypher


def _show_results(rows: list[dict], elapsed: float, cypher: str) -> None:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    with st.expander("Cypher", expanded=False):
        st.code(cypher, language="cypher")

    if not rows:
        st.info("No results for these parameters.")
        return

    st.markdown(
        f'<div class="result-meta">{len(rows)} row{"s" if len(rows)!=1 else ""}'
        f" &nbsp;·&nbsp; {elapsed}s</div>",
        unsafe_allow_html=True,
    )
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    dl_col, _ = st.columns([1, 5])
    with dl_col:
        st.download_button(
            "↓ CSV", df.to_csv(index=False),
            file_name="template_results.csv", mime="text/csv",
        )

    # Auto chart
    num_cols = df.select_dtypes("number").columns.tolist()
    txt_cols = df.select_dtypes("object").columns.tolist()
    if num_cols and txt_cols and 2 <= len(df) <= 40:
        try:
            import plotly.express as px
            fig = px.bar(
                df, x=txt_cols[0], y=num_cols[0],
                color_discrete_sequence=["#C1440E"],
                template="plotly_white", text=num_cols[0],
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                height=320, margin=dict(t=16, b=0, l=0, r=0),
                xaxis_title="", yaxis_title=num_cols[0],
                font_family="Inter",
                plot_bgcolor="#F9F7F4", paper_bgcolor="#F9F7F4",
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass


# ─── Template tabs ────────────────────────────────────────────────────────────

t1, t2, t3, t4, t5 = st.tabs([
    "① Rent Burden by Borough",
    "② Neighbor Projects",
    "③ High-Burden Tracts",
    "④ Borough Comparison",
    "⑤ Top Projects",
])

# ── Template 1: Rent burden filter by borough ─────────────────────────────────
with t1:
    st.markdown("#### ZIP codes with rent burden above threshold")
    st.caption("Filter by borough and rent burden rate. Returns ZIP codes sorted by burden.")

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        t1_borough = st.selectbox("Borough", BOROUGHS, key="t1_borough")
    with c2:
        t1_threshold = st.slider(
            "Rent burden threshold (%)", 20, 55, 35, step=5, key="t1_threshold"
        )
    with c3:
        st.markdown("<br>", unsafe_allow_html=True)
        t1_run = st.button("Run ▶", type="primary", use_container_width=True, key="t1_run")

    if t1_run:
        threshold = t1_threshold / 100.0
        if t1_borough == "All":
            cypher = """
MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WHERE a.rent_burden_rate > $threshold
RETURN z.borough           AS borough,
       z.zip_code          AS zip_code,
       a.rent_burden_rate  AS rent_burden_rate,
       a.severe_burden_rate AS severe_burden_rate,
       a.median_income_usd AS median_income_usd
ORDER BY a.rent_burden_rate DESC
"""
            params = {"threshold": threshold}
        else:
            cypher = """
MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WHERE z.borough = $borough AND a.rent_burden_rate > $threshold
RETURN z.zip_code          AS zip_code,
       a.rent_burden_rate  AS rent_burden_rate,
       a.severe_burden_rate AS severe_burden_rate,
       a.median_income_usd AS median_income_usd
ORDER BY a.rent_burden_rate DESC
"""
            params = {"borough": t1_borough, "threshold": threshold}

        rows, elapsed, q = _run(cypher, params)
        _show_results(rows, elapsed, q)

# ── Template 2: Projects in neighboring ZIPs ──────────────────────────────────
with t2:
    st.markdown("#### Housing projects in ZIP codes neighboring a target")
    st.caption(
        "Enter a 5-digit ZIP code to find all housing projects in adjacent ZIP codes. "
        "Uses pre-computed NEIGHBORS edges — no spatial computation at query time."
    )

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        t2_zip = st.text_input(
            "Target ZIP code", value="10001", max_chars=5, key="t2_zip",
            placeholder="e.g. 10001",
        )
    with c2:
        t2_hops = st.radio(
            "Relationship depth", ["1 hop (direct neighbors)", "2 hops (neighbors of neighbors)"],
            key="t2_hops", horizontal=True,
        )
    with c3:
        st.markdown("<br>", unsafe_allow_html=True)
        t2_run = st.button("Run ▶", type="primary", use_container_width=True, key="t2_run")

    if t2_run:
        if not t2_zip.strip().isdigit() or len(t2_zip.strip()) != 5:
            st.warning("Please enter a valid 5-digit ZIP code.")
        else:
            if "1 hop" in t2_hops:
                cypher = """
MATCH (z:ZipCode {zip_code: $zip_code})-[:NEIGHBORS]-(n:ZipCode)
      <-[:LOCATED_IN_ZIP]-(p:HousingProject)
RETURN p.project_name  AS project_name,
       p.borough        AS borough,
       p.total_units    AS total_units,
       n.zip_code       AS neighbor_zip
ORDER BY p.total_units DESC
LIMIT 100
"""
            else:
                cypher = """
MATCH (z:ZipCode {zip_code: $zip_code})-[:NEIGHBORS*1..2]-(n:ZipCode)
      <-[:LOCATED_IN_ZIP]-(p:HousingProject)
WHERE n.zip_code <> $zip_code
RETURN DISTINCT p.project_name AS project_name,
       p.borough               AS borough,
       p.total_units           AS total_units,
       n.zip_code              AS neighbor_zip
ORDER BY p.total_units DESC
LIMIT 100
"""
            rows, elapsed, q = _run(cypher, {"zip_code": t2_zip.strip()})
            _show_results(rows, elapsed, q)

# ── Template 3: Census tracts with high burden ────────────────────────────────
with t3:
    st.markdown("#### Housing projects in high-burden census tracts")
    st.caption("Find projects located in census tracts with severe rent burden above threshold.")

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        t3_borough = st.selectbox("Borough", BOROUGHS, key="t3_borough")
    with c2:
        t3_threshold = st.slider(
            "Severe burden threshold (%)", 25, 60, 40, step=5, key="t3_threshold"
        )
    with c3:
        st.markdown("<br>", unsafe_allow_html=True)
        t3_run = st.button("Run ▶", type="primary", use_container_width=True, key="t3_run")

    if t3_run:
        threshold = t3_threshold / 100.0
        if t3_borough == "All":
            cypher = """
MATCH (p:HousingProject)-[:IN_CENSUS_TRACT]->(r:RentBurden)
WHERE r.severe_burden_rate > $threshold
RETURN p.project_name        AS project_name,
       p.borough              AS borough,
       p.total_units          AS total_units,
       r.geo_id               AS tract_id,
       r.severe_burden_rate   AS severe_burden_rate
ORDER BY r.severe_burden_rate DESC
LIMIT 100
"""
            params = {"threshold": threshold}
        else:
            cypher = """
MATCH (p:HousingProject)-[:IN_CENSUS_TRACT]->(r:RentBurden)
WHERE p.borough = $borough AND r.severe_burden_rate > $threshold
RETURN p.project_name        AS project_name,
       p.total_units          AS total_units,
       r.geo_id               AS tract_id,
       r.severe_burden_rate   AS severe_burden_rate
ORDER BY r.severe_burden_rate DESC
LIMIT 100
"""
            params = {"borough": t3_borough, "threshold": threshold}

        rows, elapsed, q = _run(cypher, params)
        _show_results(rows, elapsed, q)

# ── Template 4: Borough comparison ───────────────────────────────────────────
with t4:
    st.markdown("#### Compare indicators across boroughs")
    st.caption("Aggregate any affordability indicator by borough via ZIP codes.")

    INDICATORS = {
        "Rent burden rate (avg %)":    ("rent_burden_rate",   True),
        "Severe burden rate (avg %)":  ("severe_burden_rate", True),
        "Median income (avg $)":       ("median_income_usd",  False),
    }

    c1, c2 = st.columns([3, 1])
    with c1:
        t4_ind = st.selectbox("Indicator", list(INDICATORS.keys()), key="t4_ind")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        t4_run = st.button("Run ▶", type="primary", use_container_width=True, key="t4_run")

    if t4_run:
        field, is_pct = INDICATORS[t4_ind]
        cypher = f"""
MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WHERE a.{field} IS NOT NULL
RETURN z.borough              AS borough,
       avg(a.{field})         AS avg_value,
       min(a.{field})         AS min_value,
       max(a.{field})         AS max_value,
       count(z)               AS zip_count
ORDER BY avg_value DESC
"""
        rows, elapsed, q = _run(cypher, {})
        if rows:
            # Convert to percentage if needed
            if is_pct:
                for r in rows:
                    for k in ("avg_value", "min_value", "max_value"):
                        if r[k] is not None:
                            r[k] = round(r[k] * 100, 1)
        _show_results(rows, elapsed, q)

# ── Template 5: Top N projects ────────────────────────────────────────────────
with t5:
    st.markdown("#### Top housing projects by size metric")
    st.caption("Rank projects within a borough by total units, low-income units, or other metrics.")

    METRICS = {
        "Total units":           "total_units",
        "Low-income units":      "low_income_units",
        "Extremely low-income":  "extremely_low_income_units",
        "Moderate-income units": "moderate_income_units",
    }

    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
    with c1:
        t5_borough = st.selectbox("Borough", BOROUGHS, key="t5_borough")
    with c2:
        t5_metric = st.selectbox("Sort by", list(METRICS.keys()), key="t5_metric")
    with c3:
        t5_n = st.number_input("Top N", min_value=5, max_value=100, value=20, step=5, key="t5_n")
    with c4:
        st.markdown("<br>", unsafe_allow_html=True)
        t5_run = st.button("Run ▶", type="primary", use_container_width=True, key="t5_run")

    if t5_run:
        field = METRICS[t5_metric]
        if t5_borough == "All":
            cypher = f"""
MATCH (p:HousingProject)
WHERE p.{field} IS NOT NULL
RETURN p.project_name   AS project_name,
       p.borough         AS borough,
       p.postcode        AS zip_code,
       p.total_units     AS total_units,
       p.{field}         AS {field}
ORDER BY p.{field} DESC
LIMIT $n
"""
        else:
            cypher = f"""
MATCH (p:HousingProject)
WHERE p.borough = $borough AND p.{field} IS NOT NULL
RETURN p.project_name   AS project_name,
       p.postcode        AS zip_code,
       p.total_units     AS total_units,
       p.{field}         AS {field}
ORDER BY p.{field} DESC
LIMIT $n
"""
        params = {"n": int(t5_n)}
        if t5_borough != "All":
            params["borough"] = t5_borough

        rows, elapsed, q = _run(cypher, params)
        _show_results(rows, elapsed, q)
