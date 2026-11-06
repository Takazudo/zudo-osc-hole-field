# Stage41 disposable B1 output-loop pilot

This is an additive, bounded native electrical/connectivity study on the incumbent jack-left board. It does not adopt the placement or copper into canonical CAD. Parent PR286, every historical stage and manufacturing outputs remain unchanged. The 117 pre-existing native open edges remain a board-level qualification blocker.

## Scope and proposed geometry

The pilot contains U3102, C3101/C3102/C3103/C3106/C3107 and R3105–R3113: 15 footprints. R3109 remains at its current native rear pose to preserve input/indicator clearance. Relative to Stage40, the U3102/two-bypass rigid cluster moves +0.2 mm in native Y and C3101 moves +1.0 mm in native X. Other scoped poses follow Stage40. The receipt records pad identities, faces and native angles. Its `origin` uses the Stage40 study frame; add (100,50) mm for the native board origin. Its pad `xy_mm` values are already native board coordinates.

Fourteen explicitly disturbed terminal nets are rerouted, including connections to retained fixed jacks and retained indicator circuitry. Their packages remain fixed; do not describe all their terminal copper as untouched. The 534 exact private copper occurrences are retired separately from five reviewed local supply occurrences. The two positive-supply anchor vias stay because one also touches a retained In2.Cu rail track. No other foreign/shared copper is removed. There are 601 proposed new copper objects: 591 signal objects and ten supply/return objects.

The two IC-to-bypass links are each 2.2975 mm planar F.Cu traces. Each capacitor has a 1.0 mm supply fanout and a 1.0 mm AGND return fanout, each ending in a through via. Native checks require +12V/In4.Cu, −12V/In3.Cu and both AGND/In1.Cu connections. These lengths exclude pad internal paths, via vertical distance and plane spread; they are not closed-loop lengths or inductance claims.

## Feedback copper inventory

These are planar segment-centerline sums per feedback net, including branches; they exclude pad internal paths, via vertical distance and plane spread.

| U3102 feedback pin | Native baseline mm / vias | Pilot mm / vias |
| --- | ---: | ---: |
| 6 | 18.750 / 4 | 10.175 / 2 |
| 9 | 22.169 / 3 | 5.050 / 2 |
| 13 | 24.567 / 4 | 5.319 / 2 |
| Total | 65.487 / 11 | 20.544 / 6 |

All14 affected nets, including output-side feedback connections, are inventoried in `evidence/metrics.json`. This is not an extracted closed-loop electrical model or proof of stability.

## Acceptance boundary

Use the final `settlement.json` and independent review receipt for completed-run status. Acceptance means only the bounded native electrical/connectivity pilot:

- Every original pad/copper net identity and geometry is preserved except exact reviewed retirements, explicit new copper and the 15 prepared footprints. Eleven duplicate segment UUID pairs are handled as distinct occurrences.
- All 14 disturbed nets close, with no new isolated islands and every retained connectivity partition equal to the baseline. Native total remains 117 pre-existing opens.
- Zero reported native error-level violations and zero schematic parity issues, using unchanged project rules.
- Both IC-to-cap links and all four supply/return fanouts pass native connection checks, including explicit filled-plane contacts.
- Three equal full connectivity memberships plus a fresh-copy check, with exact board hashes.

This is **not a full-board DRC pass**. KiCad10.0.6 hard-caps most violation categories at199 (clearance/unconnected at499). Both silkscreen categories reach199, and their reported item samples vary; exhaustive silkscreen warning nonregression is unresolved. The source confirms truncation but does not establish the cause of these particular sample changes. Uncapped warnings are compared separately. No project rule, severity, threshold or native binary was changed to bypass the reporting limit. [Exact KiCad source](https://github.com/KiCad/kicad-source-mirror/blob/10.0.6/pcbnew/drc/drc_engine.cpp#L929).

## Reproduction and tools

Exact-release CLI and pcbnew10.0.6 run via `scripts/kicad/run.sh` with task-local `KICAD_CLI_BIN`; this is not a bitwise claim about the repository's pinned Docker image. Official archive SHA256 is `8c789e36644856cff30a66801692881582b9ca7c7475699494e614ce1bcb1f9c`. Official MD5 matched. Detached signature verification was not completed because its public-key endpoint returned403. No Docker retry or canonical regeneration is required by these scripts.

Native scripts require that exact release. Signal search used the existing numerical environment (NumPy2.2.6, SciPy1.15.3, Shapely2.1.2), a 0.05 mm raster, unchanged 0.25 mm clearance and 0.2 mm signal width. Search success alone never accepts a candidate. All native/heavy work runs sequentially through the installed machine-wide heavy guard. Stdlib regression tests do not need native KiCad.

Sequence: `prepare.py` → native placement DRC/audit → `route_power.py` → existing `grid_apply.py` to a fresh disposable output → native DRC/audit/dump → `route_signals.py --resolution .05` → explicit proposal apply → DRC/audit/full connectivity → `inspect_local_branches.py` and `retire_branches.py` → repeated/fresh native checks. `compare_connectivity.py`, `verify_power.py` and `settlement.py` bind the evidence. No script promotes the candidate to canonical boards. Actual command scripts and first failures are retained in the ignored evidence archive, with small reviewable inputs/receipts committed here.

## Remaining decisions and measurements

No new owner decision is needed to retain this reversible pilot. Canonical adoption, full-cell/B2 replication and architecture expansion require separate review. The next cloud-capable step is a bounded integration assessment of the rest of B1 using the same complete identity/connectivity gates; it has not been performed here.

Before any physical qualification, make an unpowered populated mock-up and record:

1. Exact component heights, board thickness, solder tails, installed stack datums, support registration and worst-case board bow. Reject any interference with retained neighboring/connector/enclosure volumes; an unmeasured neighbor remains unknown/occupied.
2. Actual front/rear seating and tool access for U3102, all three feedback groups and both bypasses. Reject inaccessible assembly/rework or contact with foreign hardware; do not assume native courtyard clearance proves populated Z fit.
3. Core/board removal and connector withdrawal sequence, recording minimum clearance, temporary support and cable motion at each step. Reject loss of support, forced flex, trapped connectors or need to move locked front hardware.
4. Unpowered continuity and isolation for all14 affected nets, both bypass returns and supplies, using the exact net/pad manifest. Reject an unintended bridge/open; a mock-up result does not resolve the board's117 known native open edges.
5. Wire/ribbon identity, installed and service lengths, cut tolerances and repeated-flex radius from primary data or measured qualification. These earlier harness inputs remain unresolved; this copper pilot establishes none of them.

No energization, physical electrical performance measurement, fabrication, ordering, release, deployment or merge occurred. Analog stability, leakage, impedance, thermal behavior, optical alignment and manufacturing qualification remain open.
