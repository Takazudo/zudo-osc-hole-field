# MC04-S15 brief review: ACCEPT WITH CORRECTIONS (7 blocking, 6 non-blocking); not admissible at Revision 1

2026-11-28. Issue #367 (MC-04 paper gate). Independent review, model `claude-fable-5-2`, read-only.

Subject: `mc04-s15-no-growth-moves-brief-20261128.md`, Revision 1, SHA-256
`c7dd0d3299a02e887e92285bcaf4a2fcfdad94011acd968544fef123c9be97dc` (verified), with the uncommitted DS-188 row in
`decisions.md`, at head `935a2943` of `local/cloud-engineering-20261127`.

The brief does what the owner chose: one geometric rule with its own controls, then one search, with geometric
evidence only. The plan is sound. The rule as written cannot be run as it stands and is looser than the owner's
sentence in three places. Revision 2 must apply findings 1 to 7 and be reviewed again before admission. No search
was run for this review, and no file other than this one was written.

## What was checked, and how

| Check | Result |
| --- | --- |
| Brief SHA-256 | matches |
| The nine input hashes in the brief's table, and `placements.lock.json` `297300b0…5b88dbe8` | all match |
| `joint_search.py --check` at `935a2943` (`/home/user/venv312/bin/python`) | passes: input pins, P3, P4, P11, 0 scenes, 6 checkpoint digests; 31 s |
| Read-only probe of the S12 `World` (scripts kept outside the repository) | 6640 footprints, 1734 protected, 5 positionless at the base, `ROUTE_FACTOR` 1.5, 71 protected footprints under a K tail, 62 live links; figures below |
| S12 code read: `s12.py` (`census`, `check_rules`, `t1`, `t2`, `check_rows`, `base_effective`), `joint_search.py` (`stage2`, `legal_entry`, `cluster_search`, `drive`), `overlay.py`, `links_gate_part2.py` | findings below |
| KiCad oracle, docker, the search, any replay beyond `--check` | NOT RUN: outside a read-only brief review |

The brief's count of 138 protected footprints off their `s.fps` pose, its 21 and 37 floorplan differences and its
7.3 s replay time were not re-measured.

## Blocking findings

### 1. The rule rejects every IC placement, because the open ICs have no base pose

- **Location:** Rulings N1 and N2 (point set, "moved", NG1 to NG3, NG5); control C7.
- **Defect:** U5110, U8409, U5209, U5210 and U1415 are all in the protected set and are the five positionless
  footprints of the base effective scene (base row `no position`). N1 takes pads "at the footprint's effective
  pose", which does not exist for them at the base. A claimed IC therefore counts as moved, every one of its
  non-rail nets is evaluated (12 nets for U5110, U8409 and U5210; 9 for U5209), and each scene figure gains IC pads
  the base figure lacks. NG1 and NG2 then fail on any net where the IC pad is not interior, and NG3 compares a face
  against none. As written, no scene that places an IC can pass, or the executor must invent a reading.
- **Correction:** State that the five open ICs enter every point set at their paper pose, in the base, paper and
  scene figures alike, whether claimed or not, and that a claimed IC at paper is not a moved footprint. Add a control
  (an all-stay scene with one IC claimed synthetically shows 0 moved footprints and 0 evaluated nets) and a mutation
  (drop this convention: NG1 fails on a named net). Say what a positionless footprint on an evaluated net means in
  general: the scene fails.

### 2. The link end is measured at the slot centre, and only on board K

- **Location:** Ruling N1 (second bullet), Ruling N2 ("a link carrying it changes its slot centre on `b`"), stage 1
  deduplication, M11.
- **Defect, part a:** The net's copper ends at the connector, not at the slot. At the base, P-K-P-L03.01 has its slot
  at y 191.58 to 193.08, its K connector at y 179.83 to 185.93 and its front connector at y 204.73 to 210.83. The K
  end is about 9.5 mm from the slot centre and changes side with the direction; it also shifts with
  `K_extension_mm`. A direction change at one slot centre moves the K end by about 19 mm, yet the net is not
  evaluated and its figure is unchanged.
