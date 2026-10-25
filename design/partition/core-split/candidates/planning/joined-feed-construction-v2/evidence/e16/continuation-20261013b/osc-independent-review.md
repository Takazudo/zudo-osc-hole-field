# Independent source review — OSC E16 continuation

**Outcome:** No outstanding blocking findings in the assigned numerical refinement, materializer, replay/pilot mismatch guards, native request preparation or native admission paths. Initial high-priority admission and binding findings were corrected and re-reviewed at installed source commit **e215b9eb3f9695d74cd9dfc9de182e0882bebcd7**. This is source review, not native or electrical validation.

Repository: `/workspace/zudo-osc-hole-field`; comparison base `dd3ef71c7f411c55e9f6e9b29f9278b885a1d118` (PR260 integration branch).

Startup: manager reported canonical startup loader completed and entire stdout consumed; not rerun. Repository AGENTS.md and circuit/WORKFLOW.md read. Manager reported baseline circuit check PASS. Reviewer made no repository edits, commits, native calls or production/heavy runs; only this report was written in /tmp.

## Exact installed files reviewed

All paths below are relative to `design/partition/core-split/candidates/planning/joined-feed-construction-v2/`.

| File | SHA-256 |
| --- | --- |
| finite_solve.py | eb2472fd871b47b20a018ee241b5c0c16e4afc6dbb818baf4c6bbdbc8127d926 |
| test_refined_solve.py | d73e5d2640c7fb1cf396ff8cf9382ccf1633d689925f8d2079002db1752eacbd |
| materialize_e16.py | 3328edaca211fb4d42779b738a30790ac705cdfa8702d5269731d2258ebf624d |
| test_materialize_e16.py | decff036ac882fa7dd5258ee2fe48e49a687a9db9a3024ea4f9309482af59c2e |
| native_validation.py | 37c08a498e873c3b41489833d7a2253305a633134c9e84e562e75acb6bd16cfc |
| native_descriptor.py | 85992a6857a16fb1d2dbd53cf3d8f53936dcac86ec467702703544dc1d44149a |
| test_native_validation.py | 8c466feb80965b5ce98e4de01fea441295883bdab079e5939832c89953b1847d |
| pilot_construct.py | 85df4b08c8f3bca7f793eb0d1a64acc6a0fa00ee63b4372c4abd4bf39622a7d5 |
| test_pilot_authentication.py | 75e1514bbdcc3f3d911c51664af9ddd63298d39ef55f34ebe34f4c0eb2852b63 |
| compare_replay.py | 57f95655241fd84e91c869ca4b5c97babe294555da33e16aa474a09d9f5d2542 |
| test_compare_replay.py | d9b2c88b4dedddbe521043773ccb8a900abc6d7766217a1c68869498c0f80329 |

Also read existing `scripts/kicad/ci_native_admission.py`, `native_resource_guard.py` relevant APIs, `run.sh` relevant APIs, `scripts/pcbgen/ratsnest.py`, constructor UUID/offset serialization, and retained original descriptor evidence. Final installed native_validation.py and test_native_validation.py byte-match the independently reviewed implementation-owner followup files.

## Findings and resolutions

**HIGH — resolved: internal native mode admission bypass.** Initially worker/native-fill/native-connectivity checked only caller-set worker/slice/deadline formats. Installed code checks parent authority before native import, compares the complete worker run ID/attempt/target, checks actual checkout HEAD, and proves actual host checks.service cgroup membership or readonly acknowledged container gate provenance plus memory/swap caps. Native modes cannot reach pcbnew import with the initial environment-string-only bypass.

**HIGH — resolved: exact candidate request was not parent-bound.** Initially request JSON/manifest/staged digests could be replaced together under the same checkout SHA. Installed execution requires separately parent-provided `EPIC242_PARENT_REQUEST_SHA256`, in addition to exact run ID, attempt, checkout SHA and reviewed hook. Preparation records the required variable and request digest but does not set approval or dispatch. Every native entry validates the same authority. Approved values are explicitly forwarded through the existing systemd worker and Docker command boundaries.

**MEDIUM — resolved: incomplete original/staged source seals.** Installed preparation verifies and stages all materializer input_sha256 files. Staged graph and materializer input maps must exactly match original declared seal sets and hashes. Source/project/rule/board/graph/pad-map and manifest seals are checked, closing the originally observed preparation-time copied-input binding gap.

