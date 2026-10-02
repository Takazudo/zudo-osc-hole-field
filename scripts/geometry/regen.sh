#!/usr/bin/env bash
set -euo pipefail

script_dir=${BASH_SOURCE[0]%/*}
repo_root=$(cd "$script_dir/../.." && pwd -P)
cd "$repo_root"
python3 scripts/geometry/build_placements.py
python3 scripts/checks/check_led_window_facts.py