- **Defect, part b:** Board P has 0 protected footprints, so no net is ever evaluated on P. All 397 protected nets
  that span two boards resolve to a link. On the six searched links, 26 of 41 signals are on protected nets, and
  most have one K footprint and one P footprint (for example `/M5A/Ce67982_W`). A slot move can shorten the K part
  and lengthen the P part of the same node and pass. That is looser than "its node gets no longer".
- **Correction:** Use the centre of `geometry.K_connector` on K and of `geometry.front_connector` on the front
  board. Trigger evaluation on any change of the link's geometry, not of its slot centre. Evaluate a net on every
  board where it has pads when a protected footprint sits on it on any board; test each board's figure and report
  the sum. Add mutations: direction flipped at an unchanged slot centre (the net is evaluated and fails), and a
  move that shortens K and lengthens P (fails).
- **Visibility:** This also makes the rule bind a link move that displaces no part on the net, which goes beyond
  the owner's sentence. Keep it, as the strict reading, and tally "fails only on a link-end change, no footprint on
  the net moved" beside the base-limit and large-net tallies.

### 3. The base limit is not the stricter reading where the base already exceeds paper

- **Location:** Ruling N3 title and text; reviewer item 2; DS-190 (proposed); "It can claim", first bullet.
- **Defect:** The hard limit is the base figure. Where base ≤ paper that is stricter than paper. Where base > paper
  (`INHERITED EXCESS`) a protected part may move while its node stays longer than on paper. The owner's sentence
  is "no longer than on paper", so that case is looser than the sentence, and N3 calls itself the stricter reading
  without exception.
- **Correction:** Make the hard limit `min(paper figure, base figure)` on every evaluated net that carries a moved
  protected footprint, and keep the base figure for nets evaluated only through an unprotected mover or a link
  end. Alternatively keep the base limit, retitle N3, tally every scene that passes at the base and exceeds paper,
  and bar such a scene from the `CANDIDATE SCENE` verdict. Either way M12 must state the paper figure of its
  fixture.

### 4. The pad-to-pin distance promised to the owner is missing

- **Location:** Rulings N1 and N2; compare `mc04-s14-disposition-20261128.md`, "What option 1 is and is not"
  ("pad extent, pad-to-pin distance and face set no worse than paper, for every protected node touched").
- **Defect:** The brief replaces pad-to-pin distance with tree length and does not say so. Extent and tree do not
  bound it: on a three-point net with the IC pin at 0, a pad at 10 and a resistor pad at 3, moving the resistor to 7
  leaves both figures equal and more than doubles its distance to the pin.
- **Correction:** Add a test: on every evaluated net, the unrounded distance from each pad to each pin of a
  protected IC on that net and board is no greater than at the limit of finding 3. `overlay.ancillary_geometry`
  already computes this figure as `input_passives_to_buffer_mm`. Add its mutation (the example above: NG1 and NG2
  pass, the new test fails). If the design authority drops the measure instead, that is a ruling with its own
  decision row and a plain statement that the rule is looser than the option text.

### 5. The mutation table cannot meet "flip exactly the named test", so STOP 3 would fire

- **Location:** "Tests and mutations", M1, M5 to M9, M11, M14; STOP 3.
- **Defect:** Moving the one extreme point of a net outward by δ lengthens every edge at that point, so every
  spanning tree grows by at least δ. M1, M9 and M11 therefore fail NG2 with NG1, always; M7 does so in general.
  M5 names "NG1 or NG2". M6 mirrors the pads, so NG1 and NG2 can fail with NG3. M8 must move the part, and its NG1
  and NG2 state is not given. M14 leaves NG1 and NG2 undefined. STOP 3 stops the run when a mutation "flips
  another".
- **Correction:** Give each mutation its full expected vector over every NG test (pass, fail or not evaluated),
  written before the run, and reword STOP 3 to "the vector differs". Add the mutations named in findings 1 to 4,
  one for the NG4 exemption (same kind, same link at the base: passes), and one for a return to paper that
  lengthens a net (fails).

### 6. The S12 functions cannot be used unchanged for stages 1 to 3

- **Location:** "Procedure" ("imports `s12.py` and `joint_search.py` unchanged"), stages 1 and 3, Ruling N6.
- **Defect:** `s12.census` keeps a candidate only when `World.check_rules` returns no rule, and that method applies
  rule 5 (T1) and rule 6 (T2). `joint_search.legal_entry` calls the same method, and `cluster_search` rejects any
  scene whose `check_rows` reports A2 and orders its pools by the A2 screen. Used unchanged they return the S12
  result. A census "stopped after rule 4" and a cluster search judged by NG need new code.
