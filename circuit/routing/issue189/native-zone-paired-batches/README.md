# Optional full paired native batching — preparation only

Read-only native run38005209241 atd727b49 is active,40-minute bound starting
23:36:27UTC. No complete native result is claimed yet. The original single-item audit remains the default. Explicit
`--batch-size 16` bounds each native fixture to16selected artwork items and emits
new batch-scoped receipts. Every selected item is retained once per stage; full
native zone coordinates, source artwork IDs/rendered text, project/rules and
both warning caps are checked. Both before/after stages and every growing
silk-relevant zone still run. Incomplete output cannot certify coverage.

This isolated branch adds strict source-bound acceptance support for the batch
format and an opt-in `--native-zone-batch-size 16` merge argument. It requires
`--complete-native-warnings`; all four native audit commands remain mandatory.
The default stays single-item. Main is unchanged, and no writer may use this
preparation until the full real paired artifact is reconciled and checks pass.
No existing warning or other gate is waived. No canonical board changes.
All21saved native sample fixture bytes also reconstruct exactly with the new
serializer (heavy-guardPASS16s); `native-sample-serialization.json` binds each hash.
Reproduce with `verify_sample_serialization.py BEFORE_BOARD TIMING_ZIP OUTPUT_JSON`.
No native tool is invoked by that check.

Forty-three focused tests pass, including bounded tail coverage, unknown/duplicate
scope rejection, unchanged single-item serialization and malformed batch-proof
rejection, native-error/split/fresh-copy gates and opt-in command propagation. Native performance sample38002541870 independently established3.66x/
11.03x gains at4/16items on identical saved inputs, but was all-negative and
before-only. Native detection controls38004636645 at3629a72 passed and independently
reconciled all5fixtures (0/1/1/0/2identities); raw proof is in
`../native-zone-batch-probe/native-controls-receipt.json`.

Current: one read-only40-minute native paired audit on the exact95c815before and
b9f5caafter boards from artifact11631867897, with original context. Preserve all
scope/progress records, raw reports, fixtures, geometry signatures and source
hashes. No adoption step. Core writer 37984573591 is terminal and rejected: zone exit 137 left incomplete coverage. Its exact artifact is independently reconciled in `../core-complete-terminal/`; no PCB was published and no replacement writer is active.

```sh
timeout --signal=INT --kill-after=2m 40m \
  bash scripts/kicad/run.sh python3 scripts/pcbgen/audit_zone_silk_scope.py \
  VERIFIED_BEFORE VERIFIED_AFTER .circuit-cache/issue189-paired-zone-batches \
  --classify --batch-size 16
```

A passing audit
still requires independent exact coverage/report/context/source reconciliation,
then validated acceptance support, ordinary/fresh native gates and copper
retention before any promotion. Issue189 remains open.


After a terminal artifact exists, independently reconcile it with:

```sh
python3 -m scripts.pcbgen.zone_batch_evidence \
  VERIFIED_ZIP VERIFIED_BEFORE VERIFIED_AFTER OUTPUT_JSON --sha256 ZIP_SHA256
```

That verifier is prepared and unit-tested but has not yet run on this pending
artifact. It checks exact paired coverage, native scope/context, source fixture
bytes, versions/severities, hashes, caps and identity unions. Tests reject altered
fixture bytes even when the receipt hash is updated, changed context, wrong
version/severity scope, capped reports and incomplete pairs. New warning
identities are preserved in its result, never erased or treated as adoption.
The isolated consumer rejects any incomplete pair, stale source, altered fixture,
context/version/severity mismatch, capped report or new zone warning. Existing
ordinary/fresh DRC/parity, topology and retained-copper gates remain in force.
The real full paired artifact is still pending, so no eligibility is claimed.
