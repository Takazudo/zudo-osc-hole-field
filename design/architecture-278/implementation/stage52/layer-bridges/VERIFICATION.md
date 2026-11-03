# Stage52 verification

Installed KiCad10.0.6 via `source /workspace/task-tools/kicad-10.0.6/env.sh` and
`bash scripts/kicad/run.sh`; saved numerical Python
`/workspace/shared/osc-ci-python/bin/python`. No Docker/install or canonical regeneration.

Native jobs use the shared guard. Actual drivers are retained in evidence/:
```
bash /home/agent/.codex/scripts/heavy-guard.sh --label stage52-halves -- bash .circuit-cache/stage52/probe-halves.sh
bash /home/agent/.codex/scripts/heavy-guard.sh --label stage52-gap-isolation -- bash .circuit-cache/stage52/probe-gaps.sh
bash /home/agent/.codex/scripts/heavy-guard.sh --label stage52-two-bridges -- bash .circuit-cache/stage52/trial1.sh
bash /home/agent/.codex/scripts/heavy-guard.sh --label stage52-independent-replay -- bash .circuit-cache/stage52/replay.sh
```
The sandbox initially denied writing the shared home lock; stopped that queued
attempt and repeated the same scoped command with approved escalation. Guard PASS
means process completion, not routing acceptance. Diagnostic halves/gaps use native
ZONE_FILLER and explicit connectivity rebuild, not full DRC. Full candidates run
CLI DRC with refill/save/parity and complete native snapshots. Every copy is a sibling
cache directory to preserve ${KIPRJMOD} library resolution. Native acceptance is
rejected despite zero rule errors. First failures remain retained.

`sites.py DUMP STAGE51_PROPOSAL OUTPUT` screens through-via sites at0.05mm intervals.
`bridge.py DUMP OUTPUT CASE RESOLUTION` performs bounded searches; each retained
.search.json records its parameters, source dump hash and result. New endpoint
membership is synthetic proposal input only. `compose.py LOWER UPPER OUTPUT` builds
the complete target-only proposal. Byte comparisons passed for both route replays
and their composition. Native replay is a separate fresh Stage49 build.

`audit.py` generates retained evidence, while `audit.py --check` is strictly read-only
and rejects altered evidence. It binds baseline and candidate DRC commands,
dependencies, board/snapshot hashes, full identity and all retained partitions.
Run normal and `-O` under the pinned KiCad wrapper. The audit explicitly records the
−12 V and AGND failures and identical fresh-build board/snapshot bytes.

Focused unittest wrapper: `/workspace/shared/osc-ci-python/bin/python -m unittest scripts.checks.test_layer_bridges -v`
and the same command with `-O`. Portable controls do not claim native execution in
CI; local ignored-input controls report skips when the native cache is absent.
History: Stage50 check_bindings.py verifies seven checkpoints and Stage41–50
manifests normal/-O; Stage51 bindings are additionally checked byte-for-byte.
Full historical replay and aggregate regeneration are left to exact-head CI.

`pnpm circuit:check` before/after, `pnpm check`, scoped whitespace/history checks and
review bindings are recorded in WORK.md. Inventory manual68lines/0placements;
no schematic/placement binding. No physical/assembly/manufacturing/electrical pass.
Exact final SHA and terminal CI are recorded externally to avoid self-reference.
