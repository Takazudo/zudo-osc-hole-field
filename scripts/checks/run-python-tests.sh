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

mapfile -d '' -t test_files < <(
  find "${test_roots[@]}" -type f -name 'test_*.py' -print0 | sort -z
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
  if output=$(python3 -m unittest discover --start-directory "$directory" --pattern 'test_*.py' 2>&1); then
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
