# Northern F3 reconstruction proposal: reject the bounded repair

**Do not execute this 52-object reconstruction proposal.** One concrete corridor
construction was evaluated after exact source-contact accounting. It fails for
two of the five signal components: the W2 fold connection has no integrated
replacement-via region, and the O2 pulse connection's preserved frontiers lie in
different free components. Three other components have conditional opportunities;
none is a completed route. There is also an unresolved board-projection problem
for the 40 selected rail objects. No additional objects or nets are released.

Recommend preserving successful copper and changing the internal arrangement or
domain under a new bounded source-design contract. This rejects the specific
offset cell, roster and common-corridor construction below. It does **not** prove
that every placement, individual offset, routing strategy or northern F3 design
is impossible, nor that a different board architecture is required.

## Exact proposed scope and selection

Starting head was `12e25023f4036f511040c951b82f512fa0dabe0f`. The parent's instruction
authorizes this read-only reconstruction proposal, not material execution.
Accepted JL117/JR129/K1402, canonical boards, fixed panel/harness identities and
full pin order, noncore poses and unlisted copper remain unchanged.

The A24-N construction moves the original complete 24-reference integrator
closure, including U2306, with base translation (+16,−56.75) mm and the previously
declared C2325 correction. We chose one **offset region**, not a PCB pose, from
the saved courtyard polygon before consulting copper counts: the largest
connected polygon's maximum-inscribed-circle centre, with a 0.001 mm numerical
tolerance, and a square half-side min(0.25 mm, radius/4). This produces:

- dx = [1.175,1.675] mm, dy = [3.358999849,3.858999849] mm;
  square area **0.25 mm²**.
- Every one of the 416 saved pad/copper constraints was considered. All **69**
  guarded upper exclusions intersecting the square yield **52 exact source
  span/SHA objects**, without selecting first witnesses or discarding branches.
- Ignoring those objects leaves 1.275744540 mm² under the necessary pad filter,
  containing the square. This is hypothetical cleared space, not placement
  feasibility or permission to remove copper.

The exact immutable roster is `evidence/region-selection.json`; each object's
geometry, width, layers, drill and complete source contacts are in
`evidence/contacts/selected-object-contacts.json.gz`. `proposal-components.json`
specifies every selected contact component and preserved frontier. This is a
contained construction, not a demonstrated minimum. It leaves 73 of the earlier
125 obstructing objects outside the proposed roster and avoids releasing F2,
O2/TRI_SCALED and W2/LEVEL_OUT nets.

| Source net | Proposed objects (segments / vias) | Source contact components | Distinct preserved copper frontiers |
|---|---:|---:|---:|
| +5V | 21 (14 / 7) | 7 | 14 |
| +12V | 8 (4 / 4) | 4 | 1 |
| −12V | 7 (5 / 2) | 2 | 2 |
| AGND | 4 (3 / 1) | 1 | 0 |
| W2/BIAS_BUFFER | 1 (0 / 1) | 1 | 3 |
| W2/FOLD_BUFFER | 8 (7 / 1) | 3 | 13 |
| O2/PUL_SCALED | 3 (3 / 0) | 1 | 2 |

These 36 segments and 16 vias have **145 directed full-object copper-contact
records**, 35 distinct preserved frontier objects, and 15 pad-contact records
covering 14 unique pads. Midsegment contacts, overlaps, via layer contacts and
pad-mediated equivalences are included. They are electrical obligations, not
145 separate new routes. Original A migration still has **41 separate contact
debts**, with **zero overlap** with this destination roster. Its 272 conditionally
movable copper objects and the new destination reconstruction are different costs.

## Rail projection is unresolved; do not invent cross-board terminals

All 14 directly contacted source pads belong to **two-B**, in E5/M5B, rather
than two-A. They include U4521.7, C8234.1, Q4505.2, C8229.1, C8201.1 and the E5
+5V contacts. The complete mapping is in `proposal-components.json`; whole-net
pad ownership is retained in `evidence/full-net-pad-ownership.json.gz`.

