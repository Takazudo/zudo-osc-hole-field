# MC04-S13 brief: vendor-model simulation that sets a stray-capacitance budget per protected node (DS-161), Revision 3

2026-11-27. Issue #367 (MC-04 paper gate). The owner's choice DS-161 (option 1 of
`mc04-s12-disposition-20261127.md`), briefed by the design authority under DS-03 (Fable design agent at high effort,
model `claude-fable-5-2`). Executor: one session in the Cloud container. Repository `zudo-osc-hole-field` at
`e15cf2dbf6173f86da7f5de07d6b93431375c5ce`.

**Kind:** study only. It produces model evidence and a budget table. It adopts nothing and edits no board, schematic,
spec, BOM, owner bundle, inventory, gate record, options file or generated file. Every board and schematic stays an
unvalidated draft, check 5 stays NEEDS_DESIGN and #318 stays HOLD. A budget from this study is model evidence only:
it is not a stability proof, not a hardware qualification and not an acceptance of any layout.

**State:** PLANNED, not admitted. DS-161 requires an independent review of this brief before the run. Revision 1
(SHA-256 `e31a537eb3934c6773e1b2863b705d53766abfdbe65ddbb89c942994eb05ea12`) was reviewed ACCEPT WITH CORRECTIONS
(`reviews/mc04-s13-brief-review-20261127.md`); Revision 2 (SHA-256
`7757906d2db2d9da73978ac4ca16c6b3e53a30034b20d99d7dbfc2560aedb68e`) applied all twelve and its delta re-review
returned ACCEPT WITH CORRECTIONS (one required, two wording). This Revision 3 applies those three (revision history
at the end). The reviewer asks for no further round if R1 is applied as worded; the manager confirms it by
inspection. The manager admits the run after the admission checks in "Run
bounds".

## What this study answers

For each protected node that an S12 blocker sits on: how much stray capacitance to AGND may the node carry before
its cell, simulated with the vendor model of its amplifier, breaks a stated criterion?

- The answer is one row per node: a limit in pF, the paper estimate, the headroom, and a label.
- The follow-on placement study (its own brief and review) may move a protected part only on a node whose row is a
  budget, and only inside it. Every other protected node keeps the DS-150 displacement stop.
- U1415 is not in this study (scope note near the end).
- **Do not expect four ICs from this run.** The first-order estimate already puts the summers and fold cells that
  have no feedback capacitor (classes E and F) below the 45° criterion at zero stray. Usable budgets are expected
  mainly for classes A to D and H, which serve U8409 and U5210. See "Expected outcome, stated before the run".

## Three model gaps are known before the run, and one blocks the fold cell

Checked on 2026-11-27 against the owner bundles, the repository and every branch of `Takazudo/circuit-dev-resources`
(read-only `gh api`; `main` is `f6099b67`).

| Part (inventory line, owner bundle) | Vendor SPICE model | State |
| --- | --- | --- |
| OPA4196IDR, TI, C2057385 (`line-op-audio`, `component-ti-opa4196idr`) | TI OPAx196 Final 1.5 (29AUG2022), SBOMAF9E. ZIP SHA-256 `9c264813a36536f743c166b6a101904b76ed08f049f2eeb127a438cc6e8ccdf5`, `OPAx196.LIB` `31142f5dbd71b758d887ee8a411692fc4c1309c8f47100af4ba5bed7e173c430` | AVAILABLE in `circuit-dev-resources` at `texas-instruments/opa4196/opa4196-pspice-model-sbomaf9e.zip`, commit `54c00fc8` on branch `claude/project-thread-iw3gai`. I downloaded the bytes and both hashes match. **Not on `main`** (the branch is 2 commits ahead), and the owner bundle has no source row for it |
| OPA4197IPWR, C2057327 (`line-op-precision`) and OPA4197IDR, C2058532 (`line-op-precision-d`) | TI OPAx197 Final 1.3 (23JUN2022), SBOMA34D. ZIP `9e55fcaa23d54cee025dda3fa9872b11c41c531f82e0802c2b93d51e943666e5`, `OPAx197.LIB` `fc5b020e63346e511bd808bf41c856b0150b000bcf8a41fe00eeececb1f422a5` | AVAILABLE as retained evidence: source rows `src-op-precision-vendor-model` and `src-op-precision-d-vendor-model`. Bytes are in `.circuit-cache/sources/opa197-model/` in this container and match. **Not stored in `circuit-dev-resources`** on any branch |
| LM13700M/NOPB, TI, C1346265 (`line-ota`, `component-ti-lm13700m-nopb`) | TI SNOM267, `design/spec/modules/spice/filter-model/LM13700.MOD`, SHA-256 `666df501773da5e65f7fd3b3c806b2c1ae7770784685dd8191a9df33b382f390` | AVAILABLE, committed with `source-receipt.json`. Its header warns that it overstates AC bandwidth and phase margin by more than twofold |
| BAS16GW-QX, Nexperia (`line-signal-diode`, `component-nexperia-bas16gw-qx`) | none retained; the bundle holds no capacitance fact either | **MISSING. Blocks the fold cell (class F)** |
| BCM847BS,115, Nexperia (`line-matched-npn`) | none retained | **MISSING. Blocks `/E2/RISE_EXPO_SUM` (class I)** |
| BAT54S,215, Nexperia (`line-clamp-diode`); TMUX6112PWR, TI (`line-env-switch-t`) | none retained | MISSING. Not blocking: see Ruling 6 |

Ruling on the gaps (design authority):

1. The OPAx196 file is used from commit `54c00fc8`, hash-checked. Merging that branch to `main`, storing the OPAx197
   ZIP in `circuit-dev-resources` and adding an OPAx196 source row to the owner bundle are evidence tasks for the
   manager. They are not part of this study and do not gate it.
2. A missing model is a blocker for its node. No generic or assumed diode or transistor model may produce a budget.
   The generic diode parameters in `sweep_input_buffer_vendor.py` and `run_wavefolder_spice.py` are not used here.
3. The BAS16GW-QX and BCM847BS,115 models are the owner's to download into `circuit-dev-resources`. Until then
   class F and class I rows read `BLOCKED: MISSING VENDOR MODEL`.
4. **Storing a model does not admit class F or class I.** This brief defines no sweep with a diode or a transistor
   pair in the deck. A later run of either class needs an addendum by the design authority and its own independent
   review (DS-161). The addendum must give:
   - the deck, with the clamp or the pair in it;
   - the bias points, including a conducting clamp, and the large-signal criteria for them;
   - the exact-identity check of the model: manufacturer, the complete MPN the file names, its revision and date,
     and why it is the model of BAS16GW-QX or BCM847BS,115 and not of a same-name family part;
   - the file's path and SHA-256 in `circuit-dev-resources` and the owner-bundle source row that cites it.

## Design-authority rulings made in this brief

Rulings under DS-03, owner notified. None changes a part, a value, a pose or a rule outside DS-161's scope.

### Ruling 1: the budget is a limit on total stray capacitance, and the allowance is what is left above paper

- `C_stray` is the lumped capacitance from the protected node to AGND that copper adds: traces, vias and pads. It
  excludes the amplifier's input capacitance (the vendor model carries it) and every fitted part.
- `C_lim` is the limit found by simulation. `C_paper` is the estimate at paper poses. The allowance of a node is
  `C_lim − C_paper`.
- Reason: a limit on the total is testable on a routed board later. An "added" figure alone would hide a node that
  is already too long at paper.
- Lumping to AGND is the conservative case for an inverting input. Capacitance to the cell's own output acts as
  feedback capacitance and is not credited.

### Ruling 2: the criteria, and why these numbers

The project has no accepted stability requirement for these cells. Every cell in `electrical-standard.json` is
`PROPOSAL`, `NEEDS BENCH`. The limits below are therefore rulings, tied to what the project already uses.

