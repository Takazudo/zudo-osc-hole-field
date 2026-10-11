# Exact local terminal-access validation

Source-only follow-up to the [O1 mask diagnosis](../diagnosis-o1/README.md).
The same authenticated K1402 and two-A inputs, four demands, anchors, common
bounds and design rules are retained. No router, A*, KiCad, native process or
copper writer runs. Both prior empty proposals remain unapplied; parent released
reservations 1420/1438. All native slots remain free. No new native packet is
justified by these results.

## What is checked

`exact_access.py` validates the complete swept capsule of a straight segment
against original foreign pad polygons, analytic track/via radii, NPTH holes,
track keepouts and the physical outline including cutouts. No endpoint has a
foreign-obstacle exemption. Same-net copper is traversable, but contact must be
with the exact named anchor on the correct layer/net. A sufficient contact rule
requires the start center strictly inside that polygon by at least 0.000001 mm;
off-pad, tangential and tiny edge-overlap contacts are not certified.

New through-vias are checked on every copper layer, against existing holes and
all own/foreign SMD pads, board clearance and via keepouts. Existing-hole spacing
retains the frozen conservative outer-radius rule. Rail width stays 0.5 mm,
signal width 0.3 mm, foreign-copper clearance 0.25 mm, board clearance 0.5 mm,
and via diameter/drill 0.6/0.3 mm. The collision epsilon only tightens acceptance.
The frozen method remains `29140d4e19d526eed3a02a73c33f8ce4219c78f0`;
production router and source producers are unchanged.

Queries include every potentially violating obstacle. Saved `checked_margins_mm`
are explicitly censored collision-screen values, not global minimum clearances;
null means no potentially violating candidate was nearby. It does not mean an
infinite physical margin. Exact here means non-raster geometry of the saved dump,
using floating-point polygon operations, not an independent native or physical
measurement of the board.

## Reproducible findings

Each endpoint is sampled at interior 0.1 mm global grid centers and its original
pad center. Legal start caps are extended in 16 directions by 0.25, 0.5, 0.75,
1, 1.25, 1.5 or 2 mm, with endpoints outside the pad by at least half the width.
These are finite local templates, not a route search or an exhaustive escape
analysis. Counts are witnesses, not unique routes, closures or productivity.

| Endpoint | K1402 legal starts / swept edges / edges with new via | two-A legal starts / swept edges / edges with new via |
| --- | ---: | ---: |
| +12V U1109.4 | 0 / 0 / 0 | 0 / 0 / 0 |
| +12V C1134.1 | 73 / 978 / 0 | 73 / 978 / 154 |
| -12V U1109.11 | 0 / 0 / 0 | 0 / 0 / 0 |
| -12V C1135.1 | 72 / 1634 / 33 | 72 / 1634 / 282 |
| AGND U1105.12 | 108 / 0 / 0 | 108 / 0 / 0 |
| AGND C1111.2 | 73 / 2581 / 4 | 73 / 2581 / 4 |
| TRI_SUM R1177.2 | 65 / 1709 / 0 | 65 / 1709 / 0 |
| TRI_SUM U1114.6 | 111 / 1599 / 0 | 111 / 1599 / 11 |

The supply-pad result is stronger than the finite sampling result. A continuous
whole-pad Lipschitz subdivision gives a maximum center-to-foreign-pad clearance
upper bound of **0.461395002 mm** for both U1109.4 and U1109.11 on both boards
(rounded upward here). The required value is **0.5 mm**: half the unchanged rail
width plus clearance. Thus any full-width start capsule whose center lies inside
either named pad fails foreign-pad clearance under this contact policy.
Using only two actual foreign pad constraints overestimates available clearance,
so omitted obstacles cannot invalidate that negative result. The saved report
records exact values, obstacle UUIDs, 181 subdivisions and the 0.001 mm stopping
tolerance. This is an ordinary floating engineering enclosure, not a
directed-rounding certificate. It does not exclude a separately justified off-pad
pad-end contact or prove physical impossibility.

