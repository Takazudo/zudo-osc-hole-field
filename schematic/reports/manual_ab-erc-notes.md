# Manual A/B KiCad ERC notes

KiCad 10.0.6 `sch erc --severity-all` on the generated instrument sheet reported **zero errors** for X1 and X2. Each instance has six remaining warnings, all `pin_to_pin`.

| Sheet instance | Warning count | References | Reason |
| --- | ---: | --- | --- |
| X1 | 6 | D809, D909, D1009 and D3304/D3306, D3308/D3311, D3314/D3316 | Each of the three magnitude indicators uses the intentional four-diode rectifier around its LED. KiCad reports the library pin-type mismatch (`Unspecified` LED pin to `Passive` diode pin) at two bridge nodes per indicator. |
| X2 | 6 | D810, D910, D1010 and D3404/D3406, D3408/D3411, D3414/D3416 | Same intentional bridge topology for the three input/output indicators. |

The warnings are visible and justified here; no ERC check was suppressed. The smoke check also passed exported-netlist parity. KiCad does not establish the Dailywell toggle's physical contact mapping, click amplitude, source-overlap behavior or analog performance; those remain explicit bench gates.
