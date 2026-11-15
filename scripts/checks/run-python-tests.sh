#!/usr/bin/env bash
set -euo pipefail

# CI runs frozen and current as separate 30-minute jobs (scripts/checks/CI-TIMEOUT-DIAGNOSIS.md).
usage='Usage: bash scripts/checks/run-python-tests.sh [all|frozen|current]'
if (($# > 1)); then
  printf '%s\n' "$usage" >&2
  exit 2
fi
mode=all
if (($# == 1)); then
  mode=$1
fi
case "$mode" in
  all) label='Python unit tests' ;;
  frozen) label='Superseded study replay' ;;
  current) label='Current-tree Python unit tests' ;;
  *)
    printf 'Unknown mode: %s\n%s\n' "$mode" "$usage" >&2
    exit 2
    ;;
esac

# Superseded studies replay unchanged at their pinned commits (scripts/checks/frozen-studies.json).
frozen_studies=scripts/checks/frozen_studies.py
total_tests=0

replay_frozen_studies() {
  printf '%s\n' 'Replaying superseded studies at their pinned commits'
  if output=$(python3 "$frozen_studies" replay 2>&1); then
    printf '%s\n' "$output"
  else
    status=$?
    printf '%s\n' "$output" >&2
    exit "$status"
  fi
  count=$(printf '%s\n' "$output" | sed -nE 's/^Ran ([0-9]+) tests? in frozen study worktrees/\1/p' | tail -n 1)
}

if [[ "$mode" == frozen ]]; then
  if [[ ! -f "$frozen_studies" ]]; then
    printf 'Missing superseded study registry script: %s\n' "$frozen_studies" >&2
    exit 1
  fi
  replay_frozen_studies
  if [[ -z "$count" || "$count" -eq 0 ]]; then
    printf '%s\n' 'Superseded study replay reported no executed tests.' >&2
    exit 1
  fi
  printf '%s: %d tests ran.\n' "$label" "$count"
  exit 0
fi

test_roots=()
for root in scripts design; do
  if [[ -d "$root" ]]; then
    test_roots+=("$root")
  fi
done

if ((${#test_roots[@]} == 0)); then
  printf '%s\n' "$label: 0 tests ran (scripts/ and design/ are absent)."
  exit 0
fi

# This frozen host-run snapshot expects an external osc-validation checkout.
# Its portable comparator and all mutation cases live under scripts/ instead.
archived_harness=design/architecture-278/implementation/stage17-native-x0x-001
portable_parity=scripts/architecture278/implementation/test_stage17_native_parity.py
if [[ -d "$archived_harness" ]]; then
  if [[ ! -f "$portable_parity" ]]; then
    printf 'Missing portable replacement for archived parity tests: %s\n' "$portable_parity" >&2
    exit 1
  fi
  printf 'NOT RUN: frozen host harness %s/; portable parity coverage: %s\n' "$archived_harness" "$portable_parity"
fi

mapfile -d '' -t test_files < <(
  find "${test_roots[@]}" -path "$archived_harness" -prune -o -type f -name 'test_*.py' -print0 | sort -z
)

if ((${#test_files[@]} == 0)); then
  printf '%s\n' "$label: 0 tests ran (no test_*.py files found)."
  exit 0
fi

declare -A discovery_roots=()
for test_file in "${test_files[@]}"; do
  # Discover only directories that contain tests. Python 3.13 exits 5 for
  # an empty discovery root, even when another root has runnable tests.
  discovery_roots["${test_file%/*}"]=1
done

mapfile -t ordered_discovery_roots < <(printf '%s\n' "${!discovery_roots[@]}" | sort)

if [[ "$mode" == all && -f "$frozen_studies" ]]; then
  replay_frozen_studies
  total_tests=$((total_tests + ${count:-0}))
fi

for directory in "${ordered_discovery_roots[@]}"; do
  printf 'Discovering tests under %s/\n' "$directory"
  command=(python3 -m unittest discover --start-directory "$directory" --pattern 'test_*.py')
  if [[ -f "$frozen_studies" ]]; then
    command=(python3 "$frozen_studies" discover "$directory")
  elif [[ "$directory" == scripts/architecture278/implementation ]]; then
    command=(python3 scripts/checks/architecture_history.py)
  fi
  if output=$("${command[@]}" 2>&1); then
    printf '%s\n' "$output"
  else
    status=$?
    printf '%s\n' "$output" >&2
    exit "$status"
  fi

  count=$(printf '%s\n' "$output" | sed -nE 's/^Ran ([0-9]+) tests?.*/\1/p' | tail -n 1)
  total_tests=$((total_tests + ${count:-0}))
done

printf '%s: %d tests ran.\n' "$label" "$total_tests"

printf "%s\n" "NOT RUN: retained-artifact integration requires preserved local issue-38 artifacts; run bash scripts/checks/run-retained-artifact-tests.sh separately."
