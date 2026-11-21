# Fixing list of the flat-link stack as ruled (ST-08 attempt a2, part 1)

Task `osc-stack-20261114/ST-08 a2 part 1`. The list is the ruled input [`ruled-list.json`](ruled-list.json) (decision rows DS-72 to DS-76); this study checks it and does not choose it. **Status: generated paper check on unvalidated drafts.** Every figure is a courtyard-level count of the board files; nothing is a copper clearance, a DRC, a fit, a strength or a strain result, and nothing is adopted. Coordinates are in the panel frame of the placement lock, the same on K and on the front board; KiCad file coordinates add the lock's translation.

- [`fixing-sites.json`](fixing-sites.json): `fixings` (every fixing of K with `active`), `reserve`, `alternatives`, `access_holes`, `screw`, `region_scans`, `coverage` and the pins of every input.
- `scripts/stack/fixings/fixings.py` writes both files (`--check` fails on a stale file or on any checker finding); `fixings_check.py` is the checker; `test_fixings.py` holds the tests.

## DONE: all 4 ruled sleeves pass the hard screens

| Result | Value |
| --- | --- |
| Fixings of K | 22: 18 posts and 4 sleeves (2 long, 2 short) |
| Fastener operations | 44 (36 post screws, 4 sleeve screws, 4 nuts; DERIVED: a post takes a screw from each board; a sleeve one screw and one nut) |
| Delivered plate (10 long, 6 short) | covers the list |
| Dropped sites of DS-45 | 12, none active |
| Farthest point of K from a fixing | 95.71 mm at (160, 70) (posts only: 156.21 mm at (4, 8)) |
| Movement limit of DS-72 | NOT RUN on this list until ST-03 attempt a6 reports |

## The ruled sleeves: 4 pass, 0 fail the panel-side, pad, hole, keep-out and 70 mm screens

| Sleeve | xy | Front board | Boards pierced | Gap, mm | Nearest other fixing | mm | Edge clearance, mm | Decision | Findings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SLV-U1 | (74, 28) | JL | K, JL | 19.0 | POWER-JL-+5V | 132.00 | 8.00 | DS-73, DS-76 | none |
| SLV-U2 | (244, 24) | JR | K, JR | 19.0 | POWER-JR-AGND1 | 136.00 | 4.00 | DS-73, DS-76 | none |
| SLV-L1 | (93, 276) | P | K, P | 17.0 | POWER-P-AGND2 | 101.15 | 16.00 | DS-74, DS-76 | none |
| SLV-L2 | (244, 230) | P | K, P, EL | 17.0 | POWER-JR-AGND1 | 70.00 | 21.26 | DS-74, DS-76 | none |

Reserve and alternatives, screened the same way against the list (an alternative in place of the sleeve it replaces):

| Site | Role | xy | Decision | Nearest other fixing | mm | Displaced parts | Without a free position | Findings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SLV-R1 | reserve | (159, 38) | DS-73 | SLV-U1 | 85.59 | 3 | U8103 | none |
| ALT-L1-A | alternative for SLV-L1 | (97, 276) | DS-74 | POWER-P-AGND2 | 101.01 | 0 | none | none |
| ALT-L1-B | alternative for SLV-L1 | (101, 276) | DS-74 | POWER-P-AGND2 | 101.03 | 0 | none | none |
| ALT-L2-A | alternative for SLV-L2 | (261, 227) | DS-74 | POWER-JR-AGND2 | 67.00 | 11 | U4211 | POWER-JR-AGND1 within 70 mm (69.00 mm); POWER-JR-AGND2 within 70 mm (67.00 mm); POWER-JR-AGND3 within 70 mm (69.25 mm) |

