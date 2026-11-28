# MC04-S16 brief review: ACCEPT WITH CORRECTIONS (3 blocking, 8 non-blocking); not admissible at Revision 1

2026-11-28. Issue #367 (MC-04 paper gate). Independent review, model `claude-fable-5-2`. The reviewer is not the
author. Read-only, except for this file.

Subject: `mc04-s16-l0301-replan-brief-20261128.md`, Revision 1, SHA-256
`59e41db23f151b623a8acbebb666ff642cf487d890a82bbb4602d870a186544b` (verified), with the uncommitted DS-202 row in
`decisions.md`, at head `4ad14776` of `local/cloud-engineering-20261127`.

The brief asks the owner's question and nothing more: one study, nothing adopted, DS-150 held. The domain count,
the six sites, the ladder, the six displaced parts and the 50.4 mm figure all reproduce. Three defects stop
admission. The allocation tests leave out the logic-run cap of DS-120 to DS-122, which the record of L03.01 itself
obeys. The ride test depends on an order the brief does not fix. Six controls and one mutation cannot pass, or
cannot run, as written. Revision 2 must apply findings 1 to 3. The manager may confirm findings 2 and 3 by
inspection; finding 1 changes a rule and needs a second look by a reviewer.

No census, no replay and no docker command was run. Every board and schematic stays an unvalidated draft.

## The brief's facts reproduce, except the recorded conductor order

| Check | Result |
| --- | --- |
| Brief SHA-256 | matches |
| `placements.lock.json` `297300b0…5b88dbe8`; route costing `209073b4…ae12ffb7` | both match |
| S12 `joint_search.py --check` (`/home/user/venv312/bin/python`) | passes, exit 0, 25 s |
| S15 `no_growth.py --check` | passes, exit 0, 41 s, cache present, 52 digests |
| Six member sites, positions, classes and circuits alone (5, 5, 5, 4, 3, 4) | match; 15 signals; L03.01 carries no rider |
| 877 structures, 64 ride sets, 203 partitions; all 203 allocate under `allocation` and `allocation_errors` | match; size counts 1 (six 8-way), 9 (two 14-way), 16 (8-way and 26-way) match |
| Gate ladder (`gate_cluster`, join radius 35 mm): eleven sites at 26, five at 14, six at 14 | match the brief and the record |
| Six protected displaced parts; no other link and no fixing displaces them | match: R8420, C8405, U8409, C7205, R8444, U8411 |
| Nearest host with room: 50.4, 40.9 and 37.2 mm for P-K-E1, E2 and E3 | match (50.3968, 40.9004, 37.2); P-K-E1 has no host within 45 mm |
| Spare positions (L05.01.01 has 7; four others have 1 to 3) | match |
| S12 census figures in C4, C5, M8, M10, M11 and M18; 23 distinct survivors of L13.01.01.01 | match `census.json` (813, 183, 183, 0; 9464, 8841, 6903, 27, 27; 630; 1938; 0 class S alone) |
| Vectors M1, M2, M3, M5, M6, M14, M15, M16 on the retained functions and the base rows | hold (M5 and M6 for another reason than the one named; finding 6) |
| Recorded positions of L03.01 against `link_record` at 26 circuits | **differ** (finding 1) |
| No generator input forces a split or a ride | holds for `link-gate-options.json`; two other inputs are not named (finding 4) |
| Step ceilings sum to 270 min; 1200 replays at 7.3 s on 3 workers give 49 min; resumes 3 and STOP 6 agree | consistent |
| DS-196 reading in "Run bounds" and STOP 2 | matches the decision row |
| The census, any rows-only or full replay, the KiCad oracle | NOT RUN: outside a read-only brief review |

All figures come from a read-only probe of the S12 `World` at snapshot `6e5716e7`, with scripts kept outside the
repository. The 7.3 s replay time and the 290 s base replay were not re-measured.

## Blocking findings

### 1. The allocation tests omit the logic-run cap, so sizes, rides and control C3 are wrong

- **Location:** "Facts" (first bullet), Ruling P1, tests S1 to S3, the gate-check table (row "c6 record"), C3, C9,
  "It can claim" (first bullet), DS-202.
