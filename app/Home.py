"""
NYC Housing Graph — Home / Dashboard
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from utils.theme import inject_theme
from utils.connection import get_db_stats

st.set_page_config(
    page_title="NYC Housing Graph",
    page_icon="🏙",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_theme()

# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<span class="sidebar-brand">NYC Housing <span>Graph</span></span>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.caption(
        "A knowledge graph of NYC affordable housing data. "
        "Query in natural language or write Cypher directly."
    )

# ── Header ───────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="page-header">
      <div class="page-title">NYC Affordable Housing Graph</div>
      <div class="page-sub">
        Exploring naturally occurring affordable housing across New York City's five boroughs
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Live Stats ───────────────────────────────────────────────────────
stats = get_db_stats()

total_rels = sum(
    stats.get(f"r_{r}", 0)
    for r in [
        "LOCATED_IN_ZIP",
        "NEIGHBORS",
        "IN_CENSUS_TRACT",
        "CONTAINS_TRACT",
        "HAS_AFFORDABILITY_DATA",
    ]
)

stat_items = [
    ("Housing Projects", stats.get("n_HousingProject", "—"), "buildings across 5 boroughs"),
    ("ZIP Codes",        stats.get("n_ZipCode", "—"),         "NYC postal boundaries"),
    ("Census Tracts",   stats.get("n_RentBurden", "—"),       "tract-level rent burden"),
    ("Affordability",   stats.get("n_AffordabilityAnalysis", "—"), "ZIP income + rent data"),
    ("Connections",     total_rels or "—",                    "graph relationships"),
]

cols = st.columns(5)
for col, (label, value, hint) in zip(cols, stat_items):
    with col:
        display = f"{value:,}" if isinstance(value, int) else str(value)
        st.markdown(
            f"""
            <div class="stat-card">
              <div class="stat-val">{display}</div>
              <div class="stat-lbl">{label}</div>
              <div class="stat-hint">{hint}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Quick Search ─────────────────────────────────────────────────────
st.markdown("#### Search the housing data")

EXAMPLES = [
    "How many projects are in each borough?",
    "Which ZIP codes in Brooklyn have the highest rent burden?",
    "Find housing projects in ZIP codes neighboring 10001",
    "Show census tracts with severe rent burden above 40%",
    "Compare median income across Manhattan ZIP codes",
]

chip_cols = st.columns(len(EXAMPLES))
for col, ex in zip(chip_cols, EXAMPLES):
    with col:
        if st.button(ex, use_container_width=True, key=f"home_chip_{ex[:15]}"):
            st.session_state["pending_query"] = ex
            st.switch_page("pages/1_Ask.py")

st.markdown("")

qcol, bcol = st.columns([5, 1])
with qcol:
    quick_q = st.text_input(
        "question",
        placeholder="e.g. Which neighborhoods have the most affordable housing units?",
        label_visibility="collapsed",
    )
with bcol:
    if st.button("Search →", type="primary", use_container_width=True) and quick_q.strip():
        st.session_state["pending_query"] = quick_q.strip()
        st.switch_page("pages/1_Ask.py")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── About ─────────────────────────────────────────────────────────────
left, right = st.columns([3, 2])

with left:
    st.markdown(
        """
        <div class="about-section">
        <h4 style="margin-top:0">What is this?</h4>
        <p>
        This tool converts NYC's NOAH (Naturally Occurring Affordable Housing) database
        from PostgreSQL into a <strong>Neo4j knowledge graph</strong>, enabling
        relationship-centric queries that are cumbersome in traditional SQL.
        </p>
        <p>
        Each housing project is linked to its ZIP code, census tract, and
        affordability metrics. ZIP codes are connected to their geographic
        neighbors via shared boundaries.
        </p>
        <p style="margin-bottom:0">
        Ask questions in plain English on the <strong>Ask</strong> page,
        explore pre-built charts on <strong>Insights</strong>, or write
        Cypher queries directly on <strong>Explore</strong>.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.markdown("**Graph schema**")
    st.markdown(
        """
        <div style="font-size:0.85rem;line-height:2.2">
        <b style="color:#555;font-size:0.7rem;text-transform:uppercase;letter-spacing:.05em">Nodes</b><br>
        <span class="schema-node">HousingProject</span>
        <span class="schema-node">ZipCode</span>
        <span class="schema-node">AffordabilityAnalysis</span>
        <span class="schema-node">RentBurden</span>
        <br><br>
        <b style="color:#555;font-size:0.7rem;text-transform:uppercase;letter-spacing:.05em">Relationships</b><br>
        <span class="schema-rel">LOCATED_IN_ZIP</span>
        <span class="schema-rel">NEIGHBORS</span>
        <span class="schema-rel">IN_CENSUS_TRACT</span>
        <span class="schema-rel">CONTAINS_TRACT</span>
        <span class="schema-rel">HAS_AFFORDABILITY_DATA</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")
    st.markdown("**Data source**")
    st.caption(
        "NYC Department of Housing Preservation & Development (HPD). "
        "PostGIS → Neo4j migration via automated schema interpreter."
    )
