"""
Parse a Cypher query's MATCH patterns and render a Graphviz path diagram.
"""

import re

# Node label → fill colour (hex)
_NODE_COLORS = {
    "HousingProject":        "#C1440E",
    "ZipCode":               "#3A86FF",
    "AffordabilityAnalysis": "#2DC653",
    "RentBurden":            "#9B59B6",
}
_DEFAULT_COLOR = "#888888"


def cypher_to_dot(cypher: str) -> str | None:
    """
    Extract MATCH/OPTIONAL MATCH patterns from *cypher* and return a
    Graphviz DOT string, or None if no node–rel–node patterns are found.

    Handles:
      (alias:Label {props})-[:REL]->(alias:Label)   directed
      (alias:Label)-[:REL]-(alias:Label)             undirected
      chained: (a:A)-[:R1]->(b:B)-[:R2]->(c:C)
    """
    # Normalise whitespace
    text = re.sub(r"\s+", " ", cypher)

    # ── Extract all MATCH / OPTIONAL MATCH clause bodies ─────────────
    # Stop at WHERE / RETURN / WITH / ORDER / LIMIT
    clause_re = re.compile(
        r"(?:OPTIONAL\s+)?MATCH\s+(.*?)(?=\s+(?:OPTIONAL\s+)?MATCH|\s+WHERE|\s+RETURN|\s+WITH|\s+ORDER|\s+LIMIT|$)",
        re.IGNORECASE,
    )
    clauses = [m.group(1) for m in clause_re.finditer(text)]

    # ── Pattern: node-rel-node ────────────────────────────────────────
    # Node token:  (\w*(?::\w+)?(?:\s*\{[^}]*\})?)
    # Captures the *first* label after ':', ignoring alias and props
    node_tok = r"\(\s*\w*(?::(\w+))?(?:\s*\{[^}]*\})?\s*\)"
    rel_tok  = r"-\[:(\w+)\](-?>|-)"

    # Build a single pattern that captures from/rel/dir/to
    seg_re = re.compile(node_tok + r"\s*" + rel_tok + r"\s*" + node_tok)

    edges: list[tuple[str, str, str, bool]] = []   # (from, rel, to, directed)
    seen_nodes: set[str] = set()

    for clause in clauses:
        pos = 0
        while True:
            m = seg_re.search(clause, pos)
            if not m:
                break
            from_label = m.group(1) or "?"
            rel_type   = m.group(2)
            arrow      = m.group(3)      # "->" or "-"
            to_label   = m.group(4) or "?"
            directed   = arrow.endswith(">")

            if from_label != "?" and rel_type and to_label != "?":
                edges.append((from_label, rel_type, to_label, directed))
                seen_nodes.add(from_label)
                seen_nodes.add(to_label)

            # Advance past the *to* node so chained patterns are captured
            pos = m.end() - len(m.group(0).split(")")[-1]) - 1
            if pos <= m.start():
                pos = m.end()

    if not edges:
        return None

    # ── Build DOT ─────────────────────────────────────────────────────
    lines = [
        "digraph G {",
        "  rankdir=LR;",
        "  graph [bgcolor=transparent];",
        '  node [shape=roundedbox, style="filled,rounded", fontname="Helvetica", fontsize=11];',
        '  edge [fontname="Helvetica", fontsize=9, color="#555555"];',
    ]

    for label in seen_nodes:
        color    = _NODE_COLORS.get(label, _DEFAULT_COLOR)
        fc       = "white"
        lines.append(
            f'  "{label}" [label=":{label}", fillcolor="{color}", fontcolor="{fc}"];'
        )

    seen_edges: set[tuple] = set()
    for from_l, rel, to_l, directed in edges:
        key = (from_l, rel, to_l)
        if key in seen_edges:
            continue
        seen_edges.add(key)
        arrow = "normal" if directed else "none"
        lines.append(
            f'  "{from_l}" -> "{to_l}" [label="{rel}", arrowhead={arrow}];'
        )

    lines.append("}")
    return "\n".join(lines)
