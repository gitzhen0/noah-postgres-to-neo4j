#!/bin/bash
# NOAH Database Setup Script
# This script sets up PostgreSQL + PostGIS and Neo4j using Docker

set -e  # Exit on error

echo "🚀 NOAH Database Setup Script"
echo "=============================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker is running
echo -e "${BLUE}Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop and try again.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Setup PostgreSQL with PostGIS
echo -e "${BLUE}Setting up PostgreSQL + PostGIS...${NC}"

# Stop and remove existing container if it exists
docker stop noah-postgres 2>/dev/null || true
docker rm noah-postgres 2>/dev/null || true

# Run PostgreSQL with PostGIS
docker run --name noah-postgres \
  -e POSTGRES_PASSWORD=password123 \
  -e POSTGRES_DB=noah_housing \
  -p 5432:5432 \
  -v ~/noah_data/postgres:/var/lib/postgresql/data \
  -d postgis/postgis:14-3.3

echo -e "${YELLOW}Waiting for PostgreSQL to start (10 seconds)...${NC}"
sleep 10

# Verify PostgreSQL is running
if docker exec noah-postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL is running${NC}"
else
    echo -e "${RED}❌ PostgreSQL failed to start${NC}"
    docker logs noah-postgres
    exit 1
fi

# Enable PostGIS extensions
echo -e "${BLUE}Enabling PostGIS extensions...${NC}"
docker exec noah-postgres psql -U postgres -d noah_housing -c "CREATE EXTENSION IF NOT EXISTS postgis;"
docker exec noah-postgres psql -U postgres -d noah_housing -c "CREATE EXTENSION IF NOT EXISTS postgis_topology;"

# Verify PostGIS
POSTGIS_VERSION=$(docker exec noah-postgres psql -U postgres -d noah_housing -t -c "SELECT PostGIS_Version();" | tr -d ' ')
echo -e "${GREEN}✓ PostGIS installed: ${POSTGIS_VERSION}${NC}"
echo ""

# Setup Neo4j
echo -e "${BLUE}Setting up Neo4j...${NC}"

# Stop and remove existing container if it exists
docker stop noah-neo4j 2>/dev/null || true
docker rm noah-neo4j 2>/dev/null || true

# Run Neo4j
docker run --name noah-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  -e NEO4J_PLUGINS='["apoc"]' \
  -e NEO4J_dbms_security_procedures_unrestricted=apoc.* \
  -e NEO4J_dbms_security_procedures_allowlist=apoc.* \
  -v ~/noah_data/neo4j/data:/data \
  -v ~/noah_data/neo4j/logs:/logs \
  -d neo4j:5.15.0

echo -e "${YELLOW}Waiting for Neo4j to start (30 seconds)...${NC}"
sleep 30

# Verify Neo4j is running
if curl -s http://localhost:7474 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Neo4j is running${NC}"
else
    echo -e "${YELLOW}⚠️  Neo4j may still be starting. Check http://localhost:7474${NC}"
fi
echo ""

# Summary
echo -e "${GREEN}=============================="
echo -e "✓ Setup Complete!"
echo -e "==============================${NC}"
echo ""
echo -e "${BLUE}PostgreSQL:${NC}"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  Database: noah_housing"
echo "  User: postgres"
echo "  Password: password123"
echo ""
echo -e "${BLUE}Neo4j:${NC}"
echo "  Browser: http://localhost:7474"
echo "  Bolt: bolt://localhost:7687"
echo "  User: neo4j"
echo "  Password: password123"
echo ""
echo -e "${BLUE}Data stored in:${NC} ~/noah_data/"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Configure the converter: cp config/config.example.yaml config/config.yaml"
echo "2. Test connections: python main.py status"
echo "3. Load NOAH data from Yue's repository"
echo ""
echo -e "${GREEN}To stop databases:${NC}"
echo "  docker stop noah-postgres noah-neo4j"
echo ""
echo -e "${GREEN}To start databases:${NC}"
echo "  docker start noah-postgres noah-neo4j"
echo ""
echo -e "${GREEN}To view logs:${NC}"
echo "  docker logs noah-postgres"
echo "  docker logs noah-neo4j"
echo ""
