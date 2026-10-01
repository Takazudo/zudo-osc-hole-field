# Finite contact flux class for joined ground witnesses

Status: **conditional project requirement selected for the next computational
source class; physical qualification NOT RUN (#57/#65)**. This does not select a
manufacturing service or prove the common/current/voltage limits. A missing
physical support or failed numerical bound still prevents adoption of #38.

## Independent current and redistribution budgets

Retain the original single global return coefficient budget: sum(abs(x_i)) <=
4.6 A for the externally driven, named balanced source columns in
`ground-network-composition.md`. External balancing currents are included in
each column, not charged a second time to that coefficient norm. This still
allows 9.2 A balanced contact L1 in a one-signed 4.6 A return scenario.

Additionally require the following independent normal-operation flux-shape
class on external active-circuit/source boundaries. For contact support D_i
of area A_i, signed current I_i and normal density q_i, define

```
g_i = q_i - I_i/A_i,     integral(D_i, g_i) = 0,
r_i = sqrt(A_i) * norm(g_i, L2(D_i)),
sum_i r_i <= 4.6 A.
```

The second 4.6 A is a separate **PROJECT REQUIREMENT**, not a consequence of
supply rail caps, a manufacturer rating, or a restatement of the first norm.
It deliberately permits nonzero redistribution at I_i=0. No per-board copy of
either budget is allowed. Both budgets must hold in the same declared normal
scenario, including reactive/leakage and permitted external patch effects.
Startup/fault or other operation outside this class is not covered. Physical
qualification must establish the boundary flux class, not merely net terminal
current. The choice is retained before computing its resulting error bounds;
it must not be narrowed afterward merely to pass a target.

Passive internal GH/main wire interfaces are not new external injections.
Their opposite normal traces must glue pointwise and cancel. Their complete
finite conducting volumes and constructive trial fields remain mandatory;
this external-source budget cannot replace missing lead/crimp/mating volumes
or prescribe the reciprocal solution's passive interface current density.

## Constructive slab and coordinates

Use a homogeneous isotropic rectangular conducting slab D x [0,h], D of width
w and length l, with finite positive h and resistivity rho. This is a contained
physical volume requirement, not inference from a PCB pad drawing. In this
local coordinate system q enters at z=h and a uniform profile exits at z=0.
Outward normal fluxes are -q at h and +I/A at 0. Map these coordinates to the
actual native pad rotation and physical F/B normal explicitly; a B-side slab
must not inherit the F-side global z sign.

For zero-mean g, the insulated-side Neumann problem Delta psi=g has a weak
solution. The field

```
Jxy = grad(psi)/h,
Jz = -I/A - (z/h)*g
```

has zero divergence, zero side flux and the exact two normal traces. Its energy
has the bound

```
E <= rho * [h*I^2/A + (h/3 + max(w,l)^2/(pi^2*h))*norm(g,L2)^2].
```

This covers every allowed L2 trace, including infinitely many spatial modes;
no finite sampling or physical uniform injection is assumed. The implementation
uses pi^2 > 9, exact rational arithmetic on represented input values and an
outward binary64 conversion. For a positive height interval the bound is convex
in h, so its maximum is at an endpoint. A maximum resistivity is required.
`contact_flux_lift.py` and its cosine-mode/divergence/trace/zero-net/outward
regressions retain this construction.

## Physical source support admission remains mandatory

Each source contact must have a named native ref/pad/UUID, physical face,
rotated support rectangle, contained positive slab and native copper/foil
attachment. Minimum support, maximum possible wetting, registration envelope,
full possible contact metal and conductivity bounds are separate requirements.
A continuous primal witness must extend across that full metal domain; a
constant trial over it is an admissible restriction, not an ideal physical
short. A dual witness must glue actual pointwise traces to the foil lift and
all further lead/wire volumes. Slab energy is charged exactly once.

The current GH support candidate is 0.18 x 0.25 mm, h=0.025..0.05 mm and hot
rho<=2e-4 ohm mm. These dimensions are conditional process requirements,
not JST minimum guarantees. The actual pad-frame inventory and all possible
wetting must be checked per terminal. This slab class alone does not select
or prove the remaining GH lead/crimp/mating geometry, own-load lead families,
main nineteen-strand interfaces, normal/cold conductivity envelope, or the
paired whole-network contact observables. Those missing admissions continue
to block an authoritative electrical result.
