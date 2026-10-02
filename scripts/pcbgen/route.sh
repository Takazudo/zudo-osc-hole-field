#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd "${BASH_SOURCE[0]%/*}/../.." && pwd -P)
cd "$repo_root"
# The machine-wide queue guards the whole routing job, including container startup.
exec bash scripts/pcbgen/with_route_guard.sh python3 scripts/pcbgen/route.py "$@"
