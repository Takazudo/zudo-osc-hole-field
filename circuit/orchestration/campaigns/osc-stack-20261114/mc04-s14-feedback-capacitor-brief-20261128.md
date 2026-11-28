# MC04-S14 brief: a 10 pF feedback capacitor on the weak-loop cells as a what-if, and a corrected-test re-score of classes A, C and D (DS-181), Revision 3

2026-11-28. Issue #367 (MC-04 paper gate). The owner chose option 1 of `mc04-s13-disposition-20261127.md` on the
DS-180 card (2026-11-28 07:21Z). Briefed by the design authority under DS-03 (Fable design agent at high effort,
model `claude-fable-5-2`). Executor: one session in the Cloud container. Repository `zudo-osc-hole-field`, branch
`local/cloud-engineering-20261127`, at `0e54e80a199319b881a4decf7ac7400602217322`.

**Kind:** study only. It produces model evidence. It adopts nothing and edits no board, schematic, spec, BOM, owner
bundle, inventory, gate record, options file or generated file, and no file of the S13 study. Every board and
schematic stays an unvalidated draft, check 5 stays NEEDS_DESIGN and #318 stays HOLD. **No capacitor is adopted by
this study.** Fitting one is a separate owner decision after the result, with its own specification change, BOM
entry and evidence.

**State:** PLANNED, not admitted. Revision 1 (SHA-256
`985f5ce518e2b15c56897d4ede852638ad514d423f4814a1aceb3ebe3e5940ec`) was reviewed ACCEPT WITH CORRECTIONS (3 blocking,
11 non-blocking) in `reviews/mc04-s14-brief-review-20261128.md`. Revision 2 (SHA-256
`eca152126979f2a00ae027fc8500a48eec704b70be475409794000c03f050183`) applied all fourteen and was re-reviewed ACCEPT
with three non-blocking wording points. **This Revision 3 applies those three** (tables at the end). The manager confirms it and admits the run after the admission checks in
"Run bounds".

## One correction to the option the owner chose: class B already carries this capacitor

The option text named "the E, REF9, G and B-SUM cells". That was this design authority's error for class B.

- The `bipolar_attenuverter` cell already has the part: inventory line `line-audio-feedback-c`, function
  `bipolar_attenuverter:C_FB`, 47 placements, and the S13 class B deck has `C1 inm out 1e-11` beside the two
  100 kΩ resistors.
- The class B limit of 2 pF is set by K7 (2° at 20 kHz). For this cell the phase of the non-inverting path moves
  by about ω·R/2 per farad on the summing node, 0.36° per pF at 20 kHz with R = 100 kΩ. A feedback capacitor does
  not enter that term to first order, so a second capacitor cannot move the K7 limit. S13 measured K7 tripping at
  6 pF, which is this figure.
- **Ruling:** class B is not run in S14. Its 23 rows keep their S13 labels. What could change them is a resistor
  value (a specification change) or a different K7 or pair-corner ruling; both are outside this study and are
  listed under "Who decides what".
- **Consequence for the owner:** U8409 depends on class B rows, so S14 cannot free U8409. The disposition said
  "at best it frees U8409 and U5110"; that is withdrawn. S14 can at best support U5110, and only for the slots
  that do not cross a class F row. The main reason for S14 stands: 11 rows show a weak loop with no stray at all.
- **The owner has been told.** The manager informed the owner on 2026-11-28 that S14 can at best support U5110 and
  not U8409, and that the work continues unless the owner objects. The admission record states whether an
  objection arrived. An objection stops the admission.

## What this study answers

1. **What-if.** With one KEMET C0603C100J5GACTU (10 pF) from the amplifier output to the protected node, do the
   weak-loop cells of S13 (E-control, E-audio, H-REF9) and the class G cell pass, and what stray limit would each
   have? This is the Ruling 7 what-if of S13, at most 140 points.
2. **Class G baseline.** The specification cell of class G, which S13 could not evaluate.
3. **Re-score.** Classes A, C and D of S13 under the corrected tests of DS-176 and DS-178, from the recorded S13
   data, with new decks only where the record cannot give the corrected measurement.
4. **Per IC.** For U5110, U8409, U5209 and U5210: which rows now have a limit, under the unblock rule of DS-178.

It does not answer whether any real board is stable, and it does not decide that a capacitor is fitted.

## Rulings made in this brief

Everything not restated here stands as in the S13 brief Revision 8 (`360eb262…225bf4`): Rulings 1, 3, 4, 5 and 6,
criteria K1, K2 and K6 to K9, the stimulus table, the class structure and the model limits. S14 is self-contained
for the operating-point rules and the corrected tests, which are written out below.

### Ruling S1: the what-if cell is the specification cell plus one ideal 10 pF from output to the protected node

- The part is C0603C100J5GACTU, inventory line `line-audio-feedback-c`, owner bundle
  `.claude/skills/component-kemet-c0603c100j5gactu/` (identity VERIFIED, 10 pF ±5 %). It is simulated as an ideal
  10 pF capacitor: no vendor SPICE model of it is retained and none is claimed.
- Position: between the amplifier output pin of the unit that owns the protected node and that node. For class G
  this is `PRE_GAIN` to `PRE_GAIN_SUM`, across the fixed resistor and the trimmer together.
- Exactly one element is added: between `out` and the protected node, which is `inm` on the network side of the
  loop probe. Its value is 10 pF, tested as a number (the pinned builder writes `Cwhatif out inm 10p`).
- Nothing else in the cell changes. The what-if deck with its capacitor line removed must equal, byte for byte,
  the deck that the pinned S13 modules build for the same point **when the same `.nodeset` block is passed in**
  (control P10).
- A what-if deck uses the seed of its own what-if netlist at `C_stray` = 0 (S6). A capacitor does not change a DC
  solution, so where an S13 seed of the same cell and corner exists the two are one group under S6.5 and are
  compared there, not by text.
- The first deck of a what-if point uses the S13 stimulus of the same point (S4), so the comparison of P10 holds
  for it at every value. A rescaled second deck (S4, "Clipping") is compared with the pinned build in which the
  two K5 stimuli carry the same recorded scaled amplitude; every other line must be byte-equal.
