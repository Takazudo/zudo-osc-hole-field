#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 scripts/schgen/generate.py
python3 scripts/schgen/build_supply_architecture.py
