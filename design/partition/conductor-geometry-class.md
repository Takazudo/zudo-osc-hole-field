# Finite conductor geometry class: implementation scope

Status: **unselected**. This note distinguishes a proved map theorem from the
manufacturing intervals and physical interfaces still needed for acceptance.
No thickness, conductivity, registration or etch range is selected by it.

## A compatible depth transformation

Keep the planar domains and hole geometry fixed. A continuous increasing map
`F(x,y,z) = (x,y,f(z))` maps each positive nominal stack band to its actual
positive band. The ordered bands must be contiguous and cover every conductor,
including complete barrel segments between foils. The same map must apply to
foil, collar and barrel interfaces, source supports and observation functions.

Within a band, let `lambda` be actual height / nominal height. A Piola current
field transforms as `J_new(F(x)) = DF * J_old(x) / det(DF)`. Its resistance
metric is `diag(1/lambda, 1/lambda, lambda)`. The pullback potential metric is
`diag(lambda, lambda, 1/lambda)`. Thus one scalar thickness multiplier is not
correct for both lateral and vertical conduction. Source-free divergence,
normal interface flux and continuous potential traces survive each band join.
Volumetric source density transforms as `q/lambda`; boundary source flux is a
measure. On a horizontal outer-face contact, x/y area and normal Jz stay the
same, preserving its finite terminal functional.

For every band with stretch interval `[a,b]`, the metric eigenvalues are within
`[1/M, M]`, where `M=max(b,1/a)`. Taking the largest M over all bands, and
pointwise positive isotropic resistivity bounds on **every** mapped conductor,
gives the resistance-operator ordering

```
(rho_min/rho_reference)/M * R_nominal
    <= R_mapped <=
(rho_max/rho_reference)*M * R_nominal.
```

This is quadratic-form ordering for all compatible source combinations. It
does not say that an individual mutual transfer increases with resistance.
`depth_map_envelope.py` returns exact rational factors for the represented
input values; it does not perform or certify floating matrix scaling. Three
focused tests cover opposite normal/lateral resistance scaling, scalar dtype
precision and invalid band intervals. Independent mathematical review found
no defect within these stated premises.

## Work still required for a manufacturing-wide bound

- Select physically supportable positive foil/dielectric intervals and an
  overall thickness envelope consistent with the fixed mechanical design.
  The intervals' unconstrained sum is not automatically that mechanical class.
- Include maximum and minimum conductivity across the actual operating class.
  The separate nominal-hot and normal all-metal proposals remain unselected.
- Treat drill diameter, plating thickness, hole registration and etch changes
  with compatible domain maps or independently proved subset/superset trial
  constructions. A depth map does not cover any of these planar/radial changes.
- Preserve actual finite contact support and normal traces throughout each
  geometry range. Every main/lead/solder/wire interface must have a common
  physical source and observation definition in both bounds.
- Charge solder, contact interface and complete wire energies under their own
  valid classes. Independently fixed contact/Robin laws cannot be multiplied
  by the copper depth/material factors without a separate derivation.

Actual manufacture remains unqualified under #65. An as-built re-extraction
check is an additional obligation; it does not replace a finite design class
with exact nominal geometry or excuse a computable failed electrical limit.
