# MC04-S13 disposition: no budget exists; 11 rows show a weak loop in the model, 27 zero-stray failures come from the study's own tests, and the next step is the owner's

2026-11-28. DRAFT, not committed. Issue #367 (MC-04 paper gate). Design authority under DS-03 (Fable design agent at
high effort, model `claude-fable-5-2`). Subject: the fourth S13 run at `23d6fb49` under brief Revision 8
(`360eb262…225bf4`), its report `mc04-s13-report-20261127.md`, `budget.json`, `result.json` and `results.jsonl` in
`scripts/stack/studies/mc04_s13_node_cap_budget/`, and the independent result review
`reviews/mc04-s13-result-review-20261127.md` (SHA-256 `2264925b…732c65`, ACCEPT WITH CORRECTIONS, 1 blocking and
10 non-blocking). The executor is applying the review's corrections to the report and `budget.json`; this text
uses the corrected counts and cites no hash of files that are still changing.

This disposition changes no file but itself. Nothing is adopted. Every figure below is MODEL EVIDENCE ONLY from
typical-only vendor macro-models at 27 °C on ideal rails, with ideal passives. Every board and schematic stays an
unvalidated draft, check 5 stays NEEDS_DESIGN and #318 stays HOLD.

## Ruling on the result: accepted as a stopped study with no budget, with every review finding accepted

The stop at the 5 h ceiling (STOP 3) was correct. Classes A to E and H are complete; class G, the what-if arm, the
class F diagnostic and the Ruling 6 output pair are NOT RUN. No node has a `C_lim` that may be used for a move.

| Label | Rows | Classes |
| --- | --- | --- |
| FAILS AT ZERO STRAY | 38 | A 11, B 15, D 1, E-control 6, E-audio 3, H-REF9 2 |
| NO HEADROOM AT PAPER | 9 | B 8 (IN− rows, `C_lim` 2 pF), H-output 1 (`C_lim` 12 pF) |
| BLOCKED, missing vendor model | 6 | F 5 (BAS16GW-QX), I 1 (BCM847BS,115) |
| NOT EVALUATED | 11 | C 10 (K5 window, review finding 1), G 1 |

- All eleven review findings are accepted. None is disputed.
- The first draft of this disposition counted the ten class C rows under FAILS AT ZERO STRAY with a note that the
  K5 reading was an artefact. The review is right that the label itself was wrong; the rows are NOT EVALUATED.
- DS-161 asked whether simulation could give budgets that allow moves. On this evidence it cannot, with the
  circuits as specified and the tests as briefed.

## 1. `ota_nc8` is a floating no-connect pin and is excluded from the 50 µV test; a class G continuation is not worth an admission now

- **What the node is.** `wavefolder.py` gives LM13700 pin 8 no net (`'8': None`) and ties pin 7 to AGND. The deck
  follows that: `ota_nc8` is the unloaded output of the model's Darlington buffer. Nothing in the circuit sets its
  voltage. It moves 1.706 mV between tolerance steps while every other node stays within 1 µV (review finding 4).
- **Ruling.** B2.5 names "every external node of the cell". A node that carries one device pin and no other
  element, where the specification leaves that pin unconnected, is not a node of the cell. Such nodes are excluded
  from the 50 µV comparison and from the C2.5 group agreement. Each is listed in the record. The 50 µV limit is not
  widened for any other node, the OTA's connected pins included.
- **Ruling on the 1.7 mV figure.** B2.6 keeps figures from a rejected operating point out of every output. It was
  written for metrics of the circuit. The deviation that causes a rejection is a diagnostic of the acceptance test
  itself and may be recorded, labelled "diagnostic, not a study result", with the node named. It is admitted in
  that form.
- **No class G admission now.** Three reasons:
  1. Cost. Of the 18 points that ran, the tightest loop step timed out at 600 s in 7, did not converge in 5 and
     fell back to "Transient op" in 6. With the 9 interrupted invocations, class G timeouts took about 9 600 s of
     the 18 415 s counted. The 62 remaining points would need many hours.
  2. Value. Class G is one row. It serves U5110 and U5209, whose routes also cross class F rows (blocked) and
     class E rows (failing at zero stray). A class G budget would unblock neither IC.
  3. Likely outcome. The amplifier in this cell is an inverting stage with 49.9 kΩ feedback and no feedback
     capacitor, the same weakness as class E. This is an expectation, not a result.