Dropped: JL-SUP-1 (SLV-U1 within 70 mm (67.72 mm)), JL-SUP-2 (no site conflict), JL-SUP-3 (POWER-JL-+12V within 70 mm (40.08 mm); POWER-JL--12V within 70 mm (55.08 mm)), JR-SUP-1 (SLV-U2 within 70 mm (67.52 mm)), JR-SUP-2 (no site conflict), JR-SUP-3 (POWER-JR-AGND2 within 70 mm (54.63 mm); POWER-JR-AGND3 within 70 mm (39.66 mm); panel hardware (led) D1809 on JR (courtyard 2.39 mm)), K-SUP-3 (POWER-JL-+12V within 70 mm (33.50 mm); POWER-JL-+5V within 70 mm (67.50 mm); POWER-JL--12V within 70 mm (50.50 mm); hole MH_JL-SUP-4 on JL (courtyard 0.40 mm)), K-SUP-4 (POWER-JR-AGND1 within 70 mm (67.00 mm); POWER-JR-AGND2 within 70 mm (50.00 mm); POWER-JR-AGND3 within 70 mm (33.00 mm); hole MH_JR-SUP-4 on JR (courtyard 0.40 mm); panel hardware (led) D18101 on JR (courtyard 2.58 mm)), K-SUP-5 (panel hardware (pot) RV105 on P (courtyard 1.25 mm, rear pad 1.70 mm)), K-SUP-6 (SLV-L2 within 70 mm (68.74 mm); panel hardware (led) D11805 on EL (courtyard 1.83 mm); panel hardware (pot) RV1805 on P (courtyard 1.25 mm, rear pad 1.70 mm)), K-SUP-7 (hole MH_P-SUP-3 on P (courtyard 1.90 mm); panel hardware (pot) RV108 on P (courtyard 1.25 mm, rear pad 4.65 mm)), K-SUP-8 (SLV-L2 within 70 mm (60.60 mm); panel hardware (pot) RV1508 on P (courtyard 0.00 mm, rear pad 0.00 mm)).

## Parts in the sleeve keep-outs: 12 movable footprints, 3 without a free position within 12 mm, 0 of them not assigned by a decision (authority: 12 and 3)

Method of ST-04: courtyard box against the keep-out circle (r 4.05 mm on K, r 3.75 mm on a front board and on EL, both faces); the nearest free position is the smallest shift (0.25 mm steps, 24 directions, up to 12 mm) that clears every active fixing, every other footprint on its faces and the outline by 0.3 mm, tested at the rounded position that is retained.

| Fixing | Board | Reference | Footprint | Courtyard from centre, mm | Origin | Nearest free origin | Shift, mm | Ceramic 0805+ within 5 mm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| POWER-P-+5V | K | C4513 | C1206 | 4.13 | (169.06, 176.34) | (168.31, 177.639) | 1.50 | yes |
| SLV-U2 | JR | D4203 | SOT-23 | 3.00 | (243.23, 28.81) | (243.23, 36.06) | 7.25 | no |
| SLV-U2 | JR | R8436 | R0603 | 0.80 | (242.34, 25.71) | (242.34, 35.21) | 9.50 | no |
| SLV-U2 | K | Q4305 | SOT-23 | 0.75 | (243.81, 26.68) | (238.497, 28.104) | 5.50 | no |
| SLV-U2 | K | Q4306 | SOT-23 | 2.37 | (248.06, 26.68) | (248.06, 18.68) | 8.00 | no |
| SLV-U2 | K | R4380 | R0603 | 4.00 | (249.64, 23.16) | (249.89, 23.16) | 0.25 | no |
| SLV-L2 | EL | D4225 | SOD-123 | 0.00 | (243.61, 231.25) | (243.61, 237.5) | 6.25 | no |
| SLV-L2 | EL | RB4221 | R0603 | 0.93 | (242.64, 228.16) | (242.64, 223.41) | 4.75 | no |
| SLV-L2 | EL | RB4222 | R0603 | 3.68 | (242.64, 225.41) | (242.423, 225.285) | 0.25 | no |
| SLV-L2 | K | R4243 | R0603 | 3.28 | (240.89, 226.16) | (237.209, 224.035) | 4.25 | no |
| SLV-L2 | K | U4215 | SOIC-14_3.9x8.7mm_P1.27mm | 0.75 | (248.45, 230.95) | - | the re-placement search of the room study at 25 mm (DS-74) | no |
| SLV-L2 | K | U4226 | SOIC-14_3.9x8.7mm_P1.27mm | 0.87 | (238.18, 231.95) | - | the re-placement search of the room study at 25 mm (DS-74) | no |
| SLV-L2 | P | U208 | SOIC-14_3.9x8.7mm_P1.27mm | 0.00 | (243.7, 227.68) | - | the re-placement search of the room study at 25 mm (DS-74) | no |

