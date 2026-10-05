#!/usr/bin/env bash
# CI only: route_jack_grid.py --after-promote hook that pushes each adopted stage as it lands.
# Usage: bash scripts/pcbgen/ci_stage_push.sh <board> <branch>  (STAGE, OPEN_BEFORE, OPEN_AFTER from the driver)
set -euo pipefail
board=$1 branch=$2
message=$(mktemp)
{
  echo "Route $board on CI: stage $STAGE, open edges $OPEN_BEFORE -> $OPEN_AFTER"
  echo
  echo "Adopted grid-routing stage pushed as soon as it was promoted."
  echo "Unvalidated draft; electrical and physical qualification NOT RUN."
  echo
  echo "Run: ${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY:-}/actions/runs/${GITHUB_RUN_ID:-local}"
} > "$message"
bash scripts/pcbgen/ci_push_route.sh "$board" "$branch" "$message"
rm -f -- "$message"
