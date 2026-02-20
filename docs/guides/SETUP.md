# Project Setup Guide

## Prerequisites

### Required Software
- **Python 3.10+** - Install from [python.org](https://www.python.org/)
- **PostgreSQL 14+** with PostGIS extension
- **Neo4j 5.0+** - Download from [neo4j.com](https://neo4j.com/download/)
- **Git** - For version control

### Optional Tools
- **Docker & Docker Compose** - For containerized deployment
- **DBeaver** or **pgAdmin** - PostgreSQL GUI clients
- **Neo4j Desktop** - Neo4j GUI client

## Initial Setup

### 1. Clone and Navigate to Project

```bash
cd noah_postgres_to_neo4j
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e .
```

### 4. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your actual credentials
# Use your favorite editor:
vim .env
# or
code .env
```

### 5. Configure Application

```bash
# Copy configuration template
cp config/config.example.yaml config/config.yaml

# Edit config.yaml with your settings
vim config/config.yaml
```

## Database Setup

### PostgreSQL Setup

#### Option 1: Use Yue Yu's Implementation Data

If you have access to Yue Yu's PostgreSQL dump or remote database:

```bash
# If using local dump file
psql -U postgres -d noah_housing -f yue_noah_dump.sql

# If using remote connection
# Update config/config.yaml with remote credentials
```

#### Option 2: Setup Fresh Database

```bash
# Create database
createdb noah_housing

# Enable PostGIS extension
psql -U postgres -d noah_housing -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# Import schema (if you have DDL files)
psql -U postgres -d noah_housing -f data/schemas/noah_schema.sql
```

### Neo4j Setup

#### Using Neo4j Desktop

1. Download and install [Neo4j Desktop](https://neo4j.com/download/)
2. Create a new database named "NOAH Knowledge Graph"
3. Set password (update in config/config.yaml)
4. Start the database

#### Using Docker

```bash
# Run Neo4j container
docker run \
    --name noah-neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/your_password \
    -v $HOME/neo4j/data:/data \
    neo4j:5.15.0

# Access Neo4j Browser at http://localhost:7474
```

## Verify Installation

### Check Database Connections

```bash
# Test connections
python main.py status
```

Expected output:
```
✓ PostgreSQL: Connected (15 tables)
✓ Neo4j: Connected (0 nodes, 0 relationships)
```

### Run Schema Analysis

```bash
# Analyze PostgreSQL schema
python main.py analyze --export data/schemas/noah_analyzed.json
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/noah_converter

# Run specific test file
pytest tests/unit/test_schema_analyzer.py
```

## Development Workflow

### Code Style

This project uses:
- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/
```

### Jupyter Notebooks

For exploration and prototyping:

```bash
# Start Jupyter
jupyter notebook

# Or use Jupyter Lab
jupyter lab
```

Notebooks are stored in `notebooks/` directory.

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "Add feature description"

# Push to remote
git push origin feature/your-feature-name
```

## Common Issues

### PostgreSQL Connection Error

**Problem:** `psycopg2.OperationalError: could not connect to server`

**Solution:**
1. Check PostgreSQL is running: `pg_isready`
2. Verify credentials in `config/config.yaml`
3. Check firewall settings
4. For remote connections, verify host is accessible

### Neo4j Connection Error

**Problem:** `ServiceUnavailable: WebSocket connection failure`

**Solution:**
1. Verify Neo4j is running
2. Check bolt port (7687) is accessible
3. Verify credentials
4. Check Neo4j logs: `neo4j console` or check Desktop logs

### ImportError for Modules

**Problem:** `ModuleNotFoundError: No module named 'noah_converter'`

**Solution:**
```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Reinstall in development mode
pip install -e .
```

### PostGIS Extension Not Found

**Problem:** `ERROR: type "geometry" does not exist`

**Solution:**
```sql
-- Connect to your database and run:
CREATE EXTENSION IF NOT EXISTS postgis;
```

## Next Steps

1. Read [Architecture Overview](../architecture/README.md)
2. Review [API Documentation](../api/README.md)
3. Check [User Guide](user_guide.md) for usage examples
4. Explore example notebooks in `notebooks/`

## Getting Help

- Check [README.md](../../README.md) for project overview
- Review [issues](https://github.com/your-repo/issues) for known problems
- Contact project maintainer: your.email@nyu.edu
