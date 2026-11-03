# Stage42 disposable full-B1 native study

This extends the accepted Stage41 output-loop pilot to all 31 B1 electronics on the incumbent jack-left board. It is proposed placement and copper in an isolated copy, not adopted canonical CAD. The five front packages J109/J110/J209/J210/D109 remain fixed. Parent PR286, Stage41 and all historical stages remain unchanged. See `evidence/settlement.json` and `REVIEW.md` for the completed verification boundary.

## Proposed geometry and copper

All 15 Stage41 footprint poses are preserved. Relative to Stage40, the U3101/C3104/C3105 cluster moves −0.2 mm in native Y, D3102 moves −0.4 mm in Y, and R3103 moves −0.1 mm in Y. R3104 moves to native (112.75,187.5) mm, unchanged rear face and 90° native angle: 5.618051 mm from its Stage40 pose. Its bounded 0.25 mm search evaluated 1,681 positions in a 10×10 mm neighborhood and found 20 passing necessary courtyard/copper screens. This is neither a continuous global optimum nor proof of populated mechanical fit. The remaining scoped poses follow Stage40. Receipts record every exact pad position, face and native angle; study origins need the (100,50) mm native offset, while pad `xy_mm` is already native.

The candidate retires 779 exact private copper occurrences on 24 operational nets and, separately, 21 reviewed abandoned supply occurrences (15 tracks/six vias). Four shared/reused supply anchors remain. The cleanup withdraws two new segments that only reconnected an abandoned old copper island. A final +5 V approach replaces one newly added In2.Cu segment with a via at (133.8,202.5) mm and a B.Cu segment to the unchanged shared anchor at (134.9,201.4) mm; the retained rail stays on In2.Cu. This preserves a functional layer transition rather than deleting shared copper. Final additions are 1,160 objects: 1,130 routed signal/supply objects and 30 explicit bypass/fanout objects. Fixed packages stay fixed, but their B1 terminal copper may be rerouted; this is not a claim that every fixed-package terminal track is unchanged.

All six bypass capacitors for U3101/U3102/U3103 have explicit IC links and supply/AGND fanouts: 18 paths with 12 native filled-plane proofs. IC-to-cap planar links are 2.2975–2.8875 mm; fanouts are 1.0–2.0 mm. These exclude pad interiors, via depth and plane spread; no loop inductance, analog stability or current-capacity qualification follows. Native identity checks preserve every other copper occurrence, pad/net assignment, foreign/fixed footprint, zone definition, rule and board object. Eleven duplicate segment UUID pairs are handled as separate occurrences.

## Feedback copper comparison

Preserving the Stage41 footprint poses does not preserve its routes. Full-B1 rerouting changes the three U3102 feedback-net centerline sums as follows; branch lengths, pad interiors and plane spread are not a closed-loop electrical model.

| U3102 pin | Canonical mm / vias | Stage41 mm / vias | Stage42 mm / vias |
| --- | ---: | ---: | ---: |
| 6 | 18.750 / 4 | 10.175 / 2 | 9.770 / 2 |
| 9 | 22.169 / 3 | 5.050 / 2 | 8.314 / 2 |
| 13 | 24.567 / 4 | 5.319 / 2 | 8.838 / 2 |

Stage42 therefore has longer total feedback copper than Stage41 despite remaining shorter than canonical; no performance improvement is inferred. All24 private-net inventories are in `evidence/metrics.json`.

## Exact scope before modification

Stage40 binds 36 B1 packages: 31 electronics and fixed J109/J110/J209/J210/D109.
Stage41 covered 15 electronics. The remaining 16 are U3101/U3103,
C3104/C3105/C3108/C3109, D3101–D3105, R3101–R3104/R3114.
No B2 work is permitted before full-B1 native acceptance.

`scope.py` reads the retained complete native snapshots and DRC reports; it does
not invoke KiCad. It reuses Stage41's complete partition validator, verifies each
snapshot against its retained board hash, and emits all 117 DRC entries with
attribution plus every B1 net's component counts and pad list in
`evidence/open-scope.json`. Actual object net names determine ownership; opaque
net names and zone positions are not interpreted as module assignments. Full
component memberships remain in the hash-bound retained native snapshots.

Both original baseline and accepted Stage41 have:

- Zero open-item endpoints directly identifying a B1 pad.
- 103 open items on nets with no B1 pads.
- 14 shared AGND open items, reported as zone-to-zone representatives.
- All 26 B1 AGND pads together in one component; every other B1 net has one
  component. The 14 other AGND components contain foreign pads, so these remain
  real unresolved board connectivity defects, not harmless empty islands.

