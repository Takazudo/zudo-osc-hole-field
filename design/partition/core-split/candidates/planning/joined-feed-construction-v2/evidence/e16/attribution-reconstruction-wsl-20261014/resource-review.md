# Independent reconstruction resource and admission review

Reviewer: `/root/resource_review`, independent of implementation. This is source/report-readiness review, not numerical authorization. No production pickle was opened; no reconstruction, factorization, numerical profiling, native work, approval or reservation was performed. Only this temporary review and inventory were written.

## Verified intake and current state

`resource-inventory.json` contains exact paths, observed sizes, independent expected hashes and observed hashes for all 135 attempt-5 external solver artifacts and all 60 original-request-bound +12V input paths. All match. Solver artifact sizes also match their independent index: 844,803,369 bytes. The 60 input files total 271,065,269 observed bytes; their historical request provides independent hashes but not independent size fields. That distinction is retained explicitly, not filled with self-generated expected sizes.

The compressed request hash is `3ac6356762419c653c8949adb1c2d12db58e109408d52246ef482e9a398adc54`; decompressed original bytes independently hash to `ef0213b3b38f4de23804ad192043b082d8e1b2be3086c5e20e4343afea4052d6`. These are different bindings and neither is rewritten.

Durable campaign ledger SHA256 `94aafb6d13f754fdbde718a5b44c5071d946897e798a8eebf1cd4b86c0731ffb` still records COMPLETE, live_owned_work=false, 2/3 full baselines, 8/24 diagnostics. Process/systemd and lock inspection found no matching live solver/native workload or held E16/heavy lock. Persistent slot files alone do not establish a reservation. One historical failed memory-probe scope remains inactive. The separate native negative-control packet still contains only request.json. There was no ledger mutation or owned workload to clean up.

## Exact artifact and ownership distinction

The retained reductions contain full interface basis Y and simultaneous-load u0, plus free-node mapping and small Schur quantities. Driving-point files contain scalar e and terminal q projections, not selected interior fields. The selected KB observation therefore requires one selected RHS solve; the other board uses retained Y under the selected coupled terminal solution. Do not substitute simultaneous-load u0/g or reconstruct another loaded field inside this one-RHS scope.

Original +12V mesh provenance is present and hash-matched: 11 mesh chunks per board. KA has 1,555 tiles, 1,736,692 unique vertices, 1,515,457 nodes, and 1,710 ring nodes. KB has 1,352 tiles, 1,730,062 unique vertices, 1,541,278 nodes, and 1,458 ring nodes. Each board has one +12V terminal.

Serialized operators discard Assembly.group, xy, vertex_node, node_xy and original mesh items. They retain Kg_face/Kg_inner, rings, supports, support_inside and N. Exact map recovery must reproduce the original lexicographic `(group, rint(xy*SCALE))` union, bore-boundary predicate and ring-collapse order, then verify N, ring IDs, all UUID-to-node/weight/interior mappings and summed stiffness against retained operators. Member lists are provenance, not overlapping energy shares. Missing original Assembly fields are a concrete required operation, not evidence that the original mesh bytes are absent.

## Resource review

Historical receipts, not new performance measurements:

| Original operation | Elapsed seconds | Peak KiB |
| --- | ---: | ---: |
| KA Assembly | 33.83 | 1,025,916 |
| KB Assembly | 45.04 | 1,034,700 |
| KA reduction | 27.44 | 1,625,624 |
| KB reduction | 30.65 | 1,673,712 |
| KB 96-pad driving-point unit | 68.52 | 1,322,132 |

The three coupled reduction/driving-point resource receipt files were checked against independent retained index sizes/hashes. Finite Assembly receipt hashes match the original request. KB factorization was 3.36 seconds with 21,002,074 L+U entries. Separate historical operation costs do not establish a bound on the new combined operation, and cannot be summed as a measured new runtime.

A full long-double board vector costs 23.12 MiB KA / 23.52 MiB KB. One retained Y has one column. A three-int64 unique-coordinate key table costs about 39.75/39.60 MiB; a vertex-to-node int64 map about 13.25/13.20 MiB. Sorting/uniqueness workspaces, raw chunk coordinates, sparse operators, factorization, long-double residual scratch and output rows are additional. Existing `pload` holds compressed bytes plus decompressed pickle bytes while constructing Python/numpy objects; a production lifetime plan must address this peak.

Every following operation belongs inside the single admitted guarded interval, including operations previously described as preparation:

