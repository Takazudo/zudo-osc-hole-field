> Current campaign continuation is [WORK.md](../../../WORK.md), under [Takazudo’s recorded local delegation](owner-decision-20261014.txt). Seven genuine qualification-kind attempts are terminal failures; the latest [audit](qualification-attempt7/review.md) records 15/24 diagnostics, complete cleanup and the unresolved 20M-update certificate gate. Signing ownership is resolved; qualification remains NOT_QUALIFIED, production NOT_ADMITTED and Stage C NOT RUN. Historical source-only statements below retain their original scope.

# Independent admission and resource-boundary review

Reviewer: `/root/resource_review`. **PASS for the reviewed source boundary and bounded validation; RESOURCE NOT_QUALIFIED; no production execution.** This review is independent for the main author's `attribution_admission.py`, `attribution_request.py`, `attribution_worker.py`, and `attribution_lifecycle.py`. I authored the delegated host/supervisor and transport fixes, so their tests below are author validation, not independent self-review. Their separate cross-review is by `/root/numerical_review` and the main author. The numerical reviewer inspected the final watchdog, zero-swap proof and tightened aggregate caps and reported no remaining source findings.

The earlier executor checkpoint's absent host implementation is superseded: source now implements the fixed worker command, signed admission, one-unit durable accounting, provisioning, supervised execution, complete output retention, owned cleanup and final acceptance. This does not establish that the actual selected matrices fit, that this WSL host permits the required delegation/namespace/mount operations, or that authority/reservation exists. Those remain exact external qualification/admission gates. Production request digest remains null until a complete qualified production request is sealed; a source-description or qualification-request hash cannot replace it.

## Independently reviewed controls

The production path authenticates detached OpenSSH signatures against a fixed externally provisioned account trust store. Qualification, operator authorization and controller reservation use distinct identities/namespaces. Production and resource-qualification requests use distinct authorization namespaces; neither grant can authorize the other. The exact request, run/attempt, limits, operation, host boot/machine identity, immutable source/toolchain, original artifact bindings, validity window and campaign snapshot are checked. No signer-installation, signing, self-approval or reservation-creation command is provided.

Malformed/duplicate/nonfinite JSON, forged or missing signatures, changed trust bytes, stale digests, expired/short/nonexclusive/wrong-host reservations and missing resource qualification fail closed. Source preparation binds original compressed artifacts from independent retained evidence without decoding them; compressed original-request identity remains distinct from its decompressed identity. Sealing no longer revalidates selected artifact bytes outside the guard. The resource-qualification request kind avoids circular dependence on an existing resource-qualified receipt, while still requiring its own exact external authorization and reservation before any execution.

The real single-use claim uses O_EXCL, preserves the original ledger bytes in its journal, increments exactly one diagnostic and sets live-owned work. A failed launch remains consumed. The worker has its own nonreusable start token. Terminal accounting clears live-owned work only when cleanup completed, preserves historical run records, and binds the output manifest and request identity in a separate O_EXCL terminal journal. A crash between journal and ledger replacement is blocked for external reconciliation, not resumed or retried.

The worker proves actual guard ancestry, the held reservation descriptor, exact worker cgroup/no-swap limits, fixed result path and guarded deadline before authentication and numerical imports. Production Python uses `-I -S -B -X pycache_prefix=/dev/null`; disabling writes alone was insufficient because Python can still load stale bytecode. Source manifests reject unbound repository `.pyc`/extension overrides, include relevant namespace/package initializers, and bind the numerical environment and linked libraries. Loader/environment overrides and inherited execution identities are rejected; unrelated inherited credentials are removed. Only the authenticated fixed numerical site is inserted after checks.

The fixture API retains its low ceilings. Production rejects fixture requests before queueing. Fixture dictionaries do not act as production grants. The actual worker regression invokes the existing tiny serialized numerical pipeline after explicit mocked authority/kernel observations; these mocks are labeled and do not establish real admission.

## Host contract and honest resource limits

The host adapter was authored by this reviewer and independently cross-reviewed separately. Its fixed commands use documented local systemd 255 and util-linux interfaces. No real scope, namespace, mount or production worker was launched during this review.

Bounded metadata/authentication and claims are inside the shared guard. Full source/toolchain/input revalidation happens only after scoped kernel containment is established, and again in the worker. The shared guard's own entry timestamp conservatively anchors the 180-second clock; provisioning cannot reset it. An in-process SIGALRM watchdog interrupts blocked work with cleanup time reserved, then switches to a kernel-default fatal alarm at the hard deadline so broad exception handlers cannot swallow expiry. It adds no resident helper process. Work reserves time for worker kill, complete copying/hashing, unmount, child-cgroup removal, scope collection, accounting and terminal receipts.

The initial 2 GiB scope is tightened to a hard **1344 MiB** parent limit before full validation or numerical work. The complete source budget is:

- Scoped parent 1344 MiB + outer controller 64 MiB + systemd-run controller 64 MiB + bounded external controller/file-cache allowance 64 MiB + conservative shared-guard helper envelope 512 MiB (eight 64 MiB processes) = 2048 MiB.
- Within the scoped parent: worker 1216 MiB + supervisor 64 MiB + sticky bootstrap allocation allowance 64 MiB.
- Controller address spaces are limited before production validation. Supervisor and worker are separately constrained cgroups; all relevant groups prohibit swap. Peaks, limits, current usage and memory events are retained before cleanup, with a final parent sample after retention/cleanup. Post-run peaks supplement the hard limits; they do not replace them.