- **Correction:** Say that S15 carries its own census collector, legality call and cluster search, derived from the
  S12 ones, with rules 5 and 6 and A2 replaced by NG and nothing else changed. Add a control that the derived code
  with T1, T2 and A2 switched back on reproduces S12 stage 3 (for {U5210}: 13 legality calls, no complete scene).
  C8 then covers stage 1.

### 7. The run bounds contradict each other and the 30-minute slice

- **Location:** "Caps" (resumes), "Run bounds", STOP 6.
- **Defects:**
  - Three resumes of 30-minute slices give 2 hours. The expected run is 1.5 to 2.5 hours and the ceiling 5 hours,
    so a normal run reaches a fourth resume and STOP 6.
  - "Started detached" is asserted, not tested. In S12 the limit also stopped the guard, and arm 0 lost its memory
    summary.
  - Checkpoints are per stage and per 25 stage-2 candidates. Stage 3 (ceiling 60 min, expected up to 50) has none
    inside it, so it cannot finish in a 30-minute slice.
  - The step ceilings sum to 305 minutes against a 5-hour ceiling, and `timeout 5h` restarts with each resume.
  - Stage 3 keeps S12's `EAST_SLICES`, which total 75 minutes, plus South, under a 60-minute ceiling.
- **Correction:** Fix the slice the executor will use (the session tool allows a background limit of up to
  2 hours) and prove it in arm 0 with a detached no-op that outlives the slice. Derive the resume cap from ceiling
  and slice. Checkpoint stage 3 per target set and stage 4 per combination. Count wall time cumulatively across
  resumes in `result.json`, and make the step ceilings sum to no more than the total. Restate the East slices so
  they fit the stage 3 ceiling. Require the guard summary to survive an interruption (append per sample).

## Non-blocking findings

### 8. The stage 2 "complete" label does not say what happens to slots that are illegal at record

- **Location:** Stage 2; Ruling N5, second verdict row; scope table.
- **Defect:** The census counts candidates with every S12 searched link absent. Many rule-4 survivors are illegal
  once the other links stand at record, and the brief keeps those unreplayed for stage 3. The complete verdict
  needs "every rule-4 survivor ... replayed and failed", so it is unreachable whenever one such slot exists.
  "Another searched link" is ambiguous for L07 and L08, which S12's `SEARCHED` holds and S15 fixes. "A link the IC
  needs" differs between the scope table (three links for U5210) and `s12.must_move` (one).
- **Correction:** Define the complete verdict as: every rule-4 survivor that is legal with the other links at
  record was replayed and failed, and the count illegal at record is given beside it. A slot illegal against L07 or
  L08 is dropped, not kept. "Needs" means `s12.must_move`.

### 9. Pool B does not take the slots that stage 2 can actually replay

- **Location:** Stage 2, pooled links.
- **Defect:** The S12 result review found 404 legal and 104 rule-4 survivors for P-K-P-L13.01.01.01 with every
  other link at record. Pool B orders by unanchored protected count and spot, so its 150 entries may be mostly
  slots that are illegal at record and are never replayed in stage 2.
- **Correction:** For each pooled link, first replay every rule-4 survivor that is legal at record (about 104 for
  L13.01.01.01; count L15.02.01.01 in stage 1). If the total stays under the 1000-replay cap, the at-record screen
  of that link is complete and may carry the complete label of finding 8.

### 10. No control shows that NG can pass a real moved scene, or that every moved pad has a net

- **Location:** Arm 0 (C3, C7, C9).
- **Defect:** NG passes only on the all-stay scene and on synthetic fixtures. C9 has no expected outcome. On K 418
  footprints have no pin record (196 `J`, 204 `MH`, 18 `TP`); a displaced test point on a protected net would be
  invisible to NG.
- **Correction:** Add a real-data positive control with a fixed expected result, or state that none exists. Add a
  control that lists footprints with pads and no pin record by board and prefix, and make NG fail a scene in which
  such a footprint moves (STOP 4 then applies by rule, not by notice).

### 11. C5 compares a figure that has no link point

