# Fixing list of the flat-link stack (ST-08 attempt a1, part 1)

Task `osc-stack-20261114/ST-08 a1 part 1`, ruling DS-66 (`reviews/da-03.md`, Continuation c1, G8). **Status: generated paper list on unvalidated drafts.** Every figure is a courtyard-level screen of the board files; nothing is a copper clearance, a DRC, a fit, a strength or a strain result, and nothing is adopted. Coordinates are in the panel frame (`placements.lock.json`: origin at the panel's top-left, y down); K and the front boards share it, and the KiCad file coordinates add (100, 50).

- [`fixing-sites.json`](fixing-sites.json): every fixing of K with kind, coordinates, boards, keep-out radii, part moves and status, the screened candidates, the selection and its alternatives, and the SHA256 of every input.
- `scripts/stack/fixings/fixings.py` writes both files; `fixings_check.py` is the checker; `test_fixings.py` holds the tests (`python3 scripts/checks/frozen_studies.py discover scripts/stack/fixings`).

Regenerate with `python3 scripts/stack/fixings/fixings.py`; `--check` fails when a retained file differs from a fresh run.

## NEEDS_DESIGN: no site list meets both rules without moving locked panel hardware; the best reaches 93.6 mm, not 90 mm

The 70 mm rule is met everywhere. The 90 mm rule fails at 55 grid nodes in 2 clusters; the worst is (4, 247), 93.61 mm from a fixing. No node of the 1 mm site screen within 90 mm of it is clear of locked panel hardware on P. 4 of the four P-side sleeve sites of DS-45 stand on locked pots themselves. No selection from the clear nodes of the screen can do better than 93.30 mm.

| Result | Value |
| --- | --- |
| Sleeve sites that go | 10 of 12: JL-SUP-2, JL-SUP-3, JR-SUP-2, JR-SUP-3, K-SUP-3, K-SUP-4, K-SUP-5, K-SUP-6, K-SUP-7, K-SUP-8 |
| Sleeve sites kept | JL-SUP-1 (6.5, 22.5), JR-SUP-1 (311.5, 22.5) |
| Sleeve sites added | SLV-U1 (159, 38) on JL, SLV-L2 (244, 230) on P, SLV-L1 (93, 276) on P |
| Farthest point of K from a fixing, 18 posts only | 156.2 mm at (4, 8) |
| Farthest point, the 30 present fixings | 153.2 mm at (159, 8) |
| Farthest point, this list | 93.6 mm at (4, 247) |
| Sleeves per length | 3 long (19.0 mm gap), 2 short (17.0 mm gap) |
| Delivered plate (10 long, 6 short) | covers the list |
| Checker findings on the retained list | [coverage] farthest node [4.0, 247.0] is 93.606 mm from a fixing |

## Inventory: 18 posts and 12 sleeve sites; 10 sleeve sites stand within 70 mm of another present fixing

Posts from `design/stack/power-posts/joint-design.json` (the DS-44 lands govern; `stack-candidate.json` still holds the four JR lands 0.5 mm off). Sleeve sites from `stack-candidate.json` `fixings` (kind "kept support"). The front-board coordinates equal the K coordinates for every fixing. Nearest other fixing among the 30.

| Fixing | Kind | On K and on the front board | Front board | Gap, mm | Nearest other fixing | mm |
| --- | --- | --- | --- | --- | --- | --- |
| POWER-JL-+12V | post | (40, 160) | JL | 19.0 | POWER-JL--12V | 17.00 |
| POWER-JL--12V | post | (57, 160) | JL | 19.0 | POWER-JL-+12V | 17.00 |
| POWER-JL-+5V | post | (74, 160) | JL | 19.0 | POWER-JL--12V | 17.00 |
| POWER-JL-AGND1 | post | (91, 160) | JL | 19.0 | POWER-P-AGND2 | 16.77 |
| POWER-JL-AGND2 | post | (108, 160) | JL | 19.0 | POWER-P-AGND3 | 14.64 |
| POWER-JL-AGND3 | post | (125, 160) | JL | 19.0 | POWER-JL-AGND2 | 17.00 |
| POWER-JR-+12V | post | (193, 160) | JR | 19.0 | POWER-P-AGND1 | 15.00 |
| POWER-JR--12V | post | (210, 160) | JR | 19.0 | POWER-JR-+12V | 17.00 |
| POWER-JR-+5V | post | (227.5, 160) | JR | 19.0 | POWER-JR-AGND1 | 17.00 |
| POWER-JR-AGND1 | post | (244.5, 160) | JR | 19.0 | POWER-JR-+5V | 17.00 |
| POWER-JR-AGND2 | post | (261.5, 160) | JR | 19.0 | POWER-JR-AGND1 | 17.00 |
| POWER-JR-AGND3 | post | (278.5, 160) | JR | 19.0 | POWER-JR-AGND2 | 17.00 |
| POWER-P-+12V | post | (142, 175) | P | 17.0 | POWER-P--12V | 17.00 |
| POWER-P--12V | post | (159, 175) | P | 17.0 | POWER-P-+12V | 17.00 |
| POWER-P-+5V | post | (176, 175) | P | 17.0 | POWER-P--12V | 17.00 |
| POWER-P-AGND1 | post | (193, 175) | P | 17.0 | POWER-JR-+12V | 15.00 |
| POWER-P-AGND2 | post | (98.5, 175) | P | 17.0 | POWER-P-AGND3 | 11.51 |
| POWER-P-AGND3 | post | (110, 174.5) | P | 17.0 | POWER-P-AGND2 | 11.51 |
| JL-SUP-1 | sleeve | (6.5, 22.5) | JL | 19.0 | JL-SUP-2 | 57.50 |
| JL-SUP-2 | sleeve | (6.5, 80) | JL | 19.0 | JL-SUP-1 | 57.50 |
| JL-SUP-3 | sleeve | (6.5, 138) | JL | 19.0 | K-SUP-3 | 22.00 |
| JR-SUP-1 | sleeve | (311.5, 22.5) | JR | 19.0 | JR-SUP-2 | 57.50 |
| JR-SUP-2 | sleeve | (311.5, 80) | JR | 19.0 | JR-SUP-1 | 57.50 |
| JR-SUP-3 | sleeve | (311.5, 138) | JR | 19.0 | K-SUP-4 | 22.00 |
| K-SUP-3 | sleeve | (6.5, 160) | JL | 19.0 | JL-SUP-3 | 22.00 |
| K-SUP-4 | sleeve | (311.5, 160) | JR | 19.0 | JR-SUP-3 | 22.00 |
| K-SUP-5 | sleeve | (6.5, 243) | P | 17.0 | K-SUP-7 | 46.50 |
| K-SUP-6 | sleeve | (311.5, 243) | P | 17.0 | K-SUP-8 | 72.79 |
| K-SUP-7 | sleeve | (6.5, 289.5) | P | 17.0 | K-SUP-5 | 46.50 |
| K-SUP-8 | sleeve | (255.5, 289.5) | P | 17.0 | K-SUP-6 | 72.79 |

## 70 mm rule: 10 of the 12 sleeve sites go; JL-SUP-1 and JR-SUP-1 stay

The four named sites go by DS-66. A given site that stands on locked panel hardware or on a fixed hole cannot be kept, because no jack, pot, switch or LED moves; this removes K-SUP-5, K-SUP-6, K-SUP-7, K-SUP-8. The panel-side test is ST-04's: the locked courtyard against the 3.0 mm radius of an M3 head without washer, and the locked part's rear-face pads against the 3.75 mm keep-out (DS-44 accepted the same screen at the JR lands).

| Site | Kind | Status | Nearest other fixing of this list | mm |
| --- | --- | --- | --- | --- |
| JL-SUP-1 | sleeve kept | kept under DS-66: no other fixing within 70 mm | POWER-JL-+12V | 141.52 |
| JL-SUP-2 | sleeve dropped | dropped by DS-66 (pair choice of ST-08) | JL-SUP-1 | 57.50 |
| JL-SUP-3 | sleeve dropped | dropped by DS-66 (named) | POWER-JL-+12V | 40.08 |
| JR-SUP-1 | sleeve kept | kept under DS-66: no other fixing within 70 mm | POWER-JR-AGND3 | 141.41 |
| JR-SUP-2 | sleeve dropped | dropped by DS-66 (pair choice of ST-08) | JR-SUP-1 | 57.50 |
| JR-SUP-3 | sleeve dropped | dropped by DS-66 (named) | POWER-JR-AGND3 | 39.66 |
| K-SUP-3 | sleeve dropped | dropped by DS-66 (named) | POWER-JL-+12V | 33.50 |
| K-SUP-4 | sleeve dropped | dropped by DS-66 (named) | POWER-JR-AGND3 | 33.00 |
| K-SUP-5 | sleeve dropped | dropped: site conflicts (panel hardware (pot) RV105 on P at 1.25 mm) | POWER-JL-+12V | 89.51 |
| K-SUP-6 | sleeve dropped | dropped: site conflicts (panel hardware (led) D11805 on EL at 1.83 mm; panel hardware (pot) RV1805 on P at 1.25 mm) | SLV-L2 | 68.74 |
| K-SUP-7 | sleeve dropped | dropped: site conflicts (hole MH_P-SUP-3 on P at 1.90 mm; panel hardware (pot) RV108 on P at 1.25 mm) | SLV-L1 | 87.55 |
| K-SUP-8 | sleeve dropped | dropped: site conflicts (panel hardware (pot) RV1508 on P at 0.00 mm) | SLV-L2 | 60.60 |

The pair choice comes from the coverage of item 3: with each member forced, the smallest list needs

| Pair | Member kept | Added sites needed | Farthest point, mm |
| --- | --- | --- | --- |
| JL-SUP-1 / JL-SUP-2 | JL-SUP-1 | 3 | 93.61 |
| JL-SUP-1 / JL-SUP-2 | JL-SUP-2 | 4 | 93.61 |
| JR-SUP-1 / JR-SUP-2 | JR-SUP-1 | 3 | 93.61 |
| JR-SUP-1 / JR-SUP-2 | JR-SUP-2 | 4 | 93.61 |

K-SUP-5 and K-SUP-7 both stand on locked pots, so neither member of that pair can stay.

- JL-SUP-1 stays: 3 added sites against 4 with JL-SUP-2.
- JR-SUP-1 stays: 3 added sites against 4 with JR-SUP-2.

## Coverage: 3 added sites bring the farthest point from 153.2 to 93.6 mm; 90 mm is missed at 2 clusters

| Added site | On K and on the front board | Front board | Boards pierced | Sleeve | Nearest other fixing | mm | Clearance to the nearest board edge, mm | Candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SLV-U1 | (159, 38) | JL | K, JL | 19.0 mm gap | POWER-JL-AGND3 | 126.65 | 17.50 | GS-48 |
| SLV-L2 | (244, 230) | P | K, P, EL | 17.0 mm gap | POWER-JR-AGND1 | 70.00 | 21.26 | GS-199 |
| SLV-L1 | (93, 276) | P | K, P | 17.0 mm gap | POWER-P-AGND2 | 101.15 | 16.00 | GS-205 |

- **Candidates.** First the stated set: the five provisional sites of the rigid design and the 66 clear sites of `stack-candidate.json`, 71 candidates in all, of which 4 pass the screen; they cannot meet the 90 mm rule. Then a screen of K on a 1.0 mm grid with the same rules: 882 clear nodes, thinned to 212 candidates at 4.0 mm.
- **Screen.** A site needs a facing front board; the sleeve (r 3.5 mm) plus 0.3 mm inside K, the front board and EL where it lies under EL; clear of the tabs, the adapters O1, O3 and O5, the kept selectors and the sub toggles by 3.75 mm; no locked panel hardware or fixed hole in its keep-out; at least 70 mm from every post.
- **Method.** integer program (scipy.optimize.milp, HiGHS, relative gap 0) over the screened candidate set: binary choice per usable candidate and per paired sleeve; every grid node beyond 90 mm of the fixed fixings must lie within 90 mm of a chosen site; any two chosen sleeves at least 70 mm apart; exactly one sleeve of each named pair; objective 1000 per added site plus its keep-out part count, so the site count is the minimum for this candidate set and grid. Where 90 mm cannot be met, nodes that no candidate reaches within 90 mm must be reached within the smallest radius that is feasible (94.0 mm, in 0.5 mm steps); every other node keeps 90 mm.
- **Minimality.** The count is the minimum for the screened candidate set on the 1 mm coverage grid. A site off the candidate grid could do better by an unknown amount; no continuous search was run (NOT RUN). A point between grid nodes lies at most 0.71 mm farther than its nearest node.

| Fixings | Farthest point of K, mm | At |
| --- | --- | --- |
| 18 posts only | 156.21 | (4, 8) |
| 18 posts and the 12 present sleeves | 153.19 | (159, 8) |
| this list | 93.61 | (4, 247) |
| lower bound, any selection from all clear nodes of the screen | 93.30 | (4, 247) |

Grid nodes beyond 90 mm, grouped:

| Region of K (x0, y0, x1, y1) | Nodes | Farthest node | mm |
| --- | --- | --- | --- |
| (4, 243, 8, 262) | 52 | (4, 247) | 93.61 |
| (4, 290, 4, 292) | 3 | (4, 292) | 90.43 |

Both clusters lie at K's left edge, in front of the pot field of P: the grid screen finds no clear site within 90 mm of them. The corner cluster misses by under 1 mm and may close on a finer candidate grid than 1 mm (NOT RUN). Ways out are design decisions, not taken here: a site in the pot field with a smaller head or a front-side nut, a fixing through the adapter region, a K fixing to the enclosure, or a relaxed 90 mm figure at the left edge.

| Sleeve length | Needed | On the delivered plate | Covered |
| --- | --- | --- | --- |
| 18.8 mm (19.0 mm gap: JL, JR) | 3 | 10 | yes |
| 16.8 mm (17.0 mm gap: P) | 2 | 6 | yes |

## Part moves: the 3 added sites put 10 footprints in their keep-outs; 4 have no free position within 12 mm

Method of ST-04 (`design/stack/power-posts/envelopes.json`): courtyard box (pad box when none) against the keep-out circle, r 4.05 mm on K and r 3.75 mm on a front board or EL, both faces; the nearest free position is the smallest shift (0.25 mm steps, 24 directions, up to 12 mm) that clears every fixing of this list, every other footprint on its faces and the outline by 0.3 mm. No locked part is in any added keep-out. A footprint with no free position needs a hand placement. GH harness headers that a flat link replaces are not listed; the room study places the links around these keep-outs.

| Site | Board | Reference | Footprint | Class | Courtyard from centre, mm | Origin | Nearest free origin | Shift, mm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SLV-U1 | JL | C8117 | C0603 | movable | 0.57 | (158.405, 39.53) | (160.28, 42.778) | 3.75 |
| SLV-U1 | JL | D8120 | SOD-123 | movable | 3.50 | (158.35, 42.75) | (158.35, 43) | 0.25 |
| SLV-U1 | JL | U8103 | TI_RRP0016A | movable | 0.00 | (158.78, 35.77) | - | none within 12 mm |
| SLV-L2 | EL | D4225 | SOD-123 | movable | 0.00 | (243.61, 231.25) | (243.61, 237.5) | 6.25 |
| SLV-L2 | EL | RB4221 | R0603 | movable | 0.93 | (242.64, 228.16) | (242.64, 223.41) | 4.75 |
| SLV-L2 | EL | RB4222 | R0603 | movable | 3.68 | (242.64, 225.41) | (242.423, 225.285) | 0.25 |
| SLV-L2 | K | R4243 | R0603 | movable | 3.28 | (240.89, 226.16) | (237.209, 224.035) | 4.25 |
| SLV-L2 | K | U4215 | SOIC-14_3.9x8.7mm_P1.27mm | movable | 0.75 | (248.45, 230.95) | - | none within 12 mm |
| SLV-L2 | K | U4226 | SOIC-14_3.9x8.7mm_P1.27mm | movable | 0.87 | (238.18, 231.95) | - | none within 12 mm |
| SLV-L2 | P | U208 | SOIC-14_3.9x8.7mm_P1.27mm | movable | 0.00 | (243.7, 227.68) | - | none within 12 mm |
| JL-SUP-1 | JL | J101 | Jack_3.5mm_QingPu_WQP518MA | panel hardware (jack) | 3.25 | (14.5, 29) | - | locked, outside the panel-side and pad test |
| JR-SUP-1 | JR | J1801 | Jack_3.5mm_QingPu_WQP518MA | panel hardware (jack) | 3.25 | (303.5, 29) | - | locked, outside the panel-side and pad test |
| JR-SUP-1 | JR | R4615 | R0603 | movable | 2.70 | (310.94, 26.11) | - | none within 12 mm |
| JR-SUP-1 | JR | R4616 | R0603 | movable | 3.32 | (306.54, 22.51) | - | none within 12 mm |
| JR-SUP-1 | JR | RB4607 | R_1210_3225Metric | movable | 2.91 | (307.3, 26.07) | - | none within 12 mm |

Kept sites are listed too. They are given positions of DS-45 and keep their 2.5 mm distance to the board edge: the 7.0 mm sleeve overhangs K and the front board there by 1.0 mm, an open item for the design authority.

## Ceramics: 1 ceramic part of 0805 or larger within 5 mm of a fixing (C4513 at POWER-P-+5V)

Screened at every post and every kept or added sleeve, on every board the fixing pierces, from the fixing centre to the courtyard. Ceramic identity is ASSUMED from a C reference on a chip footprint; the dielectric comes from the value text where it names one, otherwise it is unknown.

| Fixing | Board | Reference | Case | Value | mm | Nearest free origin beyond 5 mm | Shift, mm |
| --- | --- | --- | --- | --- | --- | --- | --- |
| POWER-P-+5V | K | C4513 | C1206 | 100 nF C0G | 4.13 | (168.31, 177.639) | 1.50 |

## Screw lengths stay UNSOURCED: the grip is 22.2 / 20.2 mm, but no washer, nut or protrusion figure is retained

| Site class | Front board, mm | Gap (posts set it), mm | K, mm | Grip, mm | Washer | Nut | Protrusion | Length | Grip source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sleeve, JL or JR to K | 1.6 | 19.0 | 1.6 | 22.2 | UNSOURCED | UNSOURCED | UNSOURCED | UNSOURCED: 22.2 mm grip + washer + nut + protrusion | stack-candidate.json planes: JL face z -10.0 to K rear z -32.2 |
| sleeve, P to K | 1.6 | 17.0 | 1.6 | 20.2 | UNSOURCED | UNSOURCED | UNSOURCED | UNSOURCED: 20.2 mm grip + washer + nut + protrusion | stack-candidate.json planes: P face z -12.0 to K rear z -32.2 |
| sleeve, P to K under EL | 1.6 | 17.0 | 1.6 | 20.2 | UNSOURCED | UNSOURCED | UNSOURCED | UNSOURCED: 20.2 mm grip + washer + nut + protrusion; how the screw passes EL is open | head on P's front face through a clearance hole in EL; head on EL's face (z -4.4) would add 7.6 mm and bridge the 7.2 mm EL gap |

Post screws are outside this list: the Harwin posts are M3 through-tapped (ST-04), and their engagement length is UNSOURCED as well.

## Interface: `fixing-sites.json` lists all 33 fixings of K with their keep-outs, 23 of them active

Per fixing: `id`, `kind` (post, sleeve kept, sleeve added, sleeve dropped), `xy` on K and `front_xy` on the front board (panel frame), `K_kicad_xy` and `front_kicad_xy`, `front_board`, `boards` pierced, `gap_mm`, `keepout_radius_mm` per board, `part_moves` and `status`. The room study reads the active ones as link keep-outs, the mechanics study for its short pass on K, the manager for the spacer README.

| Fixing | Kind | xy | Front board | Keep-out radius per board, mm |
| --- | --- | --- | --- | --- |
| POWER-JL-+12V | post | (40, 160) | JL | JL 3.75, K 4.05 |
| POWER-JL--12V | post | (57, 160) | JL | JL 3.75, K 4.05 |
| POWER-JL-+5V | post | (74, 160) | JL | JL 3.75, K 4.05 |
| POWER-JL-AGND1 | post | (91, 160) | JL | JL 3.75, K 4.05 |
| POWER-JL-AGND2 | post | (108, 160) | JL | JL 3.75, K 4.05 |
| POWER-JL-AGND3 | post | (125, 160) | JL | JL 3.75, K 4.05 |
| POWER-JR-+12V | post | (193, 160) | JR | JR 3.75, K 4.05 |
| POWER-JR--12V | post | (210, 160) | JR | JR 3.75, K 4.05 |
| POWER-JR-+5V | post | (227.5, 160) | JR | JR 3.75, K 4.05 |
| POWER-JR-AGND1 | post | (244.5, 160) | JR | JR 3.75, K 4.05 |
| POWER-JR-AGND2 | post | (261.5, 160) | JR | JR 3.75, K 4.05 |
| POWER-JR-AGND3 | post | (278.5, 160) | JR | JR 3.75, K 4.05 |
| POWER-P-+12V | post | (142, 175) | P | K 4.05, P 3.75 |
| POWER-P--12V | post | (159, 175) | P | K 4.05, P 3.75 |
| POWER-P-+5V | post | (176, 175) | P | K 4.05, P 3.75 |
| POWER-P-AGND1 | post | (193, 175) | P | K 4.05, P 3.75 |
| POWER-P-AGND2 | post | (98.5, 175) | P | K 4.05, P 3.75 |
| POWER-P-AGND3 | post | (110, 174.5) | P | K 4.05, P 3.75 |
| JL-SUP-1 | sleeve kept | (6.5, 22.5) | JL | JL 3.75, K 4.05 |
| JR-SUP-1 | sleeve kept | (311.5, 22.5) | JR | JR 3.75, K 4.05 |
| SLV-U1 | sleeve added | (159, 38) | JL | JL 3.75, K 4.05 |
| SLV-L2 | sleeve added | (244, 230) | P | EL 3.75, K 4.05, P 3.75 |
| SLV-L1 | sleeve added | (93, 276) | P | K 4.05, P 3.75 |

## Checker: five rules with one fault-injection test each; the retained list fails only the 90 mm rule

| Rule | What the checker recomputes from the boards |
| --- | --- |
| spacing | no kept or added sleeve within 70 mm of another active fixing |
| coverage | no node of the 1 mm grid over K's outline beyond 90 mm |
| site | no sleeve on locked panel hardware, a fixed hole, a tab, an adapter, a kept selector or a sub toggle, or outside a board |
| moves | every footprint in a sleeve keep-out and every ceramic of 0805 or larger within 5 mm of any fixing has a listed move, and each listed free position clears every keep-out |
| stale | the SHA256 of every input and program file equals the provenance |

## NOT RUN: any fit, strength, strain or creep figure, any native KiCad check, a continuous site search

- The strain and deflection of K on this list: the short pass of ST-03 (DS-67).
- Copper clearance, DRC and routing around the new holes: no KiCad was run; the screen is courtyard level.
- The flat links themselves are not on the boards yet; the room study places them around these keep-outs.
- UNSOURCED: washer thickness, nut height, thread protrusion, creep of the printed sleeve.
- ASSUMED: the sleeve keep-out radii equal to the post radii (`link-options.json`), ceramic identity from the footprint class.
