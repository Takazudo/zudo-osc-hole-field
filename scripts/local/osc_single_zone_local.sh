#!/usr/bin/env bash
# Outer stop control for the local single-zone diagnostic: the controller runs
# in its own session (setsid, so its pid is its pgid) and is SIGKILLed as a
# group at 600 s, independent of its 590 s internal deadline. The oracle chain
# is bounded by the inner deadlines it receives; a bounded post-stop cleanup
# pass then removes owned containers by recorded CID/name and fails closed on
# an uncertain create record.
set -uo pipefail

if (($# < 4)); then
  printf 'Usage: bash scripts/local/osc_single_zone_local.sh SOURCE OUT STATE "AUTHORIZATION NOTE" [--payload zone|candidate|drc] [--output DIR] [--candidate DIR]\n' >&2
  exit 2
fi
source_dir=$1
out_dir=$2
state_dir=$3
authorization=$4
shift 4
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
outer_stop_seconds=600
cleanup_seconds=60

if [[ ${HEAVY_GUARD_HELD:-} != 1 ]]; then
  printf 'osc-single-zone-local: run this through heavy-guard.sh (HEAVY_GUARD_HELD missing)\n' >&2
  exit 3
fi

if [[ -z ${TOOLING_SHA:-} ]]; then
  TOOLING_SHA=$(git -C "$script_dir" rev-parse HEAD) || exit 4
  export TOOLING_SHA
fi

setsid python3 -B "$script_dir/osc_single_zone_local.py" run "$source_dir" "$out_dir" \
  --state "$state_dir" --authorization "$authorization" "$@" &
pid=$!
start_seconds=$SECONDS
killed=0
while kill -0 "$pid" 2>/dev/null; do
  if ((SECONDS - start_seconds >= outer_stop_seconds)); then
    killed=1
    # After setsid the controller's process group id equals its pid.
    kill -KILL -- "-$pid" 2>/dev/null
    kill -KILL "$pid" 2>/dev/null
    break
  fi
  sleep 0.5
done
wait "$pid"
rc=$?
printf 'osc-single-zone-local: controller exit=%s killed_at_outer_stop=%s wall_seconds=%s tooling_sha=%s\n' \
  "$rc" "$killed" "$((SECONDS - start_seconds))" "$TOOLING_SHA" >&2

timeout -s KILL "$cleanup_seconds" python3 -B "$script_dir/osc_single_zone_local.py" cleanup "$state_dir" "$out_dir"
cleanup_rc=$?
printf 'osc-single-zone-local: post-stop cleanup exit=%s\n' "$cleanup_rc" >&2

if ((rc != 0 || cleanup_rc != 0 || killed != 0)); then
  exit 1
fi
exit 0
