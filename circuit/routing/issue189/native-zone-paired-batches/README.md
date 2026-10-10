# Optional full paired native batching — preparation only

Read-only native run 38005209241 at d727b49 timed out with exit 124 after
35 of 42 batches. Artifact 11652255919 has SHA256
30bbbe4e71ba6c7e82fb4d88e135b2d30fba554c9c03ce5dfae1e6cd02bc608f.
The front zone completed both stages (9+9); the back zone completed 12+5
of 12+12. Every completed batch reported zero zone identities. Seven batches
remain unverified; no complete native result is claimed. The original single-item audit remains the default. Explicit
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

Forty-six focused tests pass, including bounded tail coverage, unknown/duplicate
scope rejection, unchanged single-item serialization and malformed batch-proof
rejection, native-error/split/fresh-copy gates and opt-in command propagation. Native performance sample38002541870 independently established3.66x/
11.03x gains at4/16items on identical saved inputs, but was all-negative and
before-only. Native detection controls38004636645 at3629a72 passed and independently
reconciled all5fixtures (0/1/1/0/2identities); raw proof is in
`../native-zone-batch-probe/native-controls-receipt.json`.

Next: one read-only resumed audit on the exact 95c815 before and
b9f5ca after boards from artifact 11631867897, with original context.
`--resume-from` requires a new output directory and validates the exact source,
scope and ordered progress prefix. Every reused fixture is reconstructed and
natively checked for geometry, artwork and rendered text; its saved bytes,
context, raw-report hash/version/severity scope, caps and identities must agree.
Incomplete or unrecorded fixtures rerun. The final full-coverage gate is unchanged. Preserve all
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
The first full paired attempt is incomplete. A complete resumed artifact is still required; no eligibility is claimed.

A second read-only verifier is prepared as `combine_evidence.py`. After the full
paired artifact passes, it checks every extracted terminal-file hash, validates
and extracts the complete paired proof to a new directory, then evaluates
`complete_reports` and the ordinary promotion gate on the exact saved sources.
It does not adopt or change a canonical board. It has been syntax-checked only;
execution is pending the real full paired artifact.

```sh
bash "$HOME/.codex/scripts/heavy-guard.sh" -- PYTHON \
  circuit/routing/issue189/native-zone-paired-batches/combine_evidence.py \
  VERIFIED_PAIRED_ZIP VERIFIED_TERMINAL_EXTRACTION VERIFIED_BEFORE VERIFIED_AFTER \
  NEW_ZONE_EXTRACTION OUTPUT_JSON --sha256 PAIRED_ZIP_SHA256
```

If it passes, refresh main and the three other-session routing branch heads,
require PR217 exact-head checks, and use one isolated bounded replay worker.
The concrete replay remains the saved finer-ground transaction (replay SHA256
25a3de5583c9bb61611a4e46d9463a581a09cba43c1dc23bf2d45c5203a3b08c)
against canonical core SHA256
a0e3cff1ebc211564b8be10f6a993d50fb6d4372edde86a056ebc8dda3ea5932.
Use the opt-in `--complete-native-warnings --native-zone-batch-size 16`; all
four audits must rerun on that worker's exact native boards. Retain its terminal
artifact even if rejected. Require settled/fresh membership, full warnings,
copper retention and native-equivalent publication compaction before promotion.
Do not reuse partial coverage or restart the rejected unchanged single-item run.
