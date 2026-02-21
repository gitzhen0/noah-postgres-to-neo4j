"""
NYC Housing Graph — Explore (Cypher Editor + Schema Reference + Saved Queries)
"""

import sys
import time
from pathlib import Path

import tempfile
import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.theme import inject_theme
from utils.connection import run_query
from utils.saved_queries import list_saved, save_query, delete_query

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
      <div class="page-sub">Cypher query editor · schema reference · saved queries</div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_editor, tab_graph, tab_saved, tab_schema = st.tabs(
    ["Query Editor", "Graph View", "Saved Queries", "Schema Reference"]
)

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

    ex_col, _, load_col, __ = st.columns([3, 0.2, 1, 2])
    with ex_col:
        selected = st.selectbox("Load example:", list(EXAMPLES.keys()), label_visibility="collapsed")
    with load_col:
        if st.button("Load →", use_container_width=True):
            st.session_state["cypher_editor"] = EXAMPLES[selected]

    # Seed default on first load
    if "cypher_editor" not in st.session_state:
        st.session_state["cypher_editor"] = EXAMPLES["Projects by borough"]

    cypher = st.text_area(
        "Cypher",
        height=170,
        label_visibility="collapsed",
        key="cypher_editor",
    )

    run_col, save_col, name_col, _spacer = st.columns([1, 1, 2, 2])
    with run_col:
        run_btn = st.button("Run ▶", type="primary", use_container_width=True)
    with name_col:
        save_name = st.text_input(
            "save_name",
            placeholder="Query name…",
            label_visibility="collapsed",
            key="save_name_input",
        )
    with save_col:
        if st.button("Save ★", use_container_width=True):
            name = save_name.strip() or f"Query {len(list_saved()) + 1}"
            save_query(name, cypher)
            st.toast(f'Saved "{name}"', icon="★")

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

