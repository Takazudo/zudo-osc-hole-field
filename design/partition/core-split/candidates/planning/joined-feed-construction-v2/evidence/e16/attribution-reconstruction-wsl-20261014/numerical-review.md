# Independent numerical/accounting review

Verdict: PASS for the bounded B0 source-fixture checkpoint. No outstanding review findings within this scope. This is not numerical authorization or production resource/uniqueness attestation.

Reviewed `attribution_reconstruction.py` and its tests against `finite_solve.py`, `finite_adapter.py`, and `resistance_attribution.py`. The selected-RHS reconstruction uses the original reduced coupling signs and terminal ordering, ignores retained simultaneous-load u0/g, retains extended solution arithmetic, and preserves the distributed rank-one terminations. The connected removed-wire fixture retains both end terminations, removes bulk only once, and agrees with an independent tiny monolithic solve. Unit-excitation E/I² remains separate from simultaneous-load watts.

Local sheet/tile and exact barrel-interval accounting preserves union membership as provenance. Original Assembly recovery is exercised on a real tiny two-layer mesh/ring fixture; persisted ring/support mappings and geometric stiffness are checked. The unchanged reporter independently checks the tiny free operator, full summed-operator partition, free/global KCL, source reactions and energy/load work. Electrical acceptance, whole-board acceptance and adoption remain false.

Findings raised and closed:

- Declared node count initially failed to constrain actual sparse storage, vertices, mesh items and support payloads. Fixed ceilings now validate those inputs before numerical work, including bounded traversal of geometry/WKB, row/column/boundary/support payloads before original Assembly construction.
- The directly callable reconstruction helper now applies reduction/configuration/observation payload checks before matrix work, with an oversized-Schur regression.
- The local accounting primitive now enforces node-current reconciliation against max(abs(global nodal injection)), matching the reporter, rather than merely returning its error.
- Added connected two-wire/one-removed coverage with independent monolithic potential parity.

Independent validation command, run from E16:

```sh
/home/takazudo/.cache/zudo-e16-numerical-venv/bin/python -m unittest test_attribution_reconstruction test_resistance_attribution
```

Result: 57 tests PASS (23 bridge plus 34 predecessor reporter tests), 1.581 seconds on the final reviewed source. No real retained pickle, production field, native oracle or campaign job was opened/executed by this reviewer.

Final reviewed SHA-256:

| File | SHA-256 |
| --- | --- |
| attribution_reconstruction.py | f7bccba3a0b204e1fa3b36ec6ee1b90258a45d725c10d3d22b63ab1072fb3ace |
| test_attribution_reconstruction.py | edb4f53c85ae8f48c8d761f374be9e6c1c9dfc37fcaf77685a16c45c8710e9ba |
| finite_adapter.py | f313a87719aba83b169a363c05d36daa5c79cd28ad41620e5d45c5d8eca613f4 |
| finite_solve.py | 20b1b9e1e7ba8653d3268c4956dc5415b91670e23f07e35ab381d2091f84b044 |
| resistance_attribution.py | 67c9735f1519b49e69cab61dfaea8947d5f7d9838185cce7f87eca0070deca70 |

B1 remains NOT EXECUTABLE / NOT ADMITTED. The source-only readiness command correctly emits exit 2, a null production request digest and no production execution command. Missing production work is explicit: guarded serialized original-map recovery and selected-RHS/accounting driver, applicable exact free-operator uniqueness evidence, combined resource proof, and applicable one-unit admission/authorization/reservation. Self-generated packet hashes and tiny eigenvalue checks supply none of these. The lower-level streaming primitives are not production admission entry points. Tiny fixture bounds and timings do not prove a real model fits 2 GiB/180 seconds. C is NOT RUN.

Final normalization delta independently reviewed: the accounting current scale is now the maximum absolute global nodal injection, not total excitation current. This retains the predecessor criterion for distributed supports. The added perturbation regression rejects a 1e-10 A current mismatch at nodal scale 0.01 A although a total-current scale of 1 A would have accepted it. Final independent rerun: 57 PASS; hashes above supersede earlier review snapshots. Verdict remains PASS for bounded B0 only; no new production scope.
