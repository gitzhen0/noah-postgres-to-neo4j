# NOAH Knowledge Graph - Streamlit Web UI

🏠 **Interactive web interface for querying NYC housing data using natural language**

---

## 🚀 Quick Start (Docker Compose - Recommended)

### Prerequisites
- Docker Desktop installed
- 8GB RAM available
- Ports 5432, 7474, 7687, 8501 available

### One-Command Launch

```bash
# Start all services (PostgreSQL, Neo4j, Streamlit)
docker-compose up -d

# Wait ~30 seconds for services to initialize, then open:
# 🌐 Streamlit UI: http://localhost:8501
# 🗄️ Neo4j Browser: http://localhost:7474
```

### First Time Setup

1. **Access the UI**: Open http://localhost:8501 in your browser

2. **Configure API Key**:
   - Go to ⚙️ Settings page
   - Enter your OpenAI or Anthropic API key
   - Click "Verify Key"

3. **Test Connection**:
   - Click "Test Connection" to verify Neo4j
   - You should see database statistics

4. **Start Querying**:
   - Go to 🔍 Query page
   - Try an example question or write your own!

---

## 📱 Features

### 🏠 Home Page
- Project overview and introduction
- Database statistics dashboard
- Example questions
- Quick start guide

### 🔍 Query Interface

#### 🗣️ Natural Language Mode
- Ask questions in plain English
- Automatic Cypher generation
- AI-powered result explanations
- Example question buttons

#### 🧑‍💻 Cypher Expert Mode
- Write Cypher queries directly
- Syntax highlighting
- Example query library
- Direct execution

### ⚙️ Settings
- API key management (OpenAI/Claude)
- LLM configuration (model, temperature)
- Neo4j connection testing
- Advanced options

---

## 💡 Example Queries

### Simple Queries
```
Which ZIP codes are in Brooklyn?
Show me all housing projects in Manhattan
How many projects are in each borough?
```

### Relationship Queries
```
Which ZIP codes are neighbors of 10001?
Find housing projects in ZIPs neighboring 11106
```

### Spatial Queries
```
Find ZIP codes within 5km of 10001
Which ZIPs are closest to 10002?
```

### Complex Queries
```
Find all ZIP codes within 2 hops of 10001
Show housing projects in high rent burden neighborhoods
```

---

## 🛠️ Manual Setup (Without Docker)

### 1. Install Dependencies

```bash
cd app
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:
```bash
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
NEO4J_DATABASE=neo4j

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=noah_housing
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123

# Optional: Pre-configure API keys
OPENAI_API_KEY=your-key-here
# or
ANTHROPIC_API_KEY=your-key-here
```

### 3. Start Databases

**Neo4j:**
```bash
# Using Docker
docker run -d \
  --name noah-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  neo4j:5.15.0

# Or install locally from https://neo4j.com/download/
```

**PostgreSQL:**
```bash
# Using Docker
docker run -d \
  --name noah-postgres \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgres123 \
  postgis/postgis:15-3.3

# Or install locally from https://www.postgresql.org/download/
```

### 4. Migrate Data

```bash
# Run migration script
python scripts/migrate_to_neo4j_with_spatial.py
```

### 5. Launch Streamlit

```bash
cd app
streamlit run Home.py
```

Visit http://localhost:8501

---

## 🔧 Configuration

### API Keys

**Option 1: Environment Variables** (Pre-configured)
```bash
# In .env or docker-compose.yml
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...
```

**Option 2: UI Input** (Recommended for teaching)
- Users enter their own API keys in Settings page
- Keys stored in session only (not saved to disk)
- More secure for shared environments

### LLM Settings

Available in ⚙️ Settings page:
- **Provider**: OpenAI or Anthropic (Claude)
- **Model**: gpt-3.5-turbo, gpt-4, claude-sonnet-4.5, etc.
- **Temperature**: 0 (deterministic) to 1 (creative)
- **Max Tokens**: Response length limit

### Database Connections

**Neo4j:**
- URI: `bolt://neo4j:7687` (Docker) or `bolt://localhost:7687` (local)
- User: `neo4j`
- Password: `password123`

**PostgreSQL:**
- Host: `postgres` (Docker) or `localhost` (local)
- Port: `5432`
- Database: `noah_housing`
- User: `postgres`

---

## 📊 Architecture

```
┌─────────────────┐
│   Streamlit UI  │  (Port 8501)
│   - Home        │
│   - Query       │
│   - Settings    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────┐
│  Neo4j  │ │PostgreSQL│
│ (7687)  │ │  (5432)  │
└─────────┘ └──────────┘
```

---

## 🐛 Troubleshooting

### "Connection refused" Error

**Neo4j:**
```bash
# Check if running
docker ps | grep neo4j

# Check logs
docker logs noah-neo4j

# Restart
docker restart noah-neo4j
```

**PostgreSQL:**
```bash
# Check if running
docker ps | grep postgres

# Check logs
docker logs noah-postgres

# Restart
docker restart noah-postgres
```

### "API Key Invalid" Error

- Verify your API key is correct
- Check for extra spaces or newlines
- Ensure you have credits/quota remaining
- Try regenerating the key

### "No module named 'noah_converter'" Error

```bash
# Add src to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Or run from project root
cd /path/to/noah_postgres_to_neo4j
streamlit run app/Home.py
```

### Port Already in Use

```bash
# Find process using port 8501
lsof -i :8501

# Kill process
kill -9 <PID>

# Or use different port
streamlit run Home.py --server.port=8502
```

---

## 🔄 Updating Data

### Refresh Neo4j Data

```bash
# Re-run migration
python scripts/migrate_to_neo4j_with_spatial.py

# Or from Docker
docker exec -it noah-streamlit python scripts/migrate_to_neo4j_with_spatial.py
```

### Add New Data

1. Update PostgreSQL database
2. Re-run spatial precomputation
3. Re-run Neo4j migration
4. Refresh Streamlit UI

---

## 📦 Deployment

### Docker Hub (Share with Others)

```bash
# Build image
docker build -t yourusername/noah-streamlit:latest -f Dockerfile.streamlit .

# Push to Docker Hub
docker push yourusername/noah-streamlit:latest

# Others can pull and run
docker pull yourusername/noah-streamlit:latest
docker-compose up -d
```

### Streamlit Cloud (Free Hosting)

1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Connect repository
4. Deploy!

**Note**: Need to configure Neo4j cloud connection (e.g., Neo4j Aura)

---

## 🎓 For Classroom Use

### Instructor Setup

1. **Pre-load Data**:
   ```bash
   docker-compose up -d
   python scripts/migrate_to_neo4j_with_spatial.py
   ```

2. **Distribute**:
   - Share `docker-compose.yml`
   - Students run: `docker-compose up -d`

3. **Students Enter Their Own API Keys**:
   - Keeps costs distributed
   - Teaches API key management

### Student Instructions

```bash
# 1. Clone repository
git clone <your-repo-url>
cd noah_postgres_to_neo4j

# 2. Start services
docker-compose up -d

# 3. Open browser
# http://localhost:8501

# 4. Enter API key in Settings
# Get free key at: https://platform.openai.com/api-keys
```

---

## 📝 License & Credits

**NYU Capstone Project 2026**
- Digital Forge Lab
- Based on Yue Yu's and Chaoou Zhang's NOAH database work

---

## 🤝 Contributing

Found a bug? Have a feature request?
1. Open an issue on GitHub
2. Submit a pull request
3. Contact the team

---

## 📚 Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)
- [Text2Cypher Project Docs](../docs/)

---

**Ready to explore NYC housing data? Start querying! 🚀**
