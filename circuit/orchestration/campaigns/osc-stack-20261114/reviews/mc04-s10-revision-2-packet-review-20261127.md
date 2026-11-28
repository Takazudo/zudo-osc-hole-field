# Independent review of the MC04-S10 Revision 2 decision packet (2026-11-27)

Reviewer: independent design-authority review, model `claude-fable-5-2` (Fable 5.2). I did not write the packet.
Under review: `../mc04-s10-revision-2-decision-packet-20261127.md`.
Repository `zudo-osc-hole-field` at `80569b5375087df519b79ead67d1bf56c16301e6`, read-only; nothing in it was changed,
no generator, regeneration or KiCad step was run. Every board and schematic stays an unvalidated draft.

## Verdict: RETURN

The packet's headline holds and is in fact stronger than stated: no S10 Revision 2 generator run is admissible.
It is returned because one "evidenced" claim is false, the recommended step 2 study is already decided by retained
data, and the study contract contradicts itself. No new investigation is needed to correct it; the numbers are below.

## Claim table: 11 confirmed, 1 refuted in part, 1 confirmed with an undercount, 1 reclassified

All figures are from my own scripts in `scripts/stack/studies/mc04_s10_r2_packet/review/` (own S-expression parser, own scene builder).
The packet's scripts were read only to explain one disagreement (claim 5).

