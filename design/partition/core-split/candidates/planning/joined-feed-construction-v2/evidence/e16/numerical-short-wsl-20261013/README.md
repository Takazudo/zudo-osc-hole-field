# Admitted short production reduction recheck

Execution head: `a73249c9f98f8fa9fd5d27aed85265062c74a907`.
Executable source: `fc1800fd8af5647ed51588be01732ebcbbf8a411`, including the precision/failure-gating correction at `c8b2db34e7501b5ae5adb46e7b24710b1f3559cb`.
Exact request: `8f8d104e1b349f063ef7627cc52a66dd64486690b938407ef03916d659ab9665`.
The owner replied “k” to this exact short request. The contextual approval and persistent single-use claim were recorded before execution; this receipt authorizes no later work.

Scope was only normal-typ-v1 whole-device service and the KA/KB baseline t2 +12V, nominal-average, uniform-dielectric reductions. Exactly three steps completed. No driving-point chunks, coupled states, other process/depth/net cases or remedy variants ran. Existing finite coverage was reused without rebuilding it. The original failed run remains unchanged in `../numerical-wsl-20261013/`.

| Reduction | Original load-relative residual (FAIL) | Recheck (PASS) | Unchanged maximum |
|---|---:|---:|---:|
| KA | 1.4499316030378085e-9 | 2.9803321747950843e-12 | 1e-9 |
| KB | 1.227478631500586e-9 | 1.309884394382926e-12 | 1e-9 |

Interface residuals are 5.19967204292978e-11 / 2.355131885196278e-11; reciprocity residuals are 6.505757820259505e-15 / 1.0712628061069046e-14. All reported reduction criteria pass without changing equations, loads, three refinement corrections or tolerances. Extended load-solution accumulation resolves the observed reduction failure on these two production inputs; it does not establish all coupled-state accuracy. The platform dtype label `float128` denotes numpy.longdouble here, not a claim of 128-bit arithmetic precision.

Service remains 151 supported / 59 partial / 21 unserved / 194 unmapped groups, 302 eligible pads, zero signed included-current residual. These are supported quiescent subset loads, not complete instrument loads.

## Resources, provenance and review

The exact command, Python/package versions, source/input hashes, approval, immutable claim, complete stdout/stderr, three step ledgers and output-bound numerical verdicts are retained and indexed. Large reduction pickles remain local and ignored, with paths, sizes and hashes in index.json. No LFS or artifact deletion.

Command exit 0; elapsed 89.251 seconds. Shared guard: `verdict=PASS exit=0 secs=91 min_mem_mb=8612 reason=-`. Both actual solver user-systemd scopes enforced memory.max=2147483648 and memory.swap.max=0. Sampled peak was 1,668,386,816 bytes; reported child peak RSS was 1,657,300 KiB. No observed OOM events. Both scopes are inactive afterward. The unbounded tmux rows in the monitoring log describe launcher processes, not the solving scopes. All 334 request input hashes and 550 protected files matched after execution.

Independent read-only review by /root/review_wsl_admission: PASS. The reviewer checked admission/claim identity, three-step scope, output/config/verdict hashes, unchanged limits, input integrity, guarded memory and cleanup. See review.md and postrun-integrity.json.

## Remaining work

The short production reductions PASS; complete production driving-point/coupled validation, node-KCL/energy closure, other cases/nets/depths and remedy numerical validation remain NOT RUN on this source. Next, prepare and independently review serialized numerical scheduling whose bounded units fit the unchanged shared heavy guard, then obtain one separate approval binding the exact final request digest. The superseded several-hour single-guard request cannot be reused: the guard's unchanged whole-command limit is 1800 seconds. No additional production execution is approved by this result.

Native fill and pad/feed/peer reconciliation previously passed. Board acceptance remains FAIL/OPEN with unresolved identities KA-t2 196, KB-t2 486 and separate KB-p1 480; DRC enumeration is capped/incomplete. Prior KA long-B 194 is distinct and lacks native/electrical acceptance. Physical source/protection geometry, unsupported loads, full-path resistance and installed qualification remain unresolved. KEEP_K1402_INCUMBENT; canonical boards, locked placements and decision.json unchanged; PR260 draft/unmerged; issue253 open.

Documentation verification: circuit check before/after, pnpm check, shared-guard documentation build and strict site check PASS. Existing single site-link allowlist exception is unchanged. SCOPE: manual inventory, 68 lines; no schematic/placement binding; pin-asset check performed. No aggregate suite or production rerun was performed.