- The ±5 % tolerance is not swept. The factor of two stands in for it, as for every other tolerance.
- Every what-if row is labelled `WHAT-IF 10 pF, NOT ADOPTED:` before its label. No other value is run.

### Ruling S2: K1, K2 and K5 stay absolute; K3 and K4 gain a relative form for a cell that already exceeds them with no stray

S13 showed that K3 and K4 can be exceeded at zero stray by a cell whose loop is sound (class A: 53.5° with 25.6 %;
with its own 1 nF harness 4 dB of peaking). A stray budget answers what a move may add. So:

- **K1, K2 and K5 are absolute at every value, as in S13.** A cell that fails one of them at zero stray is
  `FAILS AT ZERO STRAY` and has no limit.
- **K3 (3 dB) and K4 (25 %) keep their limits.** If a corner passes both at zero stray, they apply absolutely at
  every value, as in S13.
- **If a corner exceeds K3 or K4 at zero stray while K1, K2 and K5 pass,** the corner is marked
  `BASELINE EXCEEDS K3` or `K4`, and the test at each value becomes relative: peaking at most 1.0 dB above its
  zero-stray value, overshoot at most 5 percentage points above its zero-stray value. Both figures are ruled here
  and are ASSUMED.
- **Ceiling on the baseline (ASSUMED, ruled before the run).** The relative form is open only to a corner whose
  zero-stray peaking is at most 6.0 dB and whose zero-stray overshoot is at most 50 %. Above either, the corner is
  `FAILS AT ZERO STRAY` on K3 or K4. The largest known case in scope is the class A harness corner (4.1 dB,
  39.7 %). The relative test may also never pass a value above those two ceilings.
- **Known property.** A corner at 24.9 % must stay under 25 %; a corner at 25.1 % may reach 30.1 %. The form is
  discontinuous at the limit. For each relative-form row the report gives the zero-stray figure, the margin used,
  and the statement that the absolute form gives no limit.
- **Per edge.** A record holds several edges, paths and measured nodes. Each is compared with the same edge, path
  and node at zero stray, and the worst decides.
- **Unevaluated baseline.** If K3 or K4 at zero stray is `NOT EVALUATED` (S3), the corner has no baseline and is
  `NOT EVALUATED: <reason>`.
- **What-if cells.** S2 applies to them in the same way, with the same label.
- **This is looser than Ruling 2 of S13 and is said so.** The S13 labels stand in the S13 record. A row whose limit
  rests on the relative form carries that in its label, is listed separately in the report, and may be used for a
  move only by an owner decision.

### Ruling S3: K4 needs a settled window

The final value of a K4 step is the mean of the last tenth of its window. The window is settled when the
peak-to-peak in that last tenth is at most 5 % of the step. If it is not settled, K4 is
`NOT EVALUATED: window not settled`, the first peak is recorded, no percentage is quoted, and the value counts as
not passed. In a positive control an unsettled K4 window counts as the required K4 failure.

**Label when a criterion is not evaluated at zero stray (applies to S3 and S4).** A corner whose only missing pass
at zero stray is a `NOT EVALUATED` criterion is labelled `NOT EVALUATED: <reason>`, never `FAILS AT ZERO STRAY`.
`FAILS AT ZERO STRAY` needs an evaluated failure.

### Ruling S4: K5 measures oscillation, in a window that starts after the cell has settled

- For a cell with its own stated filter (class C) the late window starts no earlier than 12 zero-stray time
  constants of that corner after the edge, the same multiple at every corner.
- For every other cell the late window is the second half of the hold, as in S13.
- The step residual is the peak-to-peak after removing the mean only. No polynomial detrend.
- The sine residual is what remains after a least-squares fit of the fundamental and harmonics 2 to 10.
- **Clipping.** Every deck first uses the S13 amplitude of its point, unchanged. The output swing is read from
  the record. If it enters the band 1 V inside either rail, K5 of that record is `NOT EVALUATED: output clipped`
  and the point gets **one** second deck:
  - Scaled: the two K5 stimuli only, the large step and the 20 kHz sine. The K4 small step, the K6 step and the AC
    and noise analyses are not changed.
  - Scale: 0.9 × (11 V − |Vq|) / (recorded peak excursion from Vq), where Vq is the quiescent output of the seed,
    rounded to three significant digits. The 0.9 is the only margin.
  - The second deck supplies K5 only. Every other criterion stays with the first deck.
  - The scaled amplitude is written to the record, and `--check` rebuilds the second deck from that recorded
    value. The second deck is an invocation and counts against the caps.
  - If the second deck also enters the band, K5 stays `NOT EVALUATED: output clipped` and counts as not passed.
  - A record pinned at the rail gives no true peak, so the scale can be too small. This is expected for
    `TARGET_SUM` (`ee93250a…`), which idles at 5 V and peaked at 11.97 V at every value in S13: its K5 will likely
    be `NOT EVALUATED: output clipped` if the what-if cell still rings to the rail. That is an accepted outcome.
  - Arm R: a record whose swing enters the band (one is known: class A, 1 nF harness, 100 pF, 11.51 V) gets the
    same one second deck, built by the pinned S13 modules with the scaled amplitude and the S13 seed.
  - No gain is predicted in advance.

### Ruling S5: a pass inside the resolution is a tie, and a tie is a fail

A relative test (K6, K7, K8, K9, and the relative K3 and K4 of S2) whose margin to its limit is smaller than the
recorded resolution of that measurement is a tie and counts as a fail. By this rule class C fails K6 and K8 at
100 pF in the S13 record.

### Ruling S6: the operating point of every deck is seeded and checked (S13 Addenda B and C, with DS-177)

1. **Seed, first pass.** For every DC-distinct deck (cell, corner, loop or closed-loop): the same netlist at
   `C_stray` = 0, default tolerances, `op`, a full-precision record of every node (`set numdgt=15`) and `wrnodev`.
2. **Confirmation pass,** required when the first pass log has a "Transient op" line: the same deck with all
   first-pass node values as `.nodeset`. Accepted only with no "Transient op" line. Exactly one.
