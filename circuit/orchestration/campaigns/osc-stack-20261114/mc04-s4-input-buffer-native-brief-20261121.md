# MC04 stage 4 native brief: simulate the six input buffers with OPA4196 and OPA4197 vendor models

- Campaign / task ID / attempt ID: osc-stack-20261114 / MC04-S4-INPUT-BUFFER-SPICE / 20261121-1
- State: **PLANNED (not admitted)**. The WSL session fills the environment and admission fields before any run.
- Top-level manager: Claude Project lead, thread "Resume OSC instrument order-readiness campaign", branch
  `claude/project-thread-iw3gai`. Sole dispatcher on the device: the WSL Claude Code session the owner starts.
- Parent decisions: owner, 2026-11-21: develop option D in stages; then "Try a smaller chip package"
  (`mc04-remedy-decision-packet-20261120.md`).
- Independent reviewer: a separate reviewer session or subagent that did not write the harness.

## Goal and non-goals

Goal: model evidence comparing OPA4196 (current, SOIC-14) and OPA4197 (TSSOP-14 candidate) in the six
input-buffer stages that the stage 1a draft limits keep on their front boards:

| Board | IC | Units in the input role |
| --- | --- | --- |
| JL | U1216 (O2), U1416 (O4) | units 1–3 high_impedance_input, unit 4 general_output |
| JL | U1518 (O5, already OPA4197IDR) | 1V/oct follower (precision; compare packages only, same die) |
| JR | U4346 (E3) | units 1–3 high_impedance_input, unit 4 general_output |
| JR | U8314 (M4A), U8417 (M4B) | high_impedance_input units (U8417 also output/indicator units) |

Non-goals: no part substitution, no schematic, spec or board edit, no DRC/fill, no adoption, no hardware.

## Topology to model (source facts)

From `design/reports/io-partition.json` and the generated netlist `schematic/boards/osc-jack-right.net`
(E3 SIG path as the reference; the other inputs share the cell):

`J_SIG tip → TMUX7412 (U4302) switch → *_PROTECTED (100 kΩ R_PD to AGND) → 10 kΩ R_LIMIT → *_SENSE
(BAT54S clamp D4301, op-amp IN+) → follower (OUT tied to IN−) → *_BUFFER`; general-output units drive two
499 Ω isolation resistors to a jack (`*_DRIVE`, `ISO_MID`).

Read each instance's exact cell from `design/spec/modules/{envelope,mix4_vca,oscillator}.py` rather than
assuming E3's is universal.

## Cases (minimum)

For each amplifier model, at ±12 V:

1. ±5 V step and a 10 V-peak 20 kHz sine at the jack, source 1 kΩ (patched) and open (unpatched, 100 kΩ
   pull-down only): output overshoot, settling to 1 mV, steady-state error.
2. The follower with the added board run to its new position: 0, 10, 30, 50 pF on `*_SENSE` and on
   `*_BUFFER` (stage 3 places the TSSOP bodies 13–32 mm away; 50 pF bounds a long run, ASSUMED).
3. General-output units: 499 Ω + 499 Ω into open, 100 kΩ and 10 kΩ jacks, with 0 / 100 pF / 1 nF cable.
4. Overdrive to ±12 V at the jack through the clamp: recovery time and phase reversal check.

Report per case and model: overshoot %, settling time, any sustained oscillation, and the difference
OPA4197 − OPA4196. Acceptance targets are not set by this brief; reuse the retained 10 % overshoot / 1 mV
settle targets of `design/spec/cells/sweep_precision.py` only as diagnostics, labelled as such.

## Inputs and models

- Repository at the head of `claude/project-thread-iw3gai` at launch; record the commit.
- OPA197 model: TI SBOMA34D, already pinned in `design/spec/cells/sweep_precision_vendor.py`
  (ZIP sha256 `9e55fcaa…66e5`, LIB `fc5b020e…22a5`). Reuse that fetch-and-pin code.
- OPA196 model: **not retained**. Fetch TI's OPA196 PSpice model from the OPA196 product page, store it
  unmodified in `Takazudo/circuit-dev-resources` under `texas-instruments/opa4196/` with the vendor revision
  in the name and an inventory row, and pin its sha256 in the harness exactly as SBOMA34D is pinned.
- Clamp and switch: use the retained BAT54S and TMUX7412 owner facts; where no vendor model exists, model the
  switch as its R_ON bound (15 Ω, fact-fault-switch-t-ron-12v-single) and the clamp with a generic Schottky,
  each labelled ASSUMED.

## Program and write targets

- Write a new harness `design/spec/cells/sweep_input_buffer_vendor.py` following the pattern of
  `sweep_precision_vendor.py` (vendor libraries stay in the ignored `.circuit-cache/sources/`), and a report
  `design/reports/spice/input-buffer-vendor.json` with `--check` drift detection.
- Run ngspice only through `bash scripts/kicad/run.sh ngspice -b …` with the pinned image (`scripts/kicad/pin.env`),
  `--pull=never` if the image is present. A missing oracle is a failure, not a skip. Do not use a host ngspice.
- Allowed writes: the harness, the report, a README section in `design/spec/cells/` if that directory has
  one, and the circuit-dev-resources model file plus inventory row. Nothing else.
- Run `pnpm circuit:check` before and after. Run `bash scripts/checks/regen-all.sh` first and commit any
  tracked regeneration separately.

## Environment and budget (WSL session fills these)

- Model / effort / session ID: record from the client, not self-description.
- Windows and WSL are one host pool. Use the machine-wide heavy guard
  (`bash $HOME/.claude/scripts/heavy-guard.sh -- …`) for the ngspice runs; one native job at a time.
- Proposed ceilings, to be confirmed against actual capacity: 1 CPU, 2 GiB, no swap, 600 s per run including
  cleanup, at most one retry for a proven transient failure.

## Completion and hand-back

Push to `claude/project-thread-iw3gai`, then report: the commit, the report sha256, a per-case table of both
models, every check run with PASS / FAIL / NOT RUN and the reason, and any model or input that was
unavailable. The independent review follows before any substitution is proposed.

Native simulation result: **NOT RUN** at this brief.
