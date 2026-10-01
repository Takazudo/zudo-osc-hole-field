# Prospective finite GH termination cell

Status: **UNSELECTED conditional reference construction**. The local analytic
upper is **45.193238 mOhm per end**, below the existing 50 mOhm/end allowance
with **4.806762 mOhm** arithmetic headroom. This is a calculation over explicit
prospective geometry/material/interface requirements. It is not a JST
performance claim, actual internal-metal containment, adopted source class,
or issue-38 electrical acceptance. Exact-MPN and process qualification remain
**NOT RUN #65**.

The companion JSON is the source. Run
`python3 -m scripts.pcbgen.connector_trial_cell` for the exact rational receipt.
No native or full-board solve is involved. The current/potential fields apply
to the whole declared cell, not just a resistance pasted onto a pad average.

## Evidence and the strongest unresolved premise

The retained [JST eGH drawing](https://www.jst-mfg.com/product/pdf/eng/eGH.pdf)
was inspected visually on physical PDF indices 1 and 2, printed pages 2 and
3. The 0.55 mm label is on the contact outline, not a guaranteed solid metal
thickness. The 7.3 mm mated height is a reference dimension. The 1.25 mm
pitch, 4.25 mm header depth, 0.7 mm toe projection and 0.15 mm toe height
provide only gross envelope screens. They do not establish the proposed
internal spine, crimp slab or microscopic mating patches. Exact header and
contact identities and inspected source hashes are in the JSON.

The critical unverified premise is a **continuous 0.46..0.48 mm square,
0.10..0.14 mm thick conducting crimp redistribution slab**. A convex hull of
separated strands or a hollow stamped contact does not satisfy it. This
construction proves that a finite reference volume can fit the published
external scale and meet the end-energy allowance; it does not prove that the
interior of SSHL-002T-P0.2 contains that volume. It grants no permission to
fill a crimp with solder. Until its real containment or a replacement
constructive crimp geometry is established, the physical class stays
unselected. A successful gross-envelope check is not an interior fit check.

## Connected geometry and exact traces

Coordinates are local to one pin; z points away from the PCB. An eventual
native binding must map this frame to each actual pad/UUID/rotation and F/B
normal. It must not reuse an F-side z sign for a B-side part.

Let a be the toe width (0.15..0.16 mm), b the initial solder-patch length
(0.15..0.16 mm), h the toe-metal thickness (0.075..0.08 mm), and s the solder
height (0.025..0.05 mm). This finite current patch lies within the separately
required 0.18 x 0.25 mm actual solder support. Neither implies complete
physical-pad wetting or a uniform operating current.

1. The solder slab occupies x in [-a/2,a/2], y in [0,b], z in [0,s]. Its
   uniform unit-current trace matches the foil field at z=0 and the first
   copper corner at z=s. Both finite areal interfaces are charged.
2. The first corner occupies the same x/y rectangle, z in [s,s+h]. In
   translated coordinates its field is
   `J=(0,I*y/(a*b*h),I*(1-z/h)/(a*b))`. Divergence is zero, the bottom
   receives I/(a*b), y=b emits I/(a*h), and every other face has zero normal
   flux. Its exact energy is `rho*I^2*(h/(3*a*b)+b/(3*a*h))`.
3. A horizontal prism continues from y=b to y=0.7, with section a x h.
   The second corner occupies y in [0.7,0.7+h] and z in [s,s+h]. A rotated
   and reversed copy of the same corner field turns the current upward.
   Thus the second corner extends **inside** the body beyond the 0.7 mm
   toe projection. Both corners share the same height interval; they are
   not stacked as two toe heights.
4. A rectangular taper starts at z=s+h, centre y=0.7+h/2, section a x h.
   It ends with section body-width x body-depth and centre
   y=0.7+body-depth/2. More generally its start centre is
   `toe_projection+h/2` and its end centre is `body_front_y+body-depth/2`.
   The calculator derives the displacement from both endpoints. Moving the
   body front therefore pays a real sheared transition; it cannot leave an
   uncharged gap before the header spine. For the current coincident front
   datums, the displacement is half the difference of the section depths.
5. The header spine is a sheared constant-section prism. Its centre moves
   from that taper endpoint to y=1.5 over its own positive length. A taper
   contracts to the finite mating patch, and a second taper expands to the
   receiver spine. The two microscopic patch faces have identical support
   and normal current. The local areal interface law is charged once.
6. The receiver spine expands to the full square crimp hub at centre y=1.5.
   The hub transfers uniform input to seven disjoint finite 0.038..0.042 mm
   square crimp patches at the exact seven coordinates in the JSON. Their
   currents are alpha_j*I, where sum(alpha_j)=1; they need not be equal.
7. A finite local interface joins each crimp patch to its own strand tip.
   Each tip is a positive-length convex polygon prism inside a contained
   copper core. It transfers the patch profile to a uniform profile over
   that polygon, carrying exactly the same alpha_j*I at both ends.
   Seven disjoint tails continue those exact polygon traces to z=7.5 mm.

All adjoining normals are opposite and pointwise profiles agree. The side
normal current vanishes on every artificial contained-volume boundary, so
zero extension into additional allowed metal is divergence-free. Tangential
current discontinuities at internal faces are allowed for an H(div) trial.
The real current need not equal the trial current.

For a straight affine rectangular taper use normalized section coordinates
xi,eta in [-1/2,1/2], with `x=cx(z)+a(z)*xi`, `y=cy(z)+b(z)*eta`. The exact
Piola field is

```
J = I/(a*b) * (cx' + a'*xi, cy' + b'*eta, 1).
```

The cross-section average squared transverse factor is
`cx'^2+cy'^2+(a'^2+b'^2)/12`. Exact rational subinterval minima bound the
remaining integral of 1/(a*b); no logarithm rounding is hidden in the bound.
End normal profiles are uniform and all side normals vanish even for a
sheared or contracting section.

## Redistribution and interface energy

For a real convex slab D x [0,H], decompose the patch profile into its uniform
mean I/|D| and zero-mean g. The Neumann correction used by the existing
convex-source work gives

```
E <= rho_max * [H*I^2/|D|
        + (H/3 + diameter(D)^2/(9*H))*||g||_2^2].
```

The mean and correction are orthogonal in the unweighted volume integral:
the correction's vertical cross-section integral vanishes at every depth.
Applying rho_max to their combined unweighted energy is valid even when the
actual resistivity is not uniform. Thus no cross term is silently omitted.
For disjoint crimp patches of areas S_j and currents alpha_j*I,
`||g||_2^2/I^2 = sum(alpha_j^2/S_j)-1/|D|`. The largest permitted weighted
profile is used, not an equal-sharing assumption.

A finite interface patch with local areal resistance beta has energy
`integral beta*q^2 dA`. A uniform trial across area S carrying alpha*I costs
at most `beta_max*alpha^2*I^2/S`. The mating patch is 0.055..0.065 by
0.018..0.022 mm, not a uniformly conducting full connector face. The seven
crimp patches are similarly explicit. The beta intervals are prospective
requirements; a 50 mOhm catalogue scalar does not establish them.

The fifteen volume/interface entries in the calculator occupy disjoint
interiors and exhaust this constructed cell. Energies add across these
regions. The hub and tip entries already include their internal mean and
redistribution energies. Those entries may not be dropped or counted again
as a separate unmodeled termination allowance.

## Finite potential extension

Use one constant trial value throughout the complete possible connector
metal envelope, the full possible PCB wetting region, all seven actual
strand sections (including metal outside the inscribed current polygons),
and the outgoing collar. Every internal potential trace matches and every
interface jump is zero. This is an admissible restriction of the lower
potential trial, **not** a claim that the actual connector or cut is an ideal
equipotential. The same value must be imposed on the matching PCB trial and
on the incoming boundary of the separately modeled bulk-wire potential.

The checker requires the maximum metal box to contain every reference solid
and the full permitted outgoing strand metal, including the annuli outside
the current polygons. Affine taper and sheared-prism extrema follow from
their connected endpoints. The separate maximum-wetting rectangle is centred
on the native pad at z=0. The required minimum solder support is centred in
x and starts at y=0, like the current patch; that entire support must fit
inside maximum wetting. Maximum wetting is a conservative potential-support
restriction, not an assertion that all of the native pad is physically wet.
For the current source, required metal spans x=−0.24..0.24,
y=0..1.74 and z=0..7.5 mm. The larger declared metal/wetting envelopes remain
prospective containment requirements, not exact-MPN evidence.

## Bulk wire: rejected independent box and a nonempty correlated class

The first unselected box allowed core radius 0.077 mm with copper
rho=2.3e-5 ohm mm. Even seven complete, straight circular strands then have

```
R_per_m >= 1000*rho/(22*r^2) = 11500/65219
        > 0.17632898 ohm/m > 0.17 ohm/m,
```

using pi<22/7. Inscribed-polygon refinement cannot make that entire box
meet the original wire requirement. This is a counterexample to that
**newly proposed independent parameter box**, not an Alpha Wire failure.

The retained Alpha 6821 construction page specifies 26 (7/34) AWG bare copper
and a nominal 0.019 inch overall conductor diameter. Its properties page
labels 38 ohm/1000 ft at 20 C **nominal, for engineering purposes only**.
Neither supplies a minimum strand radius or a guaranteed hot DCR. The
original project wire ceiling remains 70 C; no new minimum ambient is
inferred. The NBS reference formula in `ground-material-evidence.json`
supplies the explicit 70 C reference rho, not an Alpha guarantee.

The proposed correlated class instead retains positive individual geometry
and material ranges, and constructs parameter-dependent trial currents:

- Each actual strand contains its radius-r_j core and lies within a
  radius-1.01*r_j envelope. The latter admits finite noncircular shape
  tolerance and bounds **all** physical metal, not only the trial polygon.
- Each strand has its own positive resistivity lower/upper bounds. Its
  scaled contained polygon has area A_j. The current trial includes actual
  arclength, curvature and frame-spin bounds through
  `M_current=1.025*(1+0.8^2*0.079^2/(1-0.1))`, approximately 1.029549.
- Put `R_j=rho_upper_j*M_current/A_j`, in ohm/mm, and
  `alpha_j=(1/R_j)/sum(1/R_j)`. Then the explicit conserved bulk trial has
  resistance upper `1000/sum(1/R_j)` ohm/m. Carry these same alpha_j through
  the crimp patches, tips and tails. No uniform physical strand sharing is
  inferred.
- A continuous potential depending on bundle-axis arclength covers all
  allowed metal, including touching strands and the unmodeled polygon
  annuli. The maximum axis-section factor is 1.025 and the maximum
  curvature-times-metal-radius is 0.05, giving
  `M_potential=1.025/(1-0.05)`. Thus
  `G_upper=M_potential*sum((22/7)*(1.01*r_j)^2/rho_lower_j)` and the
  wire resistance lower is `1000/G_upper` ohm/m. This lower follows from
  Cauchy and conservation for arbitrary physical cut flux, not uniform
  physical injection.
- Admit only geometric/material parameters whose computed upper is <=0.17
  and lower is >=0.10 ohm/m, and whose max(R_j)/min(R_j)<=1.2. These are
  explicit sufficient local conditions for the pre-existing wire contract,
  distinct from the unresolved whole-instrument GH current target.

The finite class is nonempty. A reference with r_j=0.078 mm,
rho_lower_j=1.6e-5 and rho_upper_j equal to the NBS 70 C reference yields
**0.164345 ohm/m upper and 0.108609 ohm/m lower**, with both geometric metric
allowances included. Focused tests perturb each strand radius and material
bound independently and retain strict margin. The reference is a constructed
class member, not a guaranteed Alpha part. Actual geometry/material/thermal
compliance remains NOT RUN.

The 1.2 strand-energy ratio gives alpha_j in
`[1/(1+6*1.2),1.2/(1.2+6)]`. Maximizing sum(alpha_j^2) over this box and
sum(alpha_j)=1 gives the conservative rational bound **736/5043**. The
45.193238 mOhm end result includes that weighted worst case, the scaled tip
areas, all microcontact costs and tails. It does not keep the rejected
independent-box bulk upper as an acceptance result.

## Wire length and once-only boundaries

The per-end cell starts at the foil external face and ends at the complete
seven-strand plane z=7.5 mm in this local frame. It includes each crimp
interface, strand tip and the tail up to that plane. The separate bulk wire
starts at that plane and ends at the other termination's corresponding
plane. The body before the tail reaches 4.87..5.57 mm; the resulting tails
are 1.93..2.63 mm. Tip and tail lengths are correlated through the same
actual z coordinates, not separately credited favorable extremes.

When composing actual source wire geometry, retain the two crimp-interface
planes, both 7.5 mm cuts, and the intervening path. Charge every physical
strand segment exactly once. Do not charge full source cut length as bulk
and add the same tip/tail volumes again. Conversely, a constant cell potential
gives zero lower-energy credit to its internal wire pieces: one cannot
apply a full-cut-length bulk minimum after removing those pieces from the
varying-potential region. Recovering their lower credit needs a compatible
potential extension, or conservatively use only the proven bulk length.
No shorter-wire/current-sharing credit is selected by this prototype.

## Checks and claim boundary

The focused regressions check exact corner divergence, full-face traces and
energy; taper side tangency and conserved traces; rational inverse-area
enclosure; convex patch containment and strand nonoverlap; weighted
redistribution; interface budget failure; the independent-box circular
counterexample; a nonempty correlated bulk family with independent strand
perturbations; and refusal of a missing solid hub or zero-width interval.

Native footprint binding, actual JST interior containment, physical solder
and microcontact realization, the permitted installed thermal class, the
joined PCB/wire operator and all common/current/rail/drop targets remain
open. A lower/upper source class can be selected as a conditional project
requirement without pretending physical qualification, but it must still
describe the exact intended part and complete realizable geometry. This
prototype is ready for that source-geometry review; it does not perform the
selection itself.
