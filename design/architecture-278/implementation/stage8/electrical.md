# X1 operating-state current and return study

This source-level analytical study traces all56 packages,76 units and182 pins, including five unused amplifier sections and six unused grounded fault-switch channels. It preserves the four physical harnesses,15 wires, all ten bypasses and fixed panel hardware. `current-input.json` makes the assumptions explicit; `currents-report.json` reproduces54 conditional cases. No simulation, native KiCad, ERC/DRC, hardware test or acceptance is claimed.

The distinction that changes the budget is **which current actually enters AGND**. Eight OPA4197 sections and four OPA4196 sections have a combined13mA source-conditioned full-temperature quiescent maximum at zero output current. This flows principally from positive to negative supply; multiplying it by a ground-harness resistance would invent an AGND load. Unused followers still consume quiescent current; their grounded input bias currents remain a separate return contribution. Active output currents, crossover/dynamic behavior and source conditions prevent calling the resulting sum a guaranteed active-current bound.

The three magnitude indicators do put current into the jack-board ground. Their actual diode polarities give a signed resistor/ground current of MONITOR/5600 when feedback is linear: approximately±0.893mA each at±5V monitor voltage. The output indicator senses OUT_BUFFERED, upstream of the two499Ω output resistors: under the nominal10kΩ load, its monitor is OUT_TIP +998Ω·Iload (about5.498V for a5V output), so its current is about0.982mA. This assumes linear precision feedback and sufficient amplifier/LED headroom; neither is qualified. The LED emits for either polarity, but its ground current reverses. Positive current flows from the amplifier output through the first bridge diode, LED, fourth diode and sense resistor into AGND; negative current flows from AGND through the sense resistor, second diode, LED and third diode to the negative-driving output. Opposing indicators may cancel in one nominal algebraic state, but the report sums magnitudes for its conservative scenarios and gives no cancellation credit.

ADG5412F has a real GND pin. The exact retained RevC PDF was recovered and its SHA256 matched the committed source record. Table1, printed page4/physical index3, specifies normal IGND0.4mA typical/0.6mA maximum and fault IGND0.8mA typical/1.1mA maximum. Conditions are±16.5V supplies, stated digital-input levels, and±55V source for the fault rows. These are direct ground-current facts, not an inference from unrelated supply maxima. Applying them to the project's±12V rails is explicitly a sensitivity case; it is not a new manufacturer guarantee. The raw PDF and HTTP receipt remain ignored under `.circuit-cache/sources/architecture278-stage8-adg5412f/`; the URL, hash, revision, locator and values are retained in `current-input.json`.

The enable resistor networks contribute about99.01µA total into jack AGND before digital-input current corrections. Input100kΩ pulldown currents may return locally through the input patch sleeve or share a remote supply/chassis path; output-load return may similarly enter the local sleeve or another external ground. The report leaves those divisions unknown and includes full magnitudes in its conditional envelope. Signal AGND and power AGND are electrically joined on each board and at the real middle J-PWR pin7 anchor. A label saying “signal return” does not prevent it carrying LED or supply current. No equal sharing between the two return wires of a board is credited.

The selected switch's10MΩ bias load is only about0.5µA at5V. If opposing±5V sources momentarily overlap, approximately2.273mA flows from one A/B driver through the two2.2kΩ resistors to the other driver. This is principally a signal/rail path, not a2.273mA AGND load. The physical switch's overlap/open interval and lever mapping remain unqualified; those rows are hypothetical transition states, not guaranteed operating modes.

## Conditional numerical comparison

The following uses the ADG0.6mA-per-package source-table sensitivity, two50mΩ mated contacts in each return branch, zero additional wire/board resistance and a hypothetical0.5mΩ upstream-common path. That0.5mΩ value is **not** assigned to a GH branch. All numbers omit the explicitly listed unknown contributions; they are not complete assembled bounds.

| State | Jack ground magnitude envelope | Jack-to-upstream voltage bound for modeled terms | Selector contribution from C−J ground difference |
| --- | ---: | ---: | ---: |
| Idle, A selected |1.299mA|130.55µV|0.0286µV|
| A=+5V, B=0, A selected |3.724mA|374.21µV|0.0819µV|
| A=B=+5V, A selected |4.666mA|468.97µV|0.1027µV|
| A=+5V, B=−5V, overlap |3.185mA|320.07µV|0.0350µV|
| Hypothetical open transition, both inputs+5V |3.185mA|320.07µV|318.48µV|

Several modeled ground-voltage scenarios exceed the retained200µV planning comparison even before additional impedance. This remains a concrete constraint, not a silent target relaxation or a measured failure threshold. The zero-extra-resistance cases are not actual impedance extractions. Further cases explicitly add wire/copper/common resistance and retain total current/error guarantees as UNKNOWN.

Crucially, a whole-board C−J ground shift is **not automatically unity-gain output error** in the selected circuit. With ideal unity followers, selected output relative to jack AGND is

`Vout = [Rbias/(Rbias+Rseries)]·VA + [Rseries/(Rbias+Rseries)]·(GC−GJ)`.

For2.2kΩ into10MΩ, the ground-coupling coefficient is about0.000220; overlap with both equal source resistances halves it. An open switch instead leaves the10MΩ tied to control ground, giving unity ground coupling, and a conditional15nA input-bias sensitivity across10MΩ is150mV. Unknown node capacitance and switch timing prevent turning that DC number into a transient claim. Local ground gradients at input protection/feedback pads, external source/receiver reference differences, PSRR and bias/leakage remain separate and can couple much more strongly. The small selected coefficient does not qualify total output accuracy.

## Remaining physical current paths

The ten actual100nF source bypasses sum to0.4µF per rail on the jack board and0.1µF per rail on the control board. A hypothetical12V/10ms ramp gives0.48mA and0.12mA per rail respectively. Positive- and negative-rail charging ground currents have opposite signs; no cancellation is credited because ramp order and impedance are unknown. Unallocated board bulk is not invented. The1nF remote-net envelope gives0.1/1/10mA displacement-current sensitivities for0.1/1/10V/µs, but neither actual capacitance nor its ground/rail/neighbor coupling destination has been extracted.

U3305 supply-pad-to-capacitor corridors alone are not the complete bypass loop. The C3308/C3309 ground connection and both supply paths matter, along with capacitor ESR/ESL. Any supplied AGND corridor is reported as conditional source geometry, not an impedance result. C3301's fast-feedback branch runs between drive and feedback nodes; an AGND leg must not be invented for it.

Faults and power sequencing remain specifically unresolved: input overvoltage/clamps, output short/back-drive, one-rail loss, floating rails, connector interruption and startup. The retained100nA grounded-off ADG leakage limit applies only to the stated fully grounded test; floating-off10µA is typical with no maximum. Neither bounds arbitrary unpowered behavior or authorizes hot plugging.

The next hosting/routing constraint is to keep LED bridge/sense/amplifier/bypass groups local and provide explicit current paths to the power-return landing without crossing precision input/feedback reference regions. Retain the adjacent signal return, but do not assume it stays unloaded. Carrier support, strain relief, service clearance and the real upstream POWER handoff must remain explicit. This study adds no other module and changes no canonical circuit, source ledger or Stage7 artifact.
