#!/usr/bin/env bash
# Outer stop control for the local single-zone diagnostic: the controller runs
# in its own session (setsid, so its pid is its pgid) and is SIGKILLed as a
# group at the outer stop, independent of its internal deadline. The oracle
# chain is bounded by the inner deadlines it receives; a bounded post-stop
# cleanup pass then removes owned containers by recorded CID/name and fails
# closed on an uncertain create record.
#
# OSC_BUDGET selects the deadline chain (osc_derived_fill.BUDGETS): 'standard'
# (default) stops at 600 s around the 590 s controller; 'fill-520-probe' stops
# at 900 s around the 890 s controller. The chosen outer stop is exported as
# OSC_OUTER_STOP_SECONDS and the controller refuses a budget whose outer stop
# differs from what this wrapper enforces.
set -uo pipefail

if (($# < 4)); then
  printf 'Usage: [OSC_BUDGET=standard|fill-520-probe] bash scripts/local/osc_single_zone_local.sh SOURCE OUT STATE "AUTHORIZATION NOTE" [--payload zone|candidate|drc|derive|evaluate] [--output DIR] [--candidate DIR] [--spec FILE]\n' >&2
  exit 2
fi
source_dir=$1
out_dir=$2
state_dir=$3
authorization=$4
shift 4
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
budget=${OSC_BUDGET:-standard}
case "$budget" in
  standard) outer_stop_seconds=600 ;;
  fill-520-probe) outer_stop_seconds=900 ;;
  *)
    printf 'osc-single-zone-local: unknown OSC_BUDGET %s\n' "$budget" >&2
    exit 2
    ;;
esac
export OSC_OUTER_STOP_SECONDS=$outer_stop_seconds
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
  --state "$state_dir" --authorization "$authorization" --budget "$budget" "$@" &
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
printf 'osc-single-zone-local: controller exit=%s killed_at_outer_stop=%s outer_stop_seconds=%s budget=%s wall_seconds=%s tooling_sha=%s\n' \
  "$rc" "$killed" "$outer_stop_seconds" "$budget" "$((SECONDS - start_seconds))" "$TOOLING_SHA" >&2

timeout -s KILL "$cleanup_seconds" python3 -B "$script_dir/osc_single_zone_local.py" cleanup "$state_dir" "$out_dir"
cleanup_rc=$?
printf 'osc-single-zone-local: post-stop cleanup exit=%s\n' "$cleanup_rc" >&2

if ((rc != 0 || cleanup_rc != 0 || killed != 0)); then
  exit 1
fi
exit 0
