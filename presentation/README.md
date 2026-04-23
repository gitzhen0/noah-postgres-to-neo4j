# Final Presentation · Speaker guide

18 HTML slides, zero external dependencies, designed for a 25–30 minute
Zoom defense of the capstone. Embeds three live Streamlit demos via `<iframe>`
so you never leave the deck.

## How to open

```bash
open presentation/index.html
# or
firefox presentation/index.html
```

Any modern browser works (Chrome, Safari, Firefox, Edge). The deck is a single
`index.html` with inline CSS, JS, and SVG — copy it anywhere, it still works.

## Keyboard shortcuts

| Key | Action |
|---|---|
| `→` `Space` `PgDn` | Next slide |
| `←` `PgUp` | Previous slide |
| `Home` / `End` | First / last |
| `Esc` | Overview grid (click to jump) |
| `F` | Fullscreen |
| `N` or `S` | Toggle speaker notes panel |
| `?` or `H` | Help |

Deck position is persisted in `localStorage` and in the URL hash
(`index.html#5` opens slide 5). Safe to close the tab mid-rehearsal.

## Before the Zoom call — run the preflight

```bash
bash presentation/pre-demo-check.sh
```

It checks:
- Docker daemon running, both `noah-pg-*` and `noah-neo4j-*` containers healthy
- PostgreSQL reachable and row counts match (8,604 / 177 / 176 / etc.)
- Neo4j reachable and node/edge counts match the deck numbers
- Streamlit responds on `:8505` including `/Ask` and `/Explore` sub-pages
- Three frozen JSON artifacts (`audit_report`, `benchmark_report`, `performance_report`) present and valid
- `ANTHROPIC_API_KEY` available (needed for Text2Cypher demo)

Exit 0 = ready to go. Exit 1 = something to fix, with remediation hints.

## Recommended browser setup (5 min before going live)

Pin these **six** tabs in this exact order in Chrome, left to right:

1. `file:///…/presentation/index.html` — the deck
2. `http://localhost:7474` — **NOAH Neo4j Browser (slide 7 before/after demo)**
3. `http://localhost:8505` — Streamlit Home (just in case)
4. `http://localhost:8505/Ask` — Demo 2 live fallback
5. `http://localhost:8505/Explore` — Demo 3 live fallback
6. `http://localhost:7475` — **Demo Neo4j Browser (slide 14 agnostic demo)**

If the iframes embedded inside slides 9 and 11 don't load (some browsers block
`localhost` iframes from `file://` origins), click over to the pinned Streamlit
tabs — the keyboard shortcut `Cmd+Option+→` jumps to the next tab on macOS.

## Slide 7 — Neo4j Browser choreography (IMPORTANT)

Slide 7 is redesigned as a **3-step choreography**: show the empty database,
run the migration, then show it full. You need Neo4j Browser pre-warmed.

**Before the call:**

1. Open the Neo4j Browser tab and log in (`neo4j` / `password123`)
2. Paste each of the 4 queries from
   [`neo4j-browser-cheatsheet.md`](neo4j-browser-cheatsheet.md) into Favorites
   (⭐ icon in left sidebar)
3. Run the "Clear" favorite (`MATCH (n) DETACH DELETE n`) so the graph is empty

**During the demo (slide 7):**

| Step | Tab | Action | Shown |
|---|---|---|---|
| 1 | Neo4j Browser | Click the Count favorite | `total_nodes: 0` |
| 2 | Terminal | `python main.py migrate` + `audit` | ~10 s |
| 3 | Neo4j Browser | ↑ + Enter (reruns count) | `total_nodes: 11,183` |
| 3b | Neo4j Browser | Click the `LIMIT 100` favorite | colorful graph |
| — | Deck | Advance to slide 8 | — |

See `neo4j-browser-cheatsheet.md` for the full query list and fallback plans.

## Slide 14 — Agnostic live demo choreography