- **Defect:** DS-120 limits a run of logic lines to three on every cable. DS-122 says that when the clustering
  runs again, a run of n logic lines needs ⌈n / 3⌉ − 1 grounds inside it. A re-plan is the clustering running
  again. `allocation`, `allocation_errors` and `circuits_needed` do not know this rule; the generator applies it
  in `links_gate_c6.py`, a later pass with pinned digests. That pass acts on P-K-P-L03.01 by name. The brief never
  mentions it. Measured consequences:
  - The record of L03.01 is the c6 order: 11 grounds, 0 unused, a logic run split 3 and 2. `link_record` at
    26 circuits gives 10 grounds, 1 unused and one run of 5, which `links_gate_c6.order_errors` rejects. C3 expects
    "11 grounds … and positions equal to the record", so C3 fails and STOP 1 fires in arm 0.
  - 16 of the 63 blocks have a plain allocation with a logic run of 4 or 5. The block {K-P-16, K-P-18, K-P-20}
    needs 8 circuits by `circuits_needed` and 9 by DS-122, so its stock size is 14, not 8. The size counts in C9
    change with it.
  - The two nearest hosts hold ruled c6 orders. `reallocate` would replace them with one run of 4 logic lines on
    P-K-P-L05.01.01 and of 6 on P-K-P-L03.02.01, before any rider is added.
  - `ride` accepts rides that the cap forbids. K-P-20 on P-K-P-L03.02.01 needs 14 of 14 positions by
    `circuits_needed` and 16 by DS-122. `/E1/LOOP_RAW` there needs 13 against 15. `ride` also lets one logic line
    onto P-K-P-L13.01.01.01, which the record shows with 8 of 8 positions in use.
  As written the study can return `RE-PLAN SCENE AT ROWS LEVEL` for a scene whose link sizes and rides break a
  rule on record. The cap is a count, known now; it is not bound to a generated record.
- **Correction:** Add DS-120 and DS-122 to S1 to S3. A block's size is the smallest stock size that holds
  `circuits_needed` plus ⌈n / 3⌉ − 1 for its logic run. A host accepts a rider only if its positions after the
  ride, with the cap, fit its size. Check every block and every changed host with `order_errors` on an order
  that meets the cap; state how that order is built, since `allocation` cannot build it. Restate C3 on what the
  functions give (10 grounds and 1 unused from `link_record`; 11 grounds and no unused in the record after the c6
  pass) and re-measure C9. Keep the pair ratio of DS-122 (at or below 1.0) as `NOT RUN`, and say so. Add to
  Ruling P4 and to the adoption list: every changed host loses its ruled order, and the c6 pass with its pins
  must be rewritten, because it names L03.01, L05.01.01 and L03.02.01. Correct "needs 25 circuits" in the brief
  and in DS-202: the recorded link uses all 26 positions.

### 2. The ride test depends on an order the brief does not fix

- **Location:** Ruling P1 (first bullet), S3, stage 2a, Ruling P6 (`CENSUS-COMPLETE`).
- **Defect:** `ride` takes signals in the order given and fills hosts as it goes. The brief gives no order for
  the sites of a ride set. Over all orders of the 63 non-empty ride sets, with the retained `ride` unchanged, 27
  can ride and 36 cannot. In member order only 24 ride. Four sets ride in some orders and fail in others:
  {P-K-E2, P-K-E3}, {K-P-16, P-K-E2, P-K-E3}, {K-P-20, P-K-E2, P-K-E3} and {K-P-16, K-P-20, P-K-E2, P-K-E3}.
  Three of them fail in member order. Six more sets ride in every order but onto different hosts. A structure can
  therefore be called dead at S3 when a legal ride exists, and `CENSUS-COMPLETE` would rest on it. The gate's own
  way 1 tries up to 5040 orders for this reason.
- **Correction:** State that S3 tries every order of the sites of R (at most 720) and that a ride set is illegal
  only if every order fails. Record the first legal order by a fixed rule, and the count of distinct host plans.
  Add a control with the figures above, re-measured under finding 1, and a mutation: {P-K-E2, P-K-E3} in the
  failing order alone gives S3 `F`, and over all orders gives `P`.

### 3. Six controls and one mutation cannot pass, or cannot run, as written

