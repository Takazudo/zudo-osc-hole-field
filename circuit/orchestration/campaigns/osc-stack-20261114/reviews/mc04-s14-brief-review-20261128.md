# MC04-S14 brief review: ACCEPT WITH CORRECTIONS (3 blocking, 11 non-blocking)

2026-11-28. Independent review of `mc04-s14-feedback-capacitor-brief-20261128.md`, Revision 1, SHA-256
`985f5ce518e2b15c56897d4ede852638ad514d423f4814a1aceb3ebe3e5940ec` (uncommitted draft), on branch
`local/cloud-engineering-20261127` at `0e54e80a199319b881a4decf7ac7400602217322`. Reviewer: a Fable agent
(`claude-fable-5-2`) that is neither the author of the brief nor the executor. Read-only, except for this file.

Everything below concerns a planned model study on an unvalidated draft. This review establishes nothing electrical
and admits nothing. Admission stays with the manager after the three blocking corrections.

## The brief does what the owner chose, and the class B exclusion is technically correct

- The owner chose "Study feedback capacitors (S14)": the existing 10 pF part on the weak-loop stages, corrected
  tests, a re-score of classes A, C and D, no part adopted. The brief covers E-control, E-audio, H-REF9 and G as a
  what-if, the class G specification cell, and the re-score. It adopts nothing and says so in "Kind", Ruling S1,
  the labels, STOP 5 and "Who decides what".
- Class B already carries the part. Inventory line `line-audio-feedback-c` is `bipolar_attenuverter:C_FB`,
  C0603C100J5GACTU, 47 placements, identity state VERIFIED. The recorded S13 class B deck `6d87620b…` has
  `C1 inm out 1e-11` beside `R4 buf inm 100000` and `R5 inm out 100000`.
- The K7 argument holds by my own calculation. With R_in = R_f = R, feedback capacitor C_f and stray C on the
  summing node, the non-inverting gain is (2 + sR(C_f + C)) / (1 + sRC_f). The phase added by C is
  atan(ωR(C_f + C)/2) − atan(ωRC_f/2), about ωRC/2 for any C_f in this range: 0.360° per pF at 20 kHz with
  100 kΩ. The 2° limit is reached at 5.6 pF, so 6 pF fails and Ruling 3 gives 2 pF, as S13 recorded. With
  C_f = 10 pF the correction factor is 1/(1 + 0.063²), 0.4 %. A larger or second feedback capacitor does not move
  this limit.
- The withdrawal of "at best it frees U8409" follows. DS-181 records it. Finding 14 asks that the owner sees it
  before admission.

## What I checked, and what is NOT RUN

| Check | Result |
| --- | --- |
| Hashes in "Pinned inputs": S13 brief, disposition, result review, `results.jsonl`, `budget.json`, `result.json`, `census.json`, `models.json`, `cells.py`, `runner.py`, `budget.py`, `guard.py` | all equal to the files at HEAD |
| What-if sets against `budget.json` and `results.jsonl` | 5 E-control, 2 E-audio and 1 H-REF9 topology as listed; 11 sets × 12 values = 132, under the cap of 140 |
| "Bracket open is the worse corner in S13" | confirmed at 0 pF: 18.54° against 22.59° (`c7bb7f88`), 18.95° against 22.98° (`932a592b`), 16.55° and 11.95° against 16.66° and 12.05° (H-REF9) |
| Arm R record counts from `results.jsonl` | 152 closed-loop records and 22 rows, not 200 and 23 (finding 1) |
| Own recomputation from the cached S13 waveforms (`.circuit-cache/sources/mc04-s13/`, read-only) | all 152 class A, C and D `t1` files present; K5 with the mean removed only reads below 1 µV for classes A and D at 0 and 100 pF; the last tenth of every class A and D K4 window at 0 and 100 pF is settled; class C wiper 1.0 reads 9.63 mV from 7 time constants with the mean removed only |
| Class G timings in the S13 record | at `reltol=1e-5` and at default every loop deck finished in 2.9 to 4.4 s and every closed-loop deck in 3.0 to 5.6 s; all were rejected on the 50 µV test alone |
| Capacitor cost arithmetic | 159.2 kHz, −0.068 dB and −7.16° at 20 kHz for 100 kΩ; 318.9 and 265.7 kHz, −3.59° and −4.30° for 49.9 and 59.9 kΩ: as stated |
| Any ngspice deck, docker, the sweep | NOT RUN: forbidden to the reviewer |
| `regen-all.sh`, `pnpm circuit:check`, unit tests | NOT RUN: the review writes one Markdown file under `reviews/` |
| Own census derivation and own `C_paper` computation | NOT RUN: unchanged from S13 and outside the six questions asked |

