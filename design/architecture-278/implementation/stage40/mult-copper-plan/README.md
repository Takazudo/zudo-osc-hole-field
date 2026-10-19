# Stage40 — repeated mult cells against native copper

Candidate only, continuing Stage39 recommendation A on the incumbent shared JL substrate. No architecture, face allocation, placement, enclosure or manufacturing change is adopted. All canonical bytes, fixed panel parts and foreign placement remain untouched. This directory is a source plan, not a routable board or connectivity qualification.

## Concrete proposal and comparison

`positions.json` supplies all 36 B1 package poses; B2 is the exact +34 mm X translation. Four jacks and one LED per cell retain their earlier fixed front placements. The proposed electronics use nine front packages (U3102, C3106/7, C3101/2/3, R3107/R3110/R3113) and 22 rear packages. All packages, units, numbered pins and circuit identities are retained. The output amplifier, its bypasses and feedback/compensation passives share the front face. IC/bypass clusters preserve current native B1 pad geometry through rigid translations/quarter turns; repetition is a new proposal, not the current native layout.

The search region expands upward from the Stage39 bottom-row study to panel Y118.5..163.5, X7.5..38.5 for B1. This consumes more of the existing shared substrate, not a new board or foreign-family redesign. Native footprints on both faces, through-hole pad reservations on both faces, native rule areas and retained mount/tool trials are screened. Unknown front/rear populated Z, connector seating, tails, optical alignment and assembly access still need physical evidence. Same-face courtyard clearance is 0.25 mm and retained copper-edge trial is 0.5 mm. These necessary XY screens do not establish copper clearance or physical fit.

See `plan.json.metrics` for Stage39, proposed and current-native B1/B2 distances. Bypass rail-pad distance is a pairwise path lower bound, not a complete supply/ground-return loop. Feedback terminal-only MST sums are locality proxies; Steiner junctions mean they are **not routing lower bounds**. Maximum pair distance is a connected-route lower bound. No stability, inductance, noise or return-loop performance is inferred.

| Locality measure (mm) | Stage39 | Proposed repeated cell | Native B1 | Native B2 |
| --- | ---: | ---: | ---: | ---: |
| Six bypass rail-pad distances, sum | 87.096271 | 14.850000 | 14.850000 | 14.849998 |
| Feedback terminal-only MST proxies, sum | 68.607885 | 20.376686 | 53.404402 | 44.426699 |

The two-millionths-of-a-millimetre difference in the bypass sums is native coordinate rounding (0.000002 mm), not a physical improvement. The plan enumerates 48 private nets / 1,609 copper objects for proposed rerouting; 31,816 remaining copper objects retain their original multiset binding. There are 32 old-pad shared-copper contact candidates and 23 different-net preserved-copper/new-pad candidates requiring exact review. Sixteen Stage39 conflicts with actual native obstacles remain recorded as the first failure.

## Exact copper integration plan

`plan.json` binds the complete native board and all source inputs by SHA256. Native coordinate offset is (100,50) mm; embedded backside geometry is already reflected. Every proposed movement records the original footprint identity, old pads/pose and proposed pads/pose. Net aliases are derived from reference/pin parity, including explicit NC equivalence, and checked in both directions. Global rails must preserve exact identity. Native opaque `X...` names are never interpreted as ownership.

The inventory contains 1,099 footprints, 30,564 segments, 2,861 vias and 128 zones. Eleven segment UUIDs occur twice with different geometry. Object identities therefore use top-level index, kind, UUID, occurrence and raw-object hash. Never deduplicate by UUID. The proposed 62 movable footprints leave 1,037 foreign/fixed footprints byte-bound. All private-net owners are determined from **every native pad**, including foreign packages.

1. Before a future disposable-board trial, verify exact input hashes and capture native baseline pad/net parity, unrouted edges, DRC/warning identities, zone fills and foreign connectivity. Preserve the original board. Source baseline `ab4193cf6b769bda0b86ff45656cbe71db2c1d39` is immutable.
2. Apply only the 62 explicit candidate pose/face decisions in a disposable artifact. Preserve reference, footprint/pad UUID and numbered net identity. Reject a foreign/fixed footprint change, pin alias merge/split, NC routing or unexplained item change.
3. `private_net_retire_copper` enumerates the exact private-net segments/vias proposed for retirement and rerouting. This deliberately retires complete private nets, including routes to retained panel pads, not just segments near moved parts. It is conservative, not a minimum-change claim. No foreign/shared rail may enter that set.
4. `shared_old_pad_contact_review` identifies same-net old-pad AABB contacts; `preserved_new_pad_clearance_review` identifies proposed pads near different-net preserved copper with 0.25 mm allowance. These are conservative spatial review lists, **not connectivity decisions**. Preserve all remaining copper by multiset hash until an exact branch walk proves any proposed local cut is owned. Shared-rail/ground bulk deletion is forbidden. Prefer adjusting candidate access/routing over disturbing foreign copper. The plan does not yet resolve those review lists.
5. Preserve all 123 rule-area objects byte-for-byte. Preserve definitions of the five filled copper zones: AGND F.Cu/B.Cu/In1.Cu, −12 V In3.Cu and +12 V In4.Cu. After routing, refill rather than reuse stale polygons. Compare zone connectivity/islands/warnings and ensure foreign supply/return connectivity remains unchanged. No fill or netclass rule is relaxed.
6. First route one complete B1 output-amplifier loop and its two supply/ground-return paths; include R/C feedback endpoints and retained output-jack terminals. Quantify actual route lengths, via count, return topology and changes from native baseline. Reject residual old copper, unmatched local stubs, new shorts/unrouted edges or foreign connectivity regressions. Only after that pilot passes should the full B1 cell and translated B2 be integrated. Cross-face signal connections, private routing and shared returns remain unsolved until this native trial.

## Decision and next boundary

The smallest next implementable step is the **disposable B1 loop pilot with exact baseline connectivity and the contact-review lists**, not canonical adoption. It requires native KiCad tooling and a separate authorization/task scope; it has not been run here. No owner choice is needed merely to retain this reversible candidate. Adoption or permission to alter shared/foreign copper is a genuine later decision, informed by the pilot. Interchangeable physical modules and other families are outside this stage.

For an unpowered mock-up, measure exact front/back populated heights and jack/LED seating, tail projections, board bow/registration, tool/removal clearance and optical alignment. Pass only with measured worst-case envelopes plus stated tolerances clear of every occupied/unknown neighbor; unresolved dimensions block physical acceptance. Check point-to-point continuity and absence of shorts against all numbered nets after any prototype assembly. No energization, stiffness/current qualification, fabrication, order or release is authorized by this study.

`generate.py` deterministically produces `plan.json` and `plan.svg`; it only reads canonical data. `search.py` is an optional bounded author search using NumPy2.3.5, seed40; CI validates committed positions independently and does not rerun optimization. See `VERIFICATION.md` for first failures, commands and limitations, and `REVIEW.md` for the final independent review.
