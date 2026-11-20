# Power posts: ST-04 joint design and electrical re-derivation (paper, attempt a1, continuation c1 and attempt a2)

Task `osc-stack-20261114/ST-04`, 2026-11-14, launch commit `4a00e72`; continuation c1 on `a2831f7` applies the rulings of DA-02 (`reviews/da-02.md`, E10, E2, E3 and "Rulings on the ST-04 proposal"); attempt a2 on `21d1cd9` applies DS-44 (DA-03 F7: the four JR lands at +0.5 mm in x instead of +1.0 mm). The flat-link coupling and ground-current bounds of attempt a2 are in [`../link-electrical/`](../link-electrical/README.md). **Status: unvalidated paper design.** Nothing is selected, bought, measured or qualified. Every joint resistance, current and fit below is NOT RUN on hardware; the hot Kelvin measurement of #65 stays open.

Files:

- [`joint-design.json`](joint-design.json): every term with value, tolerance, unit, status and source; the land pattern; the 18 joints with coordinates and nets.
- [`envelopes.json`](envelopes.json): courtyard-level screen of the post keep-outs on K, JL, JR and P, with the nearest free position of every footprint inside. Written by `python3 scripts/stack/power_posts/measure_envelopes.py` (plain-Python board reader of ST-02; no KiCad).
- `scripts/stack/power_posts/power_posts.py`: recomputes every table between `calc:` markers from the JSON (`--write-readme` refreshes them; the tests fail if they differ).

Inputs: XY, counts and nets come from the geometry candidate (`design/stack/geometry/stack-candidate.json`, still at the first planning heights and the old land positions). Heights and planes come from DA-02 E10: K F.Cu at z = −30.6 mm; JL and JR to K 19.0 mm; P to K 17.0 mm. The joint positions in `joint-design.json` carry the rulings: the four JR lands at +0.5 mm in x (DS-44), and P's AGND2 and AGND3 on a second tab segment (DA-02, confirmed by DS-44). The EL AGND count (12) and rail count per rail (6) are DERIVED from DS-14; the candidate still holds six 1×6 sites. Status words: SOURCED (file, hash, locator), DERIVED (formula), ASSUMED (with the check that closes it), UNSOURCED.

## The method reproduces the partition's 15.321 / 15.058 / 11.113 mV, its contact shares and its 0.194 V budget

Same formula as `scripts/checks/partition35.py`: drop = I_rail × (R_wire + 1 mΩ) + 4.6 A × (R_wire + 0.5 mΩ), with R_wire = 0.013 Ω/m × 110 mm + 0.2 mΩ. Shares use the partition's own GH terms; the budget is rail conductor + 4.6 A return conductor (0.020 Ω each) + 40 mV protection + 20 mV distribution.

<!-- calc:reproduce -->
| Rail | Rail current, A | Partition figure, mV | Recomputed, mV |
| --- | --- | --- | --- |
| +12V | 2.1 | 15.321 | 15.321 |
| -12V | 2.0 | 15.058 | 15.058 |
| +5V | 0.5 | 11.113 | 11.113 |
| Wire term (hot wire plus terminations) | | 1.63 mΩ | 1.630 mΩ |
| GH worst single contact, JL | | 0.482 A | 0.482 A |
| GH worst single contact, JR | | 0.478 A | 0.478 A |
| GH worst single contact, P | | 0.479 A | 0.479 A |
| Rail-plus-return budget, +12V | | 0.194 V | 0.194 V |
| Rail-plus-return budget, -12V | | 0.192 V | 0.192 V |
| Rail-plus-return budget, +5V | | 0.162 V | 0.162 V |
<!-- /calc:reproduce -->

Only the wire term changes. The plane ceilings (1 mΩ rail, 0.5 mΩ common AGND), the 4.6 A single-return rule and every source-side term stay as the partition and the supply page define them.

## Each joint is about 0.40 mΩ on paper with the 19.00 mm body, a fifth of the 2.33 mΩ that the 20 mV limit allows

The joint is two bolted faces, the post body and the land with its vias on each board. The land transfer is counted here although the plane ceilings already include main-terminal transfer, so it is double-counted on purpose. The planning requirement is DERIVED from the 20 mV limit, not taken from the plan page's 0.5 mΩ.

