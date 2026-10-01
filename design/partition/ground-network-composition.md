# Ground network composition work plan

Status: **source incidence complete; joined electrical proof OPEN**. No native
board, physical interface or manufacturing class is selected by this plan.

## Exact nodes and physical wires

`ground-network-incidence.json` is generated from the partition, physical
package/source-pin report, complete loom and wire requirements. It contains
4921 distinct ground contacts and 389 physical wire edges: 380 GH returns and
nine independent main returns. Four GH edges are the JL/P utility returns.
Each wire's signed incidence is exactly -1 at its sending PCB contact and +1
at its receiving contact. There is no ideal K or ideal rest-network node.

The fitted source current-contact counts are JL 1070, JR 896, P 214, K 1903
and EL 60. O1–O5 have no source component AGND contacts, but retain all actual
ground interconnects and their finite copper. Zero source component contacts
does not eliminate their passive ground paths or prove a parasitic-current
bound. Exact current native bindings cover JL 1177, JR 1005 and K 2288 total
ground contacts, including their headers and main lands. Missing P/EL/adapter
native operators remain explicit.

## Balancing contacts are not implicit physical source placements

The nominal board matrices use a named main contact as a mathematical current
reference. For example, a K unit probe injects at one named contact and removes
the same current at TP990008. Rebasing to another main changes that explicit
probe. A potential gauge, by itself, carries no source or sink current.

The accepted source contract deliberately leaves CN301/XB301 abstract and
non-energizable. This work adds no bridge across that boundary. A joined
source scenario must name every actual modeled source/return functional and
its signed current. It must not silently place an ideal source at a K gauge.
Conditional load-side comparisons can enumerate named existing K balancing
contacts, but must retain that scope separately from physical source-inlet
realization under #57.

## Finite board/wire assembly

For each board b, retain a finite conductor operator with its own named
reference and complete physical contact functions. Let E map external load
and source amplitudes x to board contacts, and D be the explicit wire
incidence. The complete contact-current vector is

```
q = E*x + D*i.
```

Every board must have zero sum of q, and the full external source vector must
balance globally. Do not assign each board its own independent 4.6 A budget;
the normal signed-current requirement applies once to the complete scenario.

The budgeted coordinates x are actual load-to-balancing-source current
amplitudes. Each column of E has a named positive load contact and named
negative source contact (or an explicitly proved distributed balancing
profile), with exact zero column sum. The original return envelope is
sum(abs(x)) <= 4.6 A for the selected normal class. For a simple +I/-I column,
its coefficient norm is |I| and the full-contact norm is 2|I|; in general
||E*x||1 <= 2*||x||1 for these unit endpoint columns. Thus 4.6 A of one-signed
returns balanced at a source permits 9.2 A of external contact L1. This does
not allocate 4.6 A separately to every board, wire or contact. D*i consists
of internal physical wire endpoint currents and is solved by the joined
network; it is not silently charged as a second external load budget.

For real spatial contact flux, retain each signed finite profile plus any
zero-net redistribution. A net terminal current does not bound the integral
of absolute flux. Reactive, leakage, circulating and external patch currents
must have explicit additional coefficient/total-variation constraints or be
included within a justified common scenario class. No such total-terminal
constitutive class has yet been adopted. Historical numerical screens use
their original load-to-reference coefficient norm and are not reinterpreted
as a 4.6 A bound on the fully balanced contact vector.
All K/P/EL own loads, capacitor/leakage currents and permitted external patch
currents must be accounted for. Planning quiescent values are not maxima.

The upper witness is the sum of all actual PCB current-field energies and
complete wire/termination energies. Full normal traces must match at each
physical joint. A compatible lower witness uses one continuous potential
across every possible contact-metal support. Matching only patch averages or
subtracting a private diagonal from an unrelated interval is insufficient.
Any internal current minimization needs a true minimum: positive definiteness
or a rigorously handled semidefinite range, without projecting an arbitrary
lower matrix to PSD. Outward numerical allowances remain required.

For each candidate GH, the observation is between its exact two endpoints,
including the remote P endpoint of each utility return. Its denominator gets
the source wire minimum and zero added candidate PCB/contact credit. All
alternative accesses and complete wire terms remain charged once. This
current check does not replace the independent common J/P plus K 0.5 mOhm
ceiling, positive allocations or the rail/return voltage limits.

## Next bounded prerequisites and calculations

1. Retain the completed source-incidence and native-binding review, including all
   380 GH edges, all nine main wires and the full own-load map.