| # | Criterion | Limit | Applies to | Basis |
| --- | --- | --- | --- | --- |
| K1 | Phase margin of the loop gain (Middlebrook double injection, the MC04-S4 method) | ≥ 45° | every class | the project's draft criterion `PM_LIMIT_DEG = 45.0` in `mc04_s1b_indicator_loops/loops.py` (ASSUMED there, kept for consistency) |
| K2 | Gain margin | ≥ 10 dB, or no phase crossover below 100 MHz | every class | ruled: guards a second crossover that K1 alone misses |
| K3 | Closed-loop peaking above the low-frequency gain | ≤ 3 dB | every class | ruled: the peaking that goes with 45° in a two-pole loop is about 2.3 dB |
| K4 | Overshoot of a 100 mV small-signal output step (100 ns edges) | ≤ 25 % | every class | ruled: about 23 % goes with 45°. **Looser than the project's existing label**, see below |
| K5 | Sustained oscillation: late-window peak-to-peak after a ±5 V step and under a 10 V-peak 20 kHz sine | ≤ 1 mV | every class | the absolute 1 mV test of `input-buffer-vendor.json` |
| K6 | Settling of a 1 V output step to within 1 mV | ≤ 1 ms, absolute, for E-control and H-REF9. For class C: no more than 1 % longer than at `C_stray = 0` | control and reference classes C, E-control, H-REF9 | the "settle within 1 mV by 1 ms" wording of the `precision_output` cell note; the class C form is ruled below |
| K7 | Gain change at 20 kHz against `C_stray = 0` | ≤ 0.1 dB and ≤ 2° | audio classes A, B, D, E-audio, G, H-output | ruled: a move must not change the audible response |
| K8 | Wiper time constant against `C_stray = 0` | ≤ +1 % | class C | the 10 nF wiper filter and its "up to approximately 0.26 ms" note |
| K9 | Integrated output noise against `C_stray = 0` (20 Hz–20 kHz audio; 10 Hz–100 kHz control and reference) | ≤ +1 dB | every class | ruled: stray on an inverting input raises noise gain |

- K1 to K5 gate every row. K6 to K9 gate the classes named.
- **K4 is not the project's 10 % figure, and it does not replace it.** The `precision_output` cell note and
  `precision-output-vendor.json` use "≤ 10 % overshoot" for a ±5 V step at a jack output into a cable. That is a
  large-signal test of a compensated output cell and stays as it is. K4 is a 100 mV small-signal step on an
  internal node, used as the time-domain twin of K1: 45° corresponds to about 23 %, so a 10 % limit would silently
  demand about 60° and contradict K1. Where the two tests meet (a cell with a jack output), the 10 % label still
  applies and this study does not judge it.
- **K6 in class C is relative, because the absolute form fails by construction.** A `dc_control_source` node carries
  10 nF behind the wiper resistance and 1 kΩ. With the 100 kΩ pot at mid-travel the time constant is about 0.26 ms,
  and 1 mV of a 1 V step takes 6.9 time constants, about 1.8 ms, with no stray at all. That slowness is the cell's
  stated design ("Do not use for audio"), not an effect of a move. For class C the 1 mV settling time is therefore
  compared with its own value at `C_stray = 0`; K8 covers the filter itself.
- If `.noise` cannot run on a vendor model, K9 is `NOT RUN` with the reason and the row becomes `PROVISIONAL`.
- DC accuracy is not a capacitance term and is not tested. Leakage, hum pickup and coupling from a neighbour onto a
  longer high-impedance run are **not covered** by a capacitance budget; they stay open for the placement study.

### Stimulus and measured node of each criterion, per class

K1 and K2 are measured in the loop deck with all signal sources at 0 V AC. The loop is broken between the feedback
return and the inverting input, at the amplifier pin, with `C_stray` on the node side. K3 to K9 use the closed-loop
deck. "Out" is the amplifier output pin of the unit that owns the protected node. A cell not listed for a criterion
is `NOT APPLICABLE` for it, and the row says so.

| Class | Source node (ideal source, 0 Ω unless stated) | K3, K7, K9 (AC and noise) | K4 small step | K5 large step and sine | K6, K8 | Measured |
| --- | --- | --- | --- | --- | --- | --- |
| A | SIGNAL (IN+) | AC 1 V; K7 at REMOTE | ±50 mV at SIGNAL | ±5 V step; 10 V-peak 20 kHz sine | NOT APPLICABLE | DRIVE and REMOTE; the worse decides |
| B | two sources, BUFFERED_INPUT and REMOTE_INPUT, wiper as cornered. K3, K4, K7: each path driven alone with the other source at 0 V (note below). K5, K9: both driven together by one source | AC 1 V on the driven path, once per path | ±50 mV on the driven path, once per path | common drive: ±5 V step; 10 V-peak 20 kHz sine | NOT APPLICABLE | OUT; for K3, K4 and K7 the worse of the two paths decides |
| C | REF_HIGH stepped, REF_LOW at its specification value, wiper as cornered | AC 1 V at REF_HIGH; K7 NOT APPLICABLE | 100 mV step at REF_HIGH, and a 100 mV step injected at W_SENSE through 1 kΩ so that the amplifier is exercised past the filter | ±5 V step at REF_HIGH; sine NOT APPLICABLE | K6 relative: 1 V step at REF_HIGH. K8: time constant fitted on the same step | OUT |
| D | REMOTE_INPUT, wiper as cornered | AC 1 V | ±50 mV | ±5 V step; 10 V-peak 20 kHz sine | NOT APPLICABLE | OUT |
| E-audio | the 100 kΩ signal input of the summer (`PRE_GAIN` for `FOLDER_SUM`, `FOLDER_NEG` for `DRIVE_INV_SUM`); other inputs at 0 V | AC 1 V | ±50 mV | ±5 V step; 10 V-peak 20 kHz sine | NOT APPLICABLE | OUT |
| E-control | the first 100 kΩ input in specification order; other inputs at their DC specification value or 0 V | AC 1 V; K7 NOT APPLICABLE | ±50 mV | ±5 V step, or the largest step that keeps OUT 1 V inside the rails; sine NOT APPLICABLE | K6 absolute: 1 V output step | OUT |
| G | `IN_BUFFER` (the OTA signal input through its 100 kΩ and 200 Ω divider); `IABC` held by an ideal current source at each corner | AC 1 V at `IN_BUFFER` | step at `IN_BUFFER` sized for 100 mV at `PRE_GAIN` | ±5 V step and 5 V-peak 20 kHz sine at `IN_BUFFER` (the retained wavefolder decks use 5 V); K5 only | NOT APPLICABLE. A step on `IABC` is not run | `PRE_GAIN` |
| H-REF9 | `REF5` as an ideal 5 V source. No signal input exists, so the large disturbances are load currents at `REF9` | K3 from AC 1 V in series with `REF5`; K7 NOT APPLICABLE; K9 at `REF9` | 100 mV step in series with `REF5` (note below) | a 1 mA load step at `REF9` (0 to 1 mA and back, 1 µs edges); late-window ripple only; sine NOT APPLICABLE | K6: a separate 100 µA load step at `REF9` (0 to 100 µA and back, 1 µs edges); recovery to within 1 mV of the final value within 1 ms | `REF9` |
| H-output | `F4_OUT` (IN+) | AC 1 V sized for 1 V at `PRE_AC` | step sized for 100 mV at `PRE_AC` | ±0.6 V step and 1.2 V-peak 20 kHz sine at `F4_OUT` (gain 8 keeps `PRE_AC` inside the rails) | NOT APPLICABLE | `PRE_AC` |
| F diagnostic | as E-audio, source at the cell's 100 kΩ input | as E-audio | as E-audio | as E-audio | NOT APPLICABLE | `Fk_OUT` |

Note on class B: the cell computes `Vout = 2·Vwiper − Vbuffered_input`. With both inputs driven together and the
wiper at 0.5 the two paths cancel and the output is about zero, so a percentage overshoot, a peaking and a gain
change in dB are undefined there. For K3, K4 and K7 each path is therefore driven alone with the other source at
0 V: BUFFERED_INPUT alone (gain −1), and REMOTE_INPUT alone (gain 2 × wiper, so 1 at wiper 0.5 and 2 at wiper 1.0).
Both are run at every point and the worse result decides. K5 and K9 keep the common drive: they test for sustained
oscillation and output noise, which need no defined gain.

