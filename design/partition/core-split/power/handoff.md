# Issue #247: core power and AGND contract

Source-only architecture input for [#247](https://github.com/Takazudo/zudo-osc-hole-field/issues/247), under [Epic #242](https://github.com/Takazudo/zudo-osc-hole-field/issues/242). Two cores remain a comparison preference; neither candidate is a selected topology. No production board, circuit, generator, accepted copper, panel or non-core pose was changed.

## Revision and exchange boundary

- Topic: `agent/247-core-power-1011`.
- Verified immutable current main and historical reference: `65cefd41fc39e064d38319115ad96016a1c6b71c`.
- Assigned PR base: `integration/epic-242-core-routing`, coordinator input `1da1909846dc3255888ecd36c88cee9737c85834`, [draft baseline PR #260](https://github.com/Takazudo/zudo-osc-hole-field/pull/260).
- Exchange epoch: `epic242-e0`. This main-based lane retains its source parent; the coordinator permits incorporation after frozen-input comparison.
- `integration-check.json`: all **1,883 frozen inputs** and **390 complete existing endpoint records** agree with that integration input. No baseline drift was found. This includes the eight non-K endpoints outside the 382 K harness endpoints used by the power contract.
- `manifest.json`: hashes of consumed source dependencies, the builder/input, generated outputs and all 14 committed PCB files. Generation refuses consumed-source drift from the immutable source commit. `--compare-ref` checks consumed dependencies and PCB bytes against a full immutable integration SHA.

## Deliverables

- `input.json`: explicit two/three-core module candidates and finite connector, bulk, monitor and auxiliary-current reservations.
- `build.py`: deterministic source parser, conservation checks, immutable-source gate and integration comparison; writes only this owned directory.
- `contract.json`: per-core package/IC/AGND inventory, worksheet responsibility and separate physical-load unknowns, supply pins, bypass ownership, fitted capacitance and reserved bulk, current headroom, global voltage-drop/copper budgets and fault/return gates.
- `harness-contract.json`: all 191 K harness IDs and 382 endpoint Refs, complete signal/AGND/rail/NC pin order and source poses; separate `CS247-*` proposed feed namespace with both ends, six conductors, local terminal cells, service corridors and unresolved assembly origins.
- `package-ownership.csv`: every one of the 5,904 physical package records, including 3,385 K packages, for both candidates; retains non-core ownership, all 13 POWER parts and eight DNP parts.
- `test_contract.py`: 11 focused conservation and mutation tests, including paired endpoint/source-pose drift and direct source-provenance dependencies.
- `verification.json` and `integration-check.json`: observed check receipts with explicit evidence scope.
- [Research document](../../../../doc/src/content/docs/research/osc-core-split-power.mdx): numerical tables, source links, envelopes, assumptions and open gates.

New feed reservations are 91 × 6 mm terminal rows at each end, plus a separate 91 × 28 × 28 mm service corridor at each end. Each added core has a 20 × 20 × 5 mm monitor proposal; every core has three 5 × 3 × 5 mm bulk slots. Their assembly coordinates and exact new part numbers are unknown. Existing GH connector MPNs are preserved; they are not qualified as full-core feeds. The original 76 × 70 mm protection reserve and all 18 K main-feed lands stay on KA. CN301/XB301 remain abstract source/protection boundaries with no invented implementation.

## Verification and limits

All 11 tests passed. Deterministic generation, immutable input comparison, rail ledger, supply architecture, rail-option checks, `pnpm circuit:check` and `pnpm check` passed. `pnpm circuit:check` explicitly uses manual inventory: **schematic/placement binding was not performed**. The documentation/type check passed and existing generated pages/previews were current. All 14 original PCB hashes were unchanged.

The initial aggregate `scripts/checks/regen-all.sh` was inspected but not executed: it writes shared outputs outside this lane and enters native work without the parent's global slot. No competing regeneration was published. Aggregate regeneration, fresh native acceptance and integration CI remain **deferred, not passed**. No native, routing, heavy build, physical, thermal, startup or fault test was run. The commit requests `[skip ci]` because the default PR workflow launches four native jobs, exceeding the parent's global two-job limit. The coordinator must schedule an appropriately bounded integration run.

Two independent requested review lanes covered current/return arithmetic and connector/preservation scope. A missing provenance dependency finding was fixed by hashing directly consumed symbols and standard JSON and rejecting changed pinned inputs. Both final reviews reported no blocking source-contract finding. These reviews do not constitute electrical qualification.

Reproduce from the repository root:

```sh
python3 design/partition/core-split/power/build.py --check
python3 -m unittest discover -s design/partition/core-split/power -p 'test_*.py' -v
python3 design/partition/core-split/power/build.py --compare-ref 1da1909846dc3255888ecd36c88cee9737c85834
python3 scripts/schgen/build_rail_ledger.py --check
python3 scripts/schgen/build_supply_architecture.py --check
python3 scripts/schgen/analyze_rail_options.py --check
pnpm circuit:check
pnpm check
```

## Next coordination

Ready for architecture/floorplan/connector lane consumption and coordinator review. Reconcile again if the assigned integration input changes. Exchange actual module assignment and placed feed/bulk/monitor/service envelopes before deriving physical core current or adopting geometry. Recompute the joined return network for all mates, unbalanced demand, absent returns and partially powered cores; the 1 mΩ rail / 0.5 mΩ AGND allowances and 20 mV budget are global and cannot restart at each board. Exact core current maxima, protection consumption, connector/hot loss, effective capacitance and physical fit remain open. Existing source/protection/qualification gates #57, #59 and #65 remain intact.

No native command is requested by this lane. When architecture and geometry are ready, the parent must assign an explicit bounded command and global slot using only pinned KiCad 10.0.6 through `scripts/kicad/run.sh`, preserving the global two-worker, 6 GiB worker / 12 GiB aggregate / 2 GiB free and time limits.

Startup limitation: automatic approval review rejected both runtime-link restoration and the read-only personal-context loader because of protected home/runtime access. No fallback, profile rebuild or link overwrite was attempted. Repository AGENTS.md, circuit/WORKFLOW.md and relevant local skill references were read; personal runtime discovery/loading remains unverified.
