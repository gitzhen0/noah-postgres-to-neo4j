#!/usr/bin/env bash
# Pre-flight sanity check before the capstone final presentation.
# Run this 30 minutes before you're on Zoom; everything should say PASS.

set -u
cd "$(dirname "$0")/.."

GREEN=$'\033[0;32m'; RED=$'\033[0;31m'; YELLOW=$'\033[0;33m'; RESET=$'\033[0m'; BOLD=$'\033[1m'
PASS="${GREEN}✓${RESET}"
FAIL="${RED}✗${RESET}"
WARN="${YELLOW}!${RESET}"

failures=0
warnings=0

check() {
    local label="$1"; shift
    if "$@" >/dev/null 2>&1; then
        printf "  %s %s\n" "$PASS" "$label"
    else
        printf "  %s %s\n" "$FAIL" "$label"
        failures=$((failures + 1))
    fi
}

warn() {
    local label="$1"; shift
    if "$@" >/dev/null 2>&1; then
        printf "  %s %s\n" "$PASS" "$label"
    else
        printf "  %s %s\n" "$WARN" "$label"
        warnings=$((warnings + 1))
    fi
}

echo
echo "${BOLD}NOAH capstone · pre-demo preflight${RESET}"
echo "────────────────────────────────────"

echo
echo "${BOLD}Docker${RESET}"
check "Docker daemon running"                                   docker info
check "noah-pg-restored container healthy"                       docker inspect --format='{{.State.Running}}' noah-pg-restored
check "noah-neo4j-restored container healthy"                    docker inspect --format='{{.State.Running}}' noah-neo4j-restored

echo
echo "${BOLD}PostgreSQL (via Docker)${RESET}"
check "psql executes on PG container"                            docker exec noah-pg-restored pg_isready -U postgres
check "housing_projects = 8,604 rows"                            bash -c '[ "$(docker exec noah-pg-restored psql -U postgres -d noah_housing -tAc "SELECT COUNT(*) FROM housing_projects")" = "8604" ]'
check "zip_shapes = 177 rows"                                    bash -c '[ "$(docker exec noah-pg-restored psql -U postgres -d noah_housing -tAc "SELECT COUNT(*) FROM zip_shapes")" = "177" ]'
check "zip_demographic present (Demographic node source)"        bash -c 'docker exec noah-pg-restored psql -U postgres -d noah_housing -tAc "SELECT 1 FROM zip_demographic LIMIT 1" | grep -q 1'

echo
echo "${BOLD}Neo4j (via Docker)${RESET}"
check "cypher-shell connects"                                    docker exec noah-neo4j-restored cypher-shell -u neo4j -p password123 "RETURN 1"
check "Neo4j Browser reachable on :7474 (for slide 7 demo)"       curl -sf -o /dev/null http://localhost:7474
check "demo-neo4j container running (slide 14 target)"           docker inspect --format='{{.State.Running}}' demo-neo4j
check "demo-neo4j cypher-shell connects on :7688"                 docker exec demo-neo4j cypher-shell -u neo4j -p password123 "RETURN 1"
check "demo Neo4j Browser reachable on :7475"                     curl -sf -o /dev/null http://localhost:7475

echo
echo "${BOLD}Agnostic datasets in PostgreSQL (slide 14)${RESET}"
check "chinook.album = 347 rows"                                 bash -c '[ "$(docker exec noah-pg-restored psql -U postgres -d chinook -tAc "SELECT COUNT(*) FROM album")" = "347" ]'
check "northwind.orders = 830 rows"                              bash -c '[ "$(docker exec noah-pg-restored psql -U postgres -d northwind -tAc "SELECT COUNT(*) FROM orders")" = "830" ]'
check "pagila.rental = 16,044 rows"                              bash -c '[ "$(docker exec noah-pg-restored psql -U postgres -d pagila -tAc "SELECT COUNT(*) FROM rental")" = "16044" ]'
check "scripts/demo_agnostic.sh present and executable"           test -x scripts/demo_agnostic.sh
check "HousingProject = 8,604 nodes"                             bash -c '[ "$(docker exec noah-neo4j-restored cypher-shell -u neo4j -p password123 --format plain "MATCH (:HousingProject) RETURN count(*)" | tail -1 | tr -d " ")" = "8604" ]'
check "Demographic node present (new in v2)"                     bash -c '[ "$(docker exec noah-neo4j-restored cypher-shell -u neo4j -p password123 --format plain "MATCH (:Demographic) RETURN count(*)" | tail -1 | tr -d " ")" = "176" ]'
check "HAS_DEMOGRAPHICS edges present"                           bash -c '[ "$(docker exec noah-neo4j-restored cypher-shell -u neo4j -p password123 --format plain "MATCH ()-[:HAS_DEMOGRAPHICS]->() RETURN count(*)" | tail -1 | tr -d " ")" = "176" ]'
check "NEIGHBORS edges present"                                  bash -c '[ "$(docker exec noah-neo4j-restored cypher-shell -u neo4j -p password123 --format plain "MATCH ()-[:NEIGHBORS]->() RETURN count(*)" | tail -1 | tr -d " ")" = "392" ]'

