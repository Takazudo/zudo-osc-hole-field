# External own-source boundary lifting

Status: constructive local source fields; **whole source-family admission and
joined electrical acceptance remain OPEN**. This uses the selected independent
external current/redistribution budgets in `contact-flux-class.md`. Passive GH
and main connections are not external source boundaries.

## Actual fitted boundary inventory

The current-source nominal inventory is reproduced by
`scripts/pcbgen/current_source_boundary_manifest.py`. Its retained local v6
receipt recomputes all 4,143 fitted own AGND identities from the current
partition/IO and native source records: JL 1,070, JR 896, K 1,903, P 214,
and EL 60. It checks the same 3,620/218/305 family split below and binds
source, pad, drill, stack and board digests. JL/JR, K, P and EL now use their
fresh current-source native prerequisites. P's fresh bare-v4, six-array plan
and full-v4 native receipt report zero rule/parity errors and all 344 ground
contacts connected. Its earlier v3 receipt remains historical; the
retained-v3 local geometry bridge is kept as a separately scoped audit.
Every row still has `physical_source_support_qualified=false`.

The source/net/UUID map contains all 4143 own-load ground contacts: JL 1070,
JR 896, K 1903, P 214 and EL 60. Current retained exports contain 3620 convex,
drill-free SMD pads, 305 PTH contacts and 218 SMD pads with actual 0.3 mm drill
intersections. The latter are not false bounding-box overlaps. Exact rational
circle-to-rectangle/rounded-rectangle separation retains a 2 nm guard and each
drill UUID. All these intersecting drills are plated AGND vias. Historical
export identity is retained; bare EL and changed-source old native receipts
remain prohibited from current model entry.

A PTH source includes actual exterior annular foil contacts and the inner
barrel wall. SMD with an intersecting via also needs the actual cut domain.
Neither is replaced by a convex hull, an ideal ring or a top-face injection.
The planned finite cover uses actual same-net annuli plus convex pieces of the
pad, with positive contained overlap regions. Every mean transfer between
regions must have a constructive field and charged energy before admission.

## Convex SMD foil correction

Let D be the actual convex copper pad section and D x [0,h] a contained foil
slab, with no intersecting drill or removed copper. The physical external face
is z=h in a local coordinate system directed away from the board; z=0 is the
internal face. The full possible source support is D, although actual wetting
may be a smaller subset and q may vanish there. No claim of full-pad wetting
is made. Material/etch/registration uncertainty must preserve or explicitly map
these hypotheses before an actual process envelope is accepted.

For a reference profile uniform on a proved contained patch S, write
q=I/A+g, integral_D(g)=0, r=sqrt(A)*norm(g,L2(D)). The mismatch
q-I*1_S/|S| has zero integral. A Neumann solution Delta psi=delta gives the
conserved correction Jxy=grad(psi)/h, Jz=-z*delta/h. It has outward trace -delta
on z=h and zero on the inner face/sides. Its geometric energy bound is

```
E <= rho_max * (h/3 + diameter(D)^2/pi^2/h) * norm(delta,L2(D))^2.
```

