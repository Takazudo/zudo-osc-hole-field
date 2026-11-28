# MC04-S14 disposition: the capacitor cures the weak loops in the model but frees no IC, and the budget route should close

2026-11-28. DRAFT, not committed. Issue #367 (MC-04 paper gate). Design authority under DS-03 (Fable design agent at
high effort, model `claude-fable-5-2`). Subject: the S14 study at `8734ddc5` under brief Revision 3
(`c6904428…0ae9ec2`): report `mc04-s14-report-20261128.md` (SHA-256 `ff487e60…d23a59`), result review
`reviews/mc04-s14-result-review-20261128.md` (`18b2c02f…35371b`, ACCEPT WITH CORRECTIONS, 1 blocking and 11
non-blocking, all applied), and `whatif.json` (`9ba23251…9030e7`), `rescore.json` (`92bc0f67…b688c7`) and
`result.json` (`80fddefb…f80b8f`) in `scripts/stack/studies/mc04_s14_feedback_capacitor/`.

This disposition changes no file but itself. Nothing is adopted and no capacitor is fitted. Every figure below is
MODEL EVIDENCE ONLY from typical-only vendor and behavioural models at 27 °C on ideal rails. Nothing is measured.
Every board and schematic stays an unvalidated draft, check 5 stays NEEDS_DESIGN and #318 stays HOLD.

## Ruling on the result: accepted as a completed study

- The run finished inside every cap and ceiling (457 of 900 invocations; 989 s and 510 s against 6 300 s and
  2 700 s). Controls P1 to P10 passed. The one STOP 1 was a path typo in the study before any deck.
- The review's stricter reading of a failing output pair (finding 1, reading 16) is accepted: a row whose Ruling 6
  output pair fails at `C_lim` has no usable limit. The brief should have said so; the gap was this design
  authority's.
- The S7 result stands: **no IC is unblocked.**

## Interpretation (model evidence only)

### The 10 pF capacitor does what a feedback capacitor should, and costs what the arithmetic said

- The plain 100 kΩ / 100 kΩ summers go from 33° (S13) to 70° of phase margin at zero stray and keep 62° at 100 pF.
  The other class E cells reach 66° to 67°. H-REF9 goes from 12° to 17° up to 74° to 76°.
- The cost at 20 kHz against the specification cell is −0.08 dB and −7.15° on the class E cells and −4.31° on
  class G, and the −3 dB bandwidth falls from about 1.06 MHz to about 150 kHz. The brief predicted −7.2° and −3.6°
  to −4.3° before the run.
- On the control summers (E-control) a 7° shift at 20 kHz has no obvious consequence. On the two audio cells
  (`FOLDER_SUM`, `DRIVE_INV_SUM`) it is beyond the 2° that K7 allows a move to add. Whether that is acceptable is
  the owner's question, and only if a capacitor is ever proposed.

### What the rows say, and what decides each

| Group | Result | What decides it |
| --- | --- | --- |
| Three plain E-control sets | BUDGET 16 pF against 8.3 to 10.6 pF on paper, conditional on the capacitor | K9 (noise +1 dB) at 50 pF. K1 to K5 alone would give 50 pF |
| `TARGET_SUM` | no headroom: 8 pF against 18.22 pF | K9 at 24 pF |
| `COMMAND_INVERT_SUM`, `DRIVE_INV_SUM`, `FOLDER_SUM` | provisional 16, 50 and 50 pF | the two brackets differ by more than 2°, or a part identity is open |
| H-REF9 | no headroom | K4 from 8 pF and K3 from 12 pF, with 58° to 76° of phase margin |
| Class G specification cell | fails at zero stray: 3.65° and 3.85°, 22 dB of peaking | K1 to K4 |
| Class G with the capacitor | no usable limit | 63° at zero stray, but the output pair reads 44.1° with 100 pF on the output |
| Class A re-score | no headroom: 2 pF against 4.3 to 16.3 pF | the relative K4 form is used up at 5 pF |
| Class C and D re-score | one provisional 40 pF row, one no-headroom row, nine with no usable limit | the output pair reads 38.7° to 38.9° with 100 pF on the output |

Four things follow.

1. **The loops themselves are no longer the binding question.** With the capacitor every non-G cell has 53° or more
   at every stray value to 100 pF. What binds is noise (K9), response shape (K3, K4, K7) and the 100 pF output
   bracket.
