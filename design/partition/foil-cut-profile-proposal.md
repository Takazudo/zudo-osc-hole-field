# Finite foil-cut current and potential functional

Status: **standalone source primitive and synthetic analytic checks only**. No actual candidate cut, physical geometry/material/contact/current class or assembled solver is admitted. Historical model files and receipts are unchanged. This supplies a missing mathematical interface for the unselected [foil-collar route](./gh-foil-collar-proposal.md); it does not select that route or establish issue #38 electrical acceptance.

The [JSON fixture](./foil-cut-profile-proposal.json) deliberately declares synthetic coordinates, resistivities and currents. Its computed resistance is not an instrument common-path bound and must not be compared with the 0.5 mΩ acceptance target. Actual hardware remains an unvalidated draft.

## Sign and full section

`FoilCut` names a conductor region and cut, physical foil, exact planar endpoints, complete foil-depth interval, cardinal outward normal and current **into** the conductor. The first primitive accepts only a positive axis-aligned section; tilted/curved or partial-depth supports need another proved mapping and are rejected here.

For width w, thickness t and positive injected current I:

- Uniform volume outward current density is `−I/(w t)` A/mm².
- Uniform sheet outward normal current is `−I/w` A/mm.
- The potential weak-load functional is `+I mean_cut(V)` W, equivalently `−∫cut (j·n)V`.

This matches the existing area-profile sign convention: `potential_trial_matrix.py` adds the positive injected-current nodal load. The old `FluxSheet.boundary_current` method instead takes **outward** current, so a future adapter must pass `−I`. A focused test calls that unchanged method on a small explicit geometry and checks the complete signed face currents; no constructor or solver is used.

A lateral cut has no top-face area injection and no vertical area-source lift. Encoding it as a thin top-face patch would change the model and is prohibited by the source-kind check. This new primitive is not wired into the historical area's-only assembled path.

## Exact full-face coverage and potential ansatz

Each supplied boundary face carries its endpoint identities/coordinates, foil/depth, outward normal, singleton incidence and an adjacent interior point. The primitive checks positive full-face length, collinearity and containment in the complete cut, exact telescoping coverage without gaps/overlaps/duplicates, matching foil/depth/normal and the interior half-plane. Repeated endpoint coordinates must share the same potential-node identity; one node cannot have conflicting coordinates.

These checks verify the **supplied** finite geometry. The eventual native/mesh adapter must derive incidence, interior points and complete face membership from the actual domain. A caller-provided incidence number or region label alone is not a proof about an unseen mesh or manufactured copper.

The only accepted potential ansatz is `continuous_p1_constant_through_foil_depth`. For a face of width ell, each of its two endpoint weak-load coefficients is `I ell/(2w)`. This integrates the complete surface exactly because the potential is affine along that face and constant through depth, while the current density is uniform through depth. It is **not** quadrature for an arbitrary 3D potential. Depth-varying traces and a declaration of depth averages are rejected by this first interface; a future 3D adapter needs full-surface integration and a separate pointwise trace construction.

All coordinates, currents, weights, potentials and work use exact rational arithmetic. Compiled face/weight/coordinate records are immutable. The sum of outward face currents is exactly −I and the sum of weak-load coefficients is exactly +I, including a zero-source profile whose positive geometry must still be supplied.

## Joining traces and counting energy

`glue_cuts` requires distinct source region/cut identities, identical complete physical section, opposite domain outward normals, and exactly matching pointwise normal current densities. Equal total current on a smaller section is insufficient; it needs a paid finite adapter.

Potential traces may use different face partitions. The helper compares their values at the union of all breakpoints. Equality there proves equality of the piecewise-linear transverse functions everywhere, and the depth-constant ansatz extends equality through the entire physical section. Equal averages alone are rejected. The two internal weak-load works then cancel exactly. Tangential current components need not agree for H(div) gluing.

The helper proves these **interface traces**, not that two arbitrary physical regions are disjoint. `disjoint_energy` separately checks the supplied analytic rectangular volumes have distinct identities and no positive-volume overlap, then adds each complete energy once. It does not itself establish trace gluing. A composed current/potential witness needs both the region geometry/energy ledger and the matching interface proof. Actual native membership and material bounds remain external source obligations. The rectangular energy fixture models an artificial cut in a volumetric conductor, with no omitted contact/Robin dissipation. A real resistive interface or transition layer requires its own material model and energy charge; matching these traces does not waive that cost.

## Analytic rectangular reference

For homogeneous resistivity rho, length L, width w, thickness t and current I along the positive flow axis:

`J = I/(w t) e_axis`, `V(x) = V_entry − rho I x/(w t)`.

The current is divergence-free, the transverse exterior is insulated, and the entrance/exit currents are +I/−I into the region. The exact energy and total weak-load work both equal `rho L I²/(w t)`. The potential dual energy `∫|grad V|²/rho` has the same value. Both planar flow axes are tested.

The source fixture joins two different homogeneous resistivities across one full section with different face partitions. Its exact series resistance is `13/40000` Ω and total energy at the synthetic 1/5 A current is `13/1000000` W. Potential offsets preserve the full continuous join, and the two interface work terms cancel. These are arithmetic fixture values, not copper, harness or instrument evidence.

A gauge shift changes an individual cut's work by `I c`; it cancels only over a balanced complete source set. Tests explicitly retain this nonzero local term. They also reject equal-average/different-shape potential traces, a narrowed section carrying the same net current, mismatched foil/depth, incorrect outward normal or conductor side, and duplicate/overlapping energy regions.

## What is resolved and what remains

Resolved by this primitive: the lateral-cut source type, current sign, full finite section and face-coverage arithmetic, exact weak functional for the declared potential ansatz, complete interface trace matching, and the analytic once-only energy contract. These are computable source/design choices that do not require supplier contact.

Still required before an actual candidate can use it: source-bound native domain splitting and complete cut extraction, a mesh adapter that verifies actual face incidence/coverage, the corresponding assembled current and potential operators in a **new** epoch, and full geometry/material/profile maps. The K/JL collar refills changed copper outside their reserved patches, so their old electrical matrices cannot be rebound. No new mesh, candidate-cut selection or global solve was performed here.

The assembled-harness local power bound also needs a matching complete class: both collars carry the full series current, all other ports are insulated, no bypass exists, fixture losses are handled conservatively, and installed temperature/contact/remating/current states are specified. Actual class compliance remains physical qualification; declaring a prospective requirement does not prove it. A catalogue per-end scalar resistance does not certify this complete domain. Deterministic nonempty reference/process classes and all original joined electrical bounds remain issue #38 work; their absence cannot be waived by a physical NOT RUN label.

Run the portable tests with:

```sh
python3 -m unittest scripts.pcbgen.test_boundary_contact_profile
```

The tests include the source JSON replay and the unchanged existing boundary-current API sign comparison. They load no retained mesh or field archive and run no numerical/native solver.