**Access hole in EL at (244, 230), 7.0 mm (DS-76):** inside the 3.75 mm keep-out already applied to EL at SLV-L2 (centre offset 0.00 mm), so it displaces nothing further.

## Region scans: 11 of 16 compared figures equal the authority's scratch runs; the differences are listed

Integer nodes of a 1 mm grid; a node is clear when it faces the named board, passes the edge, tab, adapter, selector and sub-toggle screens and has no locked hardware or fixed hole in its keep-out. Free positions are searched with the posts and the node as the only fixings. The node lists are in `region_scans`. A row named "y 22 to 69" or "y 176 to 291" counts the region without its last row, for comparison only.

| Figure | This study | Authority (scratch run) | Comparison |
| --- | --- | --- | --- |
| JL clear nodes (y 22 to 70) | 327 | 322 | differs |
| JL clear nodes, y 22 to 69 | 322 | 322 | same |
| JL nodes with a free position for every part | 127 | 125 | differs |
| JL columns of those nodes | [23.0, 40.0, 57.0, 74.0, 91.0] | [23.0, 40.0, 57.0, 74.0, 91.0] | same |
| JR clear nodes | 176 | 176 | same |
| JR nodes with a free position for every part | 2 | 2 | same |
| JR those nodes | [[244.0, 24.0], [244.0, 25.0]] | [[244.0, 24.0], [244.0, 25.0]] | same |
| Upper middle clear nodes (x 120 to 200) | 92 | 92 | same |
| Upper middle nodes with no integrated circuit lacking a free position | 8 | 0 | differs |
| Upper middle nodes with a free position for every part | 0 | 0 | same |
| Lower right clear nodes | 25 | 20 | differs |
| Lower right clear nodes, y 176 to 291 | 25 | 20 | differs |
| Lower right y range | [226.0, 230.0] | [226.0, 230.0] | same |
| Lower right SOIC-14 without a free position per node | [1, 4] | [1, 4] | same |
| Lower right clear nodes 70 mm or more from every post | 5 | - | not stated by the authority |
| Corner (7.5, 23.5): panel-side courtyard, mm | [2.25] | [2.25] | same |
| Corner (310.5, 23.5): panel-side courtyard, mm | [2.25] | [2.25] | same |

## Distance screen (DS-72, no rule): farthest point 95.71 mm above the post rows and 93.61 mm below; 165 and 55 nodes beyond 90 mm

| Region | Farthest node | mm | Nodes beyond the screen | Manager's count |
| --- | --- | --- | --- | --- |
| above the post rows (y <= 160) | (160, 70) | 95.71 | 165 | 95.71 mm at (160, 70), 165 nodes |
| below the post rows (y >= 175) | (4, 247) | 93.61 | 55 | 93.61 mm at (4, 247), 55 nodes |

| Region of K (x0, y0, x1, y1) | Side | Nodes | Farthest node | mm |
| --- | --- | --- | --- | --- |
| (152, 57, 168, 76) | above | 165 | (160, 70) | 95.71 |
| (4, 243, 8, 262) | below | 52 | (4, 247) | 93.61 |
| (4, 290, 4, 292) | below | 3 | (4, 292) | 90.43 |

| Sleeve | Nearest post, mm | Manager |
| --- | --- | --- |
| SLV-U1 | 132.00 | 132.00 |
| SLV-U2 | 136.00 | 136.00 |
| SLV-L1 | 101.15 | 101.15 |
| SLV-L2 | 70.00 | 70.00 |

