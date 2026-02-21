"""
NYC Housing Graph — Explore (Cypher Editor + Schema Reference)
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
    page_title="Explore — NYC Housing Graph",
    page_icon="🔎",
    layout="wide",
)
inject_theme()

with st.sidebar:
    st.markdown(
        '<span class="sidebar-brand">NYC Housing <span>Graph</span></span>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.caption("Write Cypher queries directly against the graph database.")

st.markdown(
    """
    <div class="page-header">
      <div class="page-title">Explore</div>
      <div class="page-sub">Cypher query editor and schema reference</div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_editor, tab_schema = st.tabs(["Query Editor", "Schema Reference"])

# ── Tab 1: Query Editor ───────────────────────────────────────────────
with tab_editor:

    EXAMPLES = {
        "Projects by borough": """\
MATCH (p:HousingProject)
RETURN p.borough            AS borough,
       count(p)             AS projects,
       sum(p.total_units)   AS total_units
ORDER BY projects DESC""",

        "Neighbors of ZIP 10001": """\
MATCH (z:ZipCode {zip_code: '10001'})-[r:NEIGHBORS]-(n:ZipCode)
RETURN n.zip_code           AS zip_code,
       n.borough            AS borough,
       r.shared_boundary_km AS shared_km
ORDER BY n.zip_code""",

        "High rent-burden ZIPs": """\
MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WHERE a.rent_burden_rate > 0.35
RETURN z.zip_code          AS zip_code,
       z.borough           AS borough,
       a.rent_burden_rate  AS rent_burden,
       a.median_income_usd AS median_income
ORDER BY a.rent_burden_rate DESC
LIMIT 20""",

        "Projects in high-burden tracts": """\
MATCH (p:HousingProject)-[:IN_CENSUS_TRACT]->(r:RentBurden)
WHERE r.severe_burden_rate > 0.40
RETURN p.project_name      AS project,
       p.borough           AS borough,
       r.geo_id            AS tract_id,
       r.severe_burden_rate AS severe_burden
ORDER BY r.severe_burden_rate DESC
LIMIT 20""",

        "ZIP affordability overview": """\
MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
RETURN z.zip_code          AS zip_code,
       z.borough           AS borough,
       a.median_income_usd AS median_income,
       a.rent_burden_rate  AS rent_burden,
       a.severe_burden_rate AS severe_burden
ORDER BY z.borough, z.zip_code""",
    }

    load_col, _, __ = st.columns([2, 2, 3])
    with load_col:
        selected = st.selectbox("Load example:", list(EXAMPLES.keys()), label_visibility="collapsed")
    if st.button("Load →"):
        st.session_state["_cypher"] = EXAMPLES[selected]

    cypher = st.text_area(
        "Cypher",
        value=st.session_state.get("_cypher", EXAMPLES["Projects by borough"]),
        height=170,
        label_visibility="collapsed",
        key="cypher_editor",
    )

    run_col, _, __ = st.columns([1, 1, 4])
    with run_col:
        run_btn = st.button("Run ▶", type="primary", use_container_width=True)

    if run_btn and cypher.strip():
        try:
            t0 = time.time()
            rows = run_query(cypher)
            elapsed = round(time.time() - t0, 3)
            st.session_state["_result"] = {"rows": rows, "elapsed": elapsed, "error": None}
        except Exception as e:
            st.session_state["_result"] = {"rows": [], "elapsed": 0, "error": str(e)}

    cr = st.session_state.get("_result")
    if cr:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        if cr["error"]:
            st.markdown(
                f'<div class="error-msg">⚠ {cr["error"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            rows = cr["rows"]
            st.markdown(
                f'<div class="result-meta">'
                f'{len(rows)} row{"s" if len(rows)!=1 else ""} &nbsp;·&nbsp; {cr["elapsed"]}s'
                f'</div>',
                unsafe_allow_html=True,
            )
            if rows:
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.download_button(
                    "↓ Download CSV",
                    df.to_csv(index=False),
                    file_name="cypher_results.csv",
                    mime="text/csv",
                )
            else:
                st.info("No results.")

# ── Tab 2: Schema Reference ───────────────────────────────────────────
with tab_schema:
    n_col, r_col = st.columns(2)

    with n_col:
        st.markdown("#### Nodes")

        nodes_info = [
            (
                "HousingProject",
                "db_id",
                "integer",
                [
                    "project_id", "project_name", "building_id",
                    "house_number", "street_name", "borough", "postcode",
                    "bbl", "bin", "census_tract",
                    "total_units", "counted_rental_units",
                    "studio_units, one_br_units … six_br_units",
                    "low_income_units, extremely_low_income_units",
                    "moderate_income_units, middle_income_units",
                    "project_start_date, project_completion_date",
                    "center_lat, center_lon, area_km2",
                ],
            ),
            (
                "ZipCode",
                "zip_code",
                "string — 5-digit, e.g. '10001'",
                ["borough", "center_lat", "center_lon", "area_km2"],
            ),
            (
                "AffordabilityAnalysis",
                "zip_code",
                "string",
                [
                    "median_income_usd",
                    "rent_burden_rate  (decimal, e.g. 0.35 = 35%)",
                    "severe_burden_rate",
                ],
            ),
            (
                "RentBurden",
                "geo_id",
                "string — Census GEOID",
                [
                    "tract_name",
                    "rent_burden_rate",
                    "severe_burden_rate",
                    "center_lat, center_lon, area_km2",
                ],
            ),
        ]

        for label, mk, mk_type, props in nodes_info:
            with st.expander(f"(:{label})", expanded=True):
                st.markdown(f"**Merge key:** `{mk}` — {mk_type}")
                st.markdown("**Properties:**")
                for p in props:
                    st.markdown(f"- `{p}`")

    with r_col:
        st.markdown("#### Relationships")

        rels_info = [
            (
                "LOCATED_IN_ZIP",
                "HousingProject", "ZipCode",
                "–",
                "FK: postcode → zip_code",
            ),
            (
                "HAS_AFFORDABILITY_DATA",
                "ZipCode", "AffordabilityAnalysis",
                "–",
                "FK: zip_code → zip_code",
            ),
            (
                "IN_CENSUS_TRACT",
                "HousingProject", "RentBurden",
                "–",
                "Computed: borough + census_tract → geo_id",
            ),
            (
                "NEIGHBORS",
                "ZipCode", "ZipCode",
                "shared_boundary_km · is_touching",
                "Spatial — undirected, use -[:NEIGHBORS]-",
            ),
            (
                "CONTAINS_TRACT",
                "ZipCode", "RentBurden",
                "overlap_area_km2 · tract_coverage_ratio",
                "Spatial intersection",
            ),
        ]

        for rel_type, from_lbl, to_lbl, props, note in rels_info:
            with st.expander(f"[:{rel_type}]", expanded=True):
                st.markdown(
                    f"`(:{from_lbl})-[:{rel_type}]->(:{to_lbl})`"
                )
                if props != "–":
                    st.markdown(f"**Props:** `{props}`")
                st.caption(note)

        st.markdown("---")
        st.markdown("**Cypher tips**")
        st.markdown(
            "- Use `-[:NEIGHBORS]-` (no arrow) for undirected traversal\n"
            "- `rent_burden_rate` is a decimal — filter with `> 0.35` not `> 35`\n"
            "- `HousingProject.postcode` = `ZipCode.zip_code`\n"
            "- Always add `LIMIT` for exploratory queries"
        )
