# Conditional board partition generation

`bash scripts/partition/regen.sh` exports the current master with pinned KiCad10.0.6, checks native source parity and generates the I/O, stage, exact GH, courtyard, loom, support, nine-board definition and decision reports. It ends with an in-memory native footprint transform oracle. `--check` rejects drift. No KiCad PCB is drawn or saved.

Inputs are `design/partition/partition-input.json`, `stage-optical-input.json`, current schematic sources, retained mechanical/connector/wire evidence, and the fixed placement lock. Edit those inputs/generators, then regenerate. The aggregate `scripts/checks/regen-all.sh` calls this sequence after schematic generation; #35 itself intentionally leaves panel regeneration to #37.

The floorplan's source rotations are clockwise after an X reflection on B.Cu. Use `kicad_orientation_deg` when creating actual footprints. The native oracle verifies all used footprint/face/rotation classes. Drawn courtyards get a 0.35 mm free-placement separation and 0.30 mm board-edge allocation; KiCad's observed0.045 mm cached expansion per edge is bounded by 0.05 mm. Do not shrink a footprint or lower these margins to force a placement.

`floorplan-candidate.json` is a complete capacity proposal, not a routed PCB or a locality-optimized final layout. #38 must extend the current single-face-per-module placer to consume J's per-reference face map; the current strict board-definition parser already accepts the regions. Preserve all whole packages, same-board Sensitive islands and close bypass loops while doing actual placement/routing.

The historical `diagnostic35` and reference-fanout records are superseded snapshots. They are not current BLOCKED verdicts. Physical #55/#57/#64/#65 gates and exact #59 protection remain open independently of conditional source arithmetic.
