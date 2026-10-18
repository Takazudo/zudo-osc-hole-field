# Standard IDC comparison — proposal, not adopted

Panel audit checkpoint: `94daec5bbdbb007b40f2b5840534b4083ddece0f`, [separate report](https://github.com/Takazudo/zudo-osc-hole-field/issues/278#issuecomment-6250142982). This comparison does not revise that audit, canonical CAD, circuit, historical failures, coupon or viewers. The standalone GH4 coupon remains unordered/deferred and is not a gate. GH is not frozen. Fixed front positions remain fixed; board separation and enclosure depth may increase. 5 mm is neither a target nor a limit.

## Recommendation and dimensioned tradeoff

Carry **A: conventional 2×8 power plus custom 2×5 signals** forward as the first layout proposal. It retains familiar power-cable replacement, with CV/Gate positions NC. Keep **B: internal-only 2×4 power plus custom 2×5 signals** as a real, smaller alternative if the measured layout needs the saving. Neither is a qualified harness or an adopted pin map. Neither fits the failed narrow cassette by implication; start a new accessible edge layout, not a refinement of C36/RG34.

Use one documented mating family for comparison, Würth WR-BHD straight THT headers and female IDC sockets with strain relief. This avoids inferring cross-brand mating from pitch alone. Manufacturer drawings and catalog explicitly cover all three counts; see [source receipt](sources.json). Availability means active catalog variants, **not confirmed local stock or a completed cable assembly**. No BOM selection or supplier action.

| Item | 8 contacts (2×4) | 10 contacts (2×5) | 16 contacts (2×8) |
| --- | --- | --- | --- |
| Header exact MPN | 61200821621 | 61201021621 | 61201621621 |
| Matched socket MPN | 61200823021 | 61201023021 | 61201623021 |
| Header length, nominal ±0.20 mm | 17.82 | 20.36 | 27.98 |
| Socket length, nominal ±0.15 mm | 14.84 | 17.38 | 25.00 |
| Header pin span, nominal mm | 7.62 | 10.16 | 17.78 |
| Ribbon conductor-centre span at 1.27 mm pitch, mm | 8.89 | 11.43 | 19.05 |

The last row is `(conductors−1)×1.27`, **not cable outside width**. Insulation edges and thickness remain exact-cable inputs. Header bodies are 9.0±0.15 mm wide, 9.1±0.15 mm above their seating plane; tails 3.0±0.15 mm. Recommended holes Ø1.1±0.15 mm on 2.54 mm grid are drawing dimensions, not a new fabrication tolerance allocation. Socket closure and strain-relief geometry must enter the mated model; do not add raw heights and call it mated height.

For a first end-to-end layout along one accessible board edge, propose a **6 mm gap** between maximum body envelopes and **2 mm end clearance each**. These are layout assumptions, not proven finger access. Maximum length is 58.74 mm for A and 48.58 mm for B. Header-only strip width including 2 mm each side is 13.15 mm. Thus B saves **10.16 mm along the edge**, with no demonstrated height saving. Socket grip, strain-relief opening, key guard, routing and fasteners require additional space. The complete assembly cannot be certified inside either rectangle.

The maker PDFs supply these dimensions; the live [header catalog](https://www.we-online.com/en/components/products/WTB_WR_BHD_BOX_HEADER_2_54MM_MALE_PCB) and [socket catalog](https://www.we-online.com/en/components/products/WTB_WR_BHD_BOX_HEADER_2_54MM_FEMALE_CABLE_SIDE) explicitly list the mating pairs. Both pages returned active variants but availability “– / Check availability”. Exact stocked quantities, regional lead times, matching cable construction, tooling and assembled cable variants remain unresolved; these must be resolved before BOM adoption.

## zudo-bus reference, independently checked

Read-only sources at `Takazudo/zudo-bus@9107a8aaf055a68ff2d9141f38f4fbad3e5681c0`: BOM confirms J101–J108 use **DEALON DW254P-2X8-L0 / C4749189**. The retained maker drawing, revision A dated 2015-05-04, 16P row gives A=27.94±0.4, B=17.78±0.4, C=25.64±0.4 mm. Body dimensions 8.85/9.0, right-angle side dimension 13.5 to rear pin centre, 0.64 square contacts, 3.0 tails and Ø1.02 board holes were visually checked. The footprint carries 16 pads on a 2.54 mm grid and Ø1.02 drills; its reference-design status does not establish a new OSC placement or a mating socket.

This is a **right-angle** header; it is not dimensionally interchangeable with the straight Würth candidate. Its maker 3 A/contact number is not a cable assembly rating. The reference establishes a familiar construction, not current availability or authorization to borrow the bus upstream PSU wire. No sibling checkout changed.

## Electrical separation and wrong-port prevention

A retains conventional −12/GND/+12/+5 rail groups, with CV/Gate unused NC; do not repurpose them for REF5/REFN5. The [Doepfer primary description](https://doepfer.de/a100_man/a100t_e.htm) distinguishes 10-pin power from 16-pin power and warns that shroud orientation does not establish polarity. A fully numbered, drawing-view-aware map still needs review before implementation.

B needs a new internal-only map. A possible allocation is two contacts per each of −12, AGND, +12 and +5, but this is not assigned to physical pin numbers here. Parallel contacts do not establish equal sharing or increase the established fault rating. B sacrifices conventional power-cable interchangeability and needs its own assembly label/documentation.

Both preserve the five signal functions REF5, REFN5, IN_BUFFER, OFFSET_BUFFER and SUM_NEG plus the existing ground-return intent. The extra three positions on 2×5 do not authorize silently adding grounds, shorting references or changing return paths. The [A01 current ledger](../a01-current-ledger/README.md) remains conditional; it is not an upstream fault-current bound. WR-BHD header 3 A and socket 1 A ratings cannot be promoted to a harness limit.

**Bare A and B both fail the wrong-port requirement.** An ordinary keyed 10-pin Eurorack power socket has the same nominal format as J-SIG. Colour, labels, reversed orientation and a shroud alone are inadequate. Also test smaller plugs in larger headers, offsets, reversed plugs and power adapters; differing pin counts alone are not a complete safeguard.

Propose a removable, mechanically coded **signal-port guard and matching cable collar**, surrounding the standard socket, that stops any uncoded power socket *before contacts engage*. It must remain captive in normal service, permit socket-body grip and require deliberate tool access to remove. No guard dimensions or retention strength are established yet. Missing-pin/blocked-cavity coding alone would not stop an ordinary unblocked power socket entering a signal header, so it is not accepted as the sole remedy. If a practical guard cannot be designed from exact mating geometry, change the signal family rather than accepting ambiguous power compatibility. No protection claim is made before this guard is dimensioned and reviewed.

## Depth, ribbon routing and service sequence

Use replaceable flat 1.27 mm pitch ribbon with a supported termination. 3M TS-0732-05 supplies real rolling-flex comparison data for 28 AWG ribbon constructions including 3365, but is not an exact cable/IDC compatibility specification, a minimum-radius guarantee or an endurance requirement for this instrument. No ribbon MPN, cut length, tolerance or radius is selected. Do not reuse GH round-bundle R12 calculations for ribbon, bend a ribbon edgewise as if isotropic, or fold it sharply to preserve thinness.

Define board-to-obstacle free gap `G`, worst-case mated height `H`, flatwise bend radius `R`, cable thickness `t`, and combined bow/registration/assembly allowance `T`. A proposed 90° departure needs at least `G ≥ H + R + t/2 + T`; other routing forms need their own swept envelopes. This is a necessary local check, not whole-path proof. For rear-facing removal with a planning 15 mm straight withdrawal, reserve at least `H + 15 + T` from seating plane plus a separate grip volume while the rear cover is removed. Actual contact disengagement travel comes from the selected mating model. Do not assume 15 mm is the maker requirement.

There is currently **no finite proven feasible interval** for G or cable cut length: H, R, t, termination allowances, registration and neighbor occupancy are incomplete. All undesigned volumes stay occupied/unknown. Increase board separation or cover depth after evaluating these inequalities; no reason exists to cap the increase at 5 mm. Full DIN/core 40 mm removal, jack-board screwdriver columns, carrier rails, neighboring boards and cover fasteners must remain explicit swept reservations.

Proposed unpowered sequence:

1. Remove rear cover; support the module/core on its mechanical frame before any connector pull. Use a temporary service cradle if necessary; cable is never the support.
2. Expose the separately coded signal and power service edge without removing a load-bearing guide. Grip socket bodies/approved pull features, disconnect one at a time, and park each cable in a non-contacting holder. Provide counter-support adjacent to each header to limit board bow.
3. Release both inter-board cables before moving the core through its 40 mm path. Therefore ribbon slack need not absorb that core motion. This is a proposed sequence change, not a retrofit assumption about current access.
4. For front jack-board service, remove the disconnected harness and removable guide/guard assembly through a checked path, then expose fasteners. No intact RG34 cap or sleeve remains across access columns.
5. Reassemble mechanically, inspect pin-1/polarity and perform unpowered point-to-point/short checks against the approved map before any later, separately authorized energization.

## Integrated unpowered mock-up decision sheet

Standard parts use their exact maker drawings, pin numbering and lands plus a CAD/assembly preview; no separate physical requalification of each ordinary component is required. Use an integrated mock-up for the custom arrangement only, once exact CAD is assembled.

| Input / observation to record | Decision criterion |
| --- | --- |
| Exact header/socket/strain relief/cable and guard CAD; mated H; complete cable width/thickness | Maker variants and orientation agree; unknowns block fit acceptance, not presumed clearance |
| Accessible grip and 15 mm planning sweep at each end | Socket-body grip and disengagement without wire pull, neighbor collision or unsupported board; otherwise enlarge/reorient layout |
| Worst bow and carrier registration relative to hardware datums | Insert measured or defensible source bounds in T; all clearances remain nonnegative with the existing required margins; no assumed ≤1 mm registration |
| Cable relaxed installed path, removed-end parking path, shortest/longest admissible lengths | Length interval remains nonempty after cut and termination tolerances, while maintaining sourced bend rule and straight exits; no nominal-only tuning |
| Guard with correct signal plug and representative wrong 10/16/8-pin power plugs, offsets and reversal | Correct plug mates; wrong plug is stopped before electrical contact; otherwise reject guard/family combination |
| Guide/guard removal, front fastener access and 40 mm core extraction | Every step possible in stated order with independent mechanical support and no occupied/unknown collision |
| Support/counter-support and cable strain relief during handling | No load transferred through ribbon/IDC joint; allowable force/bow criteria must be set from actual support design before claiming pass |

This is an assembly/access check, not an endurance campaign. No physical observations have been made. Remaining source-capable work is exact cable/termination selection and availability, mated CAD envelope, reviewed numbered maps, guard geometry, then a fresh obstacle/tolerance interval study. Parent chooses the continuation; no manufacturing outputs, procurement or circuit changes follow automatically.
