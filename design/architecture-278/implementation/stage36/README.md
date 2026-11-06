# Stage36 — C36 supported cassette interface study

**FAILED_INTERFACE_CONCEPT_NOT_SOURCE_FEASIBLE. Stop for parent review.**
Baseline is Stage35 `8fd10c4a4841daf4d8e1e92346ce7d7282227764`. This is one
bounded source study, not a new qualified design. Existing cover depth 105 mm,
J-SIG/J-PWR design lengths 133/149 mm, R12, 15 mm withdrawal, K-PWR-first and
40 mm core extraction, 0.5 mm clearance and K4=0.15 mm are retained. Stage35's
one-end-withdrawal length/cover sweep is not repeated. No canonical output or
historical stage is edited. Earlier owner-approved rear-face *study* is distinct
from these new, unadopted roots, cassette, registration and cover-aperture proposals.

## One concept and its sequence

C36 holds both arches, all sleeves and four positive housing keepers together on
one removable roof. Ideal simultaneous +z translation preserves every cable
segment length, bend and straight exit: the withdrawn end never loses its sleeve.
This is a kinematic identity, **not evidence that a physical keeper can do it**.
Wire selection, repeated-flex radius, cut/strip length and current/thermal
qualification remain unresolved. The design length is not a fabrication cut length.

1. Unpowered: remove the cover, disconnect K-PWR first, support and extract core
   through its existing 40 mm reservation. Permanent roots and cassette must clear
   that path; the audit retains the complete core extrusion even at this step.
2. Replace short M3 screws one at a time with temporary service studs. The other
   screw holds the cassette; stud insertion/removal uses a full +75 mm axial sweep.
   Roof needs a separate grip/support and all four GH latches must be released.
   Neither grip nor latch geometry is established, so this is a gate, not an
   executable instruction for hardware.
3. With all keepers and sleeves still retained, lift cassette and all four housings
   +15 mm. The requested +75 mm total sweep would clear the opening plane, but
   is **not achievable**: the closed D4.4 bushing reaches the D6 stud hex at
   +32 mm and cannot pass. No alternative disassembly sequence is adopted. No single-end withdrawal is credited.
4. Reverse motion is only conditional within the unobstructed axial range. Rigid four-end remating needs an established
   capture window and signed-bow/registration compatibility; none is established.
   Remove studs one at a time, reinstall short screws, then core/K-PWR and cover.

## Explicit new interfaces and costs

- **Datum/registration (M35-01/02):** proposed positive 3-2-1 rear-carrier seating,
  A=upper crossmember top z62; panel-fixed B/C locating faces. Each endpoint gets
  independent ±1 mm on each axis and ±0.5° each-axis rotation about its exit.
  Cover translation is separately ±1 mm. No bolt friction or favorable correlation
  is credited. Signed middle-board bow is ±0.0075×diagonal = ±1.282127 mm; local
  slope must separately meet the angular obligation. Board bow is not measured.
- **Neighbors (M35-06):** authoritative placement/board outlines remain. Every
  unknown-depth or assumed-height obstacle is occupied through z350. JSON audit
  lists affected owner/ref, polygon and sufficient maximum-z obligation, retaining
  source proxy height for comparison. These caps are **not applied**. A cap below
  a source lower surface is infeasible for that footprint and needs repartition,
  not acceptance by fiat. No panel component moves or board reshaping are adopted.
- **Cover (M35-07):** new opening x199..313,y142..184, no ribs/fasteners beneath
  z105 within it, roof z98..100. Nominal roof gap 5 mm is not a robust cover pass.
  The opening/rib/fastener proposal has no authoritative lid drawing. Perimeter
  stiffness, fastening, grip and toleranced opening clearance remain gates.
- **Roots/tools (M35-08):** two integral 6×6 bosses at (265,169),(305,169),
  z51..62; integral 6 mm posts z62..90. The existing crossmember is
  x237..318,y170..174,z51..62: each boss extends 4 mm forward and overlaps 2 mm
  in y. This requires a replacement crossmember/root interface, not an invisible
  addition to canonical CAD. Proposed M3 top threads z84..90, pilot 2.5 mm give
  nominal post edge ligament 1.75 mm; no material/strength acceptance follows.
  M3×16 screw under a 1 mm washer at z101 traverses the 10 mm bushing and enters
  5 mm into the post. Bushing OD6/bore4.4,z90..100 seats on the post top.
  Temporary studs have M3 thread z84..90, D4 shaft z90..132 and D6 hex to z136;
  D6 axial tool columns extend to z205. No MPN, torque, pullout or bearing rating.

## Why this concept stops

**Removal has a hard geometric stop:** D6 service-stud heads cannot pass the
closed D4.4 bushings. Bushing top100 reaches shaft top132 at +32 mm, before
the minimum68.9 mm lift needed to clear the opening plane (requested75). The
75 mm sweep audit is a hypothetical reservation only, not an executable removal.

Nominal 0.4 mm diametral bushing play across a 10 mm bearing permits a tilt screen
atan(0.4/10). At the lowest wire exit, lever=90−43.9=46.1 mm: radial play plus tilt
is 0.2+46.1×0.04=**2.044 mm**, exceeding the proposed 0.25 mm path target. This
is a clearance-only screen, not a comprehensive worst-case bound. Both guides
lie along x, so the common pitch about that line is not eliminated by their
40 mm separation. Additional manufacturing/flex tolerances are not qualified.

Two independent endpoints can differ by 2 mm per axis; signed bow between fits
can change 2.564254 mm. Common rigid translation cannot remove relative errors.
The retained GH catalog gives nominal mating outlines but **no keeper bearing
surface, latch release travel, mating capture window or allowable keeper load**.
A closed sleeve is not a positive housing keeper. This prevents a source claim of
supported service/remating regardless of nominal envelope clearance.

Continuous +z sweep prisms conservatively cover every intermediate hypothetical
position and reverse motion; the stud-head stop prevents the full removal motion. All historical obstacles are checked, including core extraction,
anchors and access columns; unknowns stay occupied. Counts are potential blockers
of occupancy reservations, not physical collision measurements. Own housing release
occupancy remains an explicitly unresolved keeper/latch interface. Board tool
columns may be deferred until cassette removal; physical boards are never removed
from that audit. Root/crossmember contact is an intentional new integral union.
The occupied roof/corridor bounds are **not solid CAD**: internal wire voids,
shell/keeper connections, grip and tool passage are unresolved, with no internal
clearance pass claimed. No geometry here is ready to fabricate.

See [computed summary](summary.md), [plan](c36-plan.svg),
[service section](c36-service.svg), [source reconciliation](sources.md), and
[unpowered decision checklist](mock-up.md). Stage34 post allowable 39.836642 N
still fails 50 N; it does not rate this different root. R17 still does not fit.
No alternative mechanism or Stage37 is selected. Parent decision: stop C36 unless
actual GH capture/keeper interfaces and compatible registration are supplied;
neighbor caps alone cannot rescue this failed guide/capture concept.
