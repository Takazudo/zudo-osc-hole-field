# Bounded CSC residual implementation handoff

Changes were made only after explicit independent diagnostic6 terminal integrity/cleanup PASS and root's source-edit authorization. Worktree `e16-campaign`, parent HEAD9a68f1a. No commit or production execution by implementation agent.

Modified only:

- numerical `finite_solve.py`, SHA256 `d07b002c42d9e708dcf95d0702b02c7753ebcef10ec4b45d1eb68c7449d7b919`.
- `test_refined_solve.py`, SHA256 `780fb04dcba7f9e2544433e7d3b42a7726fb8d7b7da22f811bb209daaa389d48`.

Root/review_admission's actual16pad AGND profile established the target: `_extended_residual`26.569s inclusive, `searchsorted`16.966s self across9,792calls, of40.025s total. The source change avoids repeated per-entry searchsorted arrays in CSC by calling the existing compiled in-place CSC kernel over bounded slices. Only two scalar boundary searches per slice remain. Coefficients, node precision, stored-entry addition order, outputfloat64, residual normalization,3corrections, extended8projection blocks, scheduling16, fullunit identities, guard,180s/2GiB/no-swap and targets/loads/geometry stay unchanged.

CSC coefficient scratch<=65,536entries, pointer/vector span<=65,536columns, indices remain original views, one extended residual node vector per RHS. This covers long empty column spans and oversized individual columns. No full extended sparse matrix. CSR original scatter arithmetic is unchanged. Local private `_sparsetools` import is explicitly documented as a dependency on request-pinned SciPy's existing API, with equivalence fixtures. Request toolchain binding is version/Pythonbinary, not a claim that SciPy package bytes are content-hashed.

Five new test methods verify finite result byte equality including signedzeros, nonfinite propagation, cancellation, stored duplicate nonassociativity (regrouping would fail), unsorted entries, float64/longdouble vector/matrix RHS, split oversizedcolumn, longemptyspan, scratch caps/single residualbuffer via spy, unchanged inputs, CSRfallback and emptyA. Existing numerical regression expectations unchanged.

Validation: `pnpm circuit:check` before and after PASS (manual inventory68,0declared placements, no schematic/placementbinding, pinassetcheckperformed); `git diff --check`PASS;49 sourcefixture testsPASS5.756s from `test_refined_solve test_finite_adapter test_numerical_acceptance`. Log `source-fixtures.txt`. Independent source review delegated to review_checkpoint; root will review/commit and own required aggregate/documentation checks.

Actual implementation syntheticbenchmark against9a68 helper:100k-node499,924nonzero8RHS residual0.136120→0.039984s,3.40×,byte-identical.20k-node99,924nonzero case4.49×. `implemented_benchmark.py` reads old function from exactGitcommit and new actualfunction byAST, with hardcoded synthetic graphs only. Data retained in `implemented-results.json`; earlier prototype measurements remain separate. These are not production runtime/memory guarantees. Next exactfull96AGND diagnostic under unchangedbounds is still necessary before another baseline. No diagnostic budget consumed by this implementation/test work.