- Class G goes into whatever study the owner chooses next, with the exclusion above and a bounded ladder.

## 2. The what-if arm is deferred, not admitted as planned and not dropped

- The driver planned 320 what-if points. Ruling 7 allows one 10 pF variant per failing class, at most 140 points
  (review finding 9). The 320-point plan was never admitted and is not admitted now.
- For classes A and D the zero-stray failure comes from the K4 test (section 3), and class C is not evaluated. A
  what-if there would answer a question nobody asked.
- For classes E-control, E-audio, H-REF9 and the class B IN− rows a feedback capacitor is the standard remedy, and
  the what-if is the evidence the owner would need before deciding on one.
- A continuation under Revision 8 would repeat the same labels, because the tests are unchanged.

So the arm is deferred into a new reviewed brief, limited to the classes where it is informative and counted per
class as Ruling 7 says. Fitting a capacitor stays the owner's decision; no output of S13 proposes it as decided.

## 3. Rulings the review asked for

All four take effect only through a reviewed brief revision or a new brief. None re-scores an S13 row by itself.

### K5 window: the late window starts at least 12 time constants after the edge, and both wipers are measured alike

- K5 tests sustained oscillation. A monotonic settling tail is not oscillation.
- For a cell with its own stated filter (class C), the late window starts no earlier than 12 zero-stray time
  constants of that corner after the edge. Reason: after a 10 V step the tail is then below 0.1 mV, a tenth of
  the limit. Every corner uses the same multiple, so wiper 0.5 and wiper 1.0 are measured alike.
- The step residual is the peak-to-peak after removing the mean only. No polynomial detrend. For the sine, a fit of
  the fundamental and its harmonics is allowed and must be named in the brief with its order.
- The quadratic detrend and the 10-harmonic fit of the fourth run were the executor's readings. They were
  reasonable and should have been listed; the gap they filled was this brief's, which defined no window.
- The cached class C waveforms hold 14 time constants, so a window from 12 exists in them. A re-measurement from
  the cache is possible without a deck. It is a re-score and needs the new brief, a review and an admission. The
  reviewer's own figure (55 µV from 12 time constants) is a recomputation, not a study result.

### A pass inside the resolution is a tie, and a tie is a fail

- The brief already rules "a tie at 100 pF counts as a fail". This ruling defines the tie: a relative test (K6,
  K7, K8, K9) whose margin to its limit is smaller than the recorded resolution of that measurement is a tie.
- Class C at 100 pF passes K6 and K8 by 0.001 % at a resolution of 0.05 % (review finding 2). That is a tie and so
  a fail at 100 pF. By Ruling 3 a class C corner limit can then be at most 40 pF, never 50 pF.
- No class C limit is quoted from S13 in any case: the rows are NOT EVALUATED.

### A clipped output makes K5 not evaluated; the amplitude is reduced per point

- In 56 class B records the sine output passes ±11 V, and 50 of them fail K5 on the clipping alone (review
  finding 3). The brief's rail rule (keep the output 1 V inside the rails, record the value) was written for the
  E-control step and not applied to the class B sine. That was a gap in the stimulus table.
- Ruling: in those records K5 is `NOT EVALUATED: output clipped`. It is neither a fail nor a pass, and K5 leaves
  their deciding lists. No label changes, because the same corners fail K3 and K4 at zero stray.
- For any later run: the large-signal amplitude is set per point from that point's own small-signal gain at the
  stimulus frequency, so that the output peak stays 1 V inside each rail, and the value is recorded. A record whose
  swing still enters that 1 V band is `NOT EVALUATED: output clipped`.
- No re-measurement is admitted under S13.

### U5210 cannot be budgeted without the diode model; the brief's sentence was incomplete

- The brief said "U8409 and U5210 depend on classes A, B and C only". That was true of the protected neighbours
  that block their moves. It left out that U5210's own four input nets are class F, which is blocked (review
  finding 6).