## The six questions

| # | Question | Verdict |
| --- | --- | --- |
| 1 | Owner's choice; class B out of scope | PASS, with finding 14 |
| 2 | S13 lessons carried forward | PASS for seeds, DS-177, DS-178, settled-window K4, slice-start guard, cap accounting and the pinned-image container form. Gaps: findings 5, 6, 8, 9 and 12 |
| 3 | Ruling S2 | ACCEPT, not rejected: it is labelled, stated as looser, justified by the record, and bounded by absolute K1, K2 and K5. Three gaps must be closed (finding 4) |
| 4 | Controls P1 to P10 and the arm R cache binding | P10 cannot pass as written (finding 3). P6 fails on the brief's own counts (finding 1). The cache binding cannot silently accept a wrong waveform of the kinds that can really occur, but it is weaker than mutation N9 claims (finding 7) |
| 5 | Bounds | Arithmetic consistent: 20 + 20 + 150 + 35 min = 3 h 45 min. Feasible from the S13 timings. Gaps: findings 9, 10 and 11 |
| 6 | Wording | PASS: model evidence only, unvalidated draft, no adoption, NOT RUN with reasons, and the 20 kHz cost predicted before the run. Additions: finding 13 |

## Blocking findings

### 1. Arm R has 152 closed-loop records and 22 rows, so control P6 stops the run on the brief's own counts

- **Location.** "Arm R: re-score … 23 rows"; "for every closed-loop record of the three classes (200 records)";
  P6 ("the 200 arm R records … equal the counts in 'Scope'").
- **Defect.** The brief's own input line gives class A 2 × 20, class D 2 × 20 and class C 3 × (20 + 4): 152
  closed-loop records, which is what `results.jsonl` holds (and 152 loop records). `budget.json` has 11 class A,
  10 class C and 1 class D row: 22. P6 compares against 200 and 23 and is a stop on failure, or it is bent.
- **Required correction.** Write 152 closed-loop records and 22 rows (A 11, C 10, D 1) in the scope, in P6 and
  wherever the per-net count of `rescore.json` is implied. The replay cap of 200 may stay.

### 2. The arm W and arm G value list lets 24 pF become a limit without a test at 48 pF

- **Location.** "Arm W": the 12 values and "`C_lim` is the largest listed `g` for which every listed value up to
  `2g` passes".
- **Defect.** Ruling 3 (DS-165) is "a limit must pass at twice its value". In S13 every candidate had its double
  in the tested list. In the S14 list 24 has no 48. A set that passes to 32 pF and fails at 50 pF gets
  `C_lim` = 24 pF with nothing tested between 32 and 48 pF. The pinned `corner_limits` would accept it, because it
  only requires the largest tested value to reach `2g`.
- **Required correction.** State the candidate limits separately from the tested values: 2, 4, 6, 8, 12, 16, 32
  and 50 pF. 24 pF stays a tested value (it is the double of 12) and is not a candidate. Add a mutation: a
  candidate whose double is not in the tested list is rejected by the table builder. Adding 48 pF instead would
  take arm W to 143 points, over the cap of 140.

### 3. P10's byte identity cannot hold as written, because a deck's text carries its seed and its stimulus amplitude

