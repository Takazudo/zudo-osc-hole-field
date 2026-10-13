# Independent CSC boundary-index dtype source review

Reviewer `/root/review_checkpoint`, separate from author `/root/review_sources`, 2026-10-14. Reviewed only the two-query dtype correction and one regression relative to492d0e2 in the isolated candidate. No production/native computation, request or authorization was performed.

**PASS; no findings.** Source hashes reviewed:
- finite_solve.py: `20b1b9e1e7ba8653d3268c4956dc5415b91670e23f07e35ab381d2091f84b044`
- test_refined_solve.py: `b312ec1223ca1e13fcf23bc2bfa1c706ff997f1e20e00e5c51731bffad4508f0`

Each CSC boundary search now supplies a scalar of exactly `Af.indptr.dtype` rather than Python int. The offsets are nonnegative values inside the current indptr-derived nonzero interval; `lo` and `hi-1` cannot exceed representable endpoint values for a valid sparse matrix. Matching int32 or int64 queries therefore preserves exact ordering/boundaries without truncation or introducing a new indexing range. Search side, clamp, entry/column chunk bounds, kernel arguments, stored-entry accumulation, residual precision and output are unchanged. CSR is unchanged. No scheduler, numerical tolerance, acceptance rule, refinement count, loads, geometry, resource limits, guards or dependencies change.

The retained synthetic allocation experiment shows the concrete issue: one query on1,800,001 int32 pointers peaks at14,400,536 traced bytes for Python int and428 for matching scalar, with identical result800001. Retained synthetic residual samples show0.165–0.179s versus0.073–0.076s and identical original arithmetic bytes. These are synthetic performance observations; they do not establish a new production runtime or numerical receipt. Diagnostic7's prior actual96-pad success remains tied to its earlier source, not this changed method.

The added regression verifies both int32 and int64 pointer arrays, scalar dimensionality, exact query dtype and the two expected query offsets; it also checks equivalence to retained original scatter. This is a deterministic regression for the demonstrated allocation mechanism, not a timing assertion. Existing boundary, duplicate/order, signedzero/nonfinite, precision, projection and acceptance tests remain unweakened.

Independently ran the pinned-venv `python -m unittest test_refined_solve test_finite_adapter test_numerical_acceptance -v` with BLAS/OMP/MKL threads1: **50 tests PASS**, exit0. Log `residual-searchsorted/independent-source-tests.txt`. `git diff --check` PASS. No production inputs or diagnostic budget consumed by review.

Commit reviewed bytes before preparing the next exact request. Changed executable method requires a fresh source/hash-bound packet and delegated receipt; no old request may run against the new HEAD. This review approves source readiness only, not baseline execution or electrical acceptance.