The movement limit of DS-72 is ST-03's figure: NOT RUN on this list until ST-03 attempt a6 reports.

## Screw: M3 x 25 (ASSUMED) passes the head test and leaves the thread 2.80 and 4.80 mm behind K's rear face, against a 5.00 mm envelope

| Class | Grip, mm | Thread behind K, mm | Inside the envelope | Grip source |
| --- | --- | --- | --- | --- |
| long sleeve, JL or JR to K | 22.20 | 2.80 | yes | stack-candidate.json planes: JL face z -10.0 to K rear z -32.2 |
| short sleeve, P to K | 20.20 | 4.80 | yes | stack-candidate.json planes: P face z -12.0 to K rear z -32.2 |

Head at most 5.5 mm, not countersunk, against the 3.0 mm head radius of the panel-side test. Nut height and washer thickness: UNSOURCED, UNSOURCED.

## Interface: `fixings` keeps its keys; 34 entries, 22 active

Keys with unchanged meaning: `id`, `kind`, `xy`, `front_xy`, `front_board`, `boards`, `gap_mm`, `keepout_radius_mm`, `length_class`; added: `active`. The ruled sleeves keep the kind `sleeve added`. The reserve, the alternatives, the access hole and the scans are top-level objects and never in `fixings`.

| Fixing | Kind | Active | xy | Front board | Keep-out radius per board, mm |
| --- | --- | --- | --- | --- | --- |
| POWER-JL-+12V | post | yes | (40, 160) | JL | JL 3.75, K 4.05 |
| POWER-JL--12V | post | yes | (57, 160) | JL | JL 3.75, K 4.05 |
| POWER-JL-+5V | post | yes | (74, 160) | JL | JL 3.75, K 4.05 |
| POWER-JL-AGND1 | post | yes | (91, 160) | JL | JL 3.75, K 4.05 |
| POWER-JL-AGND2 | post | yes | (108, 160) | JL | JL 3.75, K 4.05 |
| POWER-JL-AGND3 | post | yes | (125, 160) | JL | JL 3.75, K 4.05 |
| POWER-JR-+12V | post | yes | (193, 160) | JR | JR 3.75, K 4.05 |
| POWER-JR--12V | post | yes | (210, 160) | JR | JR 3.75, K 4.05 |
| POWER-JR-+5V | post | yes | (227.5, 160) | JR | JR 3.75, K 4.05 |
| POWER-JR-AGND1 | post | yes | (244.5, 160) | JR | JR 3.75, K 4.05 |
| POWER-JR-AGND2 | post | yes | (261.5, 160) | JR | JR 3.75, K 4.05 |
| POWER-JR-AGND3 | post | yes | (278.5, 160) | JR | JR 3.75, K 4.05 |
| POWER-P-+12V | post | yes | (142, 175) | P | K 4.05, P 3.75 |
| POWER-P--12V | post | yes | (159, 175) | P | K 4.05, P 3.75 |
| POWER-P-+5V | post | yes | (176, 175) | P | K 4.05, P 3.75 |
| POWER-P-AGND1 | post | yes | (193, 175) | P | K 4.05, P 3.75 |
| POWER-P-AGND2 | post | yes | (98.5, 175) | P | K 4.05, P 3.75 |
| POWER-P-AGND3 | post | yes | (110, 174.5) | P | K 4.05, P 3.75 |
| SLV-U1 | sleeve added | yes | (74, 28) | JL | JL 3.75, K 4.05 |
| SLV-U2 | sleeve added | yes | (244, 24) | JR | JR 3.75, K 4.05 |
| SLV-L1 | sleeve added | yes | (93, 276) | P | K 4.05, P 3.75 |
| SLV-L2 | sleeve added | yes | (244, 230) | P | EL 3.75, K 4.05, P 3.75 |
| JL-SUP-1 | sleeve dropped | no | (6.5, 22.5) | JL | JL 3.75, K 4.05 |
| JL-SUP-2 | sleeve dropped | no | (6.5, 80) | JL | JL 3.75, K 4.05 |
| JL-SUP-3 | sleeve dropped | no | (6.5, 138) | JL | JL 3.75, K 4.05 |
| JR-SUP-1 | sleeve dropped | no | (311.5, 22.5) | JR | JR 3.75, K 4.05 |
| JR-SUP-2 | sleeve dropped | no | (311.5, 80) | JR | JR 3.75, K 4.05 |
| JR-SUP-3 | sleeve dropped | no | (311.5, 138) | JR | JR 3.75, K 4.05 |
| K-SUP-3 | sleeve dropped | no | (6.5, 160) | JL | JL 3.75, K 4.05 |
| K-SUP-4 | sleeve dropped | no | (311.5, 160) | JR | JR 3.75, K 4.05 |
| K-SUP-5 | sleeve dropped | no | (6.5, 243) | P | K 4.05, P 3.75 |
| K-SUP-6 | sleeve dropped | no | (311.5, 243) | P | EL 3.75, K 4.05, P 3.75 |
| K-SUP-7 | sleeve dropped | no | (6.5, 289.5) | P | K 4.05, P 3.75 |
| K-SUP-8 | sleeve dropped | no | (255.5, 289.5) | P | K 4.05, P 3.75 |

