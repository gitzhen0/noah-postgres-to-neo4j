"""
NYC Housing Graph — Settings
"""

import sys
import os
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.theme import inject_theme
from utils.connection import get_config, get_db_stats

st.set_page_config(
    page_title="Settings — NYC Housing Graph",
    page_icon="⚙",
    layout="wide",
)
inject_theme()

with st.sidebar:
    st.markdown(
        '<span class="sidebar-brand">NYC Housing <span>Graph</span></span>',
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="page-header">
      <div class="page-title">Settings</div>
      <div class="page-sub">API key and connection configuration</div>
    </div>
    """,
    unsafe_allow_html=True,
)

cfg_col, status_col = st.columns([3, 2])

# ── Left: API key ─────────────────────────────────────────────────────
with cfg_col:
    st.markdown("#### Anthropic API Key")
    st.caption(
        "Required for natural language queries on the **Ask** page. "
        "Stored in session only — never written to disk."
    )

    # Pre-fill from env if available and nothing already set
    if "api_key" not in st.session_state:
        st.session_state["api_key"] = os.environ.get("ANTHROPIC_API_KEY", "")

    api_input = st.text_input(
        "api_key",
        value=st.session_state.get("api_key", ""),
        type="password",
        placeholder="sk-ant-...",
        label_visibility="collapsed",
    )

    save_col, clear_col, _ = st.columns([1, 1, 3])
    with save_col:
        if st.button("Save", type="primary", use_container_width=True):
            if api_input.strip():
                st.session_state["api_key"] = api_input.strip()
                st.markdown(
                    '<div class="success-msg">Key saved for this session.</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.warning("Enter a valid key.")
    with clear_col:
        if st.button("Clear", use_container_width=True):
            st.session_state.pop("api_key", None)
            st.info("Key cleared.")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    st.markdown("#### Neo4j Connection")
    st.caption("Configured via `config/config.yaml`. Restart the app to apply changes.")

    try:
        config = get_config()
        st.markdown(
            f"""
            | | |
            |---|---|
            | **URI** | `{config.target_db.uri}` |
            | **Database** | `{config.target_db.database}` |
            | **User** | `{config.target_db.user}` |
            """,
            unsafe_allow_html=False,
        )
    except Exception as e:
        st.error(f"Could not load config: {e}")

# ── Right: Connection status ──────────────────────────────────────────
with status_col:
    st.markdown("#### Connection Status")

    # API key status
    if st.session_state.get("api_key"):
        key = st.session_state["api_key"]
        st.markdown(
            f'<div class="success-msg">API key configured: <code>{key[:8]}…</code></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="error-msg">No API key set.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")

    if st.button("Test Neo4j connection", use_container_width=True):
        with st.spinner("Testing…"):
            try:
                stats = get_db_stats()
                if stats:
                    st.markdown(
                        '<div class="success-msg">Connected to Neo4j.</div>',
                        unsafe_allow_html=True,
                    )
                    m1, m2 = st.columns(2)
                    m1.metric("Housing Projects", f"{stats.get('n_HousingProject', 0):,}")
                    m2.metric("ZIP Codes",        f"{stats.get('n_ZipCode', 0):,}")
                    m3, m4 = st.columns(2)
                    m3.metric("Census Tracts",    f"{stats.get('n_RentBurden', 0):,}")
                    m4.metric("Connections",      f"{sum(stats.get(f'r_{r}', 0) for r in ['LOCATED_IN_ZIP','NEIGHBORS','IN_CENSUS_TRACT','CONTAINS_TRACT','HAS_AFFORDABILITY_DATA']):,}")
                else:
                    st.warning("Connected but no data found.")
            except Exception as exc:
                st.error(f"Connection failed: {exc}")
