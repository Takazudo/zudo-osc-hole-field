# Stack connectors and posts: ST-01 evidence with the ST-01b and ST-01c addenda

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
| mms_fp | `samtec/mms/mms-1xx-02-xxx-sv-recommended-pcb-layout-rev-c.pdf` | C, 2016-03-08 | `7353dedb12b9d3ee2dbce18f442ba7542ac87ad48d4304aacd0f1ad6d33078e3` |
| clt_fp | `samtec/clt/clt-1xx-02-xx-d-recommended-pcb-layout-rev-j.pdf` | J, 2016-12-20 | `55368dafc562d29d1c0aaa02933cdeedc27fee0403cb53c40a9caecc1d05ab9f` |
| tw_th | `samtec/tw-th/tw-th-print-rev-bk.pdf` | BK | `bbb5eddb3f6094b50c5225662d788ef71afba4497cdfe703c29d964e5ff15ac9` |
| jso_cat / jso_print | `samtec/jso/jso-catalog-page-f-226.pdf` / `samtec/jso/jso-print-rev-t.pdf` | F-226 / T | `e9d1a8bb304bcfa65e83ebfff2470553bcf28feb2953421022047a256158a6e7` / `69035482287b2be080c950a2a0816f7c8a3c71ddf116c7264c00ba3e45bed5b1` |
| so_cat / so_print | `samtec/so/so-catalog-page-f-226.pdf` / `samtec/so/so-print-rev-az.pdf` | F-226 / AZ | `bad93640d61ebeccca24c14fa7f0c9c667666ac6db4d7b7808443a50879b08ce` / `e2b2dbce5baaac8618e8e05a9036d22370760496bf5e5aac139d475ce3861682` |
| harwin_r30_101 | `harwin/r30/r30-101xx02-m3-female-female-spacer-drg-01995-issue-7.pdf` | issue 7 | `3aaf7eaab650a65965a2b8baf20cfa591ee4d0f7260a56933eeace80da01c236` |
| harwin_r30_300 | `harwin/r30/r30-300xx02-m3-male-female-spacer-drg-01997-issue-22.pdf` | issue 22 | `ea476817a3dbc3d27a8d30f14360c075d1e03c48f702f5aaf17c397abb574ed3` |
| jlc_c | `distributor-captures/jlcpcb-lcsc/zudo-osc-hole-field-st-01c-20261114/SHA256SUMS` | capture 2026-11-14 | `fd82eeb7cc1fbb3f29f339e63cc98fea41ad4e1ccbc5a368df9cdd7991c93413` |

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

## NEEDS_DESIGN: Samtec documents pass-through for the −BE socket only, and the working code has no −BE

The tips stand 0.65 mm past the CLT socket face (7.85 − 7.2). What the documents show:

- **Layout (clt_fp revision J, sheet 5, fig 5).** The pattern is titled "CLT-110-02-XX-D-BE-A (BOTTOM ENTRY/PASS THROUGH)" and draws a 0.86 mm NPTH under each contact. The standard −D pattern (fig 1) has none.
- **Print (clt_print CT).** −BE is "same as fig 1 except insulator" (fig 6), with a 0.429 mm cut endwall (note 11). Table 1 lists the −L −D −BE contacts. Section A-A shows the contact cavities but neither dimensions nor notes an opening under the −D contact.
- **Suffixes.** −K is offered for 4 to 50 positions and −TR for 02 to 36. Neither excludes −BE.
- **Catalog (clt_cat).** Top entry needs at least 1.40 mm. Bottom entry needs at least 2.57 mm, "add board thickness". −BE is "required for bottom entry applications". Only the sister TLE socket states "pass-through" in words.
- **Pin fit.** The TW-SM pin is 0.51 mm square (tw_cw1), a 0.72 mm diagonal (CALCULATED), inside the 0.86 mm hole.
- **Characterization report (hsc).** It has only a fixture photograph (printed p. 23) and an undimensioned routing graphic (p. 25). It has no mated section.
- **Channel.** JLCPCB lists `CLT-104-02-L-D-BE-K-TR` as C6143646 (extended, stock 0) and ten other −BE variants.

