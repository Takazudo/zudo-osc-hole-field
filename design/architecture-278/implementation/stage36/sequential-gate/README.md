# Sequential J-PWR-local support/access gate

**UNKNOWN — NOT SOURCE-FEASIBLE; hard stop at the first endpoint.** This is a
bounded necessary-condition screen, not Stage37, a new mechanism, or qualification.
C36 remains rejected. Baseline4a966816; vendor manuals remain outside git. Only
J-PWR local was assessed: the condition for extending to other ends was not met.

One arrangement is considered: the operator releases the latch and grips the
whole wire row to withdraw this one connector; a separately supported former
retains both R12 bends; the opposite sleeve/end stays supported. No structural
reaction is assigned to housings, crimps or presumed grip friction. The former's
carrier joint, guidance and bend capture are **undefined**, so this arrangement
cannot be declared realizable. No second mechanism is proposed.

## Coordinates, continuous motion and slack

Local origin is the recorded wire exit(226,173,43.9); u=+x along pin pitch,
v=+y normal to the wire row's broad faces, w=+z along withdrawal. This differs
from the tilted arch-plane axes. Both +v and -v grip faces need access. The
manual's illustrated 'vertical' grip is interpreted in this connector frame,
not as global z. Latch-side sign/position must be checked on the actual top-entry
part; the generic side view is not a dimensioned latch datum.

For axial travel t in[0,15], constant length149 and R12 give:

- arch top Z(t)=88.946768+t/2; former rise0..7.5;
- local straight33.046768−t/2, opposite straight19.646768+t/2;
- required source fan-in6.905617 remains within both nominal straight lengths;
- a fixed former releases t additional length, up to15mm: operator-held arch is
  not a substitute for support;
- with former rise y(t), residual delta = delta_set + 2max(0,t/2−y(t)). Setting
  error and tracking lag consume the **same** slack budget. The inherited0.5mm
  setting residual plus0.25mm tracking lag would yield1mm, not0.5mm. Raising the
  former above t/2 instead risks tension; no force-based correction is credited.

These equations use analytic arc length, not the inherited polyline approximation
(which raises its top by0.000215mm). They cover all intermediate t and reverse motion. The open selected
leg's upper guide entry stays z74.805617. Its exposed chord shortens as t rises;
for constant residual, its t=0 prolate reach volume contains those for later t
(triangle inequality on the moving lower focus). Thus the t=0 screen is a
continuous outer bound for that leg. This is not proof that the actual wire fills
that bound, nor proof that an unsupported bend stays R12. Opposite support and
moving-former geometry are hard-stop prerequisites, not assumed passed.

At residual0.5mm the independently recomputed Stage35 lower clearance bound is
−0.009834mm against board:A01-middle:0 versus K4=0.15: deficit0.159834mm.
A diagnostic bisection puts the maximum residual accepted by **this one board
screen and inherited stack** near0.434179mm. This is not an adopted tighter
setting, global feasible interval or measured capability. Rotations, actual wire,
new support parts and every other obstacle still require qualification. Losing
this conservative screen does not prove all possible sequential arrangements
collide; it means this arrangement has no supported clearance proof.

## Explicit handoff and opening gate

| Phase | Required support and access | Current result |
|---|---|---|
| Cover removed; before opening local sleeve | Both bends positively retained by separately supported former, opposite sleeve closed; establish replacement confinement before releasing local restraint | Carrier reaction/bend capture and handoff geometry absent: STOP |
| Open selected sleeve at t=0 | Sleeve split/hinge/removal swept shape and latch approach in(u,v,w); no wire escape/pinch | Only closed outer prism exists; opening axis, joint and sweep unknown |
| Unlock and grip | Fully depress latch protrusion; access both broad faces of full row, no edge-wire pull or lateral gathering | Exact latch datum/stroke and actual grip envelope unknown |
| t=0..15 and reverse | Former follows required rise without unsupported bends; residual retained within established bound; opposite sleeve remains supported | Even ideal inherited0.5mm residual fails stated clearance screen; no mechanism/stiffness assumed |
| Return to t=0 | Verify mate, restore sleeve and its retention before releasing temporary support | No defined support overlap/closure path |

Closed sleeve corners in local coordinates are recorded in gate.json. Treating
its outer prism as a solid shows unresolved RG34 channel contacts; these are
reservation/interface conflicts, not proof of physical interpenetration. The
recorded shape is not a split shell or a hinge drawing. No collision-free sleeve
opening distance can be certified from it.

## Maximum-envelope outputs, not invented hand/tool sizes

A declared reference family preserves the four-wire pitch-row width4.75mm and
1mm depth from pitch1.25 and source maximum wire OD1.0. It is **not** a measurement
of the actual fanned bundle, finger or jaw. Probes begin above the6.905617mm
fan-in and sweep all15mm. All1039 non-own reservations/parts are included, with
unknown heights occupied and cross-carrier ±1mm XYZ converted to sqrt(3)mm.
No proposed neighbor height cap is accepted.

For zero axial grip height and zero-angle axial motion, the greatest screened
outward depths from the reference faces are approximately **+v5.405mm** and
**−v1.848mm**, limited respectively by unknown SW1301 occupancy and the middle
board. They are optimistic upper limits for this reference family, not a usable
paired grip. Finite grip height/width, rotation and approach can only consume
more space. Nominal axial budget is **H+q≤9mm**, where q≥0 is grip offset above
fan-in; this excludes tolerance and approach, and is not simultaneous permission
to use all independent maxima.

The retained planning angle is15°, not the manual's20°. A translation-only
outer bound for the full15° cone expands lateral reach by up to15tan15°=4.019mm;
its audit is also recorded and does not establish clearance. Rotation of an
actual grip would add further sweep. No narrower operating angle is selected to
make the result pass. The axial screen alone is sufficient to expose missing inputs.

For latch tools and sleeve opening, the maximum **certifiable** envelope/travel
is **unknown**, not zero and not free space: the latch datum/stroke and sleeve
kinematics needed to define a maximum are absent. A numerical maximum here would
invent the very geometry this gate forbids.

## Smallest next inputs and decision

1. On an existing unpowered exact4-way housing/header coupon, record the latch
   tip in(u,v,w), depression stroke and approach direction; measure the occupied
   envelope of the actual full-row grip from both broad faces through withdrawal
   and remating (width, two depths, axial height, angular deviation). Include
   instrument uncertainty. Compare first against the optimistic limits above;
   exceeding one rejects this reference family, fitting them is not a pass.
2. Supply a dimensioned sleeve split/opening and independently supported former
   interface, including support overlap before opening and after closure. This
   is a missing design input; measurements cannot manufacture a nonexistent joint.
   Do not test a free arch or assume grip friction supplies that reaction.
3. Only after that interface exists, measure total setting+tracking residual and
   both bend retention throughout forward/reverse travel. The0.434179mm diagnostic
   is a necessary screening target only; do not tighten tolerances by declaration.

Parent decision: hold here pending the small latch/grip measurement and an
explicit support-handoff interface. Other endpoints, guide removal and jack-board
access were not advanced. Existing lengths133/149,z105 cover,R12,0.5margin,K4=0.15,
K-PWR-first/core40 and unknown-neighbor policy remain. Original J-SIG cover
conflict is not solved by this local service gate. Wire selection, flex radius,
strength and physical/native checks remain unresolved/NOT RUN.

Reproduce: `python3 design/architecture-278/implementation/stage36/sequential-gate/gate.py --check`.
See gate.json, focused test_gate.py and review/check receipt. No restricted manual
text/images are reproduced; handling evidence is in ../GH-MANUAL-INTAKE.md.