B1 has 33 native nets: 24 operational private nets, four shared supply/return
nets and five explicit NC nets. No existing B1-private open is a routing target.
The full-cell placement must restore all deliberately disturbed B1 nets
while preserving the complete foreign partitions and all 117 baseline opens.
Unchanged open count alone is insufficient. Fixed front hardware, foreign
footprints/copper, canonical outputs and all Stage41 evidence must remain intact.

## Silkscreen comparison

Independent source review found no supported item/region selector in the exact
KiCad10.0.6 CLI, and the installed SWIG surface exposes whole-board
`WriteDRCReport`, not a region selector. Conditional ignore rules are not an
established substitute: the silk provider can force ignored clearance back to
zero for mask checks. No rule, severity, limit or checked geometry was changed.
The two capped warning categories remain explicitly unresolved; no exhaustive
silkscreen nonregression is claimed.

Sources: [CLI](https://github.com/KiCad/kicad-source-mirror/blob/10.0.6/kicad/cli/command_pcb_drc.cpp),
[silk provider](https://github.com/KiCad/kicad-source-mirror/blob/10.0.6/pcbnew/drc/drc_test_provider_silk_clearance.cpp#L261).


## Verification and reproducibility

All native/heavy runs use the shared heavy guard and exact-release KiCad10.0.6 through `scripts/kicad/run.sh`. The existing task-local tool is not claimed bitwise equivalent to the pinned Docker image. Official archive SHA256: `8c789e36644856cff30a66801692881582b9ca7c7475699494e614ce1bcb1f9c`; detached signature verification remains incomplete because the public-key endpoint returned403. The numerical router uses NumPy2.2.6, SciPy1.15.3 and Shapely2.1.2. No native installation or canonical regeneration was performed in this stage.

The sequence is `scope.py` → `prepare.py` → native placement audit/DRC → `route_power.py` → explicit proposal apply → native checks → `route_signals.py --resolution .05 --priority-net X24465B284FC5581E6283` → apply/native checks → `branch_contacts.py` → independent cleanup review → `retire_branches.py` → `route_anchor.py` plus explicit proposal apply → repeated/fresh native checks → `settlement.py`. Actual drivers and first failures are retained in the ignored evidence archive. Signal routing is additive, without foreign rip-up; clearances remain 0.25 mm, signal width0.2 mm, supply width0.4 mm, through-via diameter0.7/drill0.3 mm. Raster completion alone does not accept a candidate.

First failures remain recorded in `WORK.md` and native-attempt evidence. The source-only authorization handoff is retained as `SOURCE-REVIEW.md`; later explicit owner authorization permitted this disposable native trial. The first power verifier incorrectly used `PAD.GetLayer()` for rear SMD pads. It now uses the footprint face and verifies actual pad membership; a regression covers that API behavior. Native geometry was not changed to satisfy the checker.

Acceptance is limited to full-B1 native connectivity and uncapped scoped rule/warning nonregression: all 24 disturbed private nets close, all retained partitions match, no new islands, all18 power paths verify, and the native open count stays117. The 117 pre-existing error-level unconnected items are still unresolved board defects. Zero error-level entries in the separate rule-violation list and zero parity issues do not constitute a full-board DRC pass. Capped silkscreen categories remain unresolved as described above.

## Remaining boundary and unpowered mock-up criteria

No B2 replication or architecture adoption is part of this stage. Parent review must select the next bounded continuation. Cloud-capable work can assess B2 against the same exact baseline ownership and partition checks, or classify the foreign/shared baseline opens; neither is completed here. Canonical adoption requires a separate decision.

Before physical qualification, record these inputs on an unpowered populated mock-up:

1. Component heights, actual board thickness, solder tails, support registration, worst-case bow and enclosure datums for all31 parts. Reject any collision with fixed front hardware, neighboring boards or connector/enclosure volumes. Unknown neighboring geometry remains occupied/unknown.
2. Front/rear assembly and rework access, especially relocated R3104, U3101 and all six bypasses. Reject trapped parts, inaccessible tools or required movement of locked front hardware; courtyard clearance does not establish populated Z clearance.
3. Board/core removal and 15 mm connector withdrawal sequence, minimum measured clearances and temporary support at each step. Reject loss of support, forced bending, trapped connectors or contact during service. This copper study does not resolve earlier harness/cover/support limitations.
4. Unpowered continuity/isolation against all24 private-net pad manifests and all18 power paths. Reject any unintended bridge or open; this cannot dismiss the117 known whole-board native opens.
5. Exact cable/wire identity, installed/service lengths, cut tolerance and repeated-flex radius from primary data or measured qualification. Do not substitute a guessed wire limit or nominal cable length for the unresolved earlier harness inputs.

No energization, physical performance testing, fabrication, ordering, release, deployment or merge occurred. Analog behavior, thermal performance, optical alignment, enclosure fit and manufacturing qualification remain unresolved.
