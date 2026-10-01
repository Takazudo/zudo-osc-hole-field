# PTH source boundary geometry

Status: **nominal geometry only, pending independent review**. Native CAD
establishes through-hole identities, nominal drill dimensions, enabled foil
lands and stack depth. It does not measure plating or prove a manufactured
wall. A complete wall with minimum 25 um finished plating is a conditional
PROJECT requirement in `pth-boundary-geometry-class.json`, not a qualified
process. No solder fill, cap or physical equipotential ring is introduced.

## Complete source inventory

The immutable retained mapping contains 305 fitted own-source PTH contacts:
100 JL and 80 JR jack sleeves, five K contacts and 120 P controls. They have
circular nominal drill radii .61, .4, .5 or .545 mm and complete four-foil
spans. All original source ref/pad/net/UUID identities are retained. The
previous single- and multiple-drill SMD receipts remain unchanged.

`scripts/pcbgen/pth_source_geometry.py` checks each actual native pad block
is the matching AGND `thru_hole`, circular drill, `*.Cu` layer set with
unused layers retained. Exported hole/plating/physical-foil identities must
agree. Native board thickness and every copper/dielectric layer thickness
must equal the bound source stack and sum to its nominal depth. The complete
native Edge.Cuts polygon and all other drill voids are checked too.

The inner wall has a distinct record with actual nominal radius, full
periodic angular domain, board depth and wall area measure `ri*dtheta*dz`.
Its outer contained shell radius is `ri+0.025 mm` conditionally. The statement
that this shell is manufactured continuously through the full depth remains
unqualified. The result separately reports zero physically qualified walls.

## Each foil face and finite connection

Every enabled foil receives its own geometry record. F and B annular faces
are exterior source boundaries; inner foils are attachments, not additional
exposed source faces. Depth coordinates are board-local: F outer face is
z=0 and B outer face is z=L. Their outward normals are -z and +z respectively;
this does not provide an assembly/world coordinate transform.

For circular pads the complete foil face is the circular land minus its
open drill. For rectangular jack lands a complete contained circular
annulus plus exact convex pad/halfplane intersections covers the remaining
corners without filling the drill. Each retained overlap-tree square has
strictly positive exact area inside both physical domains. All faces are
checked against every foreign drill and the complete native cut contour.

At each foil band, a square strictly inside `ri < r < ri+0.025 mm` lies in
both the conditional shell section and the full foil annulus. Its exact
area and the foil thickness give a positive geometric overlap volume.
This proves a finite available connection under the nominal shell condition.
It neither assigns duplicate material ownership nor supplies a current
field through the connection. Currents on overlapping trial domains must
later be combined with their cross energy; a disjoint material mesh needs
its own complete interface construction.

The nominal radial margin between the contained shell and outer annulus
is recorded. It is not an etch, registration or drill tolerance allocation.
Physical perturbations that destroy any required annulus or overlap must
remain unresolved until independently bounded.

## Remaining witness work

Actual source currents may divide between the inner wall and both exterior
faces. The geometry inventory does not impose uniform injection or replace
these boundaries with a top-face source. Mean wall-to-annulus transfer,
arbitrary zero-net wall/face lifts, common foil/reference transfer, source
budgets, full cross energy and continuous whole-metal primal extension
remain required. The positive overlap squares do not instantiate those
fields or select lead/solder/contact geometry.

Certificates bind the historical exports and actual board bytes, the
original source mapping, the prior SMD receipts and the conditional plating
source. All dependencies are rechecked before exclusive publication. Native
or source drift fails without producing a successful receipt. These are
source-bound nominal geometry records, not current model, physical or
electrical acceptance.
