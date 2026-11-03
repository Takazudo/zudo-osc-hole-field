# Stage52: two local bridges rejected after native refill

No accepted repair, canonical adoption or manufacturing change. Start from the
accepted *disposable/native* Stage49 baseline (not qualified hardware):
`05f85d8cb27dcbeec76327065e91526f0112ebc316054a1cec5cae5cbc80c441`.
Stage50 specifications remain conditional; Stage51 stays a rejected experiment.
PR287 start head `fb37bafb3df737f24d65f8b9163eb0ab7fa6c3b8` had successful exact-head
CI39285545923. Parent286 remains `b58068fbaeb65886958a67a4f4978613414e31c5`.

The target remains `/F3/C945bba_SENSE` / native `XED7C19D453619667580D`, isolated
R2316:2 to the existing U2317:10 / D2303:3 component. Acceptance requires116→115
opens, zero rule/parity errors and no other retained connectivity change.

## What cuts the plane

Indices below are zero-based indices in Stage51 proposal.json's copper array.
Native **refill diagnostics**, not full DRC/acceptance, isolate the interactions:

| Added portion / omitted section | −12 V component sizes | Total opens |
| --- | --- | --- |
| Source half, indices2–13 plus seed | 1015 | 116 |
| Target half, indices14–26 plus seed | 15 + 23 + 977 | 118 |
| Full path minus16 | 38 + 977 | 117 |
| Full path minus17 | 38 + 977 | 117 |
| Full path minus25 | 23 + 992 | 117 |

Section16 is the In3 diagonal(227.8,107.1)→(229.8,105.1)mm;17 is the horizontal
(229.8,105.1)→(234.1,105.1). Either gap reconnects the two detached groups, but not
the main plane. Section25 is the vertical(236,102.7)→(236,96.4); its removal joins
the15-object group to the main977-object component. These are interacting barriers,
not three independently established minimal cut points. Omitted paths have target
discontinuities and cannot be accepted as repairs. Each diagnostic starts afresh
from Stage49; no other-net edits, plane-definition changes or footprint changes.

## Tested candidate and failure

Two bounded searches found F.Cu bridges using ordinary0.60/0.30mm through vias and
0.20mm tracks. The lower bridge links(227.948045,109.291186) to
(234.888909,104.511091); the upper links(234.885993,102.753381) to
(235.122861,99.590073). Short In3 spokes connect these to retained portions of the
Stage51 path. Composition adds43 target objects:38segments and5vias including the
original seed. It removes **no baseline copper**; Stage51 copper was never adopted.

Full native refill/DRC closes the target's1+50 retained members, but still has
**117opens, zero rule errors, zero parity errors,476warnings**:

- −12 V1015→977+38: the two former islands join each other but remain detached.
- AGND1425→1422+3: C2247:2, RB2216:2 and C2249:2 become a new island.
- Other retained partitions remain unchanged. The exact gate rejects
  `unexpected partition: -12V`; AGND is independently reported, not hidden by the
  first rejection. No added uncapped warnings; capped silk identity remains unresolved.

All existing footprints, hardware positions, netlist, stackup, rules, zone
boundaries and unrelated routed geometry are fixed. Native fill changes are
observations, not accepted geometry. Full reports/receipts, partition audit and
source proposals are retained under evidence/ and audit.json. Large boards/native
snapshots remain local and ignored, hash-bound by the audit. No Git LFS.

Source replay recreates both bridges and the composed proposal byte-for-byte.
A fresh native rebuild is checked against the first board and complete snapshot;
this is reproducibility of a **rejection**, not an accepted routing settlement.

## Search and assembly limits

Allowed bridge layers were F/In2/B. Full/short upper bridges failed at0.1/0.05mm;
reaching any nearby member of the existing50-object target component also failed
at0.05mm. Alternative west pocket and upper-main searches failed again at0.025mm.
All failures are retained. These bounded raster results do not prove continuous
routing impossible. The optimistic geometric pocket screen is not native acceptance.
Its own-via-hole correction permits legal terminating tracks while preserving
foreign-hole/new-via constraints; the initial false screen failure is retained.

Five via-to-pad copper gaps are positive (minimum0.231578mm), but exact assembly
clearance remains **UNRESOLVED**. The seed overlaps R2316/U2202 courtyards; the second
site overlaps U2217/C2247. All three eastern via centers lie inside J803's courtyard;
two also intersect U2317's courtyard. Courtyard intersection proves neither a
physical collision nor assembly acceptance. Exact populated body/termination
volumes, placement/solder tolerances and selected mask/tenting process are missing.
No special via process or physical result is invented. Prior Stage50 and earlier
mechanical/wire/flex/service unknowns remain unchanged.

## Smallest next scope decision

Parent may authorize a **target-only bridge search on the existing In4.Cu layer**,
keeping the current six-layer stackup, all dimensions/rules and all other routed
copper fixed. In4 currently carries the +12 V pour: it is not empty/free routing
space. Such a study must preserve +12 V and every other net partition after native
refill, along with AGND and −12 V. Feasibility is NOT established; no In4 candidate
was generated here. This expands one routing-layer permission, not another net's
rip-up, hardware positions or the stackup. Alternatively retain the baseline and
select a different isolated target. Stop for parent review; do not silently proceed.

Before adoption of any future candidate, use an unpowered integrated mock-up to
check both sides at the fixed via locations against actual jack/IC/passive maximum
body envelopes and process tolerances. Require positive worst-case clearance and
approved mask/tenting criteria, record uncertainty and accessible probe/service
clearance. No numerical assembly threshold is invented. Physical/electrical and
manufacturing qualification NOT RUN; no fabrication/order/energization/release/merge.