- **Location:** C6, C7, C8, C10, C12, M4; STOP 1 and STOP 3. C3 is in finding 1.
- **Defect and correction, per item:**
  - **C10** says the all-stay scene "passes every A item". It fails A0, as M1 states. Write "passes A1 to A11
    and fails A0".
  - **C12** is in arm 0 and uses "the first 12 stage 2b replays". Those exist only after stages 1 and 2a, and not
    at all if no structure is live. Move it to the start of stage 2b with its time counted there, or define it on
    12 scenes that arm 0 already has, and say what holds when fewer than 12 replays exist.
  - **M4** expects `PF`. At a forced 8-way size `allocation` raises "needs 25 positions, link has 8", and
    `link_record` returns no positions, so S1 fails first. Define S1 as the class test at the block's own size and
    S2 as the fit, or change the vector to `F` at S1.
  - **C7** fails with the host's signals in position order (`link_signals`): the two riders come out swapped. It
    holds with member signals first and riders after them. Name that order.
  - **C8** names one shifted row. `s12.check_rows` on the returned S10 rows gives five new rows (as listed) and
    four shifted rows: C8405, R5148, R5253 and R8431. List all nine.
  - **C6** refers to "four 8-way sets listed above", and none is listed. Two readings differ. The ladder (each
    14-way set split at 8) gives {K-P-16, P-K-E2}, {P-K-E3}, {K-P-18, K-P-20}, {P-K-E1}. `gate_cluster` on the six
    sites at 8 gives {K-P-16, P-K-E3}, {K-P-18, K-P-20}, {P-K-E1}, {P-K-E2}. List the sets and name the call.

## Non-blocking findings

### 4. "The generator cannot be told" holds for the options file only; Ruling P5 still stands

- **Location:** "Facts" (sixth bullet), Ruling P5, "It cannot claim", the adoption list.
- **Defect:** Confirmed from the code: a split happens only in `_place_ladder` when a link has no place at its
  size, slot holds fix a slot and a direction only, and no key of `link-gate-options.json` forces a split or a
  ride. Three things are missing. `link-cluster-baseline.json` is a retained input that fixes the members of each
  top-level cluster (P-K-P-L03 with eleven sites), so it can regroup sites; it cannot set a size or a
  sub-partition. Signals also ride in the consolidation pass and in the c6 pass, not "only through the ways out".
  DS-61 gives each P link the largest size that places, and the domain takes the smallest.
- **Correction:** Name the baseline and say why it cannot express a structure. Reword the ride sentence. Add to
  the adoption list that the generator change must override the largest-size rule of DS-61 and rebind the c6
  pass. A12 stays `NOT RUN` with the completed reason.

### 5. The domain is honest but four exclusions are not labelled

- **Location:** Ruling P1, the text under Ruling P6, "It cannot claim" (fourth bullet).
- **Defect:** No legitimate by-site structure is missing from the 877, and the count is right. Not stated:
  (a) the 40-way size is stock on this joint and is left out; (b) a rider may not use a block of the same
  structure as its host; (c) the record already holds a rider that divides a site (`/E1/STAGE_FALL` of K-P-19,
  DS-121), so "sites are not divided" excludes a ruled mechanism; (d) the 35 mm radius is S12's ruling for eight
  named links and is applied here to new links. "A site's signals stay together" is also untrue for a riding
  site: way 1 sends the two signals of K-P-18 to two hosts. Partitions and partial rides of a placed link are
  not generator behaviour; Ruling P5 covers that.
- **Correction:** Add (a) to (d) to the domain label and to the report. Reword to "a site either rides whole or
  sits whole in one block". Report the ring of each block slot (up to 24 mm, 24 to 35 mm) as S12 did. Say what
  the full-set census of stage 1 is for, since the present plan is outside the domain.

### 6. Three failure modes have no mutation, and M5 does not test the distance it names

- **Location:** "Tests and mutations", M5, M6, M18.
- **Defect:** M5 fails at `/E1/LOOP_RAW`, a logic line refused by a full host at 51.2 mm; the 40 mm precision
  test is never reached. No mutation fails A1. Ruling P3's new path (class S deferred, R5 `P`) is never
  exercised: M18 expects "no such slot".
