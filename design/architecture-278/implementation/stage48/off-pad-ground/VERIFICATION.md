# Stage48 verification and limits

Existing portable bootstrap was already consumed; it was not rerun. Executor
availability was verified successfully once. Repository instructions/current
head/latest issue state were read before work; PR287 remained draft at ce732b7.
`pnpm circuit:check` passed before edits (68manual lines, zero placements).
Canonical regeneration and full historical replay were not duplicated locally;
this bounded task uses exact-head CI for repository-wide coverage.

Native commands, installed KiCad10.0.6 through scripts/kicad/run.sh:

```
bash /home/agent/.codex/scripts/heavy-guard.sh --label stage48-offpad-trial -- bash .circuit-cache/stage48/trial1.sh
bash /home/agent/.codex/scripts/heavy-guard.sh --label stage48-b-only-trial -- bash .circuit-cache/stage48/trial2-b-only.sh
```

Each driver applies its retained proposal to Stage44 in a fresh owned directory
at the same depth as baseline, then runs Stage44 drc_run.py (schematic parity,
refill zones, save board, full JSON severity) and Stage41 connectivity.py.
Drivers are retained in evidence/. Trial1 process PASS123s; Trial2 PASS112s.
These are **rejected designs**, for the distinct reasons in README, not accepted
fresh-pair settlement. No expanded-scope candidate or independent fresh repeat
was run because the parent explicitly requires scope review first.

`inspect_trials.py` verifies full native inventory, exact new copper contracts,
all retained geometry/footprints, complete disjoint connectivity partitions,
DRC execution/dependency bindings and exact uncapped warning differences. Its
receipts bind ignored full boards/snapshots by SHA; those oversized artifacts
remain local. Portable tests validate retained DRC evidence and adverse controls;
local replay additionally verifies the actual boards and full snapshots.

First audit invocation failed because it requested UUIDs from non-object
S-expressions. Fixed by restricting retirement inspection to segments before
UUID lookup; failure was not a candidate failure or waived assertion.
Exploratory screen initially treated refillable AGND polygons as hard obstacles;
corrected before either native trial. An exploratory command also had a Python
SyntaxError; no board was modified by it. Initial zone-width screen assumed0.25;
actual B AGND source is0.15, unchanged in every candidate. Neither rejected
native result depends on claiming the initial screen was a proof.

Final focused commands and actual results are recorded in WORK.md. Source tests,
native rule/connectivity verification and physical qualification are distinct.
No physical, manufacturing, energized or canonical-output validation occurred.
