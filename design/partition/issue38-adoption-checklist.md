# Issue 38 source-adoption gates

Status: **OPEN / unselected source variant.** The canonical boards are unchanged.
Numerical diagnostics and native connectivity passes do not yet establish the
required electrical limits. All CAD remains an unvalidated draft.

## 1. Complete the numerical coverage

- [x] Source-replay native equivalence: JL/JR rule and parity errors zero,
  exact 507/475 warning identities, 599/553 fitted rail feeds, 214/200 complete
  bypass loops/feeds/returns, zero open AGND pads, and unchanged complete named
  signal-edge inventories of 1063/1109.
- [x] JL full nominal ground basis: 1176 profiles. The latest paired result has
  explicit original-current/new-potential provenance. Its unrestricted
  all-reference upper intervals are 0.497505 / 0.492558 / 0.511111 mOhm.
- [x] JL +5 full nominal rail basis: 59 profiles. R3306:1 is the worst full
  pad-to-main upper, 8.429654 mOhm, or 4.214827 mV at the full 0.5 A envelope.
- [x] Historical JL +12: the reviewed current refinement completes all 271
  profiles. Worst U1416:4 full upper is 5.124917301 mOhm. The actual shared
  IC/bypass exit then motivated source-owned parallel feeds.
- [x] Historical JL -12: all 269 profiles complete; worst U109:4 full upper is
  4.752883211 mOhm. These values retain their original geometry hashes.
- [ ] New parallel-feed JL/JR geometry: recompute applicable ground/rail
  witnesses. The 214 JL and 156 JR added vias change holes and fills, so none
  of the earlier electrical receipts is rebound to the new geometry.
- [ ] JR +12/-12/+5 full fitted-contact matrices and path accounting.
- [ ] JR full ground basis, including every physical load/observation/main
  contact and the source-independent UUID inventory.
- [ ] Fixed physical geometry/profile refinement and origin checks with a
  positive numerical margin. Do not change a physical contact when refining.

The smallest useful numerical improvement is to reduce demonstrated trial
error, not invent lower currents. In the actual 0.3 mm drill / 25 um barrel,
a local fixed-geometry diagnostic gives F-to-In1 upper/lower gaps of 0.141694,
0.098275 and 0.076956 mOhm for 2/4/8 radial subdivisions with other subdivisions
fixed. B-to-In1 gaps are 0.059826 / 0.043091 / 0.035633 mOhm. These are template
diagnostics, not whole-board results; they identify a concrete convergence
cost. Current row-specific work bounds are now available as well. Use the
full unrestricted load envelope first so resistor caps are unnecessary if a
tighter certificate suffices.

## 2. Select a finite material and manufacturing class

**Computation required before electrical acceptance:** define the actual
conditional class and evaluate valid upper and lower witnesses across it.
Nominal F/In1/In2/B copper is 70/140/70/70 um and the seven-band stack totals
1.6 mm. A valid class needs finite positive foil/dielectric/plating intervals,
maximum conductivity as well as minimum conductivity, and compatible drill,
etch/registration and collar/interface geometry maps. A minimum copper or
barrel thickness alone cannot justify the potential witness for thicker metal.

Do not promote the unselected 100 MS/m normal all-metal ceiling or a uniform
70 C hot floor to a guaranteed all-temperature class. Fixed-domain global
resistivity scaling is only an enclosure diagnostic: a +/-5% pointwise range
already widens the resistor-conditioned JL intervals to 0.508885 / 0.523013 /
0.542353 mOhm. This is not a physical failure and does not justify narrowing a
material floor to fit the target. Correlated material/process parameters or
more precise matched-domain witnesses must be represented explicitly.

