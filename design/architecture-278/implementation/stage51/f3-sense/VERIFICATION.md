# Stage51 verification

Native oracle: installed KiCad10.0.6 via `source /workspace/task-tools/kicad-10.0.6/env.sh`
and `bash scripts/kicad/run.sh`. No installation or canonical regeneration.

Actual guarded drivers (retained under evidence/):
```
bash /home/agent/.codex/scripts/heavy-guard.sh --label stage51-f3-first -- bash .circuit-cache/stage51/trial1.sh
bash /home/agent/.codex/scripts/heavy-guard.sh --label stage51-seed-isolation -- bash .circuit-cache/stage51/seed.sh
```
Driver dependencies were copied from stage49-fresh into sibling cache directories,
preserving relative library depth. Both process runs returned guard PASS (128/119s),
but full-trial engineering acceptance FAILED; seed is incomplete. Reports retained
include the exact CLI command, saved board hash and dependency receipts. Large native
boards/snapshots remain ignored locally; audit.json binds those bytes. No Git LFS.

`audit.py` replays both complete native snapshots, validates DRC execution/dependency
bindings and retained identity, then retains the rejected outcomes. Its first run
failed command/report binding because an absolute path differed from the recorded
relative command. Corrected to use that exact recorded path, without relaxing checks.

Generation: numerical Python `/workspace/shared/osc-ci-python/bin/python`; search.py
modes back/multilayer/wide/fine; escape.py modes in3/in2/in2-fine/guarded. All diagnostics
retained, including first failures. Original proposal replays byte-exact with:
```
PYTHONPATH=. /workspace/shared/osc-ci-python/bin/python design/architecture-278/implementation/stage51/f3-sense/evidence/trial1-escape.py .circuit-cache/stage51/dump.json .circuit-cache/stage51/replay.json
cmp .circuit-cache/stage51/replay.json .circuit-cache/stage51/escape.json
```
First invocation without PYTHONPATH failed import resolution after the script moved
one directory deeper; original bytes preserved. This is source generation replay,
not two successful independent native builds. No accepted candidate exists.

Focused controls run normal and optimized:
`python3 -m unittest scripts.checks.test_f3_sense_repair -v` and the same with `-O`.
Local ignored-input controls must report a skip when their native inputs are absent;
portable report bindings and failure assertions remain checked in CI.
History: Stage50 check_bindings.py (seven checkpoints and Stage41–50 manifests),
normal and optimized. Full historical replay/aggregate regeneration left to exact-head
CI, not duplicated locally. `pnpm circuit:check`, `pnpm check`, whitespace and scope
checks are recorded in WORK.md. Manual inventory68lines/0placements, no schematic
placement binding. No physical/assembly/electrical/manufacturing pass is inferred.
