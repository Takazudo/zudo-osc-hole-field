# Whole-instrument ERC — unvalidated draft

Pinned KiCad 10.0.6 `kicad-cli sch erc --severity-all` on the generated 36-page hierarchy reports **zero errors** and **240 warnings**, all `pin_to_pin`. No rule is suppressed. The root smoke script asserts each sheet's exact warning count and type; the exported netlist matches the spec at every pin. These are schematic consistency checks, not bench qualification.

| Sheet instances | Count each | Total | Pin-type cause |
| --- | ---: | ---: | --- |
| H1–H2 | 6 | 12 | Three magnitude LEDs per instance expose `Unspecified` pins against rectifier diode pins; [pilot note](sample_hold-erc-notes.md). |
| F1–F3 | 8 | 24 | Four magnitude LEDs per instance; [filter note](filter-erc-notes.md). |
| E1–E6 | 10 | 60 | Five magnitude LEDs per instance; [envelope note](envelope-erc-notes.md). |
| B1–B2 | 2 | 4 | One magnitude LED per instance; [multiple note](mult-erc-notes.md). |
| X1–X2 | 6 | 12 | Three magnitude LEDs per instance; [selector note](manual_ab-erc-notes.md). |
| M5A–M5B | 14 | 28 | Six magnitude LEDs plus SUM clip LED per instance; [MIX5 note](mix5-erc-notes.md). |
| M4A–M4B | 14 | 28 | Six magnitude LEDs plus SUM clip LED per instance; [MIX4 note](mix4_vca-erc-notes.md). |
| W2, W1 | 6 | 12 | Three magnitude LEDs per instance; [wavefolder note](wavefolder-erc-notes.md). |
| A01–A06 | 8 | 48 | Four indicator LEDs per instance; [offset note](offset-erc-notes.md). |
| POWER | 12 | 12 | Manufacturer connector pins typed `Unspecified` against intentional parallel/passive supply pins; [power note](power-erc-notes.md). |
| O1–O5, OCTAVE_REF, N1, root | 0 | 0 | No warnings. |

The manufacturer LED symbol's `Unspecified` electrical type and the connector symbol's `Unspecified` supply pins explain these intentional connections; the exact circuit nets and pin identities are separately checked by the netlist verifier. Changing symbol electrical types or suppressing warnings would hide this distinction. Numeric clip LED references now export without KiCad's generic annotation warning while preserving each panel UID and coordinate. ERC does not establish headroom, timing, protection, stability, mechanics or current maxima.
