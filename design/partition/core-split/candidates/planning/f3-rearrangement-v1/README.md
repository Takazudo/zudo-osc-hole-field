# Three bounded F3 rearrangements: exclusions and a concrete copper decision

All three predeclared constructions are excluded in their declared domains.
No pose or candidate PCB was selected. The northern integrator construction A
is the most narrowly specified design for an owner decision: its courtyard fits,
but retained **+5V copper and foreign F2/O2/W2 signal copper each independently
block every available offset**. Proceeding with this construction requires a
bounded proposal that may alter both categories, with complete electrical
contact preservation, or a changed internal arrangement/domain. F3-only repair
or rail-only repair cannot resolve this frozen construction. This is not a
global F3 impossibility result or proof that wholesale repacking is necessary.

This source-only continuation follows the owner's “ok keep goin” instruction,
starting at `9cc7fce8d7845f2827a1fd71d2b5550c4a4cdea4`. Accepted JL117/JR129/K1402,
canonical PCB bytes, electrical identities, 438 fixed panel records, 195 harnesses
and 390 endpoints with full pin order, and 2,519 noncore poses remain unchanged.
No new routing, native execution, adoption, merge, fabrication or energization.

## Compared constructions

Dimensions and windows are millimetres. Every construction retains all 171 F3
references and seven existing headers on its assigned source candidate; none
introduces a partial-F3 cross-board interface. Orientations and faces are fixed.
Exact reference lists and base transforms are in `screen.py` and saved results.

| Construction | Declared geometry | Continuous courtyard result | Necessary pad/copper result |
|---|---|---|---|
| A24-N | Original complete 24-reference integrator closure, including U2306; 37.15 × 70.67 envelope in north window [124,88,164,168]. Base translation (+16,−56.75), offset dx=[0,2.85], dy=[0,9.33]. | 21.834275545 mm² remains | All remaining offsets excluded by 416 constraints: 411 foreign-copper, one foreign-pad and four same-net-via/SMD constraints. |
| B25-FOLD-N | Complete U2311 11-reference and U2314 14-reference sensitive/bypass blocks stacked at x=124,y=88 with 0.36 envelope separation. 32.280001 × 70.299999 envelope; offset dx=[0,7.719999], dy=[0,9.700001]. Integrator closure remains in place. | 17.979820752 mm² remains | All remaining offsets excluded by 727 constraints: 720 foreign-copper, six fixed-pad-drill and one same-net-via/SMD constraints. |
| C24-SW-THREE | The A closure inside existing three-B whole-F3 ownership; southwest window [4.3,208,64,288]. | Entire domain excluded by 138 fixed-courtyard/reservation/service-hole constraints. | Unnecessary after courtyard exclusion; not run. |

A and C include a separately declared C2325 local correction of (−0.04,+0.01)
in addition to the common group motion. This changes its U2306 courtyard gap from
0.349999 to 0.359999 and decreases their centre distance from 6.000426120 to
5.997350548 mm. It preserves the bypass proximity criterion but is not perfectly
rigid: both C2325 contacts remain explicit obligations. The original deficit is
**one nanometre**, not one micrometre. B leaves this genuine inherited shortfall
unresolved. Four other raw floating-point distances just below 0.35 were
independently verified as exactly 350,000 nm on the declared integer grid;
their raw values remain in the saved reports.

The actual board polygon is (4,8), (314,8), (314,246), (258,246), (258,292),
(4,292). C's y=288 limit is inside that polygon; 284 is board height, not its
maximum y coordinate. Its x=4.3 boundary preserves the declared edge margin.

## Exact contact and copper accounting

`electrical-boundaries.json` preserves every moved and fixed pad identity on each
affected net, including rails and NC labels. Its whole-net inventory counts
must not be interpreted as affected-object counts or permission to cut nets.

| Accounting | A24-N | B25-FOLD-N |
|---|---:|---:|
| Boundary signal nets + shared rails | 22 + 3 rails | 17 + 3 rails |
| Internal net labels, including NC labels | 11 | 10 |
| Conditionally common-motion source contact components | 12 | 20 |
| Objects in those components, pending all other gates | 272 | 505 |
| Original selected pad-to-copper contacts | 77 | 94 |
| Contacts retaining exactly the same declared base transform | 36 | 55 |
| Contacts with fixed or differently transformed copper, requiring reconnection | **41** | **39** |

The physical component test uses saved source copper adjacency and pad contacts,
not net equality alone. Every pad contact on a component must have the same
nonzero transform before that component is provisionally movable. Mixed fixed,
two-block and C2325-correction components remain in place. The B blocks share
GAIN_DEPTH, whose 54-object whole-net inventory cannot simply move with either
block. Zones and full native connectivity are not established by this source
component classification.

