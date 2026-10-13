# Baseline numerical execution: first coupled node-KCL failure

One explicitly approved attempt ran on local WSL and stopped on its first numerical failure. **Batch FAIL; admission consumed; no retry or resume.** This is an unvalidated circuit draft, not board or electrical acceptance. KEEP_K1402_INCUMBENT remains unchanged.

## Exact identity and execution

- Execution HEAD: `0dab96a0fb6434da41765cb181bc8807544f0a7e`.
- Request SHA-256: `7daa746001d8965891df6135be0b08054e5ca0c7dc9981798429be2919b729e8`.
- Run: `19563d44a548466bbe43723a69ece2fe`, attempt 3, account `takazudo`, UID 1000.
- Checkout: `/home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-r4`.
- Packet: `.circuit-cache/e16-numerical-0dab96a-19563d44/` in that checkout.
- Output: `/home/takazudo/.cache/zudo-e16-runs/coupled-approved-0dab96a-19563d44`.
- Actual user approval is quoted in `packet/operator-approval.json`; its SHA-256 is `09e52ea40881d4ffad559855e47ebc1b71d87cdcdd71b125aaf29a30966f6bcc`. No previous approval was reused.

The approved scope was baseline t2 KA/KB, whole-device `normal-typ-v1` subset, four nets, three process cases and uniform-dielectric depth, at most 148 sequential units. **Actual execution reached only +12V / nominal-average / uniform-dielectric:** service, both reductions, three KA and three KB driving-point chunks, then one all-present coupled unit. Nine units passed; the tenth failed. The other nets/cases and remaining coupled states were NOT RUN because the first failure stopped the batch. No remedy, finite regeneration, native execution or extra scenario was launched. The failed coupled output includes the existing method's built-in 110 mm wire-length sensitivity; no separate sensitivity command was dispatched.

The unchanged, hash-bound execution hook was invoked once, without an outer shared guard:

```sh
python3 /tmp/osc-wsl-20261013/execute_unit_guard_numerical.py --request /home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-r4/.circuit-cache/e16-numerical-0dab96a-19563d44/request.json --expected-sha256 7daa746001d8965891df6135be0b08054e5ca0c7dc9981798429be2919b729e8 --approval /home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-r4/.circuit-cache/e16-numerical-0dab96a-19563d44/operator-approval.json
```

This is a historical command, **not permission to run it again**. The persistent claim and terminal result are retained. Python 3.12.3, NumPy 2.2.6, SciPy 1.15.3 and Shapely 2.1.2 matched the request. `packet/request.json.gz`, `packet/execution-result.json`, all ten step ledgers and complete streams retain exact commands, hashes and versions. The hook and shared guard bytes are retained as text. `index.json` maps original and retained bytes.

## Execution and resource controls

The exact command exited 1 after 874.011 seconds. Each unit acquired the unchanged account-wide heavy guard independently. Nine guard receipts are PASS; the final receipt is `FAIL exit=1 secs=3 min_mem_mb=9380 reason=-`, propagating the numerical failure. It is not an OOM, timeout or environment-suspect result. No cap was increased or bypassed.

The live preflight proved `memory.max=2147483648` and `memory.swap.max=0`. All nine observed reduction/driving-point/coupled scopes had these limits and zero sampled memory events; peak observed memory was 1,717,420,032 bytes. Child peak RSS was 1,705,572 KiB. The short service scope was not caught by the two-second sampler: its CLI self-check and successful guard receipt are retained, without claiming an independent live sample. Unbounded launcher rows are preserved in the raw observation log and are not solver scope measurements.

Before any tracked edit, all 337 sealed inputs, request, approval, execution HEAD and clean checkout matched; all 550 protected files matched. All nine observed scopes were inactive and absent, no workload process remained, and the shared guard owner and lock were released. `postrun-integrity.json` and its retained checking script record these checks. No source, dependency, generated input, canonical board, accepted copper, placement or decision changed during the frozen interval.

## Numerical accuracy

All limits below remain 1e-9.

| Criterion | Observed | Result |
| --- | ---: | --- |
| KA reduction load residual | 2.9803321747950843e-12 | PASS |
| KB reduction load residual | 1.309884394382926e-12 | PASS |
| KA / KB interface residual | 5.19967204292978e-11 / 2.355131885196278e-11 | PASS |
| KA / KB reciprocity | 6.505757820259505e-15 / 1.0712628061069046e-14 | PASS |
| Six driving-point chunks, worst residual | 2.850814388399312e-10 | PASS |
| Coupled global KCL | 8.349850854768625e-11 | PASS |
| Coupled energy minus load work | 2.4892459643435285e-12 | PASS |
| Coupled KA free-node KCL | **1.515200877665821e-8** | **FAIL** |
| Coupled KB free-node KCL | **7.277530568849482e-9** | **FAIL** |

