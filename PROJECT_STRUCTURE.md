# Project Structure Overview

## 📁 Complete Directory Tree

```
noah_postgres_to_neo4j/
│
├── 📄 README.md                      # Project overview and quick start
├── 📄 CLAUDE.md                      # AI assistant context and guidelines
├── 📄 PROJECT_STRUCTURE.md           # This file
├── 📄 .gitignore                     # Git ignore rules
├── 📄 .env.example                   # Environment variables template
├── 📄 requirements.txt               # Python dependencies
├── 📄 main.py                        # Main CLI entry point
│
├── 📁 src/noah_converter/            # Main application code
│   ├── __init__.py
│   ├── 📁 schema_analyzer/          # PostgreSQL schema introspection
│   │   ├── __init__.py
│   │   ├── analyzer.py              # Main analyzer class
│   │   └── models.py                # Data models (Table, Column, FK, etc.)
│   │
│   ├── 📁 mapping_engine/           # RDBMS → Graph mapping logic
│   │   ├── __init__.py
│   │   ├── mapper.py                # Mapping generation
│   │   ├── rules.py                 # Conversion rules
│   │   └── models.py                # Graph model classes (Node, Relationship)
│   │
│   ├── 📁 data_migrator/            # ETL and data migration
│   │   ├── __init__.py
│   │   ├── migrator.py              # Main migration orchestrator
│   │   ├── extractor.py             # PostgreSQL data extraction
│   │   ├── transformer.py           # Data transformation logic
│   │   ├── loader.py                # Neo4j data loading
│   │   └── validator.py             # Data validation
│   │
│   ├── 📁 text2cypher/              # Natural language query interface
│   │   ├── __init__.py
│   │   ├── translator.py            # NL → Cypher translation
│   │   ├── schema_context.py        # Schema-aware prompting
│   │   └── llm_client.py            # LLM API client (Anthropic/OpenAI)
│   │
│   └── 📁 utils/                    # Shared utilities
│       ├── __init__.py
│       ├── config.py                # Configuration management
│       ├── logger.py                # Logging utilities
│       ├── db_connection.py         # Database connection managers
│       └── helpers.py               # Common helper functions
│
├── 📁 tests/                        # Test suites
│   ├── __init__.py
│   ├── 📁 unit/                     # Unit tests
│   │   ├── __init__.py
│   │   ├── test_schema_analyzer.py
│   │   ├── test_mapping_engine.py
│   │   └── test_data_migrator.py
│   │
│   ├── 📁 integration/              # Integration tests
│   │   ├── __init__.py
│   │   ├── test_full_migration.py
│   │   └── test_text2cypher.py
│   │
│   └── 📁 fixtures/                 # Test data and mocks
│       ├── sample_schema.json
│       └── sample_data.sql
│
├── 📁 data/                         # Data files
│   ├── 📁 schemas/                  # PostgreSQL schemas (DDL)
│   │   ├── noah_schema.sql
│   │   └── noah_schema_analyzed.json
│   │
│   ├── 📁 samples/                  # Sample data for testing
│   │   ├── sample_zipcodes.csv
│   │   └── sample_buildings.csv
│   │
│   └── 📁 crosswalks/               # Geographic crosswalk files
│       └── zip_tract_crosswalk.csv
│
├── 📁 outputs/                      # Generated outputs
│   ├── 📁 cypher/                   # Generated Cypher scripts
│   │   ├── .gitkeep
│   │   ├── 01_create_constraints.cypher
│   │   ├── 02_create_nodes.cypher
│   │   └── 03_create_relationships.cypher
│   │
│   ├── 📁 reports/                  # Validation reports
│   │   ├── .gitkeep
│   │   └── migration_report.html
│   │
│   └── 📁 validation/               # Data validation results
│       ├── .gitkeep
│       └── validation_results.json
│
├── 📁 config/                       # Configuration files
│   ├── config.example.yaml          # Configuration template
│   └── config.yaml                  # Actual config (gitignored)
│
├── 📁 notebooks/                    # Jupyter notebooks
│   ├── 01_explore_noah_schema.ipynb
│   ├── 02_design_graph_model.ipynb
│   ├── 03_test_migration.ipynb
│   └── 04_text2cypher_examples.ipynb
│
├── 📁 scripts/                      # Utility scripts
│   ├── setup_databases.sh
│   ├── export_schema.py
│   └── benchmark_queries.py
│
├── 📁 docs/                         # Documentation
│   ├── 📁 architecture/             # System design docs
│   │   ├── README.md
│   │   ├── schema_mapping.md
│   │   └── data_flow.md
│   │
│   ├── 📁 api/                      # API documentation
│   │   ├── README.md
│   │   └── endpoints.md
│   │
│   └── 📁 guides/                   # User guides
│       ├── SETUP.md                 # Setup guide (created)
│       ├── user_guide.md
│       └── development.md
│
└── 📁 resources/                    # Reference materials
    ├── 📁 first_hand_resources/     # Project specs from professor
    │   ├── Digital Forge Capstone Project SP26...docx
    │   ├── Briefing- Why the NOAH Knowledge Graph...docx
    │   ├── Chaoou Zhang Final Report.pdf
    │   └── YUE Final Report.docx
    │
    └── 📁 second_hand_resources/    # Generated project docs
        ├── Final Project Proposal Finished (1).docx
        └── FRS_Requirement_Specification_Zhen.docx
```