3. **DC ramp,** when item 2 is not accepted or the seed fails item 4: a `dc` sweep of the cell's bias source from 0
   to nominal in at least 20 steps, last point. Accepted only with no "Transient op" line. A cell with no
   non-zero DC source has no ramp.
4. **Seed validity.** Operational-amplifier inputs within 1 mV in every class, class G included; only the OTA's
   own inputs are exempt. This is stricter than the pinned `seed_validity`, which skips the test for the whole
   class G cell; the change to the copy is listed in the report. Output at least 1 V inside each rail, every
   node with a DC value from the specification within 10 mV of it, and no "Transient op" line in the deck that
   produced the reference.
5. **Group agreement.** Seeds whose netlists differ only in capacitor values, and the loop and closed-loop seeds
   of one cell and corner, agree within 5 µV on shared nodes. A what-if seed and the S13-equivalent seed of the
   same cell are one group. A disagreeing group is re-seeded once by the ramp, else `NOT EVALUATED`.
6. **Use.** All seed node values are `.nodeset` lines in every loop and closed-loop deck of that cell and corner.
   The seed SHA-256 is in the row and in the deck key.
7. **Acceptance of an evaluation deck.** Every operating point in it equals the full-precision seed reference
   within 50 µV on every node of the cell, the two operating points of a loop deck agree within 0.1 mV, and its
   log has no "Transient op" line. Otherwise that tolerance step yields no metric and the ladder continues. If no
   step is accepted the row is `NOT EVALUATED` with the attempts recorded.
8. **No-connect exclusion (DS-177).** A deck node that carries one device pin and no other element, where the
   specification leaves that pin unconnected, is excluded from items 5 and 7 and is listed in the record with its
   deviation, labelled "diagnostic, not a study result". For class G these are `ota_nc2` and `ota_nc8`. The set
   is derived from that rule on the deck and the specification, not from a list of names. The 50 µV limit is
   unchanged for every other node.
9. **No figure from a rejected operating point** is written as a metric.
   **Recorded per seed:** the method that produced the reference (`op`, `op confirmed`, `dc ramp`), whether the
   first pass fell back, the full-precision reference, the `.nodeset` SHA-256 and the group agreement.
10. **Ladder.** Classes other than G: `reltol=1e-6 vntol=1e-9 abstol=1e-15`, then `reltol=1e-5`, then default.
    **Class G: `reltol=1e-5`, then default, only.** Reason: in S13 the tightest step gave no accepted class G
    deck in 18 of 18 points and cost about 9 600 s in timeouts. This is a bound, stated in every class G row.

### Ruling S7: an IC is unblocked only by all of its rows (DS-178)

An IC counts as supported for a move only when every row of its blocker route and every row on its own pins has a
limit above its paper estimate. A row that is BLOCKED, NOT EVALUATED, failing or without headroom keeps the IC
blocked. A what-if row supports nothing until the owner decides on the capacitor. A relative-form row and a
`PROVISIONAL` row support nothing until the owner decides to use them. The per-IC table shows such rows as
"conditional on an owner decision", never as support.

## Expected outcome, stated before the run

- **Cost of the capacitor, by arithmetic.** 100 kΩ with 10 pF is a pole at 159 kHz: −0.07 dB and −7.2° at 20 kHz
  on an E-audio path. Class G (49.9 kΩ to 59.9 kΩ) gives 266 to 319 kHz, about −3.6° to −4.3° at 20 kHz. These
  exceed the 2° of K7 against the specification cell. The study reports them; whether they are acceptable is the
  owner's question when deciding on the capacitor.
- **Loop.** The capacitor is expected to raise the phase margin of the plain 100 kΩ / 100 kΩ cell above 45°. No
  figure is predicted here. A what-if cell that still fails K1 at zero stray is a result, not a control failure.
- **Class A and D.** Expected to become `BASELINE EXCEEDS K4` (and K3 for the class A harness corner) with a
  relative limit.
- **Class C.** Expected to pass K5 under S4. The limit cannot exceed 40 pF (S5).
- **ICs.** U8409 stays blocked by class B. U5209 and U5210 stay blocked by class F. U5110 can at best be supported
  by what-if rows, for the 60 of 66 slots that do not cross `/W2/F4_SUM`. **No IC can be unblocked by S14 without a
  further owner decision:** what-if rows need the capacitor decision, and relative-form rows need the owner's
  decision to use them.

## Scope

### Arm W: what-if, 133 points (cap 140)

- **Tested values, 11 per set:** 0, 4, 6, 8, 12, 16, 24, 32, 50, 64, 100 pF.
- **Candidate limits:** 4, 6, 8, 12, 16, 32 and 50 pF. Each has its double in the tested list. 24 pF is tested
  (it is the double of 12) and is **not** a candidate, because 48 pF is not tested.
- **Limit rule (Ruling 3 of S13):** `C_lim` is the largest candidate `g` for which every tested value up to `2g`
  passes. A candidate whose double is not a tested value is rejected by the table builder.
- **The candidate rule holds per corner, in every arm.** A value is a candidate at a corner only if its double
  is a tested value at that same corner. The pinned `corner_limits` accepts a candidate when the largest tested
  value reaches its double; the S14 copy is changed to this stricter rule and the change is listed.
- 2 pF is not tested. Every paper estimate in scope is 6.3 pF or more, so a limit below 4 pF could not give
  headroom. A set with no passing candidate has no limit and is `NO HEADROOM AT PAPER`, with "no candidate from
  4 pF passes" as its reason.
- 11 sets × 11 values = 121 points, plus the 12 bracket points below.

