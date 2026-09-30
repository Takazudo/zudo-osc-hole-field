# Issue #30 filter capture work note

Date: 2026-09-28. Authority: PROPOSAL (planning, owner-delegated).
Unvalidated draft — not bench tested.

## Requested result and scope

Capture F1–F3 with four OTAs, independent LP/BP/HP and parallel dry OUT,
54 fixed panel UIDs, protected standard cells, model evidence and rail planning.
Own filter.py, additive instrument registration, generated filter/root schematic,
filter tests/model/current reports and architecture/osc-block-vcf.mdx. Index block
21–23 is reserved; no oscillator/pilot allocations are changed. No inventory,
placer, fabrication output or pristine handoff change is included.

## Actions and evidence

- Initial regen-all and circuit:check passed without baseline changes.
- Read latest issue #30 including OSC-ES-1. Adopted G06 dry OUT-only GAIN;
  owner confirmation is still open and prominently identified in the page.
- Used existing exact LM13700M/NOPB source-backed library/pin map, retained TI
  SNOM267 model unchanged with SHA-256 receipt and full copyright header.
- Built two integrators, exponential current conversion, third-OTA resonance
  with nonlinear feedback, fourth-OTA dry VCA, all interface/control/LED cells.
- Separated LED-driver and filter-core islands; marked local integrators and
  exponential nodes Sensitive. All panel controls are remote-safe cell bindings.
- Seven internal adjustments replace the rough three-trimmer estimate. Whole
  captured amplifier packages replace the handoff's rough section count.
- KiCad 10.0.6 ERC: zero errors, 24 filter LED pin-type warnings explained in
  filter-erc-notes.md; existing pilot adds twelve. Complete netlist parity and
  six isolated integrator nets pass. There are no ERC suppressions.
- Eight AC vendor-OTA cases cover three cutoffs, low/high resonance and dry mute;
  ninth transient bounds model-only self-oscillation. Ideal opamps, imposed
  currents, generic diode limiter and offset fixtures are explicit limitations.
- Pinned native PDF exported and visually inspected at whole-sheet scale and
  detail: filter grid fits A0, final row clears page border/title block. This is
  schematic readability evidence, not PCB placement or dimensional proof.

## Foreground review findings applied

Reviewed the actual source topology, component attributes, physical OTA pins,
source/model hashes, G06 paths, package packing, report values and doc statements.
The dry servo's first 5.11k sense choice demanded nearly 1mA through a 22k bias
feed, losing collector compliance at full-scale command. Changed it to 12.4k
(403.2uA nominal), selected 68.1k TIA feedback, added a regression constraint and
reran all nine model cases: dry full-scale model gain +0.0142dB into 100k. The
calculation is a nominal headroom screen; real PNP/model corners remain open.
Other review fixes completed during capture: separate LED/core amplifier packing,
unique package keys across islands, explicit current reserves, reverse B–E
protection, and nonlinear maximum-resonance feedback. No known deterministic
source/netlist error remains after the final checks.

## Verification and remaining gates

20 module tests pass, including six filter contract tests. circuit:check and
pnpm check pass; their manual-inventory scope does not bind the entire schematic
or prove component performance. The filter native check and source/current
regeneration checks pass. No browser, full site build or heavy suite was run;
manager owns the merged-base build and root schematic regeneration if needed.

Current planning upper total for three filters: +12V 174.6mA, -12V 167.4mA,
+5V 0.9mA. Guaranteed maxima are NOT ESTABLISHED and null in the report. #33/#34
must include the expanded count and measured startup/dynamic/fault loads. The
complete instrument supply budget is not declared passing.

Still open: G06 owner confirmation, exact trimmer/value procurement, physical
converter and servo operation, current mirror matching, real amplifier stability,
noise/distortion/headroom, temperature/cutoff slope, self-oscillation limits,
control feedthrough/mute, power-off/patch-fault protection, board fit/harnesses,
and measured rail current. These are declared design/bench gates, not invented
measurements. No tracker or external communication was made by this worker. The unmodified
manufacturer model contains inherited trailing spaces; these bytes are retained
for hash fidelity. Authored/generated files pass the whitespace check with that
one retained source excluded.
