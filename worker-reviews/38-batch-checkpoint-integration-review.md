# Issue 38 finite-profile checkpoint integration review

Scope: read-only adversarial review of `batch_checkpoint_store.py`, both trial
matrix drivers, `solve_conductor_volume.py`, and the focused checkpoint tests.

## Verified

- The run key binds native-export SHA-256, model-source hashes, native prerequisite
  receipts, exact profile bytes and ordered finite profile components, mesh
  parameters, solver library versions, and mode-specific assembled numerical
  operands. The driver rechecks those sources before loading, before each save,
  and before publishing the final receipt. A changed key or payload digest fails
  closed.
- The store enforces exact contiguous ranges, float64 array shapes, finite
  entries, and the current physical residual or potential equation residual
  gate. Both drivers restore all four current arrays or all three potential
  arrays, plus receipts, then rerun reciprocity and the final bracket gate.
- Existing focused tests: 15 passed. I separately ran the real small conductor
  fixture with nine profiles at batch size eight: current and potential each
  produced batches 0:8 and 8:9, and each final matrix exactly matched an
  uninterrupted run (`maxdiff 0.0`). This checks the actual eight-column shape
  path, though it is not a full K-board run.
- Matrix formation and conservation follow the corresponding steps in
  `SheetVolume.area_profile_matrix_batched`; the new drivers use the intended
  refined solve and row-wise residual-work enclosure.

## Finding closed: interrupted two-file save

`BatchCheckpointStore.save` writes the `.npz` payload and then the `.json`
manifest. A process killed between them originally left a payload-only tail
that blocked resume. The manager added recovery under the store lock: it
discards only an exact next-range payload with no manifest when that range is
the last entry; gapped, JSON-only, and other malformed entries still reject.
The focused test now covers recovery after a complete first batch and an
uncommitted second batch. I reran all 15 focused tests after this change;
they passed. This closes the concrete restart defect.

## Boundary requiring an explicit decision

The SHA-256 manifest detects accidental bit changes. It does not authenticate
locally writable artifacts: someone able to rewrite both files can forge a
matching payload digest and keep the run key. The restored arrays are not
recomputed from the operator; receipt validation checks ranges and selected
residual scalars, while arbitrary numerical refinement and conservation receipt
contents are only canonical-JSON checked. This is a normal checkpoint trust
assumption, but the final result must be described as depending on trusted
local checkpoint files. If the intended requirement is to reject deliberately
rehashed semantic tampering, the current protocol does not establish that.

## Existing cache risk outside the new checkpoint store

`solve_conductor_volume.py:141-144` unpickles the mesh cache before validating
its embedded key, then accepts `sheets` solely on that key. The source and
operand run key does not independently prove that cached mesh objects came
from `Sheet(...)` applied to the current native geometry. This pre-existing
trust assumption should remain explicit for any published numerical receipt.