Each concept accounts for all **133,551 segment/via objects**, plus **346 rule
areas and five zones**. Canonical disposition is always UNCHANGED. Objects
assigned exclusively to other partition candidates remain explicitly accounted
for there; they are not silently deleted from the original. Shared rails and
unknown ownership stay obstacles. Compressed contacts include exact source
span/hash keys, pad identities/positions, object endpoints and transform debts.

`verify-dispositions.py` reconstructs every original full disposition record
losslessly from the compact encoding and sealed existing copper index, and
checks the raw JSON hash. The redundant 6.1 MB raw gzip files remain local;
their hashes and encoding contract are durable in `disposition-encoding.json`.
No local path is required to verify the compact records.

## Decision supported by the saved geometry

Independent saved-set recombination gives two separate coverage certificates
for A's entire 21.834275545 mm² courtyard-available region:

- +5V alone: **183 constraints from 40 distinct source objects**.
- Non-F3 signal copper alone: **85 constraints from 42 objects**, on
  `/F2/REF5`, `/O2/PUL_SCALED`, `/O2/TRI_SCALED`, `/W2/BIAS_BUFFER`,
  `/W2/FOLD_BUFFER` and `/W2/LEVEL_OUT`.

Releasing any single whole net family still leaves full exclusion. Releasing
all rails, all signals, or all rails plus F3-only copper also fails. These are
necessary-obstacle certificates for this specific arrangement; they do not
identify a minimal release set. Individual signal coverage includes
19.02131 mm² from W2/FOLD_BUFFER and 18.21361 mm² from O2/PUL_SCALED.

Hypothetically ignoring all **125** saved blocking copper objects restores the
pad-only region under the remaining fixed-pad constraint. That superset is
**not a recommendation to remove 125 objects**, and says nothing about whether
replacement routing can preserve continuity. Exact source keys and layer/net
bindings, policy unions and region polygons are in
`evidence/copper-policy-review.json.gz`; the concise decision is in
`evidence/copper-policy-decision.json`.

**Recommended owner decision:** permit preparation of one bounded reconstruction
proposal for A involving exact shared +5V and foreign-signal objects, preserving
all original electrical equivalences and unchanged frontiers. This permits a
proposal only, not deletion or adoption. Every selected object must be named by
source span and SHA; every affected non-F3 pad, sensitive relationship, via and
zone must enter the contact ledger; unlisted successful copper stays fixed.
Any proposed replacement requires its own bounded source geometry and retained
copper checks. No whole-net release authority follows from the coverage result.

If successful copper must remain entirely fixed, A's internal arrangement or
domain must change. The saved results do not identify a passing alternative.
The present task stops at this concrete constraint decision rather than running
an unbounded sequence of new arrangements.

## Evidence, execution and limits

`input-seals.json` and `pad-input-seals.json` bind source boards, partition
assignments, imported code and actual stage-one output bytes. Stage-two execution
source is `d189e43de74aac0791e0d2d44e5e14b2314bd0e2`; script hashes and artifact
provenance are in `ledger.json`. The recovered original dump contains 13,406 pads
and hashes to `2dae7737731cb9d6f230e3f61848d01f6939fd7e7e6b56d3ed23f74ea8684807`.
No old local checkpoint bundle was assumed to exist.

Stage one completed in **3.686 s**, one worker, 156,140 KiB peak, under 30 s/2 GiB.
Stage two completed in **18.589 s**, one worker, 787,128 KiB peak, under 180 s/2 GiB;
28,456 broad-phase iterations produced 1,195 constraint candidates, below the
50,000 cap. Independent recombination took about 1.25 s. Zero retries of project
geometry, zero selected poses and zero native calls. A packaging verifier's
initial serialization mismatch was corrected to include the recorded final
newline; no geometry was rerun or output changed for that correction.

The continuous numerical method uses actual courtyard/obstacle polygons,
configuration-space forbidden regions, declared 1 nm source quantization and
1 μm inward/outward numerical guards. Exclusion requires lower forbidden regions
to cover the complete available domain and leave an empty difference. The pad
stage applies necessary retained foreign-pad/copper clearances, drill clearance
and same-net via/SMD exclusion. These are floating GEOS source certificates,
not formal exact-arithmetic proofs or fresh native DRC.

Independent pre-execution and output reviews are saved under `evidence/`.
The pad reviewer recombined all saved lower regions and retained nonminimal
24- and 31-constraint witnesses. Negative necessary-gate results make further
moving-copper, internal-via, keepout, zone and selected-point gates unnecessary
for rejecting these constructions; none of those unrun gates is claimed passed.
U2309's original full-width rail-access issue remains unaffected. None of the
four original F3 native demands receives completion credit.

Repository circuit checks, generated-output/doc type checks, 1,881 frozen baseline inputs
and compact-record verification are recorded in the final ledger. Full circuit
regeneration and native eligibility were not run under the source-only scope.
Historical accepted DRC/parity 0/0 and open-edge counts remain historical evidence.
