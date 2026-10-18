# Stage35: shortening clears a height screen, but service is not established

**NO_ROBUST_SERVICE_SOLUTION_ESTABLISHED.** This bounded source study starts at
`9d9aa404a27dc7e5b8476e0d9f826fc44c517fbe`. PR #287 remains draft, stacked on
#286 at `b58068fbaeb65886958a67a4f4978613414e31c5`. All historical stage bytes and
canonical CAD/manufacturing outputs are preserved.

The owner approved the earlier R33 rear-face header study and its provisional
RV-ARCH/RV-ACCESS reservations. That is not adoption of hardware. Stage35's shorter
lengths, tracking former, revised removable guides, fastening and cover alternatives
are **new proposals**, not silently approved carrier/enclosure/reservation changes.

## The approximately 2.42 mm option is insufficient even in the inherited model

The inherited numerical model needs **2.423890 mm**, not exactly 2.42 mm, of shortening.
At length 130.58 mm its cover spare is 0.148055 mm, below the unchanged 0.15 mm K4.
The nominal 130 mm diagnostic has 0.438055 mm spare, with the same 0.5 mm placement
margin and inherited tolerance stack. This is a source calculation, not a selected
finished or raw cut length.

The generated [analysis](analysis.json) and [summary](summary.md) evaluate lengths
129, 130, 130.5, 130.58 and 133 mm. The 129–130.5 mm trial interval is a reviewable
height-screen subset, not a claimed feasible hardware interval. All sampled
single-end states fit the corresponding historical RG34 channel at the inherited
three whole-arch height corners. The new exact-circle analysis covers continuous
0–15 mm single-end travel, +/-0.5 mm length and both signs of the 1.282127 mm middle
board bow at fixed nominal XY. Its extrema are affine, so endpoint extrema bound
the interior. Every state retains R12 and its housing fan-in straight. Neither
analysis bounds actual service shape while a sleeve is removed.

## The datum allocation changes the necessary length interval

For planar exits separated by D, heights a and b, radius R, straight fan-in f,
and housing accounting h=14.6:

- `Z = (L - h - D + a + b + (4-pi)R)/2`.
- `Lmin = D + abs(a-b) + 2f + (pi-2)R + h`.
- A single-end withdrawal of t raises Z by t/2 and consumes t/2 of the withdrawn
  end's straight lead. Thus every t in [0,15] is covered by its endpoint extrema.
- The cap adds bundle radius, 0.3 play and 1.2 wall. The cover check additionally
  subtracts 0.5 margin, 0.1 fabrication, 0.1 mount float, 1.0 carrier-to-cover
  allowance and 0.15 K4. Finished design-length tolerance is +/-0.5 mm.

These formulae use exact circular arcs; the inherited polyline gives a top about
0.000215 mm higher. Historical bytes and historical numerical results are retained;
the exact-circle upper bound is not substituted into old artifacts.

Three distinct **necessary screens**, not three qualified tolerance specifications:

| J-SIG screen | Lower L (mm) | Upper L (mm) | Meaning |
|---|---:|---:|---|
| Inherited whole-arch height shifts | 126.437261 | 130.576540 | Height/straight screen; displaced housings not re-solved |
| Endpoint box, historical downward-only bow | 127.155134 | 128.576540 | Nonempty for this restricted arch family |
| Same endpoint box, signed bow | 128.437261 | 127.294413 | Empty for this restricted arch family |

The endpoint box is an explicit **sensitivity**, not an established tolerance:
each housing independently +/-1 mm along the arch and in z relative to the rear
carrier, with n=0. Its two necessary witnesses use D+2 and the greatest height
difference (short-cable/straight limit), and D-2 with both exits high (long-cable/
cover limit). Actual Stage34 wording does not resolve per-axis versus radial or
pairwise registration, datum correlation, or rotations. The box may overestimate
a pairwise radial allocation. The historical bow model is only toward the carrier;
physical bow sign is unestablished. The empty box interval therefore rejects that
family under that sensitivity, **not every possible shorter harness or guide**.
Routing registration transitions into the fixed guide requires additional geometry;
no S-bend length is silently credited. Full tolerance feasibility remains UNKNOWN.
J-PWR 149 mm falls within all three necessary screens, but shares the service gaps.

## Length, bends and slack remain distinct requirements

The old design lengths include two 7.3 mm mated-height accounting terms. They are
not raw wire cuts. Strip/insertion lengths, crimp take-up, conductor-specific fan-in
paths and process capability are unknown. +/-0.5 mm is a finished design-length
assumption, not measured raw-cut capability. Do not send 130 mm as a cut instruction.

At 130 mm the historical nominal remainder above minimum installed plus 15 mm
withdrawal is **7.345296 mm**, compared with 10.345296 at 133 mm (the inherited rule
requested 10 mm and rounded up). The 3 mm reduction is an explicit proposal to
change that rule. The former's 0.25 mm setting gap leaves 0.5 mm potentially mobile
slack; withdrawal additionally releases 15 mm above the fixed former regardless
of shortening. These are different allowances and cannot be spent twice.

R12 is unchanged. Required bundle-centreline radii under the inherited 10x-OD,
inner-surface convention are 11.75 mm J-SIG and 11.457107 mm J-PWR. Fan-in straights
remain 10.389297 / 6.905617 mm. The fan-in model assumes a favorable conductor
mapping; it is not an actual individual-conductor cut/dress design. Housing exit
straightness and assembled mapping need measurement. R17/15x with RG34 and the
historical 20x failure are preserved, not solved by selecting a smaller flex rule.

No wire is selected. Stage34's A01 conditional current budgets supersede the old
X1 mistake; no electrical budgets are revised here. Maker repeated-flex radius,
Thermax installed bend evidence, AWG28/30 JST contact rating, LM393B supply current,
upstream limiting and assembled derating remain unresolved. No new maker data or
physical facts were invented.