Slide 14 is now a live demo proving the pipeline is dataset-agnostic. Three
PostgreSQL databases (Chinook / Northwind / Pagila — zero NOAH code touched)
get migrated in sequence to a **separate** Neo4j container on
`bolt://localhost:7688` (so NOAH's Neo4j on 7687 stays untouched — if the Q&A
circles back to anything NOAH-related, it's still there).

**Before the call:**

1. Ensure `demo-neo4j` container is up — preflight script checks this.
2. Open `http://localhost:7475` in a tab and log in (`neo4j` / `password123`).
3. Save one favorite: `MATCH (n) RETURN labels(n), count(n)` — you'll run it
   after each migration to show what just got loaded.

**During the demo (slide 14):**

| Step | Tab | Action | Expected |
|---|---|---|---|
| 1 | Deck | Read the title and the table out loud | audience sees "0 orphans" column |
| 2 | Terminal | `bash scripts/demo_agnostic.sh all` | 3 timed blocks, ~8 s total |
| 3 | Demo Neo4j Browser (:7475) | Run `MATCH (n) RETURN labels(n), count(n)` | shows Pagila labels (last migrated) |
| 4 | Demo Neo4j Browser | `MATCH (n) RETURN n LIMIT 80` | renders the Pagila graph |
| 5 | Deck | Advance to slide 15 | — |

**Key talking points:**

- *"I did not touch a line of code in `src/noah_converter/` between running
   this on NOAH and running it on Pagila. The YAML was the whole change."*
- *"Pagila has 25,758 nodes, which is bigger than NOAH, and it migrated in
   3.4 seconds without any PostGIS."*

**Fallback if the terminal misbehaves:** the frozen results are in
`outputs/agnostic_benchmark.json`, and the table on the slide itself is a
screenshot of exactly the same numbers. Point at it and move on.

## Slide-by-slide speaker plan

Total target: **25–30 min speaking + 3 min live demos × 3 = 32–40 min**. Aim
for 30 min. Cut slides 14 and 15 (Generalization, Business Value) if you're
running long.

| # | Title | Minutes | Mode | Depends on |
|---|---|---|---|---|
| 1 | Title | 0:30 | static | — |
| 2 | The Problem (SQL vs Cypher split) | 1:30 | static | — |
| 3 | Project Goal | 0:45 | static | — |
| 4 | Academic Foundation (3 papers) | 1:15 | static | — |
| 5 | System Architecture | 1:30 | static SVG | — |
| 6 | Graph Schema | 1:15 | static SVG | — |
| 7 | **LIVE — Migration Pipeline** | 3:00 | terminal | PG + Neo4j up |
| 8 | Audit result table | 1:00 | static | — |
| 9 | **LIVE — Text2Cypher via Streamlit Ask** | 5:00 | iframe | Streamlit + ANTHROPIC_API_KEY |
| 10 | Text2Cypher accuracy donut | 1:30 | static SVG | — |
| 11 | **LIVE — Graph viz via Streamlit Explore** | 2:00 | iframe | Streamlit + Neo4j |
| 12 | Performance by category | 1:30 | static SVG | — |
| 13 | **Hero: Q9 37× speedup** | 1:30 | static SVG | — |
| 14 | **LIVE — Agnostic: Chinook + Northwind + Pagila** | 2:30 | terminal + demo-neo4j | demo-neo4j on :7688 |
| 15 | Business value (3 audiences) | 1:15 | static | — |
| 16 | Limitations (honest inventory) | 1:00 | static | — |
| 17 | Lessons learned | 1:15 | static | — |
| 18 | Thank you + Q&A | 0:30 | static | — |

## Rehearsal tips

- **Record one full dry run on Loom.** Watch at 1.5× — catches pacing
  problems instantly.
- **Pre-type the three Text2Cypher questions** on slide 9 so you don't have
  to think on the call. Suggested three:
  1. `"How many housing projects are in each borough?"` (easy · 2s)
  2. `"Which ZIP codes have the highest median age?"` (medium · uses new Demographic)
  3. `"Find housing projects in ZIP codes neighboring 10001 built before 1960"` (hard · var-path)
- **For slide 11 Explore**, pre-copy this to clipboard so you can paste:
  ```cypher
  MATCH path = (z:ZipCode {zip_code:'10001'})-[:NEIGHBORS*0..2]-(n) RETURN path LIMIT 50
  ```
- **Fallback plan** if wifi/API dies: slides 9 and 11 include speaker-note
  copy you can read aloud over a screenshot of the expected output.

## If an iframe won't load

Some Chrome configurations block `http://localhost` iframes inside a
`file://` parent. Fix:

```bash
# option 1 — serve the deck over HTTP
python3 -m http.server 8000 --directory presentation
# then open http://localhost:8000
```

Now both the deck and the Streamlit iframes share the `localhost` origin and
Chrome won't block. This is the recommended way for live presentations.

## What's in the repo for a skeptical professor

Point to these files from slide 18:
- `outputs/audit_report.json` — machine-generated PASS record, timestamped
- `outputs/benchmark_report.json` — 20-question Text2Cypher grading output
- `outputs/performance_report.json` — 10-query benchmark with category_summary
- `tests/unit/test_audit_semantics.py` — 9 unit tests covering the audit logic
- `docs/CAPSTONE_REPORT.pdf` — the long-form write-up
- `docs/CODE_IMPROVEMENTS_APR22.md` — delta log of final polish pass

Everything a grader would want to verify is committed. No surprises.
