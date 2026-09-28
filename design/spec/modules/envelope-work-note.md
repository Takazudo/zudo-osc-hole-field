# Issue #31 envelope capture work note

Date: 2026-09-28. Authority: PROPOSAL (planning, owner-delegated).
Unvalidated draft — not bench tested.

## Request and initial state

Read latest #31 including OSC-ES-1, AGENTS.md, canonical circuit workflow, spec
API, retained standard cells/pin maps and the ideal ar-engine.js handoff model.
Initial regen-all and circuit:check passed, with no tracked baseline changes.
The inventory check covered42 manual records, no schematic placement binding.
Six E1–E6 instances use reserved internal indices41–46;108 panel UIDs are fixed.

## Decisions and source work

Recorded G07 truth table before drawing: SIG/button OR, rising-edge retrigger
from present level, ASR early gate release, AR fall-edge immunity, LOOP restart
following EOC, stage gates/lamps and explicit startup/mode-change behavior.
G07 remains an owner-confirmation item, not an owner-approved fact.

Captured a clocked one-hot HC74/HC00/HC14 state machine, dual-OTA integrator,
two exponential rate converters, finite-target curved slopes, local hold/idle
clamps, HC221 EOC pulse, standard protection/control/output cells and all five
indicators. Packed logical channels with explicit physical pin mapping and
supply domains. Timing stays local/Sensitive; LED circuits observe ENV_BUFFER.

The design uses more logic/amplifier packages than the rough planning sketch.
Counts and planning reserves are explicit; no guaranteed current maxima exist.
EOC uses the already retained source-backed HC221 as an explained addition to
the requested state-logic family. No IC inventory or imported evidence is edited.

## Applied foreground-review findings

- Registered completion and synchronized both threshold flags: a combinational
  completion pulse could otherwise become too short near a clock edge. Local
  raw-threshold clamps with100Ω paths bound storage while synchronization catches
  up. Comparator inputs use buffered ENV+1V and hysteresis, preventing negative
  common-mode input and clamp-induced threshold chatter. Timing, model, current
  and oracle checks rerun after this correction.

- Binding fixed envelope hardware exposed pre-existing oscillator collisions
  at D1301 and RV1306. Manager authorized bounded DO/RVO internal oscillator
  reference prefixes. Locked panel references and all oscillator connectivity
  are preserved. Whole-instrument uniqueness and oscillator native checks pass.
- OTA current outputs now combine through separate100Ω resistors; native ERC
  output/output conflict resolved without suppressing the rule or changing the
  source-backed library. These resistors are local integrator elements.
- Shared complemented signals eliminate redundant NANDs; unused logic outputs
  and complements become NCs, removing isolated-label warnings. Independent
  truth-table tests exercise the actual packed NAND graph, not only source ASTs.
- BIP divider is selected directly as64k/80k, leaving unresolved value MPN blank;
  gain2.25 produces1.25×ENV−5. Modified button capacitor identity is also blank.
- The behavioural EOC timestamp storage uses a very high off resistance so its
  artificial leakage does not shorten the nominal pulse. The fixture still does
  not validate physical HC221 timing/non-retriggerability. Model report hashes
  include capture, logic and runner sources.

## Verification and limitations

Native envelope and oscillator ERC/netlist checks: zero errors.60 documented
white-LED pin-type warnings belong to envelopes;48 existing warnings belong to
pilot/filter/power.108 bindings and six isolated storage nets pass. No suppression.

Eight transient cases cover ASR/AR/LOOP×LINEAR/CURVED plus early ASR release and
fall retrigger. These exercise the actual packed NAND/DFF graph with ideal analog
boundaries; physical converter, RC clock/reset, semiconductor dynamics, temperature,
propagation/metastability, protection and actual rail currents are NOT RUN.

Model, current, truth-table, topology and whole-instrument reference regressions
pass with the module suite. circuit:check, pnpm check and regeneration checks
pass. Native19-page PDF exported and E1 whole-sheet/detail inspected: the A0 grid
fits with border/title-block clearance and readable detail. No PCB-fit proof.
No browser, full build or heavy suite: manager owns the merged build.

Per-instance planning upper:+12V58.45mA,-12V53.45mA,+5V21.541489mA.
Six-envelope planning upper:+12V350.7mA,-12V320.7mA,+5V129.248936mA.
Guaranteed maxima remain null/NOT ESTABLISHED. #33/#34 must reconcile expanded
counts and actual startup/load/fault currents with whole-instrument rail ceilings.

Remaining gates: G07 owner confirmation; exact unresolved passives/trimmers;
clock/reset/power sequencing; HC timing and synchronizers; bounce/minimum trigger
width; real OTA/mirror/temperature/time range; clamp/hold accuracy; EOC and loop
limits; output/patch protection; indicator behavior; board fit, local routing and
remote harnesses; bench current. No fabrication, publication, push or issue edits.
