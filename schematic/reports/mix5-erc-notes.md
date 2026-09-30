# MIX5 ERC notes — unvalidated draft

KiCad 10.0.6 `kicad-cli sch erc --severity-all` on the generated root reports **zero errors** and **14 `pin_to_pin` warnings per M5A/M5B sheet**. The six magnitude LEDs each contribute two warnings where their library pins are typed `Unspecified` and the rectifier diodes are `Passive` (12 warnings). The SUM clip LED contributes one `Unspecified`–`Open collector` comparator output and one `Unspecified`–`Passive` series resistor warning. The pin maps and netlist export match the source spec. These are library electrical-type warnings at intentional LED connections, not a declaration of electrical qualification. The fixture asserts exactly these counts, and any new type or count fails.

Other-sheet warnings are enumerated by the root smoke test. The MIX5 result has no hardware, fault or stability pass.

The earlier suffix-A clip LED references produced a KiCad annotation warning. The geometry source now assigns numeric references D9061 and D10061 to the same locked UIDs and coordinates. Full-instrument netlist export no longer emits the annotation warning; exported pin parity passes.
