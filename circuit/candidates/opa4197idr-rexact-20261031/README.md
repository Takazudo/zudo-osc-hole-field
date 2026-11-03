# OPA4197IDR option B + R-exact candidate (UNADOPTED, isolated development record)

**Status: UNADOPTED isolated development candidate. Not canonical, not validated, not a
manufacturing or order input.** The canonical specification, schematics, board projects,
partition, BOM and placement lock are unchanged by this directory. Nothing here is a
fabrication file. No DRC, zone fill or #293 fill was run.

## What the candidate is

One combined change set against predecessor commit
`60c7c3ab78cba5e2fcd81973024894510e090cfb` (`receipts/application-receipt.json` also
records its tree hash):

1. **OPA4197IDR, control-board option B.** The phase-15 OPA4197IDR evidence patch
   (`design/readiness/phase15/opa4197idr-candidate.patch`) plus a role migration.
   `design/spec/modules/io_partition.py` `precision_package()` moves every OPA4197IPWR
   package outside the `control` region to the pin-identical SOIC-14 OPA4197IDR
   (`op_precision_d`, LCSC C2058532). The octave reference gets the same rule. Result:
   **85 OPA4197IDR + 4 OPA4197IPWR** (U102, U202, U3303, U3403 keep TSSOP-14). The
   standard's `precision` role still names `op_precision`.
2. **R-exact.** The 14 `r-exact-candidates.json` roles are applied to envelope,
   oscillator and wavefolder. There are 80 added series elements per unit (oscillator
   12 × 5, envelope 3 × 6, wavefolder 1 × 2). Each first element keeps its original key
   and slot. Added elements (`*_SERn`) are numbered after every existing part, so
   **no existing designator moves**: 8234/8234 key→designator rows are identical.
   `scripts/schgen/audit_master.py` takes a +80 designator-lock increment.

3. **JR slot swap (phase 17).** The SOIC-14 reflow of the jack boards put RB4515 into
   the slot that the issue189 `jr-rb4413-edge-bridge` translation binds to RB4413.
   `design/partition/candidate-slot-swaps.json` swaps the two R0603 slots. RB4413 goes back to
   its recorded position, and the pending translation is again rejected only by connector
   JR-K-6-JR, as on the predecessor.

Downstream code that hard-coded OPA4197IPWR was widened to accept either package. That
covers current worksheets, model contracts, the rail ledger, checks and tests. The
rail allocation inputs gain one load row each for H1, H2, X1 and X2, which now carry
both packages.

## Contents

| Path | Content |
| --- | --- |
| `patches/source.patch` | the 53 source and input files (includes the phase-15 bundle) |
| `receipts/application-receipt.json` | before/after sha256 of all 212 changed files, source or generated |
| `receipts/checks.json` | step and check results of the candidate run |
| `tools/reproduce.sh` | generation order that rebuilds the successor from the predecessor |
| `tools/verify_record.py` | offline consistency check; `--tree` compares a rebuilt tree |
| `review/tmux6112_routes.py`, `review/tmux6112-routes.json` | S2b envelope-switch route comparison (phase 17) |

The 159 generated successor files (schematics, board sheets, partition, reports) are
not committed; their hashes are in the receipt. Never apply this patch to the canonical tree
without an adoption decision.

## Reproduce

```sh
git worktree add --detach <scratch> 60c7c3ab78cba5e2fcd81973024894510e090cfb
ln -s "$PWD/node_modules" <scratch>/node_modules
bash circuit/candidates/opa4197idr-rexact-20261031/tools/reproduce.sh <scratch> circuit/candidates/opa4197idr-rexact-20261031
python3 circuit/candidates/opa4197idr-rexact-20261031/tools/verify_record.py --tree <scratch>
```

## Status

See `receipts/checks.json` for the full list.
