# Stack connectors and posts: ST-01 evidence with the ST-01b addendum

Task `osc-stack-20261114/ST-01b`, 2026-11-14, built on DA-01 decision D3. Nothing here is selected, validated or qualified. Fit, force and alignment are NOT RUN because no specimen exists. The machine-readable records are [`candidates.json`](candidates.json) and [`land-patterns.json`](land-patterns.json). Vendor files are in the private `Takazudo/circuit-dev-resources` store (branch `claude/project-thread-zao1qg`), cited by path and SHA-256.

Status words: **SOURCED** (a retained document states it), **UNSOURCED** (none does), **CALCULATED** or **DERIVED** (arithmetic or a stated rule on SOURCED figures) and **NEEDS_DESIGN** (the documents leave a decision open).

## Sources used in this addendum

| Key | File (circuit-dev-resources) | Revision | SHA-256 |
| --- | --- | --- | --- |
| spec | `samtec/mms/mms-tmm-product-specification-rev-a-2022-08-15.pdf` | A, 2022-08-15 | `f7cc75253302d6b4d6a48469f1841f095a4ff2f4e2b9c9a12f9dd0796024ee10` |
| mms_print | `samtec/mms/mms-1xx-02-smt-print-rev-cz.pdf` | CZ | `d19c85659d2712ed67ad31b5d9f251b4d0556da84de3ad9e1dfd7ff8c67e2130` |
| mms_cat | `samtec/mms/mms-catalog-page-f-226-pdf-2025-10-20.pdf` | F-226 | `8500181e673b139b5615b470c6338117194451c0e07a300ff76b7d592e06d531` |
| tw_cw1 | `samtec/tw-sm/tw-sm-print-sheet-1-rev-cw.pdf` | CW | `7eab7b79b8025486771214a79014a619487402916a0da61f143341faefde9e17` |
| tw_cw2 | `samtec/tw-sm/tw-sm-print-sheet-2-rev-cw.pdf` | CW | `774e1f325e40636ed2731ef6f66a6a1dc07ee8da97d48a8fd1696ffc77112d53` |
| tw_da | `samtec/tw-sm/tw-sm-print-rev-da.pdf` | DA | `5ebc9747de16c3e22064cd311cd5df98b331248a69685112900a9ced8a091a61` |
| tw_fp | `samtec/tw-sm/tw-recommended-pcb-layout-rev-c.pdf` | C | `ab03319ec45dbfc53789f17286e63477745c8bb85eea27c6f75c04c6258ee8d0` |
| clt_print | `samtec/clt/clt-1xx-02-xx-d-print-rev-ct.pdf` | CT | `0f2251dfcf25fb80a1f29209bce3a8cf8170c51c4ab75c6faee32055b343c6ef` |
| clt_cat | `samtec/clt/tle-clt-catalog-page-f-226-rev-22dec25.pdf` | 22DEC25 | `6e62ac4a63718ae9e00ca477108d94d433f068b881eebfd4b5b790042bc3201c` |
| smm_cat | `samtec/smm/smm-catalog-page-f-226-pdf-2025-10-21.pdf` | F-226 | `c1ac1129e007eb08e742f94efe0f56245c3a852e7fd3bed6b36039249f0d81cb` |
| qual | `samtec/test-reports/mms-tmm-design-qualification-154341-rev-2.pdf` | 154341 rev 2 | `02fd7a450b4eebd3b7666cc1751a57e48238d5c6f25d3c90047afe59dd740690` |
| hsc | `samtec/test-reports/tw-clt-18mm-high-speed-characterization-2006-01-30.pdf` | 2006-01-30 | `4d104d5de3026b7af19b4780405beb64d9c1c0f520662cdaa07a685a06d9d137` |
| jlc | `distributor-captures/jlcpcb-lcsc/zudo-osc-hole-field-st-01b-20261114/SHA256SUMS` | capture 2026-11-14 | `174f3c90c5b170f666c61cc248b0ee33cec3cd37a3ee903cd4d50507bf5e3e06` |

The other DA-01 files (`mmx-mated-views-rev-c.pdf`, `mms-tmmh-design-qualification-187548-rev-1.pdf`) are retained but not cited for a figure.

## Working pair: MMS −02 −SV socket with TW-SM stacker (DA-01 D3, NOT SELECTED)

The socket is MMS-1nn-02-L-SV on the front board's B.Cu. The stacker is TW-nn-LL-L-S-AAA-SM on K's F.Cu. Each catalog page lists the other as its mate (mms_cat, F-226).

## SMM is demoted: its 0.20 mm window cannot give three gaps from one family (DA-01 C1)

