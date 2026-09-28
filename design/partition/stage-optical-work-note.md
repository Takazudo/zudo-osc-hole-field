# Stage optical source cut and physical candidate

Authority: PROPOSAL (planning, owner-delegated). This is an intermediate issue #35 result, not an accepted full partition. Issues #61 and #62 are being integrated before final LED, fanout, connector and power checks.

## Why a separate plane is required

Each stage emitter is fixed at pot x+5.9 mm, y unchanged. The retained PTV09 footprint mounting pad5 is centred at x+5.3 mm and has Ø2.4 mm copper / Ø1.8 mm through drill. A shared board places the stage LED over that mounting hole on either face. Fixed x/y and the pot family are preserved.

`io_partition.py` now takes the already dedicated complete stage amplifier package, all stage_indicator parts, and its two actual bypass capacitors into `stage_optical` / `IO_STAGE_OPTICAL:<instance>`. The electrical nets, active channel assignment, package count and capacitor inventory are unchanged by this source cut. The twelve fixed stage LEDs receive geometry domain `EL`. The candidate contains 126 physical parts before #61 adds its twelve actual 330Ω resistors; regeneration after that merge must include them locally.

Native source-boundary checks find 465 crossing nets, zero forbidden crossings and zero package/island assignment errors. Native ERC has zero errors and the same 228 warning identities. The rail ledger still has 640 fitted IC packages and 347 load rows; its check and the unchanged conditional source-budget check pass. These figures precede #62 and must not overwrite its new accounting.

## Candidate geometry

The originally considered narrow optical strip had no conservative connector corridor among the pot bodies. The x210..313/y164..266 board then left too little clear space for actual SOIC stage-driver courtyards near the lower shaft holes. The current bounded candidate is **x210..317/y164..277**,107×113mm, so the lower front component corridor is usable. It includes **42** passages:18 toggle body passages,6 button/actuator passages,12 E pot shafts and6 A01–A06 ATTEN shafts. Omitting the latter would cut through a fixed shaft near the extended board edge.

`stage-optical-input.json` owns the candidate; `stage_optical35.py` generates its JSON check/placement proposal and dimensioned SVG. It checks the fixed LED roster, complete island/package/bypass allocation, every crossing net against the48 specified GH8 contacts, all42 passage/support circles, six rear header envelopes against the jack-board edge/control-field corridor, and conservative F.Cu courtyard packing with 0.25mm edge/part/fastener clearances. The proposal includes all current 126 packages at fixed or generated coordinates. This is source geometry, not a generated or routed KiCad PCB. The old 102 jack LEDs await #61's independent exact land-pattern audit.

F.Cu is at z=-4.2mm, board thickness0.4mm, panel rear at z=-2mm. A 1.75mm front package leaves 0.45mm nominal panel clearance. The rear surface is z=-4.6mm; a required control-body front no nearer than z=-5.0mm leaves 0.4mm. The real pot seating/body datum and the accumulated panel/PCB/part/support tolerance remain **UNSOURCED / OPEN**. These nominal gaps are not an installed-fit claim. Optical brightness and crosstalk remain NOT RUN.

Two layers are an explicit exception to the normal four-layer circuit board default. This sparse stage-only circuit has no oscillator timing or hold node, all driver/emitter/sense loops remain local, and the rear copper is to retain an AGND return pour with short local supply bypasses. The 0.4mm target avoids a deterministic nominal panel/control-body collision. Four-layer0.4mm fabrication is not assumed. Signal/rail return continuity and routing must be verified later; the layer exception does not waive them.

JLCPCB's Standard PCBA capability table lists unrestricted assembly thickness, double-sided SMT/through-hole assembly, and single-board dimensions 70×70..460×500mm. The candidate is within that dimensional window. Its 0.4mm manufacturing option is limited to a two-layer ENIG proposal; the published capability is not an accepted quote. Factory tooling/support rails, final laminate stack and process/stiffness approval remain open. No supplier was contacted.

## Connectors and supports

The retained JST GH PDF was inspected visually on physical pages0–2. `gh8-evidence.json` records the exact BM08B-GHS-TBT(LF)(SN) header, GHR-08V-S housing and SSHL-002T-P0.2 contact;1A atAWG26,50V,30mΩ initial/50mΩ after-test contact resistance,13.25×4.25mm header body, and7.3mm reference mated height. That reference height has no tolerance in the drawing; it cannot be a guaranteed installed stack limit. The header's actual primary land pattern/numbering must be implemented in the downstream connector library; no generic footprint is substituted here. Supplier codes remain unselected.

Six ports sit on B.Cu at y172mm, x218.5/235.5/252.5/269.5/286.5/303.5. Each carries its module's ENV_BUFFER/NOT_RISE/NOT_FALL, three rails and two AGND contacts. Currents, six actual cable routes, service loops and end-to-end loss remain part of full partition closure. Any one return is checked without assuming equal sharing; powered-off and failed-return protection remains #59 OPEN.

The 35 M2 support locations are explicitly enumerated in the generated report. Front screw/collar heads stay beneath the front panel; these are **not 35 front-panel drill holes**. Their support path is through a proposed insulating control-body carrier and enclosure structure; no load is assigned to a connector or solder joint. The shared control carrier must capture bushingless pot bodies to carry knob torque independently of their soldered mounting legs. All rear port envelopes clear the proposed Ø2 posts in plan. Matrix support is a proposal: plate stiffness, screw engagement, thermal expansion, shock and actual cable loads are NOT RUN. Factory mating/unmating requires local backing and enclosure strain relief takes in-service cable pull.

## Separate reference-fanout blocker

`reference-fanout-diagnostic.json` records the original shared oscillator-reference problem for #62. Ten fitted TC33X-2-103E trimmers alone draw 10mA per reference at nominal±5V and 13.333mA at their sourced−25% resistance corner. Fifteen 100k panel pots add 1.25/1mA nominal on positive/negative references. Fixed dividers and wiper loading are additional. The electrical standard explicitly limits shared DC drivers to 2 mA and local fanout pairs to six 100k pots. Connector branch current cannot stand in for total source-driver load. Actual full-temperature reference extrema are not promoted in the retained REF5050 facts; the diagnostic's±10% range is a sensitivity case, not a claimed manufacturer limit. #62 owns the repair and final true branch/rail accounting.

## Reproduction

Run geometry and schematic regeneration separately; this task does not regenerate the panel PCB after changing domain data. Export the master with pinned KiCad 10.0.6, then run `io_partition60.py --netlist <native.net> --require-cut`, `audit_master.py <native.net>`, and `stage_optical35.py` / `--check`. The focused source tests check the complete optical package and both bypasses. `python3 scripts/geometry/test_geometry.py` passes 15 tests.

The complete board list, core/control supports, all connector pin maps, fanout/return/loss closure, final geometry and #36–#43 amendment text remain unfinished. No original board group has been skipped and no accepted partition.json has been fabricated.
