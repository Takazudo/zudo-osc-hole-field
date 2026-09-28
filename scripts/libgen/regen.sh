#!/usr/bin/env bash
set -euo pipefail

script_dir=${BASH_SOURCE[0]%/*}
repo_root=$(cd "$script_dir/../.." && pwd -P)
cd "$repo_root"

check_mode=false
if (($# > 1)); then
  printf 'Usage: bash scripts/libgen/regen.sh [--check]\n' >&2
  exit 2
fi
if (($# == 1)); then
  if [[ $1 != --check ]]; then
    printf 'Usage: bash scripts/libgen/regen.sh [--check]\n' >&2
    exit 2
  fi
  check_mode=true
fi

if [[ $check_mode == true ]]; then
  python3 scripts/libgen/gen_selector_assembly.py --check
  python3 scripts/libgen/gen_gh_connectors.py --check
  python3 scripts/libgen/build_symbol_lib.py --check
  python3 scripts/libgen/gen_courtyards.py --check
  python3 scripts/libgen/gen_component_envelopes.py --check
  python3 scripts/libgen/gen_ic_package_envelopes.py --check
else
  python3 scripts/libgen/gen_selector_assembly.py
  python3 scripts/libgen/gen_selector_diagram.py
  python3 scripts/libgen/gen_gh_connectors.py
  python3 scripts/libgen/build_symbol_lib.py
  python3 scripts/libgen/gen_courtyards.py
  python3 scripts/libgen/gen_component_envelopes.py
  python3 scripts/libgen/gen_ic_package_envelopes.py
fi
python3 scripts/libgen/check_lib.py
