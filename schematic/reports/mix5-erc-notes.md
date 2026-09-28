# MIX5 ERC notes — unvalidated draft

KiCad 10.0.6 `kicad-cli sch erc --severity-all` on the generated root reports **zero errors** and **14 `pin_to_pin` warnings per M5A/M5B sheet**. The six magnitude LEDs each contribute two warnings where their library pins are typed `Unspecified` and the rectifier diodes are `Passive` (12 warnings). The SUM clip LED contributes one `Unspecified`–`Open collector` comparator output and one `Unspecified`–`Passive` series resistor warning. The pin maps and netlist export match the source spec. These are library electrical-type warnings at intentional LED connections, not a declaration of electrical qualification. The fixture asserts exactly these counts, and any new type or count fails.

Other-sheet warnings are enumerated by the root smoke test. The MIX5 result has no hardware, fault or stability pass.

KiCad netlist export also prints `Warning: schematic has annotation errors` and exits 0. A temporary copy of the MIX5 child sheet with only locked `D906A`/`D1006A` changed to unique numeric references exported with no warning. This isolates the message to the suffix-A clip LED reference form. The temporary copy was removed; panel lock references remain authoritative, and exported netlist pin parity passes. Track this KiCad annotation compatibility issue separately rather than silently renaming fixed hardware.
