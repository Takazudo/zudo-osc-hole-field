# Stage43: B2 translation counterexample — rejected

This bounded study starts at reviewed Stage42 commit
`d00622590d12f67d9883957387dfdb3acf376374` and tests reuse of its disposable B1
cell for B2. The owner explicitly authorized B2 native work on working copies.
Nothing here adopts the proposal into canonical CAD or manufacturing outputs.
Parent PR286 and all earlier stages remain unchanged; PR287 remains draft.

**An identical translated cell is not established.** The first complete native
attempt has 154 error-level DRC violations and changes 11 retained supply-copper
net identities. It is rejected. A separate raw source diagnostic restores those
11 original identities and passes the complete source preservation gate; its
native-load gate is evaluated separately. A successful process or unchanged open
count cannot override either failure. The native DRC output is evidence of the
failed attempt, not a qualified retained-identity comparison.

The correspondence is 36 packages / 115 pads, with the same numbered pins:
31 electronics map from 31xx to 32xx; fixed J109/J209/J110/J210/D109 map to
J309/J409/J310/J410/D309. Source semantic net mapping has 24 private nets,
4 shared rails and 5 explicit NCs. Unused op-amp feedback nets are operational,
not NCs. The intended translation is +34 mm X, no Y change, reflection or
rotation. Routing translates 1,160 added objects (30 power and 1,130 signal/rail
objects); B2's 830 private occurrences are retired, with no authorized shared
retirement. The B1-specific 21 shared branch retirements are not copied.
Strict native pose comparison additionally records nanometre rounding
discrepancies; no tolerance was relaxed to declare exact equality.

## Concrete blocker

The failed native attempt reports 71 shorting-items, 65 clearance, 11 crossing,
5 keepout, 1 hole-clearance and 1 solder-mask-bridge errors. It contains 487
warnings versus Stage42's 476. Fifty-nine translated copper objects across
13 nets participate in error reports. These are affected-object counts, not a
proven minimum repair set. The two silk categories remain capped at 199 each;
exhaustive silkscreen nonregression is unresolved.

R3209's translated center is native (152.9,208.07) mm on B.Cu, inside
`pcbgen:osc-jack-left:keepout:POWER-JL-2-BCu-1:B.Cu`. Both pads, the footprint,
and an associated translated via/track produce keepout errors. Retaining that
reservation requires changing the B2 resistor placement and its connections,
which breaks identical placement. No minimum displacement or safe alternate
pose has been established. Translated In2.Cu routes also intersect retained
foreign copper, for example net X2116EAF991E4FD59E329. Protecting that copper
requires B2-specific rerouting; no clearance threshold was changed.

The 11 reassigned retained objects comprise 7 segments and 4 vias, formerly
+12V or -12V. Six retained-net partitions change, including the U3201 pin12 NC
net. All 24 private target nets appear closed and the native open count remains
117, but retained-net/partition acceptance fails. The 117 pre-existing whole-board
opens remain real defects, not an allowance for the new shorts or relabels.
All 18 translated bypass/supply/ground-return paths show native connectivity
and intended filled-plane contacts on the **invalid** output. This diagnostic
is not exact dedicated-path, electrical performance or hardware qualification.

## Boundary and next work

B1's accepted file and canonical board stay byte-identical. Source identity
checks protect all fixed/foreign footprint bytes, every retained copper
occurrence (including duplicate UUID occurrences), pad identities, rule areas,
zone definitions, project rules and schematics. Native loading/saving failed
that protection in the rejected output; it was never adopted or substituted for
Stage42. Large boards, snapshots and first-failure logs remain local and ignored.

A next cloud-capable stage could design a B2-specific R3209 location, prove B2
shared-branch ownership before any removal, and reroute against the actual B2
obstacles. It must preserve B1 and acknowledge that the cells then differ.
Alternatively, a new common layout would need both cells evaluated again;
Stage43 does not authorize or perform that redesign. There is no qualified
identical-cell or fabrication conclusion.

Physical stackup, housing fit, assembly/access, repeated-flex wire data,
mechanical measurements, manufacturing and energization remain unverified.
Earlier rear-face study authorization does not adopt new carrier/enclosure or
reservation changes. No order, release, deploy or merge was performed.

`VERIFICATION.md`, `evidence/`, and the final independent `REVIEW.md` distinguish
source passes, expected rejection, native failures and remaining limits.
