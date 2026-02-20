# NOAH Database Setup Guide

## Phase 0: Setup & Data Access

This guide walks you through setting up the NOAH PostgreSQL database and Neo4j from scratch.

## Prerequisites

- Python 3.10+
- PostgreSQL 14+ with PostGIS
- Docker (for Neo4j) or Neo4j Desktop
- Git

## Step 1: PostgreSQL Setup with PostGIS

### Option A: Using Homebrew (macOS - Recommended)

```bash
# Install PostgreSQL and PostGIS
brew install postgresql@14 postgis

# Start PostgreSQL service
brew services start postgresql@14

# Create database
createdb noah_housing

# Enable PostGIS extension
psql noah_housing -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql noah_housing -c "CREATE EXTENSION IF NOT EXISTS postgis_topology;"
```

### Option B: Using Docker

```bash
# Run PostgreSQL with PostGIS
docker run --name noah-postgres \
  -e POSTGRES_PASSWORD=password123 \
  -e POSTGRES_DB=noah_housing \
  -p 5432:5432 \
  -v ~/postgres_data:/var/lib/postgresql/data \
  -d postgis/postgis:14-3.3

# Verify PostGIS is installed
docker exec -it noah-postgres psql -U postgres -d noah_housing -c "SELECT PostGIS_Version();"
```

### Verify PostgreSQL Setup

```bash
# Test connection
psql -U postgres -d noah_housing -c "SELECT version();"

# Should show PostgreSQL 14.x

# Test PostGIS
psql -U postgres -d noah_housing -c "SELECT PostGIS_Full_Version();"
```

## Step 2: Load NOAH Data

### 2.1: Navigate to Yue's Repository

```bash
cd ~/Desktop/noah-source-data
```

### 2.2: Setup Environment Variables

Create a `.env` file in the `noah-source-data` directory:

```bash
# Copy the example
cp env.example .env

# Edit .env with your credentials
cat > .env << 'EOF'
DB_HOST=localhost
DB_PORT=5432
DB_NAME=noah_housing
DB_USER=postgres
DB_PASSWORD=password123

# Optional: Socrata API token for data updates
# Get one from: https://data.cityofnewyork.us/profile/edit/developer_settings
SOCRATA_APP_TOKEN=your_token_here_optional
EOF
```

### 2.3: Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2.4: Initialize Database Schema

```bash
# Run database initialization
python scripts/init_database.py
```

This creates the `housing_projects` table with PostGIS geometry columns.

### 2.5: Populate Data from Socrata API

**Note:** This fetches live data from NYC Open Data and may take 10-20 minutes.

```bash
# Run the data pipeline
python scripts/run_data_pipeline.py
```

Expected output:
```
Fetching data from Socrata API...
Processing batch 1/10...
Processing batch 2/10...
...
✓ Loaded 12,345 housing project records
```

### 2.6: Build ZIP-Level Aggregated Tables

This creates the analytical tables we need for the knowledge graph:

```bash
# This script creates:
# - noah_zip_income (median income by ZIP)
# - noah_zip_rentburden (rent burden by ZIP)
# - noah_affordability_analysis (unified table)
python scripts/build_zip_level_tables.py
```

### 2.7: Create Additional Required Tables

The NOAH analysis requires several census and geographic tables. Let me check what's in the frontend data folder and create scripts to load those.

**Note:** Yue's implementation pulls data from Census API and creates these tables:
- `zip_tract_crosswalk` - Geographic crosswalk between ZIP codes and Census tracts
- `zip_shapes` - ZIP code geometries for NYC
- `median_income` - Tract-level median household income
- `rent_burden` - Tract-level rent burden statistics
- `zip_median_rent` - Market rent data by ZIP and bedroom count

We'll need to either:
1. Connect to Yue's deployed database (if accessible), OR
2. Download Census data and create these tables manually

For now, let's check the database to see what tables exist after running the scripts.

### 2.8: Verify Database Setup

```bash
# Check tables created
psql -U postgres -d noah_housing -c "\dt"

# Check row counts
psql -U postgres -d noah_housing << 'SQL'
SELECT
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
SQL

# Check for PostGIS geometries
psql -U postgres -d noah_housing -c "SELECT COUNT(*) FROM housing_projects WHERE geom IS NOT NULL;"
```

Expected tables:
- `housing_projects` (main table with ~12,000+ rows)
- `noah_zip_income` (if build script succeeded)
- `noah_zip_rentburden` (if build script succeeded)
- Additional tables depend on what data sources were available

## Step 3: Neo4j Setup

### Option A: Using Docker (Recommended)

```bash
# Run Neo4j in Docker
docker run --name noah-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  -e NEO4J_PLUGINS='["apoc"]' \
  -e NEO4J_dbms_security_procedures_unrestricted=apoc.* \
  -v ~/neo4j/data:/data \
  -v ~/neo4j/logs:/logs \
  -d neo4j:5.15.0

# Wait for Neo4j to start (30 seconds)
sleep 30

# Verify Neo4j is running
curl http://localhost:7474
```

### Option B: Using Neo4j Desktop