2. **Most of what binds is a criterion or an assumption of this design authority, not a stability limit.**
   - K9's +1 dB, K7's 2°, the relative K4 margin of 5 points and the 100 pF output bracket of Ruling 6 are all
     rulings. Under K1 to K5 alone many rows would read 50 pF.
   - For H-REF9 the K4 stimulus is a 100 mV step in series with REF5. A DC reference sees no such step. The
     failure is real for that stimulus and says little about the cell in use. The stimulus was ruled in the S13
     brief; it is not re-scored here.
   - Loosening these after two studies, until some row passes, would be choosing the criterion by the result.
     That is not offered.
3. **Two findings do not depend on any criterion and deserve the owner's attention as design items, separate from
   placement.**
   - Eleven rows (E-control 6, E-audio 3, H-REF9 2) have 12° to 33° of phase margin with no stray and no capacitor
     (S13), and the capacitor cures that in the model.
   - The class G pre-gain stage has under 4° in the model. The report states that the retained LM13700 model
     overstates bandwidth and phase margin, so the real stage is not expected to be better. That model is the
     weakest in the study; the figure is a warning, not a measurement.
4. **The sensitive nodes are sensitive.** Class A uses its whole relative allowance by 5 pF. Class B moves 0.36° per
   pF at 20 kHz (S14 brief). The amplifier outputs lose margin under 100 pF. The DS-150 protected-part rule was
   written on that expectation, and two studies support it rather than relax it.

### Limits of all of this

Typical-only models; one temperature; ideal rails and passives; generic single-channel cores; the capacitor ideal
and its tolerance not swept; the class G trim 0 corners, the AGND-bracket sweeps and classes B, F and I NOT RUN;
`C_paper` from four assumed geometry terms. No bench measurement exists for any cell.

## What this means for the four unplaced ICs

| IC | Why it stays blocked | What simulation cannot supply |
| --- | --- | --- |
| U8409 | all 12 rows block: 7 class B, 3 class A, 2 class C | class B is limited by phase sensitivity (K7), which no capacitor moves; class A has no room |
| U5210 | all 17 rows block: U8409's rows, one more class B row and four class F rows | the same, and the BAS16GW-QX vendor model |
| U5209 | class A, class F, class C and class G rows block; three rows are conditional on the capacitor | the BAS16GW-QX model, and a credible class G result |
| U5110 | class A (2 pF against 10.45 pF), class F and class G rows block; one row is conditional | the same |

- DS-161 opened this route to find how far a protected part may move. The answer after S13 and S14 is that no
  binding row has room above its paper estimate under the criteria as ruled. A budgeted move, which adds
  capacitance to a node, is therefore not available for any of the four ICs.
- This does not say the ICs cannot be placed. It says they cannot be placed by lengthening a protected node on the
  strength of this evidence.

## Further simulation is not worth another round, and the budget route should close

- A third study could change a criterion, a capacitor value or a bracket. Each is a choice made after seeing two
  results, and at best it yields more conditional rows.
- Three of the four ICs would stay blocked whatever it found: U8409 and U5210 by class B, U5209 and U5210 by the
  missing diode model.
- The open questions that matter now are not simulation questions: whether the weak loops are real (a bench),
  whether the class G model can be trusted (a better model or a bench), and whether the owner wants a compensation
  change (a design decision).

**Ruling:** no further capacitance-budget study is admitted by the design authority under the present rules. The
route reopens only by an owner decision. S13 and S14 stay on record as model evidence.

## What is the owner's to decide

- Whether the four ICs are pursued by another route, and which.
- Any change to the DS-150 protected-part rule, including a no-growth rule.
- Any capacitor on any cell. It would be a specification change with its own evidence, BOM entry and review, and it
  brings the 20 kHz cost above.
- Any criterion looser than those ruled, and storing the BAS16GW-QX and BCM847BS,115 models.

## Owner options

All four stay inside the project rules: no purchase, no physical action, and any part adoption or circuit change
is a separate owner decision and a separate change.

| # | Label | Consequence |
| --- | --- | --- |
| 1 | Close route; try no-growth moves | Budget studies end. A reviewed geometric rule lets a protected part move only if its node gets no longer than on paper, then one search. May place some ICs; evidence is geometric only. |
| 2 | Close route; draft capacitor change | Budget studies end. A proposal to add 10 pF to the nine weak summer cells is drafted for your approval. Better loop margin in the model, 7° at 20 kHz; it places no IC. |
| 3 | Close route; leave ICs open | Budget studies end and nothing replaces them now. The paper gate fails for these ICs, earlier alternatives return, and the prototype order review stays on hold. |
| 4 | Run one more simulation round | A third study with other tests or another capacitor value. At best more conditional rows; U8409, U5209 and U5210 stay blocked by class B and the missing diode model. |

