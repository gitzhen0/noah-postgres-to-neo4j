"""
NYC Housing Graph — Ask (Natural Language Query)
"""

import sys
import os
import time
from pathlib import Path

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.theme import inject_theme
from utils.connection import get_config, run_query

st.set_page_config(
    page_title="Ask — NYC Housing Graph",
    page_icon="🔍",
    layout="wide",
)
inject_theme()

# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<span class="sidebar-brand">NYC Housing <span>Graph</span></span>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    show_cypher = st.toggle("Show Cypher", value=True)
    show_explain = st.toggle("Show explanation", value=True)

    st.markdown("---")

    # History in sidebar
    if st.session_state.get("query_history"):
        st.markdown("**Recent**")
        for item in st.session_state["query_history"][:6]:
            icon = "✓" if item["ok"] else "✗"
            color = "#5CB85C" if item["ok"] else "#E05C5C"
            st.markdown(
                f'<div style="font-size:0.78rem;color:#AAA;margin:0.3rem 0;line-height:1.4">'
                f'<span style="color:{color}">{icon}</span> '
                f'{item["question"][:42]}{"…" if len(item["question"])>42 else ""}</div>',
                unsafe_allow_html=True,
            )

# ── Header ────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="page-header">
      <div class="page-title">Ask</div>
      <div class="page-sub">Query the housing knowledge graph in plain English</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Session state ─────────────────────────────────────────────────────
if "query_history" not in st.session_state:
    st.session_state["query_history"] = []
if "result" not in st.session_state:
    st.session_state["result"] = None

# ── API key ───────────────────────────────────────────────────────────
api_key = (
    st.session_state.get("api_key")
    or os.environ.get("ANTHROPIC_API_KEY")
)

if not api_key:
    st.markdown(
        '<div class="error-msg">⚠ No Anthropic API key found. '
        'Set it in <b>Settings</b> or export <code>ANTHROPIC_API_KEY</code>.</div>',
        unsafe_allow_html=True,
    )
    if st.button("Go to Settings →"):
        st.switch_page("pages/4_Settings.py")
    st.stop()

# ── Example chips ─────────────────────────────────────────────────────
EXAMPLES = [
    ("By borough",    "How many housing projects are in each borough?"),
    ("Rent burden",   "Which ZIP codes in Brooklyn have the highest rent burden?"),
    ("Neighbors",     "Find housing projects in ZIP codes neighboring 10001"),
    ("High burden",   "Show census tracts with severe rent burden above 40%"),
    ("Affordability", "Which ZIP codes have the lowest rent burden rate?"),
    ("Income gap",    "Compare median income across Manhattan ZIP codes"),
]

ex_cols = st.columns(len(EXAMPLES))
for col, (label, question) in zip(ex_cols, EXAMPLES):
    with col:
        if st.button(label, use_container_width=True, key=f"chip_{label}"):
            st.session_state["_pending"] = question

# ── Query input ───────────────────────────────────────────────────────
default_q = st.session_state.pop(
    "_pending",
    st.session_state.pop("pending_query", ""),
)

question = st.text_area(
    "question",
    value=default_q,
    placeholder="e.g. Which neighborhoods have the most affordable housing?",
    height=88,
    label_visibility="collapsed",
)

btn_col, _, _ = st.columns([1, 1, 4])
with btn_col:
    submitted = st.button("Search →", type="primary", use_container_width=True)

# ── Execute ───────────────────────────────────────────────────────────
if submitted and question.strip():
    try:
        from noah_converter.text2cypher import Text2CypherTranslator
        from noah_converter.utils.db_connection import Neo4jConnection

        config = get_config()
        neo4j_conn = Neo4jConnection(config.target_db)

        with st.spinner(""):
            translator = Text2CypherTranslator(
                neo4j_conn=neo4j_conn,
                llm_provider="claude",
                api_key=api_key,
                model=config.text2cypher.model,
            )
            t0 = time.time()
            result = translator.query(
                question=question,
                execute=True,
                explain=show_explain,
            )
            result["elapsed"] = round(time.time() - t0, 2)

        neo4j_conn.close()
        st.session_state["result"] = result
        st.session_state["result_question"] = question

        st.session_state["query_history"].insert(0, {
            "question": question,
            "cypher": result.get("cypher", ""),
            "rows": len(result.get("results") or []),
            "ok": not result.get("error"),
        })

    except Exception as exc:
        st.session_state["result"] = {"error": str(exc), "question": question}
        st.session_state["result_question"] = question

# ── Display results ───────────────────────────────────────────────────
result = st.session_state.get("result")
if result:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    if result.get("error"):
        st.markdown(
            f'<div class="error-msg">⚠ {result["error"]}</div>',
            unsafe_allow_html=True,
        )
    else:
        rows = result.get("results") or []
        elapsed = result.get("elapsed", 0)

        # ── Cypher ────────────────────────────────────────────────────
        if show_cypher and result.get("cypher"):
            with st.expander("Cypher query", expanded=False):
                st.markdown(
                    f'<div class="cypher-block">{result["cypher"]}</div>',
                    unsafe_allow_html=True,
                )

        # ── Table ─────────────────────────────────────────────────────
        if rows:
            df = pd.DataFrame(rows)

            meta_col, dl_col = st.columns([4, 1])
            with meta_col:
                st.markdown(
                    f'<div class="result-meta">'
                    f'{len(rows)} result{"s" if len(rows)!=1 else ""}'
                    f' &nbsp;·&nbsp; {elapsed}s'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with dl_col:
                st.download_button(
                    "↓ CSV",
                    df.to_csv(index=False),
                    file_name="results.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            st.dataframe(df, use_container_width=True, hide_index=True)

            # Auto bar chart: first text col + first numeric col, ≤ 30 rows
            num_cols = df.select_dtypes("number").columns.tolist()
            txt_cols = df.select_dtypes("object").columns.tolist()
            if num_cols and txt_cols and 2 <= len(df) <= 30:
                try:
                    import plotly.express as px

                    fig = px.bar(
                        df,
                        x=txt_cols[0],
                        y=num_cols[0],
                        color_discrete_sequence=["#C1440E"],
                        template="plotly_white",
                        text=num_cols[0],
                    )
                    fig.update_traces(textposition="outside")
                    fig.update_layout(
                        height=300,
                        margin=dict(t=16, b=0, l=0, r=0),
                        xaxis_title="",
                        yaxis_title=num_cols[0],
                        font_family="Inter",
                        plot_bgcolor="#F9F7F4",
                        paper_bgcolor="#F9F7F4",
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception:
                    pass
        else:
            st.info("No results found for this query.")

        # ── Explanation ────────────────────────────────────────────────
        if show_explain and result.get("explanation"):
            st.markdown(
                f'<div class="answer-box">{result["explanation"]}</div>',
                unsafe_allow_html=True,
            )
