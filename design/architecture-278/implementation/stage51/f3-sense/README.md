# Stage51: F3 sense route rejected; seed isolated

No accepted repair and no canonical adoption. Baseline is Stage49 disposable board
`05f85d8cb27dcbeec76327065e91526f0112ebc316054a1cec5cae5cbc80c441` at Stage50
head `8b204afe0e97d45fc3417ef2782ab005994698e1`. Parent286 remains
`b58068fbaeb65886958a67a4f4978613414e31c5`; all historical stages are preserved.

The only target is `/F3/C945bba_SENSE` (native `XED7C19D453619667580D`), isolated
R2316:2 to the existing U2317:10 / D2303:3 component (1 + 50 objects). Intended
acceptance requires 116→115 opens and preservation of every other net partition.

| Experiment | Native opens | Rule/parity errors | Warnings | Decision |
| --- | --- | --- | --- | --- |
| Baseline | 116 | 0/0 | 476 | Historical disposable baseline |
| Full In3 trial: 26 tracks + 1 via | 117 | 0/0 | 476 | REJECT: target closes but −12 V splits 1→3 |
| Seed only: B track + 1 via | 116 | 0/0 | 477 | Incomplete diagnostic; all retained partitions preserved |

The full trial isolates 15 and 23 objects from the 1,015-object −12 V component,
leaving 977. The small groups contain U2317:11/U2303:4/C2348:1/C2320:1 and
U2202:4/U2217:11/C2218:1/C2248:1 respectively. Zero DRC rule errors is insufficient:
`accept.py` rejects `unexpected partition: -12V`. Seed adds one dangling-via warning;
it is not a completed route. See [audit](audit.json), full reports and execution
receipts in evidence/. Native geometry, footprints, netlist, stackup, rule/zone
definitions and dependencies remain fixed; refill changes pours only.

Four initial raster searches (B only, local multilayer, wider, finer 0.05 mm) fail.
An exact subgrid seed permits an In3 onward route. Avoiding In3 fails at 0.1 and
0.05 mm. The existing −12 V fill guard rejects the full route and finds no alternate
non-In3 path. These are bounded searches, not proof of continuous impossibility.
`analyze.py` is an optimistic local screen, not acceptance: it omits pours, drills,
edges and rule areas, and its nonempty pockets touch the crop boundary.

The seed is a 0.2 mm B track from (229.01,113.39) to (227.980882,113.013236) mm,
then an ordinary 0.6/0.3 mm through via. Independent analytic copper screening
finds only 0.013518 mm surplus above required clearance at the tightest neighbor.
It is off-pad, but its annulus overlaps R2316 and U2202 courtyards by approximately
0.180882 and 0.079118 mm. This is neither proof of package collision nor assembly
acceptance. Exact body/process/tolerance inputs remain unresolved. No special
via process is selected. A second screened pocket at (228.725,117.470423) lacks a
proven B escape and lies within D2337's courtyard; it is not a safer accepted option.

## Proposed next bounded study

Retain the seed only as a disposable candidate. Isolate which In3 sections cut the
two −12 V necks using subset/refill diagnostics. Investigate short target-net-only
bridges onto F/In2/B with ordinary through vias around those sections. Bridge sites
and manufacturable paths are NOT established. Require full native all-net partition
checks, no collateral changes, fresh generation and independent final review.
Do not add power stitches, rip up other nets or move components without new scope.
Stop here for parent selection; no such bridge has been implemented.

## Unpowered boundary

Before any adoption, bind exact populated R2316/U2202/U2217 variants and maximum
body/termination envelopes; obtain placement/solder/mask/tenting tolerances and
approved clearance criteria. Inspect both sides on an unpowered mock-up at the
fixed coordinates. Accept assembly only if worst-case envelope plus allowances
clears the via/track and applicable mask criteria; a nominal courtyard screen is
insufficient. Confirm probe access and no exposed unintended contact. Record actual
measurements and uncertainty, not invented tolerances. Electrical, physical and
manufacturing qualification NOT RUN. Stage50 R8270 inputs and earlier mechanical,
wire/flex/service gaps remain unresolved and independent of this failed route.
