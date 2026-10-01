# Issue 38 drilled-source 3D flux: smallest constructive next step

Read-only design audit, 2026-09-30. No code or board source was changed. The retained nominal receipts report 213 single-drill SMD, 5 multiple-drill SMD, and 305 PTH geometry certificates with zero unresolved rows. They certify historical geometry only; the PTH receipt reports zero qualified finished walls. Current-epoch UUID/geometry transfer is a separate obligation.

## A common cut-plane contract

Make one *source-to-foil cut* per local field, with a source trace on the actual exterior metal boundary and a specified **pointwise** return profile on an internal copper cut. These are field interfaces, not necessarily disjoint partitions of material: a PTH wall field and a face field can occupy the same metal. The downstream conductor field must supply the opposite **sum of all local profiles** at every geometric cut. Record its physical face, orientation, support, and exact source/native epoch. Current equality alone is insufficient. Charge all fields on overlapping metal by a Gram bound or by `(sum sqrt(E_i))^2`; do not sum diagonal energies. For the paired lower witness, use one continuous H1 potential, constant over the **entire possible wetted support** of a terminal (including the PTH wall and both exterior annular faces), with that same constant through its lead/contact metal. The constant is a trial-space restriction, not a physical equipotential assertion. Its trace on every cut must equal the downstream potential trace; otherwise supply a finite-energy transition and charge it. The source functional then equals `I*V_terminal` for every allowed flux shape.

### Drilled SMD: one planar cover lift extruded in actual foil

For each of the 218 certificates, let `D` be the union of its actual same-face annulus and convex domains, excluding every drill; let `S` be the exact disjoint first-domain partition of the possible source support. Choose a positive contained reference patch `O` on an *internal cut within the same foil*, and `b=1_O/|O|`. Its cut must be below a strictly positive source slab thickness `h` and leave strictly positive foil thickness for the downstream conductor. For any signed external `q in L2(S)`, `I=int_S q`, set `f=q-I*b` on `D` (zero extension). Thus `int_D f=0`, including `I=0` with nonzero redistribution. Solve `Delta psi=f` with insulated boundary on each cover domain, using the existing exact overlap tree to cancel all internal mean transfers. With local depth `z=0` at the internal cut and `z=h` at the exterior, use

```
J_xy=grad(psi)/h,       J_z=-I*b-(z/h)*f.
```

It has zero divergence; exterior outward trace `-q`, internal outward trace `+I*b`, and zero trace on the actual drill wall and lateral boundary. The field may live on the union of pad and via-land copper; all overlaps are one metal volume, not duplicated copper. `finite_cover_flux.cover_poincare_upper` provides a conservative planar `C` once each local convex/annular Poincare bound, an upper bound on the **whole support of f** (including O), and every exact overlap-square lower area are supplied. The 3D energy satisfies

```
E <= rho_max * ( |I|*sqrt(h/|O|)
                + ||f||_L2(D)*sqrt(C/h+h/3) )^2.
```

This form includes base/correction cross energy. The declared flux-shape class must bound `||f||`, either directly or by a proved transformation from the existing `q-I/|S|` norm. Do not substitute a sampled q. Verify the actual foil band, face reversal on B.Cu, cut location, and the reference patch against the current native board; historical cover digests alone cannot admit it.

### PTH: close the wall-to-foil trace, then use the same face lift

The existing `barrel_source_flux` mean-wall field exits at **the exterior B annulus**. Its B-face positive trace cannot be treated as a downstream foil port: it must be cancelled or rerouted in real copper. A finite constructive reroute is possible without a point electrode. Let `ri` be the actual finished inner radius, `ro=ri+t_plating` a proven contained full shell, `L` the board depth, and choose `0<d<t_B` in the actual B foil band and a complete annular land radius `R>ro`. Let `q0=I_wall/(2*pi*ri*L)`, `D=ro^2-ri^2`, `s(r)=(r^2-ri^2)/D`, `g(z)=1/d` on `[L-d,L]` and zero elsewhere, `G(z)=int_0^z g`. The stream function and shell field are

