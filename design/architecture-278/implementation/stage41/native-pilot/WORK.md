# Stage41 bounded native pilot work note

Parent-authorized continuation from unchanged Stage40 head `977c657a244fa4e80f6eefbb8eb15acc78453799`. Keep parent286, all historical stages, fixed front/foreign footprints and canonical manufacturing outputs unchanged. Develop only a disposable B1 output-amplifier/feedback and both bypass-return routing pilot. Never adopt architecture or broaden into unrelated circuitry. Native checks use the recovered official exact-release KiCad 10.0.6 through the repository wrapper and real machine-wide heavy guard.

The first trials and earlier Docker failure are retained in the ignored native-capability directory and the earlier evidence archive. The 15-package trial failed 22 native errors/149 open edges; native connectivity propagation also reassigned two retained −12 V segments and one via to C3101's signal net. These are real failures, not hidden by a renamed net or updated expected result. Exact upstream 10.0.6 connectivity source propagates pad-origin net identities to changeable copper, explaining why a track/via-net gate is necessary in addition to DRC.

Current scope is U3102, C3101/2/3/6/7 and R3105..R3113. Moving the complete U3102 package disturbs 14 exact terminal nets, including its links to retained D3101/R3104 and U3103. Those package positions stay fixed, but their explicitly named terminal-net copper is retired and must fully reconnect. Other input/indicator copper is preserved. All 14 nets were connected in the untouched native baseline.

The initial corrected trial retains R3109's native pose, moves the U3102/C3106/C3107 cluster +0.2 mm Y, and shifts C3101 +2 mm X relative to Stage40. Complete raw/native object-net identity checks pass through native DRC/refill; one new courtyard error remains against fixed J209. Revision2 reduces C3101's shift to +1 mm X. B2 translation and whole-cell integration are not inferred from this B1 trial.

New source guards compare every copper occurrence's geometry/UUID/net, all numbered pad identities/nets, all zone definitions/nets, rule-area bytes, all other board objects and every prepared/foreign footprint definition. Native-memory checks run immediately after load, after pose changes/save and around connectivity recalculation. Explicit route additions need reviewed net/geometry identities and new UUIDs. An observed three-object net-propagation fixture and mocked-native checks regress the original failure. Ten focused tests pass in normal and optimized Python at this checkpoint.

Routing proposals are bounded and additive. Signal search includes exactly the 14 disturbed nets on F.Cu/In2.Cu/B.Cu, preserving other copper. Power geometry includes two IC-to-capacitor supply links and four local fanouts: two supply-plane fanouts and both distinct capacitor AGND returns. Stub lengths do not establish closed loop length, inductance or electrical performance. Native DRC, intended plane contact, settled/fresh complete connectivity and no unrelated changes remain mandatory.

Before edits, `pnpm circuit:check` passed at its unchanged manual 68-line inventory scope (no schematic/placement binding). Final checks, native result and independent review will be recorded after the last substantive change. No accepted pilot is claimed by this work note.

Revision2 native placement: zero DRC errors, zero parity issues, 149 open edges and 479 warnings; full raw/native net identities, prepared/foreign footprint bytes, outline/setup and 123 rule-area bytes survive refill/reload. All 14 intentionally disturbed terminal nets require reconnection before viability.

The first exact local-branch inspection rejected removing a positive-supply via because it also contacts retained In2.Cu rail track `1469e03d-eb79-5b5c-92d0-c7ed41dea028`. The failed inspection is retained. Positive-supply anchor vias are now preserved; only owned leaf tracks are proposed for cleanup. The separate negative branch has two leaf tracks and one via, with no outside copper/pad contacts. Any cut still requires native replacement connections and full retained-connectivity equality; the source contact screen alone is not acceptance.

### Complete connectivity and routing continuation