- **Location.** Ruling S1 third bullet; P10; Ruling S4 "Clipping"; Ruling S6 items 5 and 6.
- **Defect.**
  - Every S13 evaluation deck contains the `.nodeset` block of its seed, internal model nodes included, as
    six-digit text (for example `.nodeset v(xu.n2425287) = 8.47033e-16`). S6.1 seeds the what-if netlist itself;
    S6.5 only requires 5 µV agreement with the S13-equivalent seed on shared nodes. Nothing makes the two blocks
    byte-equal, and noise-level internal nodes will not be.
  - For class G there is no S13 seed at the larger-resistance trimmer setting at all: S13 ran only trim 0,
    `IABC` low, and accepted no deck.
  - S4 sets the large-signal amplitude "per point". If that changes the 5 V step or the 10 V sine of a what-if
    deck at 0 pF, the PWL and sine lines differ from the S13 deck.
  - The pinned builder writes the line as `Cwhatif out inm 10p`, not with the text `1e-11`.
  - P10 is a stop on failure. As written it either stops a correct run or is re-read by the executor.
- **Required correction.** Define the comparison exactly: the what-if deck with its capacitor line removed equals
  the deck that the pinned S13 modules build for the same point **with the same `.nodeset` block passed in**, byte
  for byte; the seeds are compared separately under S6.5. State which seed a what-if deck uses. State the value
  test as numeric (10 pF), and that exactly one element is added, between `out` and the protected node (`inm` on
  the network side of the loop probe). Resolve the amplitude rule first (finding 5), so that it is known whether a
  0 pF what-if deck keeps the S13 stimulus.

## Non-blocking findings

### 4. Ruling S2 is acceptable, but it has no ceiling, a discontinuity at the limit, and an undefined baseline case

- **Location.** Ruling S2; labels; Ruling S7; mutations N2 and N11.
- **Assessment.** Not rejected. The reason is in the record: class A has 53.5° and 25.6 %, so K4 is not the twin of
  45° that Ruling 2 assumed. K1, K2 and K5 stay absolute, the form is said to be looser, the rows are labelled and
  listed apart, and their use for a move is the owner's. DS-176 allows a corrected test only through a new
  reviewed brief, which this is.
- **Defects.**
  - No upper bound on the baseline. A corner with any peaking or overshoot at zero stray enters the relative form
    as long as K1, K2 and K5 pass. Within S14's scope the largest known case is the class A harness corner (4.1 dB,
    39.7 %), but the rule is not limited to it.
  - A corner at 24.9 % must stay under 25 %; a corner at 25.1 % may reach 30.1 %. The worse baseline gets the
    looser test.
  - If K4 at zero stray is `NOT EVALUATED: window not settled` (S3), S2 does not say whether the corner "exceeds
    K4". It has no baseline figure.
  - Each record holds several edges (two or four overshoot figures). S2 does not say which figure is compared with
    which.
  - S2 does not say whether it applies to what-if cells. S7 and N11 do not say that a relative-form row cannot
    count as support in the per-IC table without the owner's decision.
- **Required correction.** Rule a ceiling for the baseline (ASSUMED, stated before the run), or state that none
  exists and why K1 and K2 suffice. State the discontinuity as a known property and report, for each relative-form
  row, the limit the absolute form would give (none) and the margin used. Rule that an unevaluated baseline makes
  the corner `NOT EVALUATED`. Rule the comparison per edge against the same edge at zero stray. State whether S2
  applies to what-if rows. Extend N11: an IC marked supported through a relative-form or `PROVISIONAL` row is
  rejected.

### 5. The per-point amplitude of S4 has no stated source and conflicts with rebuilding decks without simulating

- **Location.** Ruling S4 "Clipping"; "End checks" (`--check` rebuilds every deck text without simulating).
- **Defect.** "That point's own small-signal gain at the stimulus frequency" is a result of the same deck that
  holds the large-signal stimulus. The brief does not say whether the gain comes from an earlier invocation
  (counted against the caps, and against the time estimate), from an analytic figure, or from inside the deck. A
  deck text that depends on a measured value cannot be rebuilt by `--check` unless the value is read from the
  record.
- **Required correction.** Rule the source of the gain, that the S13 amplitude is kept unless the predicted peak
  enters the 1 V band, that the amplitude used is in the record and is the one `--check` rebuilds from, and
  whether a pre-pass counts as an invocation.

### 6. A criterion that is NOT EVALUATED at zero stray has no stated row label