- **Location:** C5.
- **Defect:** The seven `input_runs` nets lie on JL and JR and cross no link, so C5 holds as written. It does not
  test the link point of N1, and the brief does not say the comparison is pads only.
- **Correction:** State "pads only". The link point gets its own hand-value control, like C4.

### 12. The strictness for protected ICs is not made visible

- **Location:** Ruling N4; "Outputs".
- **Defect:** A moved protected IC has all its non-rail nets evaluated (U8411 has 10, U5205 has 5). A net-blind
  ring shift is unlikely to pass on all of them, so the IC blockers of U8409, U5209 and U5210 will probably decide
  the result. This is strict and honest, but only the base-limit and large-net tallies are reported.
- **Correction:** Report the first-failure tally by moved footprint as well as by net, with ICs and passives
  separated.

### 13. DS-188 and the proposed rows describe the Revision 1 rule

- **Location:** `decisions.md` DS-188 (uncommitted); DS-189 to DS-191 (proposed).
- **Defect:** DS-188 names "pad-centre net extent and rectilinear tree length no longer than at the base effective
  scene", which findings 2 to 4 change. It cites the brief without a hash.
- **Correction:** Reword the row with Revision 2, cite the revision's SHA-256 and this review, and align DS-189 and
  DS-190.

## The readings: three are too loose, none is too strict to be useful

| Reading | Verdict |
| --- | --- |
| Pad-centre half-perimeter and rectilinear tree | Honest and computable (`current_pad`, `s.pins`, `s.net_refs`). Not sufficient alone: pad-to-pin distance is missing (finding 4) |
| Per node, not per part | Stricter than the owner's sentence on K, which is acceptable. Looser across boards (finding 2b) |
| Base effective scene as the limit | Stricter than paper only where base ≤ paper (finding 3) |
| Link-slot centre included | Right intent, wrong point; too loose on a direction change (finding 2a) |
| A tie passes, 1e-9 mm guard, no rounding | Matches "no longer". Sound |
| Face, cover and position tests | Sound. NG3 is stricter than the "face set" of the option text |
| No large-net exemption | Strict and visible. Sound |

With the corrections the rule will be very strict for moved ICs (finding 12). That is a property of the owner's
choice, not a defect, and an empty result remains a valid result.

## Scope is consistent with S12

- The six links, the fixed L07, L08 and U1415, and the South and East clusters match `s12.CLUSTERS` and the S12
  disposition. Rule 4 still protects U1415's courtyard.
- The counts match `census.json` and the S12 report: 66, 183, 86 and 179 rule-4 survivors for the four complete
  links; 6903 and 3469 for the pooled two; 0, 0, 27, 0, 0 and 73 after T1 and T2; 23 and 54 distinct. The replay
  bound 514 + 77 + 300 = 891 is right, and 891 × 7.3 s is 108 minutes in sequence.
- The verdict vocabulary cannot overstate a pooled or single-move result once finding 8 is applied. "Exhaustive"
  is rightly barred.
- Joint combinations 9 is right for two clusters of at most 3 clean scenes.

## Claims are sound

The brief claims geometric evidence only. It states that S13 and S14 leave a scene with no electrical evidence. It
lists routing, c6, checks 2 to 4, latch access, threading, DRC and ERC as `NOT RUN` with the reason. It writes no
board, schematic, options or generated file, keeps panel hardware at the pinned lock, and makes adoption depend on
a disposition, an owner decision on DS-150, a generator task and its review. No correction is required here,
except that "no evaluated node longer than at the base" in "It can claim" must follow finding 3.

## Verdict: ACCEPT WITH CORRECTIONS

Findings 1 to 7 are blocking. Revision 2 needs a second review before the manager admits the run. Findings 8 to 13
should be applied in the same revision.

---

# Revision 2 re-review: ACCEPT WITH CORRECTIONS (1 blocking, 4 non-blocking); admissible once finding R1 is applied, no third review needed

2026-11-28. Same reviewer, read-only. Subject: Revision 2 of the brief, SHA-256
`f7c0ed3f3b816998530c92bb066d539895f2d9c5ec49d1b0bc2d1f3c57f7e98b` (verified), and the reworded DS-188 row
(uncommitted). No search, replay or docker run was made. Only this file was written.

