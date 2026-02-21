"""
NYC Housing Graph — Insights (Pre-built data visualizations)
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.theme import inject_theme
from utils.connection import run_query

st.set_page_config(
    page_title="Insights — NYC Housing Graph",
    page_icon="📊",
    layout="wide",
)
inject_theme()

ORANGE   = "#C1440E"
ORANGE2  = "#E8581A"
TAN      = "#F4A261"
PALETTE  = ["#C1440E", "#E8581A", "#F4A261", "#FFD6B5", "#6B4B3E"]

with st.sidebar:
    st.markdown(
        '<span class="sidebar-brand">NYC Housing <span>Graph</span></span>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.caption("Pre-built visualizations pulled live from the graph database.")

st.markdown(
    """
    <div class="page-header">
      <div class="page-title">Insights</div>
      <div class="page-sub">
        Housing affordability patterns across New York City's five boroughs
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ────────────────────────────────────────────────────────────────────
# Helper: run a cached query and return a DataFrame
# ────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def _q(cypher: str) -> pd.DataFrame:
    rows = run_query(cypher)
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ── Section 1: Projects by borough ───────────────────────────────────
st.markdown("#### Housing Projects by Borough")

df_borough = _q("""
    MATCH (p:HousingProject)
    RETURN p.borough          AS borough,
           count(p)           AS projects,
           sum(p.total_units) AS total_units
    ORDER BY projects DESC
""")

