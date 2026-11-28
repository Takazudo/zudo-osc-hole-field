# MC04-S13 result review: ACCEPT WITH CORRECTIONS (1 blocking, 10 non-blocking)

2026-11-28. Independent review of the fourth MC04-S13 run (commit `23d6fb49`, branch
`local/cloud-engineering-20261127`). Reviewer: a Fable agent (`claude-fable-5-2`) that is neither the executor nor the
author of the brief. Read-only, except for this file. Brief Revision 8, SHA-256
`360eb262216fdf80004bc4d0d7d4108f64a8c003d1b2e97ab73f255d30225bf4`, confirmed.

Everything below is model evidence on an unvalidated draft. This review establishes nothing electrical.

## The stop and the controls stand; ten class C labels do not

- The STOP 3 stop at the 5 h sweep ceiling is correct and correctly accounted.
- Arm 0 passed as reported, and M12 is NOT EVALUATED as required.
- 54 of the 64 labels follow from the brief's rules and the recorded records.
- The 10 class C rows are labelled FAILS AT ZERO STRAY on a K5 reading that measures the cell's own RC settling
  tail, not an oscillation (finding 1). They must be relabelled before the result goes to the design authority.
- Finding 1 does not give any IC a budget. U8409's binding rows in classes A and B still fail or have no headroom.

## What I ran, and what is NOT RUN

| Check | Result |
| --- | --- |
| `budget.py --check` | PASS: 1 480 decks rebuilt, 0 key mismatches, `budget.json` identical |
| `python -m unittest test_s13` | PASS: 41 of 41 |
| Own re-derivation of all 64 labels from `results.jsonl` (own judge of K1 to K9, own Ruling 3 limit rule) | 64 of 64 equal to `budget.json` |
| Own recomputation from the cached waveforms in `.circuit-cache/sources/mc04-s13/` | class A and D overshoot equal to the record; class C K5, class B sine K5, class G `ota_nc8` and the P7 step as in the findings |
| Any ngspice deck, the sweep, docker | NOT RUN: forbidden to the reviewer |
| Own census derivation and own `C_paper` computation (brief reviewer checks 1 and 6) | NOT RUN: outside the six questions asked; P6 was checked only through the unit test |
| `regen-all.sh --check`, `pnpm circuit:check` | NOT RUN: the review changes one Markdown file under `reviews/` |

## The six questions

| # | Question | Verdict |
| --- | --- | --- |
| 1 | Arm 0 controls and M12 | PASS. P5 9.9528°, 59.6661°, 7.7132°; P6b four corners, group difference 0.99 nV, tightest step and trap; P7 2.600° and 1.189°; P8 54.821° at 2.597 MHz and 63.955° at 9.986 MHz; all equal to `result.json`. M12: timeout, no convergence, transient-op fallback, no metric. The P7 overshoot figure needs a caveat (finding 10) |
| 2 | STOP 3 accounting | PASS. Slice walls sum to 16 604.9 s; with 1 810.1 s discarded the total is 18 415.0 s against 18 000 s. Slice 14 started at 17 160 s, and every point in it started before the ceiling. 1 512 + 325 + 9 = 1 846 invocations; seeds 22 + 78 + 40 = 140 |
| 3 | Labels | 54 follow; the 10 class C rows do not (finding 1). Spot-checked: A `/F3/Cf75ecf_FB`, B(IN+) `/M4A/C154038_W_SENSE` and `/A01/Cc045d2_W_SENSE`, B(IN-) `/M4A/C154038_SUM`, C `/E2/Cd69090_W_SENSE`, D `/W1/C629978_W_SENSE`, E `/W1/DRIVE_INV_SUM` and `/M4B/TARGET_SUM`, H `/E2/REF9_FB` and `/W1/OUTPUT_FB` |
| 4 | Class G | PASS. All 36 records are NOT EVALUATED with `metrics` null; no class G figure is in `budget.json` or P9. Wording corrections in finding 4 |
| 5 | Run-time fixes and the docker kill deviation | PASS. None changes a deck that was recorded (`--check` rebuilds every key) or a criterion. The five unfiltered kills are recorded as a deviation. Two records are incomplete (finding 11) |
| 6 | Wording | PASS for status wording: no output claims validation, qualification or release. NOT RUN reasons are incomplete (finding 8) |

