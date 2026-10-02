# Current unrouted P layout candidate

`boards/osc-control/osc-control-layout.kicad_pcb` is a reproducible **unvalidated,
unrouted draft**, separate from the canonical partition outline. It contains
418 source packages, 36 board-only supports and all 139 fixed P controls.
The H1/H2 slew groups use the current compact source positions. No panel
hardware moved.

The candidate applies the already reviewed RV601 edge tab and individual
power-terminal reservations from `control-ground-feasibility/proposal.json`.
The tab gives 0.65 mm nominal clearance to the mounting-pad copper and 0.95 mm
to its drill. The original broad reservation is replaced by six finite
terminal reservations, with source-identity-specific owning-pad exceptions.
The conditional O5 neighbor envelope remains in `osc-control.receipt.json`;
it is not installed-fit qualification. Canonical adoption remains a separate
source-architecture step.

All 418 visible references use 1 mm text and 0.15 mm strokes. Explicit source
positions preserve at least the checked 0.15 mm clearance from same-face
courtyards, mask pad projections, other silk and other references, with
0.25 mm board-edge clearance. The generator copies only the selected
reference fields into the original PCB bytes. This avoids KiCad introducing
unselected dielectric or hidden-text defaults when serializing the board.

The project applies the proposed Default/Ground/Rails classes with 0.25 mm
clearance and the 0.2 mm minimum-track rule. **No tracks, ground planes or via
arrays are added.** Fresh native DRC has zero violations and zero schematic
parity findings; full native connectivity still has **872 open edges over
348 multi-pad candidate nets**. CLI DRC lists only 499 unconnected items, so
that truncated list is not used as the connectivity count.

Run the complete disposable replay through the pinned oracle:

```sh
bash scripts/kicad/run.sh python3 scripts/pcbgen/check_control_layout.py
```

The replay regenerates the source definition and receipt, constructs a fresh
bare board, applies the reference positions, compares complete PCB/project/
schematic/rule bytes against the pinned complete rule/class configuration,
runs four rejection controls, and performs fresh native
DRC and full connectivity checks. CI runs the same replay. Failed replay
evidence is retained locally. Heavy local runs use the shared heavy guard.

Validation history: the initial source-position pass and 1,117 unit tests
passed (the system-Python run needed the existing pinned numerical environment
for its remaining directories). The first disposable-layout replay failed
because its temporary project omitted board-local library tables; the
corrected replay passed in 13 seconds, then the replay with all four rejection
controls passed in 11 seconds. The first failed replay's console log was
retained, but its temporary detailed DRC report was not; the checker now
preserves failed workspaces. The pinned-rule replay then passed in 12 seconds.
The earlier label-search failures are retained
in local work logs; `reference-positions.json` is the checked result, and CI
does not repeat that search.

The 4-layer, 2 oz, 1.6 mm stack is still a proposal. Routing, current-source
copper analysis, exact power/protection, manufacturing process, installed
clearance and physical qualification remain open. Historical ground/current
receipts are not rebound to the 18 moved slew packages. No order files are
created, and this candidate cannot enter a conductor model as a connected PCB.

Final local replay, including dependency immutability: PASS, 42 seconds. Documentation build and site checks: PASS, 68 seconds, with the existing single workbench-link allowlist exception unchanged. The three reference-byte ownership tests pass. Integrated CI is pending.
