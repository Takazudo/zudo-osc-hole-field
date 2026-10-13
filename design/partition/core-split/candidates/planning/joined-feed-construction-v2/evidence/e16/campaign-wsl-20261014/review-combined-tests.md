# Independent combined-source regression review

2026-10-14 JST. Reviewer: separate Codex review agent. Candidate `/home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-campaign`, HEAD `53d46fd299e3fab0a8ce145e89f39fd3ddc06daa`, with uncommitted focused regression/docs additions. Method: read complete changes, independently execute tiny source-only tests, compare production numerical files, and verify browser receipt bindings. No tracked files edited by reviewer. No aggregate/native/browser/production-input execution.

**Verdict: PASS for source integration and the reviewed regression/docs delta; no blocking findings.** This is not numerical execution, native acceptance or whole-project gate completion.

Reviewed integration sequence:

- `54f680ac853c3d26b11bb5bf21cfb5a141453da4` (PR272 fixture isolation).
- `5269b9724946f95cf51d53a3280ed43c8a2b4c18` (PR272 source-only selector).
- `5d0b34decbe660af23f628b4766bd4c0b399620d` (PR272 exact discovery-root binding).
- `2b38c943b440243619f432a65dda630824c00e45` (PR273 launcher/source).
- `53d46fd299e3fab0a8ce145e89f39fd3ddc06daa` (PR273 evidence).

New `scripts/checks/test_source_only_python.py`: eight tests cover both exact discovery identities, missing oracle, duplicate oracle, unexpected prefix, oracle in unexpected root, nested unrelated suite, propagation of a selected test failure, and actual neighboring threshold case with `model()` forbidden. Mismatch cases assert no cases execute. Test loader patch and streams are context-managed/restored. Fixture oracle execution would cause explicit failure. No native launch path is called.

New numerical-source `test_local_fixture_environment.py`: three meta-tests execute existing disposable LocalStagingTests against a clean parent and a CI/local-authority contaminated parent, compare the complete environment mapping before/after, and inject a later setup failure to prove addCleanup restores authority even when tearDown is skipped. Empty and absent authority values remain distinct. Existing production mixed-authority refusal is tested inside the reused fixture suite. Temporary fixture cleanup for the injected setup failure is explicit. The tests do not modify production authority or create real approvals.

`circuit/checks/README.md`: accurately names the exact excluded native oracle, both discovery occurrences and fail-closed selection. It explicitly states native CI helper does not automatically execute that oracle, records retained historical WSL execution without declaring a new run, and maintains fresh-admission/NOT RUN distinctions. It does not remove required checks or reinterpret source-suite success as native success.

Independent verification on combined candidate (pinned numerical venv, PYTHONDONTWRITEBYTECODE=1):

- `python -m unittest discover -s scripts/checks -p test_source_only_python.py -v`: **8 PASS**, 0.061s.
- From numerical source directory, `python -m unittest test_local_fixture_environment -v`: **3 PASS**, 1.984s. These meta-tests invoke their own existing local fixture cases; do not add their nested case counts to aggregate discovery counts.
- `git diff --check`: PASS.
- All **19** final Mac receipt input SHA256 bindings match combined source/assets.
- `finite_solve.py` and `numerical_acceptance.py` are unchanged from execution SHA9f69cd8 in this combined candidate. PR272 changes local fixture source only; new regressions do not change executable numerical methods.

Parent-owned aggregate checks and mechanical tests were already running; reviewer did not duplicate them or claim their result. Native/oracle/browser/production diagnostics NOT RUN by this review. Historical browser evidence remains Mac evidence, no WSL render claim. Applicable checks and source/evidence publication still belong to coordinator completion.