| # | Claim | Result | My numbers |
| --- | --- | --- | --- |
| 1 | 7.93 first appears as a rounded display value, with no electrical derivation | CONFIRMED | `slot_moves_a2.py` 207–208 `r2(dist(...))`; `r2 = round(v, 2)` in `replacement.py` 66–67; first retained occurrence is `result-a2.json` `joint_scene.parts_re_placed[20]` (R5257) at `8243acdf`; then report line 78, DS-147, brief lines 32/78/112, `overlay.py` line 33. No capacitance, length or margin derivation exists in `circuit/`, `scripts/stack/` or `design/`. |
| 2 | Paper poses and the integer inequality | CONFIRMED | R5257 (174.66, 199.89) B 90°, U5210 (180.97, 204.70) B 0°, identical in `adopted-placement-pins.json` and `floorplan-candidate.json` at `6093081c`, `8243acdf`, `6e5716e7`, `32580f77` and HEAD, and on the interim K board. 631² + 481² = 629522 > 793² = 628849; distance 7.934242244852375 mm; excess 0.004242 mm. |
| 3 | `/W1/F2_SUM` has exactly three pins; R5256 is on F | CONFIRMED | U5210.6, R5256.2, R5257.2. `/W1/F2_OUT`: U5210.7, R5257.1, R5258.1, R5259.1. Identities match `io-partition.json` and the inventory (OPA4196IDR C2057385 `line-op-audio`; RT0603BRD07100KL `line-r-precision`; R5255/R5258 MPN empty). R5256 (175.39, 196.16) F. |
| 4 | Pad-centre figures 11.949 and 11.795 mm | CONFIRMED | R5257.2 (174.66, 199.14) → U5210.6 (183.445, 207.24): 11.9493 mm. R5257.1 (174.66, 200.64) → U5210.7 (183.445, 208.51): 11.7946 mm. Same in the candidate scene. |
| 5 | Interim copper 26.160 mm / 3 vias and 35.807 mm / 5 vias, "neither reaching U5210.6 or U5210.7" | **REFUTED in part** | Lengths and via counts confirmed (26.1595 mm, 3 vias; 35.8072 mm, 5 vias; no zone on either net). The gap does not exist: see defect 1. |
| 6 | S9-A2 candidate coverage | CONFIRMED, with an undercount | 16 of 16 pairs re-place R5249, R8221, R8331. 81 of 81 L13.01.01.01 candidates re-place R8356. 4 of 14 clean first-link candidates were paired. R8456 is moved in 79 of 81, not 7: see defect 4. |
| 7 | Six protected movements, four shifted-row movements, node extents | CONFIRMED | All ten poses, distances and causes match. Node pad extents (paper / pre-S10 / candidate, mm): FOLDER_SUM 85.875 / – / 85.875; F2_SUM 19.865 / – / 16.885; Ca92eeb 80.395 / 80.395 / 80.395; M4A C38051c 84.495 / 84.495 / 71.176; C24ce01 84.395 / 84.395 / 93.941; REF9_FB 34.013 / 34.013 / 33.553; M4B C38051c 48.765 / 45.515 / 55.015; W2 FOLDER_SUM 74.980 / 69.480 / 73.105; F1_SUM 30.555 / – / 33.383; Cfaa69a_FB undefined (U8409). Pad-to-pin distances match to 0.001 mm. Eight returns to paper confirmed (R5226, R5228, R5247, R5250, R5251, R5260, R5263, U5207). |
| 8 | Five locality discrepancies, all predating S10 | CONFIRMED | U5113 84.7728 mm to gate row (73.887, 118.9205) against 65.97 recorded. U5112 118.3 mm / 23.7 pF / R5108 59.8 and 84.3 / 16.9 / R5112 44.3. U4646 D4601 48.7; 103.3 / 20.7 / R4612 33.0. U4417 L016 114.51, L018 100.88, L021 72.56, RISE 112.26, START 100.88, TOP 96.08 (36.89–40.42 pF). U4526 CURVED 75.81, L069 75.81, L070 95.25, RISE 27.03, TOP_RAW 19.21. Pre-S10 equals candidate for every one; the gate rows involved exist at `8243acdf` and not at `6093081c`. IC distances 52.56, 46.89, 48.84, 26.71 match. |
| 9 | U4526 HOLD_N and READY | CONFIRMED | HOLD_N 39.81 mm / 25.01 pF → 65.25 / 30.10 (overlay), 50.31 / 27.11 (overlay withheld). READY 22.39 / 36.38 pre-S10 (4.12 / 32.73 recorded) → 30.64 / 38.03 (overlay), 32.89 / 38.48 (withheld). U4537 is the only changed footprint on both nets. |
| 10 | 56 movements, 16 face changes, no rotation-only change, gate rows identical | CONFIRMED | 56 with the same reference set as `overlay.json`; 16 face changes (18 if U5209 and U5210 gaining a face are counted); none rotation-only. Row changes 18 removed, 21 new, 15 shifted. `replacement.footprints` identical at `32580f77`, `557b5a6e` and HEAD. Withheld poses and decoupler distances match (C4239 7.66 / 24.87 / 6.85; C4244 17.67 / 20.90 / 6.85; C4554 5.06 / 7.04 / 5.06; U4227 13.18 mm from pre-S10). |
| 11 | First-order loop estimate | CONFIRMED as arithmetic only | 31.4°, 24.1°, 21.3°, 17.1° at 0, 5.96, 10, 20 pF with GBW 2.5 MHz, 8.0 pF, 50 kΩ. I opened the datasheet copy (SHA-256 `d89dd600…793d`): GBW 2.5 MHz typical, ZID 100 MΩ ∥ 1.6 pF, ZIC 6.4 pF. Labelling: see defect 7. |
| 12 | `input-buffer-vendor.json` does not cover U8208, U8310, U8311, U4240 | CONFIRMED | Instances are U1216, U1416, U1518, U4346, U8314, U8417 only. The 45° criterion is labelled ASSUMED there. |
| 13 | Coordinate equality is an owner decision | **NOT SUPPORTED** | It is within delegated design scope: see defect 6. |
| – | Input table | CONFIRMED | All 42 SHA-256 rows reproduce. |

## Defects to correct before filing

### 1. The interim K board does route the F2 loop to U5210 pins 6 and 7 (HIGH)

Tested by copper geometry (pads as rectangles, tracks buffered by half their width, vias across their layer span):
each net is one connected component containing every pad.

| Net | Track end | U5210 pad | Result |
| --- | --- | --- | --- |
| `/W1/F2_SUM` | (184.375, 207.05) B.Cu, 0.2 mm | pin 6, 1.95 × 0.6 mm at (183.445, 207.24) | end is inside the pad |
| `/W1/F2_OUT` | (182.55, 208.25) B.Cu, 0.15 mm | pin 7, 1.95 × 0.6 mm at (183.445, 208.51) | end is inside the pad |

The packet's `f2_sum_connectivity.py` looks for track ends within ±0.45 mm in x of the pad centre; a SOIC pad is
1.95 mm long, so it missed ends 0.93–0.95 mm from the centre. Corrections:

- delete "neither reaches U5210 pin 6 or pin 7" and "No routed loop exists"; the paper state has a routed F2 loop
  (summing node 26.16 mm, three vias);
- move "their gap at U5210" out of the "Evidenced" row;
- use the routed 26.16 mm (5.2 pF at 0.20 pF/mm, vias excluded) beside the 5.96 pF pad estimate.

The absence of link-era routing and of any stability evidence still stands.

### 2. The recommended S10R2-A study is already decided by retained data: zero survivors (HIGH)

`result-a2.json` reports `caps_reached: []`, so its enumeration over the 2.0, 0.5 and 0.25 mm grids within 24 mm is
complete. The packet proposes the same domain.

| Link | Complete accepted set in S9-A2 | Protected parts at paper under each one |
| --- | --- | --- |
| P-K-P-L13.01.01.01 | 81 (3, 20, 81 per grid; all +y, x 200.92–202.92, y 197.42–201.67) | R8356 courtyard [204.75, 206.5, 206.57, 209.78] under the K connector in 81 of 81 (also under the K tail in 8) |
| P-K-P-L13.01.01.02 | 17: three displace U5207, C5205, C5206; 14 at x = 176.0 | slot alone: R5254 (`F1_SUM`) for y 192.25–195.0; R5256 for y 194.75–197.0; R5257 for y 198.25, 198.5; R5259 (`F3_SUM`) for y 192.75–195.0 |

The rejection reasons for L13.01.01.01 name only L03.01, L15.02.01.01, panel hardware, fixings, U8409 and U5210.
None names L13.01.01.02 or L13.01.02.01, so moving those two links cannot add a candidate. U5210 cannot return to
paper unless L13.01.01.01 moves. Therefore no slot-only scene on this domain frees U5210 without displacing R8356.

Corrections:

- replace "Whether any protected-clean scene exists is unknown" and "The ten unpaired ones are untested, not
  excluded": all ten have their slot over R5254 or R5256;
- drop step 2 as written. It would end at its own stop "zero preflight survivors for any link", and it repeats a
  search that DS-150 already ruled out as slot-only;
- record the negative result without a run and take the "no clean scene" alternatives to the owner now;
- add the omitted alternative of a wider domain for L13.01.01.01 (beyond 24 mm, up to the 35 mm join radius that
  DS-149 allowed for other links). That is a different search and needs its own ruling.

### 3. The study contract contradicts itself and is incomplete (HIGH if any study is kept)

- **Reference pose.** "Each at its pre-S10 effective pose" cannot apply to U5209 and U5210, which have no pre-S10
  position, and it conflicts with "placed at paper".
- **Returns to paper.** Moving the three links removes gate rows of R5226, R5228, R5247, R5250, R5251, R5260, R5263
  and U5207. Four of these change face on return (R5251, R5260, R5263, U5207). The acceptance text forbids a
  shifted or face-changed protected footprint, so every possible scene fails. State the reference as paper and rule
  explicitly whether a return to paper is allowed.
- **Tail rectangle.** The gate does not displace parts under a K tail: at `32580f77` R5259 is listed in
  `under_tails` of L13.01.01.02 and has no row. A preflight that rejects on the tail is stricter than the gate.
  Define which applies, and say so for R5259, which the proposed wording pins at (177.89, 194.16) B under that tail.
- **Open ICs.** S9-A2 rule 4 (no candidate covers the recorded courtyard, grown 0.35 mm, of U1415, U5110, U8409) is
  not restated. They have no pre-S10 pose, so the protected-set wording does not reach them.
- **Run bounds.** No memory limit and no expected run time; ORCHESTRATION.md section 3 requires both.
- **Tests.** No positive control. The preflight must reproduce the known result at `32580f77` (R5249, R5256,
  R8221, R8331, R8356) before it is trusted. Add mutations for a candidate over U8409's courtyard and for R5259.

### 4. The coverage table undercounts knock-on moves and misstates its source (MEDIUM)

- R8456 (`/M4B/C24ce01_W_SENSE`) moves in 79 of 81 L13.01.01.01 candidates: 7 directly, 72 as a passive moved by
  the U4222 block. R4238 (`/E2/REF9_FB`) moves in 72 of 81 the same way. C8408, R7215, R7219 and R8471 move in 4.