The SMM insertion window is 3.05 to 3.25 mm (smm_cat, F-226). Each TW-SM lead style therefore serves one 0.2 mm band of gap, so no lead-style set gives gaps 4.2 and 6.0 mm apart. The ST-01 claim "`h` ≥ 7.874 mm" is withdrawn (C2). The ST-01 record is kept under `demoted` in `candidates.json`. CLP with FW-SM stays a fallback of last resort.

## MMS is no longer excluded (DA-01 C3)

The MMS body height is fixed, but the gap is set by the ordered TW-SM height, so the ST-01 "fixed-height" exclusion does not apply to it.

## Gap = pin tip + socket seated height − insertion

| Term | Value | Status and locator |
| --- | --- | --- |
| MMS −SV seated height | 4.496 +0.102/−0.051 mm | SOURCED, mms_print sheet 1, −SV side view |
| MMS −SV top-entry insertion | 2.13 to 4.32 mm | SOURCED, mms_cat |
| SMM insertion | 3.05 to 3.25 mm | SOURCED, smm_cat |
| CLT top-entry insertion | 1.40 mm minimum | SOURCED, clt_cat |
| TW-SM pin tip (maximum "A", "B" = 0) | −02 7.85; −09 9.86; −03 11.86; −04 12.37; −06 15.37; −07 17.35 mm | SOURCED, tw_cw1 sheet 1, table 1 |
| Stacker "A" | from .170 in in .005 in steps, ± .005 in | SOURCED, tw_cw1 figure 1, note 8 |
| "B" | tip − "A" | DERIVED |
| "A" rule | "A" ≤ gap − 4.50 − 0.80 mm, rounded down to 0.005 in | DA-01 D3 |

The method reproduces the published 18 mm TW + CLT stack (hsc, title page).

## Misalignment limits are SOURCED for the MMS socket only

| Limit | Along the row (X) | Across the row (Y) | Locator |
| --- | --- | --- | --- |
| Initial linear | 0.39 mm | 0.57 mm (−SV); 0.37 mm (−DV) | spec p. 4, §5.1.1, table 1 |
| Final linear | 0.07 mm | 0.16 mm (single); 0.07 mm (double) | spec p. 4, §5.1.2, table 5 |
| Initial angular | X 8.0° (−SV) | Y 4.5°, Z 2.0° (2–10 positions) | spec p. 5 |
| Final angular | X 3.0° (−SV) | Y 2.1°, Z 1.0° (2–10 positions) | spec p. 5 |

## Forces are about 0.7 to 1.0 N per position new and up to 1.33 N after 100 cycles

These forces were measured on MMS with TMM, not with TW-SM (qual). The MMS contact is the same, so these are the closest SOURCED figures.

| Measurement | Total | Per position (CALCULATED) | Locator |
| --- | --- | --- | --- |
| Mating, 80 positions, new | 12.77–15.03 lb | 0.71–0.84 N | qual printed p. 15 |
| Mating, 80 positions, after 100 cycles | 16.35–23.83 lb | 0.91–1.33 N | p. 15 |
| Unmating, 80 positions, new | 8.37–10.34 lb | 0.47–0.57 N | p. 15 |
| Unmating, 80 positions, after 100 cycles | 14.41–17.66 lb | 0.80–0.98 N | p. 15 |
| Mating, 50 positions, new | 7.98–10.87 lb | 0.71–0.97 N | p. 16 |

The product specification also gives these ratings (spec p. 2):

- Normal force: 30 g minimum.
- Contact resistance change: 15 mΩ maximum.
- Current: 3.9 A with one pin powered per row.
- Durability: 500 cycles with S plating.

## Every D3 working code is CONFIRMED against the prints; the margins match D3

| Code | Gap (mm) | "A" (in) | Insertion (mm) | Margin (mm) | Supply / note |
| --- | --- | --- | --- | --- | --- |
| MMS-105-02-L-SV-K-TR | — | — | — | — | −K from 3 positions, −TR 2–36 (mms_print sheet 1, sheet 3 fig 6) |
| MMS-103-02-L-SV-K-TR | — | — | — | — | −K at its 3-position minimum |
| MMS-106-02-L-SV-K-TR | — | — | — | — | same |
| TW-05-03-L-S-295-SM | 12.8 | .295 | 3.556 | −1.43 / +0.76 | tube |
| TW-03-06-L-S-460-SM | 17.0 | .460 | 2.866 | −0.74 / +1.45 | bulk (note 6); no −P below 4 positions (note 10) |
| TW-06-06-L-S-460-SM | 17.0 | .460 | 2.866 | −0.74 / +1.45 | tube |
| TW-06-07-L-S-530-SM | 18.8 | .530 | 3.046 | −0.92 / +1.27 | tube; −07 not on tape and reel |
| TW-03-07-L-S-530-SM | 18.8 | .530 | 3.046 | −0.92 / +1.27 | bulk; no pad |
| Shallow: TW-x-02-L-S-180-SM | 9.885 | .180 | 2.461 | −0.33 / +1.86 | note 8 repress |
| Shallow: TW-x-04-L-S-345-SM | 14.085 | .345 | 2.781 | −0.65 / +1.54 | — |
| Shallow: TW-x-06-L-S-415-SM | 15.885 | .415 | 3.981 | −1.85 / +0.34 | — |
| TW-04-02-L-D-170-SM-P-TR | 7.2 | .170 | 2.94 into CLT | +1.54 over 1.40 minimum | note 8 repress; −P with "B" = 3.53 ≥ 1.91 |
| CLT-104-02-L-D-K-TR | 7.2 | — | 2.94 | open upward | −K 4–50 positions, −TR 02–36 (clt_print) |

