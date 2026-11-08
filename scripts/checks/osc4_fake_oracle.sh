#!/usr/bin/env bash
# Fake native oracle for scripts/checks/test_osc4_transaction_signals.py.
# Mirrors scripts/kicad/run.sh: bash waits on a foreground grandchild, as run.sh waits on the docker client.
# Usage: osc4_fake_oracle.sh <mode> <seconds> <pidfile>
#   quick   exit 0 at once                     fail    exit 7 at once
#   sleep   the grandchild sleeps <seconds>    ignore  the grandchild sleeps and ignores SIGINT/SIGTERM (uncooperative)
# Every process appends its PID to <pidfile> so the test can prove nothing was left behind.
set -euo pipefail
mode=$1; seconds=${2:-60}; pidfile=${3:-/dev/null}
echo "$$" >> "$pidfile"
case $mode in
  quick) echo "fake oracle: ok"; exit 0 ;;
  fail) echo "fake oracle: failed"; exit 7 ;;
  sleep|ignore)
    python3 - "$mode" "$seconds" "$pidfile" <<'PY'
import os,signal,sys,time
mode,seconds,pidfile=sys.argv[1],float(sys.argv[2]),sys.argv[3]
if mode=='ignore':
    signal.signal(signal.SIGINT,signal.SIG_IGN);signal.signal(signal.SIGTERM,signal.SIG_IGN)
with open(pidfile,'a') as f:f.write(f'{os.getpid()}\n')
time.sleep(seconds)
PY
    ;;
  *) echo "fake oracle: unknown mode $mode" >&2; exit 2 ;;
esac
