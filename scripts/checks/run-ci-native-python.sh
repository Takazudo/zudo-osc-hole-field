#!/usr/bin/env bash
# Exact existing Python-job native checks, executed within one admitted worker.
set -euo pipefail

bash scripts/libgen/fixtures/check_ic_units.sh
bash scripts/pcbgen/test_placer.sh
bash design/spec/cells/check_harness.sh
bash scripts/kicad/run.sh python3 scripts/pcbgen/power_locality_native_regression.py
bash scripts/pcbgen/test_fixture.sh
python3 scripts/checks/monitor_permit_native.py --check
python3 scripts/checks/monitor_permit_rc.py --check
bash scripts/kicad/run.sh python3 scripts/libgen/fixtures/check_courtyard_minimum.py
bash scripts/kicad/run.sh python3 scripts/libgen/fixtures/check_wrl_dimensions.py --check
bash scripts/kicad/run.sh python3 scripts/panel/check_feature_mutations.py
bash scripts/pcbgen/test_route.sh --dense
bash scripts/kicad/run.sh python3 scripts/pcbgen/fixtures/check_fixed_only.py
bash scripts/kicad/run.sh python3 scripts/pcbgen/fixtures/check_octave_labels.py
bash scripts/kicad/run.sh python3 scripts/pcbgen/check_octave.py --disposable
bash scripts/kicad/run.sh python3 scripts/pcbgen/fixtures/check_octave_mutations.py
bash scripts/kicad/run.sh python3 scripts/pcbgen/check_stage_optical.py --disposable
bash scripts/kicad/run.sh python3 scripts/pcbgen/check_control_copper.py
bash scripts/checks/regen-all.sh --check
