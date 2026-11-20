# Molex 150200075 family-specification contract

Binds Molex PS-15020-001 Rev F (family specification, 2023-12-06) and SD-15020-001 Rev F
(sales drawing, approved 2026-02-16) to the exact candidate 150200075 (8P, type A,
51 ± 2 mm). Both PDFs are retained unmodified in the private `circuit-dev-resources`
store under `molex/150200075/`; `evidence.json` records their paths, sizes and SHA-256.

Run from this directory:

```sh
python3 -B audit.py --store /path/to/circuit-dev-resources [--output new-file.json]
python3 -B test_audit.py
```

Without `--store` (or `CIRCUIT_DEV_RESOURCES`) the byte check reports `NOT_RUN`; a
missing or changed file fails. The audit imports the retained link-electrical kernel and
runs only the two checks whose consumed inputs the specification changes (about 6 s).

`finite_thickness_study.py` (numpy and scipy) solves the 8-circuit
cross-section with `finite_thickness_fd.py` (about 10 minutes) and writes `finite-thickness-result.json`;
`audit.py` reads that file by its recorded hash and fails if it or any of its inputs drift.

What it records:

- **Scope.** PS-15020-001 covers 15020-XXXX and points to drawing 150200001. SD sheet 1
  binds 150200075 (N8 / 51 ± 2 / type A), strip length, Tc and the 6 ± 2 stiffener. SD
  sheet 2 (cross-section, end tail, 0.155 mm stiffener) applies to odd counts only, so
  width, span, conductor width and layer data for N8 come from the PS.
- **Dimensions.** Reinforcement length conflicts (PS 6 ± 1, SD 6 ± 2) and neither document
  states precedence, so checks use the SD envelope 4–8 mm. It decides the FH12 4.5 mm
  support recommendation, which stays open. PS stiffener 0.15 mm nominal, no tolerance.
- **Current.** Molex rates 0.55 A (all conductors, ≤ 40 °C rise at 23 °C) and lists
  0.5 A per contact; the lower is used. FH12's derived 0.35 A all-contacts rating governs.
  Allocation verdicts are unaffected.
- **Ground share.** The source gives only a maximum, 730 Ω/km (36.5 mΩ per 50 mm), so
  the legacy LX minimum of 65.3 mΩ per 50 mm is above every conforming Molex conductor and
  the retained share PASS does not transfer. At the 49 mm minimum length the kernel needs
  at least 8.70 mΩ per 50 mm to hold one ground contact at 0.35 A (5.88 mΩ for 0.5 A). The
  nominal-copper estimate (26.1 mΩ at 20 °C) clears it; the whole end-stack envelope does
  not. Status OPEN until a minimum resistance or copper tolerance is sourced.
- **Capacitance.** 62 pF/m (cond/cond balanced, 1 kHz) has no qualifier or fixture, and
  together with 130 Ω implies an implausible eps of about 5.8, so it is not consumed
  directly. A first proxy (scale eps to 62 pF/m) put 17 links above 1.0 only because the
  cable eps was raised against the harness; it is kept as a rejected method. The physical
  cross-section (0.10 mm copper, polyester both sides, air outside) is solved on a
  three-level grid ladder (first-order convergence, step ratio about 2), extrapolated,
  corrected to an open boundary and given a further discretisation allowance. With the
  cable and harness at the same eps, every evaluated link stays below 1.0 up to eps 4.7.
  With the harness held at its retained 3.2, one link exceeds 1.0 once the cable eps passes
  about 3.8. The 62 pF/m figure implies eps about 3.3 under an adjacent-pair-grounded
  reading and about 4.4 under adjacent-pair-floating. Status OPEN, narrowed to the cable
  dielectric constant relative to the harness.

Not done: product qualification, BOM change, DRC, zone fill, adoption, manufacturing.
