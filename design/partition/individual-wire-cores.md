# Individual registered reference-core construction

Status: conditional mathematical construction, **not physical admission**.
This extends the [shared main-wire reference](main-wire-reference.md). It does
not specify Alpha Wire 5859 BK005's actual strand lay, qualify a factory cut,
select material/interface requirements, or close #38/#65.

## Shared exact joining planes

The source-computed numerical foil planes are canonical input datums. The
component heights are summed as exact rationals, and the same rational cuts
place solder, tip, fan, adapter and bulk. The record includes every stage cut;
the helper rejects any disagreement. The exact bulk span is the difference
between its shared end cuts. Its downward/upward floating enclosures feed
geometry bounds, and the potential collar span is subtracted exactly before
rounding downward. Enlarging an endpoint box alone would not establish this
trace identity.

Endpoint x/y values, zero endpoint slopes, the returned Bishop frame and the
identical root polygons define matching traces analytically. Floating preview
points are not the joining datums. Their axial conversion residuals, including
the displayed span and cap height, are explicitly checked against the 1e−9 mm
sampling allowance. Current numerical output can differ by rounding units;
the energy formulas and original acceptance limits are unchanged.

## Individual bulk lengths

Each source curve lies in one vertical plane, is monotone in depth and has
axial endpoint tangents. Let T = sin(theta) u + cos(theta) z and choose the
continuous Bishop normal N = cos(theta) u − sin(theta) z, including through
inflections. The other normal is the fixed perpendicular horizontal vector.
Each of the 19 actual numerical fan-root coordinates defines fixed coefficients
a,b in this frame. The proposed core centre is r + aN + bB.

Its derivative with respect to axis arclength is (1−a*kappa)T, where
kappa = d(theta)/ds is **signed** curvature. Positive Jacobian makes its length
L − a(theta_end−theta_start) = L. Both endpoint angles are zero. Every
individual constructed bulk centreline therefore has the axis length; this
does not follow merely from the old mean-strand bound. The core frame has
zero spin, and its curvature is bounded by
1/(axis_radius_lower−maximum_root_radius).

The helper checks every root against the full-metal radius, positive Jacobian,
the source core-curvature limit and the existing length-ratio/spin limits.
No smaller resistance is substituted into the existing conservative energy
calculation.

## Global separation

Local positive Jacobian alone does not prove a tube cannot meet itself.
Write the planar axis as a graph r(z)=(g(z),z), with |g'|<=S and
|g''|<=M. Here M is the raw parameter second-derivative upper divided by H²;
an arbitrary geometric-curvature bound cannot replace it.

If two normal sections of radius R met the same point p, their depths would
differ by at most 2RS. Between those depths,
|g(z)−p_transverse| <= R(1+2S²). Half the squared distance to p has second
derivative at least 1−MR(1+2S²). When this is positive, its first derivative
cannot vanish at both alleged normal incidences. The out-of-plane coordinate
is fixed, so the argument proves injectivity of the whole normal tube.
The current worst factor MR(1+2S²) is below 0.074292, against the strict
threshold 1. Fixed-offset paths also remain monotone in depth, between the
registered endpoint planes.

Within that tube, distinct root sections remain disjoint. For both fan stages,
the helper separately minimizes every pair's squared separation exactly over
the smoothstep parameter in [0,1]. Horizontal fan sections share a unique depth,
so this check covers the full fan rather than sampled heights. The current
minimum core gap is greater than 0.019999 mm. These are reference sections;
actual copper containment remains a manufacturing qualification requirement.
The convex hull of every fan stage, enlarged by the core/solder-support extent,
is also checked inside both registered endpoint boxes. The current horizontal
reference clearance exceeds 0.574999 mm; a shrunken box is rejected. Axial
box bounds round outward to enclose the exact sum of component heights as
well as the numerical reference cap, including after source changes.

## Complete endpoint and length accounting

Every endpoint includes both smoothstep fan stages, the 0.1 mm redistribution
tip, the 0.25 mm registered adapter and the 0.05 mm solder prism. Exact-rational
Jensen bounds enclose each stage length. The largest full endpoint bound is
3.982372 mm (rounded upward), within the existing 4 mm allocation. Solder
height is included even though it is not an actual copper strand.

| Reference group | Maximum individual reference path plus 10 mm preparation, mm |
| --- | ---: |
| JL | 103.944852 |
| JR | 102.087397 |
| P, −4 mm offset | 100.469208 |
| P, zero offset | 100.352719 |

Table values are rounded upward. These bounds use axis length plus two complete
4 mm endpoint allocations and preparation. The worst remaining margin under
110 mm exceeds 6.055148 mm. This differs from the 103.244852 mm mechanical
centreline screen, whose caps use axial height rather than individual fan paths.

The helper rejects a cut ceiling below its computed bound, even if the
resistance-budget comparison would pass. Exact rational arithmetic and directed
rounding protect geometry comparisons and reported bounds. Independent tests
integrate all 19 paths in each of the four source groups, check source limits
and endpoint propagation, and reject overlap, unproved injectivity and short
cuts. All 18 source-labelled wires receive the new diagnostic.

## Remaining qualification

The existence of these disjoint reference cores does not show they lie inside
the actual stranded wire. Actual containment, the full-metal envelope, material
and solder/interface limits, mechanical retention, finished cut practice and
PCB terminal traces remain OPEN. The old mean-strand resistance calculation
and every original common-ground/rail/current limit are unchanged. No native
receipt is rebound and no PCB, wire class or fabrication output is released.
