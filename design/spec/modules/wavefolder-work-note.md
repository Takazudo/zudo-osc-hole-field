# Issue #32 wavefolder capture work note

Date:2026-09-28. Authority: PROPOSAL (planning, owner-delegated).
Unvalidated draft — not bench tested.

Read latest #32 with OSC-ES-1, AGENTS/spec API and applicable canonical workflow.
Workflow blob matches the previously read current workflow; no instruction change.
Initial regen-all and circuit:check passed with no tracked baseline drift.
Manager confirmed W2=51/W1=52 and the narrow PNG publication-allowlist additions.

## Implemented decisions

- W2 remains physically left of W1;22 fixed UIDs bind once. Additive instrument
  registration only; no locked hardware or pristine handoff modification.
- One active OTA pre-gain section, linear FOLD bias servo, fixed0.1 bias gain,
  four feed-forward diode reflection cells, gain8, local1uF/100k AC coupling,
  buffered LEVEL and standard998ohm output. Planning unity bias was explicitly
  replaced to keep normal drive within the useful four-cell range.
- Chose existing BAS16GW-QX, LM13700M/NOPB, OPA4196IDR/OPA4197IPWR and standard
  input isolation/control/indicator cells. Ten exact100nF C0G parts form the
  coupling capacitor bank; unresolved passive-value MPN fields remain blank.
- Two trims (offset and maximum gain), not the rough one-trimmer estimate.
- Core/indicator islands are separate; coupling and fold junctions Sensitive.
  Lamps monitor input buffers only; no OUT LED or hidden jack normals.

## Foreground review and applied fixes

Reviewed actual physical pin mapping, signal/control polarity, current-source
collector compliance, stage feedback graph, panel binding, active/unused IC
sections, value/MPN consistency, current arithmetic, model limits and plots.
The nonconvergent initial all-hard-limited amplifier model was replaced with
ideal linear amplifiers plus one smooth bias-servo output bound. It is not a
claim about physical amplifier saturation. The runner now deletes prior trace
files and rejects missing/aborted results, preventing stale-data success when
ngspice returns0 after a failed analysis. Added internal-voltage monitoring and
source/model/plot hashes, then reran every model case and regenerated both PNGs.

Structural stability proof is scoped: passive clamp plus negative local feedback,
acyclic interstage graph, ideal bound |2c(x)-x|<=|x| and positive RC decay. Real
phase margins and bias-servo/cable behavior remain explicitly unqualified.
Model diode mismatch/control-dependent offset are documented, not hidden by the
calibration fixture or described as physical measurements. Current planning uses
explicit branch envelopes and keeps guaranteed maxima null.

## Verification

- Pinned KiCad10.0.6 ERC: zero errors;12 documented wavefolder LED warnings.
  Other captured families contribute108 warnings. No suppressions.
- Complete native netlist parity,22 panel bindings, left/right order and two
  isolated AC storage nets PASS. Entire-instrument reference uniqueness PASS.
-38 module tests PASS, including7 wavefolder tests.
- Offset calibration sweep +16 DC response cases +one sine transient PASS,
  model only. Required12 transfer curves plus limit/mute/mismatch fixtures.
  Eight turning points at full FOLD/zero BIAS; transient OUT -2.614..+2.813V,
  mean -1.17mV over700..800ms for the stated100Hz fixture.
- Required transfer/transient PNGs generated with matplotlib3.9.2 and visually
  inspected; plots are explicit about pre-AC versus jack output and model status.
- Native21-page schematic PDF exported and W2 whole-sheet/detail inspected:
  218 units fit A0 with border/title clearance. This does not prove PCB fit.
- Current regeneration, circuit:check, pnpm check, regen-all --check and
  whitespace checks PASS. Inventory scope is42 manual records; schematic/
  placement binding not performed, pin-asset check performed.

Planning upper both instances:+12V88.438138mA,-12V82.338138mA,+5V0.5mA.
Guaranteed maxima NOT ESTABLISHED. #33/#34 must reconcile instrument counts and
measured startup/dynamic/fault loads; the whole-instrument budget is not passing
by assertion here.

Open: exact unresolved sourcing; diode thresholds/matching/fold count; OTA and
servo offsets/current/gain; actual phase margins, noise/distortion/bandwidth;
control-step/output peaks, protection/startup; capacitor/harness and board fit;
Sensitive routing; measured currents. No fabrication files, push, issue edit or
deploy. Browser/full build/heavy tests NOT RUN; manager owns merged build.