All 13 findings of the first review are met. The three choices the author raised are sound. Every mutation vector
was recomputed and is correct. One gap of the finding 6 kind remains in stage 4. It is a table edit; the manager
can confirm it without another review.

## The 13 findings are all met

| Finding | Status in Revision 2 |
| --- | --- |
| 1 Open ICs | Met: N1 "Open ICs", NG6, C9, M21, M22 |
| 2 Link end and boards | Met: connector centres, any geometry change, every board, "link end alone" tally, C7, M13 to M15 |
| 3 Limit | Met: `min(paper, base)` on P-moved nets; claim reworded; M16 to M20 |
| 4 Pin distance | Met: NG3, C5, M2 |
| 5 Mutation vectors | Met: fixtures F to F9, full NG1 to NG7 vectors, STOP 3 reworded |
| 6 Derived code | Met for stages 1 to 3 (C10, C11); not for stage 4, see R1 |
| 7 Run bounds | Met: C17, 100-minute slices, cap 4, checkpoints in stages 3 and 4, cumulative clock, 290 min sum, sets 50 min |
| 8 Complete label | Met: three classes at record, verdict on legal-at-record survivors, `s12.must_move` |
| 9 Pool B | Met: L13.01.01.01 is replayed in full; only L15.02.01.01 can be pooled, and no IC needs it |
| 10 Positive control, pin records | Met as allowed: N7 states it, C15 and NG7 added; see R2 |
| 11 C5 | Met: pads only; C7 for the link point |
| 12 IC strictness | Met: N4 and "Outputs" |
| 13 DS-188 | Met; see R4 for the hash it cites |

## The three choices the author raised are sound

- **`min(paper, base)` instead of barring such scenes.** This is the stricter of the two corrections offered and
  matches the owner's sentence on every net with a moved protected part. It is never looser than Revision 1. A
  return to paper can now fail (M19); that is correct, and the "stricter limit alone" tally shows it. The base
  limit on class Other nets is right, because no protected part moves there.
- **No real-data positive control (N7).** The statement is honest and the first review allowed it. A stronger
  control costs nothing and invents no scene; see R2.
- **NG4 compares faces only where both poses exist.** Sound. The only footprints without a base position are the
  five open ICs (checked: exactly 5). They are never moved at paper, and A1 fails any other pose. A footprint that
  loses its position fails NG6 and A3, so no pose change escapes.

## The mutation arithmetic is correct

Each fixture and vector was recomputed by hand from the stated points (Manhattan tree, half-perimeter, Euclidean
pin distance).

| Item | Recomputed | Brief |
| --- | --- | --- |
| F base | extent 12; tree 3 + 4 + 7 = 14 | 12, 14 |
| F2 base | extent 14; tree 1 + 3 + 10 = 14 | 14, 14 |
| M1 | 12.25; 3 + 4 + 7.25 = 14.25; pin 10.25 | same, F F F |
| M2 | 12; 3 + 4 + 7 = 14; pin 7 against 3 | P P F |
| M3 | 14; 1 + 4 + 10 = 15; pin 0.7071 against 1 | P F P |
| M4 | 11; 3 + 4 + 6 = 13; pin 9 | all pass |
| M5, M6 | every figure equal; then 12.000001, 14.000001, pin longer | pass; F F F |
| M7 | pads at dx = 0, so the mirror moves no pad; face differs | P P P F |
| M8 | pad at (10.75, ±0.75): 11.5; 3 + 8.5 = 11.5; pin 10.776 | F F F |
| M11, M13, M14 | 12, 12, pin 12 against 6; M14 extent 29 | F F F |
| M15 | K 9, 9 pass, pin 9 against 10 passes; P 5, 5 against 4, 4; sums 14 and 14 | F F P |
| M16 to M19 | limits 10, 10, 8, 8; scene 11, 10, 9, 10 | F, P, F, F |
| M20 | limit 12; 11 passes, 12.01 fails | P then F |
| M22 | limit extent 9, tree 4 + 7 = 11; scene 12, 14; pin pairs absent at the limit | F F F |
| M9, M10, M12, M21, M23 to M26 | follow from the conventions | as stated |

C7's "more than 15 mm" holds: the K connector centre of P-K-P-L03.01 is 9.45 mm from its slot centre, so a flip
moves it 18.9 mm. The same offset holds for all six searched links.

## Remaining findings

