#!/bin/sh
# Mounted read-only from the guard's private snapshot, outside writable /work.
set -eu
gate=$1
deadline=$2
token=$3
shift 3
cid=$(cat "$gate/container-id")
case "$cid" in *[!0-9a-f]*|'') exit 125;; esac
[ ${#cid} -eq 64 ] || exit 125
expected="$token:$cid"
while :; do
  remaining=$((deadline - $(date +%s)))
  [ "$remaining" -gt 0 ] || exit 124
  if [ -f "$gate/ack" ]; then
    [ "$(cat "$gate/ack")" = "$expected" ] || exit 125
    break
  fi
  sleep 0.1
done
mkdir -p "$HOME/.config" "$HOME/.cache" "$HOME/.local/share" "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
# Admission consumes the same absolute deadline, never a fresh timeout budget.
remaining=$((deadline - $(date +%s)))
[ "$remaining" -gt 0 ] || exit 124
exec timeout --signal=TERM --kill-after=5s "${remaining}s" "$@"