1. Download Neo4j Desktop from https://neo4j.com/download/
2. Install and open Neo4j Desktop
3. Create a new project "NOAH Conversion"
4. Create a new database "noah-housing"
5. Set password to `password123`
6. Install APOC plugin
7. Start the database

### Verify Neo4j Setup

```bash
# Using cypher-shell (if installed)
cypher-shell -u neo4j -p password123 "RETURN 'Neo4j is running!' AS message;"

# Or visit in browser
open http://localhost:7474
# Login: neo4j / password123
```

## Step 4: Configure Our Converter Tool

Now configure the `noah_postgres_to_neo4j` project to connect to these databases.

```bash
# Navigate to our converter project
cd ~/Desktop/noah_postgres_to_neo4j

# Create config file from template
cp config/config.example.yaml config/config.yaml

# Create .env file from template
cp .env.example .env
```

### Edit `config/config.yaml`:

```yaml
# Source Database (PostgreSQL)
source_db:
  type: postgresql
  host: localhost
  port: 5432
  database: noah_housing
  user: postgres
  password: password123
  schema: public

# Target Database (Neo4j)
target_db:
  type: neo4j
  uri: bolt://localhost:7687
  user: neo4j
  password: password123
  database: neo4j
```

### Edit `.env`:

```bash
# PostgreSQL Connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=noah_housing
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password123

# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
NEO4J_DATABASE=neo4j

# LLM API Keys (for Text2Cypher - Phase 4)
ANTHROPIC_API_KEY=your_anthropic_key_here
```

## Step 5: Test Connections

```bash
# From noah_postgres_to_neo4j directory
python main.py status
```

Expected output:
```
Database Connection Status

✓ PostgreSQL: Connected (5 tables)
✓ Neo4j: Connected (0 nodes, 0 relationships)
```

## Step 6: Analyze NOAH Schema

```bash
# Run schema analysis
python main.py analyze --export data/schemas/noah_yueyu_schema.json
```

This will:
1. Connect to the PostgreSQL database
2. Analyze all tables, columns, relationships
3. Export the schema to JSON for reference

Expected output:
```
Starting schema analysis...

Schema Analysis Summary
┌─────────────────────────┬───────┬─────────┬──────┬─────┐
│ Table Name              │ Type  │ Columns │ Rows │ FKs │
├─────────────────────────┼───────┼─────────┼──────┼─────┤
│ housing_projects        │ table │ 45      │ 12345│ 0   │
│ noah_zip_income         │ table │ 5       │ 177  │ 0   │
│ noah_zip_rentburden     │ table │ 8       │ 177  │ 0   │
└─────────────────────────┴───────┴─────────┴──────┴─────┘

✓ Schema exported to: data/schemas/noah_yueyu_schema.json
```

## Done Criteria for Phase 0

Check that you've completed:

- ✅ `python main.py status` shows both databases connected
- ✅ `python main.py analyze` returns 3+ tables from NOAH database
- ✅ Exported JSON schema exists at `data/schemas/noah_yueyu_schema.json`
- ✅ PostgreSQL has PostGIS enabled: `SELECT PostGIS_Version();`
- ✅ Can query data: `SELECT COUNT(*) FROM housing_projects;` returns >10,000

## Troubleshooting

### PostgreSQL Connection Failed

```bash
# Check if PostgreSQL is running
brew services list | grep postgresql
# or
docker ps | grep postgres

# Check connection manually
psql -U postgres -d noah_housing -c "SELECT 1;"
```

### PostGIS Extension Missing

```bash
psql -U postgres -d noah_housing -c "CREATE EXTENSION postgis;"
psql -U postgres -d noah_housing -c "CREATE EXTENSION postgis_topology;"
```

### Neo4j Connection Failed

```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Restart Neo4j
docker restart noah-neo4j

# Check logs
docker logs noah-neo4j
```

### Missing Tables After Scripts

If `build_zip_level_tables.py` fails, it's likely because:
1. Missing source tract-level tables (from Census)
2. Missing crosswalk table

**Workaround:** We can create simplified versions of these tables from the housing_projects data for initial testing, then enhance later.

### Socrata API Rate Limiting

If the data pipeline is slow:
1. Get a free Socrata API token: https://data.cityofnewyork.us/
2. Add it to `.env` as `SOCRATA_APP_TOKEN`
3. This increases rate limits from 1000 to 100,000 requests/day

## Next Steps

Once Phase 0 is complete:
- ✅ Move to **Phase 1: Design Graph Model**
- Design the Neo4j schema based on the analyzed PostgreSQL schema
- Create mapping specifications

## Data Sources Reference

- **NYC Housing Data:** https://data.cityofnewyork.us/Housing-Development/Housing-New-York-Units-by-Building/hg8x-zxpr
- **Census ACS Data:** American Community Survey 5-year estimates
- **Geographic Data:** NYC Open Data - ZCTA/Tract shapefiles
- **Yue's GitHub:** https://github.com/Becky0713/NOAH
- **Yue's Dashboard:** https://becky0713-noah-frontendapp-gehyze.streamlit.app/
