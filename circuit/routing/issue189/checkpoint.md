# Issue 189 implementation checkpoint

Unvalidated draft. Issue #189 remains open. No fabrication, release or hardware qualification.

## Frozen baseline and plan

Remote main refreshed at `1fe06ad50248d6434876fbf2bd6e32e1bfbb13bb` on 2026-10-08.
No open PRs at initial inspection. Core run 37775496177 remained in aggregation
(one successful shard, seven failures); no result adopted from that concurrent branch.
`input-hashes.json` identifies 251 board/project/rule/schematic/library-context and fixed-input files.
All remained byte-identical after attempted initial regeneration.

1. Reproduce H1/H2 before changes, then fix geometry ownership and transaction replay.
2. Compare old/new on identical saved native inputs: ten deterministic signal nets
   per JL/JR/core, short stranded neighbours, long nets and high-island-count nets.
   One rip-up round, four victim nets, 100,000 expansions per search, 0.1 mm grid.
   Minimum useful progress is one native edge closed without pad-membership splits
   or new warning identities. Do not repeat two negligible comparisons unchanged.
3. Retain native-accepted local proposals and continue diagnosed hotspot repair,
   including rail/AGND obligations. Do not promote merely on raster success.
4. Recheck P/EL/octaves, aggregate source regeneration and integrated CI. The goal
   remains JL/JR/core zero native open edges, not just a router fix.

## Reproduction and implementation

`hypotheses-before.txt`: both regression assertions fail on unchanged main.
H1: the removed via remains in the transaction's hole mask.
H2: the soft search marks a fixed foreign terminal traversable.

The raster now separates fixed terminal/drill ownership, rebuilds route occupancy
from surviving source objects plus committed result paths, and snapshots/restores
removable drill records on rollback. Fixed PTH/NPTH holes and overlapping surviving
vias are retained. Soft searches keep foreign pads hard and soften only routing
drills/copper. Victim ordering is deterministic. Structured diagnostics explicitly
use `unknown` where a specific geometric cause is not established.

Native acceptance remains mandatory; these tests prove raster behavior only.
The benchmark additionally rejects lost pad-component membership even when totals
improve, records warnings by type/item identities, and reports retained copper UUIDs.
It does not modify canonical boards. Any eligible candidate still needs review of
proposal/source replay and promotion on this isolated branch.

## Environment and checks

- Initial `pnpm circuit:check`: PASS. Manual inventory, 68 lines, zero declared
  placements; no schematic/placement binding; pin-asset check performed.
- Existing focused suite: 30 tests PASS before edits.
- H1/H2 tests: 2 expected failures before edits; corrected regressions and focused
  suite pass. Additional fixture/gate tests are in the same Python test discovery.
- Initial aggregate regeneration: BLOCKED at pinned KiCad startup, exit 1.
  Docker pull exhausted the 32 GB overlay; no container started. Only this session's
  unused image was removed to recover space. No tracked regeneration drift.
- Local native KiCad is 9.0.2 and was not used for acceptance. Native JL/JR/core,
  P/EL/octave checks are NOT RUN locally. CI uses the pinned 10.0.6 wrapper.
- Personal-context loader was rejected by automatic approval review because its
  path resolved into forbidden `/root/.codex`; no workaround attempted. Runtime
  bridge restoration succeeded separately. This is not proof of automatic delivery.

## Exact continuation

```sh
git fetch origin
git switch agent-fix/189-obstacle-transactions
python3 -m venv .circuit-cache/route-venv
.circuit-cache/route-venv/bin/pip install -r scripts/pcbgen/numerical-requirements.txt
.circuit-cache/route-venv/bin/python -m unittest scripts.pcbgen.test_obstacle_transactions scripts.pcbgen.test_benchmark_obstacles scripts.pcbgen.test_grid_router scripts.pcbgen.test_route_jack_grid
# Native-capable host, with the machine-wide heavy guard:
python3 scripts/pcbgen/benchmark_obstacles.py osc-jack-left
# Same command for osc-jack-right and osc-core; do not change inputs between variants.
```

CI equivalent: dispatch `routing-benchmark.yml` on this topic branch with `board`
set to each board. It has read-only repository permission, no canonical writer,
90-minute compute cap and 30-day artifact retention. `result.json` contains source
and board hashes, selected identities, component memberships, old/new native stage
receipts, timings, diagnostics, warning identities and retained-copper evidence.
Copy durable compact results/proposals into this directory before artifact expiry.

If a candidate is eligible, inspect its complete proposal, rules and native receipt;
replay against the exact input SHA and run fresh settled checks before adopting.
If both variants make negligible progress, use failed victim/terminal identities to
change the local repair method. Do not simply increase global rerouting budgets.