Nearest valid codes, for the design authority; none is chosen here:

- `CLT-104-02-L-D-BE-K-TR`.
- `CLT-104-02-L-D-BE-TR`.
- `CLT-104-02-L-D-K-TR` as written, with pass-through undocumented.
- The D3 fallback of six short harnesses.

## Land patterns: the DA pad span and width hold, the row length is corrected

The full entries are in [`land-patterns.json`](land-patterns.json), in the frame of `design/stack/geometry/land-pattern.json`, with a 0.25 mm growth.

- **The pad span and width hold.** The 5.54 mm pad span and the 6.04 mm courtyard width are CONFIRMED (tw_fp sheet 3, fig 3).
- **The copper extent holds.** (n − 1) × 2.00 + 1.02 mm is correct as the copper extent along the row.
- **The courtyard length is corrected.** The body and drawn outline are n × 2.00 mm (± 0.25 mm), so the courtyard length is 2n + 0.75 mm: 6.75, 10.75 and 12.75 mm for 1×3, 1×5 and 1×6.
- **TW-SM double row 2×4.** Courtyard 8.07 × 8.75 mm.
- **MMS −SV copper is now SOURCED (ST-01c, mms_fp revision C).** Pads are 1.016 mm along the row and 2.085 mm across (DERIVED from the 5.44 mm span and 1.27 mm gap), staggered at 2.000 mm pitch. Each position has a 0.86 mm hole on the centreline marked "PASS THRU ONLY". Courtyard 5.94 × (2n + 1.19) mm: 7.19, 11.19 and 13.19 mm long. The width is 0.14 mm over the 5.8 mm planning envelope and inside the 6.04 mm stacker courtyard. The −SV tail span stays UNSOURCED.
- **CLT −D copper is now SOURCED (clt_fp revision J).** Standard pattern: pads 0.89 × 1.91 mm, span 5.92 mm, 2.000 mm pitch. The −BE pattern adds a 0.86 +0.05/−0 mm NPTH under each contact and shortens the pads to 1.40 mm, leaving a 0.13 mm web to the hole (DERIVED). Courtyard 6.42 × 8.70 mm.

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

## Posts: catalogue lengths exist at 17.0 mm (Harwin) and within 0.10 to 0.15 mm of 18.8 and 12.8 mm (Samtec)

The fitted class is mechanically fixed, conductive and threaded at both ends (DA-01 D4, D6). The full records are under `posts` in `candidates.json`. The Harwin files are `harwin/r30/r30-101xx02-…-issue-7.pdf` (`3aaf7eaa…c236`, F/F) and `…r30-300xx02-…-issue-22.pdf` (`ea476817…3ed5`, M/F). Samtec SO is `so-print-rev-az.pdf` (`e2b2dbce…1682`) and JSO is `jso-print-rev-t.pdf` (`69035482…d5b1`).

| Gap | Part | Length (mm) | Tolerance | Offset | Insertion if gap = length (margin) |
| --- | --- | --- | --- | --- | --- |
| 17.0 | Harwin R30-1011702, M3 F/F, A/F 5.30–5.50 | 17.00 | ±0.15 | 0 | 2.866 (−0.74/+1.45) |
| 17.0 | Harwin R30-3001702, M3 M/F, A/F 4.8–5.0 | 17.00 | ±0.15 | 0 | 2.866 |
| 17.0 | Samtec SO-1715-05 (F/F) / -03 (M/F), M3, hex 4.76 | 17.15 REF | not stated | +0.15 | 2.716 (−0.59/+1.60) |
| 17.0 | Samtec JSO-1715 jack screw | 17.15 | ±0.05 | +0.15 | 2.716 |
| 18.8 | Samtec SO-1890-05 / -03 | 18.90 REF | not stated | +0.10 | 2.946 (−0.82/+1.37) |
| 18.8 | Samtec JSO-1865 jack screw | 18.65 | ±0.05 | −0.15 | 3.196 (−1.07/+1.12) |
| 18.8 | Harwin R30-1011902 / R30-1011802 | 19.00 / 18.00 | ±0.15 | +0.20 / −0.80 | 2.846 / 3.846 |
| 12.8 | Samtec JSO-1265 jack screw | 12.65 | ±0.05 | −0.15 | 3.706 (−1.58/+0.61) |
| 12.8 | Harwin R30-1011302 / R30-1011202 | 13.00 / 12.00 | ±0.15 / ±0.10 | +0.20 / −0.80 | 3.356 / 4.356 (outside the window) |
| 12.8 | Samtec SO-1315-05 (also -1215) | 13.15 REF | not stated | +0.35 | 3.206 |

