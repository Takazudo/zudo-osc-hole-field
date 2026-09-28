# MULT KiCad ERC notes

KiCad 10.0.6 `sch erc --severity-all` on the generated instrument sheet reported **zero errors** for B1 and B2. Each instance has two remaining warnings, all `pin_to_pin`.

| Sheet instance | Warning count | References | Reason |
| --- | ---: | --- | --- |
| B1 | 2 | D109, D3103, D3105 | The magnitude indicator's LED and steering-diode bridge pins meet at intentional rectifier nodes. KiCad reports the library pin-type mismatch (`Unspecified` LED pin to `Passive` diode pin); no pins are left floating or shorted by the warning. |
| B2 | 2 | D309, D3203, D3205 | Same intentional magnitude-indicator bridge topology as B1. |

The warnings are visible and justified here; no ERC check was suppressed. The smoke check also passed exported-netlist parity. This establishes the captured pins and nets only. The input isolation, ±12 V fault case, output loading, stability and pitch accuracy remain unvalidated bench gates.