- Occurrence-aware native baseline snapshot: 37,346 pad/copper objects, 117 native open edges; exact raw/native net guard passed. Stable copper keys include geometry, avoiding collapse of the 11 duplicate UUID pairs.
- Power candidate after refill: zero errors, 479 warnings, 145 opens, zero parity issues; complete retained net/geometry/foreign footprint checks passed. This is intermediate, not acceptance.
- Local supply branch screen rejected the initial positive-via removal because it touches retained In2.Cu rail copper. Revised proposal preserves both positive via anchors and considers only two positive leaf tracks and the three negative branch objects. No cut has been applied.
- Routing trials preserve first failures: 0.075 mm grid left five links; 0.025 mm left three; 0.05 mm found all 28 links over 14 nets, proposing 591 objects. Clearance, width, allowed layers and retained copper remained unchanged. Search success is not native acceptance.
- Independent source review of occurrence-aware connectivity, pure acceptance and narrower branch screen found no blocker; requested exact snapshot bindings and explicit deltas at integration. Added a bound comparison command and fail-closed consistency checks for empty components/declared open counts. These later changes still require review.

### Review fixes and first completed native candidate

The final source review found and closed two fail-open ledger cases: an empty/partial power-path manifest could previously pass; and local retirement UUID/net metadata was not bound to its raw hash. The power verifier now requires exactly six specified paths and consumes all ten audited power objects. All retirements now bind hash, original top-level occurrence index, kind, UUID and net. A malicious hash substitution or shared positive-via retirement is rejected by regressions.

The first attempted zone-filtered `IsConnectedOnLayer(via, layer, [PCB_ZONE_T])` call failed with the actual SWIG `std::initializer_list<KICAD_T>` conversion TypeError. Its source/log remain retained. The replacement requires a native connected filled-zone UUID, a native intended-layer connection and no touching non-zone object on that layer. It is conservative and successfully verified all four fanouts. No binary/config/rule change was used.

The new retirement-mismatch regression initially indexed the `top_level_spans` generator and failed with `TypeError: 'generator' object is not subscriptable`. The fixture now materializes the generator; the production guard was unchanged. Final focused coverage subsequently reached31 tests, normal and optimized PASS.

First cleaned candidate native result: zero reported error-level violations, zero parity,117 opens,476 reported warnings. Full retained partitions equal baseline; all14 disturbed nets closed; no new-only islands. Native inventory37,408 versus baseline37,346, exactly601 added minus539 retired. Board SHA256 `9fbdb51c891ee21abfe0c4242baf5b789aee05fd1a7403464d2ddd54aec4fcef`. Both positive anchor vias stay.

Warning comparison exposed a reporting boundary: silk_overlap and silk_over_copper are capped at199. Reported UUID samples change; source confirms the cap but not the exact cause of this observed sample variability. No exhaustive silkscreen nonregression claim is made. Uncapped warning comparison removes only one old dangling private-net segment warning (`f47846ba-e788-5f23-90ab-f319dc9e3f3e`), with no new uncapped warning. The recorded476 is a truncated reported total, not a full-board pass or a count of all physical defects.

Local `pnpm circuit:check` and `pnpm check` pass. Circuit scope: manual inventory68 lines, no schematic/placement binding, pin-asset check performed. Retained Stage40 tests8normal/8optimized pass; all seven historical checkpoint bindings pass normal/-O. Full historical replay remains delegated to the existing exact-head CI budget, not duplicated locally. Repeated/fresh native settlement and final artifact review are recorded separately when complete.

### Completed native settlement

Three sequential cleaned-candidate passes and a separately copied/reloaded/refilled fresh candidate all pass exact identity, all14 target-net closure, full retained partition equality,117 baseline opens and all six required power paths. Every candidate has the same SHA256 `9fbdb51c891ee21abfe0c4242baf5b789aee05fd1a7403464d2ddd54aec4fcef`. Native error-level/parity counts are zero. The final three-pass/fresh driver completed under the guard in535s. `settlement.py` normal and optimized outputs are byte-identical; `metrics.py` normal/optimized outputs are also byte-identical.

Final collector review additionally bound every pass's audit to the current preparation receipt/canonical baseline and rejects additional capped warning categories. Focused suite33tests passes normal and optimized. The final independent artifact review follows these substantive fixes and native results. This accepts only a bounded native electrical/connectivity pilot;117 known opens, capped silk warnings and physical/electrical qualification remain unresolved. No canonical/historical tracked file has changed.
