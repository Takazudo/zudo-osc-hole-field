# H1/H2 sample-hold pilot ERC notes

The generated pilot is an unvalidated draft. KiCad 10.0.6 ERC reports **zero errors and twelve warnings**: for each of H1 and H2, each of the three white magnitude LEDs has two `pin_to_pin` warnings between the LED symbol's `unspecified` electrical pin type and the passive bridge diode/resistor pins. The warnings concern library electrical pin types. The exact LED and BAS16GW-QX diode physical pin polarity is mapped by retained evidence and the source spec. `scripts/schgen/smoke.sh` enforces zero errors and only these twelve warnings; any additional type or count fails.

Two pilot instances use one shared source sheet. The original two-page attempt put `RAW_HELD` on a global label, which shorted the two LF398 outputs and produced an ERC output-to-output error. The final family keeps all module signal nets local to the shared sheet, preserving H1/H2 separation. Rails alone are global and have test-only supply flags until the actual power interface is captured.

ERC and exported pin parity do not establish acquisition pulse width, LF398 hold behavior, output compensation, panel mechanics, factory allocation or rail current limits. Vendor-model and bench checks remain open.
