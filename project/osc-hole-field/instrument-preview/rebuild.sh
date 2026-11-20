#!/usr/bin/env bash
# Rebuild the instrument 3D preview as a new dated snapshot of the current boards.
#   bash project/osc-hole-field/instrument-preview/rebuild.sh [source-commit]
# source-commit defaults to HEAD; pass the commit whose boards are checked out when
# running on a branch that only adds the snapshot. Reads board files, never writes them.
set -euo pipefail
here=$(cd "${BASH_SOURCE[0]%/*}" && pwd -P)
root=$(cd "$here/../../.." && pwd -P)
cd "$root"
commit=${1:-$(git rev-parse --short=10 HEAD)}
python3 "$here/extract.py" --base-commit "$commit"
python3 "$here/build.py"
python3 -m unittest "$here/test_extract.py"
python3 "$here/build.py" --check
node "$here/test_browser.mjs" --publish
printf 'Snapshot rebuilt from %s. Review the screenshots, then commit the instrument-preview data and doc/public/assets/osc-hole-field/instrument-3d*.\n' "$commit"
