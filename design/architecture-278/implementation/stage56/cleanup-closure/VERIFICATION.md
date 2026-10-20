# Stage56 verification record

Base `0f873098aa01ae2ff8cb2d36fd8ceaca38d5626f` (Stage55). Oracle: KiCad 10.0.6, image
`kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`
through `scripts/kicad/run.sh` (same digest via the `mirror.gcr.io` mirror). Linux
cloud container; no Mac or hardware.

## Commands, in order

```sh
python3 design/architecture-278/implementation/stage56/cleanup-closure/candidate.py
bash scripts/kicad/run.sh python3 design/.../pcb_cleanup.py boards/osc-core/osc-core.kicad_pcb \
  .circuit-cache/stage56/cleaned.kicad_pcb .circuit-cache/stage56/pcb-receipt.json \
  .circuit-cache/stage56/schematic-receipt.json
python3 design/.../pcb_fields.py .circuit-cache/stage56/cleaned.kicad_pcb \
  .circuit-cache/stage56/candidate/osc-core/osc-core.kicad_pcb \
  .circuit-cache/stage56/schematic-receipt.json .circuit-cache/stage56/fields-receipt.json
python3 design/.../native.py run      # candidate ERC, DRC, refilled ratsnest, rail clusters, ~28 min
python3 design/.../native.py audit    # writes native-audit.json
python3 design/.../native.py check    # replays it without writing; PASS, all 11 gates
python3 design/.../decoupling.py --check   # PASS
python3 -m unittest scripts/checks/test_stage56_cleanup_closure.py   # 9 tests OK; also with -O
python3 -m unittest scripts/checks/test_idle_quad_cleanup.py         # Stage55, 11 tests OK
pnpm circuit:check
```

**First attempt (retained in `evidence/first-attempt/`).** The first field step
deleted every dropped field from the footprints. DRC then reported 199+ parity items
`Missing symbol field 'Role' in footprint`, because the board renderer always emits
Role and Island (empty once dropped). `pcb_fields.py` was changed to set those two to
`""` and delete only LogicalCellKey; the run was then repeated from the field step.
The gate definitions were not changed between attempts.

**After independent review** (raw reports unchanged): `check` now compares instead of
rewriting the audit; a baseline-parity-zero gate (11 gates) and a binding of every
unchanged candidate input to the canonical board file were added; `pcb_fields.py`
now asserts every requested field was synchronised; the rail-cluster roster is
checked on both sides. The audit was regenerated from the same evidence.

## Evidence SHA256

| Item | SHA256 |
| --- | --- |
| Source PCB (canonical) | `fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10` |
| Cleaned PCB (before field sync) | `065b37d72d73adce895da6267abbff5150c8e3b826227bff51bd85b783d9a71a` |
| Candidate PCB (after field sync) | `0e69b44b4b48ede939960d09da873c08b05f26cbf22d542c1c28a342fd580a37` |
| Candidate refilled PCB (ratsnest input) | `d8959dd82f09d30ee8406f98e1130b033dca298fa8dae26b3bf4d056399b955c` |
| candidate-erc.json | `80f3140ea74ea673dbe84b00597db6a8c5905f644f3c2a6ed3e33c824373fbd3` |
| candidate-drc.json | `134ee915250d390b0344849e4bf77e36133ffdda0de97d91a177cf7b804f9487` |
| candidate-ratsnest.json | `c14ab91da79ef6d602bb71aa37e5d3d2fe65d797cd472f3ec2994522d2d85982` |
| candidate-rail-clusters.json | `e79fd788c5cc5e310f3c01ca5aec415ad0d382668070cb046314bbd3e32a1520` |

Baseline evidence is Stage55's, bound by the canonical source hash. Disposable PCBs
stay in `.circuit-cache/stage56/` (git-ignored). A second independent cleanup run
was not made for Stage56; determinism is inferred from the Stage55 rule, not shown.

## Status by check

| Check | Status |
| --- | --- |
| ERC, DRC, schematic parity, complete ratsnest, rail clusters, decoupling replay, unit tests | PASS (disposable candidate) |
| Capped warning types (hole_to_hole, silk_over_copper, silk_overlap) | NOT ESTABLISHED, KiCad 199 cap |
| Downstream use of dropped osc-core unit fields | NOT RUN beyond `pnpm circuit:check` |
| PDN impedance, analog behavior, thermal, assembly | NOT RUN |
| Canonical adoption, generator/BOM/worksheet update | NOT RUN, needs owner approval |
| Mac local run, hardware measurement | NOT RUN |
