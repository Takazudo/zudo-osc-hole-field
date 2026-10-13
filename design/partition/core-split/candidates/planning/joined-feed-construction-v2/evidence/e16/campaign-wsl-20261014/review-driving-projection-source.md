# Independent source review — bounded driving-point projection

2026-10-14 JST; separate Codex review agent. Candidate worktree `worktrees/e16-campaign`; reviewed uncommitted `finite_solve.py` and `test_refined_solve.py` diff. Exact inspected SHA256:

- finite_solve.py: `dfd3578cd6c7ca822e15766ea019aeecf43967c4d6393bf5ad145e32633506f6`
- test_refined_solve.py: `f125a509284e781b11c6c4334d056c3fb417e3556de3ad5df078db7eac2c6855`

**Source review PASS; no blocking findings.** Commit-worthy bounded numerical correction candidate. This verdict does not establish the production failure's cause, full96-pad runtime/memory, complete baseline numerical accuracy or electrical acceptance.

The original numerical refinement body moves into a private helper. Its matrix, RHS, initial factor solve, extended residual, three corrections and best-iterate calculations are unchanged. Extended matrices are restricted to width1…8 and original128bytes/node solution budget before LU/allocation. The public ordinary refinement API still allows float64 multi-RHS and refuses extended multicolumn input, preserving load/interface call semantics.

`refined_projection` accepts at most16 RHS, slices8-wide blocks, projects from each extended solution directly into small float64 e/q outputs, and deletes U before the next helper call. It combines residuals using subblock absolute maxima normalized by the original16-column RHS maximum, not an easier96-column scale or changed tolerance. Nonfinite/negative diagnostics refuse. Empty projection returns correctly shaped arrays without entering max-on-empty refinement; zero RHS remains zero. dpoint changes only this solve/projection call; serialized unit scheduling, batch16, method/hash binding, support weights, net/case/depth, loads, tolerances, guards and limits stay unchanged.

Six new regressions are meaningful: independent branch equations plus analytic projections and old float64 failure;8+3 tail and weakref release proof with exactly initial+3 LU calls per subblock; original whole-batch normalization for scaled second block; invalid diagnostic refusal; early width refusal before LU; zero/empty results. Existing load/interface precision, ordinary float64 API, independent monolithic fixture, energy/KCL, binding and stop-on-first-failure tests remain intact. No test or assertion was weakened to accommodate production failure; the dtype assertion label now accurately describes the unchanged ordinary helper rather than the replaced driving-point implementation.

Independent command, from numerical source directory using pinned venv and one BLAS/OMP thread:

`python -m unittest test_refined_solve test_finite_adapter test_numerical_acceptance -v`

**44 tests PASS in7.877s.** These are source/analytic/small disposable adapter fixtures only, including their tiny generated finite networks; no production input/pickle, native oracle or production diagnostic was executed. `git diff --check` PASS. Reviewer made no tracked edits.

Memory argument is bounded and sensible:8wide longdouble x/best have same nominal bytes as16wide float64 x/best, residual/correction are narrower, and explicit deletion prevents overlapping old/new solution blocks. Still measure actual complete-unit peak RSS and duration: mixed-type projection/BLAS workspaces, sparse residual scratch and allocator behavior are outside simple array-size accounting. Existing180s/2GiB/no-swap/unit-heavy-guard limits must remain mandatory. The source fixture pass must not replace diagnostic3's exact failing-subrange result or subsequent full96-pad verification.
