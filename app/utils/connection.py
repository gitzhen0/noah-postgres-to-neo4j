"""
Shared Neo4j connection utilities for the Streamlit app.
All pages import from here to get a single cached driver.
"""

import sys
from pathlib import Path

import streamlit as st

# Resolve project root so imports work regardless of cwd
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

from noah_converter.utils.config import load_config
from noah_converter.utils.db_connection import Neo4jConnection


@st.cache_resource(show_spinner=False)
def _get_driver():
    """Create and cache the Neo4j driver for the whole app session."""
    config = load_config()
    conn = Neo4jConnection(config.target_db)
    return conn.driver, config


def get_config():
    _, config = _get_driver()
    return config


def run_query(cypher: str, params: dict = None) -> list[dict]:
    """Execute a Cypher query and return a list of dicts."""
    driver, _ = _get_driver()
    with driver.session() as session:
        result = session.run(cypher, **(params or {}))
        return [dict(r) for r in result]


@st.cache_data(ttl=300, show_spinner=False)
def get_db_stats() -> dict:
    """Fetch and cache live graph statistics (5-minute TTL)."""
    try:
        stats: dict = {}
        for row in run_query(
            "MATCH (n) RETURN labels(n)[0] AS lbl, count(n) AS cnt"
        ):
            if row["lbl"]:
                stats[f"n_{row['lbl']}"] = row["cnt"]
        for row in run_query(
            "MATCH ()-[r]->() RETURN type(r) AS t, count(r) AS cnt"
        ):
            stats[f"r_{row['t']}"] = row["cnt"]
        return stats
    except Exception:
        return {}