- Ruling: an IC is unblocked only when the rows of its blocker route and the rows on its own pins all have a
  budget. For U5210 that needs the BAS16GW-QX vendor model. The same holds for U5209 through R5253.
- Consequence: of the four ICs, only U8409 depends on classes with models (A, B, C). U5110 depends on A, E and G
  and, for 6 of 66 slots, on a class F row.

## 4. Interpretation: only the first group points at the circuits

### 11 rows show a weak loop with no stray; the first-order estimate confirms it for the plain cell only

E-control (6), E-audio (3) and H-REF9 (2): phase margin 12° to 33° at zero stray, with K1, K3 and K4 failing
together.

- The cause is the same in each: a high feedback resistance (100 kΩ / 100 kΩ, or 40 kΩ / 50 kΩ at REF9) against the
  amplifier's own input capacitance, with no feedback capacitor.
- The brief stated this before the run ("Expected outcome": 31.4° from `f2_loop_estimate.py`).
- **Correction to the first draft.** It said the vendor model and the estimate agree within 1.8°. That holds for
  the three plain 100 kΩ / 100 kΩ decks only. The other six class E decks are 3.4° to 15.3° below the estimate (for
  example `/M4B/TARGET_SUM`, 16.09° against 31.4°), because the estimate describes only the plain cell (review
  finding 7). For those six decks and for H-REF9 the low margin rests on the vendor model alone.
- No placement can fix it: the rows fail with zero added capacitance.
- **Limits.** These are typical-only models. Nothing is measured. Whether a real board rings or oscillates is not
  established; the cells are `PROPOSAL`, `NEEDS BENCH`. It is correct to call this an indicated weakness of the
  paper circuits, and not correct to call it a proven defect.

### 27 zero-stray failures come from the study's tests, which were this design authority's rulings

| Class | Rows | What fails at 0 pF | Why it is not evidence of a circuit defect |
| --- | --- | --- | --- |
| A, no harness | 11 (same rows as below) | K4 only: 25.6 % to 25.8 % against 25 % | K1 passes at 53.5°, K2 passes, K3 passes at 2.1 dB. K4 was ruled as the time-domain twin of K1 on a two-pole assumption (45° ↔ 23 %). The vendor model is not two-pole: 53.5° gives 25.6 % |
| A, 1 nF harness | 11 | K3 3.8 to 4.1 dB, K4 38 % to 40 % | phase margin stays 53.3°. The peak near 400 kHz is the cell's response to its own stated worst harness, independent of stray |
| D | 1 | K4 only: 26.3 % to 26.5 % | K1 passes at 45.2° to 47.4°, K3 passes at 2.5 dB. The row is non-monotonic (review finding 5): it fails K4 at 0 and 1 pF and passes from 2 pF at wiper 0.5, and fails to 8 pF and passes from 10 pF at wiper 1.0. The overshoot sits on the limit. The row is also truly close to the K1 limit |
| B, IN+ (`W_SENSE`) | 15 | K3 (10.3 dB), K4 (164 % to 195 %) only at the pair corner | the pair corner puts 50 pF on the IN− node, 25 times that node's own 2 pF limit. With IN− at 0 pF these rows reach 32 pF and 50 pF. The corner rule of the brief produced the label |

- The K4 limit and the pair-corner rule are in the brief. They were reviewed, and they were still wrong for these
  cells. The executor applied them as written.
- **These rows are not cleared.** Changing a criterion after seeing the result is the relaxation the brief
  forbids. The labels stand in the S13 record. A corrected test needs a new reviewed brief before any row is
  scored again, and a re-score means exactly that.
- For the class A harness corner the peaking is real in the model. It belongs to the cell's own envelope, which
  the retained input-buffer receipt covers, and S13 adds no stray-related finding to it.

### 10 class C rows are not evaluated

Every recorded class C value passes K1 to K4, and K5 at wiper 0.5. K5 at wiper 1.0 measured the filter tail. Under
the rulings of section 3 the rows could be scored from the cached waveforms, with a limit of at most 40 pF. That
has not been done and is not a result. The Ruling 6 output pair and the `IDENTITY OPEN` part on each net also
stand before any class C limit.

