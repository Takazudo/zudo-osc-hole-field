# Stage51 work record

Authorized target only: /F3/C945bba_SENSE, isolated R2316:2 to existing U2317:10 /
D2303:3 component. Fixed hardware, footprints, netlist, stackup and other retained
partitions must remain unchanged. Disposable copies only; no canonical adoption.
Stage50 exact-head CI39275001627 terminal success verified before new work; prior
issue/PR pending text reconciled. PR287 draft head8b204afe0e97d45fc3417ef2782ab005994698e1,
parent286 b58068fbaeb65886958a67a4f4978613414e31c5. Portable bootstrap already consumed.

Baseline .circuit-cache/stage49-fresh board SHA
05f85d8cb27dcbeec76327065e91526f0112ebc316054a1cec5cae5cbc80c441.
Read-only native dump confirms116opens,3925pads,30968tracks,2890vias; target
components50+1objects. Current canonical CAD and all earlier stages are untouched.
`pnpm circuit:check` before editing passes (manual68lines/0placements; no schematic
placement binding). Existing aggregate regeneration is supplied by exact-head CI;
canonical output regeneration is not repeated in this disposable scope.

Four conservative raster searches failed: B-only; local multilayer; wider window;
0.05mm wider search. All first failures retained. Continuous optimistic analysis
has nonempty candidate pockets and touches the crop boundary: it cannot prove
impossibility. It ignores pours/drills/edges/rule areas and is not a routing pass.
An independent reviewer found a sub-grid ordinary0.6/0.3mm via pocket with a direct
0.2mm B escape. It is off-pad but intersects courtyards; assembly acceptance is not
inferred. Exact proposal preserved, no special via process selected.

First native candidate: one via,26tracks; F3 closes, but -12V splits1→3, total
opens116→117. Zero rule/parity errors,476warnings. Acceptance gate rejects the
unexpected -12V partition. This is a genuine failure, not waived by zero DRC errors.
In2/F/B-only onward searches at0.1/0.05mm also fail. Seed-only diagnostic separates
new-via effects from the longer In3 track. No -12V repair or wider net rip-up has
been authorized or applied.

First replay-helper invocation from evidence/ failed ModuleNotFoundError because
its relative import root moved; repeated with explicit PYTHONPATH=. and the original
script bytes reproduces the proposal exactly. No geometry/threshold changed.
Native/heavy jobs use installed KiCad10.0.6 and the shared heavy guard; no Docker or
installation. No fabrication output, order, contact, energization, deployment or merge.

Seed-only native result116opens,477warnings,0rule/parity errors; every retained
partition/object preserved. Extra warning is the incomplete seed's dangling via.
Existing fill-guard search rejects full In3 path (fill_guard_disconnection), no
alternate route found. Independent reviewer confirms only -12V splits and proposes
local target-net layer bridges as next study, not implementation. No accepted repair.
First audit invocation failed absolute/relative command receipt matching; fixed the
caller path to match original recorded command, preserving strict validation.

18 focused tests pass normal/-O, no local skips; pnpm circuit:check/check pass.
Seven historical checkpoint and Stage41–50 manifest checks pass normal/-O.
Canonical JL SHA e984c0a01156b5f282f0c849077c61572df30ee0c70dfe6c9db94fbfcfe52107
unchanged. Added portable review-binding control for final evidence. Fresh review
requested after baseline receipt hardening; unused settlement code removed.
Final 19 focused tests pass normal/-O independently and locally, no skips. Native
rejected-audit normal/-O replay passed. Reviewer noted --check wrote evidence before
comparison; changed it to compare retained bytes read-only and reject drift. Latest
optimized audit replay and final delta review follow that change.
