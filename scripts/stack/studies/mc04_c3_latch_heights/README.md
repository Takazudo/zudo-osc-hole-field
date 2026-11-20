# Task C step 3a: 18 of the 31 NOT SHOWN latches now have sourced neighbour heights

```sh
python3 -B heights.py [--output new-file.json]
python3 -B test_heights.py
```

The DS-88 latch rule exempted chip 0603, SOD-123 and SOT-23 neighbours of the K connectors as
"ASSUMED lower than the 2.0 mm connector body; no height retained". That left 31 latches NOT SHOWN.
This study reads each remaining neighbour's MPN from the K schematic sheets. It takes the
manufacturer maximum body height from `evidence.json`, which records the path, hash and locator of
each source, and compares it with the FH12 closed-height minimum of 1.8 mm (EDC3-150229-11, 2.0 ± 0.2).

Result (`result.json`, SHA-256 `f558e2686104560df4ffa22fa9636d7fe52e58aef9a59d478372705b7353a728`):

| Verdict | Latches | Basis |
| --- | --- | --- |
| LOWER THAN BODY (sourced) | 18 | Every neighbour has an exact sourced maximum. The tallest is 1.3 mm (BAS16GW SOD123), at least 0.5 mm below the closed body. |
| NOT SHOWN | 13 | 27 neighbours (25 R0603, 2 C0603) have no MPN on their symbol, so no exact height can be bound. |

Heights used: Yageo RC0603FR and RT0603BRD 0.55 mm, KEMET C0603C101J5GACTU 0.87 mm,
Murata GRM1885C1H103JA01D 0.9 mm, Murata GRM188R71H104KA93D 0.9 mm (the retained catalogue
response, where width and thickness are both 0.8 ± 0.1), BAT54S and MMBT3906 SOT23 1.1 mm,
BAS16GW SOD123 1.3 mm.

A LOWER THAN BODY latch stands on the same footing as the 27 retained open latches; it is not a
physical access proof. The following stay open for all 61 links:

- The open-actuator sweep. The reference figure is 4.8 mm at 90°, which is not a maximum.
- The central finger approach.
- The cable fold.
- Solder fillet height.
- Placement binding of schematic MPNs, which `pnpm circuit:check` reports as NOT RUN.

Closing the 13 cases needs exact identities for the 27 unbound parts. That is a BOM decision,
and it is part of the wider order-package gap of unbound 0603 passives. The EDC3 drawing should
also be retained in `circuit-dev-resources`; today only its reviewed hash is recorded.
No geometry, schematic or BOM was changed.