- **Correction:** Ride `/E1/REF5` alone in M5 and assert the reason text in M5 and M6. Add an A1 case (the base
  rows with a position given to U5110: A1 `F`). Add a real case for P3: `t1` on the record geometry of L03.01
  gives six class S parts and no class N, so R5 is `F` when strict and `P` by default with six parts listed.
  Add a static line for S3.

### 7. M13 has no fixed vector

- **Location:** M13.
- **Defect:** "The five values `s12.check_rows` gives" is not an expected value.
- **Correction:** The vector is `––––––––– FPFPPP`, computed for this review from the returned rows at
  `32580f77`. U8409 has a row with no position there.

### 8. Rulings P3 to P6 are sound; three sentences need tightening

- **Location:** Rulings P3 to P6, "Caps".
- **Defect:** P3 loosens only the preflight: A2 compares the row of every protected footprint with its base row
  on every replay, and DS-150 is enforced there. P4 adopts nothing. P5 is right. P6 is sound once findings 1 and
  2 are applied. Loose wording: `CENSUS-COMPLETE` says "an illegal ride" where stage 2a tests S1 to S3; the
  positive verdict says "every test" while A12 is `NOT RUN`; the cap of 5 kept scenes is "recorded" and not
  called a bound.
- **Correction:** Write "fails S1 to S3 in every order, or has a block with no census survivor". Write "every
  test except A12". State that any cap reached in stages 2b to 3 makes a negative result `BOUNDED`.

### 9. The U5210 reading is limited, but `NOT SEEN` says too much

- **Location:** Stage 4, "What the result means for U5210".
- **Defect:** The 23 survivors are the right set: S12 took them with L03.01 out of the placed index. Stage 4
  omits A0. Five kept scenes times 23 survivors is 115 replays against a cap of 60. "`NOT SEEN` means U5210 needs
  more than L03.01 out of the way" does not follow from kept scenes only. "If no scene exists" covers the
  `BOUNDED` verdict, where none was found.
- **Correction:** Add A0 to stage 4. Raise the cap to 115 or order the replays and report a reached cap with the
  reading. Write "`NOT SEEN` on the kept scenes, under the present rules and the stated cap" and "if no scene is
  found".

### 10. Pins and STOP 8 leave three things out

- **Location:** "Source pins", STOP 8.
- **Defect:** `test_s16.py` is "pinned" in one section and not in the pin list of another, since the driver does
  not import it. `rp.snapshot_root` and S12's full replay write a snapshot and a scratch root in the system
  temporary directory, which STOP 8 does not allow. The generator files are pinned only through C1.
- **Correction:** Pin `test_s16.py` and `guard15.py` by name. Allow the temporary snapshot and scratch roots
  outside the repository in STOP 8. Say that C1 carries the generator pins.

### 11. Six controls are marked real, not seven

- **Location:** "Arm 0".
- **Defect:** C3 to C8 are marked real. C8b and C9 are measured values and are not marked.
- **Correction:** Mark C8b real, or state the count as six.

## Feasibility and storage hold

The caps, the 4.5 h ceiling, the slices of 100 minutes with checkpoints under 15 minutes, the guard limits of
`guard15.py`, the ignored cache `.circuit-cache/mc04-s16/` with a durable copy under `/mnt/project-files/`, and
the STOPs are consistent with each other and with DS-196 and DS-197. Stage 1 time is an estimate; STOP 5 covers
it. The claims section presents no rows-level scene as a gate pass.

## Revision 2 re-review: ACCEPT; admissible after three wording fixes the manager can confirm (0 blocking, 3 non-blocking)

2026-11-28. Same reviewer, read-only. Subject: Revision 2 of the brief, SHA-256
`736e2e3cc7136d33a7b6167a1bda4f09ede27e6601c469ef43694eda510c46e9` (verified), with the updated DS-202 row. The
first issue of this review file, before this section, was `7c39fb134df095d6…92062d6d`.

Ruling P7 closes finding 1. Findings 2 to 11 are applied. Every figure the author measured under the cap
reproduces. No third review is needed: the three points below change wording only, and controls C15 and C16
already fix the outcomes they touch. No census, no replay and no docker command was run.

### Ruling P7 is DS-120 and DS-122 by count, and its builder reproduces the five records

The builder was written for this review from the brief's text alone and run on the S12 `World`.

