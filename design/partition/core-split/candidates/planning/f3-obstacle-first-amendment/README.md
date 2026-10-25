# Retire the eastern transform; require obstacle evidence before another proposal

This amendment supersedes the next-experiment recommendation in the
[c3e4bc95 plan](../f3-next-approach/README.md) and the broader-repacking suggestion
in the [8aa322d3 audit](../../pilots/f3-whole-east-v1/README.md).
`F3-WHOLE-CELL-E-ONE-RIGID-AUDIT` is **completed, rejected and retired**.
No second pose, sweep, native run or physical redesign is commissioned here.

## The planning method selected an occupied destination

The plan acknowledged N1 and service occupancy, but selected the translation
because its combined bounding box fit the eastern rectangle. That was an
insufficient selection method. The existing fixed polygons could have rejected
this destination before a copper-transplant experiment was proposed.

The saved audit contains **24 newly introduced N1 courtyard conflicts** and one
separate inherited C2325/U2306 gap failure. It also records **10 reservation
overlaps**. The three analytic service-hole collisions are witnesses to three of
those same reservation overlaps; they are not three additional independent
obstacles. These categories must not be summed into a failure total.

## What is established, and what is still unknown

| Question | Evidence-backed answer |
| --- | --- |
| Is the audited eastern translation obstacle-clear? | No. Fixed N1 courtyards and JR-K-15/K-16 service geometry reject it. |
| Is another externally obstacle-clear whole-F3 location known? | No. The earlier north/east/southwest window areas and envelope comparisons do not demonstrate one. They also do not prove that none exists. No complete allowable-domain exclusion was performed. |
| Can the current unchanged internal geometry pass every strict source placement gate after a rigid move? | No. Any common rigid motion preserves the approximately 0.349999 mm C2325/U2306 gap, below 0.35 mm. This is a source-model invariant, not a new native DRC result. |
| Is substantial internal rearrangement unavoidable? | Not established. The intrinsic gap first needs either an independently justified source-geometry correction or a permitted minimal geometric adjustment. Its 0.000001 mm deficit does not justify wholesale repacking, and is not permission to round or waive the gate. |
| Must the 4,491 internal copper objects be reconstructed? | Not established. All passed the audited source contact-closure classification. Destination conflicts prevented acceptance. The 112 lost fixed contacts belong to this particular transform; they are neither a general minimum cut set nor a reconstruction count for another site. |

## Corrected prerequisite for any future location proposal

A location may be recommended only with a sealed source-feasibility certificate:

1. Define the allowed board, faces/orientations, internal geometry and movement
   domain. Identify the candidate's fixed parts and explain any source ownership
   filtering. Keep all non-F3 poses, panel/harness identities and pin order,
   service/support/power geometry and six layers fixed.
2. Screen the **actual per-face component courtyards** against every fixed
   courtyard with the strict spacing rule, all reservation polygons, analytic
   holes and edge allocation. Screen the internal geometry too. Deduplicate
   hole/reservation evidence by object and physical obstacle. An envelope or
   free-area number is only a necessary dimensional check.
3. For an externally clear concept, account for eligible retained/transformed
   copper, pad and drill clearance, copper keepouts, full source contacts, all
   seven fixed signal headers and shared return/supply paths. Keep source-only
   findings separate from unresolved zone and native gates. Unknown geometry or
   ownership cannot become an implicit PASS.
4. Only then define one justified candidate and an exact evidence/resource
   contract for any separately authorized experiment. If no clear concept is
   demonstrated, report the screened domain and unknown remainder. A claim that
   rearrangement is unavoidable requires a complete exclusion argument for that
   domain, not several failed points.

This is a planning gate, not permission to run a new translation enumeration or
placement search. No certificate for a new site has been produced by this
amendment, and no new location is proposed.

## Recommend preserving internal copper until evidence requires otherwise

**Owner decision:** retain internal-copper preservation as the next design
priority, allowing only an independently justified minimal intrinsic correction
if needed, or deliberately relax that priority and commission electrical-cell
repacking with a new reconstruction budget. Recommend the preservation-first
choice; the current evidence does not justify the larger intervention.

Broader planning is already authorized. The missing technical deliverables are
an explained resolution of the inherited source gap and fixed-obstacle
feasibility evidence. Neither another knowingly colliding experiment nor blanket
permission to rearrange all 171 parts is an appropriate next request.

This amendment uses saved evidence only. [Evidence join](evidence/existing-evidence-join.json),
[independent review](evidence/independent-review.json) and [ledger](ledger.json)
record its scope and checks. Canonical boards and the previously audited outputs
remain unchanged; no additional geometry experiment or native acceptance is
claimed.
