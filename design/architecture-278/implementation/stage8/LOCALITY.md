# Stage8 X1 output locality and bounded copper corridors

This source candidate relocates eight complete packages. U3305, C3301, C3308, C3309 and R3314–R3316 move together into the output-jack neighborhood. R3313 relocates to origin [108.5, 282.0] mm below U3303 to clear the control substrate edge. C3308 rotates as a whole package by 180 degrees to separate supply and return pad escapes without changing pin assignments. All 56 source packages, their units and pin/net records, ten bypass associations and seven fixed X1 devices remain present. Stage7 artifacts remain unchanged.

The proposed copper uses 0.20 mm trace width, 0.20 mm copper clearance, 0.25 mm substrate-edge clearance and 0.60 mm via pad diameter and 0.30 mm drill (0.15 mm nominal annular ring). These are candidate engineering inputs, not approved fabrication rules. Actual pad dimensions are read from the retained footprints; the transformed pad locations come from the mechanical placement report. Unknown or unaccounted footprint pads fail closed.

| Connection | Stage7 pad distance mm | Stage8 pad distance mm | Proposed copper centreline mm | Vias |
|---|---:|---:|---:|---:|
| U3305:8–C3301:1, fast feedback output | 9.1178 | 2.5601 | 3.6875 | 0 |
| U3305:9–C3301:2, fast feedback input | 9.3739 | 4.0812 | 5.8375 | 0 |
| U3305:9–R3316:2, sense feedback | 4.9125 | 5.0191 | 6.4875 | 1 |
| R3316:1–J1009:T, output sense | 54.1472 | 12.7737 | 15.9300 | 0 |
| U3305:8–R3314:1, output isolation feed | 8.1086 | 12.3192 | 26.8750 | 3 |
| R3314:2–R3315:1, isolation chain | 8.5738 | 3.3531 | 9.7250 | 2 |
| R3315:2–J1009:T, isolated output | 48.2406 | 7.5774 | 9.1925 | 0 |
| U3305:4–C3308:1, positive bypass feed | 2.2975 | 2.8551 | 4.1375 | 0 |
| U3305:11–C3309:1, negative bypass feed | 2.3513 | 4.0683 | 4.6375 | 0 |
| C3308:2–C3309:2, local AGND tie | 10.3321 | 12.5591 | 24.1000 | 0 |

Pad distances include actual face depth; the copper column is planar centreline length and excludes each explicit 1.6 mm via barrel. The report records planar copper and explicit via barrels separately, accounts for any through-hole endpoint face change as `endpoint_THT_barrel_mm`, and sums all three in `developed_copper_and_barrel_mm`. A through-hole terminal entered on the opposite copper face adds its own 1.6 mm barrel even when no new via is added. Improved sense and fast-feedback geometry does not mean every local connection improves: the isolation feed and bypass spans grow, and the sense-amplifier feedback branch increases slightly. All connected-net maximum-span changes are retained in the report. No universal feedback-length or stability threshold is inferred.

The deterministic router uses the actual conservative manufacturing cut bounds, including the mechanical report’s process tolerances, rather than the narrower ideal openings. These bounds depend on the explicitly requested precision process, which has not been accepted by a supplier; the standard-process negative comparison remains in the mechanical report. It excludes mounting/attachment envelopes, header courtyards, same-face package courtyards and actual other-net pads; through-hole pads block both faces. Width and edge-clearance inflation apply to segment sweeps and vias. A pad escape can cross only its own package courtyard; other pads and substrate exclusions remain active. Endpoint escape segments are checked inside the outline. Each successful corridor reserves its trace and via copper before the next different net is routed. Same-net sharing is allowed. The report exposes all obstacle IDs, boxes, source identities, actual endpoint XYZ, segment layers, courtyard escape exemptions and via locations for independent replay.

Ten corridors are present together under this conservative rectangular model. This is not a routed-board acceptance result. The capacitor AGND tie does not connect the entire return network to the power header. Remaining ground-return copper, plane continuity, complete power distribution, remaining signal routes, via fabrication, parasitics, return coupling and analog stability remain open. Grounded spare amplifier inputs are not treated as dedicated bypass returns. Mechanical body/cutout and carrier qualification constraints remain those of the mechanical report. No native KiCad/ERC/DRC, simulation, fabrication or physical execution occurred.

Reproduce with `python3 scripts/architecture278/implementation/stage8_locality.py --check` and the focused `test_stage8_locality.py` unit suite. Geometry and source hashes are embedded in `locality-report.json`.
