# Optional full paired native batching — preparation only

Native NOT RUN. The original single-item audit remains the default. Explicit
`--batch-size 16` bounds each native fixture to16selected artwork items and emits
new batch-scoped receipts. Every selected item is retained once per stage; full
native zone coordinates, source artwork IDs/rendered text, project/rules and
both warning caps are checked. Both before/after stages and every growing
silk-relevant zone still run. Incomplete output cannot certify coverage.

The acceptance consumer explicitly rejects the new batch format until independent
coverage support and artifact reconciliation are implemented and validated.
No existing warning or other gate is waived. No canonical board changes.
Twenty-one focused tests pass, including bounded tail coverage, unknown/duplicate
scope rejection, unchanged single-item serialization and unsupported batch-proof
rejection. Native performance sample38002541870 independently established3.66x/
11.03x gains at4/16items on identical saved inputs, but was all-negative and
before-only. Native detection controls38004636645 at3629a72 are still running;
do not dispatch this full paired diagnostic until those controls pass.

Next: one read-only40-minute native paired audit on the exact95c815before and
b9f5caafter boards from artifact11631867897, with original context. Preserve all
scope/progress records, raw reports, fixtures, geometry signatures and source
hashes. No adoption step. Keep the sole core writer37984573591 untouched.

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
