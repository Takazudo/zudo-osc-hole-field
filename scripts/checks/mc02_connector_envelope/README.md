# FH12 nominal field versus drawing tolerance

This source-only Decimal audit compares the retained virtual field depth with
actual reviewed Hirose EDC3-150229-11 drawing dimensions. It does not change a
field, create a footprint transform, recalculate collision geometry or prove fit.

Actual PDF SHA-256 `c3257beed2331e5c95e176bc28441b04b804301a44c11b462e486fb5cc649d07`
is required from the ignored authorized transfer path in `evidence.json`. Printed
sheets1/2, physical indices0/1, show depth5.6 +/-0.3 and closed height2 +/-0.2
(relative to datum b), for <=34 and >=35 contacts respectively. The selected
8/14/26/40 SH(55) variants use these corresponding views. The PDF was visually
inspected; it is not published by this checker.

| Quantity | mm | Scope |
| --- | ---: | --- |
| Retained virtual field depth |6.1|Existing model, unchanged|
| Declared maximum connector depth |5.9|5.6+0.3 drawing bound|
| Total dimensional difference |0.2|Subtraction only; not clearance proof|
| Difference per side if exactly centered |0.1|COUNTERFACTUAL centering assumption|
| Depth needed to retain0.25 growth on both sides at maximum |6.4|COUNTERFACTUAL arithmetic, not an adopted field|
| Closed drawing height interval |1.8–2.2|Not installed height or access clearance|

The retained option explicitly assumes the5.0mm land chain lies inside the
nominal depth. Neither its body/terminal/land registration nor its virtual-field
center is established by the project. Therefore6.1 being greater than5.9 does
not establish physical containment. Even under exact centering the original
0.25mm per-side nominal growth would reduce to0.1mm at maximum depth. If a
physical datum is not centered, the division by two cannot be used as actual
edge clearance. No new centered registration is asserted.

All122 endpoint rectangles are read, and their direction-dependent6.1 depth
and existing long-axis formula0.5n+5.6 are checked. Long-axis spans are reported
only as project nominal fields: this narrow audit does not map a physical-width
or recommended-land union to those spans. XY growth cannot cover Z tolerances.
The reference-only open height(4.8) and angle(90 degrees) are not maxima.
All physical containment verdicts remain NOT_ESTABLISHED; adopted depth stays null.

```sh
python3 -B scripts/checks/mc02_connector_envelope/audit.py
python3 -B scripts/checks/frozen_studies.py discover scripts/checks/mc02_connector_envelope
pnpm circuit:check
```

These commands perform only frozen-source hashing and arithmetic. No placement
search, native KiCad, routing, DRC, fill, inventory adoption or manufacturing.
Missing transferred PDF or changed source bytes fails closed. No network retry
or automatic source substitution is performed.
