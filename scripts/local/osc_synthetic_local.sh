#!/usr/bin/env bash
# Outer stop control for the local synthetic qualification. Independent of the
# controller's 115 s internal deadline: the controller runs in its own process
# group and is SIGKILLed as a group at 120 s. A bounded owned-container cleanup
# pass always follows, so a stopped run never leaves an owned container behind.
set -uo pipefail

if (($# != 4)); then
  printf 'Usage: bash scripts/local/osc_synthetic_local.sh SOURCE OUT STATE "AUTHORIZATION NOTE"\n' >&2
  exit 2
fi
source_dir=$1
out_dir=$2
state_dir=$3
authorization=$4
script_dir=$(cd "${BASH_SOURCE[0]%/*}" && pwd -P)
outer_stop_seconds=120
cleanup_seconds=40

if [[ ${HEAVY_GUARD_HELD:-} != 1 ]]; then
  printf 'osc-synthetic-local: run this through heavy-guard.sh (HEAVY_GUARD_HELD missing)\n' >&2
  exit 3
fi

setsid python3 -B "$script_dir/osc_synthetic_local.py" run "$source_dir" "$out_dir" \
  --state "$state_dir" --authorization "$authorization" &
pid=$!
pgid=$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' ')
start_seconds=$SECONDS
killed=0
while kill -0 "$pid" 2>/dev/null; do
  if ((SECONDS - start_seconds >= outer_stop_seconds)); then
    killed=1
    if [[ -n $pgid ]]; then kill -KILL -- "-$pgid" 2>/dev/null; fi
    kill -KILL "$pid" 2>/dev/null
    break
  fi
  sleep 0.2
done
wait "$pid"
rc=$?
printf 'osc-synthetic-local: controller exit=%s killed_at_outer_stop=%s wall_seconds=%s pgid=%s\n' \
  "$rc" "$killed" "$((SECONDS - start_seconds))" "${pgid:-unknown}" >&2

timeout -s KILL "$cleanup_seconds" python3 -B "$script_dir/osc_synthetic_local.py" cleanup "$state_dir" "$out_dir"
cleanup_rc=$?
printf 'osc-synthetic-local: post-stop cleanup exit=%s\n' "$cleanup_rc" >&2

if ((rc != 0 || cleanup_rc != 0 || killed != 0)); then
  exit 1
fi
exit 0