- **Location.** Rulings S2, S3 and S4; labels.
- **Defect.** S3 and S4 say an unevaluated K4 or K5 "counts as not passed". At zero stray that reads as
  `FAILS AT ZERO STRAY`. The blocking finding of the S13 result review was exactly a failure label on a measurement
  that was not valid.
- **Required correction.** Rule that a corner whose only missing pass at zero stray is a `NOT EVALUATED` criterion
  is labelled `NOT EVALUATED: <reason>`, never `FAILS AT ZERO STRAY`. Add a mutation for it.

### 7. The cache binding is adequate against a stale or foreign file, but it does not do what N9 says

- **Location.** Arm R "Where the waveform comes from"; mutation N9.
- **Assessment.** A cached waveform is used only if its deck text hashes to the recorded key and the pinned S13
  measurement on it reproduces the record; otherwise a replay; otherwise `NOT EVALUATED`. Every sample that S3 and
  S4 read lies inside a window that S13 measured (the 12 to 14 time-constant window lies inside the recorded 7 to
  14 one). An unbound waveform cannot be used silently.
- **Defects.**
  - S13 records no hash of a data file. The binding is by metrics. A single changed sample that moves no rounded
    metric passes it, so N9 cannot be guaranteed as worded.
  - "Six significant digits" is not available for overshoot: `overshoot()` records five.
  - The cached `.cir` holds the data path in place of `@D@`; the key is the hash of the text with the placeholder.
  - The replay tolerances (0.01°, 0.01 dB, 0.1 percentage point) name no figure for K5 (volts), K6 or K8.
  - A replay must take its `.nodeset` block from the pinned S13 seed record to rebuild "to the identical key". The
    brief does not say so, and does not say that a replay needs no new seed.
- **Required correction.** Bind on every time-domain metric of the record (K4 including the injection window, K5,
  K6, K8 time constant, sine swing), equal as recorded. Reword N9 to a sample inside a K4 or K5 window that moves a
  recorded figure. Record the SHA-256 of each waveform file S14 uses. State the placeholder step, the replay
  tolerances for K5, K6 and K8, and the seed source of a replay.

### 8. The bracketed what-if sets sweep one bracket, and a single check at `C_lim` does not satisfy Ruling 6

- **Location.** Arm W table ("bracket open") and the bullet "The other bracket is checked by the Ruling 6 pair at
  `C_lim`".
- **Defect.** Ruling 6 makes a row `PROVISIONAL` when the two brackets differ by more than 2° in K1 or by one
  candidate step in `C_lim`. The second test needs the other bracket's sweep. In S13 the brackets already differ by
  4.0° at 0 pF for `c7bb7f88` and `932a592b`. With the capacitor fitted the worse bracket is not known in advance,
  and one deck at `C_lim` does not test `2·C_lim` for the other bracket.
- **Required correction.** For the four bracketed sets, run the other bracket at 0, `C_lim` and `2·C_lim` (inside
  the existing caps), label the row `PROVISIONAL` when the 2° test fails or any of those points fails, and state
  that the `C_lim` comparison of Ruling 6 is NOT RUN. The same wording is needed for class G: only the
  larger-resistance trimmer setting is run (name it: trim 1.0, 59.9 kΩ), so the trim 0 corners are NOT RUN and the
  row says so.

### 9. Class G is run last although the disposition's lesson was "class G not last", and P6b can spend class G time outside its ceiling

- **Location.** "Order"; "Class G ceiling"; P6b; "Arm 0 ceiling 20 min".
- **Defects.**
  - The S13 disposition lists "class G not last" among the lessons. The brief runs it last and gives no reason.
    The 45 min are a ceiling, not a reservation: if the other arms take more than 1 h 45 min, class G ends in
    STOP 3 and not as `NOT EVALUATED: class G time ceiling`.
  - P6b runs the 0 pF class G decks in Arm 0. Four corners with up to four 120 s attempts each is 32 min in the
    worst case, against an Arm 0 ceiling of 20 min, and that time is not counted in the class G ceiling.
  - P6b ends class G on "a class G miss"; the bound ends it when "the first four class G points are all
    `NOT EVALUATED`". These differ. The stated order (arm G, then the what-if) also does not start with those four
    points.
