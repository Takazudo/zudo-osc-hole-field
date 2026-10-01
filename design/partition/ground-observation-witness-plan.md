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

## Two-budget support implementation — 1 October 2026

`observation_support_bound.py` now evaluates the observation objective for an
explicit complete source-ID set and a separate complete redistribution-ID set.
For an admitted observation trial, let Delta be an outward upper of its energy
gap; let t_i be each source functional on the trial, U_i the complete balanced
source-current energy upper, s_j the normalized trace-oscillation upper on each
actual external source support, and C_j the energy upper for every permitted
unit normalized zero-net redistribution on that support. Then

```
|observation| <= B max_i (|t_i| + sqrt(Delta U_i))
                + G max_j (s_j + sqrt(Delta C_j)).
```

Here B and G are separate global ampere budgets (both 4.6 A in the retained
conditional source contract). They are not multiplied by board/contact count.
The second term remains even when every net injection is zero. Optional
per-source absolute-current caps use a greedy support optimization under the
single global B budget; each cap requires an explicit evidence reference, whose
physical validity remains the admission layer's responsibility. Other source
correlations may tighten the result; omitting them here is conservative.

All arithmetic after input interpretation is exact rational except the returned
binary64 values, which round upward. Square-root uppers use integer arithmetic.
Missing, duplicated or foreign identities, omitted coefficients, negative gaps,
nonfinite values and undocumented caps fail. No missing physical coefficient is
filled with zero. A small complete resistor-chain regression compares the bound
against all sampled signed net/redistribution scenarios; a zero-net regression
checks that redistribution is still charged.

For the existing unit-current voltage observation, Delta/U_i/C_j are in ohms,
and the objective is volts. For a closed-network unit-test-EMF wire-current
observation, Delta is in siemens, U_i/C_j remain ohms, and the objective is
amperes. These are different witness problems, explicitly named in the API.
The current result status is CONDITIONAL WITNESS SUPPORT ONLY. This helper does
not admit a physical class, supply continuous full-interface witnesses, or
accept any board/current/voltage target. Those inputs remain the next gate.

## Closed-network wire-current and regional common objectives

`cut_current_witness.py` implements an exact-rational resistor-graph regression
for the complete closed-network current observation. With incidence B (+from,
−to), resistance R, conductance C, signed candidate cut c, potential trial v and
conserved circulation k, let z=c−Bᵀv. The auxiliary unit-test-EMF gap is

```
Delta = zᵀCz − (2cᵀk − kᵀRk) = (Cz−k)ᵀR(Cz−k) >= 0.
```

For a balanced source f and a conserved source-current trial of energy U_f,
`|I_cut − fᵀv|² <= Delta U_f`. The candidate wire remains in the graph. The
continuum counterpart requires a pointwise unit potential jump across a complete
internal wire cross-section through every strand and continuity elsewhere.
Neither cut face is required to be physically equipotential. A bridge can have
zero auxiliary gap; negative variational lower values are also legitimate.
The graph fixture checks circulation/source conservation exactly and exercises
signed scenarios through the two-budget objective. It does not substitute a
lumped graph for unadmitted physical connector geometry.

A direct GH-current pass does not itself prove the separate common-ground
limit. `regional_transfer_bound.py` retains every region and bounds the actual
regional reciprocal integral rather than subtracting a private self resistance.
Given complete source/observation current error-energy bounds Delta_s/Delta_b,
and trial regional energy uppers U_s,W/U_b,W, its regional cross-product error is

```
error_W <= sqrt(U_s,W Delta_b) + sqrt(U_b,W Delta_s)
           + sqrt(Delta_s Delta_b).
```

The last term is charged once for a selected union of disjoint regions. Full
source and observation functionals must match those used by both witnesses;
the regional partition must cover the whole physical conductor exactly once.
Main-terminal spreading and shared necks cannot be renamed private to evade
the original limit. Private regions stay in the full current/voltage budget.
Negative regional cross products are allowed: regional transfer is not positive
energy and is not ordered by deleting copper. Exact resistor-graph tests include
such a negative regional transfer and conserved perturbed trial fields.

All three helpers provide conditional mathematical support only. Selecting the
actual common/private region partition and full finite connector/material/source
class, assembling compatible continuum witnesses and proving the original
0.5 mΩ / 0.5 A / 1 mΩ / 20 mV / 0.20 V limits remain required before #38 acceptance.