| Class | Sets | Cell and corner | Points |
| --- | --- | --- | --- |
| E-control | 5 | topologies `0841e309…` (`/F3/RES_CONTROL_SUM`), `3ef5b8d0…` (`/M4B/COMMAND_SUM`), `8fb559a8…` (`/W1/CONTROL_SUM`), `ee93250a…` (`TARGET_SUM`, two nets), `c7bb7f88…` (`/M4B/COMMAND_INVERT_SUM`, bracket open) | 55 |
| E-audio | 2 | `a10f67ef…` (`FOLDER_SUM`, two nets), `932a592b…` (`/W1/DRIVE_INV_SUM`, bracket open) | 22 |
| H-REF9 | 2 | `e06fd44a…` at TMUX output capacitance 0 and 100 pF, bracket open | 22 |
| G | 2 | `2f451c39…` at trim 1.0 (59.9 kΩ of feedback, the larger setting), `IABC` low and high | 22 |
| Bracket check | 4 | the four bracketed sets (`c7bb7f88…`, `932a592b…`, H-REF9 at TMUX 0 and 100 pF) with the bracket to AGND, at 0, `C_lim` and `2·C_lim` | 12 |

- "Bracket open" is the worse Ruling 6 corner in S13 at zero stray. With the capacitor the worse bracket is not
  known in advance. A bracketed row is `PROVISIONAL` when the two brackets differ by more than 2° in K1 at any of
  the three check values, or when any check point fails. The comparison of the two brackets' `C_lim` that Ruling 6
  also names is NOT RUN, because the AGND bracket is not swept; the row says so. A set without a limit gets only
  the 0 pF check point.
- Class G: only trim 1.0 is run. The trim 0 corners (49.9 kΩ) are NOT RUN and every class G row says so. If the
  netlist shows that trim 1.0 is not the larger feedback resistance, that is a stop under STOP 6.
- One point is one loop deck (K1, K2) and one closed-loop deck (K3 to K9).
- K7 and K9 are measured against the what-if cell at `C_stray` = 0. A what-if row that passes K7 has therefore
  not been compared with the specification cell. So **every what-if row carries the gain and phase difference at
  20 kHz against the specification cell at zero stray,** and each E-audio and class G row carries the note
  "exceeds the 2° of K7 against the specification cell" where it does. For class G the reference is arm G; if
  arm G has no accepted deck the field is `NOT EVALUATED`.
- The report also gives the full "cost of the capacitor" at zero stray: gain and phase at 20 kHz, the −3 dB
  bandwidth, integrated noise, and K6 where it applies.

### Arm G: class G specification cell, 22 points

The same two corners and the same 11 values, without the capacitor. These are not what-if points.

### Arm R: re-score of classes A, C and D from the S13 record, 22 rows

Input: `scripts/stack/studies/mc04_s13_node_cap_budget/results.jsonl` at
`7dbfce7bdc8c5a21a6d221e2b78a5dc0468b93a37429b5c3b3271a5af4c20c45`: class A 2 corners × 20 values, class D
2 corners × 20 values, class C 3 topologies × (wiper 1.0: 20 values; wiper 0.5: 0, 25, 50, 100 pF). That is 152
closed-loop records and 152 loop records, for 22 rows: class A 11, class C 10, class D 1.

- **Taken from the record unchanged:** K1 and K2 (loop records); peaking, gain and phase at 20 kHz, noise, K6
  and K8 (closed-loop records). Rulings S2 and S5 are applied to them.
- **Measured again from the waveform:** K4 under S3 and K5 under S4, for every closed-loop record of the three
  classes (152 records).
- **Where the waveform comes from, first the cache.** The cached file in `.circuit-cache/sources/mc04-s13/` is
  accepted only if both hold:
  1. the cached deck text, with its data path put back to the placeholder `@D@`, hashes to the recorded key;
  2. the pinned S13 `runner.py`, run on that file, reproduces every time-domain metric of the record exactly as
     recorded, digit for digit: every K4 overshoot (injection window included), every K5 figure, K6, the K8 time
     constant and the sine swing.

  S13 recorded no hash of a data file, so the binding is by these metrics. A changed sample that moves none of
  them is not detected; every sample S3 and S4 read lies inside a window S13 measured. S14 records the SHA-256 of
  each waveform file it uses.
- **Otherwise a replay.** The deck is rebuilt by the pinned S13 modules, with the `.nodeset` block taken from the
  pinned S13 seed record of that point, to the identical key. No new seed is run. It is run once and accepted
  only if the record is reproduced within 0.01° (K1), 0.01 dB (peaking and gain), 0.1 percentage point (K4), the
  larger of 1 µV and 1 % (K5), and 0.01 % (K6 and the K8 time constant). A replay is an invocation and counts
  against the caps.
- A record with neither is `NOT EVALUATED: waveform not recoverable`.
- **Candidates in arm R.** Classes A and D and class C at wiper 1.0 have the 20 S13 values, so their candidates
  are the S13 ones whose double is tested. Class C at wiper 0.5 will have 0, 25, 32, 40, 50, 64, 80 and 100 pF,
  so its candidates are 20, 25, 32, 40 and 50 pF only.
- **New decks:** the rescaled second decks of S4, and for class C wiper 0.5 at 32, 40, 64 and 80 pF for the three topologies (12 points), because S5
  makes 100 pF a fail and the limit rule then needs the values between 25 and 100 pF. They use the S13
  specification deck with the S4 window and the time-resolution rule of S13 (timestep at most 1/1000 of the
  zero-stray time constant).
- **Ruling 6 output pair.** Unit: one pair per topology that gets a limit, at its deciding corner and at `C_lim`,
  with 0 and 100 pF on the output; each of the two points is a loop and a closed-loop deck, so four decks per
  topology. At most 16 topologies (9 non-G what-if, class G what-if, class G, A, D and 3 of C): at most 64 decks.
  64 is a count, not a separate stop; the total cap governs.
- Class C rows stay `PROVISIONAL` where a part on the net is `IDENTITY OPEN`, as in S13.

### Not in scope

- Class B (23 rows): see the correction above. Classes F and I (6 rows): blocked, no vendor model for BAS16GW-QX
  and BCM847BS,115; no generic model is substituted. H-output (1 row): keeps its S13 label, `NO HEADROOM AT PAPER`;
  its Ruling 6 output pair was NOT RUN in S13 and stays NOT RUN.
- The class F diagnostic of S13: NOT RUN, not part of the owner's choice.
- Any capacitor value other than 10 pF, any second capacitor, any changed resistor.
- U1415: handled separately, as in S13.

