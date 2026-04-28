# How to Use This Project

A step-by-step guide written for someone who just received this repo and wants to **see it run** without reading any code. No prior experience with Neo4j, Docker, or Streamlit assumed.

> **What this project does:** It converts the NYC NOAH (Naturally Occurring Affordable Housing) PostgreSQL database into a Neo4j knowledge graph, then lets you ask questions about it in plain English (powered by Claude AI). It also proves the same conversion pipeline works on three completely unrelated databases — Chinook, Northwind, and Pagila.
>
> **Author:** Zhen Yang · NYU SPS MASY Capstone, Spring 2026 · Advisor: Dr. Andres Fortino

---

## Table of Contents

1. [What you need installed first](#1-what-you-need-installed-first)
2. [First-time setup (10 minutes)](#2-first-time-setup-10-minutes)
3. [Daily use — start everything](#3-daily-use--start-everything)
4. [Open the four things you'll look at](#4-open-the-four-things-youll-look-at)
5. [The five demos, command by command](#5-the-five-demos-command-by-command)
6. [Connection details (passwords, ports)](#6-connection-details-passwords-ports)
7. [Stop everything when you're done](#7-stop-everything-when-youre-done)
8. [Common problems and how to fix them](#8-common-problems-and-how-to-fix-them)
9. [Where things live in this repo](#9-where-things-live-in-this-repo)

---

## 1. What you need installed first

You need three things. If you're on a Mac, the easiest path is Homebrew (`brew install ...`).

| Tool | Why | Install command (Mac) | Verify |
|---|---|---|---|
| **Docker Desktop** | Runs PostgreSQL and Neo4j in containers so you don't have to install them manually | Download from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop), then **launch the Docker Desktop app once** | `docker info` (should print info, not an error) |
| **Python 3.10 or newer** | Runs the migration scripts and the web app | `brew install python@3.14` | `python3 --version` |
| **A web browser** | To view the slides, the Neo4j browser, and the Streamlit web app | Chrome, Safari, Firefox, or Edge — any modern one works | — |

**No other installation needed.** No Neo4j Desktop, no PostgreSQL local install, no JDK. Docker handles it all.

---

## 2. First-time setup (10 minutes)

You only do this once. After that, jump to [Daily use](#3-daily-use--start-everything).

### 2.1 — Open a Terminal in the project folder

```bash
cd /path/to/noah_postgres_to_neo4j
```

You should see folders named `app`, `config`, `presentation`, `scripts`, etc. when you run `ls`.

### 2.2 — Create a Python virtual environment and install dependencies

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

This downloads ~50 Python packages into `venv/`. Takes 2–3 minutes the first time. **You will not need to repeat this.**

### 2.3 — Set your Anthropic API key (only needed for Text2Cypher demo)

The natural-language query demo (Demo 2 below) needs an Anthropic Claude API key. If you don't have one, you can skip this step and skip Demo 2 — the migration, audit, and graph visualization demos all work without it.

**To set it:** Open the file `.env` in the project root, find this line:

```
ANTHROPIC_API_KEY=your_anthropic_key_here
```

Replace `your_anthropic_key_here` with your real key (it starts with `sk-ant-...`). Save the file.

> **Where to get a key:** [console.anthropic.com](https://console.anthropic.com) → API Keys → Create Key. The benchmark cost for the full demo is well under $0.10.

### 2.4 — Start the Docker containers (PostgreSQL + two Neo4j databases)

```bash
docker compose up -d postgres neo4j
```

Wait ~20 seconds, then check both are healthy:

```bash
docker compose ps
```

You should see something like:

```
NAME                    STATUS
noah-postgres           Up X seconds (healthy)
noah-neo4j              Up X seconds (healthy)
```

For the agnostic demo (Demo 5 below), there's a second Neo4j container called `demo-neo4j`. If you want it too:

```bash
docker compose up -d demo-neo4j
```

### 2.5 — One-time migration of NOAH data into Neo4j

```bash
./venv/bin/python main.py migrate
./venv/bin/python main.py audit
```

The first command takes ~10 seconds and converts 8,604 housing-project rows + supporting tables into 11,359 Neo4j nodes and 13,022 relationships. The second checks that everything migrated correctly — you should see **`Overall Status: PASS`** at the bottom.

You're ready.

---

## 3. Daily use — start everything

Three commands, in order:

```bash
# 1. Make sure Docker Desktop is running (open the app, look for the whale icon in your menu bar)

# 2. Start the database containers (instant if they were already up)
cd /path/to/noah_postgres_to_neo4j
docker compose up -d postgres neo4j demo-neo4j

# 3. Start the web app
./venv/bin/python -m streamlit run app/Home.py --server.port 8505
```

The web app prints a URL when it's ready — you'll see something like:

```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8505
```

**Leave that terminal window open** — it's running the app. To stop the app later, press `Ctrl+C` in that terminal.

---

## 4. Open the four things you'll look at

Open these four browser tabs, in this order:

| Tab | URL | What it is |
|---|---|---|
| 1 | open the file `presentation/index.html` | The 18-slide presentation deck (single HTML file, no server needed) |
| 2 | http://localhost:8505 | The Streamlit web app — Home page |
| 3 | http://localhost:7474 | Neo4j Browser for the **NOAH knowledge graph** (Demo 1 + Demo 3) |
| 4 | http://localhost:7475 | Neo4j Browser for the **demo-neo4j** instance (Demo 5 only) |

**To open the slide deck:** double-click `presentation/index.html` in Finder. It opens in your default browser. Use `→` and `←` keys to navigate, `F` for fullscreen, `Esc` for slide overview.

**For Tabs 3 and 4 (Neo4j Browser):** the first time you visit, log in with:

- Username: `neo4j`
- Password: `password123`
- Database: `neo4j` (leave default)

The browser remembers the login.

---

## 5. The five demos, command by command

### Demo 1 — Migration: empty → 11,359 nodes in 10 seconds

**The story:** Show that the converter takes raw PostgreSQL tables and produces a fully populated Neo4j graph automatically.

**Steps:**

1. In **Tab 3 (NOAH Neo4j Browser, port 7474)**, paste and run:
   ```cypher
   MATCH (n) DETACH DELETE n
   ```
   (this empties the graph)
2. Then run:
   ```cypher
   MATCH (n) RETURN count(n) AS total_nodes
   ```
   You should see `total_nodes: 0`.
3. Switch to your terminal and run:
   ```bash
   ./venv/bin/python main.py migrate
   ./venv/bin/python main.py audit
   ```
   This takes ~10 seconds. The audit prints `Overall Status: PASS`.
4. Switch back to Tab 3 and re-run the count query (just press `↑` then Enter). You'll see `total_nodes: 11359`.
5. Run this to see the actual graph:
   ```cypher
   MATCH (n) RETURN n LIMIT 100
   ```
   A colorful network diagram appears — five node colors, one per label.

### Demo 2 — Natural language query (needs Anthropic API key)

**The story:** A non-technical user types a question in English. Claude generates the Cypher. The system runs it and shows the answer.

**Steps:**

1. In **Tab 2 (Streamlit app)**, click **Ask** in the sidebar.
2. Type any of these questions:
   - "How many housing projects are in each borough?"
   - "Which ZIP codes have the highest median age?"
   - "Find housing projects in ZIP codes neighboring 10001 built before 1960"
3. Click **Search →**. The app shows the generated Cypher, the result table, and a plain-English explanation.

### Demo 3 — Visual graph exploration

**The story:** Browse the knowledge graph as a force-directed network — see how housing projects, ZIP codes, and rent-burden tracts connect.

**Steps:**

1. In **Tab 2 (Streamlit app)**, click **Explore** in the sidebar.
2. Click the **Graph View** tab at the top.
3. Pick an example from the dropdown (e.g., "ZIP → Affordability (Bronx)"), click **Load →**, then **Render Graph ▶**.
4. An interactive node-and-edge diagram appears below. Drag nodes around, hover for details.

### Demo 4 — Pre-built insights (no Cypher knowledge needed)

**The story:** Show that even without writing any query, the app produces ready-made charts — rent burden by borough, income vs. affordability, etc.

**Steps:**

1. In **Tab 2 (Streamlit app)**, click **Insights** in the sidebar.
2. Scroll through the four pre-built visualizations. They render automatically against the live graph.

### Demo 5 — Agnostic: same pipeline, different databases

**The story:** Prove the converter is **not** NOAH-specific. Three completely unrelated PostgreSQL databases — a music store, an office-supply store, and a movie-rental store — all migrate successfully **without changing a single line of code**.

**Steps:**

1. In your terminal, run:
   ```bash
   bash scripts/demo_agnostic.sh all
   ```
   This sequentially migrates Chinook → Northwind → Pagila into the **demo-neo4j** instance (the one on port 7475/7688). Total time: ~8 seconds.

2. Each migration uses a **different YAML config** (in `config/chinook.yaml`, `config/northwind.yaml`, `config/pagila.yaml`) — but the same Python code. Open one of those YAML files to see how easy it is to declare a new mapping.

3. Switch to **Tab 4 (demo-neo4j Browser, port 7475)** and run:
   ```cypher
   MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY count DESC
   ```
   You'll see Pagila labels — Film, Actor, Rental, Customer, etc. — totaling 25,758 nodes. (Pagila was the last of the three to load, because each migration starts by clearing the previous one.)

4. To audit any of the three:
   ```bash
   ./venv/bin/python main.py --config config/northwind.yaml audit \
     --mapping-rules config/northwind_mapping.yaml \
     --output outputs/northwind_audit.json
   ```
   Replace `northwind` with `chinook` or `pagila` for the others.

---

## 6. Connection details (passwords, ports)

Everything runs locally on this machine. No accounts, no cloud.

### PostgreSQL (source database)

- **Host:** `localhost` (or `127.0.0.1`)
- **Port:** `5432`
- **Database:** `noah_housing` (the main one; also `chinook`, `northwind`, `pagila`)
- **Username:** `postgres`
- **Password:** `password123`

If you want to poke around with `psql`:
```bash
docker exec -it noah-postgres psql -U postgres -d noah_housing
```

### Neo4j — main instance (NOAH graph)

- **Browser URL:** http://localhost:7474
- **Bolt URL** (for code/scripts): `bolt://localhost:7687`
- **Username:** `neo4j`
- **Password:** `password123`
- **Database:** `neo4j`

### Neo4j — demo instance (agnostic-demo target)

- **Browser URL:** http://localhost:7475
- **Bolt URL:** `bolt://localhost:7688`
- **Username:** `neo4j`
- **Password:** `password123`

### Streamlit web app

- **URL:** http://localhost:8505
- No login.

### Anthropic Claude API

- Key is read from the `.env` file in the project root. The Streamlit app also accepts a key pasted directly into the **Settings** sidebar — useful if you don't want to edit `.env`.

---

## 7. Stop everything when you're done

In the terminal that's running Streamlit, press `Ctrl+C`.

Then stop the Docker containers:

```bash
docker compose stop
```

The data persists — next time you run `docker compose up -d ...` everything will be exactly as you left it.

If you want to **completely wipe** everything (start fresh next time, including erasing the migrated graph):

```bash
docker compose down -v   # the -v also deletes the data volumes
```

---

## 8. Common problems and how to fix them

### "command not found: python"

On macOS, use `python3` (not `python`), or use the venv directly:

```bash
./venv/bin/python main.py migrate
```

This is the safest form — works regardless of whether the virtual environment is "activated."

### Streamlit page won't load

Check that the app is still running (the terminal you launched it in shouldn't have closed). If it's running but the page doesn't load, refresh with `Cmd+Shift+R` (Mac) / `Ctrl+Shift+R` (Win/Linux).

### Neo4j Browser says "Cannot connect"

Most likely the Neo4j container isn't running. Run:

```bash
docker compose ps
```

If you see `noah-neo4j` not listed or stopped, start it:

```bash
docker compose up -d neo4j
```

Wait ~15 seconds for it to come up, then refresh the browser tab.

### "Port 5432 / 7474 / 7687 / 8505 already in use"

Something else on this machine is using that port. The most common culprit on Macs is a Homebrew-installed PostgreSQL on port 5432. To check what's using a port:

```bash
lsof -i :5432
```

Either stop the conflicting service, or change the port in `docker-compose.yml`.

### Anthropic API key isn't working in the Ask page

Open the **Settings** page in the Streamlit sidebar and paste your key directly into the input field. This overrides whatever is in `.env` for the current session.

### The audit shows "WARN" with datetime mismatches

This is a known cosmetic issue, not a data problem. PostgreSQL returns Python `datetime` objects (`datetime.datetime(2002, 8, 14, ...)`), while Neo4j returns ISO strings (`'2002-08-14T00:00:00'`). They represent the same moment in time. The audit's exact-string comparison flags them as different. The actual migrated data is correct.

### A migration was interrupted halfway through

The pipeline is **idempotent** — safe to rerun. Just run the same `migrate` command again. It uses Cypher `MERGE`, which updates existing nodes instead of creating duplicates.

### "Module not found" errors when running Python commands

You forgot to use the venv. Always run with `./venv/bin/python ...` instead of just `python ...`.

---

## 9. Where things live in this repo

```
noah_postgres_to_neo4j/
├── HOW_TO_USE.md                  ← you are reading this
├── README.md                      Technical overview, benchmark numbers, architecture
├── .env                           Database passwords + Anthropic key (you edit this)
│
├── main.py                        CLI entry point. All commands start with: python main.py ...
├── docker-compose.yml             Defines the PostgreSQL + Neo4j containers
├── requirements.txt               Python dependencies
│
├── app/                           Streamlit web application
│   ├── Home.py                    Landing page (port 8505)
│   └── pages/                     Ask, Explore, Templates, Insights, Settings
│
├── presentation/                  The 18-slide HTML deck
│   ├── index.html                 ← the slides — open this in a browser
│   ├── README.md                  Speaker notes and demo choreography
│   ├── pre-demo-check.sh          One-shot health check before any presentation
│   └── neo4j-browser-cheatsheet.md  Cypher queries for the Neo4j Browser demos
│
├── src/noah_converter/            Core library (the actual pipeline)
│   ├── schema_analyzer/           Reads PostgreSQL schema automatically
│   ├── mapping_engine/            Applies the YAML mapping rules
│   ├── data_migrator/             Runs the MERGE Cypher batches
│   ├── data_auditor/              Post-migration integrity checks
│   └── text2cypher/               Natural-language → Cypher translator
│
├── config/                        YAML mapping rules (one per database)
│   ├── mapping_rules.yaml         NOAH (the main one)
│   ├── chinook.yaml + chinook_mapping.yaml
│   ├── northwind.yaml + northwind_mapping.yaml
│   └── pagila.yaml + pagila_mapping.yaml
│
├── scripts/                       Standalone scripts
│   ├── demo_agnostic.sh           Runs the three-dataset agnostic demo
│   ├── benchmark_text2cypher.py   Reproduces the 95% accuracy benchmark
│   └── performance_comparison.py  Reproduces the PG vs Neo4j benchmark
│
├── outputs/                       Generated reports (timestamped, safe to delete)
│   ├── audit_report.json          Latest NOAH audit
│   ├── benchmark_report.json      Text2Cypher accuracy
│   └── performance_report.json    PG vs Neo4j timings
│
└── docs/                          Long-form documentation
    ├── CAPSTONE_REPORT.pdf        The full NYU SPS capstone report
    ├── architecture/              System architecture diagrams
    └── guides/                    Additional user guides
```

---

## Quick reference card

Print this and tape it next to your laptop.

```
START EVERYTHING
  cd /path/to/noah_postgres_to_neo4j
  docker compose up -d postgres neo4j demo-neo4j
  ./venv/bin/python -m streamlit run app/Home.py --server.port 8505

URLS TO OPEN
  presentation/index.html       → slide deck
  http://localhost:8505         → web app
  http://localhost:7474         → NOAH Neo4j Browser
  http://localhost:7475         → demo-neo4j Browser

PASSWORDS
  Postgres / Neo4j (both):  user=postgres or neo4j   pass=password123

CORE COMMANDS
  python main.py migrate        Migrate NOAH PG → Neo4j (~10s)
  python main.py audit          Verify migration integrity (~1s)
  bash scripts/demo_agnostic.sh all
                                Migrate Chinook + Northwind + Pagila (~8s)

STOP EVERYTHING
  Ctrl+C in the Streamlit terminal
  docker compose stop
```

---

**Questions or issues:** open an issue in the GitHub repo, or contact Zhen Yang directly.