1. Verify bound input bytes; bounded decompression and selected retained artifact loading.
2. Recover original per-board coordinate/ring/support mappings from all original mesh chunks; verify original operators and provenance.
3. Build/factor the selected KB free operator, refine exactly one selected RHS using existing numerical conventions, retain selected vectors/projections and release factorization scratch.
4. Verify retained basis and reduced coupling, solve its small terminal system, and reconstruct KA/KB selected fields serially. No second loaded-field reconstruction is included.
5. Establish exact matrix/held-set/return-state-bound uniqueness with an independently reviewed checking method and evidence.
6. Stream every local union tile and physical barrel interval, reconcile complete per-board partition/operator/current arrays, and charge live wire bulk once. Removed wires preserve original end terminations.
7. Reconcile free/global KCL, original class energies, source reactions, selected load work and normalization using unchanged tolerances.
8. Serialize/hash bounded deterministic output and terminal/resource receipts; remove only owned temporary files/processes. Output budget includes all emitted files, not only component rows.

The proposed180s/2GiB/no-swap/64MiB one-attempt ceiling is neither demonstrated feasible nor proved impossible. An implementation may reduce live memory by separating LU lifetime from map recovery/accounting, using one board at a time and streaming mesh chunks. The full combined cost still needs an exact executable operation plan and appropriate qualification/admission; no expensive step may be moved outside the guard to make the packet appear to fit.

## New source boundary review

Reviewed `attribution_reconstruction.py` SHA256 `ffaf262190eee8c7af1fd4edc75bec35c43161ecd8ed36465f0775ec43ae4ae2` (source may receive subsequent numerical review edits, which require a delta review).

`reconstruct_fixture` rejects combined KA+KB+terminal order above256 before constructing full matrices or factoring. `recover_fixture_assembly` rejects operator N above256 and raw mesh vertices above4096 before Assembly sorting/concatenation. There is no production artifact loader, execution command, authority switch or scheduler. Its report explicitly identifies TINY_SOURCE_FIXTURE_ONLY. These are legitimate source-test bounds, not a physical impossibility theorem about the real model.

`copper_stream` yields local matrices using structured coordinate lookup and original ring mapping. `PatternSum` retains one board CSR copy and one long-double value per reference nnz; local mapping/searches are tile-sized. `account_copper` retains one shared board current vector instead of a full board temporary per component. It exhausts its iterator before returning accounting, rejecting missing terminal items and duplicate IDs/physical ownership. Its resource lifecycle still includes AssemblyMap argsort/unique scratch, PatternSum reference-copy and relative-error temporary, the one original-operator application, current arrays, Python identity sets and result rows.

`fixture_report` intentionally materializes the local-component list and full embedded reporter matrices, but only after the tiny-node gate, for parity with PR275. Its synthetic self-binding is not independent production provenance. This is acceptable bounded B0 parity scaffolding and must not be exposed as a production-scale executor by raising the ceiling. The per-board accounting output cap is not an aggregate production output quota; the final fixture result has its own check. No resource-boundary finding blocks these source fixtures. Numerical correctness is a separate independent review.

## Exact production blockers and next reviewable work

1. No independent positivity/uniqueness receipt was found. Recorded SuperLU success, residuals, L+U counts and graph connectivity do not certify the exact free operator. Certifying both exact Af blocks plus the exact coupled Schur G is a valid possible block proof, but those factor/inertia/backward-error checks and their evidence are not retained. G positivity alone is insufficient. A different proof based on validated local PSD operators and the complete constraint nullspace would itself need explicit reviewed evidence; connectivity alone cannot replace it.
2. There is no admitted complete production executor for map recovery + selected solve + accounting. The historical `/tmp/osc-wsl-20261013/execute_unit_guard_numerical.py` hardcodes maximum_units==148 and the old controller command shape. It cannot execute a relabeled one-unit packet. Reuse of shared guard/lifecycle conventions is appropriate, but adding the precise one-unit execution operation requires a source-owned reviewed implementation, not a claimed ready request.
3. Combined operation cost is unmeasured and its complete live-object/phase plan remains unqualified for180s/2GiB. This is an explicit resource/admission blocker, not lack of retained mesh bytes.
4. Genuine applicable authorization and exclusive reservation are absent. Historical standing delegation concerns diagnosed correctness corrections in the terminated baseline campaign; it does not automatically authorize this new attribution experiment. The unrelated native negative-control lane supplies no authority here.

