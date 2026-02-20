**Briefing: Why the NOAH Knowledge Graph + Interface Matters for Urban
Lab**

**1) The point of the Knowledge Graph**

Urban Lab already has value from NOAH as a relational database (RDBMS):
it supports **tabular facts, filters, and standard reporting**. The
Knowledge Graph (KG) is a complementary layer that makes it easy to ask
and answer **relationship questions** that are awkward, slow, or
impractical in SQL---especially when the question requires multiple
"hops" across entities (building → owner → LLC → agent → other buildings
→ neighborhood adjacency, etc.).

Put simply:

- **RDBMS** = "facts in tables"

- **KG** = "facts + relationships as first-class objects"

The KG is not a replacement for NOAH. It's an **extension** that turns
NOAH into a system that can support network discovery, multi-hop
queries, and graph analytics.

**2) Why the interface is as important as the conversion code**

A KG is only valuable to the client if they can **use it without
learning graph query languages** (Cypher/SPARQL) and without constantly
relying on the student team.

Urban Lab's real need is not "a graph database." Their need is:

- to **ask high-impact questions quickly**

- to **explore connections and explain results**

- to **repeat analyses reliably** (saved queries, templates)

- to **share outputs** (tables, maps, network views) for research,
  policy, and communication

So: conversion code delivers the KG technically, but the interface is
what makes it **adoptable** and **useful**.

**3) What Urban Lab can do with a KG that they cannot do easily with the
RDBMS**

The "wow" comes from questions that have a natural graph form:

**A. Multi-hop relationship queries (path queries)**

- "Show buildings connected to Owner X through LLC chains within 2--3
  hops."

- "Which buildings are linked through the same registered
  agent/manager?"

- "What is the relationship path that connects this building to
  known-risk portfolios?"

**B. Spatial adjacency as a relationship**

- "Show buildings in ZIPs/tracts adjacent to a target area with rising
  violations."

- "Identify spillover: changes in one area followed by correlated
  changes in neighboring areas."

**C. Pattern matching ("find this shape in the data")**

- "Find the pattern: high violations → ownership transfer → rent
  increases → eviction uptick."

- "Find buildings that match the same relationship pattern as a known
  set of problem buildings."

**D. Graph analytics**

- "Which entities are most central in the ownership--building network
  (and why)?"

- "What clusters of buildings behave like portfolios?"

**4) Interface goals (what the UI must enable)**

The UI must let Urban Lab do four things:

1.  **Ask** common questions without writing code

2.  **Explore** connections visually (and drill down)

3.  **Explain** results ("why did this show up?" with paths/provenance)

4.  **Export/share** results (CSV tables; map layers; saved queries)

If the UI doesn't support those four, the KG will remain a "cool
backend" that is rarely used.

**5) Recommended UI approach: start template-driven, add exploration**

The best adoption path is usually:

**Phase 1 (MVP): "Question Library" (templates)**

A small set of parameterized queries with dropdowns and sliders:

- choose geography (ZIP/tract/borough)

- choose timeframe

- choose indicator sets (violations, evictions, rent burden, etc.)

- choose relationship depth (1--3 hops)

This avoids requiring Cypher and keeps results consistent and
repeatable.

**Phase 2: "Explorer" mode**

For analysts: a more flexible view with

- filters + table + map

- a "connections panel" to show relationships and multi-hop paths

**Phase 3 (optional): Natural language with guardrails**

Natural language is demo-friendly, but should be constrained to
validated templates to avoid incorrect queries and misleading results.

**6) Minimum viable interface features (what you should build first)**

To make the KG immediately useful, the first release should include:

1.  **Entity search** (building address / BBL / owner name / LLC /
    manager)

2.  **Connection query** ("show related entities within N hops")

3.  **Adjacency query** (neighbor ZIP/tract exploration)

4.  **Explain panel** (display the relationship path and data sources
    used)

5.  **Export** (CSV for tables; ideally GeoJSON for map layers)

6.  **Saved queries** (bookmark templates + parameters)

**7) Suggested MVP "Top 5" templates**

These five templates create immediate value and demonstrate why the KG
exists:

1.  **Connected-to**: "Find buildings connected to X
    (owner/agent/manager) within N hops."

2.  **Neighborhood spillover**: "Compare a target ZIP/tract to adjacent
    areas on selected indicators."

3.  **Portfolio discovery**: "Find clusters of buildings sharing
    ownership/control signals."

4.  **Risk pattern match**: "Find buildings matching a selected risk
    relationship pattern."

5.  **Explainability**: "Why is this building flagged? Show paths +
    contributing indicators."

**8) What "success" looks like for Urban Lab**

The project is successful if Urban Lab staff can:

- answer 80% of their recurring relationship questions in minutes,

- generate defensible outputs (with explainability),

- share results with colleagues and stakeholders,

- and do it without asking the student team for custom queries.

**9) What you (students) should produce as deliverables**

**Technical**

- Graph model (node/edge types + properties)

- ETL conversion pipeline from NOAH RDBMS → KG

- Basic performance benchmarks for 1-hop / 2-hop / 3-hop queries

**Product**

- 5-template MVP UI ("Question Library")

- Explorer page (even if limited)

- Explainability view (path display)

- Export function

- A short user guide ("How Urban Lab uses this")
