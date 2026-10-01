# Finite contact and whole-wire trial proposal

Status: **unselected conditional model**. No manufactured contact, wire class,
PCB, or joined J/K network is accepted by this note. Physical qualification is
NOT RUN under #65. Alpha 5859 BK005 remains the exact fitted wire identity.

## Compatible fields across the whole wire

A wire cut is not assumed to be physically equipotential. The current trial
carries I/19 continuously through nineteen contained strand sections, both
finite fans, both redistribution tips, the solder supports and the PCB foil.
Normal current traces must agree at every interface. Transverse current may
jump at a shared face without creating a divergence source or surface energy.

For a strand normal-frame map F(s,u,v), with positive Jacobian
h = 1 - curvature dot (u,v), a Bishop-frame trial has physical current
J = I t/(19 A). A centred section gives Joule energy
rho I² L/(19² A). Curvature does not add energy to this particular current
trial. Rotation of a non-circular trial section adds a bounded term:

```
R_upper <= rho/(19² A) * sum_k integral(
    1 + omega_k² * m2/(1 - a*kappa_k), ds)
```

Here omega is **trial-frame spin**, not an asserted Alpha lay rate. The actual
strand centreline arclength and curvature are separate geometric conditions.
A genuinely contained circular normal core allows a Bishop-oriented inscribed
polygon independently of the conductor's material rotation; endpoint polygon
phase and normal matching still require construction.

The current polygon can be centred at its own centroid, with the frame origin
translated by the same amount, so the physical section does not move. The
whole actual polygon must remain inside the declared circular core. Added
metal may carry zero trial current. The current class constrains individual
contained paths; a scalar assembled parallel DCR does not bound their
arithmetic-mean transfer energy.

The potential witness is one continuous function of the **bundle coordinate**
through all actual bulk metal, including any touching strands. If the total
metal area in each bundle-normal section is at most Amax, every conductive
material has rho >= rho_min, and h >= hmin > 0, a linear potential drop across
axis length L has energy at most Amax * deltaV²/(rho_min*hmin*L). Thus it
supplies the finite lower resistance rho_min*hmin*L/Amax. Both fans, tips and
solder can carry their respective land's constant trial potential. This
restriction sacrifices lower-bound sharpness; it does not claim a physical
short across a land or between strands.

## Main land and termination accounting

The dual PCB source uses nineteen disjoint 0.24 mm squares, each carrying I/19.
The current extraction checks every square against the actual circumscribed
barrel/collar ownership polygons. Their union is one exact balanced source
functional, avoiding a rounded sum of nineteen fractions.

The primal is constant over the entire possible wetted 4 x 4 mm land and every
owned array barrel touching it. Additional solder may cover insulation but
must not contact copper beyond the stated maximum support. The same constant
extends through all such contact metal. These scalar variables describe a
restricted trial space, not physically equipotential PCB nodes.

The existing combined termination allowance is 0.2 mOhm per complete wire.
The finite two-end fan-bending, tip-redistribution and solder charge is about
0.024429118 mOhm above the straight-wire baseline. A proposed normal interface
energy class of 0.000045 ohm mm² at each of four metallurgical interfaces adds
0.164473684 mOhm for the nineteen square supports. Their sum is about
0.188902802 mOhm, leaving 0.011097198 mOhm before adapters. The explicit two-end adapter debit is 0.006304825 mOhm, leaving 0.004792373 mOhm. These interface values are project
requirements requiring qualification, not manufacturer guarantees. Endpoint
adapters must also fit the remaining energy and existing 4 mm fan-length
budgets before selection. No interface is silently treated as zero resistance.

The bulk-wire baseline and the fans' straight-wire baseline are counted once.
The historical 125 mm / 13 mOhm per metre / 0.2 mOhm comparison is retained
under an explicitly historical output name. The current helper separately reads
length, hot resistance per metre and termination allowance from
`partition-input.json`. At the current 110 mm limit, these give a complete-wire
budget of **1.630 mOhm**, including both terminations.

| Branch | Conditional whole-wire upper | Current budget margin |
| --- | ---: | ---: |
| JL | 1.407810 mOhm | 0.222190 mOhm |
| JR | 1.383835 mOhm | 0.246165 mOhm |

Table values are rounded for display. The helper compares the computed trial
value against exact decimal source-budget arithmetic without a favorable
tolerance and rounds the reported margin downward. This does not improve the
upstream numerical trial's own arithmetic or physical applicability. A negative
current margin is reported as a failed conditional comparison even if the
historical budget would pass. The separate termination margin also consumes the
current source allowance, rather than a hard-coded 0.2 mOhm value.

These are **conditional arithmetic comparisons**, not adoption of the wire
class or transfer of a new margin into joined ground/rail acceptance. The
reported 96.190423 / 94.288670 mm bounds cover *mean contained-strand arclength*
with both fans. A mean does not bound the longest strand, prove an actual
finished cut length, or establish source preparation/slack and endpoint
compatibility. Those geometric and trace conditions remain open. P is not
evaluated by this JL/JR curve construction: its unequal endpoint y coordinates
need a separate compatible construction. No JL/JR result is assigned to P.

## Source and measurement functionals

A PCB numerical patch is not automatically an actual component electrode.
The present full-board matrices still use numerical GH/load probes. Extending
an actual physical-terminal current through a contact requires a compatible
finite current field; its lower witness must extend through all possible
contact metal. Scalar contact resistance alone is insufficient for an
arbitrary prescribed nonuniform patch transfer.