## A tracking former alone does not close guided service

The fixed-former service screen allows the released 15 mm plus the 0.5 mm residual
slack at an open-sleeve span. Its bounding volumes fail K4. This means the source
cannot certify excursion, not that every real cable must collide.

An unadopted alternative would couple the former to connector travel by `t/2`,
with 7.5 mm stroke and tracking/contact gap <=0.25 mm. It must own both R12 corners,
keep the lid/end walls closed, positively retain the unserviced end, and tolerate
both pull and re-mate directions without relying on wire stiffness or an operator
holding the arch. There is no designed slide/drive/lock/joint yet.

Even granting perfect tracking, a conservative full-open-sleeve span screen gives
**J-PWR local spare lower bound -0.009834 mm**, below K4 by 0.159834 mm at
A01-middle. The normal installed sleeve lower bound is 0.416060 mm there. These
include the conservative numerical sampling allowance; the historical samples
were -0.008601 and 0.422967 mm respectively. A telescoping/split guide that
keeps effective support during release is therefore a further proposal; its bore,
travel, latch access, transition radius and moving envelope must be explicitly
modeled before claiming service closure. The screen treats both potential open
spans together as a conservative superset, not an allowed both-ends procedure.
The new occupancy screen extends both unknown-depth and assumed-height obstacles
through the full envelope. The other three tracking spans also have unresolved
UNKNOWN_OCCUPANCY blockers, so a local known-board bound is not an overall pass. Friction from cable weight
alone is not a drag guarantee; bend reactions, abrasion and stiffness are unknown.

## Neighbours, core extraction and removal remain explicit gates

The full ledger evaluates all 1,028 inherited obstacle prisms against 13 retention
prisms without the historical proximity cull. Unknown-depth geometry is extended
through the sweep and assumed-height objects are labelled UNKNOWN_OCCUPANCY.
Missing foreign board outlines/planes/heights, wiring and rear-cover features
remain unknown, not free. Extended foreign columns overlapping the channels are
requirements to resolve, not proof those parts physically penetrate an A01 board.
Known board shielding may be evaluated in a later explicit geometry model.

The modeled core envelope includes the unchanged 40 mm extraction and K-PWR-first
sequence. The inherited RG34 known-part/core clearance is retained; no clear
connector/fastener/wire interaction outside those recorded solids is inferred.
The J-PWR channel corner still misses the A01-jack M4 tool-column K4 by 0.494368 mm
(spare -0.344368). Removing the guide first is still a proposal, not an evaluated
assembly procedure.

The vertical-removal ledger sweeps each retention prism until its bottom is above
z105+0.5. It preserves unknown-occupancy and tool-column failures. It is a necessary
screen only: it does not define side-opening lid trajectories, mutual guide-part
removal order, post fasteners/tools, lifting grip, attached harness movement or the
rear-cover aperture. No physical removal pass is claimed. A candidate sequence to
study is: cover off; disconnect K-PWR and withdraw core 40 mm into a supported rest;
positively restrain both harnesses; open lids/sleeves in a modeled order; disconnect
middle ends; remove J-SIG then J-PWR guide/post with specified tool corridors;
only then use jack-board M4 access. Temporary harness/rest support and every swept
part must be designed before this can replace the historical sequence.

Shortening does not reduce RG34 plan thickness: the precise RV-ARCH excess is
0.875 mm (historical rounded 0.9). RV-ACCESS occupation remains. Any enlargement,
post interface, or changed assembly sequence is an unadopted hardware proposal.
The post allowable remains 39.836642 N and fails 50 N; shortening does not move the
J-PWR farthest-load point. Root fixity, overhang, joints and guide-wall strength
are still unestablished. A bigger post cannot be adopted without its obstacle and
fastener envelope; no material stiffness or load rating is invented here.

## Deeper covers are height alternatives, not service solutions

With the old 133 mm J-SIG and inherited Stage34 assumptions, the height threshold
is **z106.211945**, a +1.211945 mm depth change. That is the smallest change for
that historical height equation only, with zero additional design reserve.

Under the signed endpoint-box screen, the minimum common height at its lower
length endpoint is **z105.571424** with L=128.437261 mm. Retaining 133 mm under that
same screen needs **z107.852794**. These are lower bounds for the stated arch
family, not proposed manufacturing dimensions; registration interpretation,
transitions and physical bow can change them. A positive interval and practical
rounding/reserve must be allocated before selecting a cover depth.

Every deeper alternative needs enclosure wall/aperture/fastener redesign,
clearance to internal cover ribs and wiring, a longer removal path and packaging
review. It changes the enclosure but does not by itself solve open sleeves,
unknown neighbours, M4 access, post strength, R17, wire flex or assembly support.
Preserve the z105 cover in canonical CAD. The next decision is the registration/
bow contract and service-guide concept, not an order for a deeper cover.

## Reproduction and remaining work

Handwritten inputs: this README, design-input.json and mock-up.md. Generated:
analysis.json and summary.md, from `stage35_cover_service.py`. Tests:
`test_stage35_cover_service.py`. Review bindings and actual command outcomes are
recorded separately after final review. All source checks differ from physical
verification; native KiCad, regeneration, ERC/DRC, fabrication, orders, energisation,
deployment and merge are NOT RUN / not authorized.

Next cloud-capable work: define a reviewable datum/rotation tolerance allocation;
design the tracking and telescoping guide plus its fasteners and tool corridors;
model staged lid/guide/harness removal against explicit foreign and enclosure
keep-outs. Use the [unpowered measurement checklist](mock-up.md) to supply the
missing physical geometry and wire behavior. No continuation beyond Stage35 is
performed in this task; parent review chooses the next scope.
