# MC04-S13 brief review: ACCEPT WITH CORRECTIONS (12)

2026-11-27. Independent read-only review of
`mc04-s13-node-capacitance-budget-brief-20261127.md`, SHA-256
`e31a537eb3934c6773e1b2863b705d53766abfdbe65ddbb89c942994eb05ea12` (matches the expected value), at repository commit
`e15cf2dbf6173f86da7f5de07d6b93431375c5ce`. Reviewer: a separate session, model Fable 5.2 (`claude-fable-5-2`).
This is the same model as the brief's author, in a different session with no shared context; I am neither the author
nor the executor. No study, sweep or receipt check was run. Nothing was edited except this file. No commit, push or
GitHub write.

The brief stays inside DS-161 in substance: study only, nothing adopted, U1415 excluded, a new part reported to the
owner. Its scope, receipts and missing-model claims reproduce. Twelve corrections are needed before admission. Six of
them (1 to 6) change what the run does or what a row means, so they need a Revision 2 and a short delta check.

## Scope reproduces exactly: 107 footprints, 64 nets, classes 11/23/10/1/9/5/1/3/1

Own derivation from `census.json` (`t1_by_footprint`, three grids, six links) and `io-partition.json`
`package_units`:

- Union of the six tallies is 107 footprints (5, 14, 66, 30, 29 and 68 per link). The L07, L08 and 26-way L07 tallies
  hold 23 other footprints with no overlap.
- 64 nets end in `_FB`, `_SUM` or `_SENSE`. Every one of the 107 footprints has at least one such net.
- The class membership lists match net by net, including the amplifier MPN per net (OPA4197IDR on the three
  `/A0x/Cc045d2_W_SENSE` and two `/A0x/C38cac0_W_SENSE` nets, OPA4197IPWR on both `REF9_FB` and on
  `/E2/RISE_EXPO_SUM`, LM13700M/NOPB pin 5 on `/W1/PRE_GAIN_SUM`).
- Binding rows match: L12.02.01.02 gives U5205 48, C5218 29, R5268 24, R5149 27, R5162 6. L03.01 gives C8313, R7216
  and U8411 on 183 each. U8411's four protected pins are as listed. R5253, R5250, R5251, R5228, C8409, R2335, RV5205
  and the four L15.02.01.01 neighbours sit on the stated nets.
- The spec text agrees with the class descriptions: BAS16GW-QX pair on `Fk_CLIP` behind 10 kΩ (`wavefolder.py` lines
  99 to 103), BCM847BS base behind 1 kΩ `BASE_LIMIT` (`envelope.py` line 216), `OUTPUT_RF` 20 kΩ + 50 kΩ, REF9 40 kΩ
  and 50 kΩ.

All 21 pinned input hashes and the LM13700 model hash match the working tree.

## The retained receipts exist as described; reproduction was not run

- `input-buffer-vendor.json` has 136 rows. Its three `loop_break_validation` rows read 9.953°, 59.67° and 7.713°, and
  Middlebrook equals analytic in each. The two `case5a_control` rows read 54.82° at 2.597 MHz and 63.95° at 9.986 MHz.
- `precision-output-vendor.json` has 12 cases, 12 pass.
- Both scripts accept `--check --offline` and raise on drift without writing.
- The OPAx197 ZIP and library are in `.circuit-cache/sources/opa197-model/` with the pinned hashes.
  `.circuit-cache/sources/opa196-model/` does not exist yet, so P4b depends on P3.
- The image `kicad/kicad@sha256:1869…d3ec` is present. `kicad-cli version` prints 10.0.6 and ngspice is 44.2. One
  warm `run.sh` call costs about 0.55 s (two container starts); the first call took 15 s.

## The missing-model claims are true on every branch

- `Takazudo/circuit-dev-resources` has ten branches; `main` is `f6099b67`. I listed the full tree of each. No file
  for BAS16, BCM847, BAT54 or TMUX6112 exists on any branch. No OPAx197 model is stored there either (datasheet only).