## Blocking finding

### 1. The ten class C rows fail K5 on the cell's own filter tail, so FAILS AT ZERO STRAY is wrong for them

- **Files.** `scripts/stack/studies/mc04_s13_node_cap_budget/runner.py` (`late_residual`), `cells.py` (class C
  `K5_step` windows, lines 701 to 704), `results.jsonl` (60 class C closed records at wiper 1.0), `budget.json`
  (10 class C rows), `result.json` (`label_counts`), the report (headline, class table, per-node table, "Class C
  rows" bullet), `README.md` (status line).
- **Defect.** At wiper 1.0 the zero-stray time constant is 10 µs and each K5 hold is 140 µs. `late_residual`
  starts its window at half the hold, which is 7 time constants after a 10 V step. The RC tail there is still
  9.63 mV. A quadratic detrend cannot remove an exponential, and leaves 3.67 to 3.72 mV. That is the recorded K5
  "residual". Recomputed from the cached waveform of `/E2/Cd69090_W_SENSE` at 0 pF (deck `3b814f62…`):

  | Window | Peak-to-peak |
  | --- | --- |
  | as recorded (from 7 τ, quadratic detrend) | 3.69 mV |
  | same window, one 10 µs exponential removed | 9.8 µV |
  | from 10 τ, raw | 0.47 mV |
  | from 12 τ, raw | 55 µV |

  The other two class C topologies give the same figures. At wiper 0.5 the window starts 13.6 time constants after
  the edge, so the same test reads 13 nV. The two corners were therefore not measured alike. Phase margin (48.8° to
  64.9°), gain margin, peaking and overshoot (0 %) are the same at both wipers. The brief's reviewer check 14
  requires "that no class C row fails on the cell's own filter time". All ten do.
- **Consequences.** The headline "48 of 64 rows fail at zero stray" is wrong: 38 rows fail on recorded evidence.
  Three of the ten are binding rows of the brief: `/M4A/C1c45d6_W_SENSE` and `/M4B/C1c45d6_W_SENSE` (U8409) and
  `/F3/C8c344f_W_SENSE` (U5209). The 48 class C full-list points (96 decks) ran only because of this reading. The
  quadratic detrend and the 10-harmonic fit are the executor's reading of K5 and are not listed under the stricter
  readings (STOP 7).
- **Required correction.**
  1. Withdraw K5 as a class C result at wiper 1.0 and relabel the ten rows
     `NOT EVALUATED: K5 late window overlaps the cell's RC settling tail at wiper 1.0`. Correct the counts to
     38 FAILS AT ZERO STRAY, 9 NO HEADROOM AT PAPER, 6 BLOCKED and 11 NOT EVALUATED in `budget.json`,
     `result.json`, the report and the README.
  2. Put the K5 window for class C to the design authority as a brief question. The cached waveforms allow a
     re-measurement without a deck, but the window is a criterion detail and not the executor's or the reviewer's
     to set.
  3. Do not promote the rows. With K5 set aside every recorded class C value passes, but that is a reviewer
     recomputation and not a study result. Finding 2, the Ruling 6 output pair (NOT RUN) and the `IDENTITY OPEN`
     part on each net all stand before any class C limit.
  4. List the K5 detrend and harmonic fit under the readings made.

## Non-blocking findings

### 2. Class C passes K6 and K8 at 100 pF by 0.001 %, inside the recorded 0.05 % resolution

- **Files.** `results.jsonl` (class C closed records at 100 pF), `budget.json` (class C corners at wiper 0.5,
  `c_lim_pF` 50), the report ("at wiper 0.5 every row reaches 50 pF").
- **Defect.** At 100 pF the time constant rises by 0.9990 % (10.00514 µs to 10.10510 µs) and the 1 mV settling
  time by 0.990 % to 0.998 %. The limit is 1 %, and the recorded `resolution_fraction` is 0.0005. The brief
  expected this point to sit at the limit and ruled that "a tie counts as a fail". A pass by a margin 50 times
  smaller than the resolution is not listed as a reading made.
- **Required correction.** State the margin and the resolution in the report, list the reading, and ask the design
  authority whether such a pass is a tie. Until then no class C corner limit above 40 pF is quoted as a result.

### 3. In 56 class B records the sine output clips at the rails, and the 50 K5 failures among them are not oscillation

- **Files.** `results.jsonl` (`sine_swing` and `k5.sine@out`), `budget.json` (`deciding` of the 15 class B IN+
  rows), the report ("at wiper 1.0 K5 … a 2.43 V residual", and K5 in the per-node table).
- **Defect.** In all 40 class B IN+ records at wiper 1.0 with IN- at 50 pF, and in 16 IN- records at high stray,
  the output swings beyond ±11 V (to ±11.97 V at the pair corner). The 10 V-peak sine is amplified to about 12.9 V
  by the gain change that 50 pF on IN- causes, and the output clips. In 50 of the 56 records the harmonic-fit
  residual (up to 2.43 V) fails K5, and it is the clipping. The brief requires such an amplitude to be reduced
  until the output stays 1 V inside the rails, with the value recorded. It was not.
- **Required correction.** Mark K5 `NOT EVALUATED: output clipped` in those records, or re-measure at a reduced
  amplitude under a new admission. Remove K5 from the deciding lists and from the report text for these rows. No
  label changes: the same corners fail K3 (10.3 dB) and K4 (164 % to 195 %) at zero stray.

### 4. The class G account misstates the tightest-step results and quotes a figure from a rejected operating point

- **Files.** The report (stop section, class G section, decision 1), `budget.json` (class G label).
- **Defects.**
  - "From 5 pF upward, the tightest loop step of every class G point ran into the 600 s deck timeout" is wrong.
    Of the 18 recorded points, 7 timed out (5, 6, 12, 20, 24, 32 and 40 pF), 5 did not converge and 6 fell back
    to "Transient op".
  - The 9 interrupted invocations were further 600 s timeouts of points that were then run again whole. Class G
    tightest-step timeouts therefore took about 9 600 s of the 18 415 s counted. The report does not say so.
  - "1.7 mV" comes from rejected operating points, which B2.6 keeps out of every output, "not as a note". I
    confirm the figure (1.706 mV at both operating points of deck `921b6372…`, every other node within 1 µV).
  - `ota_nc8` is the unconnected LM13700 pin 8 node. The report does not say that the rejection rests on a node
    with no cell element on it.
  - The label reason reads "sweep incomplete" and omits that no run point had an accepted operating point.
- **Required correction.** Correct the counts, add the timeout cost, name `ota_nc8` as an unconnected pin node,
  mark the 1.7 mV as a diagnostic that is not a study result (or ask the design authority to admit it), and give
  both reasons in the label.

### 5. The class D row is non-monotonic and the report does not say so

- **Files.** `budget.json` (`/W1/C629978_W_SENSE`, `non_monotonic` true at both corners), the report.
- **Defect.** At wiper 0.5 the row fails K4 at 0 and 1 pF, passes from 2 to 64 pF and fails K7 from 80 pF. At
  wiper 1.0 it fails K4 from 0 to 8 pF and passes from 10 to 100 pF. Ruling 3 requires a pass above a fail to be
  reported as non-monotonic. The label (lowest fail decides) is correct.
- **Required correction.** Report the row as non-monotonic, with the values above.

### 6. The per-IC section does not give the brief's binding rows

- **Files.** The report ("U8409's rows fail … U5210's four rows stay blocked").
- **Defect.** The section lists the nets on each IC's own pins. The brief's binding rows are the nodes of the S12
  blockers, and the report must repeat them per IC. Missing: for U8409, `/M4A/C1c45d6_W_SENSE`,
  `/A02/Cc045d2_W_SENSE`, `/M4B/Ccb7527_FB`, `/M4B/C24ce01_SUM`, `/M4B/C24ce01_W_SENSE` and
  `/M4B/C1c45d6_W_SENSE`; for U5210, `/M4A/C24ce01_W_SENSE`; and all of U5110 and U5209. The report also does not
  flag that U5210's own four nodes are class F and blocked, while the brief expected U5210 to depend on classes A,
  B and C only.
- **Required correction.** Add the binding rows per IC for all four ICs with their labels, and state the U5210
  contradiction for the design authority.

### 7. P9 reports three of nine class E decks under a heading that claims agreement

- **Files.** The report ("P9 agrees with the paper estimate within 1.8°"), `budget.json` (`P9_cross_check`, 27 rows).
- **Defect.** The three plain 100 kΩ / 100 kΩ decks differ from the estimate by 0.86° to 1.76°. The other six
  class E decks differ by −3.4° to −15.3° (for example `/M4B/TARGET_SUM`, 16.09° against 31.4°). The brief asks for
  "the class E result" beside the estimate.
- **Required correction.** Report all nine decks, and say that the estimate describes only the plain cell.

### 8. Three NOT RUN items lack a reason or are missing

- **Files.** The report.
- **Defect.** The class F diagnostic is NOT RUN beside the sentence "Classes F and I are blocked", which is not
  its reason: it needs no diode model and was pending when the ceiling was reached. The Ruling 6 output pair for
  `/W1/OUTPUT_FB` at 12 pF is NOT RUN and is not mentioned. The fourth-run section omits the brief's standing list
  (KiCad DRC and ERC, c6 and checks 2 to 4, bench stability, temperature and tolerance corners).
- **Required correction.** Add each item as `NOT RUN` with its reason.

### 9. The planned what-if arm is 320 points against the brief's "up to 140"

- **Files.** `budget.py` (`dependent_phases`), the report ("All 320 what-if points").
- **Defect.** The brief allows one 10 pF variant per failing class, 20 values, up to 140 points. The driver plans
  one per topology and, in class B, per swept node and pair value. None ran, so no result is affected.
- **Required correction.** State the difference in the report. A continuation needs a design-authority ruling on
  the what-if plan before admission.

### 10. P7's 50.97 % overshoot is read from a window that never settles

- **Files.** `checkpoints/controls.json`, `result.json` (`controls.P7`), the report (P7 row, withdrawn-figures section).
- **Defect.** In deck `acd3968e…` the last tenth of the K4 window still rings by 79 mV on a 100 mV step, so the
  "final" value is −139 mV and the percentage is not an overshoot. The first peak is −193 mV, about 93 %. `overshoot()`
  has no settled-window test. The K4 failure, and so P7, is not in doubt.
- **Required correction.** Quote the P7 result as "fails K4, window not settled", not as 50.97 %. Add a
  settled-window test to `overshoot()` before any further run, so that an unsettled window is NOT EVALUATED.

### 11. Three claims have no retained evidence, and one edit is undescribed

- **Files.** The report; `checkpoints/discarded-controls-run1.json`; `budget.py`.
- **Defects.**
  - "The captured output of all five calls holds none": the output of the unfiltered `docker kill` calls is not retained.
  - "Every figure was equal in both runs": the first controls run's figures are not retained.
  - The file time of `budget.py` is 00:31:33 UTC on 28 November, between slices 9 and 10. The last fix the report
    describes (sweep order) took effect before slice 6 at 23:09. The later edit is not described. `--check` shows
    that it changed no recorded deck, and `runner.py` (the measurements) is unchanged since 22:24:55.
  - 16 605 s + 1 810 s is 18 415 s, not 18 414 s.
- **Required correction.** Mark the two claims as attested by the executor only, describe every study-file edit
  made after the first sweep slice with the slice at which it took effect, and correct the sum.
