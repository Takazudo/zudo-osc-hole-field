# WSL production numerical failure and candidate correction

Original exact request `beb7f4d8bad67fa1d525abdbbe378f3934efccbc68d0f38657c7933ebdbeeca4` at head `4bde7e8adadd931e8c3655013a9a6223f913933f` was separately approved by the owner's “ok continue” after the exact approval request and pending-work explanation. The approval and single-use claim were recorded before launching the exact requested command. All332 input hashes/tool versions and live user-systemd2GiB/no-swap scope were checked.

## Preserved results

The whole-device service census passed:151 supported,59 partial,21 unserved and194 unmapped groups;302 eligible pads, zero signed included-current residual. Both nominal +12V board reductions completed as processes but **failed numerical acceptance**:

| Reduction | Load-relative residual | Required maximum | Result |
|---|---:|---:|---|
| KA | 1.4499316030378085e-9 | 1e-9 | FAIL |
| KB | 1.227478631500586e-9 | 1e-9 | FAIL |

Three KA driving-point chunks completed within180s and met their residual threshold. The old driver checked process exit only, so it continued past both failed reduction diagnostics. After explaining the failure and offering a stop/full-collection preference, with no reply received, the integration owner applied the approved stop-on-failure condition and stopped only the active owned user scope. The first KB driving-point chunk is therefore **deliberately interrupted, exit-15**, not a timeout, OOM, spontaneous crash or completed numerical result. The original command exited1; shared heavy guard recorded FAIL. All six observed solver scopes are inactive; no solver remains. Scope observations show a maximum1,716,764,672 bytes with the2GiB/no-swap caps. Input hashes remained unchanged through shutdown.

Six steps completed; the seventh was interrupted. **No coupled state was produced.** Remaining process cases/nets, remedy variants, full node-KCL/energy closure, and electrical acceptance remain NOT RUN or unresolved. Original partial outputs/receipts are unchanged, with external pickle hashes listed in index.json; no retry/resume/reset occurred.

## Scoped source correction

Source `c8b2db34e7501b5ae5adb46e7b24710b1f3559cb` now checks reported reduction, driving-point and coupled diagnostics against the existing declared tolerances. Missing/nonfinite metrics, incomplete coupled states and failed energy sign checks fail closed. Each unit retains its original output and a hash-bound numerical verdict before returning failure; the ledger binds the verdict too. Both board reductions must pass before either board's driving-point chunks begin. Process exit0 alone cannot promote numerical failure to acceptance.

A tiny independent two-node fixture demonstrated a float64 solution-accumulation precision floor even with extended residual evaluation. The candidate correction preserves only the single load solution in numpy.longdouble through refinement and node reconstruction. Multi-RHS arrays remain float64; the small interface RHS is explicitly float64 for NumPy solve compatibility. The coupled and independent KCL reconstruction paths both preserve the load-vector precision. Equations, loads, three refinement corrections, tolerances and resource guards remain unchanged.

The analytic fixture and small coupled/monolithic tests pass, including a live check that widened node vectors reach coupled KCL. This does **not** prove the production root cause, revised production memory usage, coupled residual/energy accuracy or full electrical acceptance. Source changes invalidate the old request; a fresh final-head request is required before any production retry.

The standalone prototype remains at `/mnt/c/Users/takaz/Dropbox/cclogs/zudo-osc-hole-field/repro-numerical-residual`; its source hash and results are retained. Prototype code is not a production input. Independent review found and corrected an intermediate float64 reconstruction downcast before final source review. See review.md and final-source-checks.json.

Prior native results remain: matched fill/census reconciliation PASS with KA196 / KB486 / separate KB-P1 480; capped DRC reports and board acceptance FAIL/INCOMPLETE. Prior KA long-B194 remains distinct. Physical source/load/full-path resistance remain unresolved. KEEP_K1402_INCUMBENT; protected geometry/decision unchanged; PR260 draft/unmerged, issue253 open.

Final source verification:44 affected source tests PASS; circuit/doc check, guarded documentation build and strict site check PASS (existing link allowlist unchanged). No production retry was run.