The unchanged shared-guard source hash binds its main shell, sampler, watchdog and bounded external helpers; their additional reserve is not hidden outside the sum. Host `SwapTotal=0` is required before claim because the scoped zero-swap setting alone does not cover outside controllers. This gate never changes host swap configuration.

The external controller/file-cache allowance and the complete operation still require host/resource qualification. This review does not turn an allowance into measured production evidence. Large toolchain enumeration/linkage inspection and repeated hashing, nine complete mesh passes per board, interval LDL/fill/factor objects, residual and functional enclosure passes, selected solve, original Assembly workspaces and complete accounting all remain part of the same combined qualification.

The dedicated tmpfs capacity is at most half the remaining aggregate output allowance, reserving both original and durable copy simultaneously, plus bounded logs, claims/accounting and receipts, under 64 MiB. No component is dropped to fit. Retention verifies every file before removing originals. Persistent I/O failure is reported with the available inventory/partial-copy evidence and explicit possible negative-artifact loss on mandatory cleanup; it is never reported as successful retention. No unbounded namespace keeper or numerical retry is introduced.

Only fresh scope identities may be created. A preexisting scope is refused before claim, and the created scope Description binds exact run and request digest. Cleanup verifies that ownership before killing or stopping a unit; a same-name race cannot authorize destruction of someone else's scope. Scope query, unmount or cleanup failure remains negative.

Host output stays **PENDING_SHARED_GUARD**. Read-only acceptance requires the immutable terminal journal/output binding, unchanged retained outputs and claim, false acceptance/adoption flags, and exactly one durable matching shared-guard PASS row with known memory, successful exit and the original time bound. The unchanged guard writes that row while holding its slot. Missing, failed, ambiguous or mismatched guard evidence cannot turn the pending result into COMPLETE. Historical signed grants are checked against the actual execution interval, not against a later inspection time.

## Findings closed

Independent findings on the main-authored code included unbound import shadows, overly broad pre-guard input revalidation during sealing, source-binding size bounds and the need for an independently retained terminal output-manifest binding. These are resolved in the reviewed hashes.

Separate host cross-review found uncounted controller/bootstrap memory, stale-bytecode loading despite `-B`, an environment-check API mismatch, acceptance based only on result-local hashes, editable acceptance flags, preexisting-scope ownership ambiguity, and retention-failure reporting gaps. The implementation and adversarial regressions now cover those cases. No unresolved source defect was found in the reviewed main-author admission/request/worker/lifecycle scope. Host syscall feasibility and combined real-data qualification are explicitly NOT RUN.

## Validation and preservation

Focused command from the E16 directory:

```sh
/home/takazudo/.cache/zudo-e16-numerical-venv/bin/python -m unittest test_attribution_admission test_attribution_worker test_attribution_lifecycle test_attribution_host test_attribution_supervisor -v
```

Final combined result: **90 tests PASS in 2.693 seconds** after the scope-ownership, watchdog and outside-swap corrections. A subsequent supervisor docstring-only correction identifies the now-implemented host owner; the final full-suite result is recorded by the main author. This is a focused count, not the full E16 suite count.

Coverage includes real detached-signature verification with disposable fixture keys and a temporary fixture trust store; fixture ledger/claim/terminal writes; actual `finish_accounting()` to `accepted_result()` integration; coordinated result-plus-local-manifest tampering against an unchanged independent journal; actual tiny lifecycle/executor work inside the subprocess supervisor; worker refusal before numerical work; timeouts, cancellation, simulated OOM, pipe/output quotas, filesystem faults and mocked Linux provisioning/cleanup. Disposable fixture keys are not production keys or grants. All real trust stores, campaign state, original data and production resources remained untouched.

The campaign ledger still hashes to `94aafb6d13f754fdbde718a5b44c5071d946897e798a8eebf1cd4b86c0731ffb`: actual ledger delta zero; 2/3 baselines and 8/24 diagnostics preserved; Attempt 5 remains terminal. No production artifact was decoded, no real numerical unit or native oracle executed, and no production authorization/reservation was created. Fixture children/files were cleaned. Stage C on the real KB U7105.4 observation remains NOT RUN; every electrical/whole-board acceptance and adoption flag remains false.

## Reviewed hashes

| File | SHA-256 |
| --- | --- |
| attribution_admission.py | 0801a321807bb70e65270cea9518d44740ba76554c84afca94399d5206a1dfb4 |
| attribution_request.py | 9a0a0425b2d545cae3b255248e06bda12b273c10dfc20d3e0d9243f69660353a |
| attribution_worker.py | d60a06b35f2effb1ae4dc9ba498102e2a2ec5c17b275619938bcc9a8ffd6afae |
| attribution_lifecycle.py | d197895130ea756bfcd9de2068b5f067c67d99ace788f132fbac6eefb3ed12b4 |
| attribution_host.py | d16e4cea5aa8632b4bc1e6bad24f09c032947e868bfbb430fe1f6e1655908714 |
| attribution_supervisor.py | 3dbced6806af08a6bd80aadf7159af64eb42dfa349afabe51ceb5f5ed36d9c30 |
| test_attribution_admission.py | e0ab43db5f2c83b9aa7fb6ba625814b37e67caa068bc0acf83b9d943d0e8a35d |
| test_attribution_worker.py | c5882be700ed492780858fa6b2733e33bec8d63b584a6e33c86e2ade4ffcdd93 |
| test_attribution_host.py | 013ae3eb4f891f7b1a61327eb7a9fe3e1f0bd8c210fdb726ea7564a1cf3f4fb3 |
| test_attribution_supervisor.py | 9255fbfa9f9c4e9cd10f5d1e2657205a99dc54fbeab3ed9ada44a386ef977b6f |