Next executable source-only work is the focused E16 regression command using the retained numerical Python. Production execution has no truthful ready command yet. A future command must name the implemented exact one-unit executor and immutable request after the blockers above are resolved; inventing its digest or calling B1 ready would be false.

Broad source discovery currently excludes exactly `PrecisionVendorSweepGate.test_original_network_returns_nonzero_for_supported_failure` twice, through design/spec and design/spec/cells. Preserve this selector; do not let broad tests dispatch the native oracle. Aggregate regeneration/native/production work was NOT RUN in this review.

B0: fixture/resource-boundary source review complete at the pinned module hash; numerical review and final tests remain separate. B1: NOT ADMITTED / NOT RUN. C: NOT RUN. This review is not authorization and creates no reservation or campaign consumption.

## Final resource-boundary delta review

Independent final review observed at 2026-10-14T07:43:23.901402+00:00.

The source now checks actual sparse shapes/nnz, support/barrel counts and per-support storage, plus Assembly/item/vertex/entry/plan bounds before the fixture full matrices or factorization. The node ceiling cannot hide a sparse operator with a larger shape or an oversized duplicate-entry payload. `account_copper` now enforces the complete-node current difference at the unchanged1e-9 tolerance using the selected excitation current, rather than merely returning that discrepancy for a caller to check.

The new readiness CLI parses the actual `finite_units.assemble` saved-operator dictionary using Python AST without executing it. It reads source and the compact experiment specification only, reports missing original mapping fields, emits a fresh optional report with exclusive creation, and exits2 with NOT_EXECUTABLE_NOT_ADMITTED. It creates no execution request or production command; their fields remain null. The readiness report digest must never be relabeled an execution-request digest. No production loader, reconstruction, scheduling or approval pathway was added.

Independently ran the source-fixture command `/home/takazudo/.cache/zudo-e16-numerical-venv/bin/python -m unittest test_attribution_reconstruction test_resistance_attribution` from E16:54 tests PASS in1.584s (20 bridge +34 existing reporter). This is source-fixture evidence only. No production work occurred.

Final exact reviewed source/test SHA256 values:

| File | SHA256 |
| --- | --- |
| attribution_reconstruction.py | `130ba2af686912f1ab18713fff6a86b3275a89043080ea14e6356bbf81aa6b19` |
| test_attribution_reconstruction.py | `9d7735bd8eadefe913dde5672adbc0a193b0e301627ce201f2451f895125b5ed` |
| resistance_attribution.py | `67c9735f1519b49e69cab61dfaea8947d5f7d9838185cce7f87eca0070deca70` |
| test_resistance_attribution.py | `fb0630b0b226f94654087a8e1e1ac059dc8845ed68a615cbcf48b0a8dd468848` |
| finite_units.py | `4b7d02381a98a3f006394b0bb5988503c5fc3122c39fede3dfaecfd8fb153ffc` |
| finite_adapter.py | `f313a87719aba83b169a363c05d36daa5c79cd28ad41620e5d45c5d8eca613f4` |
| finite_solve.py | `20b1b9e1e7ba8653d3268c4956dc5415b91670e23f07e35ab381d2091f84b044` |
| numerical_unit_guard.py | `513efaf0b4f4a5bb1f94c15190822a2a79d84df399f83e69d7ed0297444ea571` |

Post-test ledger SHA256 remains `94aafb6d13f754fdbde718a5b44c5071d946897e798a8eebf1cd4b86c0731ffb`; activity=COMPLETE: bounded campaign terminal, reviewed and published; no live owned numerical work; live_owned_work=false. Budget remains {"full_baseline_limit": 3, "full_baseline_used": 2, "production_diagnostic_limit": 24, "production_diagnostic_used": 8}. Thus this delta consumed no baseline or diagnostic.

Disposition: no blocking resource/admission-boundary finding for the bounded B0 source implementation at these hashes. The full real operation remains unimplemented/unqualified and NOT ADMITTED: independently certified exact Af/G positivity is absent; no complete admitted production executor exists; the combined original-map recovery + selected solve + complete accounting/uniqueness/hash/output lifetime has no established180s/2GiB bound. Tiny-fixture limits do not prove physical impossibility. B1 and C remain NOT RUN. This is review, not authorization.

## Final handoff review: initial finding and verified comparison