## Pinned inputs

| Input | SHA-256 |
| --- | --- |
| this brief, at the revision admitted | recorded at admission |
| S13 brief Revision 8 | `360eb262216fdf80004bc4d0d7d4108f64a8c003d1b2e97ab73f255d30225bf4` |
| S13 disposition | `93d75e2bba4e32cce6188638675f25f39d7228e0c3911e0c0cfbb44e65aac0d0` |
| S13 result review | `2264925b62386271de73b8f391f9cf44ea92ee19b2730ebbbd58c5f5b3732c65` |
| S13 `results.jsonl` | `7dbfce7bdc8c5a21a6d221e2b78a5dc0468b93a37429b5c3b3271a5af4c20c45` |
| S13 `budget.json` | `511c29409661dd236695dc0bcb368f97d5e95b87bf0f29d1378b5dae01bd4136` |
| S13 `result.json` | `4310cbbc97420817b15ae6b56b480836d8d0d6a067651edebc7c9f59fe93ca1a` |
| S13 `census.json` | `a28e85b64175e903f9953bc5ffdfc8d9164d64c870ad889bb748caa8bbdfc830` |
| S13 `models.json` | `5163dc1da7c11ed7164d961d9c977b5ed2dde04e4e9441e5623312fa5531534e` |
| S13 `cells.py`, `runner.py`, `budget.py`, `guard.py` | `a4105eb4…fade6c`, `225f5283…7131c2`, `e691ef18…95ec931`, `5d066228…c51651` (full values in the admission record) |
| OPAx196 Final 1.5: ZIP, library | `9c264813a36536f743c166b6a101904b76ed08f049f2eeb127a438cc6e8ccdf5`, `31142f5dbd71b758d887ee8a411692fc4c1309c8f47100af4ba5bed7e173c430` |
| OPAx197 Final 1.3: ZIP, library | `9e55fcaa23d54cee025dda3fa9872b11c41c531f82e0802c2b93d51e943666e5`, `fc5b020e63346e511bd808bf41c856b0150b000bcf8a41fe00eeececb1f422a5` |
| `design/spec/modules/spice/filter-model/LM13700.MOD` | `666df501773da5e65f7fd3b3c806b2c1ae7770784685dd8191a9df33b382f390` |
| inventory, and every other pin of the S13 `result.json` `pinned_inputs` | as recorded there; P1 compares each |

The LM13700 identity limit of S13 stands: every class G row is `PROVISIONAL`.

## How the oracle is invoked

- Every deck runs as `bash scripts/kicad/run.sh ngspice -b <deck>` from the repository root, one at a time. The
  image is `kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec` and must report
  KiCad 10.0.6 and ngspice 44.2. A missing image or a version mismatch is a failure under project rule 4.
- **The study directory is new:** `scripts/stack/studies/mc04_s14_feedback_capacitor/`. It starts from byte copies
  of the S13 `cells.py`, `runner.py`, `budget.py`, `guard.py` and tests. Every change to a copy is listed in the
  report with its reason. The S13 directory is not edited; its modules are imported read-only for replays and for
  control P4, so that an S13 deck rebuilds to its recorded key.
- Loop deck and closed-loop deck are as in S13 (Middlebrook double injection at the inverting pin; AC, noise,
  small step, large step and sine in one `.control` block, noise read with `setplot previous`), with rulings S3,
  S4 and S6 applied.
- Timeout: 600 s per deck; **120 s per class G deck**.
- Working files, ignored: `.circuit-cache/sources/mc04-s14/`. The S13 cache is read, never written.
- `.spiceinit` at the repository root: created with the exact content `set ngbehavior=ps` if absent, removed at
  every slice end and at the end. One found at a start with that exact content is removed and recreated; one with
  other content is a stop.
- **Containers are stopped only by the pinned-image form:** `docker ps -q --filter ancestor=<pinned digest>`, then
  `docker kill` on that list. No unfiltered `docker kill`, by the driver or by hand.

## Arm 0: controls, in this order, stop on any failure

| # | Control | Pass condition |
| --- | --- | --- |
| P1 | input pins | every hash in "Pinned inputs" matches |
| P2 | oracle identity | image digest equal to the pin; `kicad-cli version` prints exactly `10.0.6`; the ngspice banner reads 44.2 |
| P3 | model pins | the five model hashes match; OPAx196 from `circuit-dev-resources` commit `54c00fc8` (read-only) as in S13 |
| P4 | S13 record replay | six recorded S13 decks, a loop and a closed-loop deck of each of `/W1/CONTROL_SUM` 0 pF, `/E2/REF9_FB` 0 pF at TMUX 100 pF bracket open, and class A 0 pF with the 1 nF harness: rebuilt by the pinned S13 modules to the identical key, run, and equal to the record within 0.01°, 0.01 dB and 0.1 percentage point |
| P5 | loop-break method | the S14 runner reproduces the three `loop_break_validation` rows (9.953°, 59.67°, 7.713°) within 0.1°; with the probe polarity swapped it fails all three |
| P6 | scope | the 11 what-if sets, the 2 class G corners, the 152 closed-loop and 152 loop arm R records and the 22 arm R rows (A 11, C 10, D 1) are derived from the pinned S13 files and equal the counts in "Scope" |
| P6b | operating points, classes other than G | for every seed of the E-control, E-audio and H-REF9 what-if sets and of the H-REF9 specification cell: valid under S6.4, group agreement under S6.5, and the seeded loop and closed-loop decks at 0 pF accepted under S6.7 at some ladder step. For H-REF9: 9.000 V ± 10 mV and the inverting input within 1 mV of 5.000 V. Class G is not part of Arm 0: its seeds and its 0 pF points run at the start of the class G arm, inside the class G ceiling ("Run bounds") |
| P7 | positive control | the S13 specification cells at 1 nF: `/W1/DRIVE_INV_SUM` fails K1 (S13: 2.600°, within 0.1°) and fails K4 or has an unsettled K4 window (S3); `/E2/REF9_FB` fails K1 (S13: 1.189°, within 0.1°). Both evaluated on an accepted operating point. `NOT EVALUATED` is neither the required failure nor a pass: stop |
| P8 | negative control | the plain unity follower gives 54.82° at 2.597 MHz (OPAx196) and 63.95° at 9.986 MHz (OPAx197), within 0.1° and 0.5 % |
| P9 | corrected tests on known cases | from the S13 cache or a replay: the class C wiper 1.0 record at 0 pF reads below 0.1 mV under S4 (the review found 55 µV from 12 time constants); a class C record at 100 pF fails K6 and K8 under S5; the S13 P7 deck `acd3968e…` is "not settled" under S3; one class B record with a ±11.97 V sine swing is `NOT EVALUATED: output clipped` under S4. The class B case is read from the cache; if its file is not bound, exactly one replay of that one named record is allowed for this control. It yields no row and is the only class B deck of the study |
| P10 | what-if identity | for every what-if deck, checked when it is built, in Arm 0 for the 0 pF decks of the non-G sets and later for every other deck (no run needed): with its one capacitor line removed, the text equals byte for byte the deck that the pinned S13 modules build for the same point with the same `.nodeset` block passed in; exactly one element is added, between `out` and the protected node (`inm` on the network side of the loop probe), and its value is 10 pF as a number. Seeds are compared under S6.5, not here. For class G, where S13 has no seed at trim 1.0, the same definition applies: the reference deck is built by the pinned modules from the S14 seed. A rescaled second deck is compared with the pinned build carrying the same recorded scaled amplitude |

