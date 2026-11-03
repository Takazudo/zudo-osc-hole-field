# Stage47 verification

## Native executions

All native work used installed KiCad10.0.6 through scripts/kicad/run.sh and the
shared heavy guard, with no installation or Docker invocation. Drivers are
retained under evidence/. Exact invocations:

```
bash /home/agent/.codex/scripts/heavy-guard.sh --label stage47-local-reroute -- bash .circuit-cache/stage47/trial1.sh
bash /home/agent/.codex/scripts/heavy-guard.sh --label stage47-correct-depth -- bash .circuit-cache/stage47/trial2.sh
bash /home/agent/.codex/scripts/heavy-guard.sh --label stage47-fresh-reroute -- bash .circuit-cache/stage47/fresh.sh
```

First run: process PASS, 136s, but acceptance FAIL because of 199 new library
warnings. Preserved, not counted as an accepted build. Correct-depth run:
process PASS, 113s. Fresh independent rebuild: process PASS, 118s. Fresh starts
from baseline and applies the proposal again; it is not merely a copy of the
accepted output. Both accepted runs refill/save/DRC with schematic parity and
export complete native connectivity, then pass the final preservation gate.

The source gate and settlement were run as:

```
python3 design/architecture-278/implementation/stage47/local-reroute/accept.py .circuit-cache/stage44-b2-fresh .circuit-cache/stage47-trial2 .circuit-cache/stage47/proposal.json pass1
python3 design/architecture-278/implementation/stage47/local-reroute/accept.py .circuit-cache/stage44-b2-fresh .circuit-cache/stage47-fresh .circuit-cache/stage47/proposal.json passfresh
python3 design/architecture-278/implementation/stage47/local-reroute/settle.py .circuit-cache/stage44-b2-fresh .circuit-cache/stage47-trial2 .circuit-cache/stage47-fresh .circuit-cache/stage47/proposal.json .circuit-cache/stage47/settlement.json
```

Settlement re-evaluates both gates after the final receipt/cap fixes and compares
full board bytes, snapshots and acceptance results. Both builds match exactly.
The earlier pre-review acceptance file remains local as acceptance-before-review.

## Focused and repository checks

Using existing /workspace/shared/osc-ci-python/bin/python:

```
python -m unittest scripts.checks.test_local_ground_reroute scripts.checks.test_ground_escape scripts.checks.test_b2_specific scripts.checks.test_b2_specific_settlement -v
python -O -m unittest scripts.checks.test_local_ground_reroute scripts.checks.test_ground_escape scripts.checks.test_b2_specific scripts.checks.test_b2_specific_settlement -v
python3 design/architecture-278/implementation/stage45/connectivity-inventory/verify_bindings.py
python3 -O design/architecture-278/implementation/stage45/connectivity-inventory/verify_bindings.py
pnpm circuit:check
pnpm check
git diff --check
```

**49 tests pass in normal and optimized Python**, no skips locally:
16 Stage47, 5 Stage46 and 28 retained Stage44 tests. Stage47 includes 13 portable
adversarial controls plus 3 local artifact tests. Stage44 test logs print a
synthetic acceptance result; it is not evidence for a new Stage44 board.
On CI, the 3 Stage47 and 1 Stage46 tests requiring large ignored native artifacts
explicitly skip when absent; all portable controls still run. Local full replay
and native checks provide the missing ancestry, not a claim that CI recreated it.

Seven historical checkpoint bindings and four Stage41–44 review manifests pass
in both modes. Stage45 (30 files) and Stage46 (37 files) review manifests also verified.
Full historical suites and canonical regeneration were not duplicated locally;
exact-head CI supplies those repository-wide checks. CI outcome is reported
externally after push, tied to the exact SHA.

Both pnpm checks pass. Circuit evidence still has 68 manual inventory lines and
zero declared placements; no schematic/placement binding or sourcing qualification.
The before/after SVG is generated from pinned Stage46 native-derived geometry
and exact Stage47 proposal coordinates, and rendered for visual inspection.

## Review and retained failures

Fresh-context independent review replayed the full first accepted identity and
partition proof, inspected fresh native reports and verified identical fresh
board/snapshot/acceptance bytes. Its requested receipt-metadata and non-silk cap
hardening was implemented before final settlement/tests. New negative tests reject
those cases, wrong ground merges, unrelated signal changes, duplicate/missing
objects, new-only islands and wrong counts. The initial test invocation occurred
before native snapshots existed and explicitly skipped its local replay case;
final runs above include it. No failed assertion or native warning was waived.

Source verification is distinct from native rule/connectivity verification, and
both are distinct from physical/electrical/manufacturing qualification. The latter
remains NOT RUN, including assembly treatment for the via inside R8270:2 SMT pad. No canonical or historical file changed.

## Replaying from an authorized prepared environment

Require the exact ignored baseline board/snapshot/dependencies from settlement,
the installed oracle and pinned numerical environment. Verify hashes first.
Use a new owned directory directly under .circuit-cache, matching baseline depth,
and copy its schematic/project/rules/sheets/library tables before applying
proposal.json via scripts/pcbgen/grid_apply.py. Run DRC/refill/save and native
snapshot before acceptance. Never overwrite canonical, baseline, previous-stage
or prior evidence outputs; never re-pin hashes to different inputs. Without the
ignored artifacts, only portable source tests are available—not native replay.