Read README.md, resource-plan.md, readiness.json, checks/summary.json and retained-comparison.json in the new attribution-reconstruction-wsl-20261014 evidence directory. README and resource plan correctly separate bounded B0 fixtures from incomplete production bridge/B1 and C NOT RUN. The complete operation plan includes artifact decompression/loading, original map sorting/ring recovery, selected factor/refinement, basis/Schur checking, independent uniqueness, serialized field reconstruction, full partition/current/energy accounting, in-guard hashing, aggregate output and cleanup. It preserves the exact KB U7105.4 +12V nominal/all-present target, three held sources, one RHS and original caps. Historical separate costs and tiny bounds are not presented as either a production-fit proof or impossibility proof.

Independently verified retained-comparison.json directly against original hash-bound JSON/GZIP and attempt5/index.json: exact source39146bytes, SHA256 b6b6b8928fe77619202f9d323d44b5f04a784435134be8ebb152b24d68e7b96d; selected pad e97b2d02-463a-5a6d-ab37-748ce29d7cf8 in all-present.driving_point.KB; total0.0071730985235579775ohm and copper0.0059921452927738485ohm; original operator/reduction/config/method/service bindings all match. Separate selected loaded potential and board/class watts exactly match their distinct original fields. No physical interval attribution, second field reconstruction or new experiment comparison is claimed or performed. Ledger remains94aafb6d13f754fdbde718a5b44c5071d946897e798a8eebf1cd4b86c0731ffb.

Found one handoff inconsistency requiring correction: readiness.selected_experiment copied the predecessor's scope verbatim, including a second retained simultaneous-load reconstruction, and its decision_rule.reject_if classified incomplete conditions as mechanism rejection. Those conflict with the current user's narrower one-RHS scope and incomplete/inconclusive C outcome. Requested an explicit current-task projection/override in the readiness report, leaving the predecessor specification unchanged and preserving its provenance. Final disposition awaits the corrected report and source/test bindings below.

## Final handoff finding closure

The readiness scope inconsistency is resolved in source SHA256 `957c4a96e5e65275e4c66eee6282ae6c2c91eeb2d491933f6695a7889e0fb50a`, test SHA256 `6a428892d3f19f274d6e7efc59a8b8aa976396f563fab9936a2ad0d433530982`. Readiness now projects only the current exact selected identity, original held sources/via and unchanged bounds; selected current is explicitly1A, inherited loaded observation0.004A is omitted, simultaneous_load_reconstruction is false, and loaded comparison is limited to existing JSON watts without a second field solve/reconstruction. Complete adverse evidence rejects the mechanism; incomplete/unresolved evidence is explicitly inconclusive and cannot support the via. The predecessor specification remains unchanged and separately bound at SHA256 `a755d4558260f5e9e669855d6464a8d3f54c64cbae44a90ea9bed211aadf7383`.

Independently ran the changed readiness regression alone:1 test PASS in0.016s. The author reports57 focused tests PASS after this readiness-only delta; numerical implementation remains unchanged by this last correction. Earlier final296-test E16 and independent numerical57-test evidence bind the preceding numerical source; final evidence should retain their actual imported hashes and identify this subsequent readiness-only delta rather than imply a rerun. Broad1859 coverage is expressly intermediate, including20 bridge tests before3 added regressions; this limitation is disclosed accurately.

The final handoff cleanly reports B0 bounded bridge/source fixtures, B1 NOT_EXECUTABLE_NOT_ADMITTED with null execution-request digest and zero real diagnostic/ledger change, and C NOT RUN. It states the remaining production driver/independent uniqueness/combined-resource blockers concretely and supplies only truthful source/readiness commands. Resource phase completeness and selected unchanged geometry/caps are preserved. Retained comparison independently verified above remains valid. Ledger remains `94aafb6d13f754fdbde718a5b44c5071d946897e798a8eebf1cd4b86c0731ffb`.

Final disposition: no unresolved blocking source/resource/handoff review findings for this deliberately incomplete production checkpoint, subject to regenerated readiness and final source-hash evidence matching the final source above. Production bridge is NOT complete; this review is NOT authorization, a reservation or proof of real-model fit.

Regenerated readiness artifact independently re-read and hash-verified: `91b228c67d8a3ea062bb0732d05b46e498d9b55c0d10b07da8f3fb2821b602f6`. Its source/test bindings and corrected one-RHS scope match the final reviewed source. This closes the handoff scope finding. The author is rerunning the final296-test E16 suite to bind this readiness-only delta; its result should be recorded from the completed run, not assumed here.
