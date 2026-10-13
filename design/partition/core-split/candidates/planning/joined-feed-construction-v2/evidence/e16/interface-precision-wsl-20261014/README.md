# Interface precision correction and fresh-request preparation

The owner explicitly authorized diagnosis, source correction, review and preparation after attempt 3 failed. The actual clarification is recorded in `index.json`. **No new production batch is approved or executed.** Attempt 3 remains consumed FAIL with all original outputs and receipts unchanged.

## Diagnosis from preserved inputs

Two read-only decomposition diagnostics reused the exact retained +12V nominal-average uniform-dielectric reductions and operators. They held the original terminal solution and load vector fixed, reproduced the original coupled failures exactly, and compared direct copper/termination application against reduced-matrix application. Both methods agree.

| Load-relative node-KCL | KA | KB |
| --- | ---: | ---: |
| Original reconstruction | 1.515200877665821e-8 | 7.277530568849482e-9 |
| Widen multiplication of the stored float64 basis only | 6.00834966438689e-9 | 4.3226185014636564e-9 |
| Stored interface-basis residual contribution | 6.010112215246928e-9 | 4.327971934782051e-9 |
| Original load-vector residual | 2.9803321747950843e-12 | 1.309884394382926e-12 |
| Recompute only the interface basis with extended accumulation | **1.7881993048770505e-11** | **8.233559050406965e-12** |
| Unchanged declared limit | 1e-9 | 1e-9 |

The interface basis had passed its own residual test normalized by a large terminal stamp; that error nevertheless exceeded the much smaller load-relative coupled criterion. Widening multiplication of already-rounded basis values could not recover the lost precision. Recomputing and retaining the basis in extended precision resolves this isolated reconstruction failure on both exact production input matrices. Worst-node identities, absolute residuals, normalization, method/input hashes and complete diagnostic streams are retained.

A tiny two-node analytic prototype independently reproduced the same failure class through branch-current equations: original 2.7288480769606665e-8 versus candidate 2.7485079427375445e-11. Its regression is now in `test_refined_solve.py`.

## Correction

Source commit: `9341dfb2eac826769e1c17a3831c081d60b72357`.

`refined_interface_solve` refines each small interface RHS separately and retains its extended accumulator. It preserves the same three corrections, equations and whole-matrix residual normalization. The reduced interface matrix and RHS remain float64 for the small NumPy solve. Driving-point batches remain float64. Serialization preserves the extended basis. No load, numerical threshold, geometry, scheduling, timeout or memory control changed.

The final source also refuses nonfinite/negative per-column residuals before maximum aggregation; otherwise Python's maximum operation could hide NaN. The real-input diagnostics preceded this final hardening, at solver SHA-256 `2686f85d5b3697f632689e4669a724548fa4bc2c66c45a82a433fab177a0354d`. That production-source snapshot is retained as text. Final solver SHA-256 is `3c993a2505dc279a4b970aadd13db5274e9f70beaf50caba800597d76287344f`; the added rejection leaves the valid arithmetic unchanged. No final-source production diagnostic rerun is claimed.

## Resources, integrity and review

Each of the four diagnostics used the pinned shared guard, verified ownership helper, 180-second timeout and actual user-systemd 2 GiB/no-swap scope. Original decomposition guard times were 4/3 seconds; candidate diagnostic guard times 7/8 seconds. All four guard receipts PASS; all recorded memory events are zero; maximum reported cgroup peak is 1,102,270,464 bytes. All four scopes are inactive/absent afterward. All 550 protected files remain unchanged. `prior-attempt-preservation.json` verifies all 67 prior original records and eight external result blobs without changing the original failed attempt.

Independent review by `/root/review_e16` verified the decomposition, candidate code and diagnostic input/source/log hashes; independently ran 26 fixture tests, then seven refinement tests after the final rejection check. No reviewer production run occurred. Parent final targeted suite: **48 tests PASS**. Tests cover the nonzero interface cancellation, independent branch equations, multiple RHS/signs, original normalization, held zeros, serialization, float64 small-solver boundary, unchanged driving-point dtype, invalid-result refusal and unchanged numerical failure gates. An initial new test's unnecessarily tight cross-column scaling assertion was replaced by direct comparison with the analytic solution at the existing 1e-9 criterion; no production tolerance or pre-existing test was weakened.

Exact final source test command, from `joined-feed-construction-v2`:

```sh
/home/takazudo/.cache/zudo-e16-numerical-venv/bin/python -m unittest test_refined_solve test_numerical_acceptance test_finite_adapter test_numerical_unit_guard -v
```

This evidence establishes the isolated correction and source regressions, **not a fresh full production coupled PASS**. A fresh interface solution, the remaining nets/process cases and revised peak memory for complete units await a new exact approved batch. No native, finite-coverage or aggregate rerun was performed. CI is NOT RUN for this `[skip ci]` source/evidence publication.

## Next request and retained scope

Prepare attempt 4 at the final clean evidence HEAD using the existing reviewed preparation/execution recipe, fresh run/output and all rebound inputs. Scope stays baseline t2 KA/KB, normal-typ-v1 whole-device subset, +12V/-12V/+5V/AGND, nominal-average/sensitivity-thin/legacy-conditional-requirement, uniform-dielectric, at most 148 serialized units. Keep the same per-unit guard, 180 seconds, 2 GiB/no-swap, both reductions before driving-point work and stop at the first failure. No resume, old approval, native execution or remedy variant is included. The final exact digest and independent packet review are published on PR260/issue253; preparation does not approve itself.

KEEP_K1402_INCUMBENT, canonical boards, accepted copper, fixed placements and `decision.json` remain unchanged. Connectivity196/486 (separate KB-P1 480; distinct KA long-B194), complete loads/GH currents, absent physical source/protection, full-path resistance, incomplete DRC enumeration and physical/bench qualification remain open. PR260 remains draft/unmerged; issue253 stays open.

Prototype source remains ignored at `worktrees/e16-r4/__inbox/e16-coupled-residual/`, with a retained copy under `/home/takazudo/.cache/zudo-e16-runs/reconstruction-diagnostic-20261014/`. `index.json` gives exact paths, sizes and hashes for transfer; copy these directories with `rsync -a` and verify destination hashes. Prototype scripts and large input pickles are not committed. Compact diagnostic results, command/guard logs, production-source snapshot, integrity and review are committed here.

Documentation/evidence checks PASS: circuit validation, generated/type checks, shared-guard build and strict site check (existing single allowlist exception unchanged). SCOPE: manual inventory68lines; no schematic/placement binding; pin-asset check performed. Exact commands/results/log hashes are in checks.json.