## Tests and mutations

The S13 mutations M1 to M8 and M12 to M21 are carried over on the S14 copies, except M12, which needs a 600 s
deck and is replaced by its in-memory form. Added:

| # | Mutation | Must |
| --- | --- | --- |
| N1 | the capacitor of a what-if deck placed from the node to AGND, or given another value | fail P10 |
| N2 | a row whose limit rests on the relative K3 or K4 labelled as a plain budget | be rejected by the table builder |
| N3 | a what-if row without the `WHAT-IF 10 pF, NOT ADOPTED:` prefix | be rejected |
| N4 | a K4 window with 79 mV of ripple in its last tenth on a 100 mV step | be `NOT EVALUATED: window not settled`, never a percentage |
| N5 | a class C K5 window starting at 7 time constants | be rejected by the builder's test |
| N6 | a relative test passed by 0.001 % at a resolution of 0.05 % | count as a fail |
| N7 | a record with an output swing of ±11.5 V on ±12 V rails | have K5 `NOT EVALUATED: output clipped` |
| N8 | `ota_nc8` moved by 2 mV (in-memory copy) | not reject the deck; the same change on `inm` must reject it; a node with one device pin that the specification does connect must not be excluded |
| N9 | a cached waveform with one sample changed inside a K4 or K5 window so that a recorded figure moves | fail the cache binding of arm R and force a replay |
| N10 | a class B row given any S14 label | be rejected: class B is out of scope |
| N11 | an IC marked supported while one of its rows is BLOCKED or NOT EVALUATED, or supported through a what-if, relative-form or `PROVISIONAL` row | be rejected by the per-IC table builder |
| N12 | the invocation counter fed a discarded and an interrupted deck | count both |
| N13 | 24 pF in arm W, or at any corner of any arm a value whose double is not a tested value at that corner (for example 16 pF at class C wiper 0.5), offered as a candidate limit | be rejected by the table builder, per corner |
| N14 | a corner whose only missing pass at zero stray is a `NOT EVALUATED` criterion | be labelled `NOT EVALUATED`, never `FAILS AT ZERO STRAY` |
| N15 | a corner with 6.5 dB of peaking or 55 % overshoot at zero stray | be `FAILS AT ZERO STRAY`, not a relative-form row |
| N16 | a clipped record given a K5 figure, or a second deck built with an amplitude not in the record | be rejected |

## Run bounds (ORCHESTRATION.md section 3)

| Bound | Value |
| --- | --- |
| Environment | the Cloud container: 4 CPU, 15 GiB RAM, no swap. Interpreter `/home/user/venv312/bin/python` |
| Heavy processes | one at a time; decks run sequentially; no worker pool; no second container |
| Memory budget | 4 GiB on the sum of process-tree RSS and the oracle container's memory, both sampled every 5 s; abort when `MemAvailable` falls below 8 GiB. S13 peaked at 1.6 GiB |
| Admission | `MemAvailable` ≥ 11 GiB, no other heavy process, no container of the pinned image, at least 5 GiB free disk, the pinned image present, no `.spiceinit` with foreign content, and a tree that is clean except the new study directory. This brief, its review and DS-181 are committed by the manager first |
| Start checks | `bash scripts/checks/regen-all.sh` (416 s in S13; ceiling 15 min) and `pnpm circuit:check` (ceiling 5 min) |
| Arm 0 | ceiling 20 min. No control runs a deck that is expected to time out, and no class G deck runs in Arm 0 |
| Order | arm R (cache binding, replays, the 12 class C points), then arm W classes E-control, E-audio, H-REF9 with their bracket checks, then the Ruling 6 pairs of those arms, then **class G last** |
| Why class G is last | the S13 disposition listed "class G not last" because class G then had no time of its own. Here it has a reserved ceiling, so it can neither starve nor be starved. It is last because its cost is the least predictable, and every other result is then already on disk |
| Sweep ceiling | **2 h 30 min, hard, in two parts,** each counted over every slice and including discarded and interrupted work |
| Ceiling of the other arms | **1 h 45 min.** Reaching it is a stop (STOP 3) reported with the arms that are complete. Worst case from the S13 timings is about 97 min: 65 replay, 15 new class C, 12 what-if, 5 pairs |
| Class G ceiling | **45 min, reserved:** it is available whatever the other arms used. It covers the class G seeds, both arms and the class G output pairs. Sequence: the seeds, then the four 0 pF points (each corner, arm G and what-if), then the rest of arm G, then the rest of the what-if, then the pairs |
| How class G ends early | one rule: class G ends as `NOT EVALUATED: <reason>` when a class G seed is invalid under S6, or when all four 0 pF points are `NOT EVALUATED`, or when its ceiling is reached. A class G timeout is never a study stop. Rows finished before the end keep their results; a corner without all its values has no limit |
| Deck caps | **900 ngspice invocations in total,** counting recorded, discarded, interrupted, replayed, seed and control decks alike. Of these at most 180 seed invocations (60 seeds) and at most 200 replays. Reaching any cap is a stop |
| Slices | the background limit is 30 min. A slice ends by itself after 28 min. **A deck starts only if its whole timeout plus 60 s fits before 28 min from the slice start;** otherwise the slice ends with no partial line. One line per finished deck is appended to `results.jsonl`, keyed by deck SHA. A resume re-checks P1 and P3, clears pinned-image containers, and is not a retry. Every slice writes a guard summary, a killed slice included: a slice without one is a deviation and its lines are discarded and run again |
| Stopping the oracle | on a deck timeout, a guard abort, a slice end and at every start and resume: `docker kill` on `docker ps -q --filter ancestor=<pinned digest>`, and that list must be empty before the next deck. A survivor is a stop |
| End checks | `--check` (rebuilds every deck text and every table from `results.jsonl` without simulating), the unit tests, `regen-all.sh --check` (ceiling 15 min), `pnpm circuit:check`, and a check that no `.spiceinit` and no pinned-image container is left |
| Retries | at most one, for a proven transient failure only. A non-converging deck is `NOT EVALUATED` |
| Total wall time | ceiling 3 h 45 min (20 min start, 20 min Arm 0, 2 h 30 min sweep, 35 min end). **Expected 1 h 15 min to 1 h 45 min** |

