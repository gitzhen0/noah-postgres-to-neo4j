"""
Shared Streamlit CSS — warm orange-red palette, low AI feel.
"""

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Global ─────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.stApp { background: #F9F7F4; }
#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar ────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #1A1A1A !important;
    border-right: none !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown { color: #BEBEBE !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #FFFFFF !important; }
[data-testid="stSidebarNav"] a { color: #BEBEBE !important; font-size: 0.875rem; }
[data-testid="stSidebarNav"] a:hover,
[data-testid="stSidebarNav"] [aria-selected="true"] {
    color: #F4A261 !important;
    background: rgba(244,162,97,0.08) !important;
    border-radius: 6px;
}

/* ── Buttons ────────────────────────────────────────────────── */
.stButton > button[kind="primary"] {
    background: #C1440E !important;
    border: none !important;
    color: #fff !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    letter-spacing: 0.01em;
    transition: background 0.18s ease !important;
    padding: 0.45rem 1.4rem !important;
}
.stButton > button[kind="primary"]:hover { background: #D9541A !important; }
.stButton > button:not([kind="primary"]) {
    border: 1.5px solid #DDD8D2 !important;
    color: #444 !important;
    background: #fff !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}
.stButton > button:not([kind="primary"]):hover {
    border-color: #C1440E !important;
    color: #C1440E !important;
    background: #FEF1EB !important;
}

/* ── Inputs ─────────────────────────────────────────────────── */
textarea, input[type="text"], input[type="password"], input[type="number"] {
    border-radius: 8px !important;
    border-color: #DDD8D2 !important;
    background: #fff !important;
}
textarea:focus, input:focus {
    border-color: #C1440E !important;
    box-shadow: 0 0 0 2px rgba(193,68,14,0.1) !important;
}

/* ── Metrics ────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #fff;
    border: 1px solid #EDE8E3;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
[data-testid="stMetricValue"]  { color: #C1440E !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"]  {
    color: #999 !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    font-weight: 500 !important;
}

/* ── Tabs ───────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] { border-bottom: 2px solid #EDE8E3; gap: 0; }
.stTabs [data-baseweb="tab"]      { font-weight: 500; color: #999; padding: 0.55rem 1.2rem; border-radius: 0; }
.stTabs [aria-selected="true"]    { color: #C1440E !important; border-bottom: 2px solid #C1440E !important; }

/* ── Expanders ──────────────────────────────────────────────── */
[data-testid="stExpander"] { border: 1px solid #EDE8E3; border-radius: 10px; overflow: hidden; }
[data-testid="stExpander"] summary { font-weight: 500; color: #444; }

/* ── DataFrames / tables ────────────────────────────────────── */
[data-testid="stDataFrame"] { border-radius: 10px; border: 1px solid #EDE8E3; overflow: hidden; }

/* ── Selectbox ──────────────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div {
    border-radius: 8px !important;
    border-color: #DDD8D2 !important;
}

/* ── Toggle ─────────────────────────────────────────────────── */
[data-testid="stCheckbox"] label { color: #444 !important; }

/* ────────────────────────────────────────────────────────────── */
/* Custom utility classes                                         */
/* ────────────────────────────────────────────────────────────── */

.page-header {
    padding: 0.25rem 0 1.25rem;
    border-bottom: 1px solid #EDE8E3;
    margin-bottom: 1.5rem;
}
.page-title  { font-size: 1.65rem; font-weight: 700; color: #1A1A1A; margin: 0; }
.page-sub    { font-size: 0.875rem; color: #999; margin-top: 0.2rem; }

.stat-card {
    background: #fff;
    border: 1px solid #EDE8E3;
    border-radius: 12px;
    padding: 1.1rem 1.4rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    height: 100%;
}
.stat-val {
    font-size: 1.9rem;
    font-weight: 700;
    color: #C1440E;
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
}
.stat-lbl {
    font-size: 0.7rem;
    color: #AAA;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-top: 0.3rem;
}
.stat-hint { font-size: 0.75rem; color: #CCC; margin-top: 0.15rem; }

.divider { height: 1px; background: #EDE8E3; margin: 1.25rem 0; }

.cypher-block {
    background: #1E1E1E;
    color: #D4D4D4;
    border-radius: 8px;
    padding: 1rem 1.25rem;
    font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
    font-size: 0.82rem;
    line-height: 1.65;
    overflow-x: auto;
    border-left: 3px solid #C1440E;
    white-space: pre;
}

.answer-box {
    background: #FFFBF7;
    border: 1px solid #F4C5AE;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    color: #3D2B1F;
    line-height: 1.7;
    font-size: 0.93rem;
}

.result-meta { font-size: 0.78rem; color: #AAA; margin-bottom: 0.4rem; }

.schema-node {
    display: inline-block;
    background: #EBF3FF;
    color: #1A5FAD;
    border-radius: 5px;
    padding: 0.12rem 0.55rem;
    font-size: 0.8rem;
    font-weight: 600;
    font-family: monospace;
    margin: 0.15rem;
}
.schema-rel {
    display: inline-block;
    background: #F2EEFF;
    color: #6B21A8;
    border-radius: 5px;
    padding: 0.12rem 0.55rem;
    font-size: 0.8rem;
    font-weight: 600;
    font-family: monospace;
    margin: 0.15rem;
}

.error-msg {
    background: #FFF2F2;
    border: 1px solid #FFCDD2;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    color: #B71C1C;
    font-size: 0.88rem;
    margin: 0.5rem 0;
}
.success-msg {
    background: #F1F8F1;
    border: 1px solid #C8E6C9;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    color: #1B5E20;
    font-size: 0.88rem;
    margin: 0.5rem 0;
}

.sidebar-brand {
    font-size: 1.05rem;
    font-weight: 700;
    color: #FFF !important;
    letter-spacing: -0.01em;
    padding: 0.3rem 0 0.6rem;
    display: block;
}
.sidebar-brand span { color: #F4A261; }

.quick-search {
    background: #fff;
    border: 1.5px solid #EDE8E3;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin: 0.75rem 0 1.25rem;
}

.about-section {
    background: #fff;
    border: 1px solid #EDE8E3;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
}
</style>
"""


def inject_theme():
    import streamlit as st
    st.markdown(THEME_CSS, unsafe_allow_html=True)
