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

The nut input **2.40 +/-0.25 mm is UNVERIFIED_HANDOFF**, not a manufacturer fact
verified by this tool. Exact PDF bytes were unavailable to this task. The handoff comment URL, official URL, reported drawing revision and expected
PDF SHA-256 are retained in `evidence.json`; `verified_pdf_sha256` remains null.
The expected hash is a handoff claim, not a digest of bytes inspected by this task. The reported steel/zinc
handoff conflicts with the retained steel/nickel catalog description; that
version discrepancy remains unresolved. The tool refuses silently promoting the
handoff or changing its identity/dimensions. A later actual primary-source review
must explicitly revise this separate record, not reinterpret this output.

The formula is `W + P <= L - G - N`, with W washer thickness, P required thread
protrusion, L screw length, G grip and N nut height. Interval arithmetic uses
`[Lmin - Gmax - Nmax, Lmax - Gmin - Nmin]`. The table fixes L and G at their
nominal source values solely for sensitivity and applies the handoff nut range
2.15–2.65. It does not assign zero real screw or grip tolerance. Negative residuals
are preserved; a positive residual or zero boundary never yields assembly PASS.

Still unknown: exact screw identity and length tolerance; assembled grip tolerance
including compression; washer identity/thickness/tolerance; minimum required
protrusion; verified nut dimensions; nut finish/version. The guaranteed maximum
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
unknowns, exact boundary, malformed inputs, source drift and false handoff
promotion. This independent audit does not regenerate canonical outputs.
