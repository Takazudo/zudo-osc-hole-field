# Stage53 verification

Oracle: existing KiCad 10.0.6 through `source /workspace/task-tools/kicad-10.0.6/env.sh`
and `bash scripts/kicad/run.sh`. Numerical source Python:
`/workspace/shared/osc-ci-python/bin/python`. No install/Docker or canonical regeneration.

Before search, `preflight.py` verifies saved native seed/full baseline partitions
and ordinary-via entry/exit conditions. Independent read-only native fill inspection
assesses In4 plausibility. `fill_export.py OUTPUT` and `topology.py INPUT OUTPUT`
reproduce the approximate preliminary topology check, not native acceptance.

Source commands:
```
/workspace/shared/osc-ci-python/bin/python design/architecture-278/implementation/stage53/in4-study/preflight.py
/workspace/shared/osc-ci-python/bin/python design/architecture-278/implementation/stage53/in4-study/search.py .circuit-cache/stage51/dump.json .circuit-cache/stage53/coarse.json coarse
/workspace/shared/osc-ci-python/bin/python design/architecture-278/implementation/stage53/in4-study/search.py .circuit-cache/stage51/dump.json .circuit-cache/stage53/replay.json coarse
```
Proposal and search metadata match byte-for-byte. One 0.1 mm-resolution design
candidate only; the optional 0.05 mode was not used. Replaying is not another design.
Search refuses overwriting first evidence. Bounded search success is not acceptance.

Native commands (drivers retained; copies provisioned with identical project,
schematic, sheet, rules and library tables at baseline directory depth):
```
bash /home/agent/.codex/scripts/heavy-guard.sh --label stage53-in4-candidate -- bash design/architecture-278/implementation/stage53/in4-study/evidence/trial1.sh
bash /home/agent/.codex/scripts/heavy-guard.sh --label stage53-independent-fresh -- bash design/architecture-278/implementation/stage53/in4-study/evidence/fresh.sh
```
Initial shared home-lock sandbox failure was stopped/retried with scoped escalation;
first native run PASS 119 s. Guard process success is distinct from routing acceptance.
Each driver separately applies the proposal to Stage49, then DRC with schematic
parity/refill/save and full native snapshot. No Stage51/52 copper used as baseline.

`accept.py BASE CANDIDATE PROPOSAL LABEL` requires exact authorized added properties,
all retained geometry/partitions, intended 115 opens, native execution/dependency/hash
bindings and unchanged uncapped warnings. `settle.py BASE FIRST FRESH PROPOSAL OUTPUT`
re-evaluates both acceptances and requires identical board, complete snapshot and
acceptance. `--check` checks existing settlement without writing evidence. Large
native boards and snapshots remain ignored locally, hash-bound by settlement.
Retained full DRC reports/receipts and acceptances stay portable under evidence/.
No Git LFS.

Focused tests:
```
/workspace/shared/osc-ci-python/bin/python -m unittest scripts.checks.test_in4_study -v
/workspace/shared/osc-ci-python/bin/python -O -m unittest scripts.checks.test_in4_study -v
```
Ignored-native controls explicitly skip when their local inputs are absent in CI;
portable acceptance-negative and evidence controls still run. No CI native result
for this proposal is invented from a skipped control.

History checks use Stage50 check_bindings.py normal/-O (seven checkpoint bindings
and Stage41–50 manifests), plus Stage51/52 manifests. Full historical replay and
aggregate regeneration remain bounded by exact-head CI. `pnpm circuit:check` before
and after, `pnpm check`, whitespace/scope and final review bindings are required.
Manual 68 lines/0 placements; no schematic/placement binding. Physical, assembly,
ampacity, source-capacity and manufacturing qualification NOT RUN. Exact final SHA
and terminal CI are recorded on Issue278/PR287 outside self-referential files.

Results: both native guards PASS (119/115 s); both independent native acceptances
and settlement agree. All23 focused tests pass normal/-O locally and independently,
no local skips. Optimized read-only settlement replay passes. Historical/Stage51/52
bindings, pnpm checks and scoped whitespace pass. Review includes the final balanced
partition regression and documentation/manifest delta.
