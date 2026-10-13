#!/usr/bin/env bash
set -euo pipefail

if (($# != 3)); then
  printf 'Usage: bash circuit/routing/epic-242/jr/run_native.sh ARCHIVE LABEL PARENT_SLOT\n' >&2
  exit 2
fi
archive=$(realpath "$1")
label=$2
parent_slot=$3
[[ -n $parent_slot && $label == 251-* ]] || exit 2
[[ -f $archive ]] || exit 2
repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"
source scripts/kicad/pin.env

# One container contains the host driver and every native child, so the 6 GiB
# bound also covers pcbnew, refills and Python rather than only a CLI process.
exec bash "$HOME/.codex/scripts/heavy-guard.sh" \
  --max-run 1200 --min-mem-mb 2048 --label "$label" -- \
  docker run --rm --platform linux/amd64 --network none \
  --memory 6g --memory-swap 6g --cpus 1 --pids-limit 128 \
  --user "$(id -u):$(id -g)" \
  --volume "$repo_root:/work" --volume "$archive:/inputs/jr129.zip:ro" \
  --workdir /work --env HOME=/tmp/jr251-home \
  --env KICAD_CLI_BIN=/usr/bin/kicad-cli --env PYTHONDONTWRITEBYTECODE=1 \
  --entrypoint /bin/bash "$KICAD_IMAGE" -c \
  'set -euo pipefail
   mkdir -p "$HOME"
   python3 -c "import numpy, scipy, shapely, pcbnew; assert shapely.__version__.startswith(\"2.\")"
   exec python3 circuit/routing/epic-242/jr/native_diagnostic.py /inputs/jr129.zip --label "$1" --native-slot "$2" --execute' \
  jr251-diagnostic "$label" "$parent_slot"
