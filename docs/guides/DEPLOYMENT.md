# Deployment Guide

## Local Development (Recommended for Classroom Use)

### Prerequisites

- Python 3.10+
- PostgreSQL 14+ with PostGIS extension
- Neo4j 5.x Community or Enterprise
- 4 GB free disk space

### Step 1: Clone and Install

```bash
git clone <repo-url>
cd noah_postgres_to_neo4j
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure PostgreSQL

1. Install PostGIS: `CREATE EXTENSION postgis;`
2. Create the NOAH database and load data:

```bash
# Load the NOAH schema and data
psql -U postgres -c "CREATE DATABASE noah_db;"
psql -U postgres -d noah_db -f data/schemas/noah_schema.sql
```

Or fetch live from NYC Open Data (requires `sodapy`):

```bash
python scripts/fetch_noah_data.py
```

### Step 3: Configure Neo4j

1. Download [Neo4j Desktop](https://neo4j.com/download/) or use Neo4j Community Server
2. Create a new database named `neo4j`
3. Start the database (default ports: 7474 HTTP, 7687 Bolt)

### Step 4: Configure the Application

```bash
cp config/config.example.yaml config/config.yaml
```

Edit `config/config.yaml`:

```yaml
postgresql:
  host: localhost
  port: 5432
  database: noah_db
  user: postgres
  password: your_pg_password

neo4j:
  uri: bolt://localhost:7687
  user: neo4j
  password: your_neo4j_password

llm:
  provider: anthropic
  model: claude-sonnet-4-6
  api_key: ""   # or set ANTHROPIC_API_KEY environment variable
```

### Step 5: Run the Migration

```bash
# Analyze the PostgreSQL schema
python main.py analyze

# Run the full migration (takes ~2-5 minutes)
python main.py migrate

# Verify data integrity
python main.py audit
```

### Step 6: Start the Dashboard

```bash
streamlit run app/Home.py --server.port 8505
```

Open http://localhost:8505 in your browser.

---

## Docker Deployment

The included `docker-compose.yml` starts Neo4j and the Streamlit app together.

### Step 1: Set Environment Variables

Create a `.env` file:

```bash
ANTHROPIC_API_KEY=sk-ant-...
NEO4J_PASSWORD=your_password
PGPASSWORD=your_pg_password
```

### Step 2: Start Services

```bash
docker compose up -d
```

This starts:
- `neo4j` — Neo4j Community on ports 7474 and 7687
- `app` — Streamlit dashboard on port 8505

### Step 3: Load Data

After Neo4j is ready (check http://localhost:7474):

```bash
docker compose exec app python main.py migrate
```

### Step 4: Access

- Dashboard: http://localhost:8505
- Neo4j Browser: http://localhost:7474

---

## Classroom Setup

For classroom/lab use where students share a single server:

### Single-Server Multi-User Setup

1. Run Neo4j and the Streamlit app on a classroom server
2. Set `ANTHROPIC_API_KEY` as a server-side environment variable (not per-student)
3. Share the server IP with students: `http://<server-ip>:8505`
4. Streamlit handles concurrent users via independent session state

### Student Personal Setup

For students running locally (recommended for exercises):

1. Students install Neo4j Desktop (free, cross-platform)
2. Instructor provides a database dump:
   ```bash
   # Create dump (run on server)
   neo4j-admin database dump neo4j --to-path=/tmp/noah_dump
   # Students restore:
   neo4j-admin database load neo4j --from-path=/tmp/noah_dump
   ```
3. Students run `streamlit run app/Home.py` locally

---

## Streamlit Secrets (Production)

For production deployment, store credentials in `.streamlit/secrets.toml`:

```toml
[neo4j]
uri      = "bolt://localhost:7687"
user     = "neo4j"
password = "your_password"

[anthropic]
api_key  = "sk-ant-..."
```

The app automatically reads from `st.secrets` if available.

---

## Troubleshooting

### Neo4j connection refused

```bash
# Check Neo4j is running
neo4j status
# or
systemctl status neo4j
```

### Migration fails with "already exists" error

The migration uses `MERGE` (not `CREATE`) — it is idempotent. Re-running is safe. If you want a clean slate:

```cypher
-- In Neo4j Browser
MATCH (n) DETACH DELETE n
```

Then re-run `python main.py migrate`.

### Out of memory during migration

Reduce batch size in `config/config.yaml`:

```yaml
migration:
  batch_size: 200   # default 1000
```

### Streamlit "Module not found"

Make sure you activated the virtualenv:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

*Deployment Guide v1.0 · Spring 2026*
