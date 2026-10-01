# Full assembled-harness energy with finite lead collars

Status: **conditional theorem and arithmetic implementation; no actual GH
harness, measurement or physical source class is admitted**. This is a
replacement route for the unverified solid-crimp-hub construction. It does
not infer internal contact dimensions or physical strand sharing from a
catalogue resistance. All hardware remains an unvalidated draft.

## Use one complete physical conductor

The unknown passive domain includes both mated headers/contacts, both crimps,
all strands and interstrand contacts, and the complete connecting wire. Its
two external interfaces are full cross-sections of the **single connected
header leads** at the PCB ends. No artificial cut inside a seven-strand
bundle is introduced into the scalar measurement model.

The local requirement is an upper R_test on **total passive input power/I^2**
at explicit excitation terminals. The entire measured I must cross both
collars with net currents +I and -I. Every other electrical port is absent or
insulated. The fixture, other header pins, other harness conductors, shields,
grounded instruments and PCB copper must not provide a parallel bypass.
Passive fixture losses may remain inside the measured power bound
conservatively. They must not be subtracted from an unrelated point-voltage
measurement. A 100-ohm harness shunted by a 1-milliohm fixture illustrates the
failure: its small total input resistance says nothing useful about the
harness normalized by total source current.

This is a prospective, independently testable **local assembly requirement**.
It is not the unresolved whole-instrument GH-current <=0.5 A result. Neither
the retained JST 50 mOhm/end catalogue figure nor the nominal Alpha DCR is a
certificate for this complete domain and these excitation terminals.

## Collar theorem

Each collar is a full physical conductor section D x [0,L], with convex D,
positive L, no sources, and insulated lateral boundary. The two collars have
disjoint interiors. Their section geometry, material and normal directions
are named explicitly. A **contained copper core is insufficient**: unmodeled
side metal or solder could inject current laterally and destroy the slice
conservation used below.

Let J be any finite-energy conserved current in the tested assembly, with
the required net I in each collar. Orient one collar toward its external end.
Write A=|D|, chi=z/L, mu=(I/A)e_z, and g=J_z-I/A. Slice conservation gives
integral_D g=0. For almost every z, solve the insulated-side Neumann problem

```
Delta_xy psi = chi' * g,   integral_D psi = 0.
K = (1-chi)*J + chi*mu + (grad_xy psi, 0).
```

Then div K=0, its side normal flux vanishes, K has exactly J's normal trace
at z=0, and its normal trace at z=L is uniform I/A. Endpoint tangential
components need not match: continuity of the full normal trace is the
H(div) gluing condition. The construction works with weak normal traces;
no unproved L2 bound on the terminal flux density is required. It controls
arbitrary finite-energy zero-net redistribution as well as the net current.

For homogeneous reference resistivity, mu is the cross-sectional orthogonal
projection of J onto the constant longitudinal mode. Thus

```
||(1-chi)J+chi*mu|| <= ||J||,
||grad_xy psi|| <= d/(pi*L) * ||J||,
E(K) <= (1+d/(pi*L))^2 * E(J),
```