How to read the margin column:

- Each margin is measured against the 2.13 to 4.32 mm window.
- Each "A" value is the result of the D3 rule.
- No stacker passes the pin-tip maximum of its lead style.
- None of the 1×3 stackers can take a pick-and-place pad (−P covers 4 to 36 positions only), so their placement stays UNSOURCED.

## NEEDS_DESIGN: print CT does not state that the EL socket lets the pin pass through

The tips stand 0.65 mm past the CLT socket face (7.85 − 7.2). Neither sheet of print CT states that a top-entry pin may pass through the −D insulator. These are the nearest options; none is chosen here:

- `CLT-104-02-L-D-K-TR` as written, with pass-through UNSOURCED.
- The −BE bottom-entry insulator listed on print CT. Its suffix compatibility with −K has not been checked.
- The D3 fallback of six short harnesses.

## Land patterns: the DA pad span and width hold, the row length is corrected

The full entries are in [`land-patterns.json`](land-patterns.json), in the frame of `design/stack/geometry/land-pattern.json`, with a 0.25 mm growth.

- **The pad span and width hold.** The 5.54 mm pad span and the 6.04 mm courtyard width are CONFIRMED (tw_fp sheet 3, fig 3).
- **The copper extent holds.** (n − 1) × 2.00 + 1.02 mm is correct as the copper extent along the row.
- **The courtyard length is corrected.** The body and drawn outline are n × 2.00 mm (± 0.25 mm), so the courtyard length is 2n + 0.75 mm: 6.75, 10.75 and 12.75 mm for 1×3, 1×5 and 1×6.
- **TW-SM double row 2×4.** Courtyard 8.07 × 8.75 mm.
- **MMS −SV and CLT copper patterns are UNSOURCED.** The MMS courtyard is not derived; the planning fallback of 5.8 × (2n + 1) mm still holds. The CLT body gives a lower bound of 5.9 × 8.7 mm.

## The factory channel lists the three sockets, the CLT and two stackers; the K-joint stackers are not listed

| Code | JLCPCB | Library | Stock | Minimum order |
| --- | --- | --- | --- | --- |
| MMS-105-02-L-SV-K-TR | C3323733 | extended | 10 | 1 |
| MMS-103-02-L-SV-K-TR | C5799438 | extended | 0 | 3 |
| MMS-106-02-L-SV-K-TR | C6991117 | extended | 0 | 2 |
| CLT-104-02-L-D-K-TR | C3322261 | extended | 0 | 7 |
| TW-04-02-L-D-170-SM-P-TR | C20387359 | extended | 0 | 2 |
| TW-05-02-L-S-180-SM (shallow) | C20388456 | extended | 0 | 3 |

- **Not listed:** TW-05-03-L-S-295-SM, TW-03-06-L-S-460-SM, TW-06-06-L-S-460-SM, TW-06-07-L-S-530-SM, TW-03-07-L-S-530-SM, TW-03/06-04-L-S-345-SM and TW-03/06-06-L-S-415-SM.
- **Package:** every listing reads "SMD,P=2mm".
- **Captures:** stored under jlc. LCSC was seen only through each listing's `lcscGoodsUrl`.
- **Evidence status:** a listing is distributor identity, not manufacturer evidence.

## Post survey is PARTIAL: only the manufacturer's standoff advice is SOURCED

- **SOURCED.** The product specification recommends standoffs, and jack-screw standoffs for mates of several connectors (spec p. 7, §5.8).
- **UNSOURCED.** The threaded post at 12.8, 17.0 and 18.8 mm has no retained print, so its thread, across-flats, material, plating and tolerance are all UNSOURCED. The jack-screw standoff class is also UNSOURCED.
- **Refused.** Reflowed SMT spacers are refused by DA-01 D4. They were not surveyed again; the ST-01 record stays in `candidates.json`.

## Sources not located: the MMS and CLT land patterns and the TW-TH print

- **MMS land pattern:** the MMS product page links no footprint. The −SV tail span is not dimensioned on print CZ.
- **CLT land pattern:** the CLT product page gives no layout link, so the relief holes are not dimensioned.
- **TW-TH print:** no link was found, so it was not fetched.
