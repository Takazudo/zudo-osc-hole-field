# Stage49 verification

Native oracle: installed KiCad10.0.6 through scripts/kicad/run.sh; no installation
or Docker. Exact guarded commands:

```
bash /home/agent/.codex/scripts/heavy-guard.sh --label stage49-led-tail -- bash .circuit-cache/stage49/trial1.sh
bash /home/agent/.codex/scripts/heavy-guard.sh --label stage49-independent-fresh -- bash .circuit-cache/stage49/fresh.sh
```

Both drivers are retained under evidence/. Each separately applies proposal.json
to the pinned Stage44 baseline in an owned directory at baseline depth, then runs
schematic-parity DRC with refill/save and exports full native connectivity. First
run PASS114s; fresh PASS116s. No new native failure or waiver. Fresh build starts
from baseline, not a copy of the first candidate. Both boards contain37779objects.

After review hardening, exact acceptance and settlement commands:

```
python3 design/architecture-278/implementation/stage49/led-tail-cleanup/accept.py .circuit-cache/stage44-b2-fresh .circuit-cache/stage49-trial1 design/architecture-278/implementation/stage49/led-tail-cleanup/proposal.json pass1
python3 design/architecture-278/implementation/stage49/led-tail-cleanup/accept.py .circuit-cache/stage44-b2-fresh .circuit-cache/stage49-fresh design/architecture-278/implementation/stage49/led-tail-cleanup/proposal.json passfresh
python3 design/architecture-278/implementation/stage49/led-tail-cleanup/settle.py .circuit-cache/stage44-b2-fresh .circuit-cache/stage49-trial1 .circuit-cache/stage49-fresh design/architecture-278/implementation/stage49/led-tail-cleanup/proposal.json design/architecture-278/implementation/stage49/led-tail-cleanup/settlement.json
```

The initial pre-review acceptance is preserved locally as acceptance-before-review,
and its log retained. Final settlement re-evaluates both gates, validates both
baseline and candidate native execution/dependency receipts, binds every retained
artifact hash, and compares complete board/snapshot/acceptance bytes. All agree.
Exact added-object fields are checked, so a new tenting or other property cannot
silently enter a geometry-only allowlist. Uncapped warning multiset is unchanged;
capped silk identity remains UNRESOLVED. Native pass is not assembly qualification.

Focused normal/optimized Python tests use the pinned numerical environment
`/workspace/shared/osc-ci-python/bin/python`. Stage49 has20controls, Stage48 has11.
The first final command runs19+11; a subsequently added portable retained-evidence
hash test runs separately in each mode. Together31tests pass each mode, no local
skips. CI skips four Stage49 cases and one Stage48 case requiring ignored native
inputs when absent; portable negative and evidence-hash controls still run.

```
python -m unittest scripts.checks.test_led_tail_cleanup scripts.checks.test_offpad_ground_trials -v
python -O -m unittest scripts.checks.test_led_tail_cleanup scripts.checks.test_offpad_ground_trials -v
python -m unittest scripts.checks.test_led_tail_cleanup.module.AcceptanceTests.test_retained_evidence_bindings -v
python -O -m unittest scripts.checks.test_led_tail_cleanup.module.AcceptanceTests.test_retained_evidence_bindings -v
```

Failure preservation: initial18tests passed. First post-review19test run exposed
an invalid miniature-board fixture: the added-property negative test omitted the
outer kicad_pcb expression and failed its positive control. Fixed the fixture;
production gate was not relaxed. That failed log is retained. Assembly source
checker initially expected a closing parenthesis immediately after the MPN value,
but native properties contain nested metadata; fixed the literal prefix check.
No numerical threshold or geometry changed. The original four empty polygon
records are remote mounting holes, not silently assumed free solder-pad geometry.

`assembly.py --write` and replay use pinned Shapely; they bind baseline/dump/
footprint hashes and measure the pad/drill gaps and courtyard intrusion. Native
footprints/settings are unchanged, and new-object property checks enforce inherited
tenting. No manufacturing outputs were generated or inspected. Exact component
body/process validation remains unresolved. The SVG is source-derived and was
rendered with installed Chromium for visual inspection.

Repository checks: pnpm circuit:check before/after and pnpm check pass (manual
inventory68lines/0declared placements, no schematic/placement binding; pin-asset
check performed). Historical seven checkpoint and four Stage41–44 review bindings
pass normal/-O; Stage45–48 manifests verified separately. Staged whitespace and
Stage49 manifest checks pass. Full historical/aggregate regeneration was not
repeated locally; exact-head CI supplies it. CI terminal result is recorded on
the issue/PR after push. No physical/electrical/manufacturing qualification.