- The row for x = 176.0 is not "read from `result-a2.json`": no pair record lists R5256 or R5257. It is a geometric
  result and must be labelled so. It also omits R5259 under the K tail at all four y values.

### 5. Rebasing the locality limits is an unlabelled ruling item (MEDIUM)

The contract limits `/E5/READY` to 22.39 mm, the pre-S10 effective value; the accepted record says 4.12 mm. Step 3
compares `locality-acceptances.json` "against pre-S10 effective geometry". Brief Revision 1 stops on "a worse figure
in `locality-acceptances.json`". Changing the comparison basis is a change to that stop and must be listed as a
ruling. The five inherited mismatches need their own disposition outside S10: U5113 sits at 84.77 mm against an
accepted 65.97 mm, and U4417 nets exceed their records by up to 29 mm.

### 6. Coordinate equality is within delegated design scope, not an owner decision (MEDIUM)

- DS-147, which set the number, is a design-authority ruling under DS-03.
- DS-150's "Reverse by" is "an evidence-backed prospective change to the conflicting conditions, followed by a
  separately admitted joint candidate and independent review". It does not name an owner message.
- Under DS-150's own stop rule R5257 (on `F2_SUM`) may not move and U5210 must return to paper. The distance is then
  fixed at 7.934242 mm, so the numeric condition is subsumed.
- The 2026-11-23 review, finding 3, already asked for this wording.

"A distance exception of 0.004242 mm" mislabels a rounding artefact as an exception to a limit that the packet
itself shows has no electrical basis. Correct sequence: a design-authority ruling in a new decision row, with the
owner notified. Keep the owner card for the real choice in defect 2. As written, step 1 spends an owner round trip
on a change that unlocks nothing.

### 7. The loop estimate is labelled as an assumption but worded as a finding (LOW)

Change "says the node is sensitive even at paper" and "Separate finding for the owner" to "estimate suggests".
Add the missing assumptions: IN+ (`F2_CLIP`, 10 kΩ and clamp) treated as AC ground; small-signal, clamp not
conducting; amplifier second pole and output impedance ignored, so the model figure is not a lower bound.
The recommendation to run the vendor-model simulation is sound.

## The recommended sequence is not sound as written; the safety of what it fixes is

| Question | Finding |
| --- | --- |
| Repeat of the identical failed search | Yes for step 2: same links, grids, radius and cap as S9-A2, with a stricter acceptance (defect 2) |
| DS-150 protected-part rule | Not weakened; the proposed protected set is wider |
| DS-149 and U1415, U5110, U8409 | Links L07, L08, L12.02.01.02, L03.01 stay fixed and no placement is proposed; rule 4 must be restated (defect 3) |
| Electrical claims | Estimate is under "Assumed" and marked "must not be cited as a margin"; wording fix in defect 7 |
| Checks | NOT RUN items are stated with reasons; no generator, oracle or search was run by the packet or by this review |

## Review scripts

| Script | Purpose |
| --- | --- |
| `scripts/stack/studies/mc04_s10_r2_packet/review/lib.py` | S-expression parser, board reader, `git show` helpers |
| `scripts/stack/studies/mc04_s10_r2_packet/review/r1_f2.py` | paper poses at five commits, integer check, net membership, identities, pad distances, copper lengths |
| `scripts/stack/studies/mc04_s10_r2_packet/review/r2_conn.py` | copper connectivity by geometry for `F2_SUM` and `F2_OUT` |
| `scripts/stack/studies/mc04_s10_r2_packet/review/r3_scene.py` | pre-S10, gate-only and candidate scenes; row changes; protected movements (writes `scenes.json`) |
| `scripts/stack/studies/mc04_s10_r2_packet/review/r4_nodes.py` | node pad extents and pad-to-pin distances |
| `scripts/stack/studies/mc04_s10_r2_packet/review/r5_locality.py` | locality distances, grown nets, input runs, U4526 figures |
| `scripts/stack/studies/mc04_s10_r2_packet/review/r6_pm.py` | loop estimate arithmetic |

S9-A2 coverage, the rectangle test of the 14 first-link candidates, the hash table and the datasheet rows were
checked with inline one-off scripts; their inputs are `result-a2.json` and `floorplan-candidate.json` courtyards.

## Limits of this review