- The OPAx196 ZIP exists only on `claude/project-thread-iw3gai` at `54c00fc8` (2 ahead of `main`, 3 behind). I
  downloaded it: ZIP `9c264813…cdf5`, `OPAx196.LIB` `31142f5d…c430`, both as pinned.
- The BAS16GW-QX and BCM847BS,115 bundles hold 8 facts each: no SPICE source and no capacitance fact. The BAT54S
  bundle has no capacitance fact. The TMUX6112PWR bundle has no on-capacitance fact.
- The repository holds no model file for these parts. The only diode parameters are the ASSUMED generic ones in
  `sweep_input_buffer_vendor.py` (`DIODES`), which Ruling 2 of the gaps correctly forbids here.

## The criteria are rulings, and the brief labels them so

- `electrical-standard.json` has 19 cells, all `PROPOSAL (planning, owner-delegated)` and `NEEDS BENCH`. It contains
  no phase-margin or gain-margin requirement.
- `PM_LIMIT_DEG = 45.0` in `mc04_s1b_indicator_loops/loops.py` carries the comment "ASSUMED draft criterion", and the
  S4 receipt repeats "the 45 degree phase-margin criterion is ASSUMED". The brief says the same. K1 is a ruling, not
  an accepted requirement, and is labelled correctly.
