#!/usr/bin/env bash
# Agnostic live-demo wrapper. Run on slide 14 of the final presentation.
#
# Takes 1 arg — which dataset to migrate, or `all` for the triple-play.
# All 3 go to the `demo-neo4j` container on bolt://localhost:7688, keeping
# NOAH on 7687 untouched.
#
# Usage:
#   scripts/demo_agnostic.sh chinook
#   scripts/demo_agnostic.sh northwind
#   scripts/demo_agnostic.sh pagila
#   scripts/demo_agnostic.sh all     # sequential, ~8 s total

set -u
cd "$(dirname "$0")/.."

GREEN=$'\033[0;32m'; BOLD=$'\033[1m'; DIM=$'\033[2m'; RESET=$'\033[0m'; CYAN=$'\033[0;36m'

run_one() {
    local name="$1"
    local config="config/${name}.yaml"
    local mapping="config/${name}_mapping.yaml"

    printf "\n${BOLD}${CYAN}▶ %s${RESET} ${DIM}(config=%s, mapping=%s)${RESET}\n" "$name" "$config" "$mapping"
    local start
    start=$(date +%s.%N)
    ./venv/bin/python main.py --config "$config" migrate --clear --mapping-rules "$mapping" 2>&1 \
        | grep -E "✅|Nodes created|Relationships created|relationships created \("
    local end
    end=$(date +%s.%N)
    printf "${GREEN}${BOLD}  elapsed: %.2fs${RESET}\n" "$(echo "$end - $start" | bc)"
}

case "${1:-}" in
    chinook|northwind|pagila)
        run_one "$1"
        ;;
    all)
        for ds in chinook northwind pagila; do
            run_one "$ds"
        done
        echo
        echo "${BOLD}${GREEN}All three agnostic migrations complete.${RESET}"
        echo "Point Neo4j Browser at ${BOLD}http://localhost:7475${RESET} to explore (demo-neo4j)."
        ;;
    *)
        echo "Usage: $0 {chinook|northwind|pagila|all}" >&2
        exit 2
        ;;
esac
