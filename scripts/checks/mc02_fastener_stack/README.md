# MC02 conditional four-site fastener stack

Read-only Decimal arithmetic for the four active ST-08 sleeves. No source
geometry, BOM, generated report or installed fastener is changed.

| Site | Front board | Fixed XY mm | Nominal grip mm | Conditional W + P capacity mm |
| --- | --- | --- | --- | --- |
| SLV-U1 | JL | 74, 28 | 22.2 | 0.15 to 0.65 |
| SLV-U2 | JR | 244, 24 | 22.2 | 0.15 to 0.65 |
| SLV-L1 | P | 93, 276 | 20.2 | 2.15 to 2.65 |
| SLV-L2 | P | 244, 230 | 20.2 | 2.15 to 2.65 |

The pinned ruled list supplies site IDs/coordinates/boards. The pinned stack
planes reproduce the grip as front-board face Z minus K rear Z. The pinned
threading record supplies the ASSUMED M3 x 25 screw and class-level grip/thread
projections; those independent source relationships are checked.

The nut height **2.40 +/-0.25 mm is now PRIMARY_DIMENSION_VERIFIED** from
actual transferred manufacturer drawing bytes: Keystone DWG4708, dated5.26.11,
172371bytes, SHA-256
`b31545f168c90a3bc2d44f06b0f0a3003a6aaeef002b4366e11a44230637af44`.
The single unnumbered sheet (physical index0) gives the side-view height2.40;
NOTE1 defines millimeters and the lower title block specifies general decimal
[MM] tolerance +/-0.25 unless otherwise specified. Top view states M3 x0.5
thread and5.50 across flats. The revision grid is blank; CODE C is not a revision.

The original handoff comment URL, official URL, reported drawing and expected
hash remain recorded alongside actual reviewed hash/locators in `evidence.json`.
This offline arithmetic tool consumes that reviewed transcription; it does not
re-download or visually inspect the PDF each run. Source bytes stay ignored.

The actual drawing title block specifies STEEL / ZINC PLATE, while the previously
retained catalog description says steel/nickel. The finish/version discrepancy
is still unresolved; this review establishes what this drawing states, not a
current production-lot finish or precedence over the retained catalog. The current
official4708 product page, read by the coordinator on2026-11-17, lists Steel,
Zinc & Clear Chromate,5.5mm outer diameter and M3 thread. This text observation
agrees with the drawing's zinc direction, while historical revision and lot
applicability remain unresolved. Its URL/date/text are retained without inventing
a raw HTML hash. The tool
rejects changing or waiving that discrepancy. Only the nut-dimensional source
gap is removed; no screw, washer or assembly qualification is implied.

The formula is `W + P <= L - G - N`, with W washer thickness, P required thread
protrusion, L screw length, G grip and N nut height. Interval arithmetic uses
`[Lmin - Gmax - Nmax, Lmax - Gmin - Nmin]`. The table fixes L and G at their
nominal source values solely for sensitivity and applies the drawing-verified nut range
2.15–2.65. It does not assign zero real screw or grip tolerance. Negative residuals
are preserved; a positive residual or zero boundary never yields assembly PASS.

Still unknown: exact screw identity and length tolerance; assembled grip tolerance
including compression; washer identity/thickness/tolerance; minimum required
protrusion; nut finish/version. The guaranteed maximum
washer thickness therefore remains null. In a later fully sourced analysis it
would be `Lmin - Gmax - Nmax - Pmin`, but this tool has no sourced Pmin or complete
extrema. Thread engagement, sleeve creep, strength and the rear envelope are not
qualified. The existing instruction to use a washer only where the screw comes
through the nut remains conditional; no washer size or omission is selected.

```sh
python3 -B scripts/checks/mc02_fastener_stack/audit.py
python3 -B scripts/checks/frozen_studies.py discover scripts/checks/mc02_fastener_stack
pnpm circuit:check
```

These are lightweight offline checks, with no native KiCad, placement search,
DRC, fill, source acquisition, vendor contact, ordering or hardware adoption.
Pre-edit component validation passed (84 manual inventory records, 445 declared
placements unverified, pin-asset check performed). Fixtures cover signed extrema,
unknowns, exact boundary, malformed inputs, source drift and improper finish/version
waivers despite verified dimensions. This independent audit does not regenerate canonical outputs.
