# Partial control-board copper checkpoint

`boards/osc-control/osc-control-routed-draft.kicad_pcb` is a reproducible,
**partially routed, unvalidated draft**. It preserves the checked control
layout's 418 source packages, 36 supports, 139 fixed controls, actual outline,
stack proposal and original reservations. The canonical partition outline is
still separate from this candidate.

`copper.json` owns 1,355 explicit track segments and 368 through vias, including
all 150 original main-terminal array vias. Its coordinates are native integer
nanometres. The constructor appends only this copper and the source-defined
ground pours to the checked labelled layout. It preserves all other input
bytes. Every main-array annulus remains inside its owning 4 × 4 mm terminal.

Fresh KiCad 10.0.6 checks give zero DRC violations, zero schematic parity
findings, **366 open edges** and **344/344 connected ground contacts**. A second,
independently loaded and refilled copy retains those counts. `ratsnest.json`
contains the complete per-net open-edge inventory; the truncated CLI DRC item
list is not used as a connectivity count. This is progress from 872 open edges
in the unrouted layout and 529 with the original ground prerequisite.

The third bounded autorouter attempt produced a partial session. Recovery
restored its omitted empty mechanical-footprint name and nine one-nanometre
import-rounding changes without moving original geometry. The recovered
stored fill hid four isolated ground pads. Fresh refill exposed them; four
short front-layer signal bridges now open those back-plane boundaries. One
additional via joins an unfinished B.Cu/In2.Cu signal transition. The explicit
source records every replaced segment and new bridge. All failed local runs
are retained; the router is not rerun to reproduce this checkpoint.

Ten further nonredundant same-block links reduce the retained 376-edge
checkpoint to 366 edges. These join short control and switch paths without
changing footprints or vias. A native connectivity
forest removed three redundant proposed links before adoption. All 344
ground contacts remain connected after independent refill.

Run the complete check through the pinned oracle and shared heavy guard:

```sh
bash scripts/kicad/run.sh python3 scripts/pcbgen/check_control_copper.py
```

The check first replays the underlying layout, then compares all generated
PCB/project/schematic/rule bytes, checks the complete native ratsnest and
source ground-contact inventory, and independently reloads/refills the board.
Source and input immutability are checked. Failed workspaces remain local.
Native front/rear previews are bound to the PCB and image hashes in
`views.json`; they are visual aids, not manufacturing output.

The final native replay passed in 40 seconds; independent reload/refill passed
in 43 seconds. Preview generation plus replay of the complete retained
connectivity report passed in 47 seconds. Local source-schema tests pass.
Combined source regeneration, native replay/refill, documentation build and
publication checks passed in 473 seconds. Strict links retain the single
pre-existing workbench exception. Post-merge regeneration passed in 270
seconds, including the exact-feedback standard-cell harness. The ten-link
extension passed native DRC, full-ratsnest, independent refill, regenerated
previews, four source tests and publication checks in 75 seconds. CI is
pending.

Current-source resistance/current analysis, rail-distribution compliance,
protection, source/inlet selection, manufacturing process and installed-fit
qualification remain open. The 4-layer, 2 oz, 1.6 mm stack is a proposal.
No historical ground/current receipt is rebound to this copper, and no
fabrication or order files are produced.
