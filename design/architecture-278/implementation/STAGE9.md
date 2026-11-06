# Stage9 — bounded X1 manufacturing and service comparison

This comparison starts at `a7cb09da7f7b53100c3e6610ebeeda59e89e852c` and preserves Stage8. It compares the perforated-board arrangement with one alternative: continuous circuit boards behind the fixed terminal plane, factory-terminated leads and integrated support. It does not adopt either construction, route the complete circuit or implement A01.

## What is actually fixed

The [history evidence](stage9/HISTORY.md) distinguishes accepted USER decisions from engineering proposals. The fixed baseline is the flat318×298mm panel,438hardware centres, no new front support drills, factory soldering and mechanically supported controls/connectors. No accepted numerical inner or outer enclosure dimensions were found in the bounded reviewed history. The120/95/105mm depths and Stage8's322mm internal width/six new anchors are proposals. They must not silently become requirements.

Power-off/discharged service, no hot swap, no routine owner soldering and six rear trimmers accessible for normal calibration without middle-board removal remain obligations. Exact service forces, cycle life, extraction distances and external workspace are not accepted numerical limits. This finding does not declare unexamined space free.

## Published manufacturing capability

[Process evidence](stage9/process-evidence.json) retains actual downloaded HTML hashes, locators and applicability. Raw pages/HTTP headers remain ignored; no supplier was contacted and no files were submitted for manufacture.

