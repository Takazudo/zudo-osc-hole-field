#!/usr/bin/env bash
set -euo pipefail

test_roots=()
for root in scripts design; do
  if [[ -d "$root" ]]; then
    test_roots+=("$root")
  fi
done

if ((${#test_roots[@]} == 0)); then
  printf '%s\n' 'Python unit tests: 0 tests ran (scripts/ and design/ are absent).'
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
  printf '%s\n' 'Python unit tests: 0 tests ran (no test_*.py files found).'
  exit 0
fi

declare -A discovery_roots=()
for test_file in "${test_files[@]}"; do
  # Discover only directories that contain tests. Python 3.13 exits 5 for
  # an empty discovery root, even when another root has runnable tests.
  discovery_roots["${test_file%/*}"]=1
done

mapfile -t ordered_discovery_roots < <(printf '%s\n' "${!discovery_roots[@]}" | sort)
total_tests=0

for directory in "${ordered_discovery_roots[@]}"; do
  printf 'Discovering tests under %s/\n' "$directory"
  command=(python3 -m unittest discover --start-directory "$directory" --pattern 'test_*.py')
  if [[ "$directory" == scripts/architecture278/implementation ]]; then
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

printf 'Python unit tests: %d tests ran.\n' "$total_tests"

printf "%s\n" "NOT RUN: retained-artifact integration requires preserved local issue-38 artifacts; run bash scripts/checks/run-retained-artifact-tests.sh separately."