2. Build a **disposable P ground-conductor prerequisite** at all 418 existing
   source footprint origins and fixed four-layer, 1.6 mm construction.
   The original P notch intersects RV601's retained mounting pad/drill; the
   explicit unselected local edge-tab and per-terminal reservation revision
   is documented in `control-ground-feasibility/README.md`. No hardware or
   clearance change is allowed by that revision.
   P contains 214 fitted AGND contacts, 127 GH returns and three AGND mains.
   All six power lands, foreign pads/drills, keepouts, source unit metadata and
   exact ownership remain. Choose a source-defined ground stack and finite
   legal transfers, then require native rules/parity zero and exact ground
   connectivity before model entry. This is prerequisite work inside #38,
   not a circular dependency on completed #39 or permission to publish P.
3. Obtain fresh JL/JR ground witnesses on the parallel-feed geometry. Their
   added holes/fills invalidate historical J operators. The completed K
   coupling matrix is a useful initial finite-profile diagnostic, but does
   not include the other 170 K GH contacts or its 1903 own-load functions.
4. Form explicitly named balanced scenarios and complete board operators for
   the selected composition. P/EL/adapter operators cannot default to zero.
   An alternative proof that bounds or removes a passive subnetwork needs its
   actual topology and a valid self-energy/maximum-principle or elimination
   theorem; mutual transfer is not Rayleigh monotone. Such a theorem must also
   cover every omitted load injection and actual terminal trace class.
5. Select and compute compatible finite lead/solder/wire, material and
   geometry classes. The current numerical patches and scalar contact
   resistance facts alone do not establish them. Quantify numerical error
   and geometry refinement, then test the separate common/private/current
   and complete 20 mV / 0.20 V budgets without changing their limits.

The P prerequisite is bounded ground feasibility only. Actual #39/#43 routing
and the later EL/adapter layouts must re-extract their final conductors and
verify the selected allocations. Physical qualification remains open under
#55/#57/#59/#64/#65; it does not waive a deterministic failed design limit.

## Implemented algebra and remaining operator inputs

`network_port_composition.py` constructs an exact integer board-incidence
matrix, a spanning-tree right inverse and the complete physical-wire cycle
basis. The actual ten-board source graph has 389 wires and 380 independent
cycles; removing any one of the four JL/P utility candidates leaves 379.
The particular wire-current map balances each named board source. Cycle
currents are then minimized over the sum of every supplied board energy and
every paid whole-wire energy. The internal block must be positive definite;
an indefinite stationary maximum is rejected. This is currently a floating
diagnostic of an exact-arithmetic identity, not an outward certificate.

The helper requires an explicit operator for every declared board and a row
for every declared contact, including own loads. Its fixtures compare a
three-board J/K/P network against a directly assembled resistor Laplacian,
with a P own-load injection and a true +J-GH/−P-GH utility observation. There
is no implicit K gauge current or ideal rest connection. Constituent energy
ordering survives the constrained minimum under the stated trace premises;
individual wire currents are not ordered by that theorem.

The complete required contact inventories are:

| Board | Own-load contacts | GH contacts | Main contacts | Total |
| --- | ---: | ---: | ---: | ---: |
| JL | 1070 | 104 | 3 | 1177 |
| JR | 896 | 106 | 3 | 1005 |
| P | 214 | 127 | 3 | 344 |
| K | 1903 | 376 | 9 | 2288 |
| EL | 60 | 12 | 0 | 72 |
| Each O1–O5 | 0 | 7 | 0 | 7 |

A full joined calculation cannot substitute the existing 214-function K
coupling matrix for the missing K contact functions. Nor can a fixed-patch
lower matrix be minimized over arbitrary physical terminal distributions:
the lower bound must cover every permitted distribution, and constructive
upper fields must have compatible full traces at all joints. The physical
contact/material/current-class work and outward numerical composition remain
computational gates for issue 38, separately from later physical qualification.

EL and O1–O5 use two physical copper layers and have no main load-wire land.
The present conductor extraction assumes four foil names and a B-layer index
of three; the present caller chooses a main land as its reference. Therefore
those boards cannot enter it unchanged. A supported extension must retain
only the actual enabled native foils, use their real positive stack bands,
exercise a two-foil sheet/barrel fixture, and name an actual GH balancing
contact. It must not add fictitious inner foil/annuli or an ideal main source.
The smallest such source/model extension and the missing K contact basis
remain a separate reviewed step after the current P diagnostic.
