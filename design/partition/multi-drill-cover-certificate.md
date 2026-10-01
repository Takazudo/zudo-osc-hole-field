# Multiple-drill SMD nominal cover certificates

Status: **nominal geometry only, pending independent review**. This adds five
historical source-domain certificates without changing the previous 213-row
single-drill receipt. All 305 PTH contacts remain open. No physical source,
current field, three-dimensional transfer, primal witness or model is admitted.

The exact targets are JR U8304:6 and K C6113:2, C7305:2, C7417:2, R2169:2.
They have respectively two, two, two, four and four intersecting plated AGND
drills. The implementation is `scripts/pcbgen/multi_drill_cover.py`.

## Coverage outside every hole

For each actual drill i with centre c_i and radius a_i, retain its same-net,
same-face complete native land annulus through radius R_i. Require
R_i² > 5a_i²/4. Every annulus must avoid **every other hole**, including the
other target drills. The actual source pad and full annular disks must be
inside the complete native Edge.Cuts contour. Additional holes intersecting
the pad, clipped annuli, unsupported geometry or failed overlap searches
produce an unresolved row rather than an approximate certificate.

For each hole use the eight rational halfplanes from the single-drill proof.
Intersect the actual convex pad with one halfplane choice for **each** hole.
The resulting convex pieces avoid all target holes. Any source point outside
the union of retained annuli belongs to one such choice for each hole, so
distributing these finite unions/intersections covers the pad minus all
drills. This argument does not fill a hole or replace a rounded pad by a hull.

Rational polygon clipping starts from the pad's bounding rectangle. The
physical domain is still the actual analytic pad intersected with the clipped
polygon. Rectangle domains are exact polygons. For rounded rectangles, an
exact polygon-to-core-rectangle minimum squared distance determines whether
the intersection with the circularly rounded pad has positive area. Only
zero-area intersections are pruned. Pruned prefixes and positive leaves
account for every one of the 8^m complete choices. Domains may overlap and
need not form an efficient energy decomposition.

## Positive connections and partition

A breadth-first search connects all nonempty convex pieces and all actual
annuli using integer-nanometre overlap squares. Exact rational predicates
check every square against both participating domains. Annuli use minimum
and maximum distance to the square; convex pieces use all halfplanes and
the original pad's exact circular corners. A tangent or zero-area overlap
does not pass. Floating polygons only propose witness locations.

The receipt retains every domain's halfplane choices, exact rational clipped
polygon, pruned branch proofs, ordered tree and positive square areas. The
source partition is defined by assigning each point of the actual pad minus
all drill interiors to its first containing domain in that order. This is a
disjoint measurable partition up to boundaries of zero area. It does not
choose a physical current profile or evaluate its integrals.

## Epoch and physical scope

The previous single-drill receipt and original complete 4,143-contact mapping
have mandatory exact digests. Their frozen partition/IO, native exports and
actual board bytes are checked, and all fitted source identities are
reconciled before selecting these five pads. Both old receipts remain
unchanged. The new receipt records additional helper hashes and rechecks
all dependencies before exclusive publication.

Actual overlap sizes and the number of cover pieces can give loose Poincare
and transfer-energy bounds. Positive nominal area alone gives no tolerance
margin or electrical acceptance. Physical geometry/material/source classes,
finite-cover current fields, three-dimensional extrusion and annular/foil
transfers, all cross energy and continuous whole-metal primal fields remain
separate requirements. No historical source is relabeled as a current native
or numerical authority.