The convex Neumann estimate is stated in equation (1.4) and proved within
Theorem 1.1 (p=2) of Esposito, Nitsch and Trombetti,
[Best constants in Poincare inequalities for convex domains, arXiv:1110.2960v1](https://arxiv.org/pdf/1110.2960v1),
physical PDF index 1 / printed page 2. Version bytes are retained at
`math-evidence/1110.2960v1.pdf`, SHA
`61071ee2e4fdd736958fda4698e32a305d45a9e0620778dc186a597235a66242`.
This geometric auxiliary problem does not assume that the real PCB potential
is harmonic in a homogeneous material. A pointwise resistivity upper bound
suffices for the trial-field energy inequality.

`convex_source_flux.py` uses pi²>9 and rational area/diameter bounds. Separate
unit-current profile-transfer and unit normalized-redistribution bounds are
retained. The complete current field is a superposition with the existing
foil field. Charge at least

```
(sqrt(U_base) + |I|*sqrt(U_net_transfer) + r*sqrt(U_redistribution))^2
```

or a tighter proved Gram bound. Simply adding diagonal energies is invalid.
The primal witness must be constant on the entire possible source support and
continuous through every connected conductor used in its extension; this is
a restriction on a trial field, not a physical equipotential-pad claim.

## PTH inner-wall zero-net correction

Let ri and ro be the actual inner/outer radii of the plated shell, with L the
actual length. In surface coordinates u=ri*theta, z in [0,L], use the actual
inner-wall measure du dz=ri dtheta dz. For mean-zero delta, solve the periodic-u,
Neumann-z problem Delta psi=delta. With D=ro²-ri² and w=(ro²-r²)/D, define

```
Jr     = ri*delta*w/r
Jtheta = 2*r*psi_u/D
Jz     = 2*ri*psi_z/D.
```

Cylindrical divergence is exactly zero. Inner outward flux is -delta; outer
wall and axial end fluxes vanish. The angular seam and axial end conditions
are part of the construction. The radial energy coefficient is at most ro-ri;
the larger tangential coefficient is (ro²+ri²)/(ri*D). The periodic/Neumann
Poincare coefficient is at most max(ri²,L²/9), so

```
E <= rho_max * [(ro-ri)
      + (ro²+ri²)/(ri*D)*max(ri²,L²/9)] * norm(delta,L2(inner wall))².
```

`barrel_source_flux.py` rounds this coefficient outward from exact represented
inputs. The actual jack ri=0.61 mm / ro=0.635 mm / L=1.6 mm mode fixture checks
cylindrical divergence, inner/outer/end/seam traces and three-dimensional
energy quadrature. The zero-net correction never supplies the nonzero mean
wall source: a wall-to-existing-foil/reference base field, all cross energy,
annular exterior faces and full primal continuation remain required. The
source radius must equal the physical wall or have a certified compatible
geometry map; a contained shell alone cannot lift flux from a different wall.
Finite plating/drill/depth/material ranges are separate source requirements.

## PTH inner-wall mean to annulus base

The standalone conditional `pth_wall_to_b_cut.py` now carries a **uniform
full-wall mean** through a complete plated shell and B annular sleeve to a
specified internal cut inside B.Cu. Its shell and sleeve radial traces match
pointwise, the exterior B face has zero flux, and it retains an outward
upper energy bound. The construction requires a full physical wall, a complete
same-net B annulus, `0 < transfer depth < B foil thickness`, and a hot
resistivity upper bound. These are unqualified PROJECT premises, not measured
properties. It is not yet joined to the native downstream cut, the independent
exterior F/B face fluxes, the wall zero-mean correction, or a continuous
whole-network primal witness. The current-epoch PTH local geometry bridge
records all 305 nominal fitted PTH contacts (JL 100, JR 80, P 120, K 5);
it qualifies zero finished walls or electrical source fields.

For a net inner-wall current I over the full actual inner wall, let
q=I/(2*pi*ri*L), D=ro²-ri², w=(ro²-r²)/D and let z=L be one actual exterior
annulus. The retained local field is

```
Jr=q*ri*w/r, Jtheta=0, Jz=2*q*ri*z/D.
```

Its radial divergence is -2*q*ri/D and its axial divergence is +2*q*ri/D.
The inner-wall outward flux is -q; the outer wall and z=0 have zero flux;
the z=L annular outward flux is I/(pi*D). The cylindrical volume measure is
2*pi*r dr dz. Bounding |Jr|<=|q| and |Jz|<=2*|q|*ri*L/D gives the
conservative unit-current resistance upper

```
rho_max*D/[4*pi*ri²*L] * [1+(2*ri*L/D)²].
```

`barrel_source_flux.py` evaluates an outward rational upper using pi>3.
The construction requires a real full plated inner wall and full receiving
annulus of the specified radii and length. It carries only the wall's mean
current to that annulus. Annulus-to-foil transfer, exterior annular source
flux, the prior zero-net correction, their cross energy, finite process
envelopes, and complete primal continuation remain open. A physical source
class must bound current partition among actual wall and exterior faces;
this field does not impose uniform real injection.
