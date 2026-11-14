# Stack connectors and spacers: ST-01 evidence

Task `osc-stack-20261114/ST-01@b4daa754`, 2026-11-14. This is an evidence draft for the design authority (Gate A). No part is selected, and nothing here is validated or qualified. The full requirement-by-requirement matrix with sources, locators and calculations is [`candidates.json`](candidates.json). Retained documents are in the private `Takazudo/circuit-dev-resources` store (branch `claude/project-thread-zao1qg`) and are cited by path and SHA-256.

Status words: **SOURCED** means a retained document states it. **UNSOURCED** means no retained document states it, even when a distributor listing or an unretained page was observed. **CALCULATED** means arithmetic on SOURCED values; it is not a manufacturer statement.

## NEEDS DESIGN: no surveyed family reaches the fixed 7.2 mm EL-to-P gap

The 2.00 mm Samtec pair has a deterministic lower bound of 7.874 mm (minimum SMT stacker height 4.32 mm plus SMM socket height 3.56 mm), which is 0.674 mm above 7.2 mm. The 1.27 mm Samtec FW-SM catalog range starts at 7.67 mm mated. It reaches 7.165 or 7.292 mm only through "smaller stack heights" that the catalog says are available on request to Samtec. That request is an outward action and was not made. The planning adapter gap `h` = 6.9 mm is also out of reach. Any `h` of 7.874 mm or more works for the three gaps to K.

## The adapter gap h must be at least 7.874 mm for the recommended family

| Family | Lowest `h` | Steps | Example set: `h`, `h+4.2`, `h+6.0` (stacker code to mated mm) | 7.2 mm EL to P |
| --- | --- | --- | --- | --- |
| A. Samtec SMM + TW-SM, 2.00 mm, single row | 7.874 (lower bound) | 0.127 mm (0.005 in) | -170 to 7.874; -335 to 12.065; -405 to 13.843 | Not possible |
| B. Samtec CLP + FW-SM, 1.27 mm, double row | 7.67 (catalog) | 0.127 mm | -215 (lead -03) to 7.673; -380 (lead -05) to 11.864; -450 (-05) to 13.642 | Non-standard only (-195 to 7.165) |

Family A arithmetic assumes the two insulators touch when the joint is fully mated. Samtec states no TW-SM plus SMM mated-height formula on the retained pages, so the A values are lower bounds. Family B uses Samtec's own mated-height table (stacker height + 2.21 mm with CLP -02 and a 0.065 in post), so it is better sourced. Which TW lead style is valid for each stacker height is unsourced.

## Recommendation: Samtec SMM sockets with TW-SM stackers; fallback Samtec CLP with FW-SM

**Recommended pair family: Samtec SMM-1nn-02-L-S socket with TW-nn-LL-L-S-HHH-SM stacker.** It is recommended on condition that the design authority sets `h` ≥ 7.874 mm and resolves the 7.2 mm EL-to-P gap. Four facts decide it:

1. It is the only surveyed family with both halves SMT in a single 2.00 mm row, so the GH pin order carries over one for one.
2. The stacker height is ordered in 0.13 mm steps from 4.32 mm. One stacker family therefore gives all three gaps to K.
3. The socket has a retained Samtec print (revision BM) with forces: insertion 3.0 oz maximum, withdrawal 0.4 oz minimum, 100 cycles with 10 µin gold. The catalog ratings are 3.3 A per pin (SMM) and 3.9 A per pin (TW), both with 2 pins powered, against a 0.3 to 0.8 A return share.
4. The socket fits every GH courtyard on retained dimensions: n × 2.00 mm long and a 4.32 mm REF tail span. The JLCPCB parts channel lists the exact 1x3, 1x5 and 1x6 sockets.

**Fallback: Samtec CLP-1nn-02-L-D socket with FW-nn-LL-L-D-SSS-065-SM stacker (1.27 mm, double row).** It has the only retained manufacturer mated-height table. Its catalog offers smaller stack heights, the only route to 7.2 mm. Its 2x2 and 2x3 bodies fit every GH courtyard. The costs: the pin map must be re-cut onto two rows, the CLP documents are unavailable, and the 1.27 mm robustness and misalignment figures are unsourced.

## Comparison: misalignment and contact resistance are unsourced for every candidate

