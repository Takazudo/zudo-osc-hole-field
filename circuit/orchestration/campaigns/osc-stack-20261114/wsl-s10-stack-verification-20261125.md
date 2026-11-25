# S10 stack verification on WSL

## Inputs and commands

Pre-S10 reference `6e5716e7fc011e2f028982f645d18b8d802acb29` was checked out separately. The first inventory ran `python3 -m unittest -v MODULE` from each module directory for the non-study, non-trimmer stack tests and the separately named `links_gate_c6_test`. Five modules could not import NumPy or Shapely under the system Python. Those import errors provide no engineering verdict. The second run used `/tmp/osc-s10-numeric/bin/python` with repository-pinned NumPy 2.2.6, SciPy 1.15.3 and Shapely 2.1.2. It repeated the five modules on that same reference. Both numerical library thread limits were one. The shared heavy guard serialized numerical suites, with a user scope limited to one CPU, 3 GiB memory, no swap and 64 tasks. Each module had a 300 s wall-time ceiling; the baseline group had a 1530 s guard ceiling, and the current group 1250 s.

Exact baseline invocations from their respective directories were `python -m unittest -v test_fixings`, `test_procedure`, `test_link_electrical`, `test_stack_mechanics`, and `links_gate_c6_test` using the pinned interpreter above. Fixings passed 16/16, threading procedure 24/24, electrical 57/57 and c6 5/5. Mechanics passed 72/76. This run took 62 s under the guard and exited 1 on assertions. The initial baseline's 101 geometry-link tests (238 s) and 54 stack-geometry tests (31 s) passed. No additional unchanged full geometric replay was needed to identify these failures.

The targeted old/current comparison also used the same numerical interpreter for power-post, sub-toggle and thermal failure cases. Current checks began at `9e6e2fc3`. A later run at the regenerated-gate checkpoint verified the changed placement consumers. The S7 Revision 14 report described older revisions and sometimes pytest subtest counts; its failure count is historical.

## Reproduced failures

| Area | Test and result | Relevance |
| --- | --- | --- |
| Mechanics | `TestAttemptA3.test_pins_are_current` fails on S-GEOM, `TestReviewFindings.test_f2_candidate_hash_is_recorded_and_current` expects `9bd03493…` versus actual `22e817ea…`, `TestGeometry.test_geometry_block_is_current` derives a different geometry block, and `TestTerms.test_repository_sources_unchanged` fails on S-PART. | Reconcile the stage's retained geometry with the live partition/candidate before claiming current mechanical evidence. Both historical README rendering tests passed on the pinned baseline interpreter. |
| Power posts | `AttemptA2.test_repository_sources_are_current` fails on S-PART, S-P35, S-SUPPLY, S-SUPPLY-PAGE and S-GEOM. `Reproduction.test_present_shares_match_partition` computes 0.4817939293140001 A versus 0.4771714782527333 A. | A current-share discrepancy requires engineering review of inputs and model. Preserve the accepted current budget. |
| Sub-toggle | `TestSpecFile.test_spec_matches_generator` differs only in seven `inputs_sha256_at_launch` fields. The live renderer rehashes changed IO partition code, oscillator report, component inventory and four TI facts. | A historical provenance repair can source launch bytes at `78246cf0`; the retained Dailywell facts hash belongs to `59d7e03b`. Verify acquisition lineage before changing this separate contract. |
| Thermal | `Screen.test_inputs_and_pins_match_the_repository` reports a stored-input mismatch plus 11 stale pins covering load/rail cases, packages, assignment/boards, floorplan and gate figures. | Thermal and supply projections require review against the correct source. An identical failing test on two SHAs does not establish equal figures. |
| Historical D4309 | On both revisions, `python -m unittest scripts.checks.test_partition35_evicted_cap.EmittedD4309.test_d4309_is_within_the_cap_or_reported` fails because the JR eviction list omits D4309. The test stops before comparing its distance. | Determine whether eviction is still expected and reconcile the placement contract. |
| Trimmers | The separate continuation `test_trimmers` run passed all 14 cases. | The previously reported S7-R14 failure in this module cannot be described as a current failure solely on historical evidence. |

The power-post, sub-toggle, thermal and D4309 failures reproduced at both pre-S10 and the continuation. No failing assertion was removed or marked expected. S7-R14 item 7 directed the original report to identify existing failures. It did not waive the current PR gates. The current-test CI discovery includes these files, and none is in the repository's frozen-study registry. For a PR carrying this inherited source, the failures remain integration holds until corrected or formally dispositioned under repository policy. The S10 study remains separately returned on geometry and locality grounds.

## Current matched results

The final numerical run started and ended at `557b5a6e92e2600fcb4319bd8528c4f5812d3177`. In the test directories, the pinned interpreter ran `-m unittest -v test_procedure` (24/24 PASS), `test_link_electrical` (57/57 PASS), the four named mechanics failures above (0/4 PASS, same assertion causes as baseline), and `links_gate_c6_test` (5/5 PASS). It ran for 22 s after waiting for the shared slot. Guard verdict FAIL, exit 1, minimum available memory 10471 MiB. No timeout. The unchanged fixings suite and the 72 passing baseline mechanics methods were not repeated. In addition, `python -m unittest test_gate_a_open_items test_link_era_replacements` passed 15/15 after the producer regenerated the embedded gate. That geometry was committed at `4c0ec4aaa0a3753cc03135b2f3360bd73e219557`. These checks include rejection of missing evidence, new unaccounted open rows, and stale or injected placements.

Local raw log hashes (SHA-256) for reproducibility:

- Original stack baseline `/tmp/osc-s10-stack-baseline.log`, `c5d118305e30e3780bf5a0ac576d7ce2c208bc63c0335ab8182a7b1dbb573a35`.
- Baseline with pinned dependencies `/tmp/osc-s10-matched-baseline.log`, `f486c8c8cacaf24da05610b04a5e35d7b7938e292128b42b1dcf59879f24a3cb`.
- Matched power-post/sub-toggle/thermal cases `/tmp/osc-s10-matched-base-prior.log`, `6f3fb1980c2c77ab50d0463de6c2c02d4b532af7eceda8a5bd89d475899aa19a`, and `/tmp/osc-s10-matched-current-prior.log`, `88d04c50ec844024853ed02a03658f5ad825629b112e2c26369907c94e757c0c`.
- Final numerical group `/tmp/osc-s10-matched-current.log`, `7eed04af23c4da3ef2db4f44e0c069d8251af3c4c0de7cf73186516cd4aae099`.

Disposition: preserve the specific passes and failures above. No whole-stack success, independent stage acceptance, Gate A acceptance or hardware qualification follows from these runs.
