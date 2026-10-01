# P fresh current-source native prerequisite: read-only plan

## Finding

`control_model_gate.require_native_prerequisite` cannot admit the retained P v3 export at the current source epoch. Its board, DRC, export, and copied companion hashes still match, and its native result reports zero rule/parity errors with all 344 ground contacts connected. Its receipt, the upstream bare v2 receipt, and the main-via plan each retain exactly three stale dependencies: `design/reports/io-partition.json`, `scripts/pcbgen/extract_power_geometry.py`, and `scripts/pcbgen/native_stack.py`. The old IO has a separate bounded geometry bridge, but that bridge deliberately does not make the old native/model receipt current. Do not rewrite any old digest or use `.circuit-cache/issue38-recovery/white-land-review/io-partition.json` in the fresh path.

The authored P proposal and generated definition/DRU/definition receipt are **current**: all seven direct generator receipt hashes and all four `geometry_source_sha256` entries match live source. Existing `candidate.json` still hashes the stale bare v2 receipt and plan, so simply rerunning `build_control_ground_feasibility.py` against it fails. The smallest valid source-first path starts at the current authored/generated definition, regenerates bare native authority, replans the six finite main arrays, and builds a fresh candidate from a new exact-hash config. It need not regenerate the P definition unless those source hashes change before execution.

## Ordered command path

Run from the issue38 worktree. Use fresh `v4` names (or the next unused version) throughout; never overwrite v3 or earlier evidence. Run `pnpm circuit:check` before any edits and after the path. All KiCad calls use the pinned oracle; heavy native runs use the shared guard.

1. Recheck the seven direct definition receipt hashes and four geometry source hashes against current files. If one differs, run `python3 scripts/pcbgen/generate_control_ground_feasibility.py design/partition/control-ground-feasibility/proposal.json design/partition/control-ground-feasibility/osc-control.json`, then verify its generated diff and hashes. Present state needs no definition rewrite.
2. Fresh bare export:

   ```sh
   bash /home/takazudo/.codex/scripts/heavy-guard.sh --max-run 1800 --min-mem-mb 5000 --label issue38-P-bare-v4 -- bash scripts/kicad/run.sh python3 scripts/pcbgen/build_control_ground_bare.py design/partition/control-ground-feasibility/proposal.json design/partition/control-ground-feasibility/osc-control.json boards/osc-control/osc-control-ground-bare-v4.kicad_pcb .circuit-cache/issue38-recovery/control-ground-bare-v4
   ```

   Require bare receipt `rule_error_count=0`, `schematic_parity_count=0`, current IO/exporter/stack hashes, and actual same-board DRC. Bare is still prohibited from model entry.
3. Replan from that new source-bound bare geometry, using the pinned local numerical environment (system Python has no Shapely):

   ```sh
   .circuit-cache/issue38-recovery/solver-venv/bin/python -m scripts.pcbgen.plan_control_arrays .circuit-cache/issue38-recovery/control-ground-bare-v4/bare-geometry.json .circuit-cache/issue38-recovery/control-ground-bare-v4/bare-native-receipt.json design/partition/control-ground-feasibility/osc-control.receipt.json design/partition/control-ground-feasibility/main-via-plan-v4.json
   ```

   Inspect all six rows, retained and blocked identities, and count. The old plan had 150 sites; equality is an observation to verify, not a hash to carry forward.
4. Create `design/partition/control-ground-feasibility/candidate-v4.json` from current `candidate.json`, replacing the four `bare_*` input paths/hashes and the `main_via_plan` path/hash with the fresh v4 artifacts. Keep `manifest` and `definition` pointing at their current files and recalculate **all seven** input SHA-256 values from actual bytes. Update the `allowed_changes` descriptive count only if the new plan count changes. This config is a source input and should be reviewed before the native build. Do not point it at the historical IO cache.
5. Fresh full candidate:

   ```sh
   bash /home/takazudo/.codex/scripts/heavy-guard.sh --max-run 1800 --min-mem-mb 5000 --label issue38-P-native-v4 -- bash scripts/kicad/run.sh python3 scripts/pcbgen/build_control_ground_feasibility.py design/partition/control-ground-feasibility/candidate-v4.json boards/osc-control/osc-control-ground-feasibility-v4.kicad_pcb .circuit-cache/issue38-recovery/control-feasibility-v4
   ```

   The builder verifies the upstream bare receipt, source manifest, plan, exact copied companions, original pad/hole/block preservation, KiCad 10.0.6 DRC/parity, and all 344 connected contacts. It writes `ground-feasibility-geometry.json` and `ground-feasibility-native-receipt.json` only for the fresh candidate.
6. Call `control_model_gate.require_native_prerequisite` on those v4 files and `design/partition/control-ground-feasibility/osc-control.receipt.json`; require its PASS and inspect its dependency map. A minimal invocation is:

   ```sh
   python3 -c 'from scripts.pcbgen.control_model_gate import require_native_prerequisite as gate; from pathlib import Path; c=Path(".circuit-cache/issue38-recovery/control-feasibility-v4"); r=gate(c/"ground-feasibility-geometry.json",c/"ground-feasibility-native-receipt.json",Path("design/partition/control-ground-feasibility/osc-control.receipt.json")); print(r["status"],r["full_source_ground_inventory"]["connected_count"],len(r["dependency_sha256"]))'
   ```

   Then run the focused P tests and `pnpm circuit:check`; update aggregate current-source consumers to the new artifact paths, regenerate their receipts, and rerun their gates. Existing P nominal matrices are historical unless rerun or a separately reviewed equivalence proof is made.

## Risks and limits

- The fresh bare export can change byte hashes and potentially physical geometry because `native_stack.py` and the exporter changed. Replanning is mandatory; do not assume old 150 sites or v3 board equivalence. If the fresh candidate loses a connection or shows rule/parity errors, repair source/generator and repeat the chain, never patch the receipt.
- `build_control_ground_bare.py` freezes current `io-partition.json` and both changed helpers. The old bare receipt and old candidate config fail source checks; no old IO cache is needed or appropriate.
- A passing P native gate admits a **draft nominal model input**. It does not settle own-load current, physical solder/lead/contact support, material and manufacturing intervals, rail/signal routing for issue39, or whole-system voltage/common limits.

No source, native, or heavy run was performed for this review. The only file written is this plan.