The common PCB/K spreading observable and the separately charged wire and
termination drops must be defined in the same joined operator. Private energy
cannot simply be subtracted from an unrelated transfer interval. A valid
composition glues conserved dual traces and continuous primal traces through
both boards and the complete wire, retaining matched private energy in the
operator bounds. Common spreading, GH current and each finite positive K
allocation then remain independent acceptance checks.

For a compatible linear current trial basis q, let M q be the vector of wire
currents, positive from J towards K. The two PCB source traces have opposite
signs: each J support carries -I/19 into its foil and each corresponding K
support carries +I/19. The complete upper energy is the sum of the PCB current
Gram matrices and `M.T @ diag(R_wire_upper) @ M`. Each bulk wire, fan, adapter,
solder layer and metallurgical interface is included once in the appropriate
term. The extra full adapter debit is explicitly conservative, as stated below.

For the paired potential witness, each complete wire adds an energy term
`(V_J - V_K)**2 / R_wire_lower` between its two full-wetting trial variables.
The normal proof must use the normal-material lower bound, about
0.334771739 mOhm for the proposed J/K geometry; the separate uniform-hot lower
is about 0.669543478 mOhm. Both represent restricted continuous trial fields,
not physical equipotential cuts. Gluing requires the same external source and
measurement functionals in both bounds and the actual K wetted supports.
These assembly equations are conditions for the future joined certificate;
the current nominal PCB caller does not yet implement that certificate.

The fixed-geometry material helper applies a proven pointwise resistivity
ratio to the entire matching-domain conductor energy operator. It does not
scale an independently fixed solder/interface resistance, change a source
functional, or certify foil, drill, etch or registration tolerances. Such
terms require their own valid bounds before summing the joined energies.

K #43 must consume the final source class, the matching maximum wetted support
and traces, and verify its actual finite common/private allocations. Existing
source, patch-ground, startup/fault and dynamic-current qualifications remain
open. The present numerical work does not substitute planning currents for
guaranteed maxima or waive any failed electrical limit.

## Constructed endpoint adapter class

An explicit 0.25 mm Bishop arc turns an incoming normal section with at most
3 degrees tilt into the exact horizontal fan-root polygon. Its minimum core
Jacobian is 0.963348; the maximum lateral centre offset is 0.0065435 mm.
At 0.37 mm root pitch, vertical containing cylinders retain a positive
0.0069130 mm gap. The maximum fan-plus-adapter path is 3.9323712 mm, inside
the existing 4 mm allocation. Actual incoming centres, tangents, roll and
contained tubes remain factory geometry requirements, not Alpha facts.

The full two-adapter energy is deliberately charged as conservative excess,
even though the 4 mm straight-wire baseline already funds its arclength. No
second baseline credit is taken. The paired primal stays constant through
0.075 mm collars at both bulk ends: this covers the all-metal 1.2954 mm radius
envelope at 3 degrees tilt, rather than just the smaller current-trial core.
The varying axial span is at least 81.05 mm for the proposed J/K geometry.

The proposed rho_min = 2e-5 ohm mm is **uniform nominal 70 C hot-only**. It
is not a valid cold/mixed-temperature lower bound. The maximum conductivity
across the actual permitted normal operating/material envelope remains an
explicit unresolved requirement for the GH-current proof.

A global axial end extent is not a bundle-arclength collar. With the declared monotone axis and slope bound, the near-end branch is established first; then z >= (1/kappa - R) sin(kappa s) gives s <= asin(kappa d/(1-kappa R))/kappa. The all-metal end extent 0.0679102 mm requires at least 0.0714846 mm of bundle arclength, enclosed by the 0.075 mm collar. The retained curved JL endpoint regression fails the former 0.070 mm choice.

A separate, deliberately broad **unselected normal material requirement** now
limits conductivity of every modeled bulk metal to 100 MS/m, equivalently
rho >= 1e-5 ohm mm, across whatever operating conditions are ultimately
permitted. It does not infer a minimum temperature or turn the hot-only floor
into a cold bound. Actual materials, coatings, temperatures and this direct
conductivity requirement remain NEEDS BENCH under #65 before selection. The
helper prints separate hot-only and normal-material lower bounds.

## Normal current envelope and resistor sensitivity scope

The numerical load basis covers every fitted source AGND contact. It does not
assert that every pad is an independent powered load. A total-current proof
requires the stated bound on the sum of absolute actual terminal fluxes,
including reactive discharge and external circulation within the permitted
operating class. Input rail caps or planning quiescent currents do not by
themselves prove that condition.

The unselected resistor sensitivity calculation uses exact source values:
100k and 5.6k contacts remain distinct, and a reused logical symbol does not
supply a missing MPN. The example conditions |V| <= 75 V and operating
R >= 0.9 times the exact source value bound only the resistive contribution.
They do not bound arbitrary parasitic C*dV/dt or leakage. Applying those
numbers as total-current caps therefore requires a separate, explicitly
unselected total-terminal-current requirement, or additional quantified
reactive/leakage bounds. The numerical margin from the resistive-only screen
is not an accepted K allocation.

Actual normal waveforms/source conditions remain open under #57, external
patch/fault/transient scope under #59, and operating resistance, parasitics,
leakage, temperature and physical current verification under #65. This draft
does not infer new fitted current limiting or omit any signed boundary flux.
