# MC04 route costing review: ACCEPT WITH CORRECTIONS (2 blocking, 9 non-blocking)

2026-11-28. Independent review of the draft `mc04-route-costing-20261128.md` (SHA-256
`d4bda821f77d53350476558c7f489df9f0f277e27db9d09959bfbc62da95830e`, verified, uncommitted) and the appended DS-199
row, at head `27448163` of `local/cloud-engineering-20261127`. The reviewer is not the author. Read-only, except
for this file. No search and no simulation was run; the S15 figures were re-read from the cached `screen.json`
(`76d2e8e5…3304152f`, verified). Desk estimate only; every board and schematic stays an unvalidated draft and
nothing is adopted.

Both blocking findings are wording corrections to two claims. The recommendation survives them.

## The recommendation stands on U8409 alone: test the L03.01 re-plan first

U8409 has no supported route on record other than a change to P-K-P-L03.01, and the gate needs all five ICs. That
is enough for option 1. The second leg of the argument, that U5210 also waits on L03.01, does not hold as written
(finding 1). The four options stay inside the project rules: nothing is bought, quoted, built or adopted, each
study needs a brief and a review, and the unavailable checks are listed as `NOT RUN`.

## The quoted figures match their records, with the exceptions in the findings

- **S9 packet and S9-A.** Far poses 38.71, 40.61, 49.65, 80.61 and 113.22 mm; grown nodes +45.6, +92.7, +129, +235
  and +69 mm; "near 27 pF"; the three overlapping poses; "likely to fail"; TSSOP courtyard 7.70 × 5.99 mm; 40.61,
  49.34, 79.21 and 113.22 mm; U1415 at 22.5 mm with seven passives, three of them C1302, C1303 and R1321. All match.
- **Link record at head.** 62 live links. L12.02.01.02 8-way, 6 circuits, 3 riders; L03.01 26-way, 25 circuits, 6
  sites; L13.01.01.02 7 circuits, 2 riders; L13.01.02.01 8 circuits, 4 riders; L13.01.01.01 8 of 8; L08 40-way, 27
  circuits, 9 sites. All match.
- **Decisions.** DS-110 (339 unused positions, 122 connectors), DS-128 (61, 122, 83), DS-143 (73 packages, 62 and
  124, 0 mA), DS-145, DS-149, DS-150, DS-185 and DS-186 are quoted correctly.
- **S12 and S15.** 16 and 28, 131 at A3, 25, 81 and 5358, and 787 class-legal slots of L08 match. 4686 of the 5358
  joint-only slots give an L03.01 conflict as their first reason, so "mostly" is fair.
- **S14.** 16 pF on three control sets with the capacitor, class A 2 pF against 4.3 to 16.3 pF, nine cells, about
  7° at 20 kHz, class B already carrying `C_FB`, and the blocking classes per IC match the disposition.
- **Route C, re-read from the cache.** 5.53 mm at (159.0, 229.0) +y, 11.08 mm at (200.92, 199.67) +y and 19.70 mm
  at (167.75, 189.0) +y are reproduced, as growth of the tree figure against the base. For L03.01 the minimum over
  all 131 slots is 12.0 mm, 25 failing nets and 4 moved ICs.
- **Inventory.** OPA4196IDR (SOIC-14), OPA4197IDR (SOIC-14, "precision candidate"), OPA4197IPWR (TSSOP-14) and
  KEMET C0603C100J5GACTU (`bipolar_attenuverter:C_FB`) are present. No OPA4196 TSSOP and no OPA196-family dual is
  present.

## Estimates and part candidates are marked honestly

The blanket estimate statement, the per-section "(estimate)" marks and "Not established" cover the workload, link
count, capacitance and risk figures. The two candidates carry no part number and are labelled as not in the
inventory. OPA4197IPWR is correctly excluded with the DS-145 reasons: 0 mA of +12 V margin and no simulation of
these cells with that part. The owner's choice of DS-198 option 1 at 14:41Z is taken from the draft; the reviewer
has no record to check it against.

## Findings

### 1. Blocking: "U5210 cannot be placed while L03.01 stands" is false under route C

- **Location.** Route C "Against it" ("U5210's best slot still needs L03.01 out of its way in a joint scene");
  U5210 table, route C row ("needs L03.01 moved too", "nothing while L03.01 stands"); "What the comparison shows"
  point 3; option 1 ("It decides U8409 and U5210 either way"); the recommendation's reason; DS-199 and DS-200.
- **Defect.** The slot the draft itself quotes, L13.01.01.01 at (200.92, 199.67) +y, is gate-legal with L03.01 at
  its record. In the S15 screen it claims U5210 and passes A1, A3, A4 and A6. It fails only the no-growth rule:
  11 nets, two passive face changes (R5260, R5263), largest growth 11.08 mm on two link-carried nets on P, and
  6.44 mm at most on a protected node (`/M4B/Cfaa69a_DRIVE`). 51 of the 81 legal slots pass the four acceptance
  items in the same way. The dependence on L03.01 holds under DS-150 (S12) and under no-growth (S15), and for the
  5358 joint-only slots. It does not hold under a growth bound.
