#!/usr/bin/env bash
# Rebuild the complete E16 chain from tracked sources into a fresh directory.
# Usage: replay_e16.sh PYTHON OUTDIR [--board KA|KB]... [--through ROUND] [--resume]
# With no options this is the full fresh replay of both boards, serialized.
# PYTHON must carry the pinned numpy/scipy/shapely (scripts/pcbgen/numerical-requirements.txt).
# Source-only: no KiCad/native call. Each step keeps its own 180 s / 2 GiB bound.
set -euo pipefail
py=$1; out=$2; shift 2
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
[[ $out = /* ]] || { echo "absolute OUTDIR required" >&2; exit 2; }
exec "$py" "$here/replay_steps.py" --python "$py" --output "$out" "$@"