## Pins: 13 whole files, 11 objects, 10 decision rows and 1 review section

| Pin | SHA256 |
| --- | --- |
| DS-43 | c80de3cd9eb4b7fc229afec63ae4231fe2b28f5f3498641cb2767391fdd77ef3 |
| DS-44 | ea630dc80b607567f2020941de9bc03f38d471505c719d811c89fc85899e1c15 |
| DS-45 | fd063ea96d2f78041e8cead343adfcc862e086a8426aee3deed3605f4c01636f |
| DS-66 | 9d76e54171c64b1c17b8df322e26365e5bf8c3ffec7848f22da0daa588ca2723 |
| DS-70 | 4ca08935586381a803900307198d073b47550bb676f32fd7ff2bcf26c1155b57 |
| DS-72 | db81e22c17374cd4f38b6a515effb607d1959d9b14e69ead15faafd0b016f591 |
| DS-73 | 92631aaa732abfad66d965c0189c0852dbce1df5055c194c2493f36672ae8152 |
| DS-74 | ac65213d0b8dcdbed6ab6d3288c29a87548031cb329d0f9a4031f276789eaabb |
| DS-75 | cb907b51004015a5848b7cd3a4e6ea7cd256eb616fde38bef4a7c6a18834b107 |
| DS-76 | 02801200abda6e3e03fe76e8173b1c5a7f1591b3a6faeeb994d642bf0fb6ea8a |
| da-03 c2: scratch runs and H1 to H5 | c3cd4bea7a86ac24591197fef5a5c7a0dd0edbfcaac2094c290dfe9fafcb98c4 |
| design/stack/geometry/links/link-options.json fixing_keepout_radius_mm, board_edge_margin_mm | e0e744f7e8e9844fe473c8da173cc8e8d2dc22e1fecf958cfb9eba2d8dafae3f |
| design/stack/geometry/stack-candidate.json candidate.fixings (kept supports) | a795d3555182f7c54c4d7cb4eab5252839341a4a1a4d14b1b47ca6911779eeba |
| design/stack/geometry/stack-candidate.json candidate.pairs[].sites.*.replaces | a868c38e57296f8cd9ffd2799fb4fff83716500267e1bfa531ee66a9f7fb014e |
| design/stack/geometry/stack-candidate.json candidate.planes | 1fe42572782266ce81af20248470f6a9ba1479d0f25545ea99b2b877365e213c |
| design/stack/geometry/stack-candidate.json candidate.retired (K_headers, front_headers) | 9e1f2758fa7fe73aca0b1925b8d9446386aa69ffb465750c1f3382c06e8ac898 |
| design/stack/geometry/stack-candidate.json candidate.selectors_kept | 8b06d74ed309428d9ccd16570c6bb198c24b2fa540aa57f418e1d5d3995340b0 |
| design/stack/geometry/stack-candidate.json candidate.stack (K_rear_z_mm, K_rear_parts_z_mm) | d4e9d88a0e832b1e80a1e0c1de5a1f475626e3c29fe7bfcb33a88203ce6bda16 |
| design/stack/geometry/stack-candidate.json candidate.sub_toggles | 6a4bc1070b774ce2b342e1e0ace16cd1aab0c416b8fe122be666a137d25302ff |
| design/stack/geometry/stack-candidate.json candidate.tabs | 05c7f0282fafeddb9c658e463d780d229829827058ef5172951eb79cc034dd36 |
| design/stack/power-posts/joint-design.json joints | cb58dd654f2b169336a22d2bdef50de8448c63dca9c7dfb74e3e4d3980b0b218 |
| design/stack/spacers/spacer-set.json sleeve, length_allowance_mm, members | fed1446f89d2345d2692e822ac0e91b228c124d880bada37fdeb3c7f9bf4c436 |
| boards/osc-control/osc-control-routed-draft.kicad_pcb | 111c5af77fa5fff3ebe96de988197fac36f37eb54d332c66b36477fa3b6e7f44 |
| boards/osc-core/osc-core.kicad_pcb | 7311cd8e7aabb609c0a6d1a7f2ef42324c585d0c7b51f77c6bd3fc0338c54f22 |
| boards/osc-jack-left/osc-jack-left.kicad_pcb | 5900338a0aecafc6e4370f4f2ce812fc7b80ffdb730ea4bce3d8e1db55a2a779 |
| boards/osc-jack-right/osc-jack-right.kicad_pcb | 3ffaa03739983dd326345ac1884b0cb56432a65c558abde42c2e151bd4c75e56 |
| boards/osc-stage-optical/osc-stage-optical.kicad_pcb | 7e0d9a25c13a5108439d391815409ddd60cc837db0563d45adb5f5a137fa2d61 |
| design/grid/placements.lock.json | 297300b067fd646624b9e501791163fa2d60702862b61568753bf92e5b88dbe8 |
| design/partition/partition.json | aa84af4cc17672276f1512e5404a41a7139a676aa5326c3260b0530d3f7ff339 |
| design/stack/fixings/ruled-list.json | fb18e85e1c7a9be576a5c9d5d5efd2738999a86449afeae00e8ed84d65ce234d |
| scripts/stack/fixings/fixings.py | d1b1dbe6eaab479aa1b890c1c7fd446d03411bab3259498b750862d41eb0f48c |
| scripts/stack/fixings/fixings_check.py | 02d565882c7211f2eebc1d36ef33d66922a04952382e30dac91d9616e46e76e7 |
| scripts/stack/fixings/fixings_readme.py | f0e5a3a8452a51303192392a3022c93655fa9d5447e6e169deb3b3e78ae4ea62 |
| scripts/stack/geometry/kicad_extract.py | 23093e93bf8a5c9072310531d771f9592783673c13f9a23dd70eb9272505ecdd |
| scripts/stack/geometry/stackgeom.py | 70db6b0833512a20029b743c49d9adf0fe1b69ef8bb4d0063afc3515cb07d7ab |

## NOT RUN: K's movement and strain on this list, native KiCad checks, any fit, strength or creep figure

- The movement limit of DS-72 on this list: ST-03 attempt a6.
- Copper clearance, DRC and routing around the holes: no KiCad was run; the screen is courtyard level.
- The flat links are not on the boards; ST-02 attempt a8 reads `fixings` as its keep-out list.
- UNSOURCED: nut height, washer thickness, creep of the printed sleeve. ASSUMED: the screw figure, the sleeve keep-out radii equal to the post radii, ceramic identity from the footprint class.
