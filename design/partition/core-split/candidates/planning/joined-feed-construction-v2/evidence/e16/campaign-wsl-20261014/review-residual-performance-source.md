# Independent bounded CSC residual optimization source review

Reviewer `/root/review_checkpoint`, separate from implementation author `/root/review_sources` and executing coordinator, 2026-10-14. Read-only review of final two-file diff against HEAD `9a68f1a87db7afbc20ae16a95ef523a5f8d093ca`. No production inputs, geometry, operator pickle, numerical diagnostic, native job, receipt or launch was executed by reviewer.

**PASS for committing this narrow source optimization. No blocking findings.** Production runtime/numerical feasibility remains unverified for these changed bytes and needs a fresh exact admitted diagnostic; neither this review nor synthetic tests permit bypassing that gate.

Reviewed hashes:
- `finite_solve.py`: `d07b002c42d9e708dcf95d0702b02c7753ebcef10ec4b45d1eb68c7449d7b919`
- `test_refined_solve.py`: `780fb04dcba7f9e2544433e7d3b42a7726fb8d7b7da22f811bb209daaa389d48`

## Cause and implementation

Retained diagnostic6 terminal/profile review supports the cause: actual unchanged production KB AGND first16-pad unit spent26.569s inclusive in extended residual,16.966s in repeated searchsorted, out of40.041s wrapper elapsed. These overlapping values are not additive. The prior96-pad timeout is preserved; the profile is not a full-chunk runtime guarantee.

Only CSC residual evaluation changes. Instead of materializing a major-column index for every nonzero and scattering products in NumPy, the request-pinned SciPy private `_sparsetools.csc_matvec` adds the same negated extended coefficient products directly to the one existing extended residual vector. The residual is initialized with b; stored-column and stored-entry order are preserved, including unsorted rows and duplicates. This avoids a separately grouped row sum. Original coefficients/x precision, final float64 residual type, matrix/vector shapes and input immutability remain intact. CSR retains the previous scatter implementation.

Both coefficient-entry chunks and outer column spans are bounded at65,536. Clipped/rebased pointer segments correctly support a column crossing entry chunks and empty columns across span boundaries; indices remain a view. No full extended sparse matrix is allocated. Scratch remains bounded in entries and columns; the existing node-sized residual vector is reused. Missing/private-kernel incompatibility fails visibly; there is no lower-precision fallback. Private API usage is candidly documented and existing pinned toolchain/hash admission remains required.

No scheduler, DP chunk count, iteration count, stopping threshold, acceptance rule, tolerance, load, geometry, source/protection model,180-second timeout,2GiB/no-swap control, shared guard or request mechanism changes. Existing refusal/nonfinite/projection tests remain and no assertion was weakened.

## Independent verification

Executed pinned-venv `python -m unittest test_refined_solve test_finite_adapter test_numerical_acceptance -v` from the numerical source directory with BLAS/OMP/MKL thread counts1: **49 tests PASS**, exit0. Log: `residual-performance/independent-source-tests.txt`. These are source/synthetic fixtures only. `git diff --check` also PASS.

Five new methods meaningfully test equivalence against retained pre-optimization scatter arithmetic: extended cancellation, non-associative stored duplicate order, unsorted rows, vector/multi-RHS and float64/longdouble input; signed-zero bytes and nonfinite propagation; a70,001-entry split column and70,002-column empty span; coefficient/pointer/column caps, same residual buffer and input preservation; unchanged CSR path and empty matrix.

Additionally executed102 independent synthetic checks:100 deterministic random CSC matrices with unsorted duplicate entries and varying magnitudes, and two fixtures crossing both65,536-column span and65,536-entry boundaries with explicit64-bit sparse indices. Every result matches original scatter finite float64 bytes exactly. No production input or budgeted diagnostic was used. Test fixture timings do not establish actual AGND performance.

Required next gate: commit tested bytes, prepare/review a fresh exact request with delegated campaign authorization, then verify the actual complete96-pad AGND unit under unchanged guards/limits. Do not reuse diagnostic5 or6 requests and do not claim these source tests repair the numerical campaign by themselves.
