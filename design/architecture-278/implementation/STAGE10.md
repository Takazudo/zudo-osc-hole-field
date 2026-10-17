# Stage10 — one A01 OFFSET1 source demonstrator

This isolated candidate begins at `ce779ce6ba5709fd26493f0bb71e22d8f3675969`. It assigns the complete A01 circuit to its own front jack/control, middle interface and rear core proposal. It does not adopt the architecture, replicate another function, host POWER or reopen X1. All earlier candidate evidence remains unchanged.

## Source conservation and identity

The [source inventory](stage10/INVENTORY.md) preserves90 packages:29 K,59 JR and2 P;118 units;285 physical pin entries including16 NC;17 bypass associations; and all nine fixed devices (three jacks, four LEDs, two pots). Whole multi-unit devices remain intact. The instrument retains5904 packages, five OSC,33 functions and438 fixed centres.

The29 K packages are **new candidate source assignments**, not physically qualified hosting. The retained non-OSC ledger changes2572→2543 unassigned K packages; all13 POWER packages remain unresolved and unchanged. The full5904-reference overlay makes the90 A01 ownership changes explicit and preserves every other assignment.

The captured RV1308 circuit identity is Bourns PTV09A-4020F-B104, while panel/function metadata names B103. Both are preserved and the discrepancy remains unresolved; this demonstrator performs no substitution. Twenty original package MPNs remain unspecified. Manufacturer evidence and source connectivity do not qualify assembled electrical performance.

## Independent mechanics and service

A01 uses its own supports and interfaces. No Stage9 X1 frame, clamp or free-space conclusion is treated as qualified infrastructure. The exact Bourns PTV09A-4020F variants are bushingless rear-mount parts: a body cradle, mounting-lug retention and rear-shaft relief must replace any assumed pot-nut force path. Shaft centres remain fixed.

The candidate dimensions, signed board planes, installation/removal procedure, insulation, neighboring exclusions and force-path limitations are recorded in the mechanical report and drawings. Enclosure dimensions remain engineering proposals; extending a board behind the panel does not establish a complete enclosure fit. Unknown neighboring hardware and routing volumes remain occupied/unknown constraints, not available space.

The [mechanical assessment](stage10/MECHANICAL-ASSESSMENT.md), [source report](stage10/mechanical-report.json) and [overview drawing](stage10/overview.svg) define the concrete proposal:

| Assembly | Outline size | Panel/rear pad planes |
|---|---:|---:|
| Active jack PCB |45×88mm|Z35/36.6mm|
| Passive control PCB |17×43mm|Z10/11.6mm|
| Independent middle PCB |82×150mm|Z48.4/50mm|
| Rear core PCB |76×108mm|Z69.2/70.8mm|

The control PCB reachesY307 and its carrier reachesY313, beyond the fixed panel'sY298 edge. The proposed minimum internal envelope is320×319×105mm, with new enclosure cleats; this is a revisable engineering input, not an accepted enclosure or fit result. The core is clear of the five retained OSC outlines in the modeled projection. Other-function solids, old K retention/removal and actual service corridors remain unresolved.

Fifteen local exclusion screens pass, including actual packages, own/foreign through pads, mounting tools, registered DIN contacts, retained middle headers, connector-release envelopes and carrier/PCB intersections. A toleranced edge notch permits the modeled J-PWR release sweep. Fourteen factory tail wires require explicit insulated guides through the jack rail. The combined LED strip supports all four LEDs, including the close output pair. Three own-jack body projections beneath that strip remain unknown even though the known pads clear.

Rear replacement uses two handles and proposed40mm supported DIN withdrawal after power-off/discharge, power unplugging and captive-screw release. Front repair requires the proposed removable panel/right-side access and other-function harness retention. Installed driver access to jack mountM4 is blocked by the middle/core boards: the complete front subassembly must be removed before PCB-level factory repair. No driver passage through those boards or owner soldering is assumed. Normal OSC calibration must still avoid middle removal. Exact body cradles, anchor joints, guide retention and assembled force ratings remain open.

## Electrical and acceptance boundary

The interface report inventories signal, power and return contacts separately. Harness cuts, local copper allocations, connector developed lengths and complete pad-to-pad path terms are distinct; none is reported as routed copper. Shared branches and return continuations must remain visible. Actual trace/contact resistance, coupling, reference error, protection, rail sequencing and output stability remain open.

The [electrical assessment](stage10/ELECTRICAL.md) and [explicit interface graph](stage10/interfaces-report.json) account for34 physical wires:20 GH service-harness conductors plus14 permanent jack/LED tails. Four harnesses use eight headers/eight housings and40 crimps. The DIN pair has96 physical mated contacts (eight signals,eight returns,80NC); together with40 GH contacts, the candidate has136 physical mated contacts. The28 tail-wire ends are not automatically28 added solder joints relative to direct mounting.

All269 connected source endpoints,16 NC endpoints,21 crossing-signal paths and106 power/return endpoint paths are retained. The longest complete crossing allocation is**467.579mm**, IN_BUFFER U7106:1→U7104:12; seven complete allocations exceed300mm as a historical sensitivity. The longest crossing-signal harness cut is93mm; the separate K power harness is118mm maximum. Permanent tails are88mm maximum. These measures remain distinct from routed length and from whole transfer-function behavior.

Two GH mated-contact source maxima total60mΩ initially or100mΩ after the documented tests, before wire/crimp/copper. Those bounds do **not** establish the inherited0.5mΩ return/1mΩ rail targets; no equal-current-sharing or ground-cancellation credit is taken. They are not measured minima or proof every actual contact fails. A low-resistance feed remains unresolved. Reference load subtotals, hypothetical wire capacitance and opamp quiescent current do not close full operating-state or stability requirements.

The applicable300mm cable/1nF envelope and inherited0.5mΩ return/1mΩ rail targets are retained. Choosing a connector does not establish either impedance or current acceptance; a published contact limit cannot be silently replaced by a favorable nominal value. No local source-placement result closes fullStage1.

This task stops after A01. Native KiCad10.0.6/ERC/DRC, simulation and physical qualification were **NOT RUN**. No default native CI, merge, adoption, fabrication export, purchase or energization is authorized by this source result.

## Verification and stop point

**56 focused tests PASS:** inventory9, mechanics15, interfaces/electrical14, independent composition16 and drawing2. The composition reconstructs actual footprint pads and independently checks source graph nodes, every reported path walk, wire/contact metrics and exact predecessor hashes. Independent code, electrical, mechanical and root receipts distinguish authored work from independent review. The overview was rendered and visually inspected; that is illustration review only.

The next bounded coordination decision is whether to refine A01's unresolved low-resistance feed and exact support/service construction. This result authorizes no replication and makes no global hosting-capacity claim. All earlier electrical unknowns and incomplete acceptance issues remain open.