The first failing declared criterion is `all-present.max_free_node_kcl_relative`. Nonnegative energy is true; wire/terminal imbalance is 8.326672684688674e-17 A. The latter is a reported diagnostic, not an additional gate invented for this checkpoint. The original failed coupled JSON and its hash-bound numerical verdict remain intact. Neither the process nor the batch is relabeled PASS because other checks passed.

## Electrical scope and gaps

Whole-device service reproduced 151 supported / 59 partial / 21 unserved / 194 unmapped groups, 302 eligible pads and zero signed included-current residual. This is a supported quiescent subset, not full instrument loads.

The failed coupled state reports 116 injected +12V pads (KA 76, KB 40), 171.6 mA total subset current and approximately 77.44 mA through W1. Reported maximum source-referenced pad-drop magnitudes are KA 0.117419 mV and KB 0.288468 mV. **These are provisional outputs from a numerically failed state**, not accepted voltage results. AGND was not solved, so no new rail-minus-local-ground or return-removal conclusion is available. The output's copper figures exceed 1 mOhm at all 525 evaluated pads (KA 1.079–5.174 mOhm; KB 2.156–6.481 mOhm); their numerical acceptance likewise remains failed. No complete physical source-to-pad resistance claim follows.

Connectivity remains KA-t2 196 / KB-t2 486 unresolved identities, separate KB-P1 480 and distinct KA long-B 194. Physical source/protection geometry is absent, complete signed loads and GH380 conductor currents are unresolved, full-path resistance remains unqualified, and native DRC enumeration remains capped/incomplete. Previously completed native control/startup qualification, the single oracle test, matched fill/census and finite coverage remain complete in their recorded scopes and were not repeated. Installed/mechanical/process/bench qualification remains NOT RUN. Canonical boards, fixed panel positions, accepted copper and `decision.json` remain unchanged; PR260 stays draft/unmerged and issue253 open.

## Review and next task

Independent read-only review by `/root/review_e16` verified original packet/approval/claim bindings, all inputs and protected files, step/output/verdict hashes, scope/resource receipts, cleanup and exact scope. It performed hashing, JSON/gzip parsing, source inspection and read-only OS queries; no solve, pickle loading, hook, guard, test or approval execution. See `review.md`.

The reduction load vector retains extended precision, while interface basis `Y` and the `Y @ v_t` contribution are computed in float64 before subtraction in `reconstruct_potential`. That is a plausible precision/cancellation seam, **not a proven root cause**. Retained JSON does not identify the worst node or decompose its residual.

The smallest useful follow-up is a separately approved isolated +12V reconstruction diagnostic using these exact preserved reductions/operators: identify worst nodes, decompose load/interface/reconstruction residuals, compare the independently reconstructed operator with the reduced operator, and test wider reconstruction under unchanged tolerances and controls. Do not rerun the full batch, change production solver code or treat this consumed approval as diagnostic authority. Any subsequent execution requires a new exact request and approval.

## Retention and transfer

Compact packet, streams, verdicts, failed coupled output and service manifest are committed here. Eight pickle artifacts totaling **50,087,109 bytes** remain in the original supported WSL cache output directory; their individual sizes/hashes are in `index.json`. Sealed external inputs total **1,205,881,577 bytes** and are indexed by their original locations and hashes. Existing finite-input storage is preserved; no oversized PCB/pickle blob or Git LFS was added.

To transfer, copy the output directory, packet directory and the `sealed_external_inputs` paths from this WSL host to approved retained storage with `rsync -a` or equivalent. Preserve the original bytes and verify every destination against `index.json` and the decompressed request manifest. Repository inputs are available at the exact execution commit. Copying artifacts does not authorize execution at a different path or on another host; the existing request is consumed and path-bound.

Full regeneration/native checks and aggregate tests were NOT RUN for this evidence-only checkpoint: they are outside the approved execution scope and would repeat or invoke excluded native work. Focused checks PASS: `pnpm circuit:check`, `pnpm check`, shared-guard `pnpm build`, and `pnpm check:site`. The strict site check retains the unchanged existing single allowlist exception. SCOPE: manual inventory 68 lines, no schematic/placement binding, pin-asset check performed. Exact commands, exit statuses and logs are recorded in `checks.json`.

CI for this evidence-only publication is NOT RUN (`[skip ci]`); no additional native or aggregate execution is admitted.