- **Required correction.** Either reserve the 45 min (the other arms stop at 1 h 45 min) and say why class G is
  last, or move it earlier under its own ceiling. Count the class G part of P6b against the class G ceiling and
  say that a class G timeout there ends class G, not the run. Give one rule for ending class G. The worst case of
  the other arms from the S13 timings is about 97 min (65 replay, 15 new class C, 12 what-if, 5 pairs), so a
  reservation fits.
- **Assessment of the dropped tight step and the 120 s timeout.** Sound. The tight step gave no accepted deck in
  18 of 18 points (7 timeouts, 5 without convergence, 6 fallbacks). The other two steps ran in 3 to 6 s per deck.
  The expected 20 s per point is conservative.

### 10. The Ruling 6 output-pair count can exceed "at most 60 decks"

- **Location.** Arm R, "The Ruling 6 output pair is run at `C_lim` for every row of arms W, G and R that gets a
  limit: at most 60 decks".
- **Defect.** The pinned S13 form is two points (0 and 100 pF on the output) at the deciding corner per topology,
  each a loop and a closed-loop deck: four decks. If every topology gets a limit that is 16 topologies (9 non-G
  what-if, class G what-if, class G, A, D and 3 of C) and 64 decks. The brief does not say whether 60 is a cap
  that stops the run, or what the unit is.
- **Required correction.** State the unit (per topology at the deciding corner, or per row), recount, and say
  whether reaching the figure is a stop. The total cap of 900 has room either way: my worst-case count without
  ladder fallbacks is about 850.

### 11. Control P9 may need a class B deck that the brief forbids

- **Location.** P9 ("a class B record with a ±11.97 V sine swing … from the S13 cache or a replay"); "No class B
  deck"; N10.
- **Defect.** If the cached file fails its binding, P9 calls for a class B replay, and the STOP section forbids any
  class B deck.
- **Required correction.** Say that this case is read from the cache only and that an unbound file makes P9
  `NOT EVALUATED`, which is a stop; or exempt one named replay. Also add the real tie case to P9: the class C
  100 pF record must fail K6 and K8 under S5.

### 12. Ruling S6 matches Addenda B and C and DS-177, with three small differences

- **Location.** Ruling S6 items 3, 4 and 8; mutation N8.
- **Assessment.** Items 1 to 7, 9 and 10 match C2.1 to C2.6, B2.4 to B2.6 and the Revision 8 fallback rule. Item 8
  matches DS-177; `wavefolder.py` leaves LM13700 pins 2 and 8 unconnected, so `ota_nc2` and `ota_nc8` are the two
  nodes.
- **Defects.**
  - Item 4 says "amplifier inputs within 1 mV (not for the OTA)". Addendum B and the pinned `seed_validity` skip
    the input test for the whole class G cell. The byte copy and the text disagree.
  - Item 3 omits "a cell with no non-zero DC source has no ramp" (C2.3), and S6 omits the per-seed record of C2.7.
  - N8 tests the exclusion by node name. Nothing tests that the excluded set is derived from the rule (one device
    pin, no other element, unconnected in the specification).
- **Required correction.** State which reading of item 4 holds and list the code change if it is the stricter one.
  Restate C2.3's last sentence and C2.7. Add to N8: a node with one device pin that the specification does
  connect is not excluded.

### 13. The cost of the capacitor is predicted but is not in the what-if rows, and three NOT RUN items are missing

- **Location.** "Expected outcome"; Arm W last bullet ("That table is report-only"); "Outputs".
- **Defect.** K7 of a what-if row is measured against the what-if cell at zero stray. A row
  `WHAT-IF 10 pF, NOT ADOPTED: BUDGET n pF` can then be read as passing K7, while the cell with the capacitor is
  predicted to be 7.2° (E-audio) and 3.6° to 4.3° (class G) away from the specification cell at 20 kHz. The NOT RUN
  list of the report does not name the Ruling 6 output pair of H-output (NOT RUN in S13 and still so), classes B,
  F and I, or the un-run corners of finding 8.
