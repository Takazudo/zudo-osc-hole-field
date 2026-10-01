# Observation-first joined ground witnesses

Status: **implementation plan; no physical contact/current/material class or
common allocation is selected**. Numerical patch averages remain diagnostics.
This plan reduces redundant solves; it does not discard source scenarios.

## Exact network and objective

Use the source incidence in `ground-network-incidence.json`: all ten boards,
380 GH wires and nine main wires. For one GH candidate remove exactly that
physical edge, leaving 388 edges and all nine mains. For a P utility candidate,
the other three utility edges remain. No K, P, EL, adapter or balancing contact
is replaced by an ideal rest node. Each board has its own current conservation.

On this candidate-open physical network, b is the signed voltage observation
at the actual local GH terminal minus its actual remote GH terminal. The
reconnection inequality must use the same physical terminal functional and
the retained candidate wire minimum. The candidate contributes zero extra
PCB/contact denominator credit. A 50 mOhm maximum contact resistance gives no
positive contact-resistance lower bound. A patch average does not by itself
supply the scalar Thevenin terminal required by this step.

Every external source column e_i is balanced between named actual load and
source contacts. The coefficient convention is the one in
`ground-network-composition.md`: one global sum(abs(x_i)) <= 4.6 A return
class, not 4.6 A independently on every board or on the balanced full-contact
L1 norm. All resistor caps, reactive/leakage/patch circulation and independent
zero-net redistribution require their exact mechanism and scenario constraints.
No typical or quiescent-current substitution is made.

The separate common-ground, common-rail and total-voltage objectives remain
mandatory: combined branch/K common <=0.5 mOhm; rail common <=1 mOhm;
distribution <=20 mV; source/rail/return total <=0.20 V. Private uncertainty
cannot be subtracted from an unrelated transfer bracket. Their source and
observation functionals, physical regions and once-only cost ledger must be
named before judging a result.

## Variational bound

Let a be the complete physical passive-conductor energy form on the gauge
quotient, with the actual wire/contact/foil materials and interfaces. It must
be coercive on the represented connected network. Let u_b solve a(u_b,w)=b(w).
A pointwise continuous admissible potential v_b gives

```
L_b = 2 b(v_b) - a(v_b,v_b).
```

A conserved, fully glued current trial gives U_b >= a(u_b,u_b). Thus

```
a(u_b-v_b,u_b-v_b) <= U_b-L_b = Delta_b.
```

For each permitted balanced source e_i retain an admissible conserved current
trial with energy U_i. Reciprocity and Cauchy-Schwarz give

```
|T_bi - e_i(v_b)| <= sqrt(Delta_b * U_i).
```

For f = sum_i x_i e_i, without assuming independent source signs or losing
actual circuit correlations,

```
U_f <= (sum_i |x_i| sqrt(U_i))^2
|b(u_f)| <= |sum_i x_i e_i(v_b)|
             + sqrt(Delta_b) sum_i |x_i| sqrt(U_i).
```

Optimize this expression over the unchanged supported scenario constraints.
It is legitimate to evaluate every e_i(v_b) without solving a separate load
right-hand side. Every e_i still needs its physical support, complete source
identity and constructive U_i. A source group can replace individual columns
only with a proved incidence/current relation covering every permitted member.
The 1903 K own-load contacts are not zero because the old coupling matrix
omitted them. The current K prerequisite must admit all 376 GH plus nine mains
and retain every own-load functional before this route is used.

Numerically, use a lower enclosure of 2 b(v_b) and an upper enclosure of the
complete a(v_b,v_b); retain all conservation/formation/roundoff charges in U_b
and U_i. Reject an inconsistent negative gap before any numerical nonnegative
handling. Energy Loewner ordering does not order individual wire currents.

## Physical source and contact conditions still required

Finite minimum pad coverage and a terminal-current L1 limit do not bound
three-dimensional self energy for arbitrary concentrated boundary flux.
Neither a uniform patch nor a finite list of samples covers that class.
Every e_i must have a fixed finite admissible trace family, or a uniform
energy bound for *every* permitted trace, with a constructive lift matching
its real normal current. This applies to every own load as well as mains/GH.

Two possible source contracts must not be conflated:

1. A finite passive lead/contact volume connects the PCB to an explicitly
   defined active-circuit boundary. If that external boundary is modeled as
   an equipotential terminal with prescribed total current, uniform current
   is only an admissible trial there; no physical uniform PCB injection is
   assumed. The boundary abstraction and any real nonuniformity allowance
   need explicit source applicability. Passive wire cuts cannot acquire an
   equipotential assumption merely by this label.
2. A prescribed physical boundary-flux family includes a constructive finite
   energy bound for redistribution from each allowed trace to the reference
   profile. Its amplitude/energy constraints include zero-net redistribution;
   a bound proportional only to net current would miss that case. Minimum
   geometry alone does not supply this bound.

The first bounded GH geometry candidate uses the actual pad frame and asks
for minimum 0.18 x 0.25 mm connected transfer support, solder thickness
0.025..0.05 mm and hot solder resistivity <=2e-4 Ohm mm. Maximum PCB wetting is
the actual 0.6 x 1.7 mm native pad. These are **unselected PROJECT requirements**,
not JST guarantees. The regional 0.2 mm nominal lead width / 0.7 mm projection
supports neither a minimum rectangle nor lead thickness. Lead, crimp, mating
interface and strand geometry, maximum possible metal extent, full paired
traces and the existing 50 mOhm/end total energy accounting remain required.
A solder slab alone does not close the GH class.

For materials, retain the original per-board nominal foil counts/depths and
separately select finite positive foil/gap/barrel/drill/etch/registration
ranges with both conductivity directions. The broad 100 MS/m all-metal ceiling
is still a candidate requirement, not an inferred temperature floor or
manufacturer guarantee. A narrower floor is not selected to fit a nominal
margin. Physical qualification remains #57/#65; that does not waive any
computable failure or replace a finite class with impossible zero tolerance.

## Immediate bounded implementation

Construct the five actual O prerequisites and bare EL source authority,
retaining all fixed source hardware, holes, exclusions and original outlines.
Use the reviewed explicit two-foil/reference path. Require fresh source/native
identity, companion and connectivity gates before any operator admission.
No full EL/O matrix or 2287-column K run follows automatically. After finite
source/contact/material contracts are concrete, implement and test the joined
observation and constructive source-energy witnesses against a small complete
network before selecting the minimum necessary large calculations.