where d is the diameter of D and the norms are volume norms. The convex
Neumann estimate is the same [Poincare result](https://arxiv.org/pdf/1110.2960v1)
already retained by `source-boundary-lifting.md`; it is not applied to the
disconnected seven-strand section or a convex hull containing air.

For a resistivity/geometry pullback metric between a and b times the
reference metric throughout the **complete** collar, multiply the energy
factor by beta=b/a. This permits finite material and geometry tolerances
when their map and complete metric bounds are actually proved. Merely
assigning beta does not certify an arbitrary manufactured lead.
The comparison must cover the **complete dissipation**, not just bulk
resistivity. In particular, a zero-thickness internal contact/Robin interface
may acquire extra surface energy under the transverse correction. A bulk
coefficient ratio does not bound that charge. The helper requires a complete
volumetric ohmic metric with no omitted internal interface energy. A finite
physical transition layer may be included in that metric; another interface
model needs a separately proved complete-energy comparison.

The implementation uses pi>3 and exact rational arithmetic:

```
gamma_uniform = beta * (1+d/(3*L))^2.
```

### Weighted reference profile

If a known positive transverse reference conductivity sigma_0(x,y) is
independent of z, use `mu_z=I*sigma_0/integral_D sigma_0`. Solve
`div_xy(sigma_0*grad_xy psi)=chi'*(J_z-mu_z)` and add
`sigma_0*grad_xy psi` to the transverse current. Weighted projection gives
the same contraction. A transverse conductivity contrast kappa gives
weighted Poincare constant at most sqrt(kappa)*d/pi. Therefore

```
gamma_weighted = beta * (1+sqrt(kappa)*d/(3*L))^2.
```

The output is the **conductivity-weighted** profile, not uniform. Its
complete profile reference is mandatory and the adjacent adapter must
match it. Axial material variation or a geometric map belongs in beta.
A square-root upper is formed rationally, followed by outward conversion
only for display. Unknown plating must not be declared homogeneous to get
a smaller multiplier.

## Whole-harness bound and once-only energy

Apply the collar transformations to the two disjoint regions of the same
tested current field. Outside the collars, keep that field unchanged:

```
E_harness_fixed_traces <= max(gamma_left,gamma_right) * R_test * I^2.
```

The factors are **not multiplied or added**. The original total energy
already bounds the sum of all internal contact, wire and collar energies.
The two hidden crimps may distribute strand currents differently and the
strands may touch: all such behavior is already inside the same conserved
test field. No arbitrary seven-component current vector is imposed on one
unknown connector independently of the other.

Add disjoint, matched toe/solder/foil-access adapter energies outside the
tested domain exactly once:

```
R_fixed_upper = max(gamma_left,gamma_right)*R_test
                + R_adapter_left + R_adapter_right.
```

An adapter needs its complete profile matching and actual physical support.
It cannot be counted again in the test domain. If regions overlap, simple
addition is invalid; reconstruct the field and charge cross energy.

`scripts/pcbgen/harness_collar_bound.py` implements these conditional
arithmetic bounds. It requires two distinct full-section collar identities,
the series-current/no-bypass premises, total-power measurement kind,
complete output-profile references and a once-only adapter ledger. These
declarations do not establish physical admission. The helper refuses point
Kelvin-voltage substitution, missing sections, possible lateral injections,
fixture-energy subtraction and duplicate region identities.

## Why a per-end catalogue scalar is insufficient

Consider one header connected to seven strand endpoints by resistors: one
branch is 0.03 ohm and the other six are M ohm. Short all strand endpoints
together with the measurement electrode. The measured equivalent resistance
is less than 0.03 ohm for every positive M. But a prescribed equal-strand
unit-current trial costs `(0.03+6*M)/49`, which is unbounded as M grows.
Any fixed nonzero weight on a poorly contacted strand has the same problem.

Finite solder and header-lead lifts cannot repair this disconnected
strand-mode gap. Either retain a complete physical multiport contact
construction, obtain a matching seven-strand operator bound, or place the
**entire two-ended cable** inside the scalar domain as done here. The latter
leaves only two connected full lead sections to transform.

## A local class can be nonempty without being accepted hardware

For a synthetic homogeneous-collar example, L>=0.6 mm and d<=0.18 mm give
gamma<=1.21. A complete-domain bound R_test<=0.08 ohm and two disjoint
0.001-ohm adapters yield R_fixed_upper<=0.0988 ohm. These are explicit finite
local conditions and an arithmetic example, **not selected JST dimensions
or a measured cable result**. They show how to retain positive local margin
before the joined-network calculation. The collar/material geometry and
the tested domain must still be realizable for the exact hardware.
This arithmetic example also has finite metric slack: allowing beta up to
1.01 gives `1.01*1.21*0.08+0.002=0.099768 ohm`, still below 0.1 ohm.

For an existing local whole-wire allowance R_allow, require and independently
qualify
`R_test <= (R_allow-R_adapter_left-R_adapter_right)/gamma_max`.
This is a local assembly acceptance condition with named measurement
terminals; it does not assume that common ground, GH sharing, rail drop or
total voltage pass. If even that independently measurable local condition
cannot be supported, this route remains unselected.

## Minimum evidence and physical test definition

1. Identify the exact header, housing, contact, wire, strand construction,
   both board endpoints and actual wire path/length. Preserve all fixed
   hardware positions. Define all boundaries of the one tested conductor.
2. Establish a full source-free external lead neck at each end: complete
   cross-section, insulated sides, positive length, convex reference section,
   full possible metal, material profile and finite geometry/metric bounds.
   Inspect or measure the outside lead locally; proprietary crimp interior
   reconstruction is unnecessary for this route. A solder fillet crossing
   that neck invalidates an insulated-side assertion.
3. Use an isolated assembled conductor fixture. Both mates/crimps and the
   actual wire are installed. No other pin, coupon plane or fixture lead
   may shunt the tested conductor. The entire excitation current crosses
   both declared collars. Define the two actual excitation terminals and
   an upper on their delivered DC power, including instrument uncertainty.
   Attach fixtures outside the insulated collar side surfaces; an attachment
   or solder fillet injecting current into a side invalidates the theorem.
   Retaining passive fixture power conservatively is permissible. A local
   point-to-point sense voltage with unknown excluded spreading is not the
   required total-power certificate.
4. Require the scalar bound over the declared normal/hot/cold, assembly and
   ageing class. A single fresh-room-temperature result is not the class.
   The test-to-operation transfer requires the same admitted linear passive
   parameter family over the actual normal currents and contact states.
   Low-current DCR does not by itself bound a nonlinear, temperature-changing,
   fretting or ageing contact at its operating current. Removing an external
   passive fixture can discard its positive energy, but does not relax the
   collar geometry, series-current or material/profile requirements.
   Keep the selected wire <=70 C ceiling and the existing lower-resistance
   obligations; infer no new ambient range from this theorem.
5. Bind known toe/solder/foil fields to the transformed full end profiles.
   Preserve compatible potential extensions on all possible actual metal.
   Record exact domain cuts so collars, wire tails and adapters are each
   charged once.

The measured-power condition is sufficient without requiring physical
equipotential cuts. A two-terminal linear passive input field with the
specified complete current path already supplies a finite-energy current
trial; the theorem changes its endpoint traces analytically.

### Finding a real full-section collar

The GH drawing's nominal 0.7 mm toe projection does not establish an
insulated lead collar. A solder fillet can couple the toe's bottom or sides
to the pad along that length. A real neck must be outside all such wetting,
with its full metal section and all possible side contacts checked. A neck
inside the housing is possible only with evidence of its actual geometry;
the external body prism cannot establish it.

A prospective source-owned alternative is an isolated GH AGND land joined
to the board's ground conductor by one dedicated PCB foil neck. Reserve the
complete collar segment against vias, branches, another foil connection,
parallel copper and solder wetting; a mask-covered segment can keep solder
outside. Its full foil cross-section, outer and inner cut faces, physical
etch/thickness class and insulated sides must be source-defined and checked.
The unknown tested domain then includes the pad, solder, both complete
connectors and wire. The entire tested current must pass through both necks;
coupon planes or remaining board copper may not bypass them.

All neck resistance and adapters remain paid once as actual access costs.
This would be a copper/source change requiring native regeneration and a
fit/electrical review; it is not current-board geometry or permission to cut
existing copper. It preserves panel hardware centres but supplies no free
common-ground or current-sharing credit. A full single-foil collar avoids
assuming an inaccessible solid crimp hub or an unmodeled internal Robin
interface. It is the next concrete geometry candidate for this theorem.

## Evidence currently available and missing

The retained GH WRLs are explicitly derived header **body prisms**;
`gh-contact-mapping.receipt.json` is a pin-number mapping aid. Neither is
internal contact CAD. The [official GH page](https://www.jst-mfg.com/product/index.php?series=105)
lists an SSHL-002T-P0.2 2D drawing and GH manuals. At review time their links
led to an email-delivery form requiring contact details; no form was
submitted and no supplier was contacted. The unavailable document identifiers
are `SSHL-002T-P0.2.pdf`, `CHM-1-2149.pdf` and `CHM-1-2111.pdf`.

[JST's general handling instructions](https://www.jst-mfg.com/product/pdf/eng/handling_e.pdf)
(physical indices 5–7) call for appropriate application tooling and
terminal-specific crimp-height control, and say bare copper wire requires
compatibility checking. This is relevant to the retained bare-copper Alpha
6821 choice. AWG and insulation-diameter agreement alone does not establish
that compatibility; the document does not prove the wire incompatible.

No inspected primary source defines the full-harness measurement terminals,
total-power upper, actual full lead-neck sections or a qualified assembled
temperature/ageing class. Those exact gaps remain. A catalogue maximum cannot
be rebound to this theorem by changing a label.

## Remaining whole-network proof

This route supplies a constructive **upper** for one complete harness with
fixed full traces. A lower potential witness still needs the actual bulk
wire/material envelope, the entire possible end metal, correct constant
end extensions, and the cut-current test EMF across all strands. Keep all
wire/lead regions in the same joined geometry and all source/observation
functionals compatible. No per-end or bulk term disappears because its
interior geometry is hidden inside a qualified energy upper.

Common ground <=0.5 mOhm, GH <=0.5 A, rail common <=1 mOhm, distribution
<=20 mV and total <=0.20 V remain separate unproved targets. Physical checks
remain NOT RUN. The theorem offers a smaller local evidence requirement;
it does not waive an electrical or mechanical design gate.
