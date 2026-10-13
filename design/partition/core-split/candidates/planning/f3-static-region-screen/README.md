# Bounded static F3 region screen: incomplete

The single analytic run stopped at a consistency guard after **1.7185 seconds**
(exit 1). No eastern feasible-region or exclusion verdict was produced. This is
an implementation failure, not evidence that the eastern window is impossible.
The script at execution was commit `ececa973e02e44bfffbfdffe904cbd7a024c8540`,
SHA256 `b241f89c6b37cd620e177cb93c6670e075738c7a532da575255b502176003990`.
The receipt and complete traceback are retained in `evidence/`.

## Bounded conclusion

At the unchanged orientation, the 171 F3 courtyard polygons have bounding box
[93.75,139.75,151.82,246.53] mm, measuring 58.07 × 106.78 mm.
The previously considered northern window [124,88,164,168] is only 40 × 80 mm.
Its containment translation intervals are dx=[30.25,12.18] and
 dy=[−51.75,−78.53], both empty. This dimensional exclusion is independent of the
failed obstacle computation. It only excludes whole-courtyard containment in
that rectangle, not all northern placements or the entire two-A board.

The eastern window [164,48,244,168] permits the closed containment domain
**dx=[70.25,92.18], dy=[−91.75,−78.53] mm**, area 289.9146 mm². Its complete
obstacle coverage remains **unknown**. No region polygons or coverage witnesses
were saved before failure; absence of these outputs establishes no clearance.

## Method and limits

For each moving polygon M and same-face fixed courtyard O, forbidden translations
are O⊕(−M), expanded by the 0.35 mm courtyard rule. Reservation polygons use
zero expansion; analytic service-hole centers use their actual radii. The input
has 171 moving and 1,748 fixed placements, plus 802 reservation polygons. Both
windows lie within the source board outline inset by 0.30 mm; this is a courtyard
allocation check, not copper-edge eligibility. No candidate point or PCB is
materialized. The analysis uses entire domains, not sampled poses.

Integer convex hulls use 1 nm rounded input, with 1 µm inward/outward guards.
Rounded upper buffers are circumscribed. A no-region verdict would require lower
forbidden sets to cover the full closed domain and leave an empty difference;
zero uncovered area alone is insufficient. Floating GEOS unions remain source
numerical evidence, not exact-real or native proof. Inputs and versions are
sealed; one worker, 2 GiB address-space limit, 30-second parent cap, zero retries.

The C2325/U2306 inherited 0.349999 mm source gap is a separate rigid invariant.
It remains below the strict 0.35 mm source gate everywhere. It neither excludes
external sites nor proves that wholesale repacking is necessary. Copper, pads,
drills, routing access, zones and native acceptance are outside this screen.

## Failure, prepared repair, and one next action

The failed guard was `hi.buffer(1e-9).covers(lo)`. Synthetic geometry reproduces a
valid empty clipped lower region for which this predicate is false. The actual
failing pair was not recorded, so this reproduced defect is **not a confirmed
runtime root cause**. Independent review agrees with that limit.

The current script now accepts empty lower bounds, still rejects nonempty lower
regions outside the upper bound, and saves pair identity and geometry if that
nonempty guard fails. Nine synthetic tests pass. The repaired script **has not
been run on project geometry**; the retained start receipt identifies the older
executed source. The pre-run review and seven-test receipt apply to that older
source; the final review and nine-test receipt apply to the prepared repair.

One next action is a separately admitted single bounded run of the reviewed,
repaired static screen on the **same sealed N/E domains**, with failure witnesses
retained. Do not select another pose or expand the domain based on this failure.
No additional input artifact is missing; the prerequisite is successful execution
of the repaired consistency guard, with its actual witness if it still fails.
This task stops here with zero retries. No broad impossibility or reconstruction
necessity has been established.

## Verification

Independent source/result review and ordinary repository checks are retained in
`evidence/`. No board candidate, routing, native validation, canonical edit,
adoption, merge, or physical redesign occurred. Full regeneration was not run
because it would invoke unadmitted native work. Historical canonical receipts
remain JL117/JR129/core1402, DRC/parity 0/0; these are not fresh native evidence.
