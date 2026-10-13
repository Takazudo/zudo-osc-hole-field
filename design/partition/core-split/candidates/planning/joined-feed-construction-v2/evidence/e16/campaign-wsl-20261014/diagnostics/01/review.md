# Independent driving-point diagnostic source/packet review

Reviewer `/root/review_admission`, separate Codex agent, 2026-10-14. Read-only source/hash/JSON/OS inspection; no production-input load, solve, native operation, admission receipt or execution. Prepared a separate read-only process observer outside execution inputs. No test suite was needed to alter the unchanged execution controls; source review is not represented as tested execution.

Initial packet reviewed: `.circuit-cache/e16-dpoint-diagnostic-65d062bf`, SHA-256 `a6a7cb8bb73daca66b385ae3e4466ce97bde7cb345e33b68458467fcb00eca98`, clean HEAD `9f69cd8a2e7b80cba813a5bd66546c4d5ac705ec`.

## Source review

The driver enforces exactly one diagnostic unit and at most32 of the96 failed-chunk pad positions. It creates a fresh external output, authenticates spec inputs, invokes exactly one unchanged Ledger.run with the pinned UnitGuard, then asserts one log entry. No resume, retry, variant or full-baseline dispatch exists. The inherited hook ceiling148 is explicitly not a diagnostic authorization: request scope/spec restrict actual execution to1, charged against24 campaign diagnostic units.

The probe reexecutes its own exact argv in user-systemd with2GiB/no-swap and proves live caps before NumPy/source import or matrix loading. It does not import and call finite_solve.enter_memory_scope, which would run the wrong script. It preserves the same operator/coverage/config/cases and matches the complete first96 pad list against the original failed output before selecting first32. Exactly two16-column batches are compared; all candidate columns are sequential, one factorization is shared, and only projected e/q outputs are retained. It does not allocate a full extended multi-RHS solution. Original batch residual scratch is explicitly freed before candidate solves. Existing180-second timeout and guard remain unchanged; any resource failure stops and preserves negative evidence.

The original uses production refined_solve and production e/q expressions. Candidate columns use the existing extended_solution path with the same3 corrections. Multiplying each relative residual by its own RHS max then dividing the maximum absolute residual by whole-batch max preserves the existing batch normalization. Candidate residuals must be finite/nonnegative before aggregation and all batch results must meet unchanged1e-9 after report retention. Inputs are rehashed at end. This is a useful diagnostic, not a production artifact replacement or electrical acceptance.

Interpretation limits: batch-float64 versus sequential-extended changes per-column LU/iterate selection as well as accumulator storage. A passing candidate supports that combined numerical strategy; it alone does not uniquely prove accumulator loss. Use a separate analytic fixture or sequential-float64 control before attributing the cause solely to precision. First32 may omit the failing RHS; if all original batches pass, this diagnostic has not reproduced the actual criterion failure. Preserve that result honestly and justify any next bounded selection.

## Packet findings before admission

All341 bound hashes match, clean exact HEAD verified, output and claim absent, packet initially contains only spec/request. Driver SHA-256 `b402e6f4c002ae7a2c80dd0e3e03f3b9cad89ab0008d486d64b2e9026ad3133f`; probe `6b9ba7c061793cfe80fec020cdda4d2696e8833278a3f35170f5a13bd9e0c181`.

Two metadata corrections requested before approval/execution:
1. guards.scope still names finite_solve.enter_memory_scope, although the diagnostic performs its own exact-script reexec and live verification. Correct this evidence attribution.
2. prior_failed_request points to attempt3; this diagnostic is tied to attempt4 digest `e61a727361ad1a2fd0418d6d95c0cdae109a536d8b62a99654970685c0819c87`. Correct that provenance.

Preserve the superseded prepared request; record/review the corrected request digest before delegated authorization. Source/containment design has no blocking finding. Packet gate remains pending those metadata corrections and corresponding exact-digest verification.

## Observation

`reviewer-monitor-diagnostic.py` is prepared in the campaign directory. It accepts --packet and --evidence, samples once/second, distinguishes actual Python probe argv from launchers, records scope caps/peak/events, and exits when the hook terminal receipt exists. It has not been launched by this review. Hook finite_solve-only sampling is explicitly not claimed as independent diagnostic observation. The probe report also retains its own actual cgroup values. Coordinator should launch observer before/with admitted workload and retain raw evidence through terminal cleanup review.

## Corrected exact packet: PASS for delegated admission

Re-reviewed current request SHA-256 `aa4d462083736dce579d1730cd33f4b0baf0cda906dee0fc88504e99565332ed`. The two metadata findings are corrected; superseded request is retained unchanged as request-pre-review.json with original digest `a6a7cb8bb73daca66b385ae3e4466ce97bde7cb345e33b68458467fcb00eca98`. All341 input hashes reverified.

Scope is now first16 of96 pads, one16-column batch, with original float64 batch, sequential float64 control and sequential extended candidate. Sequential control and extended candidate use identical vector LU/refinement paths except accumulator precision, reducing the earlier interpretation ambiguity; all retain3corrections and whole-batch normalization. Candidate residuals still fail closed above1e-9. Driver remains exactly1unit, no retry/resume or other scope. Amended probe SHA-256 `f6b98dd4c62d1516b6a99a14ed31bf50f6041855ebb5f40c27ec7208a0597fde`. Source change is limited to control measurement and narrower selection. No test/production execution was performed by this reviewer.

Packet/source review PASS, subject to exact delegated receipt, durable1diagnostic budget charge, unchanged-hook immediate live preflight/exclusive claim and terminal integrity/cleanup. This review creates no authority or numerical result. The selected16 may still omit the previously failing RHS; distinguish nonreproduction from proof of correction.

## Terminal diagnostic1 review: integrity/cleanup PASS

Consumed request `aa4d462083736dce579d1730cd33f4b0baf0cda906dee0fc88504e99565332ed` ran exactly once, one unit, hook exit0 after89.57576837192755s; unit elapsed88.237s, shared guard PASS exit0 secs90 minimum available8944MiB. All341 bound hashes still match. Request/approval/head/clean-checkout terminal assertions true; persistent claim result equals packet receipt; full log, observations, output and step streams match their retained hashes. Delegated authorization scope accurately limits the execution to1diagnostic unit/first16pads, with original standing instruction and executor/account distinction retained.

Actual result: original batch4.017385299657123e-10, sequential float64 control3.9645425007968424e-10, extended candidate5.018693831950441e-13, unchanged criterion1e-9. Original and control both already pass. This subset does NOT reproduce the failed96-pad chunk; candidate improves its residual but does not prove the original full-chunk defect is corrected. A separately reviewed original-algorithm scan of the96pads to locate the failing16-column group is justified; no unchanged full-baseline rerun follows from this diagnostic.

Hook finite_solve-only observations are empty as expected and are not cited as scope evidence. Independent exact-probe observer retained87 actual diagnostic samples at verified2GiB/no-swap, all sampled memory events zero. Probe self-report peak1055375360bytes, reported RSS1057280KiB; observed scope `run-r0213db40af7448b6886bca27d7726e65.scope`. Final observer sample records terminal receipt and no processes; observer exited automatically. Observer-log SHA-256 `3542e36a9c5aeef0e41b89e6ce74475a2fb6004587f816cb819738b6aeb4caae`. Fresh scope query inactive, cgroup absent; no matching probe/driver/hook/observer, shared guard owner or held lock. No containment/integrity failure blocks next in-scope work.

No reviewer production/native/test execution occurred. Preserve this request/spec/driver/probe/output byte chain before changing diagnostic sources. Budget used: full-baseline1/3, diagnostics1/24.
