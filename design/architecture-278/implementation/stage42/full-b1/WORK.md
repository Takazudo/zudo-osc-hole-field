# Stage42 work record

Starting head b133738065e8c013dbdc0a3a8afde6bff68d43d9; existing executor usable.
No bootstrap rerun or replacement executor. Read repository workflow, current PR
head and latest Issue278 comments; no competing active implementation found.

Before modifying any disposable board: attributed all117 baseline opens using
complete bound native snapshots. Both canonical baseline and Stage41:103foreign,
14sharedAGND,0directB1. All115B1pads/33nets represented. Source-only independent
review and8normal/8optimized tests pass; retained as SOURCE-REVIEW.md.

Initial native approval was rejected twice because the approval reviewer still
applied the Stage35 source-only prohibition. No workaround used. Owner then
explicitly replied ok to the disposable KiCad routing/connectivity/DRC/refill/save
request; the supplied transcript authorization was accepted by automatic review.
All subsequent native work uses the existing exact-release10.0.6 tool through
scripts/kicad/run.sh and the required shared heavy guard.

First authorized command failed because the preparation script had been archived
during the blocked handoff. Restored it; next run rejected U3101.12 NC as a
private routing net. Fixed by excluding only source-bound NC equivalence entries.
Both failures and driver/source versions retained in .circuit-cache/stage42.

Full31electronics preparation retires779exact private copper occurrences on24nets;
fixed5panel packages and all foreign/shared copper initially unchanged. Added
exact-reference-set and pre-load bound_retirements guards following independent
review; reviewer independently verified all779current records against canonical.
No existing Stage41 scripts/evidence modified.

First native placement: identity/foreign-byte gates pass before and after refill;
6rail-clearance errors,178opens,0parity. Repair trial shifts U3101/C3104/C3105 rigidly
-0.2mmY; D3102-0.4mmY; R3103-0.1mmY; R3104-0.3mmX. This clears6rail errors but
introduces one R3104/D3101courtyard overlap. Second repair additionally shifts
R3104-0.6mmY. Retain all failed boards and reports; do not count guard exit0 as
DRC acceptance. Stage41 corrected15poses remain unchanged.

Power candidate code extends the exact-native geometry screen to all6bypass
capacitors/3ICs, requiring18paths/30objects. Signal search remains additive for24
private nets. These are proposals pending execution and native acceptance.

No B2 replication, canonical manufacturing changes, owner architecture adoption,
energization, fabrication, order, release, deployment or merge.

Revision2 still has3errors: R3104/D3101 and R3104/R3103courtyards plus0.2438mm railclearance. Explicit power placement gate rejects it before routing. A native-shape search of1681positions on0.25mm grid in10x10mm neighborhood finds20passing necessary screens; nearestR3104native(112.75,187.5), unchangedBface/90degrees,5.618051mm fromStage40. Full native verification of this revision3 is pending. No claim of global optimality or physical fit.

Revision3 placement passes0error-level rule violations/0parity with178deliberately
unrouted items; identity before/after native save passes. All15Stage41poses are
exactly equal. Power proposal produces18paths/30objects; native DRC passes0rule
errors/0parity and reports166opens. This is not completed connectivity. Supply
fanout lengths vary1.0..2.0mm in this full-cell geometry; earlier Stage41 fanouts
are not silently treated as unchanged. Source power verifier requires all18paths;
5normal/5optimized manifest tests reject old-subset, omitted/duplicate, wrong-pin,
wrong-plane and wrong-geometry receipts. Final native plane proof pending.

Signal search includes24private nets plus+12V/-12V/+5V (baseline complete) to
restore moved B1 supply pads. SharedAGND14foreign openings are not routing targets.
The full occurrence-aware identity/partition gate remains mandatory; same open
count alone is not acceptance. No foreign rip-up permitted.

Routing first.05trial:48/49links,1117objects, R3104.2 input-sense unresolved.
Coarse.075:8unresolved;fine.025:5unresolved. All retained. Prioritizing exact
input-sense netX24465B284FC5581E6283 at.05resolves49/49links,1131objects, no rip.
Complete native audit/refill/DRC/connectivity/power verification in progress;
raster search is not native acceptance. Widths/clearances/vias unchanged.


The first fully routed native candidate has0error-level rule violations/0parity,
117baseline opens, all24private nets closed and complete retained partition
equality.18power paths/12plane fanouts pass after correcting the verifier's
PAD.GetLayer() assumption for rearSMD pads; footprint face plus pad membership is
now checked. The initial failure and source version are preserved. Six power
regressions pass normal/-O. Native geometry did not change for this checker fix.

It introduces10dangling old supply leaves (13reported track warnings versus4
baseline, with one retired old private warning). Read-only native contact proof
selects15old tracks/six local vias; retains4shared/reused anchors. Two new route
segments only reconnected an obsolete copper island and are withdrawn with it.
Initial proof missed current pad contacts; independent review caught this and
required zero current contacts plus exact31electronics eligibility. Updated proof
passes for all10branches. Via plane-center containment is only a necessary
screen; full post-removal connectivity partition equality remains mandatory.
Reviewer cleared the exact cleanup trial after these fixes. No copper was removed
before that review. Cleanup writes a fresh disposable copy only.

Source checks:67focused regressions normalPASS; all7historical bindings normal/-O
PASS. pnpm circuit:check and pnpm check PASS. Circuit inventory scope remains
manual68lines/0declaredplacements, no schematic/placement binding, pin-asset check
performed. Full historical replay remains bounded by existing exact-head CI.

Cleanup first pass: all800retirements/1159additions exactly bound, retained
partitions equal,24private nets closed,117opens,18power paths/12plane fanoutsPASS.
Native0rule-error entries/0parity;10new track warnings cleared, one new
via_dangling on retained+5anchor a28dce6f-63f0-55fb-8804-d5ed11246b23.
Cause: both new approach and retained rail useIn2, leaving its layer transition
unused. Keep this first failure. No warning exemption and no shared-via removal.
Propose replacing only new ee856... approach with a new via at(133.8,202.5)mm
and B.Cu approach to unchangedanchor(134.9,201.4); native screen passes.
Full audit/DRC/partition/power checks pending.67tests alsoPASS optimized.

Anchor revision source review found no geometric/scope blocker; added fresh,
nonaliased disposable-output guards and an old-six-path settlement rejection.
Eight settlement regressions pass normal/-O. Shared via/rail unchanged.

Final repeated/fresh settlement: three complete native memberships plus a separately copied/reloaded/refilled candidate all PASS. Exact candidate SHA256 975cd15d5ba69b9695e8d32a575a289306a27f1ea17d6b5f7a5819071dc5505b. All24targets closed, retained partitions equal,117baseline opens,18power paths/12plane fanoutsPASS,0rule-error entries/0parity,no added uncapped warnings. Capped silk199/199 unresolved. Normal/optimized settlement output byte-identical.68focused tests PASS normal/-O. No canonical/historical modifications. Final fresh-context independent review follows this last substantive evidence update.