**MEDIUM — resolved: rerun and worker identity ambiguity.** Installed request records one positive exact GitHub attempt; changed attempts are refused. Full worker identity must equal the approved run ID, exact attempt and selected target. Actual checkout HEAD is read in both host and native contexts before native import.

No remaining blocking finding identified in the assigned paths.

## Numerical refinement

CSR/CSC index reconstruction evaluates the original stored sparse matrix with extended products/sums; the existing LU and float64 solution representation remain. REFINE_STEPS remains 3. Best reported residual corresponds to the returned iterate. Narrow-longdouble platforms fail explicitly. Full coupled KCL/energy checks and their thresholds are unchanged. The final finite_solve.py includes separate device-service integration; its numerical helper is unchanged from the initial reviewed version. This review's numerical conclusions concern refinement, not independent sign-off of the full device-service implementation.

Scratch products are bounded to 65,536 sparse entries and extended node residual is allocated one RHS at a time. Retaining the best iterate adds one float64 solution-size array over the old helper. Production peak memory and production convergence remain NOT RUN; no production outcome is inferred from the analytic two-node fixture.

## Materializer and mismatch/replay guards

CLI candidate05 PCB and both retained delta byte hashes are checked. Full normalized content excluding explicitly documented run-local seals is locked. Additive identities are unique and cannot reuse source/native UUIDs. Original candidate text remains an exact prefix/suffix; [100,50] inverse coordinates and quoted UUID syntax agree with the existing constructor/canonical PCB. Standard through-vias retain all layers; unsupported selective stacks fail. Four solid-connection rail zones are unfilled source declarations. KB P1 requires a separately sealed three-segment path and a distinct output from t2.

Terminal followup verifies terminals.json against the retained E16 index, requires six terminal records with 25 vias each, seals terminal/index inputs and records terminal_process_requirements. Process metadata remains evidence, not manufacturing qualification.

Replay guards reject equal-count identity swaps, altered base copper with unchanged connectivity, rewritten prior objects, reused/cross-span identities, missing/unproduced deltas, newly disconnected pads and non-exact legacy allowances. Pilot construction authenticates source, planes, graph, census, preflight and independent review bytes before work and rechecks input seals afterwards.

## Native packet and census

Preparation requires all three exact targets KA-t2, KB-t2 and KB-p1, separate sources and graphs, exact board/project/rule sidecars, complete rail/AGND physical pad maps and six feed anchors. Source graph normalized-caps input is compared against the materializer recipe. Targets remain separate.

Native fill, full-severity CLI DRC without refill, and connectivity are distinct processes. Phase receipts hash commands/inputs/outputs and link exact prior outputs to subsequent inputs. DRC and census must preserve the identical filled PCB and original project/rule sidecars. Existing reviewed resource guards are unchanged and retain worker caps, single-use identity and cleanup ownership; the new code also requires active resource/gate provenance before native import.

Complete native all-net cluster open counts are sum-checked against the full ratsnest using the existing project method. Rail/AGND census checks every original native UUID/ref/pad/net. Source/native peer and feed disagreements are retained explicitly. Phase completion never sets accepted:true or grants electrical/manufacturing sign-off.

## Verification and limitations

Installed source commit e215b9eb3f9695d74cd9dfc9de182e0882bebcd7:

`/workspace/osc-venv/bin/python -m unittest test_refined_solve test_materialize_e16 test_native_validation test_pilot_authentication test_compare_replay`

**41 tests PASS in 0.233 seconds** (3 numerical, 9 materializer, 16 native source-only, 1 pilot authentication, 12 replay). Tests were read before execution. Native tests use fixtures/mocks and perform no pcbnew import, Docker calls or actual admission. Expected negative replay CLI output is part of passing tests.

`git diff --quiet dd3ef71c7f411c55e9f6e9b29f9278b885a1d118 -- boards design/grid/placements.lock.json design/partition/core-split/decision.json scripts/kicad/run.sh scripts/kicad/ci_native_admission.py scripts/kicad/native_resource_guard.py scripts/kicad/pin.env` exited **0**: canonical tracked boards/decision/placements and existing native guards/oracle pins unchanged from base.

**Native status: NOT RUN / NOT ADMITTED.** Actual KiCad parse/fill/DRC/connectivity, live host/container provenance, production finite solve/convergence/peak memory, physical process and electrical qualification remain unverified. Full project suite is owned by manager and was not repeated by this reviewer. Zero execution authority granted; no source-only result counts as native or hardware acceptance.