# ── Tab 2: Graph View ─────────────────────────────────────────────────
with tab_graph:
    st.markdown("#### Visualize query results as an interactive network")
    st.caption(
        "Run a Cypher query that returns nodes and relationships — the graph will be "
        "rendered interactively. For best results keep the result set small (< 200 nodes)."
    )

    GRAPH_EXAMPLES = {
        "ZIP neighbors of 10001": """\
MATCH (z:ZipCode {zip_code: '10001'})-[r:NEIGHBORS]-(n:ZipCode)
RETURN z, r, n
LIMIT 20""",

        "Projects → ZIP (top 30 by units)": """\
MATCH (p:HousingProject)-[r:LOCATED_IN_ZIP]->(z:ZipCode)
WHERE p.total_units > 200
RETURN p, r, z
ORDER BY p.total_units DESC
LIMIT 30""",

        "ZIP → Affordability (Bronx)": """\
MATCH (z:ZipCode)-[r:HAS_AFFORDABILITY_DATA]->(a:AffordabilityAnalysis)
WHERE z.borough = 'Bronx'
RETURN z, r, a""",

        "Projects in high-burden tracts": """\
MATCH (p:HousingProject)-[r:IN_CENSUS_TRACT]->(t:RentBurden)
WHERE t.severe_burden_rate > 0.45
RETURN p, r, t
LIMIT 40""",
    }

    NODE_COLORS = {
        "HousingProject":        "#C1440E",
        "ZipCode":               "#3A86FF",
        "AffordabilityAnalysis": "#2DC653",
        "RentBurden":            "#9B59B6",
    }
    NODE_SIZES = {
        "HousingProject": 15,
        "ZipCode":        20,
        "AffordabilityAnalysis": 18,
        "RentBurden":     16,
    }

    gcol1, gcol2 = st.columns([3, 1])
    with gcol1:
        g_selected = st.selectbox("Graph example:", list(GRAPH_EXAMPLES.keys()),
                                  label_visibility="collapsed", key="g_ex_select")
    with gcol2:
        if st.button("Load →", key="g_load", use_container_width=True):
            st.session_state["graph_cypher"] = GRAPH_EXAMPLES[g_selected]

    if "graph_cypher" not in st.session_state:
        st.session_state["graph_cypher"] = GRAPH_EXAMPLES[list(GRAPH_EXAMPLES.keys())[0]]

    graph_cypher = st.text_area(
        "Graph Cypher",
        height=100,
        label_visibility="collapsed",
        key="graph_cypher",
        help="Query must RETURN node variables and relationship variables, e.g. RETURN p, r, z",
    )

    if st.button("Render Graph ▶", type="primary", key="g_run"):
        if not graph_cypher.strip():
            st.warning("Enter a Cypher query above.")
        else:
            try:
                from neo4j.graph import Node, Relationship
                from pyvis.network import Network

                with st.spinner("Fetching graph data…"):
                    from utils.connection import _get_driver
                    driver, _ = _get_driver()
                    with driver.session() as session:
                        result = session.run(graph_cypher)
                        records = list(result)

                if not records:
                    st.info("Query returned no results.")
                else:
                    net = Network(height="520px", width="100%",
                                  bgcolor="#F9F7F4", font_color="#333",
                                  notebook=False, directed=True)
                    net.barnes_hut(spring_length=120, spring_strength=0.04,
                                   damping=0.09, central_gravity=0.3)

                    added_nodes: set = set()
                    added_edges: set = set()

                    def _add_node(node: "Node") -> None:
                        if node.id in added_nodes:
                            return
                        label = list(node.labels)[0] if node.labels else "Node"
                        name = (
                            node.get("project_name")
                            or node.get("zip_code")
                            or node.get("geo_id")
                            or f"{label}#{node.id}"
                        )
                        color = NODE_COLORS.get(label, "#888")
                        size  = NODE_SIZES.get(label, 15)
                        tip = f"<b>:{label}</b><br>" + "<br>".join(
                            f"{k}: {v}" for k, v in dict(node).items()
                            if v is not None
                        )
                        net.add_node(
                            node.id, label=str(name)[:24],
                            color=color, size=size, title=tip,
                            font={"color": "white", "size": 11},
                        )
                        added_nodes.add(node.id)

                    for record in records:
                        for val in record.values():
                            if isinstance(val, Node):
                                _add_node(val)
                            elif isinstance(val, Relationship):
                                # Ensure both endpoint nodes exist before adding edge
                                _add_node(val.start_node)
                                _add_node(val.end_node)
                                eid = val.id
                                if eid not in added_edges:
                                    net.add_edge(
                                        val.start_node.id, val.end_node.id,
                                        label=val.type,
                                        color="#999", font={"size": 9},
                                        arrows="to",
                                    )
                                    added_edges.add(eid)

                    n_nodes = len(added_nodes)
                    n_edges = len(added_edges)

                    if n_nodes == 0:
                        st.warning(
                            "No graph objects found. Make sure your query returns "
                            "node/relationship variables (e.g. `RETURN p, r, z`), "
                            "not just properties."
                        )
                    else:
                        st.caption(f"{n_nodes} nodes · {n_edges} edges — drag to explore, scroll to zoom, hover for details")
                        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
                            net.save_graph(f.name)
                            html = open(f.name).read()
                        st.components.v1.html(html, height=540, scrolling=False)

            except Exception as e:
                st.error(f"Graph rendering error: {e}")

# ── Tab 3: Saved Queries ──────────────────────────────────────────────
with tab_saved:
    saved = list_saved()

    if not saved:
        st.info("No saved queries yet. Write a query in the editor and click Save ★.")
    else:
        st.caption(f"{len(saved)} saved {'query' if len(saved)==1 else 'queries'}")
        for q in saved:
            with st.expander(f"**{q['name']}** · {q['saved_at']}"):
                st.code(q["cypher"], language="cypher")
                load_btn, del_btn, _ = st.columns([1, 1, 4])
                with load_btn:
                    if st.button("Load into editor", key=f"load_{q['name']}"):
                        st.session_state["cypher_editor"] = q["cypher"]
                        st.toast(f'Loaded "{q["name"]}"')
                with del_btn:
                    if st.button("Delete", key=f"del_{q['name']}"):
                        delete_query(q["name"])
                        st.rerun()

# ── Tab 3: Schema Reference ───────────────────────────────────────────
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