| Primary publication | Relevant capability | Application to the present cutouts |
|---|---|---|
| [Eurocircuits current tolerance table](https://www.eurocircuits.com/technical-guidelines/understanding-manufacturing-tolerances-on-a-pcb/tolerances-on-a-pcb/) | Profile dimension±0.20mm; profile/cutout-to-hole position±0.20mm;0.50mm minimum slot. | Separately stated bounds exceed the Stage8 allowance. The mechanical guide permits requesting tighter limits but supplies no acceptance of±0.05/±0.05 for these features. |
| [JLCPCB rigid capability](https://jlcpcb.com/capabilities/pcb-capabilities) | Routed outline±0.20mm regular or±0.10mm precision; precision requires50×50mm minimum and three tooling holes≥1.5mm. NPTH slots have±0.20mm size tolerance. | Outline accuracy does not establish cutout registration. The36×32mm control board misses the bare-board precision size condition; panel applicability remains unknown. Hole positional tolerance is not substituted for contour registration. |
| [PCBWay capability table](https://www.pcbway.com/capabilities.html) | Shape±0.10–0.15mm appears under medium difficulty; below±0.10mm appears under “Unable to make.” | Header/column alignment was inspected in the raw table. Separately listed hole-position capability does not establish contour position. No construction-specific acceptance follows. |

The actual Stage8 land geometry gives a0.52mm pre-tolerance minimum gap. Under its explicit conservative compensation convention, the0.25mm land-edge criterion permits `(0.52−0.25)/2 = 0.135mm` combined boundary allowance. Its requested0.05+0.05mm leaves0.32mm; the Eurocircuits standard0.20+0.20mm gives a−0.28mm modeled conflict. This arithmetic is not a universal fabrication rule or a claim that every supplier is incapable. None of the three inspected publications establishes the required separate controls for these cutouts.

Ordinary rectangular board outlines avoid this particular tight internal-cutout dependency. They still need construction review; ordinary capability is not a manufacturing release. Round-hole size, slot width, profile registration, copper registration and fixed-component seating remain distinct tolerances.

## Concrete alternative and service consequences

| Item | Present Stage8 arrangement | One Stage9 alternative |
|---|---|---|
| Circuit substrates | Perforated jack/control substrates around retained fixed hardware; requested precise internal contours. | Two continuous rectangular circuit boards: jack75.7×67.9mm and selector36×32mm, front/rear copper datums35/36.6mm. Three6×6mm LED support boards retain the actual0402 devices at their original fixed plane. |
| Circuit inventory | 56 whole packages,76 units,182 source pins and seven fixed panel devices. | Same logical ownership, package XY/rotation, units, pins and fixed terminal XYZ.49 nonfixed packages move15mm in depth; no circuitry is removed. |
| Connections | Fixed terminals attach directly to local substrate. |15 permanent factory wires,35±3mm, connect fixed terminals/local LED lands to the elevated boards. No added mated interface or crimp; the three jack TN terminals remain NC. |
| Structural support | Six proposed mounts/anchors and322mm proposed inner width; GH/SW608 strip results do not qualify service forces. | Integrated frame atZ29.5..34mm with insulation toZ35mm, local connector shoes and captive body/bushing saddles reacting through the existing panel-clamped hardware. No new front support drills or loose service fixture proposed. Exact clamp engagement and load capacity remain unverified. |
| Enclosure/service change | Proposed322mm width and six side anchors are unaccepted inputs. | This local arrangement does not require those anchors/width. It instead requires a removable front-panel service opening and four new middle-board connector-access windows. Whole units do not pass through those windows or individual jack holes. Middle/core/cover50/69.2/105mm datums remain comparison proposals; no new total depth is accepted. No full-enclosure fit is established. |

Routine front repair would replace **two distinct factory service units**, jack group or selector, each disconnected at its own two existing GH ports. Power is off/discharged; the rear cover and obstructing rear cards are removed for latch access. Integrated grips retain the chosen unit before its last panel nut is released. The front-panel service opening must pass the complete unit plus grips; other-function harness retention and that extraction sweep remain unverified. No owner soldering or separate fixture is proposed. This is additional disassembly, not a demonstrated quick-service procedure. Normal rear-trimmer calibration still must work without middle-board removal.

The required foreign-hardware height ceiling29mm below the frame and5mm panel-side component envelope are **constraints to verify**, not measured clearance of all438 devices. The four modeled port-reaction paths include ordinary-allowance wire-guide holes and reduced sections; complete retention of all three jacks still needs exact saddle construction. Support beam calculations are planning surrogates, not ratings of the curved frame, clamp joints or assembled panel. The [electrical delta](stage9/ELECTRICAL-DELTA.md) retains added output-feedback, unprotected input, LED-loop, return and selector-open consequences. Stage8's complete path/return budgets do not transfer to this changed depth/header arrangement; full recalculation is separate bounded work.

## Conditional recommendation and decision boundary

Prefer developing the continuous-board alternative for this bounded comparison, subject to its explicit mechanical and terminal-assembly conditions. It removes the exceptional contour requirement rather than treating it as accepted. Existing circuitry and fixed controls remain; added leads introduce electrical consequences that Stage8 did not qualify. Detailed dimensions, support screens and the service sequence are in the [support assessment](stage9/SUPPORT-ASSESSMENT.md), with exact terminal mapping in the [electrical delta](stage9/ELECTRICAL-DELTA.md).

There is no evidenced owner enclosure limit that must be overridden merely to compare this arrangement. A proposal requiring a wider shell or special fixture must still be disclosed; neither is assumed inevitable from Stage8. Factory-complete unit replacement is the proposed service granularity. If individual front-PCB replacement without moving fixed hardware is an owner requirement outside the reviewed record, that is the precise choice to resolve before adopting this service plan.

For the original perforated arrangement, the smallest missing external evidence is a construction-specific supplier statement covering the actual cutouts, datum registration, FR4 stack and tool radii within the derived allowance. For the alternative, the next evidence concerns exact panel/bushing/clamp engagement and factory terminal/strain-relief construction, rather than tighter routing tolerance. No outreach or physical test was performed.

Completion of this comparison does **not** require full hardware qualification before a separate K-bearing source study can begin. Such a study must carry its own support/interface assumptions and must not reuse either X1 arrangement as proven infrastructure. Stage8 electrical, physical and native unknowns remain open; no native/simulation/hardware authority is inferred.
