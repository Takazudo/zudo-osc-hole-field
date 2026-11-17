# MC02 parametric manufacturer contact projection

A source-only relative pattern for the122 virtual FH12 endpoints. This consumes
the already reviewed `mc02_connector_mapping.endpoint_rows` and pinned61-link
record; it does not repeat board scanning or manufacture new footprints.

Manufacturer EDC3-150229-11 bytes were verified (1,059,562 bytes;
SHA-256 c3257beed2331e5c95e176bc28441b04b804301a44c11b462e486fb5cc649d07).
All10 sheets were visually reviewed. Sheets1/2 explicitly put contact1 at the
leftmost pad in component top/PCB pattern view:8/14/26 use sheet1,40 uses sheet2.
Sheet5 supplies exact variant A/F/G values. This offline tool checks frozen
reviewed metadata; `--source-pdf PATH` additionally re-verifies actual PDF bytes.

## Local convention and conditional basis

The reviewer-defined source-local origin is the signal-pad row midpoint, x right
in the manufacturer top/PCB view, y toward actuator/cable entry. It is not a
manufacturer-declared footprint origin. With A=0.5(n-1), contact i is
`(-A/2+(i-1)*0.5,0)`. Derived nominal tabs are x[-G/2,-F/2] and[F/2,G/2],
y[2.15,4.35], from pad half-length0.65 + gap1.5 + tab length2.2.
No dimension tolerance is propagated into a clearance or soldering verdict.

For field-to-slot direction d=(dx,dy), conditionally align local y=d. Choose
F reference view x=(dy,-dx), B reflected view x=(-dy,dx). The explicit matrix has
columns[x,y], determinant+1 forF/-1 forB. This is a **declared viewing/parity
convention**, not a measured physical orientation or KiCad footprint angle.
Mirroring a source-view copy requires reflecting both its x coordinates and the
basis; tests verify the relative physical vector remains invariant. No40P-only
reversal is inferred. Current inventory rows all specify B; F fixtures verify the
view distinction rather than admitting new face placements.

`P_i = field_center + unknown_row_midpoint_offset + basis * local_contact_i`.

The virtual field center is NOT asserted to be the pad-row midpoint. No complete
source/project registration from the virtual courtyard envelope to the signal
row has been established. Therefore translation offset, absolute row midpoint,
physical pad1 and footprint rotation remain null. Relative manufacturer-contact
vectors and logical conductor positions are separate lists; no logical-position1
net is bound to a physical pad by this output.

Cable sheet3 contact1 is drawn on the right in its termination view, whereas the
connector/PCB pattern shows it on the left. Do not directly copy that left/right
or infer whole-cable parity from the two field directions. Sheet7's bottom-contact
and conductor-face-down instructions still require a complete physical fold,
material-face and insertion transform. End-to-end physical cable parity remains
UNESTABLISHED. The explicit chosen basis does not establish mounted access.

Opening4.8mm stays a reference dimension, never a guaranteed maximum or validation
of the prior5mm assumption. No canonical geometry, native KiCad, placement, DRC,
fill, hardware adoption or manufacturing is performed.

```sh
python3 -B scripts/checks/mc02_contact_projection/projection.py
python3 -B scripts/checks/frozen_studies.py discover scripts/checks/mc02_contact_projection
pnpm circuit:check
```

Source pins, count/sheet bindings, regular pitch, four cardinal directions,
F/B/source-view reflection and all physical unknowns are checked. The source-only
122-row extraction is lightweight. Pre-edit circuit check passed:84 manual
records,445 declared placements unverified; pin-asset check performed.