The source preserves shared rail copper conservatively. That does not establish
which branches can be omitted from an A projection while remaining intact on B.
Routing A repairs back to these absent A pads would invent the wrong physical
endpoints; silently dropping their original branches would discard accepted
work. Each branch needs an explicit board disposition and complete original
contact/plane proof before any such projection is executable.

Components 0,1,3,4,5 contain 17 selected rail objects with one pad and no copper
frontier. Their source plane/zone connections remain unlocated, so a
one-terminal geometry check cannot qualify them. All five original zones remain
explicit unchanged obligations. The 40 rail objects were not declared repaired
or projected by the signal-corridor calculation.

Every selected/frontier object matches one source UUID/net/kind/geometry record;
exact span/SHA remains the identity to avoid inherited duplicate UUIDs. Historical
island membership is available for 19 selected and three frontier rail objects.
The other 33 selected and 32 frontier records have no island entry in this dump;
that means **unrecorded**, not disconnected or known closed. Via layer spans are
authenticated from source F.Cu-through-B.Cu blocks; the dump does not separately
record per-via native layers. No fresh native evidence was obtained.

## Replacement endpoints, layers and bounded corridor result

One construction was frozen before execution: for each of the five A-owned
signal contact components, use its selected copper **exterior plus 1.0 mm** on
each original layer. Preserve 0.2 mm trace width; formerly via-bearing components
require an integrated replacement 0.6 mm through-via with 0.3 mm drill. This is
a construction rule, not a universal requirement that every repair needs a new
via. Through-via centres must fit the common six-layer landing region.

Every fixed frontier keeps its exact source geometry. Retained same-net copper
and fixed-pad bridges are credited, including indirect connections outside the
local envelope. Attachment anywhere on a preserved frontier is optimistic;
exact reconstruction of the old contact loci remains unproved. No replacement
trace or via centre was selected. Physical coordinates below are in millimetres
on the original board, not the board-local offset coordinates above.

| Component | Concrete replacement connection concept | Result |
|---|---|---|
| 14, W2 bias | Replace via at (239.3,205.45); connect the two unchanged In2.Cu branches through (239.075,205.225), and the In3.Cu branch to (239.675,205.825), using their 0.2 mm widths. | Conditional common corridor; 0.378926848 mm² necessary six-layer via-landing region. No route or exact landing selected. |
| 15, W2 fold | Reconnect six fixed F.Cu frontier objects across the original 0.2 mm staircase from roughly (239.825,195.175) to (241.25,197.05). | Conditional common corridor only. |
| 16, W2 fold | Reconnect five fixed F.Cu frontier objects around the original vertical segment x=241.7, y=198.775…210.4. | Conditional common corridor only. |
| 17, W2 fold | Replace the via at (234.125,189.325) and its B.Cu link to the preserved through-via at (235.85,191.05), preserving the In2.Cu branch toward (227,182.2). | **Fails:** no necessary replacement-via region; preserved terminals remain in different free components. |
| 18, O2 pulse | Reconnect 0.2 mm F.Cu from the preserved via at (228.9,149.0) to the preserved segment starting (233.8,148.9) toward (234.5,149.6). | **Fails:** both fixed frontiers have access, but no common free component connects them inside this original-layer envelope. |

For component 17 the swept U2312.7 pad exclusion **alone covers the entire
3.133484682 mm² geometric through-via centre domain**. U2312.6, the retained
F2/REF5 via and +5V In2.Cu segment are additional recorded obstacles, but are not needed
for that exclusion. Releasing more retained copper cannot repair this particular
common-corridor construction. For component 18 two moved F3 HP_SUM segments,
the moved R2359.2 pad and a retained +5V via suffice to divide the F.Cu corridor;
R2358.1 is an additional obstacle. Exact obstacle span/hash keys and pad UUIDs are saved with every
forbidden polygon in `evidence/corridors/corridor-results.json.gz`. The review
records which saved subsets are sufficient witnesses; categories are not added
as independent failures. No F2 object or additional +5V object is released to
work around these results.