Note on H-REF9: a reference has no signal input, so the small step for K4 is a 100 mV step from a source in series
with `REF5`. It appears as 180 mV at `REF9`, and the 25 % limit applies to that step. K5 and K6 use **two separate
load steps in two separate transients**: 1 mA for K5 and 100 µA for K6. Neither is reused for the other criterion.

Time resolution of the relative tests (K6 in class C, and K8). Both compare a time with its own value at
`C_stray = 0` against a 1 % limit, so the measurement must resolve far less than 1 %:

- the maximum timestep of that transient is at most 1/1000 of the zero-stray time constant of the corner (10 ns at
  wiper 1.0, where the time constant is 10 µs and 1 % is 0.1 µs; about 0.26 µs at wiper 0.5 with the 100 kΩ pot);
- the 1 mV crossing and the time-constant fit are interpolated linearly between samples, and the same timestep,
  stop time and fit window are used at every `C_stray` value of a corner;
- the row records the timestep and the resulting resolution as a fraction of the zero-stray value. A resolution
  coarser than 0.1 % makes K6 and K8 `NOT EVALUATED` for that corner;
- 100 pF on 10 nF is a 1.0 % change, so K6 and K8 sit at their limit at the 100 pF point. A tie counts as a fail,
  and the report names the criterion that decided each class C row.

A large-signal amplitude that would drive the output into a rail for a reason unrelated to stability is reduced to
the largest value that keeps the output 1 V inside the rails, and the row records the value used.

### Ruling 3: a factor of two, and a 50 pF ceiling

- `C_lim` is the largest candidate limit `g` such that every tested value up to `2g` passes every gating criterion.
- Reason for the factor: the TI models are typical-only (`fact-op-audio-gbw` is 2.5 MHz typical with no minimum),
  the input capacitance is typical-only, and 0.20 pF/mm is an assumption.
- `C_lim` never exceeds 50 pF. Reason: 50 pF is the project's existing run limit (`LIMIT_PF = 50.0` in
  `mc04_s7_r4/buffer_runs.py`), and beyond it the uncovered terms above dominate.
- Candidate limits: 1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 25, 32, 40, 50 pF.
- Tested values: 0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 25, 32, 40, 50, 64, 80, 100 pF (20 points).
- No interpolation. A pass above a fail is reported as non-monotonic and the lowest fail decides.

### Ruling 4: how a budget in pF becomes a geometric allowance (input to the placement brief, re-reviewed there)

The pF figure is the authority. The millimetre figure is derived from it for the placement study. DS-161 gives that
study its own brief and review: this ruling is the proposed test, and it is re-reviewed there before any scene is
judged by it. It also fixes how `C_paper` is computed in this study.

```text
C_est(node, scene) = 0.20 pF/mm × 1.5 × HPWL(pad centres of the node in the scene)
                   + 0.5 pF × N_via + 0.3 pF × N_pad
a move is inside the budget when  C_est(node, scene) ≤ C_lim(node)
equivalent pad extent:            HPWL_max = (C_lim − 0.5 × N_via − 0.3 × N_pad) / 0.30 mm
```

| Term | Value | Basis |
| --- | --- | --- |
| Capacitance per length | 0.20 pF/mm | ASSUMED. `PF_PER_MM` in `mc04_s7_r4/buffer_runs.py`: an outer-layer 0.2–0.25 mm trace over the continuous In1 AGND plane, ground-flanked, stated there as a conservative upper value for the 6-layer 1.6 mm board. It is the same figure as `run_estimate_basis` of the locality records. No fabricator stack-up is retained, so it is not derived from a dielectric thickness |
| Route factor | 1.5 × HPWL | ASSUMED. `ROUTE_FACTOR` in the same file |
| Via | 0.5 pF each | ASSUMED, **new in this brief and unsourced**: no project record or retained document gives it. `N_via` is the number of node pins on the other face from the amplifier pin. Earlier estimates excluded vias |
| Pad | 0.3 pF each | ASSUMED, new in this brief and unsourced: about an 0603 pad over a plane 0.1 mm below (from the brief review). `N_pad` counts every pad on the node, amplifier pins included at the same figure. Ruling 1 counts pads in `C_stray`, so the estimate must too; leaving them out would err on the unsafe side |

- Example: a three-pad node with a 10 pF limit allows a 30.3 mm pad extent with no via, and 28.7 mm with one.
- A three-pad node therefore carries 0.9 pF, and a four-pad node 1.2 pF, before any trace. A node whose `C_lim` is
  below its pad and via terms has no geometric allowance at all and reads `NO HEADROOM AT PAPER`.
- The check uses the same pad-centre method as `buffer_runs.py` and `recompute_s10.py`, so figures stay comparable.
- A routed board must later be checked against `C_lim` with extracted copper. HPWL is an estimate, not a
  measurement.
- When a protected IC moves, every protected node on it must have a budget row and pass.

### Ruling 5: one row per node, simulated from the specification

- Decks are generated from `design/reports/io-partition.json` `package_units` and the module specifications, not
  typed from this brief. Values in this brief are for orientation.
- Nodes whose decks are byte-identical share one result; the deck SHA-256 is the key.
- Passives are ideal elements at their specification value. No vendor SPICE model exists for chip resistors and
  C0G capacitors, and none is claimed.
- **Limits of the amplifier models, stated in every row.** Both TI libraries are generic family cores (`Part:
  OPAx196`, "Model Type: Generic"; the OPAx197 file likewise), one channel each. They carry no package parasitics,
  no coupling between the channels of a quad and no supply impedance. The rails in every deck are ideal ±12 V
  sources. The models are typical-only and run at 27 °C.
- Each part is routed through `inventory.json` by its exact line. A part whose `mpn` field is empty in
  `io-partition.json` (for example the 1 kΩ `R_W`, the 10 kΩ `R_FB`, the REF9 40 kΩ and 50 kΩ) is listed
  `IDENTITY OPEN` and makes its node's row `PROVISIONAL`. The executor does not pick an MPN.
- Pots and trimmers (PTV09A-4020F-B103 and -B104, TC33X-2-102E and -103E) are two resistors per wiper position from
  the resistance code. Wiper positions 0.5 and 1.0 are both run.

### Ruling 6: an unmodelled part behind at least 10 kΩ is bracketed; one on an amplifier pin is a blocker

- If a semiconductor without a retained model hangs on the amplifier **output** behind a series resistor of 10 kΩ or
  more, its branch is run twice: resistor to AGND, and resistor open. That the real load lies between the two is
  **ASSUMED**: a reactive load behind a resistor is not guaranteed to fall between the short and open cases. The
  assumption is trusted here only because the load is at least 10 kΩ against an amplifier output impedance far
  below that, so the branch can shift the loop very little either way. If the two runs of a pair differ by more
  than 2° in K1 or by one candidate step in `C_lim`, the row is `PROVISIONAL`. This covers the BAT54S clamp behind
  `COMMAND_LIMIT` and the fold clamp feed behind `F1_CLIP_FEED`.
- The same bracket is **not** trusted on an amplifier input. There the unmodelled part sits on the node that sets
  the feedback factor and the input capacitance divider, with no resistor of the cell between it and the pin, so
  its capacitance and conduction enter the loop directly. That is why the class F runs without a diode are a
  diagnostic and never a budget.
- If it sits on an amplifier **input** node, or on the output behind less than 10 kΩ, the node is
  `BLOCKED: MISSING VENDOR MODEL`. This covers the BAS16GW-QX pairs on `Fk_CLIP` (the non-inverting input of every
  fold cell) and the BCM847BS base behind 1 kΩ.
- The TMUX6112PWR on the REF9 output is followed by 898.7 kΩ. It is represented by an output-capacitance pair of 0
  and 100 pF. Its on-capacitance is not a retained fact, so the REF9 rows are `PROVISIONAL` until that fact is read.
- Every amplifier output also carries a fixed 20 pF stray, with a 0 and 100 pF pair re-run at `C_lim`.

### Ruling 7: a failing cell is reported with one what-if, and the part is the owner's

