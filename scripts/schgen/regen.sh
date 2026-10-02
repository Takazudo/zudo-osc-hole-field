#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 scripts/schgen/generate.py
python3 -m design.spec.modules.build_sample_hold_current
python3 -m design.spec.modules.check_oscillator_reference
python3 -m design.spec.modules.run_oscillator_reference_model --refresh-load-bound
python3 -m design.spec.modules.build_oscillator_current
python3 -m design.spec.modules.run_offset_spice
python3 -m design.spec.modules.run_noise_spice
python3 scripts/schgen/build_supply_architecture.py
python3 scripts/schgen/build_supply_documentation.py