### R1 (blocking). Stage 4 still calls S12 code that applies A2 and A10

- **Location:** "Derived code" table and its closing sentence; stage 4; `--verify-scene`.
- **Defect:** `s12.judge` calls `check_rows` (A2), and `overlay_part` applies the protected clause of A10
  (`s12.py` line 691). `joint_search.stage4` and `verify_scene` call `s12.judge`. The table lists four derived
  functions and says everything else is imported unchanged. Used unchanged, stage 4 rejects every scene that moves
  a protected part, which is every scene this study exists to find. The stage 4 text states the intent, so this is
  an omission, not a wrong rule.
- **Correction:** Add `judge_ng` (from `s12.judge` and `overlay_part`: A2 and the protected clause of A10 replaced
  by NG on the post-overlay effective scene, the A8 search unchanged) and say that the stage 4 driver and
  `--verify-scene` call it. Extend C8: `judge_ng` with `rules='s12'` on the all-stay scene equals S12 P11.
  The driver, stage 2 and stage 3 loops are new code by nature; say so in place of "everything else is imported
  unchanged".

### R2 (non-blocking). A real-data positive control exists without inventing a scene

- **Location:** Ruling N7; C8, C9.
- **Defect:** C8 and C9 pass with 0 evaluated nets. No control shows an evaluated real net passing, so a fault
  that builds the base and scene point sets differently (link points, open-IC pads, per-board split) would read as
  an all-negative result, which is also the expected result.
- **Correction:** Add a forced-evaluation control: on the all-stay scene, evaluate every non-rail net that carries
  a protected pad (about 2357) against the base limit; every figure and pair must equal its base value and pass.
  Report beside it how many of those nets have base above paper. Optionally give the three C4 poses of R8356 their
  NG vectors by hand. N7 then reads "no real moved scene with a known passing result exists".

### R3 (non-blocking). A negative that rests on the link-end clause must say so in the verdict line

- **Location:** Rulings N2 (closing paragraph) and N5; "Outputs".
- **Defect:** On L12.02.01.02 all 5 signals, and on the six links 26 of 41, are on protected nets, mostly with one
  pad per board. Any slot move shifts both connector centres, so the link-end clause may reject most candidates
  before any protected part is judged. The clause goes beyond the owner's sentence. It is tallied, but the IC
  verdict could still read as a finding about protected parts.
- **Correction:** As S12 did for class S: when an IC's negative would change with the "link end alone" or
  "stricter limit alone" failures set aside, the verdict line names that dependence and its count.

### R4 (non-blocking). DS-188 cites this file's first-issue hash

- **Location:** `decisions.md` DS-188.
- **Defect:** The row cites this review as `c6af5d94…f27670bd`. Appending this section changes the file's hash.
- **Correction:** Cite the hash of this file as it now stands, or mark the cited hash "first issue".

### R5 (non-blocking). Four small wording gaps

- **Stage 1 classes:** say how "joint-only" is decided (legal with the other five searched links skipped, illegal
  with them placed), and that the geometry used in stage 2 is the one the at-record legality call returns.
- **Stage 2 time:** "120 min in sequence" is not a permitted mode, since C16 failing is STOP 1; and 1000 replays at
  7.3 s leave under 4 minutes to the ceiling. Drop the figure or state the margin.
- **C5:** add "where the record carries the figure".
- **M25:** say whether U1 has a pad on `GND`; the vector holds either way.

## Scope, caps, claims and STOP conditions are consistent

- Replays before pooling are at most 514 + 104 = 618, so the 1000 cap can cut only L15.02.01.01, as stated.
- Step ceilings sum to 290 minutes; the target sets sum to 50 of 55 minutes; 4 resumes follow from 100-minute
  slices plus one transient. C17 tests detachment before the run.
- No base row lacks a pin record (checked: 0 of 452), so NG7 will not decide the result by itself.
- Claims are unchanged in substance: geometric evidence only, no electrical evidence, routing, DRC and ERC
  `NOT RUN` with the reason, adoption a separate reviewed change and an owner decision on DS-150.

## Verdict on Revision 2: ACCEPT WITH CORRECTIONS

R1 must be applied before admission. R2 to R5 should be applied in the same edit. None changes a rule, so no third
review is needed; the manager confirms the edits against this section.