**Recommended: option 1.** Reason: two studies found no node with room to grow, so the one move rule this evidence
supports is a rule that adds nothing to any node; it is also the smallest next step.

What option 1 is and is not:

- It is option 2 of the S12 disposition ("Allow moves that keep nodes short"), now with evidence for why growth is
  not offered. It changes the DS-150 rule, which is why it is the owner's.
- The design authority would write the no-growth test as a rule with its own controls (pad extent, pad-to-pin
  distance and face set no worse than paper, for every protected node touched), have it reviewed, and then brief
  one search. Nothing is adopted without a generator task and its review.
- It is a geometric proxy. It shows a move makes no node longer than the paper design. It does not show that the
  paper design is stable; S13 and S14 say that several cells are weak on paper already.
- It may find no scene. S12 showed the blockers are protected neighbours; a no-growth move must still find a legal
  slot for each.
- U1415 stays on its own track, as before.

Options 1 and 2 do not exclude each other. If the owner picks 1, the weak-loop finding stays an open design item
(DS-185 below) that the owner can take up at any time. If the owner picks 2, the placement question stays open.

## Proposed decision-log rows

| ID | Date (UTC) | Decision | Decided by | Basis | Reverse by |
| --- | --- | --- | --- | --- | --- |
| DS-183 | 2026-11-28 | MC04-S14 (`8734ddc5`, brief Revision 3) accepted as a completed study with all twelve findings of its result review applied, the stricter output-pair reading included: a row whose Ruling 6 output pair fails at `C_lim` has no usable limit. With the 10 pF what-if three E-control sets read BUDGET 16 pF, `TARGET_SUM`, H-REF9 and class A have no headroom, class G fails at zero stray (3.65° and 3.85°) and has no usable what-if limit, and nine class C and D rows have no usable limit. No IC is unblocked. Model evidence only; nothing adopted | Design authority (DS-03: Fable agent at high effort), owner notified | `mc04-s14-disposition-20261128.md`; `mc04-s14-report-20261128.md`; `reviews/mc04-s14-result-review-20261128.md` | Design-authority ruling |
| DS-184 | 2026-11-28 | S14 interpretation: with the capacitor every non-G loop has at least 53° to 100 pF, at a cost of −0.08 dB and −7.15° at 20 kHz on class E; what then binds is K9, K7, K3 and K4 and the 100 pF output bracket, which are rulings and assumptions of the briefs, not stability limits. They are not loosened after the result. No binding row of U5110, U8409, U5209 or U5210 has room above its paper estimate, so a move that adds capacitance to a protected node is not supported for any of them | Design authority (DS-03: Fable agent at high effort), owner notified | `mc04-s14-disposition-20261128.md`, "Interpretation" | Design-authority ruling, or bench evidence |
| DS-185 | 2026-11-28 | Open design items from S13 and S14, separate from placement and flagged to the owner: (a) eleven rows (E-control 6, E-audio 3, H-REF9 2) have 12° to 33° of phase margin with no stray in the model, cured in the model by 10 pF of feedback; (b) the class G pre-gain stage reads under 4° with a behavioural LM13700 model that is the weakest in the study. Neither is a measured defect. No part is adopted and no specification is changed | Design authority (DS-03: Fable agent at high effort), owner notified | `mc04-s14-disposition-20261128.md`, "Interpretation" item 3; DS-176 | Owner decision on a specification change; bench evidence |
| DS-186 | 2026-11-28 | No further capacitance-budget study is admitted under the present rules. The route opened by DS-161 has produced no budget that allows a move after S13 and S14, and a third round could change only a criterion, a capacitor value or a bracket after the result. The route reopens only by an owner decision | Design authority (DS-03: Fable agent at high effort), owner notified | `mc04-s14-disposition-20261128.md`, "Further simulation" | Owner message |
| DS-187 | 2026-11-28 | Owner choice pending on the four unplaced ICs after the budget route: (1) close the route and try no-growth moves under a reviewed geometric rule (recommended), (2) close it and draft a capacitor change proposal for the nine weak summer cells, (3) close it and leave the ICs open, or (4) run one more simulation round. No part is adopted and no rule is changed until the owner answers | Owner (pending) | `mc04-s14-disposition-20261128.md`, "Owner options" | Owner message |

## Not established

- Any behaviour of real hardware.
- That the weak loops ring or oscillate on a board, or that 10 pF is the right value for any cell.
- The class G result beyond "the model reads under 4°": the trim 0 corners are NOT RUN and the model is weak.
- That a no-growth search finds a scene for any of the four ICs.
- Any class B, F or I limit, and any slot-level effect on U5110.