<!-- calc:joint -->
| Term | JL, JR (19.00 mm), mΩ | P (17.00 mm), mΩ | Status |
| --- | --- | --- | --- |
| K face | 0.1000 | 0.1000 | ASSUMED (`face_ohm`) |
| front face | 0.1000 | 0.1000 | ASSUMED (`face_ohm`) |
| post body | 0.0881 | 0.0788 | DERIVED from ASSUMED brass resistivity |
| K land and vias | 0.0514 | 0.0514 | DERIVED (copper SOURCED) |
| front land and vias | 0.0649 | 0.0649 | DERIVED (copper SOURCED) |
| **Joint** | **0.4045** | **0.3952** | DERIVED |
| Planning requirement from the 20 mV limit (+12 V governs) | 2.328 | same | DERIVED |
| Plan-page planning figure | 0.500 | 0.500 | plan page, not derived |
<!-- /calc:joint -->

The two face terms carry half of the joint and are ASSUMED (0.10 mΩ each). The evidence need is the contact resistance of a nickel-finished brass face on an ENIG land at the ST-08 clamp torque, for Harwin R30-1011902 and R30-1011702, measured hot by Kelvin (#65 or the coupon). The joint stays below the 2.33 mΩ requirement until each face exceeds about 1.0 mΩ.

## The distribution drop falls to 7.11 / 6.97 / 4.86 mV, inside 20 mV on every branch

<!-- calc:drop -->
| Rail | JL / JR, mV | P, mV | Limit, mV | Margin at the worst branch, mV | Requirement on the joint, mΩ |
| --- | --- | --- | --- | --- | --- |
| +12V | 7.110 | 7.048 | 20 | 12.890 | 2.328 |
| -12V | 6.969 | 6.908 | 20 | 13.031 | 2.379 |
| +5V | 4.863 | 4.815 | 20 | 15.137 | 3.373 |
<!-- /calc:drop -->

## One header contact can carry 0.54 to 0.57 A: inside the 1.0 A working limit, over the old GH 0.5 A figure

The bound keeps the partition's method: 4.6 A, no equal-sharing credit. The candidate contact has the lowest measured MMS/TMM resistance and no board term. Every alternative has the highest initial resistance plus the 15 mΩ allowed change plus the full TW-SM pin, and all of them share the 0.5 mΩ common neck. The three AGND posts of the branch sit in parallel before that neck. Positions come from the candidate (264 on K: JL 54, JR 54, P 147, adapters 9).

<!-- calc:share -->
| Branch | AGND header positions | Minimum contact path, mΩ | Maximum other path, mΩ | All alternatives, mΩ | Worst single contact, A | Against 0.5 A (GH) | Against 1.0 A (working) | Against 1.6 A (proposal) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| JL | 54 | 4.36 | 33.02 | 0.611 | 0.565 | exceeds | meets | meets |
| JR | 54 | 4.36 | 33.02 | 0.611 | 0.565 | exceeds | meets | meets |
| P | 147 | 4.36 | 32.03 | 0.582 | 0.542 | exceeds | meets | meets |
<!-- /calc:share -->

The 0.5 mΩ common neck sets this bound, not the post. Even a 0 mΩ post leaves 4.6 × 0.5 / (4.36 + 0.5) = 0.473 A. The legacy limit of 0.5 A per contact belonged to the GH cable contact.

- **Working limit.** DA-02 set 1.0 A per header contact until Gate A-paper. The normal case (0.565 A) and every post-loss case below (at most 0.942 A, all three AGND posts of a jack board open) meet it.
- **Proposal.** 1.6 A per contact remains the ST-04 proposal. It is the most conservative row of report 154341 (all adjacent contacts powered, 30 °C rise, 20 % de-rating, printed page 14). That row was measured on MMS with TMM, so its transfer to the TW-SM pin is ASSUMED. A-paper sets the final limit; the closing measurement is the temperature rise of one stacker contact at the limit (#65 or the coupon).
- **Lower resistance bound.** It is a measured minimum of 192 points (4.36 mΩ, printed page 32), not a guaranteed minimum. The longer TW-SM pin can only raise it.

## EL fed from P stays under 8 mV on every rail

EL's own term reuses the partition's EL formula. It has six rail positions per rail and 12 AGND positions (DS-14), each at the maximum contact path with the −02 pin. The P-branch drop is added at its whole-domain bound. The EL load moves from K's planes to P's, but the P-branch ceiling already counts the whole delivered domain, so no branch current rises.

<!-- calc:el -->
| Rail | EL own contact term, mV | Plus the P-branch drop, mV | Limit, mV |
| --- | --- | --- | --- |
| +12V | 0.771 | 7.819 | 20 |
| -12V | 0.771 | 7.679 | 20 |
| +5V | 0.885 | 5.701 | 20 |
<!-- /calc:el -->

## The rail-plus-return budget falls from 0.194 to 0.181 V against 0.20 V (19.00 mm body)

<!-- calc:budget -->
| Rail | Rail conductor, V | Return conductor at 4.6 A, V | Protection, V | Distribution (worst branch), V | Total, V | Limit, V |
| --- | --- | --- | --- | --- | --- | --- |
| +12V | 0.042 | 0.092 | 0.04 | 0.0071 | 0.1811 | 0.20 |
| -12V | 0.040 | 0.092 | 0.04 | 0.0070 | 0.1790 | 0.20 |
| +5V | 0.010 | 0.092 | 0.04 | 0.0049 | 0.1469 | 0.20 |
<!-- /calc:budget -->

## A single AGND post at 4.6 A drops 1.9 mV and dissipates 9 mW; E23 deposits about 40 µJ in one joint

<!-- calc:single -->
| Joint | 4.6 A drop, mV | 4.6 A loss, mW | E23 energy in the joint, µJ | in the post body, µJ | Adiabatic body rise, K |
| --- | --- | --- | --- | --- | --- |
| JL / JR 19.00 mm | 1.861 | 8.56 | 40.4 | 8.8 | 8.3e-06 |
| P 17.00 mm | 1.818 | 8.36 | 39.5 | 7.9 | 8.3e-06 |
<!-- /calc:single -->

No maker states a current rating for any surveyed post (Harwin R30, Samtec SO, JSO). 4.6 A in one post is met on paper by its I²R only. The evidence need is a temperature-rise measurement at 4.6 A on the exact post (#65). The adiabatic rise uses ASSUMED brass density and heat capacity. The energy that lands in the contact spots is not localised here, because the spot size is UNSOURCED.

## DS-44 changes no electrical figure: joint, spreading and drop stay as in c1; only the JR keep-out screen moves

Attempt a2 applies DS-44. The JR +5 V and AGND1 to AGND3 lands move from x = 228, 245, 262, 279 (c1, +1.0 mm) to 227.5, 244.5, 261.5, 278.5 (+0.5 mm), on JR and K alike. P's AGND2 and AGND3 stay on `TAB-POWER-2` at (98.5, 175.0) and (110.0, 174.5); the catalogue posts stay R30-1011902 (19.00 mm) and R30-1011702 (17.00 mm).

- **Thread.** M3 stays. The store (`circuit-dev-resources` at `2aaef4c`, `harwin/`) holds the R30 M3 drawings and the M22 connector documents only; a 19.00 mm M2.5 catalogue post is UNSOURCED, so the M2.5 preference of DS-44 does not apply.
- **Unchanged figures.** No electrical term depends on the x of a JR land: joint 0.4045 mΩ (19.00 mm) and 0.3952 mΩ (17.00 mm), drop 7.110 / 6.969 / 4.863 mV, budget 0.181 / 0.179 / 0.147 V, worst header contact 0.565 / 0.565 / 0.542 A, the fault table and the P spreading of 0.191 to 0.226 mΩ are recomputed by the calculator below and equal c1's to the printed digit.
- **Changed figures.** Only the keep-out screen of item 5: the K counts move from 32 F.Cu and 83 B.Cu (c1) to the counts in the `moves` table below, and the JR panel-side head clears the locked jacks by 0.25 mm (courtyard 3.25 mm from the land centre against the 3.0 mm keep-out) and the clip LEDs by 0.04 mm (courtyard 3.04 mm), as DS-44 states. The jack courtyards still enter the 3.75 mm K-facing keep-out on B.Cu because a through-hole courtyard counts on both faces; the nearest jack pad on B.Cu is 6.94 mm from the land centre, so no locked part conflicts with the post face. No jack or LED moves.

## Item 1 (ruled): catalogue Harwin brass spacers, R30-1011902 at 19.00 mm and R30-1011702 at 17.00 mm, ±0.15 mm, matched per unit

DA-02 E10 decided this; nothing is made to drawing and nothing is selected or bought.

| Gap | Working code | Length | Status |
| --- | --- | --- | --- |
| JL and JR to K, 19.0 mm | Harwin R30-1011902: F/F hex, M3 × 0.5-6H through-tapped, A/F 5.30 to 5.50 mm, brass CW614N, nickel finish | 19.00 ± 0.15 mm | Length, tolerance, thread, A/F, material and finish SOURCED (R30-101 drawing issue 7, `3aaf7eaa…c236`). Current rating, contact resistance, torque and thread engagement UNSOURCED for the maker |
| P to K, 17.0 mm | Harwin R30-1011702, same series | 17.00 ± 0.15 mm | Same |

- **Matching.** The spacers of one unit that join K to JL and JR are matched within 0.05 mm of each other, and likewise P's (E10). The spread inside one lot is UNSOURCED; the per-unit measurement replaces it.
- **Plane.** K F.Cu sits at z = −30.6 mm. P keeps its 17.0 mm gap and therefore sits 0.2 mm farther back (E10).
- **Electrical effect.** The 19.00 mm body adds 0.0010 mΩ against 18.8 mm. That is +1.1 % of the body term and +0.25 % of the joint (0.4045 mΩ). The drop and budget tables above are at 19.00 mm.
- **Not compared again.** The soldered SMT spacer is refused (DS-15). The alternatives of attempt a1 (SO-1890, a part to drawing at 18.80 mm, a shim) are closed by E10. The part to drawing at 18.8 mm stays only as E10's way back.

## Item 3: the land is a 7.0 mm (front) or 7.6 mm (K) plated-hole ring with filled and capped vias

| Feature | K (post on F.Cu, washer and screw head on B.Cu) | Front boards (post on B.Cu, screw head on the panel-side F.Cu) |
| --- | --- | --- |
| Hole | 3.8 mm finished, plated: 0.6 mm over a 3.2 mm M3 clearance (DS-12 asks for at least 0.5 mm) | 3.2 mm finished, plated |
| Copper land | Ø7.6 mm on F.Cu and B.Cu; every layer of the net solid to the hole, no thermal relief | Ø7.0 mm on both faces; the radius of 3.5 mm leaves 0.5 mm to the JL/JR edge (y = 164 from y = 160) |
| Via ring | 16 × 0.3 mm drill, 0.6 mm pad at r = 2.9 mm; filled and capped (they lie under the washer, r 3.5, and the hex corners, r 3.175); drill web to the hole 0.85 mm | 12 × 0.3 mm drill, 0.6 mm pad at r = 2.2 mm; filled and capped (under the post face); drill web 0.45 mm |
| Contact annulus under the post | Ø3.8 to Ø5.3 mm (hex inscribed circle at minimum A/F) | Ø3.2 to Ø5.3 mm |
| Contact annulus under the washer or head | Ø3.8 to Ø7.0 mm (washer envelope ASSUMED) | Ø3.2 to Ø7.0 mm with a washer; Ø3.2 to Ø5.5 mm head only at JR (item 4) |
| Solder mask | Opening Ø7.6 mm, both faces; no paste | Opening Ø7.0 mm; no paste |
| Keep-out used in the screen | r = 4.05 mm, both faces | r = 3.75 mm, both faces |
| Transfer resistance (barrels only, hot) | 0.051 mΩ | 0.065 mΩ |

- **The oversize costs K the post-face contact width.** The 0.6 mm oversize narrows the post-face annulus from 1.05 mm to 0.75 mm radial on K. It also pushes the via ring out from r 2.2 to r 2.9, which is why the K land is 0.6 mm wider. Within the oversize, the post can sit off-centre on K by up to 0.3 mm. The narrowest annulus side is then 0.45 mm.
- **An outer ring of unfilled vias was screened first and rejected.** That variant was a Ø9.5 mm land with the ring at r 4.0 outside the washer. It put 120 B.Cu and 89 F.Cu footprints of K inside the keep-out.
- **Fabrication rules are UNSOURCED.** The 0.45 mm drill web on the front boards and filled and capped via-in-pad are the partition's existing process requirement (#65), not confirmed fab rules.

## Item 4: every land takes a screw from the panel side; at the DS-44 shift of +0.5 mm the JR heads clear the locked jacks by 0.25 mm and the clip LEDs by 0.04 mm

The post is held to the front board by an M3 screw from the panel-side face into the post's front thread. There is no solder in the structural path; the land is solder-free copper under the post face. The panel-side face carries the screw head with a washer. The panel gap is 8.0 mm for J (F.Cu at −10.0, panel rear at −2.0) and 9.8 mm for P (F.Cu at −11.8). An M3 head of about 3 mm plus a 0.5 mm washer fits both; the head height is ASSUMED, with no screw drawing retained.

| Front land | Panel-side face | K-facing face | Proposal |
| --- | --- | --- | --- |
| JL, six lands | Clear within r 3.75 | DH214, R215, R226, R227 within r 3.75 (R226 has no free position within 12 mm; see `envelopes.json`) | Screw and washer; move the three movable parts, re-place R226 by hand |
| JR, +12 V and −12 V | Clear | Clear | Screw and washer |
| JR, +5 V and AGND1 to AGND3, shifted +0.5 mm to x = 227.5, 244.5, 261.5, 278.5 (DS-44; c1 had +1.0 mm, which put the 5.5 mm head 0.25 mm into the jack courtyards) | Locked clip LEDs D13101 to D16101 at 3.04 mm and locked jacks J1410, J1510, J1610, J1710 at 3.25 mm, both outside the 3.0 mm keep-out of a 5.5 mm head without a washer | R7133, R7207, R7333, R7306 (movable); the jack courtyards count on B.Cu as through-hole parts, jack pads 6.94 mm away | Screw without washer, M3 (a 19.00 mm M2.5 post is UNSOURCED). The 0.04 mm LED margin is a planning-keep-out tolerance question accepted in DS-44. NEEDS_DESIGN stays only for the M2.5 option, if a post is found. No jack or LED moves |
| P, four lands moved to the power tab (y = 175) | Clear (the tab has no parts) | Clear | Screw and washer |
| P, AGND2 and AGND3 re-sited to (98.5, 175.0) and (110.0, 174.5) on the second tab segment (DA-02 ruling) | Clear (tab, no parts) | Clear | Screw and washer |

## Item 5: at the DS-44 positions K needs 82 B.Cu and 34 F.Cu footprints out of the 18 keep-outs; 20 have no free position within 12 mm

This is the a2 re-run of the screen at the DS-44 JR lands (+0.5 mm) and the re-sited P lands, against the geometry candidate as it stands at `21d1cd9`. At the c1 positions (+1.0 mm) the counts were 83 B.Cu and 32 F.Cu with 20 footprints having no free position; at the a1 positions 90 B.Cu and 33 F.Cu with 24.

- **Method.** The screen counts each footprint whose courtyard enters a keep-out circle: r 4.05 mm on K; on a front board, r 3.75 mm, or r 3.0 mm on the panel side of the four shifted JR lands, which carry a 5.5 mm head and no washer. A through-hole part counts on both faces. For each footprint it searches the smallest shift (0.25 mm steps, 24 directions, up to 12 mm) that clears every keep-out and every other same-face courtyard and stays inside the board outline.
- **Comparison with the plan page.** The plan page counted 54 B.Cu footprints within 2.6 mm, a smaller circle than the washer and via ring proposed here.
- **Data.** Per-footprint shifts and target origins are in `envelopes.json`.
- **Status.** This is a courtyard screen, not a copper clearance or a placement.

<!-- calc:moves -->
| Board | Face | Footprints in the keep-out | References | No free position within 12 mm |
| --- | --- | --- | --- | --- |
| K | F.Cu | 34 | C1242, C305, C4512, D2310, D4528, D4534, D4636, D8313, D8314, Q4504, R1141, R1157, R1289, R1290, R1298, R1299, R2395, R4501, R4504, R8334, R8342, R8349, R8362, R8363, RB4432, RB4433, RB4531, RB4633, RV2307, TP301, U1206, U1212, U4507, U4508 | none |
| K | B.Cu | 82 | C1120, C1135, C1247, C306, C4521, C4523, C4535, C4537, C4554, C4627, C8236, C8339, D2309, D2315, D4404, D4530, D4630, D4631, D4634, D4635, Q4502, R1171, R1187, R1188, R1198, R1199, R1230, R1236, R1263, R1277, R1294, R1296, R2360, R2362, R2378, R2379, R2394, R2396, R4269, R4503, R4518, R4558, R4578, R4594, R4595, R4597, R4598, R5241, R7115, R7204, R8129, R8130, R8253, R8261, R8262, R8319, R8320, R8357, RB1120, RB4228, RB4431, RB4632, RB4635, RV4504, RVO1207, RVO1210, TP304, U1207, U1210, U1214, U1215, U4506, U4518, U4520, U4535, U4545, U4608, U8210, U8211, U8309, U8310, U8311 | C1247, D4530, D4634, D4635, Q4502, R1277, R4578, R4595, U1207, U1210, U1214, U1215, U4506, U4518, U4520, U4545, U8210, U8309, U8310, U8311 |
| JL | F.Cu | 0 | none | none |
| JL | B.Cu | 4 | DH214, R215, R226, R227 | R226 |
| JR | F.Cu | 4 | J1410, J1510, J1610, J1710 | J1410, J1510, J1610, J1710 |
| JR | B.Cu | 8 | J1410, J1510, J1610, J1710, R7133, R7207, R7306, R7333 | J1410, J1510, J1610, J1710 |
| P | F.Cu | 0 | none | none |
| P | B.Cu | 0 | none | none |
<!-- /calc:moves -->

The six re-positioned joints, one by one:

<!-- calc:resited -->
| Joint | K land | K footprints in the keep-out | K, no free position | Front land | Front footprints in the keep-out | Locked hardware in the keep-out |
| --- | --- | --- | --- | --- | --- | --- |
| POWER-JR-+5V | (227.5, 160) | 6: D8313, R8334, R8342, RB4531, U8309, U8310 | U8309, U8310 | (227.5, 160) | 2: J1410, R7133 | J1410 |
| POWER-JR-AGND1 | (244.5, 160) | 6: C8339, D8314, R8349, R8362, R8363, U8311 | U8311 | (244.5, 160) | 2: J1510, R7207 | J1510 |
| POWER-JR-AGND2 | (261.5, 160) | 9: D4631, D4635, RB4228, RB4431, RB4432, RB4433, RB4632, RB4633, RB4635 | D4635 | (261.5, 160) | 2: J1610, R7333 | J1610 |
| POWER-JR-AGND3 | (278.5, 160) | 6: C4627, D4404, D4630, D4634, D4636, U4608 | D4634 | (278.5, 160) | 2: J1710, R7306 | J1710 |
| POWER-P-AGND2 | (98.5, 175.0) | 2: R2379, RVO1210 | none | (98.5, 175.0) | 0: none | none |
| POWER-P-AGND3 | (110.0, 174.5) | 7: D2309, D2310, R2378, R2394, R2395, R2396, RV2307 | none | (110.0, 174.5) | 0: none | none |
<!-- /calc:resited -->

RVO1210 and RV2307 on K are trimmers in ST-07's scope. U8309, U8310, U8311, D4635 and D4634 on K have no free position near the shifted JR lands. These claimed areas are listed for ST-07 (trimmer relocation) and ST-08 (tie posts) only; their files are not edited. Refdes with an `RVO` prefix are trimmers that ST-07 relocates. The 24 footprints of K with no free position need a manual placement or a land re-site in Phase 1.

## Item 6 (ruled): the power tab reaches y = 171.0 and a second segment carries AGND2 and AGND3; spreading stays under 0.5 mΩ on paper, but the P fixing cover worsens

- **Power tab.** The four P lands stand at y = 175, coaxial with K, on a tab spanning x = 139 to 196 and y = 171.0 to 176 (accepted). `p_tabs` with the 1 mm extension is ST-02 a3's re-run: NOT RUN here.
- **Second segment.** `TAB-POWER-2` spans x = 95 to 139 and y = 171.0 to 176, about 2.6 mm from O5 (x ≤ 92.4). It carries AGND2 at (98.5, 175.0), the ruling's first position, and AGND3 at (110.0, 174.5). (110.0, 174.5) is the best P-clear position of the a1 scan at x ≥ 110: 7 K footprints, 11.5 mm from AGND2. P is clear on both faces at both. P supports, frame and outline checks for the segment: NOT RUN.
- **Seven posts refused.** Dropping to seven posts is refused (DA-02): three AGND posts per branch is a partition rule.

### Common AGND spreading on K and P: up to 0.226 mΩ after the move, against the 0.5 mΩ ceiling (ASSUMED model)

Two of P's three AGND posts move about 110 mm west of the P pairs at x = 210 to 290. Each post path is modelled as the P plane from a sample load point to the post, plus the K plane from the post to the assumed K star at (258, 246), next to the inlet reservation.
- **Planes.** One AGND layer per board at 0.07 mm (2 oz), hot copper 0.295 mΩ per square.
- **Model.** Two-point resistance of an infinite sheet, R = Rs/π × ln(d/a), with a = 3.8 mm. The three paths are treated as independent and parallel.
- **What it ignores.** Voids, cut-outs and the overlap of parallel paths, all of which raise R. The model and the star position are therefore ASSUMED. Extraction of the routed planes (#38/#39) and hot Kelvin (#65) close it.

<!-- calc:spread -->
| Sample P load point | Old AGND sites: three post paths, mΩ | parallel, mΩ | Re-sited: three post paths, mΩ | parallel, mΩ |
| --- | --- | --- | --- | --- |
| (210, 182) | 0.451 / 0.289 / 0.421 | 0.124 | 0.451 / 0.677 / 0.661 | 0.192 |
| (250, 185) | 0.559 / 0.511 / 0.451 | 0.168 | 0.559 / 0.705 / 0.692 | 0.215 |
| (290, 185) | 0.608 / 0.575 / 0.543 | 0.191 | 0.608 / 0.727 / 0.716 | 0.226 |
| P worst header contact with the worst spreading added to each post path | | 0.581 A | | 0.586 A |
<!-- /calc:spread -->

- **Spreading.** The move raises the worst parallel spreading from 0.191 to 0.226 mΩ. That stays inside the 0.5 mΩ common ceiling on paper, with 0.27 mΩ left for the K-side neck and the lands.
- **Contact share.** Adding the worst spreading to each post path moves P's worst header contact from 0.581 to 0.586 A. It stays inside the 1.0 A working limit.

### The P pairs near x = 210 to 290 lose their two nearest fixings: 8 of 10 now lie beyond 40 mm and 5 beyond 50 mm

This uses the DA-02 E2 front-side rule: a P pair counts against P-to-K fixings only. The fixings are the 6 P posts, the 4 P kept supports and the 2 P provisional sites of ST-03 a2. With the lands at (210, 179) and (227, 179) as fixings, 4 pairs of the region lay beyond 40 mm.

<!-- calc:cover -->
| P pair | Centre | Nearest P fixing with the old lands, mm | After the re-site, mm | Change, mm | Against 40 mm |
| --- | --- | --- | --- | --- | --- |
| P-K-E5 | (286.5, 172) | 59.9 | 75.3 | +15.4 | misses |
| P-K-E4 | (269.5, 172) | 43.1 | 71.2 | +28.1 | misses |
| P-K-E3 | (252.5, 172) | 26.4 | 59.6 | +33.1 | misses |
| K-P-32 | (269.5, 192) | 44.4 | 52.0 | +7.6 | misses |
| K-P-35 | (252.5, 192) | 28.6 | 49.0 | +20.4 | misses |
| K-P-16 | (235.5, 192) | 15.5 | 45.8 | +30.2 | misses |
| P-K-E2 | (235.5, 172) | 11.0 | 42.6 | +31.6 | misses |
| K-P-18 | (218.5, 192) | 15.5 | 30.6 | +15.1 | meets |
| P-K-E1 | (218.5, 172) | 11.0 | 25.7 | +14.7 | meets |
| Summary | 10 pairs in the region; provisional sites counted: 2 | 4 beyond 40 mm | 8 beyond 40 mm | | 5 beyond 50 mm |
<!-- /calc:cover -->

- **What the move does.** Four more pairs pass 40 mm, and five exceed E2's 50 mm cap. This recount is NOT RUN in DA-02 and belongs to ST-08 with its declared sites.
- **Cover is ST-08's.** No fixing site is chosen here: the re-site turns the E2 cover of this region into a NEEDS_DESIGN item for ST-08. One option is DA-02's tie coaxial with an EL collar post on the EL tab.

## Item 2 and item 9: ±0.15 mm spacers matched within 0.05 mm per unit; the clamp path is K washer, post, front land, screw head

- **Clamp path.** Each post is in two series bolted joints. On K: screw head, washer, K B.Cu land, K laminate and plated hole, K F.Cu land, post end face. On the front board: post end face, front B.Cu land, front laminate, front F.Cu land, washer (or head alone at the four JR lands) and screw head. Laminate creep under preload is UNSOURCED (coupon C-6 class).
- **Load on the mated headers.** The posts set the gap. The stacker "A" rule keeps the connector bodies apart (body clearance 0.911 mm at 19.0 mm and 0.816 mm at 17.0 mm, E10), so the clamp load does not pass through a header. The draw-down force is ST-08's.
- **Length tolerance.** ±0.15 mm on the lot mean is accepted in the Z chain (E10; ST-03 a3 carries it, need 0.474 mm at 40 mm). The 0.05 mm per-unit match keeps the step between neighbouring fixings inside the 0.198 mm strain allowance at 40 mm (E3).
- **Owner of the remaining structural items.** Tie posts, jack screws, pilot pins and the closing fixture are ST-08's. This drawing (body, thread, lengths, tolerance, flat clamped faces) is the shared input.

## Item 8: SI-2 inputs: the unplugged-harness class goes, three assembly classes arrive

| Fault class | State | Surviving return paths | Worst single path current |
| --- | --- | --- | --- |
| Unplugged GH harness | Disappears: no harness between K and JL, JR or P | n/a | n/a |
| One, two or all three AGND posts of a branch loose or missing | New | The remaining AGND posts of the branch plus the branch's header AGND positions (JL, JR 54; P 147) | Worst single header contact in the table below; 4.6 A in one remaining post is already the design case |
| Partly seated stack (posts not drawn down) | New | Posts unclamped: face resistance unbounded; header contacts may be at partial insertion (2.13 mm minimum) | Not bounded; the closing check (continuity per ST-10) must precede power |
| Rail post loose | New | Rail through the other branches' K planes is not available (each branch has one post per rail) | The branch's rail is open; loads see the rail lost, not a ground fault; the #59 rail-loss case applies |
| EL pair unseated | Changed (was harness) | EL AGND from 12 positions on the remaining pairs | 170 mA return bound; not a share concern |

<!-- calc:faults -->
| Branch | 3 AGND posts, A | 2 posts (one loose or missing), A | 1 post, A | 0 posts (all open), A | Working limit, A | Proposal (ASSUMED transfer), A |
| --- | --- | --- | --- | --- | --- | --- |
| JL | 0.565 | 0.599 | 0.671 | 0.942 | 1.0 | 1.6 |
| JR | 0.565 | 0.599 | 0.671 | 0.942 | 1.0 | 1.6 |
| P | 0.542 | 0.560 | 0.590 | 0.652 | 1.0 | 1.6 |
<!-- /calc:faults -->

With every AGND post of a branch open, the worst header contact carries 0.65 A (P) to 0.94 A (JL, JR). That is inside the 1.0 A working limit by 0.06 A and below the proposed 1.6 A. The figure is an SI-2 input, not a design case.

Counts for the matrix: 18 posts, 9 of them AGND (3 per branch). Header AGND positions are 264 on K (JL 54, JR 54, P 147, adapters 9) and 12 between EL and P (DERIVED, DS-14; the plan page printed 6). The matrix itself belongs to the partition source in Phase 1.

## Joint coordinates and nets

The 18 joints are in `joint-design.json` → `joints`. Each joint has its net, its front and K coordinates, its gap and working catalogue code, and its candidate land references (TP990001 to TP990036). The coordinates are at the ruled positions: the four P-tab lands at y = 175, the four JR lands at +0.5 mm (DS-44) and P AGND2 and AGND3 on `TAB-POWER-2`. `old_P_agnd_xy` keeps the two former P positions for the cover comparison. The geometry candidate still holds the old positions.

## Checks: calculator and tests run; every physical and native check NOT RUN

- **Run:** `python3 scripts/checks/frozen_studies.py discover scripts/stack/power_posts` (no network, no KiCad), `python3 -m json.tool` on both JSON files, `pnpm circuit:check` before and after (a1, c1 and a2), and the plain-Python envelope screen at the ruled positions.
- **NOT RUN, `pcbnew` queries:** the plain-Python reader of ST-02 was enough.
- **NOT RUN, DRC and `regen-all.sh`:** forbidden by the brief.
- **NOT RUN, hot Kelvin joint resistance, temperature rise at the contact limit and at 4.6 A in one post, thread torque, push-out and laminate creep:** no part or coupon exists (#65).
- **NOT RUN, routed-plane AGND extraction:** the spreading is an ASSUMED sheet model.
- **NOT RUN, `p_tabs` and P supports and frame for both tab segments:** ST-02 a3.
- **NOT RUN, the E2 cover recount with declared sites:** ST-08.
