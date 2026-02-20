# NOAH PostgreSQL to Neo4j Converter

Automated RDBMS-to-Knowledge Graph conversion tool for the NOAH (Naturally Occurring Affordable Housing) database.

## 🎯 Project Overview

This capstone project develops an automated bot that converts the NOAH PostgreSQL database into a Neo4j knowledge graph, implementing proven academic methodologies including Rel2Graph, De Virgilio's framework, and Data2Neo.

**Source Database:** Yue Yu's NOAH PostgreSQL/PostGIS implementation
**Target Database:** Neo4j Knowledge Graph
**Key Features:**
- Automated schema analysis and intelligent mapping
- Data migration with validation
- Natural language query interface (Text2Cypher)

## 📁 Project Structure

```
noah_postgres_to_neo4j/
├── src/noah_converter/          # Main source code
│   ├── schema_analyzer/         # PostgreSQL schema introspection
│   ├── mapping_engine/          # RDBMS → Graph mapping logic
│   ├── data_migrator/           # ETL and data migration
│   ├── text2cypher/             # Natural language interface
│   └── utils/                   # Shared utilities
├── tests/                       # Test suites
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── fixtures/                # Test data and mocks
├── data/                        # Data files
│   ├── schemas/                 # PostgreSQL schemas (DDL)
│   ├── samples/                 # Sample data for testing
│   └── crosswalks/              # Geographic crosswalk files
├── outputs/                     # Generated outputs
│   ├── cypher/                  # Generated Cypher scripts
│   ├── reports/                 # Validation reports
│   └── validation/              # Data validation results
├── config/                      # Configuration files
├── notebooks/                   # Jupyter notebooks for exploration
├── scripts/                     # Utility scripts
├── docs/                        # Documentation
│   ├── architecture/            # System design docs
│   ├── api/                     # API documentation
│   └── guides/                  # User guides
└── resources/                   # Reference materials
    ├── first_hand_resources/    # Project specs from professor
    └── second_hand_resources/   # Generated project docs
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 14+ with PostGIS
- Neo4j 5.0+
- Docker (optional)

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd noah_postgres_to_neo4j

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup configuration
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your database credentials
```

### Basic Usage

```bash
# 1. Analyze PostgreSQL schema
python -m src.noah_converter.schema_analyzer analyze

# 2. Generate mapping
python -m src.noah_converter.mapping_engine generate

# 3. Migrate data
python -m src.noah_converter.data_migrator migrate

# 4. Validate results
python -m src.noah_converter.data_migrator validate
```

## 📊 NOAH Database Overview

**Scale:**
- 177 NYC ZIP codes/ZCTAs
- ~100,000 residential buildings
- Complex spatial relationships
- Multiple join patterns

**Key Tables:**
- `rent_burden` - Household rent burden metrics
- `zip_median_income` - ZIP-level income data
- `zip_median_rent` - Market rent by ZIP and unit type
- `zip_tract_crosswalk` - Geographic harmonization

## 🗺️ Graph Model Design

**Node Types:**
- `:Zipcode` - Geographic units
- `:Building` - Individual structures
- `:Demographic` - Population metrics
- `:RentBurden` - Affordability indicators

**Relationship Types:**
- `[:LOCATED_IN]` - Building → Zipcode
- `[:HAS_DEMOGRAPHICS]` - Zipcode → Demographic
- `[:NEIGHBORS]` - Zipcode → Zipcode (spatial adjacency)
- `[:HAS_RENT_BURDEN]` - Zipcode → RentBurden

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/unit/
pytest tests/integration/

# Run with coverage
pytest --cov=src/noah_converter
```

## 📚 Documentation

- [Architecture Overview](docs/architecture/README.md)
- [API Reference](docs/api/README.md)
- [User Guide](docs/guides/user_guide.md)
- [Development Guide](docs/guides/development.md)

## 🎓 Academic References

- **Rel2Graph** (Zhao et al., 2023) - ArXiv:2310.01080
- **De Virgilio Methodology** (2013) - ACM GRADES Workshop
- **Data2Neo** (2024) - ArXiv:2406.04995
- **Text2Cypher** (Ozsoy et al., 2024) - ArXiv:2412.10064

## 📝 License

Academic project for NYU SPS MASY program - Fall 2026

## 👥 Contributors

- **Student:** [Your Name]
- **Advisor:** Dr. Andres Fortino
- **Sponsor:** The Digital Forge Lab

## 🔗 Related Projects

- [Chaoou Zhang's NOAH Dashboard](https://github.com/cz3275/urbanlab-noah-dashboard)
- [Yue Yu's NOAH Implementation](https://becky0713-noah-frontendapp-gehyze.streamlit.app/)