The earlier AGND pointwise screen found 22 clear boundary centers. The current
U1105.12 test finds no valid whole straight escape within these finite templates,
despite 108 legal start caps. Pointwise raster false exclusions therefore cannot
be promoted into a valid swept edge. Curved/multiple-segment or other off-grid
escapes remain untested.

The report retains up to three edge and three edge-plus-via witnesses per
endpoint, then checks all 18 retained edge-plus-via witnesses against the other
board at the exact same coordinates and rules. Every cross-board edge passes.
K1402's retained C1135/C1111 witnesses also pass on two-A. The retained two-A
C1134/C1135 via locations fail K1402's existing-hole constraint; its U1114.6
via locations fail K1402 foreign-copper clearance. `nearest_foreign` identifies
copper, and must not be cited as the blocking hole for a hole failure.
These are actual local geometry differences in the saved inputs, not a completed
connection, demonstrated architecture advantage or reason to adopt two-A.

## Decision and next source work

No complete paired-terminal connection has been established. The common rail
contact limitation and unresolved AGND escape remain, so merely replacing a
raster mask with this validator would not make the same four-demand native trial
informative. No budget increase, window expansion, disconnected-graph rerun,
width reduction, foreign-copper removal or architecture decision is authorized.

A further source step could establish an adequate off-pad rail contact and
cross-section at unchanged width/clearance, without a hidden neck-down. If that
requires narrower copper or placement changes, quantify the design change and
stop that path. Alternatively, the already defined F3/E1 samples require their
own all-terminal exact access screen and a genuinely matched BOTH_OPEN cohort
before a method revision or native packet is proposed. Easy or already-connected
substitutions cannot establish the intended architecture comparison.

Hardware, fixed panel, circuits, harness IDs/refs/full pin order, noncore poses
and successful copper are unchanged. Accepted JL117/JR129/K1402 and DRC/parity
0/0 are inherited baseline evidence, not fresh native verification from this
source-only work. Full-warning, eligibility and physical acceptance remain open.

## Reproduction and review

Use numpy 2.2.6, scipy 1.15.3 and shapely 2.1.2. The complete retained ZIPs are
required; artifact identities and SHA-256 are recorded in `saved-validation.json`
and the original [1420](../route-1420/result-ledger.json) and
[1438](../route-1438/result-ledger.json) ledgers. The runner authenticates both
ZIP SHA-256/CRCs, original board/dump bytes, fixture method, spec and manifest.

```sh
python3 circuit/routing/epic-242/decision-pilots/terminal-access/check_saved.py \
  --k /path/to/epic242-route-1420-38147266896.zip \
  --two-a /path/to/epic242-route-1438-38148185181.zip \
  --output /tmp/saved-validation.json
python3 -m unittest discover \
  -s circuit/routing/epic-242/decision-pilots/terminal-access -p 'test*.py'
```

Twelve tests pass: positive full-width contact/edge/via; tangential, tiny-overlap
and wrong-anchor rejection; foreign copper inside an anchor; a blocked segment
middle with clear ends; analytic track radius; other-layer via obstruction;
own SMD and same-net hole restrictions; NPTH; outline cutout; independent track
and via keepout flags; invalid dimensions; and a continuous whole-pad bound with
both passing and failing width cases. Independent review reproduced the saved
base analysis exactly and independently recomputed every final cross-board check.

The parallel [collet headroom ledger](../feed-arrangement/collet-headroom.md)
finds **0.197966035 mm** of single shared conditional local headroom above the
0.25 mm criterion. All eleven qualification entries remain false. That allowance
cannot be spent independently on multiple tolerances; local angular clearance
does not relax C1, C2, bend or cut/preparation obligations. Complete carrier/wire
collisions, supplier/process/material/retention and physical qualification remain
open. The 31 feed tests and deterministic headroom check pass.

Baseline preservation verifier, `pnpm circuit:check` and `pnpm check` pass.
Component scope is manual inventory: 68 lines, zero declared placements, no
schematic/placement binding. These checks do not replace native acceptance.
