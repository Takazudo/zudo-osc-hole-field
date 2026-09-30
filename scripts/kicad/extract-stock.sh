#!/usr/bin/env bash
set -euo pipefail

if (($# != 2)); then
  printf 'Usage: bash scripts/kicad/extract-stock.sh <Library> <Symbol-or-Footprint>\n' >&2
  exit 2
fi

script_dir=${BASH_SOURCE[0]%/*}
repo_root=$(cd "$script_dir/../.." && pwd -P)
cd "$repo_root"
bash scripts/kicad/run.sh python3 scripts/kicad/extract_stock.py "$1" "$2"
