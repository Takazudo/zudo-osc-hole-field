#!/usr/bin/env bash
set -euo pipefail

script_dir=${BASH_SOURCE[0]%/*}
repo_root=$(cd "$script_dir/../.." && pwd -P)
check_mode=false

if (($# > 1)); then
  printf 'Usage: bash scripts/checks/regen-all.sh [--check]\n' >&2
  exit 2
fi
if (($# == 1)); then
  if [[ $1 != --check ]]; then
    printf 'Usage: bash scripts/checks/regen-all.sh [--check]\n' >&2
    exit 2
  fi
  check_mode=true
fi

cd "$repo_root"
if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  printf 'regen-all.sh must run inside a Git worktree.\n' >&2
  exit 2
fi

before_diff=
if [[ $check_mode == true ]]; then
  before_diff=$(mktemp "${TMPDIR:-/tmp}/regen-all-before.XXXXXX")
  after_diff=${before_diff}.after
  trap 'rm -f -- "$before_diff" "$after_diff"' EXIT
  git diff --binary HEAD > "$before_diff"
fi

python3 scripts/checks/check_catalogue_publication.py

generators=(
  scripts/geometry/regen.sh
  scripts/libgen/regen.sh
  scripts/schgen/regen.sh
  scripts/partition/regen.sh
  scripts/schgen/regen-boards.sh
  scripts/panel/regen.sh
)

for generator in "${generators[@]}"; do
  if [[ -f $generator ]]; then
    bash "$generator"
  fi
done

python3 scripts/schgen/generate_monitor_permit.py
python3 scripts/checks/monitor_permit_behavior.py
python3 scripts/checks/monitor_permit_current.py
python3 scripts/checks/negative_inverter_candidate.py
python3 scripts/checks/monitor_reference_capacitance.py
python3 scripts/checks/monitor_reference_validity.py
python3 scripts/checks/monitor_reference_compatibility.py
python3 scripts/checks/monitor_fault_retiming.py
python3 scripts/checks/monitor_permit_rc.py
python3 scripts/checks/monitor_permit_native.py
bash scripts/kicad/run.sh python3 scripts/libgen/fixtures/check_wrl_dimensions.py

if [[ $check_mode == true ]]; then
  git diff --binary HEAD > "$after_diff"
  if ! cmp -s "$before_diff" "$after_diff"; then
    printf 'Regeneration changed tracked files; run bash scripts/checks/regen-all.sh and review the diff.\n' >&2
    exit 1
  fi
fi