- A node that fails at `C_stray = 0` is `FAILS AT ZERO STRAY`. One that passes at zero but has `C_lim < C_paper` is
  `NO HEADROOM AT PAPER`. Neither gets a budget, and neither may move.
- For each such class the study repeats the sweep once with 10 pF from the output to the inverting node, labelled
  `WHAT-IF, NOT A DESIGN CHANGE`. The part is KEMET C0603C100J5GACTU (`line-audio-feedback-c`,
  `component-kemet-c0603c100j5gactu`), which the project already fits as `C_FB`. The `summing_node_input` cell note
  already expects "10 pF C0G in parallel" on a parent summer.
- No other value or part is tried. A what-if row is evidence for an owner decision, never a budget.

## Scope: 64 protected nets on 107 footprints, in nine classes

The set is every footprint in a `t1_by_footprint` tally of `census.json` for the six links that block U5110, U8409,
U5209 and U5210 (P-K-P-L12.02.01.02, L03.01, L13.01.01.01, L13.01.01.02, L13.01.02.01, L15.02.01.01), and every net
of those footprints ending `_FB`, `_SUM` or `_SENSE` (DS-156). I derived it read-only; the executor re-derives it
as control P6. The L07 and L08 tallies are excluded: they concern U1415.

| Class | Cell and protected pin | Amplifier | Nets | Members |
| --- | --- | --- | --- | --- |
| A | `remote_buffer`: FB (IN−), 10 kΩ `R_FB`, 100 pF `C_FAST`, 100 Ω `R_ISO` | OPA4196IDR | 11 | `/F3/Cf75ecf_FB`, `/M4A/C2006b9_FB`, `/M4A/C865f36_FB`, `/M4B/C2006b9_FB`, `/M4B/C797803_FB`, `/M4B/C865f36_FB`, `/M4B/Ccb7527_FB`, `/M4B/Cfaa69a_FB`, `/M5B/Ca0a275_FB`, `/W1/C01cf3e_FB`, `/W1/C9cfd7a_FB` |
| B | `bipolar_attenuverter`: SUM (IN−, 100 kΩ, 100 kΩ, 10 pF) and W_SENSE (IN+, 1 kΩ `R_W`, 10 MΩ `R_FAIL`) | OPA4196IDR: 8 SUM, 12 W_SENSE. OPA4197IDR: 3 W_SENSE | 23 | SUM: `/M4A/C154038`, `/M4A/C38051c`, `/M4B/C154038`, `/M4B/C24ce01`, `/M4B/C38051c`, `/M4B/C75c2e7`, `/M4B/Ca1191c`, `/W1/Cb36f8a`. W_SENSE: `/M4A/C154038`, `/M4A/C24ce01`, `/M4A/C38051c`, `/M4A/C75c2e7`, `/M4B/C154038`, `/M4B/C24ce01`, `/M4B/C38051c`, `/M4B/C75c2e7`, `/M4B/Ca1191c`, `/M5B/Ca92eeb`, `/M5B/Ce67982`, `/W1/Cb36f8a`; OPA4197IDR `/A01/Cc045d2`, `/A02/Cc045d2`, `/A05/Cc045d2` |
| C | `dc_control_source`: W_SENSE (IN+) with 10 nF `C_W`, 1 kΩ, 10 MΩ | OPA4196IDR 8, OPA4197IDR 2 | 10 | `/E2/Cd69090`, `/E5/Cb80f06`, `/E5/Cd69090`, `/F3/C8c344f`, `/M4A/C1c45d6`, `/M4B/C1c45d6`, `/W1/C4c1698`, `/W1/C75db46`; OPA4197IDR `/A02/C38cac0`, `/A05/C38cac0` (all `_W_SENSE`) |
| D | `level_attenuator`: W_SENSE (IN+) | OPA4196IDR | 1 | `/W1/C629978_W_SENSE` |
| E | inverting 100 kΩ summers with no feedback capacitor | OPA4196IDR | 9 | audio: `/W1/FOLDER_SUM`, `/W2/FOLDER_SUM`, `/W1/DRIVE_INV_SUM`. control: `/W1/CONTROL_SUM`, `/W1/TARGET_SUM`, `/M4B/TARGET_SUM`, `/M4B/COMMAND_SUM`, `/M4B/COMMAND_INVERT_SUM`, `/F3/RES_CONTROL_SUM` |
| F | fold cell: `Fk_SUM` (IN−, 100 kΩ, 100 kΩ, no capacitor), BAS16GW-QX pair on IN+ | OPA4196IDR | 5 | `/W1/F1_SUM`, `/W1/F2_SUM`, `/W1/F3_SUM`, `/W1/F4_SUM`, `/W2/F4_SUM` — **BLOCKED** |
| G | `PRE_GAIN`: `PRE_GAIN_SUM` (IN−) with the OTA output on the node, 49.9 kΩ and a 10 kΩ trimmer in feedback | OPA4196IDR and LM13700M/NOPB | 1 | `/W1/PRE_GAIN_SUM` — `PROVISIONAL` (the OTA model's stated AC limit) |
| H | non-inverting gain stages: `REF9_FB` (40 kΩ, 50 kΩ) and `OUTPUT_FB` (70 kΩ, 10 kΩ) | OPA4197IPWR (REF9), OPA4196IDR (output) | 3 | `/E2/REF9_FB`, `/E4/REF9_FB`, `/W1/OUTPUT_FB` |
| I | `RISE_EXPO_SCALE`: `RISE_EXPO_SUM` | OPA4197IPWR | 1 | `/E2/RISE_EXPO_SUM` — **BLOCKED** |

Total 11 + 23 + 10 + 1 + 9 + 5 + 1 + 3 + 1 = 64.

### The nodes that decide each IC

| IC | Link and S12 cause | Blocking footprint → node (class) |
| --- | --- | --- |
| U8409 | L03.01, all 183 slots | C8313 → `/M4A/C1c45d6_W_SENSE` (C). R7216 → `/A02/Cc045d2_W_SENSE` (B, OPA4197IDR). U8411 shifted → `/M4B/Ccb7527_FB` (A), `/M4B/C24ce01_SUM` and `_W_SENSE` (B), `/M4B/C1c45d6_W_SENSE` (C) |
| U5210 | L13.01.01.01, all 104 slots with L03.01 at its record | R8356 → `/M4A/C24ce01_W_SENSE` (B). It also needs L03.01 to move, so the U8409 rows apply |
| U5110 | L12.02.01.02, 66 slots | U5205 (48) → `/W1/PRE_GAIN_SUM` (G). C5218 (29) and R5268 (24) → `/W1/C01cf3e_FB` (A). R5149 (27) → `/W2/FOLDER_SUM` (E). R5162 (6) → `/W2/F4_SUM` (F, blocked) |
| U5209 | L13.01.01.02 and L13.01.02.01 | R5228 → `/W1/CONTROL_SUM` (E). R5250, R5251 → `/W1/DRIVE_INV_SUM` (E). **R5253 → `/W1/F1_SUM` (F, blocked).** C8409 → `/M4B/C865f36_FB` (A). R2335 → `/F3/C8c344f_W_SENSE` (C). U5205, RV5205 → `/W1/PRE_GAIN_SUM` (G) |

- Consequence stated now: the only known U5209 route crosses R5253, so U5209 cannot be unblocked by this study until
  the BAS16GW-QX model is stored. U8409 and U5210 depend on classes A, B and C only, which have their models.
- R8456 (`/M4B/C24ce01_W_SENSE`, B), R4238 (`/E2/REF9_FB`, H), R8471 (`/M4B/TARGET_SUM`, E) and C8408
  (`/M4B/C38051c_SUM`, B) are the L15.02.01.01 neighbours and are covered.
- Not covered: any net outside the DS-156 suffixes, for example `/M4B/SUM_NODE` on U8411. It has no budget and is
  listed for the placement brief to rule on.

### Expected outcome, stated before the run

`f2_loop_estimate.py` (first order, typical-only, not a bound) gives the 100 kΩ / 100 kΩ cell with no feedback
capacitor 31.4° at 0 pF, 24.1° at the paper 5.96 pF, 21.3° at 10 pF and 17.1° at 20 pF. All are below K1's 45°
before any stray is added.

- The likely label for class E is therefore `FAILS AT ZERO STRAY`, and the class F diagnostic is likely to read the
  same. This is an expectation from an estimate, not a result.
- If it holds, U5209 (R5228 on `/W1/CONTROL_SUM`, R5250 and R5251 on `/W1/DRIVE_INV_SUM`) and U5110 (R5149 on
  `/W2/FOLDER_SUM`) stay blocked **whatever happens to the BAS16GW-QX model**. Their way forward is then the
  Ruling 7 what-if and an owner decision on a feedback capacitor, not this study's budget table.
- Usable budgets are expected mainly from classes A, B, C, D and H. Those are the classes U8409 and U5210 depend
  on (through L03.01 and R8356).
- The manager and the owner should plan on two ICs at best from this run, and on an owner question about the
  uncompensated summers.

## Pinned inputs

| Input | SHA-256 |
| --- | --- |
| `scripts/stack/studies/mc04_s12_five_ic_joint/census.json` | `92f6fdede21948d10ed49236889f1853b77c1e803445a945a15a92e7dbda095e` |
| `scripts/stack/studies/mc04_s12_five_ic_joint/result.json` | `32532262d6a98dbdef8e73fee4951487f417c8361cc2f008ea801be099da02ed` |
| `design/reports/io-partition.json` | `235277959121d8599cbe1b6c6ae65ed4cd3fd3813cf2a8db05d2951ce5b633ce` |
| `design/partition/floorplan-candidate.json` | `12083ea177cad1492f07fa96ad6dbfea8e5f8d2d347199bb555475c5b9e75a38` |
| `.claude/skills/component-spec-audit/references/inventory.json` | `dd31420dc068ef2953ada299f3a2a873c5da1ee86f645ce4dc95f12476256eba` |
| `design/standard/electrical-standard.json` | `0cdef30d4848414c794b7561c07bef6c5cf63a19f7f79a0fd21866412e0e40fe` |
| `design/spec/modules/wavefolder.py` | `e3a850e841a0f597571d6550e372d337c404fe4155ede3af7372be03ace37a93` |
| `design/spec/modules/envelope.py` | `015b02c5d84550e19bf92b9ec838a43b255a728e02de1e562e855ba632fc2ee5` |
| `design/spec/modules/mix4_vca.py` | `46d1efae983c32e763da7d3934d7fa01a7e0473c5b0c0bd586b28c9c85cf80e2` |
| `design/spec/cells/sweep_input_buffer_vendor.py` | `13c470004de92aeae8dbf31dc54216214b86060758884e9e2ed40e42b9cee23d` |
| `design/spec/cells/sweep_precision_vendor.py` | `31c77c207c3b3da770cbc3800c3d2c75cd96492a5a3e3c6cd246d27239d87eae` |
| `design/spec/modules/spice_trace.py` | `3234148d53ec6241468e172e28340a2f0aee1acd299b68c4eea8a6cc7927f964` |
| `design/reports/spice/input-buffer-vendor.json` | `12a0de40445d5156ccab2d583b45baa14f8b0420935ae57ca7a2f3d391654c9b` |
| `design/reports/spice/precision-output-vendor.json` | `9a974de1aa3ade8d7c189dd2238e90b96d7f41a8f134210ed3c99fac3d684e9b` |
| `scripts/stack/studies/mc04_s7_r4/buffer_runs.py` | `df656dc333dff510757b668278ba53ed2a078860d47dcff38c86070a1aaac9b1` |
| `scripts/stack/studies/mc04_s10_r2_packet/f2_loop_estimate.py` | `667c027b4ce3a861ab2ad86deb50cb702dba60e728b01daf4ba22cbaf812856d` |
| `scripts/kicad/run.sh` | `bc74f0ade82c29d64c44119ea435bc7bfd164fc06e9afff240a3cb2b44b272a0` |
| `scripts/kicad/pin.env` | `769e2be0b61e7d92a6930684f13166b7dc098522008de3969cd30d6c4a363246` |
| `mc04-s12-disposition-20261127.md` | `6c21cb39354f12f091472c1dd33c56ec53b4ea0bf1196489737f7bc1e8516f0b` |
| `mc04-s12-report-20261127.md` | `d3b9a33026089d24aa4d8e4c591b1cb16545fb617e01800d3993e38a23470a19` |
| `reviews/mc04-s12-result-review-20261127.md` | `77f8039f95d1afce36e52fe056717dc0c77e0219283bc7f5cca5662dbd58f2d9` |

The three model files are pinned in the model table above. The other spec modules a deck is generated from
(`filter.py`, `offset.py`, `mix5.py`, `mixer_common.py`, the cell builder) are hashed by the executor into
`result.json` before the first deck.

## How the oracle is invoked

The study follows the retained receipts and does not invent a second route.

- Every deck runs as `bash scripts/kicad/run.sh ngspice -b <deck>` from the repository root, one at a time, with a
  600 s timeout per deck. The image is `kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`
  and must report KiCad 10.0.6 (P2). The container has no network, so model files must already be under the repository root.
- **A deck is one ngspice invocation.** The study owns its runner (`runner.py` in the study directory). It writes
  one deck with several analyses in one `.control` block and one `wrdata` file per analysis, calls
  `bash scripts/kicad/run.sh ngspice -b`, and passes the result through the imported `check_oracle_result`, which
  is mandatory: ngspice can exit zero after an error. It checks that the deck text is unchanged after the run and
  that every data file is fresh, non-empty and finite.
- The imported `oracle()` and `loop_oracle()` are **not** used for the sweep: `oracle()` takes one analysis per
  deck, and both write to `.circuit-cache/sources/input-buffer-vendor/` and delete the deck. The study imports only
  `loop_probe`, `check_oracle_result` and the two model fetch functions, and edits none of the pinned files.
- The loop deck repeats the sequence of `loop_oracle()`: operating point, AC with voltage injection, AC with current
  injection, operating point again, with the same combination `T = (Tv·Ti − 1)/(Tv + Ti + 2)`, the same check that
  the operating point did not move, and the tolerance ladder `reltol=1e-6 vntol=1e-9 abstol=1e-15`, then
  `reltol=1e-5`, then default. P5 and P8 prove the study's runner against the retained figures.
- The closed-loop deck holds the AC, noise, small-step, large-step and sine analyses of one point. If the vendor
  cores do not converge together in one deck, the runner may split that point into one deck per analysis; each
  split deck counts against the cap.
- Working paths, all ignored: the study's decks and data in `.circuit-cache/sources/mc04-s13/` (kept until the end
  checks pass); the model caches `.circuit-cache/sources/opa196-model/` and `opa197-model/`; and, written only by
  P4a and P4b through the retained scripts, `.circuit-cache/sources/input-buffer-vendor/` and the precision deck in
  `opa197-model/`. PSpice libraries need `set ngbehavior=ps`, as the retained scripts set it.