| Check | Result |
| --- | --- |
| C3b: builder on `host_signals` against the recorded positions of L03.01, L01.02.01, L05.01.01, L03.02.01 and L01.01.02 | all five equal, and `order_errors` is empty for each |
| Block sizes: built length against `circuits_needed` plus ⌈n / 3⌉ − 1 for n ≥ 4 | equal for all 63 subsets; `order_errors` empty for all 63; {K-P-16, K-P-18, K-P-20} is 14-way |
| C9: 203 partitions, fourteen size counts | all fourteen match |
| C15: ride census over every site order | 19 ride, 44 do not, 16 ride in member order; the four order-dependent sets and the one set with two host plans match; no set with P-K-E1; none above three sites; 27 and 24 with the unchanged `ride` |
| {P-K-E2, P-K-E3} | rides in no order under the cap, as the author says |
| Hosts that ever take a rider | P-K-P-L05.01.01 and P-K-P-L01.01.02 only |
| C16: S1 to S3 over 876 structures | 622 pass, 254 fail, all at S3; 202, 260, 135 and 25 by ride set size |
| M24, M25, M26, M27 | match, reason texts included; M27 has 2 legal orders of 6, the first K-P-20, P-K-E2, K-P-16, with K-P-16 on L01.01.02 at 54.376 mm |
| M5, M6, M22, M23 | match: reasons as written; M22 gives `FFFPPP`; K-O1-1 is STATIC |
| Nearest link with a SYNC_GATE line | P-K-P-L08, 148.397 mm from K-P-18 |
| L03.02.01 with one more line | 15 positions against 14, as stated |

The ruling is sound. The cap enters as a count, the runs are as equal as possible as DS-120 says, the check is
the generator's own `order_errors`, and the pair ratio of DS-122 is `NOT RUN` in the ruling, the gate-check
table, the report list, the claims and DS-202. A built order is called "not a ruled order". The host test and
the block sizes follow from the builder.

### Findings 2 to 11 are applied

| Finding | Status in Revision 2 |
| --- | --- |
| 2 | applied: every site order, first legal order by a fixed rule, C15, C16, M27 |
| 3 | applied: C10, C12 (moved to stage 2b, with the short and empty cases), M4 (S1 is the class test), C7, C8 (nine rows), C6 (every set and call) |
| 4 | applied: baseline, DS-61 and the three places where signals ride are named; adoption list extended |
| 5 | applied: exclusions a to d in the ruling, the domain label and the report; rings; purpose of the full-set census |
| 6 | applied: M5 and M6 assert reasons; M18, M22, M23 added |
| 7 | applied: `––––––––– FPFPPP` |
| 8 | applied |
| 9 | applied: A0 in stage 4, cap 115, both sentences reworded |
| 10 | applied |
| 11 | applied: eight controls marked real and listed |

Ceilings still sum to 270 min. The new controls C15 and C16 take seconds.

### Three wording points remain, none blocking

1. **`host_signals` must say "the signals on the host's recorded positions".**
   - Location: Ruling P7, "Signal order"; the derived-code table.
   - Defect: "its member signals" can be read as the signals of the member sites. Two possible hosts have a line
     that rode out (`/E1/STAGE_FALL` from L13.01.01.01, two lines from L01.01.01), and that reading puts those
     lines back.
   - Correction: state that a line which rode out is not in the list. No figure changes: the other reading only
     makes those hosts fuller.
2. **A host should be eligible only if the builder reproduces its recorded order.**
   - Location: Ruling P7, "Hosts".
   - Defect: for 10 of the 39 other P-K links on board P the builder does not give the recorded order (ruled c6
     orders with single lines, SYNC_GATE lines, rider order). For those the count test may differ from the record;
     L13.01.01.01 counts 7 against 8 in use. None of them takes a rider today, and C15 pins the hosts to two links
     that do reproduce.
   - Correction: add the eligibility sentence, so the rule does not rest on C15 alone. C15 and C16 stay as they
     are.
3. **DS-202 and the brief's "Review applied" line cite this file by its first hash.**
   - Location: DS-202 evidence cell; brief header.
   - Defect: this section changes the file's SHA-256.
   - Correction: record both hashes in DS-202, as was done for the S15 review. The brief's line may stay if it
     says "first issue".
