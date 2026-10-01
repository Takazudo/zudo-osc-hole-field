# Issue 38: standalone batch checkpoint store

## Scope and changed files

Added `scripts/pcbgen/batch_checkpoint_store.py` and
`scripts/pcbgen/test_batch_checkpoint_store.py`. No active K solver, trial-matrix,
or other source in the running solver's hash closure was edited for this task.

The store persists each completed current or potential profile batch as a
non-pickle NPZ payload and canonical JSON manifest. It flushes and fsyncs each
temporary file before atomic rename, then fsyncs the directory. Reads verify
the exact supplied run key, mode, profile count, batch size, contiguous ranges,
payload length and SHA-256, member set, array dtype/shape/finite values, receipt
ranges, and the applicable per-batch `1e-8 A` numerical gate. Duplicate, gapped,
overlapping, incomplete, and corrupt artifacts fail closed. Dense and canonical
CSR/CSC operand digest helpers are provided for a future source-bound run key.

## Verification

- `pnpm circuit:check`: PASS before and after edits.
- Solver virtual environment: `python -m unittest scripts.pcbgen.test_batch_checkpoint_store -v`: 11 tests PASS. Mutations cover source/operand key, mode/count/batch size, payload/manifest bytes, rehashed malformed arrays and receipts, nonfinite and wrong-shape/dtype values, numerical gates, duplicate/gapped ranges, and short final batches.
- `python3 -m py_compile` on both new files: PASS.

## Limits and remaining work

This is a storage primitive, **NOT wired into the active K solver**. The caller
must construct the complete run material from frozen native and prerequisite
bytes, full model source map including checkpoint code, exact ordered profiles,
parameters, numerical library versions, and newly assembled operators; it must
recheck those inputs before each checkpoint commit and final publication. The
generic run-material digest helper cannot detect an input omitted by its caller.
The caller must restore only verified columns and receipts, recompute scalar
residuals from the restored gate components, and run all full-matrix reciprocity,
bracket, and publication gates. These local checkpoints are diagnostics, not
accepted electrical or physical evidence. An incomplete or corrupt pair is
rejected; the caller must investigate or use a fresh checkpoint directory before
recomputing it.

## Post-review repair

Independent review found that a completed eight-profile run accepted an empty 8:8 batch and that integer JSON keys could collide with their string form in the run-material digest. The store now requires `start < stop` and `start < profile_count`, and rejects non-string keys recursively before canonical JSON hashing. Two regression cases were added; all 12 focused tests and `pnpm circuit:check` pass after repair. The review's suggested current-mode residual-work gate was withdrawn: current energy-matrix residual work is charged as an allowance; the existing 1e-8 A gate applies to the separate operator/sheet/barrel/shared-face KCL components. The store remains standalone and does not resume the active K solver.
