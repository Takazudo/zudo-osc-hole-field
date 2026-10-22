#!/usr/bin/env bash
# Outer stop control for the local single-zone diagnostic: the controller runs
# in its own session (setsid, so its pid is its pgid) and is SIGKILLed as a
# group at the outer stop, independent of its internal deadline. The oracle
# chain is bounded by the inner deadlines it receives; a bounded post-stop
# cleanup pass then removes owned containers by recorded CID/name and fails
# closed on an uncertain create record.
#
# OSC_BUDGET selects the deadline chain (osc_derived_fill.BUDGETS); the outer
# stop and the required heavy-guard cap are read from that one table through
# the controller's 'budget' subcommand. The caller must set HEAVY_GUARD_MAX_RUN
# (heavy-guard reads it as its --max-run default; do not also pass --max-run)
# to at least the budget's heavy_guard_max_run, or this wrapper exits. The
# chosen outer stop and the cap are exported as OSC_OUTER_STOP_SECONDS and
# OSC_HEAVY_GUARD_MAX_RUN; the controller refuses a mismatch.
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
outer_stop_seconds=$(python3 -B "$script_dir/osc_single_zone_local.py" budget "$budget" outer_stop) || exit 2
guard_required=$(python3 -B "$script_dir/osc_single_zone_local.py" budget "$budget" heavy_guard_max_run) || exit 2
cleanup_seconds=$(python3 -B "$script_dir/osc_single_zone_local.py" budget "$budget" post_stop_cleanup) || exit 2
if [[ ! ${HEAVY_GUARD_MAX_RUN:-} =~ ^[0-9]+$ ]] || ((HEAVY_GUARD_MAX_RUN < guard_required)); then
  printf 'osc-single-zone-local: HEAVY_GUARD_MAX_RUN must be set to at least %s for budget %s (got %s)\n' "$guard_required" "$budget" "${HEAVY_GUARD_MAX_RUN:-unset}" >&2
  exit 3
fi
export OSC_OUTER_STOP_SECONDS=$outer_stop_seconds
export OSC_HEAVY_GUARD_MAX_RUN=$HEAVY_GUARD_MAX_RUN

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