## 🎯 Key Files Explained

### Entry Points
- **`main.py`** - Main CLI interface for all operations
- **`src/noah_converter/__init__.py`** - Package entry point

### Core Modules

#### Schema Analyzer (`src/noah_converter/schema_analyzer/`)
- Introspects PostgreSQL database
- Identifies tables, columns, relationships
- Classifies table types (entity, junction, lookup)
- Exports schema metadata

#### Mapping Engine (`src/noah_converter/mapping_engine/`)
- Converts relational schema to graph model
- Defines node labels and relationship types
- Applies naming conventions
- Generates mapping rules

#### Data Migrator (`src/noah_converter/data_migrator/`)
- Extracts data from PostgreSQL
- Transforms according to mapping
- Loads into Neo4j
- Validates referential integrity

#### Text2Cypher (`src/noah_converter/text2cypher/`)
- Natural language to Cypher translation
- Schema-aware prompting
- LLM integration (Anthropic/OpenAI)

### Configuration
- **`config/config.yaml`** - Main configuration
- **`.env`** - Sensitive credentials
- **`requirements.txt`** - Python dependencies

### Testing
- **`tests/unit/`** - Unit tests for individual modules
- **`tests/integration/`** - End-to-end integration tests
- **`tests/fixtures/`** - Test data and mocks

### Documentation
- **`README.md`** - Project overview
- **`docs/guides/SETUP.md`** - Setup instructions
- **`docs/architecture/`** - System design
- **`CLAUDE.md`** - AI context and guidelines

## 🔄 Typical Workflow

```bash
# 1. Setup
python main.py status                    # Check connections

# 2. Analysis
python main.py analyze                   # Analyze PostgreSQL schema
python main.py analyze --export data/schemas/analyzed.json

# 3. Mapping
python main.py generate-mapping          # Create graph mapping

# 4. Migration
python main.py migrate --dry-run         # Preview migration
python main.py migrate                   # Execute migration

# 5. Validation
python main.py validate                  # Validate results

# 6. Query
# Use Text2Cypher in notebooks or API
```

## 📝 Development Guidelines

### Adding New Features
1. Create feature branch: `git checkout -b feature/your-feature`
2. Add code in appropriate module under `src/noah_converter/`
3. Add tests in `tests/unit/` or `tests/integration/`
4. Update documentation in `docs/`
5. Test: `pytest`
6. Format: `black src/ tests/`
7. Lint: `ruff check src/ tests/`
8. Commit and push

### File Naming Conventions
- Python files: `snake_case.py`
- Test files: `test_*.py`
- Config files: `*.yaml` or `*.json`
- Documentation: `*.md` (markdown)
- Notebooks: `##_descriptive_name.ipynb`

### Import Structure
```python
# Standard library
import os
from pathlib import Path

# Third-party
import pandas as pd
from loguru import logger

# Local imports
from noah_converter.utils.config import load_config
from noah_converter.schema_analyzer import SchemaAnalyzer
```

## 🚀 Next Steps

1. **Complete configuration**
   - Copy `config/config.example.yaml` to `config/config.yaml`
   - Copy `.env.example` to `.env`
   - Update with your database credentials

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Test connections**
   ```bash
   python main.py status
   ```

4. **Start with exploration**
   - Open `notebooks/01_explore_noah_schema.ipynb`
   - Analyze the NOAH database structure
   - Design your graph model

5. **Implement core features**
   - Start with schema_analyzer (already scaffolded)
   - Then mapping_engine
   - Then data_migrator
   - Finally text2cypher

## 📚 Resources

- [README.md](README.md) - Project overview
- [docs/guides/SETUP.md](docs/guides/SETUP.md) - Detailed setup
- [CLAUDE.md](CLAUDE.md) - AI assistant guidelines
- Academic papers in `resources/first_hand_resources/`
