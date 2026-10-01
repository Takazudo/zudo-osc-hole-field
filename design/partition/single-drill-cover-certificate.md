# Single-drill SMD finite-cover geometry

Status: **exact nominal geometry certificate only**. This certificate binds
historical native epochs. It does not admit a current source, physical
manufacturing envelope, current field, potential field or numerical model.
No old native/model receipt is edited or rebound.

`scripts/pcbgen/single_drill_cover.py` targets exactly the 213 single-drill
SMD sources in the retained 4,143-contact boundary mapping. The five sources
with multiple drills and all 305 PTH contacts remain explicitly unresolved.
The other 3,620 convex SMD sources are outside this new certificate's scope.

## Exact domains and coverage

Use integer nanometres from the retained native analytic pad/via primitives
and exact decimal native drill coordinates. Let P be the actual convex pad,
c the circular drill centre, a its radius, and R the actual same-net circular
via-land radius on the same physical foil. The root domain is the full
annulus a < |x-c| < R. Eight other candidate domains are P intersected with
the halfplanes

```
+/- (x-cx) >= a, +/- (y-cy) >= a,
+/- (x-cx) +/- (y-cy) >= 3a/2.
```

Their union avoids the open drill. The complement octagon has maximum
squared radius 5a²/4. The strict exact gate R² > 5a²/4 proves that the annulus
covers every remaining point of P outside the drill, up to boundary sets of
area zero. Those sets carry no L2 surface-source mass. Convex pieces retain
the actual circular corners of P; no hull or polygonal replacement is used.
An exact support-function comparison removes only pieces of zero area.

The actual native pad and via independently establish copper ownership.
All other native holes are checked against the full pad and full via disk.
Circular holes use exact distance to the rounded rectangle/circle; other
hole shapes use a conservative enclosing disk. Any contact or intersection
rejects the certificate. This covers holes on foreign nets too. Zone-fill
polygons are not used to manufacture missing pad/via copper.

The complete native Edge.Cuts set must match the exported simple polygon.
Only the straight axis-aligned outlines actually present on the target
JL/JR/K epochs are supported. Extra, curved, self-intersecting or unmatched
cuts reject. The complete pad/via bounding rectangles must lie strictly
inside that polygon and must not touch any boundary segment. This includes
the nonconvex K outline. Unsupported geometry stays unresolved.

## Positive overlaps and source partition

Each retained tree edge carries an integer-nanometre square strictly inside
both domains. Exact rational corner tests prove convex-piece membership;
exact nearest/farthest square distances prove annular membership. The square
area is a positive exact lower bound in nm². Shapely supplies candidate
locations only. No floating intersection, sampled circle or computed area
is used as a containment/coverage proof. A failed search rejects admission
for that row even if a better search might later find an overlap.

The receipt gives domain IDs, an order with parents preceding children, and
the corresponding parent list. In that order, assigning each source point
to its first containing domain defines the disjoint measurable source
partition `S_i = (P minus drill) intersect D_i minus earlier domains`.
Identical uniform profiles on each certified square can provide the exact
opposite overlap terms in the finite-cover tree theorem. This geometric
partition specifies the sets; it does not evaluate arbitrary source flux or
choose current coefficients.

## Evidence and remaining work

The run requires the exact retained mapping digest, reconciles every fitted
source identity against frozen original partition/IO bytes, verifies native
export and actual board hashes, and retains every pad/via UUID/net/face.
Dependencies are checked again before exclusive receipt publication. Each
row binds its native export and board epoch. Receipts are local ignored
artifacts, and a fresh output path is required.

This geometry permits subsequent local Poincare and overlap-area estimates.
The actual finite-cover divergence fields, source norm and mean-transfer
budgets, common foil extrusion, barrel/annular transitions, cross energy and
continuous full-metal primal extension still require implementation and
review. Physical tolerances must preserve these proofs or provide a valid
geometry map. A positive nominal geometry receipt alone is not source-family
or electrical acceptance.