- The rectangle test in defect 2 uses ungrown floorplan courtyards against the slot, K tail and K connector
  rectangles from `result-a2.json`. Gate growth can only add overlaps.
- The overlay block poses were taken from the retained `overlay.json`; the overlay search itself was not re-run.
- `overlay.py --check`, `test_s10`, `regen-all.sh`, `pnpm circuit:check`, KiCad and ngspice: NOT RUN, read-only review.

## Re-review of packet revision 2: ACCEPT WITH CORRECTIONS

Same reviewer and model (`claude-fable-5-2`), same read-only constraints; nothing was run in the repository.
Scope: the seven defect corrections, the author's qualification on defect 2 and the new owner question.
The verdict heading at the top of this file applies to packet revision 1 only.

### All seven defects are closed

| # | Defect | Result in revision 2 |
| --- | --- | --- |
| 1 | Interim copper reaches U5210 | CLOSED. Routed loop stated (26.160 mm, 3 vias; 35.807 mm, 5 vias; track ends inside pads 6 and 7); the wrong script is removed; the "Evidenced" row is corrected |
| 2 | Study predetermined | CLOSED. Study dropped; negative result recorded without a run; the two "unknown" statements are gone |
| 3 | Contract contradictions | CLOSED. No study is kept; all six points are carried as requirements for a future brief, including paper as reference, returns to paper allowed, rule 4 and the positive control |
| 4 | Knock-on undercount | CLOSED. R8456 79 (7 + 72), R4238 72, four others in 4; the x = 176.0 rows are labelled geometric; R5259 under the K tail is stated |
| 5 | Locality rebasing | CLOSED. Both items are listed as unsettled rulings; "up to 29.01 mm" is right (114.51 − 85.5) |
| 6 | Decision level | CLOSED. Coordinate equality is proposed as a design-authority ruling with the owner notified |
| 7 | Estimate wording | CLOSED. Reworded; five assumptions listed; "not a lower bound" stated; 5.23 pF row matches my 24.7° |

### The author's qualification on defect 2 is correct and does not change the result

- The 370 figure is right: rejections for "slot on K field of P-K-P-L13.01.02.01" are 4, 102 and 370 on the three
  grids, so the L13.01.01.02 set does depend on L13.01.02.01, and U5209 alone is not proven exhaustive.
- U5210 is decided by L13.01.01.01 alone. On the 0.25 mm grid its link-caused rejections name only L03.01 (143)
  and L15.02.01.01 (2684). Neither is one of the other two L13 links, and both were fixed in the dropped study.

### Corrections to make before the owner question is posted

1. **Option 1 does not move L15.02.01.01, which is the main blocker (MEDIUM).** The option lists DS-149's four
   links plus the three L13 links. L15.02.01.01 is in neither group and is held at (193.0, 213.0) by DS-148. It
   causes 2684 of the 2827 link-caused rejections of L13.01.01.01 on the 0.25 mm grid; L03.01 causes 143. The
   sentence "a joint search is the only one that can move them" is therefore wrong for L15.02.01.01. State one of:
   - it stays held, so option 1 rests on L03.01 moving and on the 24–35 mm ring; or
   - it is released, which changes DS-148 and must be named in the option.
2. **Name everything option 1 changes (LOW).** It widens DS-149 (three more links at 35 mm), replaces DS-150's
   "S11 awaits an accepted S10", and supersedes the S11 brief's start gate, pin and "every slot hold in the pinned
   options file". The study must read the `6e5716e7` snapshot, because HEAD carries the returned candidate's gate
   rows and holds.
3. **Say that options 1 and 2 are not exclusive (LOW).** The fold-cell simulation is also U5110's DS-149 fallback
   and the packet itself calls for it; the owner should see that it can be admitted alongside option 1.
4. **Refresh the review hash (LOW).** The input table cites this file at `eee8cf0e…`; this appended section
   changes it.

### The owner question is correctly the owner's

Coordinate equality and the negative result sit with the design authority under DS-03. Option 1 changes two
owner-supplied rows (DS-149 scope, DS-150 start gate), options 2 and 3 change the DS-150 rule, and option 4
returns the DS-60 alternatives. Recommending option 1 is reasonable once correction 1 is made: it keeps the
protection intact and removes the S10/S11 deadlock. Whether any scene exists out to 35 mm is not established.