The check requires **one common corridor for the entire offset square**, using
swept moved pads/copper. Failure does not exclude a corridor tailored to a single
offset, a different envelope or a new layer strategy. A-owned, shared-retained
and labelled unknown-ownership obstacles are considered; other-board nonrail
copper is omitted. Zones/keepouts, full hole/via-pair rules, no-new-merges and
native equivalence remain unrun. Thus conditional results cannot qualify routes;
the negatives reject this specified numerical construction only.

## What the move would and would not solve

A changes the original stationary obstacle context, which is a legitimate
potential benefit. C2312 moves away from the old R2390/U2307 and RV2311/R2372
via pocket, fixed R2372/J900213 context and retained −12V obstruction. C2338 and
U2312 move away from fixed RV2309.1/.3 and the retained mixed-owner In2.Cu track
on the R2348.1/U2312.7/R2349.1 net. That mixed-owner connection also becomes a
reconnection debt; it is not free connectivity gained by moving the footprint.

**No original BP_INT or AGND demand is demonstrated closed.** Both endpoints
translate together: C2312.1→U2306.5 stays 28.925926951 mm,
C2312.1→U2312.12 stays 16.689916866 mm, and C2338.2→U2312.5 stays
7.946956965 mm. BP component 119's 42 copper objects can follow the common
transform, preserving its existing C2312.1↔U2312.12 group subject to gates; the
open connection to U2306.5 remains open. The previously rejected weighted
chain's 0.436104 mm via-pair spacing remains below its 0.700001 mm requirement
under rigid translation. Intrinsic pad relationships and U2309's +12V/−12V
own-pad access failures remain. The C2325 correction addresses only its narrow
courtyard gap. See `evidence/original-access-assessment.json` for exact prior
source records, scope and witness identities.

## Decision and approval boundary

| Choice | Concrete cost and remaining risk | Recommendation |
|---|---|---|
| Execute this A repair | 52 destination objects on seven nets, 35 preserved frontiers, unresolved 40-object rail projection, 41 additional migration debts; two failed signal corridor components and no demonstrated original demand closure. | **Reject.** The roster is not an executable cut list. |
| Keep successful copper fixed and change the F3 arrangement/domain | Requires a new bounded design contract, sensitive-group/relative-geometry review and new obstacle evidence; no passing alternative or lower total cost is yet demonstrated. | **Preferred next design direction**, without assuming an architecture switch is necessary. |
| Widen the corridor or release further F2/rail objects | Expands electrical ownership beyond this proposal; does not follow from a failed necessary check. | Do not continue automatically. |

Any later material execution would require approval of concrete placement and
replacement geometry, exact modified span/hash objects, the complete 41-contact
migration treatment, branch projection on A/B, unchanged frontiers and plane
equivalences, preserved widths/layers/drills, and its full validation plan.
This proposal supplies exact debts and a bounded rejection, so **there is no
executable geometry ready for approval**. Native work, canonical adoption and
merge remain separate and unapproved. The present task stops here.

## Evidence and checks

Source commits: `3cf75290` for the contact extraction, `edfdb326` for the corridor
check. Selection took 0.906 s worker time; the contact census took 5.027 s parent
wall time (4.574 s worker, 600,944 KiB peak). The corridor check took 6.351 s
worker time, 594,556 KiB peak and 70 obstacle records, under 180 s/2 GiB/one worker.
All computations ran once, with no alternative selection, roster expansion,
replacement routing or native call. Independent reviews before execution fixed
contact/bridge-accounting issues; no project calculation ran on those earlier
source versions.

Input manifests, source hashes, exact execution receipts, output reviews,
repository checks and final artifact seals are in `ledger.json` and `evidence/`.
Full native eligibility and circuit regeneration were not run under this scope.
Historical accepted open edges 117/129/1402 and DRC/parity 0/0 remain historical.