- K3 and K4 arithmetic holds: 45° in a two-pole loop is ζ ≈ 0.42, peaking 2.4 dB, overshoot 23 %.
- K5, K6 and K8 quote real project text (`OSC_LIMIT = 1e-3`, "settle within 1 mV by 1 ms", "up to approximately
  0.26 ms").
- `PF_PER_MM = 0.20`, `ROUTE_FACTOR = 1.5` and `LIMIT_PF = 50.0` are in `mc04_s7_r4/buffer_runs.py`, stated ASSUMED
  there, and equal `run_estimate_basis`. No stack-up record exists. The brief labels all three geometry terms ASSUMED.

## Corrections required before admission

### 1. K6 on class C fails at zero stray by construction for 100 kΩ pots

K6 demands 1 mV settling of a 1 V step within 1 ms. A `dc_control_source` node carries 10 nF behind the wiper
resistance plus 1 kΩ. With a B104 pot at wiper 0.5 the time constant is 0.26 ms, and 1 mV of 1 V needs 6.9 time
constants, 1.8 ms. If the step enters through the pot, the row reads `FAILS AT ZERO STRAY`, and class C binds U8409
(C8313). The brief does not say where the step is applied.
Fix: define K6 for class C as a step at the amplifier input side of the filter, or as a change against
`C_stray = 0` (K8 already covers the filter).

### 2. The stimulus of each criterion is not defined per class

K4 to K7 name output steps and a 10 V-peak sine, but REF9 has no signal input, class C sits behind a 10 nF filter,
and class G has two inputs (OTA and `IABC`). STOP 7 would then decide rows by "the stricter reading".
Fix: add one table: per class, the source node, amplitude and measured node of each of K3 to K9, and `NOT
APPLICABLE` where a criterion has no stimulus.

### 3. Two decks per point is not possible with the imported `oracle`, so the 2 400-deck cap does not fit

`oracle()` takes one analysis and writes one data file. The closed-loop deck needs AC, noise and three transients.
With the function "imported, not copied or edited" that is five or six decks per point, about 5 000 in all, above
the hard cap.
Fix: either allow a study-owned multi-analysis runner (still through `run.sh` and `check_oracle_result`) and define
a deck as one ngspice invocation, or restate the deck estimate, cap and sweep ceiling.
Also: the imported `oracle` and `loop_oracle` write to `.circuit-cache/sources/input-buffer-vendor/` and delete the
deck afterwards. The brief names `.circuit-cache/sources/mc04-s13/` as the only working directory. Allow the
`WORK` override or list both paths.

### 4. The 600 s deck timeout and the watchdog cannot stop the oracle container

- `run.sh` starts `docker run --rm` with no name, memory limit or CPU limit. The file is pinned, so the study cannot
  add them.
- `subprocess.run(..., timeout=600)` kills only the `bash` child. The docker client keeps the output pipes open and
  the container keeps running under dockerd.
- `guard.py` kills the process group with SIGKILL, which docker cannot forward. It compares its budget with tree RSS
  only; `docker stats` is recorded, not enforced. Only the `MemAvailable` floor covers the container, and firing it
  does not stop the container either.

Fix: on a timeout, a watchdog abort or a slice end, the driver runs `docker kill` on every container of the pinned
image and confirms `docker ps -q` is empty before the next deck and at each resume. State the 4 GiB budget as tree
RSS plus `docker stats`, enforced, and keep the `MemAvailable` floor as the backstop. `guard.py` holds its numbers
as constants and lies outside the allowed paths, so the brief must say it is copied into the study directory.

### 5. Class F and class I may not be "admitted later without a new brief"

DS-161 requires a design-authority brief and an independent review before a simulation runs. This brief defines no
class F sweep with a diode model: no bias points, no large-signal criteria for a conducting clamp, no rule for
checking that a Nexperia file is the model of the exact BAS16GW-QX and not of a same-name family part. The only
class F entry in the sweep table has no diode.
Fix: a later class F or class I run needs a reviewed addendum that gives the deck, the conditions and the
exact-identity check of the model.

### 6. The geometry formula omits pads, although Ruling 1 counts them

Ruling 1 defines `C_stray` as traces, vias and pads. Ruling 4 has no pad term. An 0603 pad over a plane 0.1 mm below
is about 0.3 pF, so a four-pad node carries roughly 1 to 1.5 pF that the estimate does not see. Candidate limits
start at 1 pF, so this decides rows, and the error is on the unsafe side (`C_est ≤ C_lim` passes too easily).
Fix: add an ASSUMED per-pad term, or state that pads are excluded and lower the limit by a stated margin.

### 7. The brief does not say that classes E and F are expected to fail K1 at zero stray

`f2_loop_estimate.py` gives 31.4° at 0 pF, 24.1° at the paper 5.96 pF, 21.3° at 10 pF and 17.1° at 20 pF for the
100 kΩ/100 kΩ cell with no feedback capacitor. That is below 45° before any stray is added. The brief cites the
figures only as cross-check P9 and lists "whether any class passes at zero stray" as not established. The likely
outcome is `FAILS AT ZERO STRAY` for class E, so U5209 (R5228, R5250, R5251) and U5110 (R5149) stay blocked whatever
happens to the BAS16GW-QX model, and usable budgets come mainly from classes A to D and H (U8409, U5210).
Fix: state this under "Consequence stated now", so the owner and the manager do not expect four ICs from this run.

### 8. K4 (25 %) is looser than the project's existing 10 % overshoot label, without saying so

The `precision_output` cell note and `precision-output-vendor.json` use "≤ 10 % overshoot". K4 is a different test
(100 mV small-signal step, tied to 45°), which is defensible, but Ruling 2 claims to be "tied to what the project
already uses". Fix: name the 10 % figure and say why K4 differs.

### 9. P2 must require KiCad 10.0.6, not 10.0.x

Project rule 4 names 10.0.6. `pin.env` accepts `^10\.0\.`, and the image reports 10.0.6. Fix: P2 passes only on
10.0.6 and ngspice 44.2, as S12 recorded.

### 10. P4b and the clean-tree condition repeat two S12 problems

- P4b is one command with no checkpoint, an unknown wall time and a 120 min ceiling. The stated background limit is
  30 min; S12 lost a guard summary to it. Fix: say how P4b runs to its ceiling (one background command with a 2 h
  limit), that a kill is a stop and not a resume, and that correction 4 applies.
- "A clean tree" cannot hold literally: the study directory with the driver is untracked at start, as the S12 result
  review recorded. Fix: "clean except the new study directory".

### 11. Ruling 6's "lies between the two" is an assumption

A reactive load behind a resistor is not guaranteed to fall between the short and open cases. It is harmless here
(output impedance far below 10 kΩ), but the claim should be labelled ASSUMED, like the other brackets. The same
bracket logic is what the class F diagnostic uses on IN+, so the brief should say why it is trusted on an output and
not on an input (the stated reason, an amplifier input node, is acceptable).

### 12. Two limits are missing from the list every row must state

- Both TI libraries are generic family cores (`* Part: OPAx196`, "Model Type: Generic"), single channel. They carry
  no package parasitics, no channel coupling inside the quad and no supply impedance; rails are ideal. The S4 receipt
  says so. Reviewer check 12 and the `budget.json` status line should include it.
- Ruling 4 is the acceptance test of the placement study, which DS-161 gives its own brief and review. Mark Ruling 4
  as input to that brief, re-reviewed there, and the 0.5 pF per via as new and unsourced.

## Beyond DS-161: two extensions, both acceptable as labelled

- The Ruling 7 what-if (10 pF C0603C100J5GACTU from output to the inverting node) and the class F no-diode
  diagnostic simulate circuits that are not the specification. DS-161 asks that a needed new part be reported to
  the owner; these rows are that report's evidence, carry `NOT A DESIGN CHANGE` and `NOT A BUDGET`, and M5 and
  reviewer checks 7 and 9 guard them. Acceptable.
- Blocking class F and class I for a missing model, rather than using the generic `DBAS` parameters, follows
  WORKFLOW ("do not borrow values from a same-name part, a family datasheet or memory"). Correct.

Nothing else exceeds DS-161. The DS-150 stop stays on every node without a budget row, and no rule, part, value or
pose changes.

## Verdict

**ACCEPT WITH CORRECTIONS.** Corrections 1 to 6 must be in a Revision 2 and checked before admission. Corrections 7
to 12 are wording and labels and can be confirmed in the same delta check.

Not run by this review: the study, P4a, P4b, any deck, `regen-all.sh`, `pnpm circuit:check`. Checked by reading and
by own derivation only: scope, pins, receipts' contents, model hashes, repository and `circuit-dev-resources` trees,
oracle version, provenance of each criterion and geometry term.

## Delta re-review of Revision 2: ACCEPT WITH CORRECTIONS (1 required, 2 wording)

2026-11-27. Same reviewer session and model (Fable 5.2, `claude-fable-5-2`), read-only. Subject: Revision 2 of the
brief, SHA-256 `7757906d2db2d9da73978ac4ca16c6b3e53a30034b20d99d7dbfc2560aedb68e` (matches the expected value). The
sections above review Revision 1 and are unchanged. No study or deck was run. The only command beyond reading was
one `sleep` container through `run.sh`, to test the container filter of correction 4; it was killed and no container
remains.

### All twelve corrections are met

| # | Met | Where, and what I checked |
| --- | --- | --- |
| 1 | yes | K6 row and paragraph; class C compares its 1 mV settling time with its own zero-stray value. See the author's choice below |
| 2 | yes, with one new defect | The stimulus table exists and covers every class. Class B at wiper 0.5 is ill-defined: remaining correction R1 |
| 3 | yes | Study-owned `runner.py`, a deck is one ngspice invocation, `oracle()` and `loop_oracle()` not used for the sweep, both working paths listed, P5 and P8 prove the runner |
| 4 | yes | Budget enforced on tree RSS plus `docker stats`; `guard.py` copied; `docker kill` by image at timeout, abort, slice end, start and resume. I tested the filter: `docker ps -q --filter ancestor=kicad/kicad@sha256:1869…d3ec` finds a container started by `run.sh`, and `docker kill` on that list empties it |
| 5 | yes | Gap ruling 4: a reviewed addendum with deck, bias points, large-signal criteria and the exact-identity check |
| 6 | yes | 0.3 pF per pad in the formula; the examples compute (30.3 mm and 28.7 mm) |
| 7 | yes | "Expected outcome, stated before the run", with 31.4°, 24.1°, 21.3° and 17.1°, and "two ICs at best" |
| 8 | yes | K4 paragraph names the 10 % label and keeps it for jack outputs |
| 9 | yes | P2 requires exactly 10.0.6 and ngspice 44.2; STOP 3 repeats it |
| 10 | yes | P4b is one command with a 2 h limit and a kill is a stop; "clean except the new study directory" |
| 11 | yes | Bracket labelled ASSUMED, with the reason it is not trusted on an input |
| 12 | yes | Model limits in Ruling 5, `method_limits` and reviewer check 12; Ruling 4 marked as input to the placement brief; via term marked new and unsourced |

### The four author's choices are sound

- **Class C K6 relative to zero stray.** Sound. It removes the built-in failure and keeps a test of what a move
  changes. Note that 100 pF on 10 nF is a 1.0 % change, so K6 and K8 sit exactly at their limit at the 100 pF point,
  which decides between a 50 pF and a lower class C limit. A numerical tie can only lower the limit, so this is
  safe; the report should say which criterion decided.
- **Study-owned runner with the 2 400 cap.** Sound. The split rule counts against the cap, and the sweep order puts
  classes B, C and A first, so a cap costs the least useful rows.
- **0.3 pF per pad.** Sound as an ASSUMED, unsourced term. The figure is my own rough estimate from the Revision 1
  review, and the brief labels it that way.
- **2° or one candidate step.** Sound. It turns an untested assumption into a measured one per row.

### Remaining corrections

**R1 (required). Class B at wiper 0.5 has no output for K3, K4 and K7.** The cell computes
`Vout = 2·Vwiper − Vbuffered_input` (`electrical-standard.json`, `bipolar_attenuverter`). With BUFFERED_INPUT and
REMOTE_INPUT driven together and the wiper at 0.5, the two paths cancel and the output is about zero. Overshoot as
a percentage of the step, peaking above the low-frequency gain and a gain change in dB are then undefined, and
STOP 7's stricter reading would turn the corner into a spurious failure. Class B holds 23 nets and binds U8409 and
U5210.
Fix: in class B, for K3, K4 and K7, drive each path separately with the other source at 0 V (BUFFERED_INPUT alone,
gain −1; REMOTE_INPUT alone, gain `2 × wiper`), and let the worse decide. K5 and K9 may keep the common drive. This
adds at most 240 decks if the closed-loop deck must be doubled, which still fits the cap.

**R2 (wording).** H-REF9 names a 1 mA load step for K5 and "the 100 µA load step" for K6. State whether these are
two steps or one, and the amplitude of each.

**R3 (wording).** For the relative tests K6 and K8, state the time resolution of the measurement (for example a
maximum timestep as a fraction of the zero-stray settling time). At wiper 1.0 the class C time constant is 10 µs, so
1 % is 0.1 µs.

### Nothing else is broken

The scope, pins, controls, mutations, STOP conditions, labels and forbidden list are unchanged or tightened. The
decision rows match the rulings as revised. The brief still adopts nothing and stays inside DS-161.

### Verdict on Revision 2

**ACCEPT WITH CORRECTIONS.** R1 must be applied before admission. It is confined to the class B row of the stimulus
table and can be confirmed by the manager by inspection; I do not ask for another review round if it is applied as
worded. R2 and R3 are wording.

## Delta review of Revision 4 (Addendum A, P4b redefined): ACCEPT

2026-11-27. Same reviewer session and model (Fable 5.2, `claude-fable-5-2`), read-only. Subject: Revision 4 of the
brief, SHA-256 `a0381b6a6c6f5a65414951c96d4eaf611c9aa7a38ff9d33eea2281eb7cfc5806` (matches the expected value),
uncommitted on top of `e3b747b7`. The sections above are unchanged. No deck, sweep or `p4b.py` was run, and `p4b.py`
does not exist yet, so this reviews the definition, not an implementation.

### The cause is as stated

- `scripts/stack/studies/mc04_s1b_indicator_loops/result.json` hashes to `40584463…840c` at HEAD.
  `git show 4b0ccee5:` of the same path hashes to `5cdac8e9…57fa`, the value pinned as `PAPER_SHA256`. The last
  commit on the file is `93197a3e`.
- In the HEAD file, U8417 unit 3 is `OPA4197IPWR` (GBW 10 MHz). `paper_point()` is called only for model `OPA4196`,
  so a re-pin alone would set an OPA4196 run beside an OPA4197 paper row. Refusing the re-pin is correct.
- The stop report gives 1233.6 s and 62 of 136 cases, which is index 62, the first row with the comparison.

### The exclusion is minimal and correctly identified

- In `input-buffer-vendor.json`, `metrics.paper_screen` exists on exactly indices 62 to 77. Those are exactly the 16
  rows with model `OPA4196` and case `case5a`, and `paper_screen` is the last key of each `metrics` object.
- `paper_point()` is the only caller of `paper_points()`, and `paper_points()` is the only reader of
  `PAPER_RESULT`. `run_all()` calls `paper_point()` at one place, under `case5a` and `OPA4196`.
- The top-level `paper_screen` block of `report()` is built from the constants `PAPER_RESULT` and `PAPER_SHA256` and
  reads no file. Keeping it inside the comparison is right; it will be equal.
- No derived block carries the excluded object. `deltas()` walks the OPA4197 keys, which have no `paper_screen`
  (confirmed: no `deltas` entry contains it). `oscillation_summary()` reads `sustained_oscillation` only, and
  `settle_comparison()` reads settle times only.
- Every vendor-simulated number of those 16 rows (`phase_margin_deg`, crossover, operating point, attempts,
  `deck_sha256`) stays compared. The excluded object adds only a paper figure and a difference derived from it.

### The two substitutions cannot change any other output

- `run_all()` looks up `all_cases` and `paper_point` as module globals at call time, so replacing the module
  attributes takes effect and nothing else needs to change.
- `run_all()` keeps no state between cases: one deck name per case, results appended in list order, and the only
  shared side effect is `.spiceinit`, written at entry and removed in `finally`. Calling it once per batch of five
  gives the same rows as one call, provided the batches are consecutive slices of one original list. Reviewer check
  18 covers that.
- `report()`, `deltas()` and `settle_comparison()` depend on row order only through the concatenated list.
  `validate_loop_break()` runs after `run_all()` and without `.spiceinit` in the retained `run()` too, so running it
  once after the last batch keeps the original sequence.
- Rows restored from `checkpoints/p4b.jsonl` round-trip exactly through JSON (floats, `null`, key order), so a
  resumed run compares equal to an uninterrupted one.

### M9 to M11 and the resume rule are sound

- M9 proves the comparison still bites on vendor metrics. M10 proves the exclusion is one key wide. M11 proves the
  set is exactly 16 rows in both directions. Together they cover A2 items 4 and 5.
- `.spiceinit` is neither tracked nor ignored in this repository, and `run_all()` refuses to start when it exists.
  Deleting it at a resume only when untracked and byte-equal to `set ngbehavior=ps` plus a newline is the narrowest
  rule that works; anything else being a stop is right.
- A slice of 20 minutes plus one batch fits the 30 minute limit at the measured 20 s per case. The later `case5b`
  transient rows were not timed by the stopped run, so the 45 to 60 minute estimate is an extrapolation; the
  120 minute and 8 slice ceilings bound it.

### Nothing else is broken

- The diff against the committed Revision 3 touches the P4b rows, STOP 2, mutations, outputs, the state paragraph
  and the addendum. Scope, criteria, rulings, sweep and caps are unchanged.
- The stopped run's commit `e3b747b7` wrote only the study directory and the report.
- Treating the stale pin as maintenance item MC04-RM1 with its own brief, outside S13's writes, is consistent with
  the forbidden list and with "a drift is a finding, not a reason to refresh a receipt".

### Two wording points, neither blocks admission

1. The state paragraph still carries the Revision 3 sentence "The reviewer asks for no further round if R1 is
   applied as worded" directly after the Revision 4 statement. Move it beside the Revision 3 text, so it cannot be
   read as covering Revision 4.
2. A4 should say that `p4b.py` takes the original `all_cases()` list once per process, before the substitution, and
   that the 136th case forms a last batch of one.

### Verdict on Revision 4

**ACCEPT.** P4b as redefined tests everything S13 leans on and excludes only what cannot be reproduced at HEAD. The
implementation of `p4b.py` is for the result review to check (reviewer checks 16 to 19).