| Requirement | A. SMM + TW-SM | B. CLP + FW-SM | Harwin M22 (excluded) |
| --- | --- | --- | --- |
| 1. Courtyard inside GH | Socket SOURCED (n × 2.00 × 4.32 REF); stacker tail span UNSOURCED | Stacker body SOURCED (n × 1.27 × 3.42); socket UNSOURCED | — |
| 2. Both halves SMT | SOURCED | Stacker SOURCED; socket by listing only | No single-row straight SMT plug (SOURCED) |
| 3. Heights 7.2 / h / h+4.2 / h+6.0 | h ≥ 7.874 CALCULATED; 7.2 not possible | h ≥ 7.67 from table; 7.2 non-standard only | Fixed heights |
| 4. Current / contact resistance | 3.3 A and 3.9 A (2 pins powered) SOURCED; resistance UNSOURCED | Both UNSOURCED | 2 A, 20 mΩ max SOURCED |
| 5. Misalignment / forces / cycles | Misalignment UNSOURCED; socket forces and 100 cycles SOURCED | All UNSOURCED | 2.0 N / 0.2 N, 300 cycles SOURCED |
| 6. Pick and place on 1x3; stable reflow; through-hole soldering on same face | Socket -K pad SOURCED; TW-SM -P is 04-36 positions only, so the 1x3 stacker has no pad; -A peg double row only; reflow and through-hole compatibility UNSOURCED | -P needs 5 per row, so no pad; -A peg from 3 positions SOURCED; rest UNSOURCED | — |
| 7. Factory channel (JLCPCB, 2026-11-14) | Sockets listed (C6489678, C6229351, C6229379), stock 0; the stack's exact stacker heights are not listed | Sockets listed with stock (C5572843: 40); stacker heights not listed | — |

Other families were excluded on retained or observed grounds:

- Samtec TMM-SM, MMS, FTS and SFM/TFM have fixed heights, and the CLT socket is double row only.
- Würth WR-PHD 2.00 mm has no single-row SMT socket. This was observed on the catalog page; the bytes were refused.
- The factory-channel hanxia PM2.0/PZ2.0 TP-YQ parts have fixed heights (4 mm and 3.8 mm in the listing), and no drawing could be retrieved.

## Spacers: no retained reflowed SMT spacer reaches 11 mm or fits a 4 × 4 mm land

- **Keystone SMT threaded metric standoffs** (retained manufacturer page, LCSC-hosted copy): M3, 2 to 10 mm, 5.56 mm outside diameter, 6.2 mm solder pad, steel with tin plate. They are too short, and the pad is wider than the land.
- **Würth WA-SMSI M2.5**: UNSOURCED, because we-online.com refused the download. The catalog page showed heights up to 10 mm in 0.5 mm steps plus 12.5 mm, with a 5.1 mm outside diameter. JLCPCB lists 9774100151R (C5367370) but not the 12.5 mm part.
- **PEM SMTSO**: UNSOURCED, because pemnet.com served a WAF challenge. The catalog listing showed 2 to 10 mm.
- **Mechanically fixed posts** (hex standoffs, swage or press-fit): UNSOURCED. No primary document was retained.
- **Torque, pull-out, resistance and current**: no retained figure for any spacer.

ST-04 should plan on mechanically fixed posts. They keep the rule that no solder joint is in the load path, so no exception is needed.

## Open items per candidate

- **A (SMM + TW-SM):**
  - The 7.2 mm gap is not possible with this family.
  - The mated-height statement, contact resistance and misalignment need Samtec's specification, test report and stack-height data, which returned 403.
  - The 1x3 stacker has no pick-and-place pad, and the single row has no locating peg. Factory placement and tall-stacker reflow stability are open.
  - The valid lead style for each height is open.
  - The recommended land patterns were not retained.
  - The stacker heights the stack needs are not stocked in the factory channel.
- **B (CLP + FW-SM):**
  - The CLP catalog and print are unavailable.
  - The pin map must be re-cut onto two rows.
  - The 2- and 3-per-row stackers have no pick-and-place pad.
  - Current, resistance, forces, cycles and misalignment are unsourced.
  - 7.2 mm needs a non-standard height.
- **Spacers:**
  - No primary document has been retained for a mechanically fixed post.
  - Every retained SMT spacer needs a land larger than 4 × 4 mm.

## Checks: candidate bundle NOT RUN because pin maps require KiCad assets

The evidence contract requires a pin map for every inventory record. With CAD enabled, `pnpm circuit:check` requires that each pin map's KiCad symbol and footprint exist in the project libraries (`cad.py`, pin-asset check). The brief excludes new symbols and footprints, and no existing asset matches these parts. The group bundle `component-stack-interconnect-candidates` was therefore not created, and no inventory, routing or publication line was added. `pnpm circuit:check`, `pnpm circuit:generate` and `pnpm check` were run on the unchanged evidence set.
