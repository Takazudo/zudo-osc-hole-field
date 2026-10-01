#!/usr/bin/env bash
# Standalone pcbnew regressions run under the pinned oracle, not unittest discovery.
set -euo pipefail
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
cd "$script_dir/../.."
if [[ ${HEAVY_GUARD_HELD:-0} != 1 ]]; then
  exec bash "$HOME/.codex/scripts/heavy-guard.sh" -- bash "$script_dir/test_native_prerequisites.sh"
fi
mkdir -p .circuit-cache
output=$(mktemp -d .circuit-cache/native-prerequisites.XXXXXX)
for name in control_terminal_access core_terminal_access two_layer; do
  bash scripts/kicad/run.sh python3 "scripts/pcbgen/${name}_native_regression.py" "$output/$name"
done
bash scripts/kicad/run.sh python3 scripts/pcbgen/core_fields_native_regression.py \
  "$output/core-fields.kicad_pcb" "$output/core-fields"
printf 'Native prerequisite regressions PASS; receipts retained in %s\n' "$output"
