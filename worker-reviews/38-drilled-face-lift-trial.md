# Issue 38 drilled SMD face lift trial

Scope: standalone conditional mathematics and one historical two-drill geometry fixture. No board, solver, native export, PTH, or production source was changed. Every board remains an unvalidated draft.

`scripts/pcbgen/drilled_face_lift_trial.py` states the source-to-internal-cut field for arbitrary signed `q in L2(S)`, extended by zero to the same-foil domain `D`. It uses a contained positive-area patch `O`, `b=1_O/|O|`, `I=int_S q`, `f=q-I*b`, and a Neumann solution `Delta psi=f` with zero normal derivative on every domain boundary. The conserved field is `J_xy=grad(psi)/h`, `J_z=-I*b-z*f/h`, where local `z=0` is the internal cut and `z=h` is the exterior metal face. It has pointwise exterior outward trace `-q`, internal-cut outward trace `I*b`, zero drill-wall/lateral trace, and zero divergence. The same equations apply for `I=0` with a nonzero signed redistribution source. F.Cu and B.Cu have opposite global axial orientation.

The exact finite-cover tree routine checks total source balance and positive overlap areas. The conditional energy routine includes the mean/correction cross term by a whole-field triangle bound and rational outward square roots: `rho_max * (|I| sqrt(h/|O|) + ||f|| sqrt(C/h+h/3))^2`, with `||f|| <= ||q||+|I|/sqrt(|O|)`. A caller must supply a proved L2 norm class; sampled traces cannot establish a universal bound.

The test reads the retained historical `osc-jack-right` `U8304:6` certificate: two complete annuli, convex leaves, and every exact rational overlap square. It computes a conditional cover constant from the pad bounding box, complete-annulus constants, conservative whole-support area and exact overlap areas. It rejects a zero-width overlap, an enlarged drill, and a reversed B.Cu orientation. These checks establish a symbolic fixture only; the historical receipt is not current board authority.

## Fail-closed gaps

- No current-native, source-bound proof of a positive same-face foil slab `h`, the actual outer and internal face locations, or positive downstream foil remaining below its cut. A historical planar cover cannot establish this 3D containment.
- No current-native proof of an internal patch `O` contained in the complete same-foil domain and of all 218 drilled SMD cover trees and local Poincaré constants at the current epoch. The example cover constant is confined to the historical two-drill fixture.
- No specified physical arbitrary-source L2 norm, material resistivity interval, possible wetted support, current allocation, solder/lead contact, or actual source-to-cut profile hash. Consequently no per-contact energy receipt or model entry is admitted.
- The weak Neumann solution is guaranteed by the connected Lipschitz-domain/Poincaré theorem once each actual cover domain and boundary is proven. This trial has not built a numerical solution, a field over the current native copper, or a downstream conductor with the negative **pointwise** cut trace. It cannot be composed into a complete source-to-main field.

Result: **CONDITIONAL SYMBOLIC ONLY**. Physical, joined electrical, and manufactured validation remain `NOT RUN`; reason: the listed current-native geometry and physical inputs are absent.