- **Required correction.** Put the gain and phase difference at 20 kHz against the specification cell into each
  E-audio and class G what-if row, with the note that it exceeds the 2° of K7 where it does. Add the three items
  to the NOT RUN list with their reasons.

### 14. The owner chose an option whose text named class B and promised U8409; the correction should reach the owner before admission

- **Location.** "One correction to the option the owner chose"; DS-181 ("owner notified").
- **Defect.** None in substance: the correction is right (first section of this review). The owner's choice was
  made on the text "At best it frees U8409 and U5110". After the correction S14 can free no IC outright: U8409
  stays blocked by class B, U5209 and U5210 by class F, and U5110 can only be supported through what-if rows and
  relative-form rows, both of which need a further owner decision.
- **Required correction.** Before admission, record that the owner has seen this consequence and still wants the
  study, or that the choice stands by the owner's earlier wording. Add to "Expected outcome" the sentence that no
  IC can be unblocked by S14 without a further owner decision.

## Revision 2 re-review: ACCEPT (0 blocking, 3 non-blocking wording points)

2026-11-28. Re-review of Revision 2 of the brief, SHA-256
`eca152126979f2a00ae027fc8500a48eec704b70be475409794000c03f050183` (uncommitted draft, same path), by the same
reviewer. Read-only, except for this section. No deck, docker, commit or GitHub write. Everything above this
section refers to Revision 1 and stands as written.

The three points below change no row that the brief does not already bound. The manager may confirm them by
inspection of a wording patch, or the executor may take the stricter reading under STOP 6 and list it. No further
review round is required for them.

### All fourteen Revision 1 findings are closed

| # | Finding | Revision 2 | Verdict |
| --- | --- | --- | --- |
| 1 | Arm R counts | 152 closed-loop and 152 loop records, 22 rows (A 11, C 10, D 1) in the scope, P6 and reviewer check 5 | CLOSED |
| 2 | 24 pF without a test at 48 pF | tested values and candidates stated apart; candidates 4, 6, 8, 12, 16, 32, 50 pF, each with its double tested; N13 | CLOSED |
| 3 | P10 byte identity | comparison against the pinned-module build with the same `.nodeset` block; seeds compared under S6.5; numeric 10 pF; class G reference built from the S14 seed | CLOSED, see R2-1 for the rescaled decks |
| 4 | S2 gaps | baseline ceiling 6.0 dB and 50 % (ASSUMED), also a ceiling on every passed value; discontinuity stated; per edge, path and node; unevaluated baseline is `NOT EVALUATED`; applies to what-if; S7 and N11 extended; N15 | CLOSED |
| 5 | Amplitude source | S13 amplitude first, one rescaled second deck from the recorded swing, amplitude in the record, `--check` rebuilds from it, counted; N16 | CLOSED, see R2-1 |
| 6 | Label at zero stray | `NOT EVALUATED`, never `FAILS AT ZERO STRAY`; N14 | CLOSED |
| 7 | Cache binding | every time-domain metric digit for digit, placeholder step, waveform hashes recorded, replay tolerances for K5, K6 and K8, replay seed from the S13 record; N9 reworded; the limit of the binding is stated | CLOSED |
| 8 | One bracket, one trim | 12 bracket-check points at 0, `C_lim` and `2·C_lim`; `PROVISIONAL` rule; `C_lim` comparison NOT RUN; trim 1.0 named with a stop if it is not the larger resistance | CLOSED |
| 9 | Class G order and P6b | 45 min reserved, other arms 1 h 45 min, reason for "last" given, no class G deck in Arm 0, one rule for ending class G | CLOSED, see R2-2 for one stale phrase |
| 10 | Output-pair count | per topology, four decks, at most 64, the total cap governs | CLOSED |
| 11 | P9 and class B | cache first, exactly one named replay allowed, no row; class C tie case added | CLOSED |
| 12 | S6 differences | C2.3 sentence, stricter class G input test listed as a code change, exclusion derived from the rule, C2.7 record; N8 extended | CLOSED |
| 13 | Cost in the rows, NOT RUN items | 20 kHz gain and phase difference in every what-if row with the K7 note; NOT RUN list extended | CLOSED |
| 14 | Owner informed | stated, with the admission record to hold any objection; "no IC can be unblocked without a further owner decision" added | CLOSED |