```
Psi=q0*ri*((1-s(r))*z+s(r)*L*G(z)),
J_r=(1/r)*partial_z Psi,
J_z=-(1/r)*partial_r Psi,       J_theta=0.
```

These give `div J=0`, wall outward trace `-q0`, zero end-face trace at `z=0,L`, and outer-shell radial flux `q0*ri*L/(ro*d)` only inside the upper `d` of B.Cu. Add the existing periodic/Neumann mean-zero wall correction for `q_wall-q0`; it has zero outer/end traces. On the adjacent physical B annular sleeve `ro<r<R`, `L-d<z<L`, let `D2=R^2-ro^2`, `C0=q0*ri*L/d=I_wall/(2*pi*d)` and

```
J_r=C0*(R^2-r^2)/(D2*r),
J_z=2*C0*(z-L)/D2,             J_theta=0.
```

Its inner radial trace matches the shell **pointwise**, its outer radial and exterior B-face traces vanish, and it exports `I_wall/(pi*D2)` uniformly through the internal B-foil cut at `z=L-d`. The exterior wall is never replaced by top-face injection. A simple safe wall-mean resistance coefficient is `rho_max*D/(4*pi*ri^2*L)*[max(1,L/d)^2+(2*ri*L/D)^2]`; the sleeve coefficient is `rho_max*D2/(4*pi*d)*[1/ro^2+(2*d/D2)^2]`. Evaluate with outward rational bounds, then apply the square-root sum across shell, sleeve, wall correction, exterior-face fields and downstream field. These are deliberately loose coefficients; improve only after a verified need.

Treat the F and B **exterior** annular source densities as two independent L2 traces. Apply the drilled-face cover lift above to each real exterior foil band, with cuts inside those bands and their own current `I_F,I_B`. At B, superpose the face field with the wall/sleeve fields on the same actual conductor and charge the cross energy; at F reverse the local depth. Retain all interior foil attachments but assign no external source there. The wall field continues through the shell below the B cut; its axial trace there must be retained when summing all fields on that section. The sleeve's stated uniform port is only on `ro<r<R`, not the whole cut. The downstream model sees every exact composite cut profile, and the terminal current is `I_wall+I_F+I_B`. If the current model accepts only one numerical port, construct and charge a further real-foil transfer to that port instead of identifying profiles by their totals. Validate the full physical domain/ownership and interface cancellation: shell/foil overlap is shared material, not two copies.

## One finite fixture and failure gates

Start with a synthetic two-drill rounded SMD pad whose exact receipt has two annuli and at least one convex child, plus a PTH fixture with `ri=.61 mm`, conditional `ro=.635 mm`, `L=1.6 mm`, `R>.635 mm`, `t_B>d>0`. Use signed trigonometric modes with nonzero mean and a nonzero zero-mean mode, and independently set `I=0` with a nonzero mode. Check analytic divergence and **all** normal traces (both drill walls, exterior faces, internal cuts, annulus outer radius, shell/foil radial interface, F/B orientation, angular seam) by symbolic expressions or interval-backed quadrature; integrate interface flux exactly and compare the energy integral with the outward bound. Test source partition and every overlap edge with exact rational predicates. Mutate one drill radius, remove one overlap square, set `d>=t_B`, reverse B orientation, omit B face flux, and perturb a radial interface profile; every mutation must fail before publication.

After this finite fixture, build per-contact receipts for all 523 drilled contacts at the **current** native epoch. Require complete source and material dependencies, unique UUIDs, exact source-to-cut profile hashes, no unresolved geometry, and replay rejection after a source/board mutation. The local construction alone does not qualify manufactured plating, etch/registration, solder/wetting support, resistivity intervals, lead and contact currents, or joined electrical limits. Those remain `NOT RUN`/open pending independent physical evidence and the paired whole-network model.