### 9 rows have a limit below their paper estimate, for two different reasons

- **Class B IN− (`SUM`), 8 rows, `C_lim` 2 pF against 5.9 to 13.9 pF on paper.** The loop is not the problem: phase
  margin is 59° to 71° up to 100 pF. Capacitance on the summing node adds a zero to the non-inverting (remote)
  path. K7 (2° at 20 kHz) trips at 6 pF, K4 at 8 to 12 pF, K3 at 12 to 16 pF. The 2 pF figure is set by K7, a limit
  ruled as "no audible change"; 2° at 20 kHz is a strict reading of that. Above about 12 pF the peaking is real in
  the model, and one paper estimate (13.85 pF) is already there.
- **H-output, 1 row, `C_lim` 12 pF against 35.73 pF on paper.** The row passes everything to 25 pF and fails K4
  and K7 from 32 pF. The paper pose already carries more than the limit. This is a finding for placement: that node
  should become shorter, not longer. Its Ruling 6 output pair is NOT RUN.

### What is model evidence only

Everything in this section: every phase margin, every overshoot, the class B zero, and the reading of the class C
waveform. `C_paper` rests on four assumed geometry terms (0.20 pF/mm, route factor 1.5, 0.5 pF per via, 0.3 pF per
pad). P7's 50.97 % is not an overshoot figure (review finding 10); the control still fails K4.

## 5. Owner options

The route DS-161 opened has not produced a budget. Three ways forward stay inside the project rules: no purchase,
no physical action, and any new part remains the owner's decision. The review changes the facts behind the
options, not the options: U5209 and U5210 stay blocked under all three until the BAS16GW-QX model is stored.

| # | Label | Consequence |
| --- | --- | --- |
| 1 | Study feedback capacitors (S14) | New reviewed simulation: the existing 10 pF part on the E, REF9, G and B-SUM cells, corrected tests, re-score of A, C, D. No part adopted. At best it frees U8409 and U5110. |
| 2 | Re-score S13 data only | Reviewed corrected tests on the existing data, no new part studied. A, C and D may get budgets; the 11 weak-loop rows stay failed and all four ICs stay blocked. |
| 3 | Close the budget route | No more simulation. Protected parts stay where they are, the four ICs stay blocked, and placement returns to the other options of the S12 disposition. |

**Recommended: option 1.** Reason: 11 rows show weak loops with no stray, which needs a compensation study whatever
happens to the moves; it includes option 2's re-score and commits to no part.

What option 1 would and would not do:

- It is a new brief with its own independent review and admission. It simulates only.
- It shows what a 10 pF feedback capacitor does to each weak class in the model. Whether to fit one, and which
  value, stays the owner's decision afterwards. A fitted part would need its own specification change, BOM entry
  and evidence.
- It can free U8409 (classes A, B, C) and, except for the 6 slots behind a class F row, U5110. It cannot free
  U5209 or U5210. Those need the BAS16GW-QX model in `circuit-dev-resources`, and class I needs BCM847BS,115; that
  is a separate owner-side item under any option.
- It carries the lessons of S13: seeded operating points from the start, the no-connect exclusion, the four
  rulings of section 3, a settled-window test in the overshoot measurement (review finding 10), a what-if count
  per class, a bounded ladder for class G, class G not last, and time limits sized from the S13 timings.

Why option 2 is weaker than it looked in the first draft: with class B IN− still at 2 pF, a re-score alone cannot
free U8409, so it frees no IC.

## 6. Proposed decision-log rows