How the expectation is sized, from the S13 timings: a non-G point took about 4.5 s (loop 0.7 s, closed 3.5 s; 9 s
closed for H-REF9), so the 111 non-G what-if points need about 12 min. Arm R with a valid cache needs minutes;
with every waveform replayed it needs about 65 min (class C closed-loop decks averaged 50 s). The 12 new class C
points need about 15 min. Class G with the two-step ladder is expected at about 20 s per point, 15 min for 44
points, and is capped at 45 min. In S13 every class G deck at these two steps finished in 3 to 6 s. No GitHub Actions job, second VM or paid capacity is used.

## Outputs

Allowed writes, and nothing else:

- the new directory `scripts/stack/studies/mc04_s14_feedback_capacitor/` with the driver, deck builders, runner,
  guard copy, tests, a README, `results.jsonl`, `whatif.json`, `rescore.json`, `result.json` and `checkpoints/`;
- the report `circuit/orchestration/campaigns/osc-stack-20261114/mc04-s14-report-<date>.md`;
- ignored working files under `.circuit-cache/sources/mc04-s14/` and the two model caches.

`whatif.json` holds one row per what-if set and per class G corner; `rescore.json` one row per net of classes A, C
and D. Each row has the S13 fields and exactly one label:

- `BUDGET n pF (MODEL EVIDENCE ONLY)` or `BUDGET CAPPED AT 50 pF (MODEL EVIDENCE ONLY)`;
- `BUDGET n pF, BASELINE EXCEEDS K3` or `K4 (RELATIVE FORM, MODEL EVIDENCE ONLY)`;
- `PROVISIONAL n pF: <reason>`; `NO HEADROOM AT PAPER`; `FAILS AT ZERO STRAY`;
- `NOT EVALUATED: <reason>`;

with the prefix `WHAT-IF 10 pF, NOT ADOPTED:` on every what-if row. Each row also gives, report-only, the limit
that K1 to K5 alone would give, so that the deciding criterion is visible.

The report gives, with headings that state the outcome: the controls; the what-if table beside the S13
specification labels; the cost-of-the-capacitor table; the class G result or the reason it has none; the re-score
table beside the S13 labels, with the relative-form rows listed apart; the per-IC table under S7 for U5110,
U8409, U5209 and U5210; the bounds (fingerprint, peak memory, every slice and resume, invocation counts by kind,
discarded and interrupted work); every reading the executor made that this brief does not spell out; and every
`NOT RUN` item with its reason, including KiCad DRC and ERC, c6 and checks 2 to 4, any bench measurement,
temperature and tolerance corners, the Ruling 6 output pair of H-output, classes B, F and I, the class G trim 0
corners, the AGND-bracket sweeps and the `C_lim` comparison of Ruling 6, and the class F diagnostic.

Status line on every output: "MODEL EVIDENCE ONLY, STUDY, NOT ADOPTED, UNVALIDATED DRAFT". `method_limits` is the
S13 list plus: the capacitor is an ideal 10 pF; its tolerance is not swept; class G uses a two-step ladder; arm R
re-uses S13 records and waveforms.

## STOP conditions

Stop, write what was found, and change nothing further on any of these:

1. input drift: a pin or a model hash differs;
2. any Arm 0 control fails. P10 is applied whenever a what-if deck is built, also after Arm 0, and a failure at
   any time is a stop; on a class G what-if deck it is a stop for class G only, which then ends as
   `NOT EVALUATED: P10 failed`, and it is reported as a defect of the study;
3. the pinned image is missing or does not report KiCad 10.0.6, the admission check fails, the guard fires, a
   container of the pinned image survives `docker kill`, a cap or the sweep ceiling is reached, or a `.spiceinit`
   with foreign content is found;
4. a deck would need a model that is not retained;
5. a result would need a different capacitor value or position, a changed part or a looser criterion than this
   brief states;
6. a rule of this brief is ambiguous in a way that changes a row: take the stricter reading, list it under
   "Readings made", and stop only if no stricter reading exists;
7. any need to write outside the allowed paths, or to edit a file of the S13 study.

No second sweep, no extra value, no class B deck other than the one replay P9 allows, no adoption.

## What the independent reviewer must check

The reviewer is not the executor and not the author of this brief. The review of this brief is read-only; the
later result review as well.

1. That class B already carries `C_FB` 10 pF, from the inventory line and one S13 class B deck, and the K7
   arithmetic of the correction section by own calculation.
2. Rulings S2 to S5 against DS-176, DS-178 and the findings of the S13 result review; that S2 is stated as looser
   than Ruling 2 and cannot produce an unlabelled budget.
