# A01 mechanical source assessment

This is the mechanical author's assessment, not an independent review of this source. The root, code and electrical agents review it independently. Native KiCad, ERC/DRC, simulation and physical tests were NOT RUN.

The candidate preserves all90 packages,118 units,285 physical source pins,17 bypass associations and nine fixed panel devices. The29 former K packages occupy a new rear board to the right of the five retained OSC cards. The52 nonfixed JR packages occupy an elevated jack board. Three jacks use permanent factory tails; four actual SMT LEDs share one continuous local support strip with eight independent wire lands. This avoids overlapping islands for the two output LEDs separated by2.05 mm. The two pots remain on a separate passive control board. The new middle board has its own outline, mounts and carrier; it is not an abstract wiring plane.

| Board | Outline, mm | Panel/rear pad faces Z, mm |
| --- | --- | --- |
| Active jack |195,94 to240,182|35/36.6|
| Passive control |210,264 to227,307|10/11.6|
| Middle |232,142 to314,292|48.4/50|
| Rear core |236,174 to312,282|69.2/70.8|
| Fixed jack/LED datum |Locked source coordinates|20/21.6 nominal|

The positions and exact footprint transforms are reproducible from `mechanical-input.json`. Rear SMT uses an explicit source-face X reflection before the quarter-turn/translation. Full packages, unused units, feedback/summing nets and bypass ownership remain intact; the all-net spans and17 actual bypass pad distances are reported, not replaced by locality claims. Several bypass connections remain longer than an eventual close PCB layout should target. No source topology or footprint pin is reassigned to improve the numerical result.

## Bourns seating and body support

The exact retained Bourns PTV09A-4020F-B103/B104 drawing is [PTV09, revision01/25](https://www.bourns.com/docs/product-datasheets/PTV09.pdf), SHA256 `411cdb6a62e61f9c5bc2df76ed64ee21d7bcfbee035c1ba36beff08c43f28558`. The official bytes were retrieved again and physical PDF page1 was visually inspected. Its -4 variant is horizontal/rear mount and **bushingless**. The candidate therefore assigns no pot nut or threaded-bushing reaction. Rearward terminals permit a PCB parallel to the panel; the explicit signed mapping takes the rear body seating plane toZ10 and the shaft toward negativeZ. The6.8 mm body depth gives front bodyZ3.2; L20±0.5 gives nominal shaft tipZ−10. With a proposed2 mm panel, nominal exposed shaft is8 mm. Neither panel thickness nor installed stack tolerance is qualified.

A3 mm candidate relief hole at each shaft axis reserves the drawing's2 mm diameter rear projection; the3.8 mm rearward projection is included. Actual terminal and mounting-land envelopes are excluded from those holes. Insulating split body cradles react the bushingless bodies to edge rails and a bottom enclosure cleat. Their exact capture surfaces, shell tolerances, bearing loads and retention method still require construction detail; soldered tabs alone are not credited as an enclosure anchor. RV1308 remains the actual source B104 despite conflicting B103 lock metadata.

## Independent support and service

Four mounts support each jack, rear and middle PCB; two lower mounts plus edge rails/body cradles support the control assembly. Reports specify drill, washer, head, spacer, insulating interface and tool-depth intervals. Control screws clamp from the panel side with spacers on the opposite side; rear/jack/middle screws clamp from the rear. The carrier rail/crossmember geometry terminates in proposed integral anchor bosses and new enclosure cleats. No existing enclosure holes are assumed. The candidate minimum internal envelope320×319×105 mm is an engineering proposal, not an owner-approved maximum or a claim that an enclosure already exists.

Carrier depths, connections and crossmembers are screened against own PCB planes and connector release envelopes. The middle carrier is offset from the elevated jack board and has a thin local tab where needed. Its left-edge notch `[232,169,234,181]` clears the J-PWR housing/latch release envelope, including0.4 mm inward boundary allowance. An independent full-span beam sensitivity is reported using the retained70 GPa aluminum planning value,5 N service load and a separate90 N DIN sensitivity. This does not prove joints, bored rail sections, cleat attachment, torsion or actual load distribution.

Fourteen factory tail wires approach independent lands through explicit insulating wire-guide requirements in the jack rail. Nominal1.2 mm bores,±0.2 diameter and0.3 radial placement give2 mm maximum removed envelopes and1 mm minimum openings. Wire/insert selection and retention remain open;3 mm pitch preserves a1 mm local ligament before structural qualification. Guides are not credited as a qualified strain-relief system.

All15 modeled local exclusion lists are empty and asserted. These include actual own/foreign through pads, complete package courtyards, mounts, handles, the96 newly registered DIN contacts, the480 retained OSC contacts, retained middle packages, source GH release sweeps and carriers crossing own PCB substrates. The padplane and signed male/female DIN transforms use the exact selected HARTING drawings already retained in Stage5/6; adoption of their engineering registration is not native validation.

Rear-core service disconnects power and releases four captive screws before supported40 mm axial DIN withdrawal using two handles. Front assemblies require power-off/discharge and the proposed removable front panel/access arrangement; other-function harness retention is not assumed. Installed rear driver access to jack mountM4 is blocked by the middle and rear boards. This is explicitly reported: remove the complete supported front assembly before PCB-level factory repair; do not pass a driver through those boards. Normal OSC calibration still requires no middle removal.

## Precise remaining constraints

The source report retains every historical other-function overlap and all relevant fixed-hardware XY projections. Unassigned Z space is not free. Three own-jack body projections under the LED strip remain unresolved even though their known through-pad envelopes clear it. Real jack seating, free-tail solder points, neighboring body/tail volumes, complete pot cradle details, mating restraint, insulation/strain relief and enclosure access require physical construction evidence. The retained old populated K cannot silently remain beneath the new core or its extraction path. This bounded A01 proposal neither redesigns other functions nor adopts the architecture.

Fifteen focused mechanical tests pass, including mutations for missing packages, fixed-centre movement, wrong DIN orientation, weaker process allowance, omitted release notch, blocked mount access and changed fixed-terminal depth. The electrical agent independently evaluates all34 candidate wires and complete signal/return allocations; mechanical source clearance does not close those electrical acceptance constraints.
