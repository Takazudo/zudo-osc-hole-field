# Issue 38 batch checkpoint store review

Scope: read-only adversarial review of `scripts/pcbgen/batch_checkpoint_store.py` and its 11 unit tests. No heavy run. The tests passed in the issue 38 solver venv.

## Finding

- **Range bug (confirmed; fix needed before integration):** `_range` permits `start == stop == profile_count` when the profile count is a multiple of the batch size. With eight profiles, `save(fixture(0, 8, count=8))` followed by `save(fixture(8, 8, count=8))` succeeds; `load_prefix()` returns `[(0, 8), (8, 8)]`. The second batch contains zero columns and is not a finite-profile batch. Require `0 <= start < stop <= profile_count`, and test the completed-run case.

- **Run-material key type collision (minor; fix or constrain caller):** `digest_run_material({1: "a"}) == digest_run_material({"1": "a"})`, including within nested objects. Python's JSON encoder stringifies non-string object keys; `_json_bytes` does not reject them. This contradicts the helper's claim to refuse a noncanonical record. Require string-only keys recursively or explicitly require callers to supply a typed JSON-compatible material schema.

## Behavior and integration limits

- The payload and manifest are each written through fsynced temporary files and atomic rename while holding a `flock`. The payload is committed first. An interrupted pair is rejected on load, so no partial batch is silently accepted. It also leaves the store unusable for automatic resume until that incomplete pair is deliberately removed or a recovery protocol handles it. This is a fail-closed availability limitation, not a numerical bypass.
- The reader rejects changed run key, mode/count/batch size, incomplete pairs, gaps/overlaps, altered payload hash, unexpected ZIP members, pickle/object arrays, incorrect float64 shapes, nonfinite arrays, duplicate/noncanonical JSON, and invalid potential/current gate receipts as defined here. The tests exercise most of these. The `current` residual-work receipt is correctly **not** capped at 1e-8: it is the energy-matrix work residual charged into an allowance; the four `physical_gate` values are the current KCL gate.
- The run key is only a digest of caller-supplied material. The helper cannot know if source hashes, native receipts, library versions, profiles, parameters, operator, basis, and other operands were omitted. It also cannot prove that cached energy columns or receipt numbers came from the claimed operator: a party able to replace both files can produce a self-consistent hash. Integration must freeze and recheck the complete run material at save/load/publication, verify loaded receipt/column relationships or trust the local writer, and repeat reciprocity, enclosure, residual, and final certificate gates after assembly. Hash checks alone must never promote a cached prefix to a numerical result.

The sparse digest normalizes duplicates and sorted indices on a copy and binds CSR versus CSC, shape, dtypes, index arrays, and data. The dense digest binds dtype, shape, and C-order bytes. Neither function is yet called by a production solver path, so integration safety remains untested.

## Final disposition after fixes

Both confirmed findings above are **closed in the standalone helper**. `_range` now rejects `start >= profile_count` and `stop <= start`, including a zero-width batch after a complete run. `_json_bytes` recursively rejects non-string keys in dictionaries nested through dictionaries, lists, or tuples, so the demonstrated run-material digest collision is refused. Regression cases cover each behavior. The focused suite now passes 12 tests. This review approves the store as a standalone, fail-closed primitive; production solver integration and its complete run-key and final numerical-gate contract remain open.