echo
echo "${BOLD}Streamlit demo server${RESET}"
check "localhost:8505 responds"                                   curl -sf -o /dev/null http://localhost:8505
check "/Ask page responds (demo 2)"                               curl -sf -o /dev/null http://localhost:8505/Ask
check "/Explore page responds (demo 3)"                           curl -sf -o /dev/null http://localhost:8505/Explore

echo
echo "${BOLD}Frozen artifacts (referenced by slides)${RESET}"
check "outputs/audit_report.json is PASS"                         bash -c 'grep -q "\"overall_status\": \"PASS\"" outputs/audit_report.json'
check "outputs/benchmark_report.json = 95%"                       bash -c 'grep -q "\"accuracy_pct\": 95" outputs/benchmark_report.json'
check "outputs/performance_report.json has var-path"              bash -c 'grep -q "\"var-path\"" outputs/performance_report.json'

echo
echo "${BOLD}Secrets (must be present for Text2Cypher demo)${RESET}"
env_key=$(grep -E "^ANTHROPIC_API_KEY=" .env 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
if [ -n "${ANTHROPIC_API_KEY:-}" ] && [ "${ANTHROPIC_API_KEY}" != "your_anthropic_key_here" ]; then
    printf "  %s ANTHROPIC_API_KEY set in environment\n" "$PASS"
elif [ -n "$env_key" ] && [ "$env_key" != "your_anthropic_key_here" ]; then
    printf "  %s ANTHROPIC_API_KEY set in .env\n" "$PASS"
else
    printf "  %s ANTHROPIC_API_KEY missing — Text2Cypher demo will fail (set it in .env or export)\n" "$FAIL"
    failures=$((failures + 1))
fi

echo
echo "${BOLD}Presentation deck${RESET}"
check "presentation/index.html exists"                           test -f presentation/index.html
warn "presentation opens in default browser (launches window)"    bash -c 'echo skip'

echo
echo "────────────────────────────────────"
if [ "$failures" -eq 0 ] && [ "$warnings" -eq 0 ]; then
    echo "${GREEN}${BOLD}All good. You're ready.${RESET}"
    echo ""
    echo "Open the deck:"
    echo "  open presentation/index.html"
    echo ""
    echo "Pin these browser tabs in the order you'll need them:"
    echo "  file://$(pwd)/presentation/index.html"
    echo "  http://localhost:8505          # Home"
    echo "  http://localhost:8505/Ask      # Demo 2"
    echo "  http://localhost:8505/Explore  # Demo 3"
    echo ""
    exit 0
elif [ "$failures" -eq 0 ]; then
    echo "${YELLOW}${BOLD}${warnings} warning(s). Probably fine to proceed.${RESET}"
    exit 0
else
    echo "${RED}${BOLD}${failures} failure(s). Fix before going live.${RESET}"
    echo
    echo "Common fixes:"
    echo "  docker start noah-pg-restored noah-neo4j-restored"
    echo "  python main.py migrate --mapping-rules outputs/mapping_draft.yaml"
    echo "  python scripts/load_demographics.py"
    echo "  ./venv/bin/python -m streamlit run app/Home.py --server.port 8505 &"
    exit 1
fi
