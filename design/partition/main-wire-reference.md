# Registered reference geometry for all main wires

Status: conditional construction, not an admitted physical wire/contact class.
Alpha 5859 BK005 remains the fitted identity. No board or panel hardware centre,
original electrical limit, material qualification or fabrication status changes.

## One geometry for both calculations

The electrical trial and mechanical loom screen now call
`scripts/geometry/power_wire.py` for all 18 source-labelled wires.
Each endpoint occupies 3.65 mm: 0.35 + 2.9 + 0.1 mm of fan, a separate
0.05 mm solder prism, and a 0.25 mm registered zero-tilt adapter. Solder energy
was already charged; its formerly omitted height is now included too.
The bulk axial spans are 81.1 mm for JL/JR and 79.3 mm for P.

For t in [0,1], the bulk displacement is
`(bow_x sin²(πt), offset_y (3t²−2t³) + 10 sin²(πt), Ht)`.
JL uses an 8 mm x bow and zero y offset; JR has zero x bow and zero y offset; four P wires have
a −4 mm y offset and two have zero. A simultaneous nonzero x bow and y offset
is rejected, including subnormal nonzero values. Thus every selected curve
lies in one vertical plane. Its endpoint tangents are axial. The Bishop frame
rotates about the fixed horizontal normal and returns to the same global x/y
frame at both ends, matching the 19 fan-root offsets without residual roll.

This selects a registered reference member of the proposed adapter class.
It does not assert that actual joints have zero tilt or that Alpha guarantees
the proposed strand arrangement. Actual metal must contain the registered
current cores and obey the declared full-metal and material envelopes.
Arbitrary independent endpoint staggering needs a new proof; it cannot
automatically use the existing 0.075 mm potential collars. Physical
containment, solder/interface bounds and matching PCB terminal traces remain
OPEN.

## Conservative geometry bounds

With d = offset_y and b = bow_x, the analytic length upper is
`sqrt(H² + 6d²/5 + π²(b²+100)/2)`. The cross integral vanishes by symmetry.
The slope upper is `(π hypot(b,10) + 1.5 abs(d))/H`; the second derivative
upper is `2π² hypot(b,10) + 6 abs(d)`. Dividing H² by the latter bounds
the bend radius below.

The helper encloses π with an exact-rational Machin series and its alternating
remainder, uses an integer-square-root enclosure, and rounds reported bounds
outward. Endpoint-cap and preparation additions are also directed outward.
This arithmetic protection covers these geometry formulas, not all upstream
electrical trial arithmetic.

The 100 bulk chords have a deviation allowance of the second-derivative upper
divided by 8×100², plus 1e−9 mm. Collision envelopes include the greater of
insulation radius and full model metal radius, existing 0.25 mm padding and
that chord allowance. Both full endpoint boxes participate in collision checks;
their 2.5 mm half extent cannot shrink below the solder land or bulk metal.
The complete continuous centreline bound includes both caps; its longest value
plus the 10 mm preparation/slack allowance is 103.244852 mm (rounded upward),
within the 110 mm source requirement. This geometric screen does not establish
a manufactured cut-length class.

## Conditional electrical comparisons

The current source budget is 1.630 mOhm including both terminations.
Rounded display values are:

| Group | Count | Whole-wire upper, mOhm | Budget margin, mOhm | Mean strand length upper, mm |
| --- | ---: | ---: | ---: | ---: |
| JL | 6 | 1.406588 | 0.223412 | 96.093474 |
| JR | 6 | 1.382586 | 0.247414 | 94.189582 |
| P, −4 mm offset | 4 | 1.361676 | 0.268324 | 92.530938 |
| P, zero offset | 2 | 1.360171 | 0.269829 | 92.411537 |

Lengths in the table are rounded upward. A mean strand length does not bound
every strand or certify the finished cut. The conservative generic adapter
energy debit remains charged even though the registered reference uses its
zero-tilt member. The normal potential lower bounds are approximately
0.334358696 mOhm for JL/JR and 0.326923913 mOhm for P; uniform-hot values
are twice these. Neither is a joined-board acceptance result.

## Source epoch and remaining work

`main-wire-source-epoch.json` records the exact six new route metadata fields
and unchanged board-definition bytes. Removing those additions reproduces the
previous structured partition inputs and outputs. The collar recipe was
recompiled using retained native inputs, with identical compiled board objects,
before refreshing its partition hash. Historical native receipts are unchanged.
All six peripheral source projections were also regenerated and compared in full;
only the partition hash in their current source receipts changed. Their separate
source-epoch audit is refreshed without rewriting historical receipts.
Native execution for the new global source epoch is **NOT RUN**; this audit
does not rebind old native or electrical results.

Focused tests cover independent quadrature, high-precision formula checks,
endpoint frames, all 18 shared references, missing-profile rejection, source
propagation and collision-envelope enlargement. The generated nominal loom
screen passes. Physical qualification, material bounds, full terminal trace
matching, the complete common-ground/rail certificate, source and protection
implementation, and downstream board routing remain open.