3. Ruling S6 against Addenda B and C of the S13 brief and DS-177, item by item.
4. The what-if sets against the S13 `budget.json` topologies, and the point count against the cap of 140.
5. That arm R can be computed from the pinned record as stated (152 records, 22 rows), and what the cache
   binding can and cannot detect.
6. The run bounds: that class G cannot consume the sweep ceiling, that the slice guard and the caps count
   discarded and interrupted work, and that only the pinned-image container form is allowed.
7. That no wording calls a draft validated, qualified or released, and that nothing in the brief adopts a part.

After the run, in addition: P4, P5, P7 and P8 by own arithmetic; three what-if decks against P10; five rows of
the limit rule; the relative-form rows; the per-IC table; and that nothing outside the allowed paths changed.

## Who decides what

| Item | Decided by |
| --- | --- |
| Rulings S1 to S7, the value list, the sets, the labels, and whether the result is accepted as a study | design authority (this brief), owner notified |
| Fitting a feedback capacitor on any cell, its value, and the 20 kHz phase cost it brings | **owner**, as a separate decision after the result |
| Using a row that rests on the relative form of K3 or K4 for a move | **owner** |
| Class B: a changed resistor value, or a different K7 or pair-corner rule | **owner** for the value; design authority by a reviewed ruling for the rule |
| Storing the BAS16GW-QX and BCM847BS,115 vendor models in `circuit-dev-resources` | **owner** |
| Whether a budget row may be used by the placement study, and Ruling 4's geometry terms | design authority on the reviewed result; the placement brief and its review |
| Acceptance of any routed layout or any hardware behaviour | nobody in this study: it needs extracted copper and a bench |

## Evidenced, assumed and not established

| | |
| --- | --- |
| Evidenced (model only) | the S13 record at the pinned hashes; the inventory identity of the capacitor; the class B deck content |
| Assumed | the relative limits of S2 (1.0 dB, 5 points) and its baseline ceilings (6.0 dB, 50 %); the settled-window figure of S3 (5 %); 12 time constants in S4; the 0.9 × 11 V rescale of S4; the two-step ladder for class G; an ideal capacitor; every assumption of S13's `method_limits` |
| Expected, not established | every item of "Expected outcome" |
| Not established by this study, whatever its result | that any board is stable; that a capacitor should be fitted; any class B, F or I limit; any acceptance of a layout |

## Revision 2 changes

Revision 1: SHA-256 `985f5ce518e2b15c56897d4ede852638ad514d423f4814a1aceb3ebe3e5940ec`, reviewed ACCEPT WITH
CORRECTIONS in `reviews/mc04-s14-brief-review-20261128.md`. All fourteen findings are applied.

| # | Finding | Changed in Revision 2 |
| --- | --- | --- |
| 1 (blocking) | Arm R is 152 records and 22 rows | "Arm R" heading, input line and second bullet; P6; reviewer check 5 |
| 2 (blocking) | 24 pF could become a limit without a test at 48 pF | "Arm W": tested values and candidate limits stated apart; mutation N13 |
| 3 (blocking) | P10 byte identity undefined against seeds, class G and the `10p` spelling | Ruling S1 (four bullets); P10 |
| 4 | S2: no ceiling, discontinuity, undefined baseline, edges, what-if, IC support | Ruling S2 (five new bullets); Ruling S7; mutations N11 and N15; "Assumed" row |
| 5 | Source of the per-point amplitude; `--check` | Ruling S4 "Clipping" rewritten: S13 amplitude first, one rescaled second deck from the recorded swing; mutation N16 |
| 6 | Label for a criterion not evaluated at zero stray | new paragraph after Ruling S3; mutation N14 |
| 7 | Cache binding and replay details | "Arm R": binding on every time-domain metric, placeholder step, waveform hashes, replay tolerances for K5, K6 and K8, seed source of a replay; mutation N9 reworded |
| 8 | Bracketed sets and class G trim | "Arm W": 12 bracket-check points, the `PROVISIONAL` rule, the NOT RUN `C_lim` comparison, trim 1.0 named and trim 0 NOT RUN. To stay under the cap of 140 the 2 pF value and candidate are dropped (11 values, 133 points) |
| 9 | Class G order, reservation and P6b timing | "Run bounds": rows "Arm 0", "Order", "Why class G is last", the two-part sweep ceiling, "Class G ceiling", "How class G ends early"; P6b limited to the other classes |
| 10 | Output-pair count and unit | "Arm R", bullet "Ruling 6 output pair": per topology, four decks, at most 64, not a separate stop |
| 11 | P9 could need a forbidden class B deck; add the tie case | P9; last line of "STOP conditions" |
| 12 | S6 against Addenda B and C | Ruling S6 items 3, 4, 8 and 9; mutation N8 |
| 13 | Cost of the capacitor in the rows; missing NOT RUN items | "Arm W" last two bullets; "Outputs" NOT RUN list; "Not in scope" (H-output pair) |
| 14 | The owner must see the U8409 consequence | correction section, bullet "The owner has been told"; "Expected outcome", last bullet |

## Revision 3 changes

Revision 2: SHA-256 `eca152126979f2a00ae027fc8500a48eec704b70be475409794000c03f050183`, re-reviewed ACCEPT with
three non-blocking wording points ("Revision 2 re-review" in the same review file). All three are applied.

| # | Point | Changed in Revision 3 |
| --- | --- | --- |
| R2-1 | The rescaled second deck against P10, cells that idle away from 0 V, and arm R | Ruling S4 "Clipping" (stimuli scaled, scale on the excursion from the quiescent output, K5 only, the `TARGET_SUM` expectation, arm R records); Ruling S1 last bullet; P10; "Arm R" bullet "New decks" |
| R2-2 | Stale class G phrases | STOP 2 (exception deleted; P10 applies whenever a what-if deck is built; a class G failure ends class G); P10 row |
| R2-3 | Candidate rule per corner | "Arm W" new bullet "The candidate rule holds per corner"; "Arm R" new bullet "Candidates in arm R"; mutation N13 |