### The 2 pF value is dropped soundly, and the counts and bounds still hold

- 11 sets × 11 values = 121, plus 12 bracket points = 133, under the cap of 140. The table sums to 133
  (55 + 22 + 22 + 22 + 12). Arm G is 22 points. DS-181 in `decisions.md` says 133.
- "Every paper estimate in scope is 6.3 pF or more" is correct: the smallest `c_paper_pF` among the E, H-REF9 and
  G rows of `budget.json` is 6.32 pF (`/W1/DRIVE_INV_SUM`). A limit below 4 pF could give no headroom, so the 2 pF
  candidate cannot change a usable row.
- 1 h 45 min + 45 min = 2 h 30 min; 20 + 20 + 150 + 35 min = 3 h 45 min. The 12 bracket points add about 1 min to
  the 97 min worst case of the other arms.
- The bracket checks add 8 seeds (4 sets, loop and closed-loop, a DC-distinct bracket). My estimate is about 52
  seeds against the cap of 60. That is close but inside.

### Non-blocking points

#### R2-1. The rescaled second deck of S4 is not reconciled with P10, with cells that idle away from 0 V, or with arm R

- **Location.** Ruling S4 "Clipping"; Ruling S1 ("the comparison of P10 holds at every value"); P10 ("for every
  what-if deck that is built"); Arm R ("New decks, class C only").
- **Defect.**
  - A rescaled what-if deck has other stimulus lines than the pinned S13 build of the same point, so P10 as worded
    fails on it, and P10 is a stop.
  - The scale 0.9 × (11 V / recorded peak) assumes the output is proportional to the stimulus. `TARGET_SUM`
    (`ee93250a`, two nets) idles at 5 V and reaches 10 V on the S13 step by design. Its S13 records peak at
    11.97 V at every value from 0 pF. The 0.9 factor covers a peak of about 11.5 V there; a record pinned at the
    rail gives no true peak to scale from. The outcome is still bounded (`NOT EVALUATED: output clipped` after the
    second deck), but the brief should say so in advance for this set.
  - The rule does not say whether the step, the sine or both are scaled, or that the second deck supplies K5 only
    and every other criterion stays with the first deck.
  - One arm R record enters the band (class A, 1 nF harness, 100 pF: 11.51 V in the cached waveform). The rule
    says "the point is run once more", and arm R says new decks are for class C only.
- **Required correction.** Exempt the rescaled deck from the byte identity of P10 and compare it with the stimulus
  amplitude normalised. State that the scale applies to the excursion from the quiescent output, or that the 0.9
  factor is the only margin. Name the stimuli scaled and that the second deck gives K5 only. State whether arm R
  re-runs a clipped record or leaves its K5 `NOT EVALUATED`.

#### R2-2. Two phrases are stale after the class G move out of Arm 0

- **Location.** STOP 2 ("except the class G case of P6b"); P10 in the Arm 0 table.
- **Defect.** P6b no longer has a class G case. The class G what-if decks are built in the class G arm, after
  Arm 0, so P10 on them runs later, and the brief does not say that a P10 failure there is a stop.
- **Required correction.** Delete the exception in STOP 2. State that P10 is applied whenever a what-if deck is
  built and that a failure at any time is a stop.

#### R2-3. The candidate rule of arm R is not stated per corner

- **Location.** "Arm W" limit rule; N13; Arm R new class C decks.
- **Defect.** The candidate list is given for arms W and G only. Arm R uses the S13 candidates, and at class C
  wiper 0.5 the tested values are 0, 25, 32, 40, 50, 64, 80 and 100 pF. The pinned `corner_limits` accepts a
  candidate when the largest tested value reaches its double, not when the double itself is tested. N13 does not
  say whether it applies per corner.
- **Required correction.** State that in arm R a candidate counts at a corner only if its double is a tested value
  at that corner (for wiper 0.5: 20, 25, 32, 40 and 50 pF), and that N13 is applied per corner.