**Later physical qualification (#65):** supplier/pressed-stack feasibility,
actual copper and plating, etch/registration, solder/process coverage and hot
measurements. No service is selected and no manufacturing claim is made. Any
as-built re-extraction obligation must be named separately from the finite
class actually proved by the design calculation; it cannot replace that class
with impossible zero tolerances.

## 3. Close the physical contact and current functionals

**Computation required:** the lower and upper operators must represent the
same actual source and observation functionals. Current numerical GH/load
patches are not a solder or lead-current guarantee. A 0.25 mm square cannot
be asserted to fit the nominal 0.2 mm GH lead width.

The preferred existing route is a constructive finite contact/wire class:

- Compose the nineteen supported main currents through finite solder, tips,
  fans, adapters and complete wires. Keep the continuous primal constant over
  the complete allowed wetting support. These are trial constraints, not an
  ideal physical pad or cut.
- Extend the same principle to actual GH and fitted-load interfaces using
  supported finite contact geometry. Preserve both minimum current-path
  support and maximum possible contact-metal extent. Include every finite
  transfer charge and possible passive contact shunt.
- Prove which resulting observable is common PCB/K spreading and which terms
  are separately paid private access/wire/termination costs. Do not subtract
  private uncertainty from an unrelated transfer interval.

A profile-independent continuum alternative needs a real finite-to-continuum
bound. Covering the pad with sample patches, a surface average, or zero net
terminal current does not alone establish that bound. Do not add another
whole-board nominal run merely to disguise this applicability gap.

**Current scope required:** map the normal signed branch currents to actual
source contacts, with every actual boundary flux included. The original 4.6 A
whole-return envelope applies to the sum of absolute load-to-balancing-source
coefficients, not to the L1 norm of the fully balanced contact vector. For one
+I/-I pair these norms are |I| and 2|I| respectively; 4.6 A of one-signed
returns plus its balancing source gives 9.2 A of full-contact L1. The exact
external incidence E and coefficient budget are defined in
`ground-network-composition.md`. Capacitive, leakage and permitted external
circulation coefficients require explicit mechanisms and total-variation
allowances; input rail caps alone do not bound them. Prefer circuit KCL,
source rail cuts and exact resistor/voltage mechanisms over planning currents.
If a local access cost needs a smaller current, establish that specific bound.

The example 75 V / operating R >=0.9 nominal resistor conditions bound only
resistive current. A total-terminal cap at the same value is a separate
unselected requirement, or needs additional quantified parasitic/leakage/edge
terms. The 153 exact source shunts preserve 112 x 100k and 41 x 5.6k values;
blank MPNs inherit no exact-part guarantee. Bypass, sleeve, input and IC currents
are not reduced by that example.

**Later physical qualification:** normal source/waveform realization #57,
patch/fault/transient limits #59, and actual material/contact/current behavior
#65. These links do not waive a computable design failure or imply fitted
current-limiting hardware.

## 4. Derive usable common and K allocations

**Computation required before #38 acceptance:** common branch plus K ground
spreading/shared neck/main transfer <=0.5 mOhm, with finite positive common
and private K requirements. The resistor-conditioned nominal JL screen leaves
only 0.016608 mOhm at its worst reference before K and class/interface additions;
that leftover is not an accepted or demonstrated feasible K allocation.

Use the exact K source port locations and intended conductor class to assess a
constructible allocation. The actual K PCB in #43 must then extract and verify
that allocation. GH proof must include all individual accesses once, all four
utility returns, and candidate PCB/contact resistance zero. The retained
alternative wire/contact allowance is +0.100 Ohm, not +0.010 Ohm. The joined
operator requires actual J-GH to K-GH observations and compatible full traces;
the algebra helper does not supply an ideal K board.

The retained K v7 full nominal ground calculation now covers 2,287 profiles:
1,903 fitted own contacts, 376 GH returns and nine main lands, with 219 barrels.
Its completed paired result and historical source scope are recorded in
`core-nominal-checkpoint-20261001.json`. Earlier v6/214-profile coupling screens
remain historical subsets. No result completes K rail/signal routing or the
physical/joined common-current proof. The four utility returns still require
P/rest-network coverage. Native connectivity supplies no resistance or
equal-sharing credit. The latest partition epoch changes one retained native
prerequisite hash; no old receipt is rebound to it.

## 5. Close every voltage budget with the same source scenarios

**Computation required:** combined common rail <=1 mOhm, hot distribution
<=20 mV and total source/rail/return <=0.20 V. Include all land/foil/shared-neck,
barrel, local pad/escape, wire and termination costs. Local access may be charged
at a supported actual branch-current bound or conservatively at its applicable
source envelope; it cannot disappear as a private zero term.

For +5, adding the full nominal 4.214827 mV JL access result to the existing
12.1075 mV baseline gives a conservative 16.322327 mV screen. This intentionally
takes no credit for overlapping common terms. It does not prove the separate
common-rail/K cap, material/contact class or omitted return-access costs.
The +12 and -12 scenarios have different original baselines (16.6275 and
16.345 mV); do not reuse +5 headroom. Keep worst single main return at 4.6 A.

The proposed finite whole-wire witness can be used only after its physical
class and matching traces are selected. Its shorter geometric path does not
permit unproved extra credits against its historical 125 mm / 13 mOhm per m /
0.2 mOhm termination model contract. The current partition separately selects a
110 mm maximum main-wire cut requirement and checks preparation allowance.
That new source requirement improves the conditional distribution arithmetic;
transfer it to a complete wire witness only after proving matching length
boundaries and traces. The physical wire/contact model has not been rebound.

## 6. Promote only the proved source and refresh all receipts

- [ ] Parent records the exact selected plane/stack/contact/current/class and
  downstream #39/#43/#57/#59/#65 contract deltas before canonical promotion.
- [ ] Regenerate the selected source and canonical native boards through the
  pinned KiCad 10.0.6 oracle; preserve fixed hardware, prior copper, owner style
  and every explicit retirement receipt.
- [ ] Bind electrical models to the final board/native/project/definition,
  source/current/profile/operator and model hashes. Reuse only explicitly
  proved physically identical inputs, never a blind hash substitution.
- [ ] Refresh native full named signal edges, warning identities, exact source
  placements, power/return inventories, renders, source documents and reports.
- [ ] Run required affected checks and foreground self-review; commit only the
  concrete reviewed result. Remaining routing must be precisely bounded SIGNAL
  routing with the issue-policy follow-up, not a power/model waiver.

The current critical path is physical-function/class applicability plus a
meaningful common/K certificate. Additional nominal matrices provide coverage
and expose concrete access costs; they do not by themselves close that path.
