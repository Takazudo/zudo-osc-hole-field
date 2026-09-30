# Envelope native ERC notes

Unvalidated draft — not bench tested. Source: design/spec/modules/envelope.py.
Run bash design/spec/modules/check_envelope.sh using the pinned KiCad10.0.6.

E1–E6 have zero errors and ten warnings each (60 total). Each of the five retained
white-LED symbols has two Unspecified pins, causing pin_to_pin warnings against
its passive driver network. Three LEDs are input magnitude monitors and two are
stage indicators. Their source-backed orientation is preserved. The checker
verifies every warning involves an actual locked panel LED reference and the
expected type. No warning suppression or library pin-type alteration was made.

On this fork, H1/H2 contribute12 warnings, F1–F3 contribute24, and POWER contributes
12. Oscillator/reference sheets have none. There are no new isolated-label
warnings; unused flip-flop complements and unused gate outputs are explicit NCs.
OTA output currents combine through individual100Ω resistors, avoiding a direct
output/output ERC conflict without suppressing the rule.

Complete native netlist parity passes, including all108 panel bindings and six
separately scoped ENV_STORAGE nets. The current source, capacitor, clamp network
and high-impedance buffer are local integrator circuitry; stage and magnitude
indicators only observe buffered nodes.

Fixed D1301 and RV1306 envelope panel references exposed collisions with existing
oscillator internal references. Manager authorized changing internal oscillator
prefixes to DO and RVO only; locked references and all oscillator connectivity
are preserved. The regression checks every reference in the assembled instrument,
and the oscillator's native checker is rerun with the envelope capture present.

These checks prove capture/connection properties only. Bench behavior, supply
sequencing, current bounds, physical orientation, placement and routing remain
open; see architecture/osc-block-ar and design/reports/spice/envelope.json.