| ID | Date (UTC) | Decision | Decided by | Basis | Reverse by |
| --- | --- | --- | --- | --- | --- |
| DS-175 | 2026-11-28 | MC04-S13 fourth run stopped at the 5 h sweep ceiling (STOP 3, commit `23d6fb49`). Accepted as a stopped study with all eleven findings of the result review accepted: classes A to E and H complete; class G, the what-if arm, the class F diagnostic and the Ruling 6 output pair NOT RUN. No node has a budget: 38 rows FAIL AT ZERO STRAY, 9 are NO HEADROOM AT PAPER, 6 BLOCKED (5 BAS16GW-QX, 1 BCM847BS,115), 11 NOT EVALUATED (class C 10, class G 1). Model evidence only; nothing adopted | Design authority (DS-03: Fable agent at high effort), owner notified | `mc04-s13-disposition-20261127.md`; `reviews/mc04-s13-result-review-20261127.md` | Design-authority ruling |
| DS-176 | 2026-11-28 | S13 interpretation: 11 rows (E-control 6, E-audio 3, H-REF9 2) show an indicated loop weakness, phase margin 12° to 33° with no stray; the first-order estimate confirms it for the three plain 100 kΩ / 100 kΩ decks only, the rest rests on the vendor model. It is not a measured defect. 27 zero-stray failures (A 11, B IN+ 15, D 1) come from the brief's own K4 limit and pair-corner rule; their labels stand and are not cleared without a new reviewed brief | Design authority (DS-03: Fable agent at high effort), owner notified | `mc04-s13-disposition-20261127.md` section 4 | Design-authority ruling, or bench evidence |
| DS-177 | 2026-11-28 | A deck node that carries one device pin and no other element, where the specification leaves that pin unconnected (LM13700 pin 8, `ota_nc8`), is excluded from the 50 µV operating-point comparison and from the seed group agreement, and is listed in the record; the deviation that causes a rejection may be recorded as a diagnostic, not a study result. The 50 µV limit is unchanged for every other node. Effective only through a reviewed brief revision | Design authority (DS-03: Fable agent at high effort), owner notified | `mc04-s13-disposition-20261127.md` section 1; `wavefolder.py` line 88; review finding 4 | Design-authority ruling |
| DS-178 | 2026-11-28 | Test rulings from the S13 result review, effective only through a reviewed brief: (a) the K5 late window starts at least 12 zero-stray time constants after the edge, the same multiple at every corner, mean removed only; (b) a relative test passed by less than its recorded resolution is a tie and a tie is a fail, so no class C corner limit exceeds 40 pF; (c) a clipped output makes K5 NOT EVALUATED and the large-signal amplitude is set per point to stay 1 V inside the rails; (d) an IC is unblocked only when its blocker-route rows and the rows on its own pins all have a budget, so U5209 and U5210 need the BAS16GW-QX model | Design authority (DS-03: Fable agent at high effort), owner notified | `mc04-s13-disposition-20261127.md` section 3; review findings 1, 2, 3 and 6 | Design-authority ruling |
| DS-179 | 2026-11-28 | No class G continuation of S13 is admitted. The what-if arm is deferred, not dropped, and the driver's 320-point plan is not admitted (Ruling 7 allows at most 140). Both go into the next brief if the owner chooses one. S13 is closed as a study at `23d6fb49` plus the review's report corrections | Design authority (DS-03: Fable agent at high effort), owner notified | `mc04-s13-disposition-20261127.md` sections 1 and 2; review finding 9 | Design-authority ruling, or an owner message |
| DS-180 | 2026-11-28 | Owner choice pending on the capacitance-budget route: (1) a new reviewed simulation of the existing 10 pF feedback capacitor with corrected tests (recommended), (2) a re-score of the S13 data only, or (3) closing the route. No part is adopted under any option, and U5209 and U5210 stay blocked under all three until the BAS16GW-QX model is stored | Owner (pending) | `mc04-s13-disposition-20261127.md` section 5 | Owner message |

## Not established

- Any behaviour of real hardware. No bench measurement exists.
- That the 11 weak rows oscillate or ring on a board, or that 10 pF cures them: the what-if did not run.
- Any class C, G, F or I limit.
- That corrected tests would give budgets to classes A, C and D. The recorded data suggests it for class C up to
  40 pF; it is not scored.
- The review's own gaps stand: it ran no deck, no own census derivation and no own `C_paper` computation.
- Two executor claims are attested only (review finding 11): the output of the five unfiltered `docker kill` calls,
  and the equality of the two controls runs.