- **Required correction.** Limit the claim to the present rules and to route A. In route C, state that U5210 has
  a rows-level slot with L03.01 standing, at about 11 mm, with the overlay items and A12 not run. Reword point 3,
  option 1, the reason and both decision rows, and update the hash in DS-199. "Realistic yield: U5110 at best"
  needs the same care.

### 2. Blocking: "U8409 has no other route" is stated as fact and holds only on the record

- **Location.** U8409 heading and table; point 3; the recommendation's reason; DS-200.
- **Defect.** The draft's own table rates the far pose "unlikely", not excluded. The TSSOP result is S9-A's:
  links at record, 24 mm, and one combined arm that failed on C8438. It was not repeated under the 35 mm radius of
  DS-149. No route considers the parts that lose their position: U8411 in 124 of the 131 slots, U8313 in 48 and
  U8310 in 31.
- **Required correction.** Write "no other route with support on record". Say what each exclusion rests on and
  what was never studied.

### 3. Non-blocking: the route C column "Protected ICs moved" counts unprotected ICs

- **Location.** Route C table; U5110 table ("one IC changes face"); "Face changes of an IC (NG4) add vias".
- **Defect.** U5201 (U5110's slot), U4222 and U4227 (U5210's slot) are not protected. U5207 (U5209's slot) is. Of
  the four ICs in L03.01's best slot only U8411 is. In U5110's slot no IC changes face: the four face changes are
  D5107, R5149, R5152 and R5268, two of them protected.
- **Required correction.** Head the column "ICs moved" and give the protected count beside it (0, 0, 1, 1 or
  more). Correct both face-change sentences.

### 4. Non-blocking: the route C figures do not state their reference or their count rule

- **Location.** Route C table and the sentence under it.
- **Defect.** Growth is measured against the base. Against the S15 limit (the smaller of paper and base) U5209's
  figure is 27.2 mm. "Nets that lengthen" is the count of nets failing NG1 to NG3 (8, 11, 26); the nets whose
  tree grows are 5, 9 and 18. Four U5110 slots tie at 5.53 mm. The "1 to 4 pF" omits the 1.5 factor the campaign
  estimate uses elsewhere; with it the range is about 1.7 to 5.9 pF.
- **Required correction.** State the reference and the count rule, and use one estimate basis.

### 5. Non-blocking: route C is mis-costed for U1415, and a class-distance route is missing

- **Location.** U1415 table, route C row; route list.
- **Defect.** U1415's blocker is L08's class distance, not a protected part (S12 disposition, DS-161). Loosening
  DS-150 does not address it, so "unknown, 1 cycle" overstates the route. An exception to L08's class distance is
  not listed as a route or excluded with a reason.
- **Required correction.** Mark route C as not addressing U1415's cause. Add the class-distance route or say why
  it is left out.

### 6. Non-blocking: the route A totals disagree

- **Location.** Route A "Workload"; point 5; the per-IC tables.
- **Defect.** "2 to 4 cycles for all five", "about 3 to 5 cycles" and a per-IC sum of 6 to 9 are three different
  totals. It is not said whether the generator task is inside them.
- **Required correction.** Give one total and say what is shared between ICs.

### 7. Non-blocking: option 1 says "25 signals"

- **Location.** Owner options, option 1.
- **Defect.** L03.01 carries 15 signals and 11 grounds on 26 positions, with 25 circuits needed.
- **Required correction.** Write "25 circuits (15 signals and their grounds)".

### 8. Non-blocking: "38 of 64 fail with no stray at all" is the S13 label count

- **Location.** Route C "Against it".
- **Defect.** S14 re-scored class A's 11 rows to "no headroom, 2 pF", and S13's 15 class B rows fail only at the
  pair corner with IN- at 50 pF.
- **Required correction.** Cite it as the S13 label count and add the S14 re-score.

### 9. Non-blocking: route D for the four quads is "none on record", not "nothing"

- **Location.** Route D; route D rows of U8409, U5210, U5209 and U5110.
- **Defect.** "Combined with connector moves, none was clean" covers three of the four: the combined arm was not
  run for U5210. The room study is bounded as in finding 2.
- **Required correction.** Write "none on record (S9-A, 24 mm)" and note the arm that was not run.

### 10. Non-blocking: the S15 disposition names a route the costing does not mention

- **Location.** U8409 table, route E.
- **Defect.** The S15 disposition lists "a remote buffer for U8409" as a DS-149 fallback. DS-149 says "simulation
  for U8409", which S13 and S14 ran.
- **Required correction.** Add one line that reconciles the two.

### 11. Non-blocking: the spare-position figure is the 2026-11-15 one

- **Location.** Route A "On record".
- **Defect.** The draft quotes 339 unused positions on 122 connectors from DS-110. The `unused` fields of the 62
  live links at head sum to 322 on 124 connectors.
- **Required correction.** Give the head figure beside the DS-110 one.
