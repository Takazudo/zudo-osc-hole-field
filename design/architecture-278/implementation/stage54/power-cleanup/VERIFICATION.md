# Stage54 verification

Saved environment and repository versions reused. KiCad10.0.6 is invoked only
through `source /workspace/task-tools/kicad-10.0.6/env.sh` and
`bash scripts/kicad/run.sh`. No Docker/install, canonical regeneration, new PCB,
ERC/DRC, fabrication or physical work. This is a removal/accounting plan.

Actual source commands:
```
python3 design/architecture-278/implementation/stage54/power-cleanup/proposal.py .circuit-cache/stage54-candidate
python3 design/architecture-278/implementation/stage54/power-cleanup/accounting.py
python3 -O design/architecture-278/implementation/stage54/power-cleanup/proposal.py --check
python3 -O design/architecture-278/implementation/stage54/power-cleanup/accounting.py --check
```
The proposal compiler first compares all baseline rendered master schematic bytes
against committed canonical files. It removes only the explicit post-refinement
idle package/bypass keys, and renders into a new ignored directory. All unaffected
schematic files remain identical. Source replay checks the full proposal hashes.

Read-only native exports:
```
bash scripts/kicad/run.sh kicad-cli sch export netlist --format kicadsexpr -o .circuit-cache/stage54/base.net schematic/zudo-osc-hole-field.kicad_sch
bash scripts/kicad/run.sh python3 design/architecture-278/implementation/stage54/power-cleanup/native.py
bash scripts/kicad/run.sh python3 -O design/architecture-278/implementation/stage54/power-cleanup/native.py --check
```
The first canonical export establishes full source parity. `native.py` repeats it
with execution receipts and exports the disposable candidate; receipts retain exact
commands, return codes, stdout/stderr and schematic/output hashes. It also binds
actual candidate schematic bytes to the deterministic proposal rendering, then
checks the entire native pin map against the complete spec and every surviving pin
against baseline. Check mode reads existing exports only and never repairs evidence.
Large exports/renderings remain ignored locally; compact removed-pin inventory and
receipts are committed. Native parity is not analog functionality or hardware proof.

Focused tests use repository Python unittest:
```
python3 -m unittest scripts.checks.test_power_cleanup -v
python3 -O -m unittest scripts.checks.test_power_cleanup -v
```
Controls reject active inputs, externally used feedback nets, missing channels,
logical roles, incorrect bypass ownership/value and surviving native-pin changes.
Accounting tests preserve unknowns and source requirements, zero reserve/grouping
rebates, correct clip-model distinction and simultaneous Iq power. Source/native
report and review bindings stay portable; CI tests do not claim a fresh native
proposal export when they inspect retained evidence.

Read-only history verification uses Stage50 `check_bindings.py` normal/-O for seven
checkpoints/Stage41–50 plus explicit Stage51–53 manifests. `pnpm circuit:check`
before/after and `pnpm check` cover repository evidence/doc consistency. Manual
inventory68lines/0placements has no schematic/placement binding. Full historical
replay and aggregate regeneration remain bounded by exact-head CI. Final SHA and
terminal CI are recorded in Issue278/PR287, avoiding self-reference.

First review finding: the original OTA branch selector matched part keys and
omitted BP/LP and RISE/FALL feeds (eight rather than26principal branches). The
original output is retained in `evidence/first-incomplete-branch-inventory.json`;
it is superseded evidence, not the final accounting. Selection now follows IABC
net connectivity and verifies12filter+12envelope+2MIX4feeds. Two unused bias-off
branches are separate. A focused regression checks counts and actual nets.

Final local results:21focused tests PASS in normal and optimized Python, no skips.
Native optimized check PASS after full deterministic proposal replay and exact
receipt schematic-roster binding. Stage50 history checks PASS normal/-O; Stage51,
52 and53 SHA manifests PASS. `pnpm circuit:check` and `pnpm check` PASS, including
documentation consistency and TypeScript. No full historical simulation or local
aggregate regeneration was run; exact-head CI supplies those bounded checks.