- A missing image or a version mismatch is a failure under project rule 4, not a skip.

## Arm 0: controls, in this order, stop on any failure

| # | Control | Pass condition |
| --- | --- | --- |
| P1 | input pins | every hash in "Pinned inputs" matches |
| P2 | oracle identity | image digest recorded and equal to the pin; `kicad-cli version` prints exactly `10.0.6` (project rule 4; `pin.env` alone would accept any 10.0.x); the ngspice banner is recorded and reads 44.2, as the brief review observed in this image. Anything else is a stop |
| P3 | model pins | the three model hashes match. OPAx196 is taken from `circuit-dev-resources` commit `54c00fc8` (read-only) or, failing that, through the existing fail-closed fetch of `https://www.ti.com/lit/zip/sbomaf9`, and is placed as `.circuit-cache/sources/opa196-model/SBOMAF9E.ZIP`; the hash decides either way |
| P4a | reproduce a retained receipt (OPAx197) | `python -m design.spec.cells.sweep_precision_vendor --check --offline` passes: `precision-output-vendor.json` is byte-equal, 12 of 12 |
| P4b | reproduce a retained receipt (OPAx196 and OPAx197) | `python -m design.spec.cells.sweep_input_buffer_vendor --check --offline` passes: all 136 rows of `input-buffer-vendor.json` byte-equal |
| P5 | loop-break method | the study's own loop measurement reproduces the three `loop_break_validation` rows (analytic phase margin 9.953°, 59.67°, 7.713°) within 0.1° |
| P6 | census | the study derives 107 footprints and 64 nets, with the class counts 11, 23, 10, 1, 9, 5, 1, 3, 1, and the four binding rows above |
| P7 | positive control: an excessive load must fail | `/W1/DRIVE_INV_SUM` with 1 nF on the node fails K1 and K4; `/E2/REF9_FB` with 1 nF fails K1. If either passes, the method cannot discriminate: stop |
| P8 | negative control | the plain unity follower, no load, gives 54.82° at 2.597 MHz (OPAx196) and 63.95° at 9.986 MHz (OPAx197), within 0.1° and 0.5 %, as the retained `case5a_control` rows |
| P9 | cross-check, not pass or fail | the class E result at 0, 10 and 20 pF is reported beside the first-order figures of `f2_loop_estimate.py` (31°, 21°, 17°), with the difference |

