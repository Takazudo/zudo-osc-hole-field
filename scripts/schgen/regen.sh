#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 scripts/schgen/generate.py
python3 -m design.spec.modules.check_oscillator_reference
python3 -m design.spec.modules.build_oscillator_current
python3 scripts/schgen/build_supply_architecture.py