What the drawings state, by maker:

- **Harwin.** Brass CW614N (CuZn39Pb3), nickel finish, M3 × 0.5-6H.
- **Samtec SO.** 6061 aluminium or 303 stainless with no plating stated; #4-40, M3 or M2 thread. Its "C" length is REF, and note 13 says standoffs are made 0.15 mm longer than the connector stack.
- **Samtec JSO.** Stainless steel; jack-screw thread size not printed. It is listed for SEAX, LPAX and LSHM only (not MMS), and its travel is not stated.
- **Ratings, all three.** No maker states a current rating or contact resistance.

Closing the gaps:

- **No shim or washer.** No catalogue shim or washer with a thickness tolerance was retained. Closing an offset needs a part made to drawing (no print) or a change of gap.
- **The D3 "A" rule ties shorter posts.** With the D3 stacker heights fixed, the body clearance is gap − 4.50 − "A". It is 0.04 mm at 18.00 mm and negative at 12.00 mm.

## Press-fit threaded elements: only Samtec's press-in standoffs are SOURCED, with no push-out or torque-out figure

- **SO −04 press-in female element (so_print sheet 4).** Knurl 4.42 ± 0.05 mm, board cutout 4.24 ± 0.08 mm, keep-out 8.44 ± 0.13 mm, heights 1.65 to 3.18 mm. Material 304 stainless is offered for −04 only.
- **SO −01 press-in (sheet 1).** Cutout 4.50 ± 0.08 mm; offered from 5.15 to 8.65 mm only.
- **JSO −01 press-in base.** Cutout 6.35 mm with an 8.00 mm keep-out.
- **Board thickness.** All Samtec standoffs need boards of at least 1.57 mm. Threaded options take boards up to 3.16 mm.
- **Not stated.** No push-out, torque-out, current or contact-resistance figure appears on any of these documents.
- **Würth REDCUBE press-fit.** `we-online.com` datasheet and product page returned HTTP 403.
- **PEM broaching standoffs.** The fetch was refused by the session's permission layer.
- **Keystone swage standoffs.** Only aggregator pages were found. All three remain UNSOURCED.

## Jack-screw standoffs: Samtec JSO is SOURCED; no other maker was reached

The specification recommends jack-screw standoffs for multi-connector mates (spec p. 7, §5.8). The JSO series covers −0400 to −1865 and −3500, with "A" ± 0.05 mm. It is fixed by a press-in base or a threaded base with a nut, torqued to 2.5 to 3.5 in·lb. The JSOM is named on the SO catalogue page for 15.24 mm only; its print was not fetched. Other makers were not surveyed.

## The through-hole stacker print is retained but not needed by D3

TW-TH print revision BK (`samtec/tw-th/tw-th-print-rev-bk.pdf`, `bbb5eddb…5ac9`) is retained. Its only figure noted here is the 1 lb minimum push-out force. EL uses the surface-mount stacker in D3.

## Still not located: the MMS −SV tail span, and the Würth, PEM and Keystone press-fit data

- **MMS −SV tail span:** not dimensioned on print CZ or on layout revision C.
- **Press-fit data:** the Würth, PEM and Keystone routes are listed in the press-fit section above.