P4a and P4b write nothing: `--check` compares and raises on drift. A drift is a finding and a stop, not a reason to
refresh a receipt.

## Sweep design

One point is one node variant, one corner and one `C_stray` value. Each point is two decks, a deck being one
ngspice invocation of the study's own runner: a loop deck (K1, K2) and a closed-loop deck (K3 to K9: AC, noise,
small step, large step, sine in one `.control` block).

| Class | Variants and corners | Values | Points |
| --- | --- | --- | --- |
| A | harness load on REMOTE: 10 kΩ with 0 and with 1 nF (the cell's stated envelope) | 20 | 40 |
| B | per amplifier: SUM swept and W_SENSE swept, each with the other node at 0 and at 50 pF, wiper 0.5 and 1.0. OPA4197IDR: W_SENSE only. The closed-loop deck is doubled if the two single-path drives cannot share one deck with the common drive: at most 240 extra decks | 20 | 240 |
| C | per amplifier, wiper 0.5 and 1.0; values 0, 25, 50, 100 pF only (the node already carries 10 nF); the full list only if one fails | 4 | 16 |
| D | wiper 0.5 and 1.0 | 20 | 40 |
| E | up to seven distinct decks; the two clamp-loaded outputs run the Ruling 6 pair | 20 | up to 200 |
| G | trimmer at 0 and 1; `IABC` at the lowest and highest value in the retained wavefolder decks | 20 | 80 |
| H | REF9: output capacitance 0 and 100 pF. OUTPUT_FB: one | 20 | 60 |
| What-if (Ruling 7) | only classes with a failing row; one 10 pF variant each | 20 | up to 140 |
| F diagnostic | IN+ to AGND, and IN+ through 10 kΩ only: no diode in the deck. Labelled `DIAGNOSTIC, NOT A BUDGET` | 20 | 40 |
| Ruling 6 output pair | at `C_lim` only | 2 | up to 60 |

- Estimated 900 points and 1 800 decks, or up to 2 040 with the class B single-path decks. Hard cap: 2 400 decks, counted as ngspice invocations, split decks included.
  A cap that is reached is reported as a cap. If closed-loop decks must be split per analysis for more than a few
  points, the cap will be reached before the sweep ends: the driver then stops and reports which classes are
  complete. It does not thin the sweep, and a higher cap is a new admission.
- Order of the sweep, so that a cap or ceiling costs the least: classes B, C and A first (U8409, U5210), then D, H,
  E, G, the what-if rows, the Ruling 6 pairs and last the class F diagnostic.
- Conditions: rails ±12 V ideal, 27 °C, model typical. No temperature or tolerance corner is run; the factor of two
  stands in for them and that is stated in every row.
- When two protected nodes share an amplifier unit, each is swept with the other at 50 pF as well as at 0, and the
  lower limit is the row.
- Class F diagnostic exists so the owner can see whether the fold cell is marginal before deciding anything. It
  cannot be promoted to a budget by the executor or by a reviewer.

## Tests and mutations

| # | Mutation | Must |
| --- | --- | --- |
| M1 | one byte changed in a cached model library | fail closed before any deck |
| M2 | the `C_stray` element dropped from a deck | change the deck SHA and be detected against the recorded key |
| M3 | loop probe polarity swapped | fail P5 |
| M4 | one criterion forced to fail at a value below `2g` | lower `C_lim`; the row may not keep its limit |
| M5 | a class F or class I row given a numeric budget | be rejected by the table builder |
| M6 | one footprint removed from the census | fail P6 |
| M7 | a pass placed above a fail | be reported non-monotonic and decided by the lowest fail |
| M8 | a row with `IDENTITY OPEN` or K9 `NOT RUN` labelled as a plain budget | be rejected |

## Run bounds (ORCHESTRATION.md section 3)

| Bound | Value |
| --- | --- |
| Environment | the Cloud container: 4 CPU, 15 GiB RAM, no swap |
| Interpreter | `/home/user/venv312/bin/python` |
| Heavy processes | one at a time, for start checks, controls, sweep and end checks alike; decks run sequentially; no worker pool; no second container |
| Memory budget | 4 GiB, enforced on the sum of the process-tree RSS (sampled every 5 s) and the oracle container's memory from `docker stats` (sampled every 5 s while a container exists). The container runs under dockerd, outside the tree, so tree RSS alone does not see it. Backstop: abort when `MemAvailable` falls below 8 GiB. Expected peak under 1.5 GiB (S12 measured 968 MiB for `regen-all.sh`) |
| Guard | S12's `guard.py` holds its numbers as constants and lies outside the allowed paths. It is **copied** into the study directory and changed there to the numbers above and to enforce the `docker stats` term; the S12 file is not edited |
| Stopping the oracle | `run.sh` is pinned and starts `docker run --rm` with no name and no limit. A Python timeout kills only the `bash` child, and a SIGKILL of the process group does not reach the container. Therefore, on a deck timeout, a guard abort, a slice end and at every start and resume, the driver runs `docker kill` on every container of the pinned image (`docker ps -q --filter ancestor=<digest>`) and requires that list to be empty before the next deck. A container that survives `docker kill` is a stop |
| Admission | `MemAvailable` ≥ 11 GiB, no other heavy process, no running container of the pinned image, at least 5 GiB free disk, the pinned image present, and a tree that is clean **except the new study directory** (the driver is untracked there at start, as the S12 result review recorded). This brief, its review and the decision rows are committed by the manager first |
| Fingerprint | into `result.json`: OS and architecture, CPU quota and affinity, cgroup memory files or their absence, `MemAvailable`, swap, disk, interpreter and package versions, docker daemon, image digest, `kicad-cli version`, ngspice banner, process list, commit |
| Start checks | `bash scripts/checks/regen-all.sh` (372 s in S12; ceiling 15 min) and `pnpm circuit:check` (ceiling 5 min) |
| Arm 0 | ceiling 2 h 30 min: P4a 10 min, P4b 120 min, the rest 20 min. P4b's wall time is unknown and is recorded. The brief review measured a warm `run.sh` call at about 0.55 s and a first call at 15 s |
| P4b | the retained script has no checkpoint. It runs as **one** background command under the guard with a 2 h limit (`timeout 2h`, and the session's background limit set to 2 h for this command, not the 30 min default). If it is killed by any limit, that is a stop: it is not resumed and not repeated in pieces. "Stopping the oracle" applies to it |
| Pilot | the first 40 sweep decks, timed. If the projected sweep exceeds 5 h, stop and report. Do not thin the value list, drop a corner or shorten a transient to fit |
| Sweep | ceiling 5 h and 2 400 decks; 600 s per deck; expected 1.5 to 3 h |
| Slices | the session's default background limit is 30 min. The sweep driver ends a slice by itself after 25 min, appends one line per finished deck to `results.jsonl`, keyed by deck SHA, and resumes from it after re-checking P1 and P3 and after "Stopping the oracle". The guard writes its summary at every slice end, so no slice lacks one. A resume after a slice end is not a retry |
| End checks | `budget.py --check` (rebuilds every deck text and the budget table from `results.jsonl` without simulating; ceiling 10 min), the unit tests (ceiling 10 min), `regen-all.sh --check` (ceiling 15 min), `pnpm circuit:check` (ceiling 5 min) |
| Total wall time | ceiling 8 h 30 min (20 min start, 2 h 30 min Arm 0, 5 h pilot and sweep, 40 min end); expected 3 to 5 h |
| Retries | at most one, for a proven transient failure only. A non-converging deck is not transient: it is recorded `NOT EVALUATED` with the tolerance ladder tried, and its row cannot be a budget |

No GitHub Actions job, second VM or paid capacity is used.

## Outputs

Allowed writes, and nothing else:

- a new directory `scripts/stack/studies/mc04_s13_node_cap_budget/` with the driver `budget.py` (`--run`,
  `--resume`, `--check`), `cells.py` (deck builders), `runner.py` (the multi-analysis runner), `guard.py` (the
  copy), the tests, a README, `census.json`, `models.json`, `results.jsonl`, `budget.json`, `result.json` and
  `checkpoints/` with the guard summaries;
- the report `circuit/orchestration/campaigns/osc-stack-20261114/mc04-s13-report-<date>.md`;
- ignored working files under `.circuit-cache/sources/mc04-s13/`, the two model caches, and what P4a and P4b
  write under `.circuit-cache/sources/input-buffer-vendor/` and `opa197-model/` (see "How the oracle is invoked").

`budget.json` holds one row per net: class, amplifier reference, pin and MPN, model and hash, every part on the net
with its inventory line or `IDENTITY OPEN`, `C_paper` with its HPWL, via count and pad count, the stimulus used for
each criterion, the per-value criterion results,
`C_lim`, the allowance in pF and as `HPWL_max`, the deciding criterion, and exactly one label:

- `BUDGET n pF (MODEL EVIDENCE ONLY)` or `BUDGET CAPPED AT 50 pF (MODEL EVIDENCE ONLY)`;
- `PROVISIONAL n pF: <reason>`;
- `FAILS AT ZERO STRAY`, `NO HEADROOM AT PAPER`;
- `BLOCKED: MISSING VENDOR MODEL <exact part>`;
- `NOT EVALUATED: <reason>`.

The file carries the status line "MODEL EVIDENCE ONLY, STUDY, NOT ADOPTED, UNVALIDATED DRAFT" and a `method_limits`
block that every row inherits: generic single-channel TI family cores; no package parasitics, channel coupling or
supply impedance; ideal ±12 V rails; typical-only; 27 °C; capacitance lumped to AGND; 0.20 pF/mm, the 1.5 route
factor, 0.5 pF per via and 0.3 pF per pad all ASSUMED; Ruling 4 pending its re-review in the placement brief. The
report repeats the
table, the binding rows per IC, every what-if row, the class F diagnostic, the controls, the bounds, and what is not
established.

Forbidden: any change under `design/`, `boards/`, `doc/`, `.claude/skills/`, any generated file, any retained SPICE
receipt, `decisions.md`, a write to `circuit-dev-resources`, a commit of a model file, a new or changed part, value
or pose, fabrication or order files, supplier contact, a deploy, and any GitHub action beyond the read-only fetch in
P3.

Checks that stay `NOT RUN`, with their reason: KiCad DRC and ERC (a study edits no board or schematic); c6, checks 2
to 4, latch access, threading and routing (rebound in a generator task); bench stability (no hardware); temperature
and tolerance corners (not admitted by this brief).

## STOP conditions

Stop, write what was found, and change nothing further on any of these:

1. input drift: a pin or a model hash differs;
2. any Arm 0 control fails, P4a or P4b drift included;
3. the pinned image is missing or does not report KiCad 10.0.6, the admission check fails, the guard fires, a
   container of the pinned image survives `docker kill`, P4b is killed by a limit, or a ceiling is reached;
4. the pilot projects the sweep beyond 5 h;
5. a deck would need a model that is not retained, other than the two cases Ruling 6 allows: mark the node blocked
   and continue with the other classes; stop only if the gap is in class A, B or C;
6. a result would need a new part, a changed value, a moved part or a relaxed criterion to become a budget;
7. a rule of this brief is ambiguous in a way that changes a row: take the stricter reading, list it under
   "Interpretations made", and stop only if no stricter reading exists;
8. any need to write outside the allowed paths.

No second sweep, no relaxed criterion, no extra value beyond 100 pF except the 1 nF controls, no adoption.

## What the independent reviewer must check

The reviewer is not the executor and not the author of this brief. The review is read-only.

1. The census by an own derivation from `census.json` and `io-partition.json`: 107 footprints, 64 nets, the class
   counts and the four binding rows.
2. Each model hash, and that no deck contains a `.model` line for a diode or transistor.
3. For three nodes of its own choice in classes A, B and E: the deck against the specification, part by part.
4. P5 and P8 with own arithmetic, and that P7 really fails.
5. The limit rule on at least five rows: every tested value up to `2g` passes, the 50 pF ceiling holds, and no
   non-monotonic row was smoothed.
6. `C_paper` for five nodes by own pad-centre computation, and the allowance arithmetic.
7. That class F and class I rows carry no number, and that the class F diagnostic is nowhere used as a budget.
8. That every `IDENTITY OPEN` part and every K9 `NOT RUN` makes its row `PROVISIONAL`.
9. That what-if rows are labelled and that no output proposes the capacitor as decided.
10. The run bounds: fingerprint, peak memory as tree RSS plus container, wall times, deck count as ngspice
    invocations, caps, every slice and resume, a guard summary for each, and an empty container list before each
    resume.
11. That P4a and P4b left both retained receipts byte-equal, and nothing outside the allowed paths changed.
12. That no output calls a draft validated, qualified or released, and that every limit of the method is stated:
    generic single-channel family cores with no package parasitics, channel coupling or supply impedance; ideal
    rails; typical-only models; 27 °C; lumped capacitance to AGND; the four assumed geometry terms; Ruling 4
    pending its re-review.
13. The stimulus table: for three rows of its own choice, that the source, amplitude and measured node are the ones
    stated, and that every `NOT APPLICABLE` is one the table allows.
14. That the class C rows use the relative K6, and that no class C row fails on the cell's own filter time.
15. That the study's runner, not the imported `oracle()` or `loop_oracle()`, produced the sweep, and that P5 and P8
    were measured with that runner.

## Who decides what

| Item | Decided by |
| --- | --- |
| Criteria K1 to K9, the factor of two, the 50 pF ceiling, the value list, the class structure, the labels, the 10 kΩ bracket, and whether the result is accepted as a study | design authority (this brief and a ruling on the result), owner notified |
| The placement test of Ruling 4, with 0.5 pF per via and 0.3 pF per pad | proposed here; settled in the placement brief and its review |
| A class F or class I run once a model is stored | design authority by a reviewed addendum (gap ruling 4) |
| Whether a budget row may be used by the placement study | design authority ruling on the reviewed result, inside DS-161 |
| Any new part or new placement of an existing part: a feedback capacitor on a fold cell or a summer, a snubber, a different amplifier | **owner**, as a separate decision (DS-161) |
| Any changed value or topology of a cell | **owner** |
| Moving a part on a node that is blocked, fails at zero stray or has no headroom; any criterion looser than Ruling 2 | **owner** |
| Downloading the BAS16GW-QX and BCM847BS,115 models, storing the OPAx197 ZIP, and merging branch `claude/project-thread-iw3gai` in `circuit-dev-resources` | **owner** for the downloads; manager for the evidence rows |
| Acceptance of any routed layout against a budget | nobody in this study: it needs extracted copper and, in the end, a bench |

## Scope note: U1415 is handled separately

U1415 (OPA4196IDR, O4 `SINE_DIFF` and `SINE_GAIN`, two unused units) is not blocked by a protected part. Every one
of P-K-P-L08's 787 class-legal slots covers its courtyard, so no capacitance budget can free it. It gets its own
brief, choosing between two routes that are both the owner's to approve: a study of L08's class distances and
clustering (it changes the DS-128 workload), or one dual op-amp in place of the quad (a new part, through Workflow
B with its own evidence bundle and footprint). Nothing in this study is evidence for either, and the L07 and L08
blockers (U1604, R1119, R1614, R1615) get no budget here.

## After the run

- The reviewed result goes to the design authority for a ruling. Only then is the placement study briefed, with
  `budget.json` pinned by hash and Ruling 4 as its test.
- A blocked or failing class goes to the owner with its what-if or diagnostic rows. For classes E and F that is
  the expected path.
- MC04-L1 proceeds regardless. S10 Revision 1 stays returned.

## Decision rows proposed for the manager

| Row | Text |
| --- | --- |
| Brief | MC04-S13 brief issued for DS-161: a vendor-model ngspice study that sets a stray-capacitance limit per protected node for the 64 nets on the S12 blockers of U5110, U8409, U5209 and U5210. Not admitted until its independent review |
| Ruling 1 | A node budget is a limit on total stray capacitance to AGND; the allowance is the limit minus the paper estimate |
| Ruling 2 | Criteria K1 to K9: phase margin ≥ 45°, gain margin ≥ 10 dB, peaking ≤ 3 dB, small-signal overshoot ≤ 25 % (the 10 % large-signal label of the precision output is unchanged), no oscillation above 1 mV, and the settling, response, time-constant and noise terms per class; class C settling is judged against its own zero-stray value |
| Ruling 3 | A limit must pass at twice its value and never exceeds 50 pF |
| Ruling 4 | The proposed placement test is 0.20 pF/mm × 1.5 × HPWL + 0.5 pF per via + 0.3 pF per pad ≤ limit; all four terms are assumptions, the last two new and unsourced; re-reviewed in the placement brief |
| Ruling 5 | One row per node, decks generated from the specification; a part without an MPN makes its row provisional |
| Ruling 6 | An unmodelled part behind ≥ 10 kΩ on an output is bracketed (an assumption); on an amplifier input it blocks the node. The fold cell (BAS16GW-QX) and `/E2/RISE_EXPO_SUM` (BCM847BS,115) are blocked, and a later run of either needs a reviewed addendum |
| Ruling 7 | A failing class gets one what-if with the existing 10 pF C0603C100J5GACTU; fitting it is the owner's decision |

Decided by: design authority (DS-03, Fable agent at high effort), owner notified. Reverse by: a design-authority
ruling on the S13 result, or an owner decision.

## Evidenced, assumed and not established

| Class | Items |
| --- | --- |
| Evidenced from retained sources | the 107 footprints, 64 nets and their classes; the amplifier and part identities named; the three model hashes (OPAx196 bytes fetched and hashed by me); the two missing models; the retained follower margins used in P8; the passing `pnpm circuit:check` before and after writing this brief |
| Assumed | 0.20 pF/mm, the 1.5 route factor, 0.5 pF per via and 0.3 pF per pad; that typical-only generic models with a factor of two are an adequate stand-in for tolerance, temperature, package and supply effects; that lumped capacitance to AGND is the worst case; the Ruling 6 bracket; that the closed-loop analyses converge in one deck; the deck count and every time estimate |
| Expected, from a first-order estimate only | classes E and F below 45° at zero stray (31.4° at 0 pF) |
| Not established | any node's margin or limit; whether any class passes at zero stray; the wall time of P4b; any electrical behaviour of a board; whether a budgeted scene exists |

No simulation was run to write this brief.

## Revision history

Revision 1: SHA-256 `e31a537eb3934c6773e1b2863b705d53766abfdbe65ddbb89c942994eb05ea12`, reviewed ACCEPT WITH
CORRECTIONS (12) in `reviews/mc04-s13-brief-review-20261127.md`. Revision 2 applies all twelve; none is disputed.
Revision 2: SHA-256 `7757906d2db2d9da73978ac4ca16c6b3e53a30034b20d99d7dbfc2560aedb68e`, delta re-review ACCEPT WITH
CORRECTIONS (R1 required, R2 and R3 wording), appended to the same review file. Revision 3 applies all three (second
table below).

| # | Correction | Changed in Revision 2 |
| --- | --- | --- |
| 1 | K6 fails class C at zero stray by construction (100 kΩ pot at mid-travel, about 1.8 ms to 1 mV) | Ruling 2: K6 row and the paragraph "K6 in class C is relative"; stimulus table, class C; reviewer check 14; decision row "Ruling 2" |
| 2 | No stimulus defined per class for K3 to K9 | new section "Stimulus and measured node of each criterion, per class" with the H-REF9 note and the rail rule; `budget.json` records the stimulus; reviewer check 13 |
| 3 | Imported `oracle()` allows one analysis per deck (about 5 000 decks against a 2 400 cap) and writes to another directory | "How the oracle is invoked": study-owned `runner.py`, a deck defined as one ngspice invocation, split rule, working paths listed; "Sweep design": deck definition, cap wording and sweep order; "Outputs": `runner.py` and the extra ignored paths; reviewer check 15 |
| 4 | The deck timeout and the watchdog cannot stop the oracle container; 4 GiB not enforced on the container; `guard.py` outside the allowed paths | "Run bounds": rows "Memory budget", "Guard", "Stopping the oracle", "Admission", "Slices"; STOP 3; "Outputs" (`guard.py` copy); reviewer check 10 |
| 5 | Classes F and I may not be admitted later without a new brief | gap ruling 4 (reviewed addendum: deck, bias points, large-signal criteria, exact-identity check of the model); "Who decides what"; decision row "Ruling 6" |
| 6 | Ruling 4 omits pad capacitance | Ruling 4: formula, the "Pad" row at 0.3 pF ASSUMED, the example and the no-allowance sentence; `budget.json` pad count; decision row "Ruling 4" |
| 7 | Classes E and F are expected to fail K1 at zero stray | "What this study answers" (last bullet); new section "Expected outcome, stated before the run"; "After the run"; the "Expected" row of the last table |
| 8 | K4 at 25 % is looser than the project's 10 % overshoot label | Ruling 2: K4 row and the paragraph "K4 is not the project's 10 % figure"; decision row "Ruling 2" |
| 9 | P2 must require KiCad 10.0.6 | Arm 0, P2; "How the oracle is invoked" (first bullet); STOP 3 |
| 10 | P4b has no checkpoint under a 30 min background limit; "clean tree" cannot hold | "Run bounds": rows "P4b", "Arm 0", "Slices" and "Admission" ("clean except the new study directory") |
| 11 | Ruling 6's bracket is an assumption | Ruling 6: the bracket labelled ASSUMED with its reason, the 2° / one-step test, and why it is not trusted on an input; the "Assumed" row of the last table |
| 12 | Missing limits: generic single-channel cores with ideal rails; Ruling 4 is input to the placement brief; 0.5 pF per via is new and unsourced | Ruling 5 (model limits); Ruling 4 title, lead paragraph and "Via" row; `budget.json` `method_limits`; reviewer check 12; "Who decides what" |

| # | Delta correction | Changed in Revision 3 |
| --- | --- | --- |
| R1 | Class B at wiper 0.5 cancels, so K3, K4 and K7 have no output under a common drive | stimulus table, class B row; new "Note on class B" (BUFFERED_INPUT alone at gain −1, REMOTE_INPUT alone at gain 2 × wiper, the worse decides; K5 and K9 keep the common drive); "Sweep design": class B row and the deck estimate (at most 240 extra decks, counted against the unchanged 2 400 cap) |
| R2 | H-REF9: one load step or two | stimulus table, H-REF9 row; "Note on H-REF9": two separate steps in two transients, 1 mA for K5 and 100 µA for K6 |
| R3 | Time resolution of the relative K6 and K8 tests | new paragraph "Time resolution of the relative tests": timestep at most 1/1000 of the zero-stray time constant, same timestep and window across a corner, resolution recorded, coarser than 0.1 % is `NOT EVALUATED`, a tie at 100 pF counts as a fail and the deciding criterion is named |