if not df_borough.empty:
    df_borough["total_units"] = df_borough["total_units"].fillna(0).astype(int)

    tbl_col, chart_col = st.columns([1, 2])

    with tbl_col:
        st.dataframe(
            df_borough.rename(columns={
                "borough": "Borough",
                "projects": "Projects",
                "total_units": "Total Units",
            }),
            use_container_width=True,
            hide_index=True,
        )

    with chart_col:
        fig = px.bar(
            df_borough,
            x="borough", y="projects",
            color="borough",
            color_discrete_sequence=PALETTE,
            template="plotly_white",
            text="projects",
            labels={"projects": "Projects", "borough": ""},
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            showlegend=False,
            height=280,
            margin=dict(t=10, b=0, l=0, r=0),
            font_family="Inter",
            plot_bgcolor="#F9F7F4",
            paper_bgcolor="#F9F7F4",
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Section 2: Rent burden & income by borough ────────────────────────
st.markdown("#### Rent Burden & Median Income by Borough")
st.caption("Average across ZIP codes with affordability data")

df_burden = _q("""
    MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
    WHERE a.rent_burden_rate IS NOT NULL
    RETURN z.borough                      AS borough,
           avg(a.rent_burden_rate) * 100  AS avg_rent_burden_pct,
           avg(a.severe_burden_rate) * 100 AS avg_severe_burden_pct,
           avg(a.median_income_usd)       AS avg_income,
           count(z)                       AS zip_count
    ORDER BY avg_rent_burden_pct DESC
""")

if not df_burden.empty:
    df_burden["avg_rent_burden_pct"]    = df_burden["avg_rent_burden_pct"].round(1)
    df_burden["avg_severe_burden_pct"]  = df_burden["avg_severe_burden_pct"].round(1)
    df_burden["avg_income"]             = df_burden["avg_income"].round(0).fillna(0).astype(int)

    b1, b2 = st.columns(2)

    with b1:
        fig2 = px.bar(
            df_burden,
            x="borough", y="avg_rent_burden_pct",
            color_discrete_sequence=[ORANGE],
            template="plotly_white",
            text="avg_rent_burden_pct",
            labels={"avg_rent_burden_pct": "Avg rent burden (%)"},
        )
        fig2.update_traces(texttemplate="%{text}%", textposition="outside")
        fig2.update_layout(
            height=280, showlegend=False,
            margin=dict(t=10, b=0, l=0, r=0),
            xaxis_title="",
            font_family="Inter",
            plot_bgcolor="#F9F7F4",
            paper_bgcolor="#F9F7F4",
        )
        st.caption("% of households spending >30% of income on rent")
        st.plotly_chart(fig2, use_container_width=True)

    with b2:
        fig3 = px.bar(
            df_burden,
            x="borough", y="avg_income",
            color_discrete_sequence=[TAN],
            template="plotly_white",
            text="avg_income",
            labels={"avg_income": "Avg median income ($)"},
        )
        fig3.update_traces(texttemplate="$%{text:,}", textposition="outside")
        fig3.update_layout(
            height=280, showlegend=False,
            margin=dict(t=10, b=0, l=0, r=0),
            xaxis_title="",
            font_family="Inter",
            plot_bgcolor="#F9F7F4",
            paper_bgcolor="#F9F7F4",
        )
        st.caption("Average ZIP-level median household income")
        st.plotly_chart(fig3, use_container_width=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Section 3: Top ZIPs by project count ──────────────────────────────
st.markdown("#### Top 25 ZIP Codes by Housing Projects")

df_zips = _q("""
    MATCH (p:HousingProject)-[:LOCATED_IN_ZIP]->(z:ZipCode)
    RETURN z.zip_code         AS zip_code,
           z.borough          AS borough,
           count(p)           AS projects,
           sum(p.total_units) AS total_units
    ORDER BY projects DESC
    LIMIT 25
""")

if not df_zips.empty:
    df_zips["total_units"] = df_zips["total_units"].fillna(0).astype(int)
    df_zips["label"] = df_zips["zip_code"] + " (" + df_zips["borough"].str[:3] + ")"

    fig4 = px.bar(
        df_zips.sort_values("projects"),
        x="projects", y="label",
        orientation="h",
        color="borough",
        color_discrete_sequence=PALETTE,
        template="plotly_white",
        labels={"projects": "Housing Projects", "label": ""},
    )
    fig4.update_layout(
        height=520,
        margin=dict(t=10, b=0, l=0, r=0),
        font_family="Inter",
        legend_title="Borough",
        plot_bgcolor="#F9F7F4",
        paper_bgcolor="#F9F7F4",
    )
    st.plotly_chart(fig4, use_container_width=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Section 4: Income vs Rent Burden scatter ───────────────────────────
st.markdown("#### Income vs. Rent Burden")
st.caption(
    "Each bubble is a ZIP code. "
    "Bubble size = number of housing projects. "
    "Hover for details."
)

df_scatter = _q("""
    MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
    OPTIONAL MATCH (p:HousingProject)-[:LOCATED_IN_ZIP]->(z)
    WITH z, a, count(p) AS project_count
    WHERE a.median_income_usd IS NOT NULL
      AND a.rent_burden_rate  IS NOT NULL
    RETURN z.zip_code                   AS zip_code,
           z.borough                    AS borough,
           a.median_income_usd          AS median_income,
           a.rent_burden_rate  * 100    AS rent_burden_pct,
           a.severe_burden_rate * 100   AS severe_burden_pct,
           project_count
""")

if not df_scatter.empty:
    df_scatter["project_count"]     = df_scatter["project_count"].fillna(0).astype(int)
    df_scatter["rent_burden_pct"]   = df_scatter["rent_burden_pct"].round(1)
    df_scatter["severe_burden_pct"] = df_scatter["severe_burden_pct"].round(1)

    fig5 = px.scatter(
        df_scatter,
        x="median_income",
        y="rent_burden_pct",
        color="borough",
        size="project_count",
        size_max=28,
        hover_data=["zip_code", "severe_burden_pct", "project_count"],
        color_discrete_sequence=PALETTE,
        template="plotly_white",
        labels={
            "median_income":   "Median Household Income ($)",
            "rent_burden_pct": "Rent Burden (%)",
            "borough":         "Borough",
        },
    )
    # Reference line at 30% burden
    fig5.add_hline(
        y=30,
        line_dash="dot",
        line_color="#AAA",
        annotation_text="30% burden threshold",
        annotation_position="right",
    )
    fig5.update_layout(
        height=420,
        margin=dict(t=10, b=0, l=0, r=0),
        font_family="Inter",
        plot_bgcolor="#F9F7F4",
        paper_bgcolor="#F9F7F4",
    )
    st.plotly_chart(fig5, use_container_width=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Section 5: Rent burden distribution histogram ──────────────────────
st.markdown("#### Distribution of ZIP-Level Rent Burden")

df_hist = _q("""
    MATCH (z:ZipCode)-[:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
    WHERE a.rent_burden_rate IS NOT NULL
    RETURN z.borough           AS borough,
           a.rent_burden_rate * 100 AS rent_burden_pct
""")

if not df_hist.empty:
    fig6 = px.histogram(
        df_hist,
        x="rent_burden_pct",
        color="borough",
        nbins=20,
        opacity=0.75,
        barmode="overlay",
        color_discrete_sequence=PALETTE,
        template="plotly_white",
        labels={"rent_burden_pct": "Rent Burden (%)", "count": "ZIP Codes"},
    )
    fig6.add_vline(
        x=30,
        line_dash="dot",
        line_color="#444",
        annotation_text="30%",
    )
    fig6.update_layout(
        height=300,
        margin=dict(t=10, b=0, l=0, r=0),
        font_family="Inter",
        legend_title="Borough",
        plot_bgcolor="#F9F7F4",
        paper_bgcolor="#F9F7F4",
    )
    st.plotly_chart(fig6, use_container_width=True)
