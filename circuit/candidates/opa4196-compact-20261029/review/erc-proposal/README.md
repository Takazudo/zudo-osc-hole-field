# Proposal: clear the 262 inherited ERC warnings in the candidate trees

**PROPOSAL ONLY. Not applied.** The candidate trees stay byte-identical to their
reconstruction receipts, and the OPA4196 candidate stays unadopted. Both patches were
applied only to disposable copies under `.circuit-cache/opa4196-native/` for verification.
No board, DRC or fill was involved.

## What the 262 warnings are

Each of the four variants has the same set of 262 warnings, and the predecessor trees have the same set.

| Count | Type | Root cause | Owner |
| --- | --- | --- | --- |
| 228 | `pin_to_pin` | The embedded Kingbright LED symbols (APHHS1005QWF/D, APG1005SEC/E-T) type both pins `Unspecified`. KiCad warns where they meet passive diode/resistor/transistor pins or an LM393 open-collector output. | Repository library `symbols/src/Kingbright_*_0402.kicad_sym`, fixed in the repository. The trees carry frozen copies |
| 22 + 12 | `endpoint_off_grid` | The inherited R9000xx series-resistor rows (Series250k/Series14/79k splits) sit at round-millimetre centres (x 50/80/110 mm, y 590–960 mm), not on the 1.27 mm grid. 22 symbol pins and 12 joining wires are reported. | Predecessor development baseline (handoff generator, not in this repository) |

The 228 pin pairs are 172 bridge nodes (LED anode to diode cathode, LED cathode to diode anode), 12+12 transistor-collector sinks with anode resistors, 10+10 LM393 open-collector sinks with anode resistors, and 6+6 DH steering-diode nodes. All of them match forward-connected indicators.

The native netlist shows that every off-grid endpoint is still connected exactly as the pin map records. **No warning hides a connectivity defect.**

## Patches

| File | Applies to | Effect |
| --- | --- | --- |
| `series-rows.snap.patch` (`9916aa62…9c38`, from `snap_series_rows.py`) | all four variants, `--fuzz=0 -p1` | 22 R9000xx symbols move to the nearest 1.27 mm grid point. Their pin-end wires and end labels follow, and mid-wire labels snap onto their wire. Nothing else moves |
| `led-pin-types.patch` (from `led_pin_types.py`) | all four variants, after the snap patch | 28 LED pins retyped `passive`: 24 in the symbol copies embedded in nine sheets and 4 in the candidate library, matching the repository symbols |

## Native verification

The checks used KiCad 10.0.6 through `scripts/kicad/run.sh`, with every run under `flock`. The reference is the unmodified candidate output of `../native_checks.py`.

| Stage | Result file | ERC per variant | Nets / components |
| --- | --- | --- | --- |
| snap only | `verification-snap.json` | 262 → 228 (off-grid 34 → 0) | identical; netlist text identical apart from header |
| snap + LED | `verification-snap-led.json` | 262 → 0 | identical; netlist text identical apart from header and pin-type tokens |

## Open

| Item | Status |
| --- | --- |
| Apply the patches to the candidate trees (a new candidate revision with new hashes) | owner choice, together with the candidate's adoption review |
| Handoff generator for the Series rows | not in this repository; this patch is the proposed fix for its output |
