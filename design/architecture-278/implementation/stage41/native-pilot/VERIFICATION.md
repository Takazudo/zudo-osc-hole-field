# Stage41 verification boundary and command receipt

Starting repository/PR287 head: `977c657a244fa4e80f6eefbb8eb15acc78453799`; branch `agent/278-stage28-din-harness-20261017`. Remote head, latest Issue278 report and PR description were reread during this continuation. PR remains draft. Parent286 was independently refetched at `b58068fbaeb65886958a67a4f4978613414e31c5`. Existing portable bootstrap and repository/circuit instructions apply; bootstrap was already fully consumed and was not rerun.

The parent explicitly authorized the disposable native continuation after the earlier negative pilot. The original source-only stage prohibition was not silently treated as native authorization. This continuation changes no canonical manufacturing output and does not adopt an architecture or perform hardware work.

## Tools and original failures

The official exact-release KiCad10.0.6 Lite AppImage was extracted task-locally. CLI and bundled pcbnew both report10.0.6. Archive302243840bytes; official MD5 `fd37a7d7580a66598426105dbf841856`; SHA256 `8c789e36644856cff30a66801692881582b9ca7c7475699494e614ce1bcb1f9c`. CLI executable SHA256 `1108ea3589e75aa274adad754275709da326f89614a9c6ce6fc456a430ef1a4b`; pcbnew.py SHA256 `1174b0cf84828d98070783843d1bfe2007d2ec1fff1735bb7ca562d8f747cf52`. Signature verification remains not completed (public-key endpoint403). No equivalence claim to the pinned Docker image beyond exact release/version.

Earlier Docker/vfs root exhaustion, missing-Shapely driver, native preparation face assumption, nine-package25-error and complete15-package22-error trials remain retained. The complete trial also reassigned two−12V segments and one via to a signal net; the new regression fixture retains those exact before/after objects. Current native/raw guards reject that condition before accepting any connectivity result.

This continuation preserves the C3101+2mm fixed-J209 courtyard failure, rejected positive anchor-via deletion, five/three unresolved routing links at0.075/0.025mm, unsupported SWIG type-filter call, and the generator-indexing test-fixture failure. The successful0.05mm route does not erase these failures or establish continuous routing optimality. Review fixes and caveats are recorded in WORK.md and README.md.

## Executed commands

All native/heavy jobs use the installed foreground guard:

```
bash /home/agent/.codex/scripts/heavy-guard.sh --label <stage41-label> -- bash <retained-driver.sh>
```

Drivers source `/workspace/task-tools/kicad-10.0.6/env.sh` and invoke `bash scripts/kicad/run.sh`. The supported `KICAD_CLI_BIN` override selects exact task-local tools. No HOME/CODEX_HOME reassignment. Driver scripts and complete logs are retained under `.circuit-cache/stage41-native-capability/` and in the local evidence archive.

Executed native pipeline drivers: `power-check.sh`, `signal-check.sh`, `power-verify.sh`, `clean-check.sh`, `settle.sh`. Guard exit0 means process completion only; actual DRC, identity, connectivity and power gates are separate. DRC invocation:

```
bash scripts/kicad/run.sh kicad-cli pcb drc --schematic-parity --refill-zones --save-board --format json --severity-all -o <report.json> <disposable-board.kicad_pcb>
```

After each final DRC/refill, `audit.py` checks complete object identities and prepared/foreign geometry, `connectivity.py` records occurrence-aware native components, `compare_connectivity.py` binds them to exact reviewed deltas, and `verify_power.py` checks all six mandatory power paths. The collector `settlement.py` requires three equal full memberships and a fresh-copy result, bound to exact board/receipt hashes. Capped silk categories remain unresolved; every other warning category must be below its cap and have no new warning identities. One removed old private dangling segment is explicitly within the retirement ledger.

Source commands:

```
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/checks -p 'test_native_pilot_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 -O -m unittest discover -s scripts/checks -p 'test_native_pilot_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 [-O] -m unittest discover -s scripts/checks -p 'test_mult_copper_plan.py'
pnpm circuit:check
pnpm check
```

Final focused source suite33PASS normal and33PASS optimized. Retained Stage40 suite8PASS normal(9.497s) and8PASS optimized(5.185s). All seven `architecture_history.verify_binding` checkpoints/eight retained modules pass normal and optimized. Full historical replay was not repeated locally; the existing bounded exact-head CI supplies it after reviewed normal push. No checks or timeouts were weakened.

Repository checks pass. Circuit scope is manual inventory68lines; schematic/placement binding not performed; pin-asset check performed. Documentation/type checking is not native board qualification.

## Final-result interpretation

The final machine-readable `evidence/settlement.json` records completed native passes and hashes. It accepts only the bounded electrical/connectivity pilot. The baseline117opens and capped silkscreen categories preclude a blanket full-board DRC or manufacturing-readiness claim. No physical measurements, analog performance tests, energization, fabrication, ordering, release, deployment or merge were performed.

The full boards/snapshots and first failures stay local and ignored; small proposals, scoped receipt, contact proof, native summaries and source regressions are committed additively. No Git LFS. Exact final commit and terminal CI status are posted externally in Issue278/PR287, avoiding a self-referential source commit hash. Stop for parent review after this bounded pilot.
