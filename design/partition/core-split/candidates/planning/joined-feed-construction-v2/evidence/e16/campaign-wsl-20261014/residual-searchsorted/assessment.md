# Typed CSC boundary queries — bounded source performance correction

Diagnostic7 passed its actual optimized96pad KBAGND unit in157.69solver seconds (hook159.32s), residual1.6892033503601012e-13, with memory/integrity/cleanupPASS. This is not another timeout or unchanged failing trial. Investigation targets remaining per-query full-index allocation and runtime headroom while preserving the now-passing mathematics.

All experiments here use synthetic arrays/matrices, no production input, no numerical diagnostic units. Tracked source remained frozen until explicit independent diagnostic7 cleanupPASS and root edit authorization.

## Measured cause

`scalar_probe.py`:1,800,001entry int32 indptr,1,000identical scalar searches. Python-int queries0.226910s; explicitly matched np.int32 queries0.001620s (~140×). Returned indices/checksums identical. At100k entries,0.015473s vs0.001779s. Bounded-localspan Python-int queries0.011194s at1.8M; matching dtype alone is simpler and faster than changing index search scope.

`allocation_probe.py`: one Python-int scalar query transiently allocated14,400,536traced bytes; a matching int32 query allocated428bytes and returned the same index800001. A full promoted1,800,001entry64bit array occupies14,400,008bytes. This directly demonstrates the full-index-size transient allocation avoided by matched query dtype on the installed NumPy2.2.6 environment, rather than inferring it from timing alone.

`residual_probe.py`:actual current CSC helper versus an AST clone changing only the two scalar query types;1.8Mnodes,8,999,924nonzeros,one RHS, int32 indices, original synthetic SPDgraph. Current residual0.178910/0.165101s; typedcandidate0.076253/0.073231s (~2.3×). Every residual is byte-identical. Profile's searchsorted self0.084308/0.087100s→0.000411/0.000494s over276calls. Peak411,172KiB with explicit2GiB address-space cap. No LU factorization or production model involved.

Raw scripts/output JSON retained alongside this assessment. These timings do not predict exact complete production runtime or guarantee memory limits.

## Minimal implementation

After cleanup authorization, changed only both CSC boundary queries to `Af.indptr.dtype.type(lo)` and `Af.indptr.dtype.type(hi-1)`, with explanatory comment. Both offsets are bounded by original indptr values and exactly representable in its integer dtype. Matrix, arithmetic/accumulation order, chunklimits, all guards, solverprecision, tolerances, scheduler, units and dependencies are unchanged.

Added one deterministic regression for both int32/int64 indptr: spy requires scalar search dtype to match the actual index array, asserts exact boundaryqueryvalues and verifies original residual equality. This tests the allocation-prevention contract without timing thresholds. Existing49tests remain unchanged.

Validation:50refinement/adapter/numericalacceptance sourcefixturesPASS6.121s; circuitcheckbefore/afterPASS (manual68lines,0declared placements; schematic/placementbinding notperformed; pinassetcheckperformed); diffcheckPASS. Full aggregate not repeated by this agent; parent retains previous aggregate plus focusedfinaldelta validation. No production unit or commit by implementation agent.

Exact uncommitted reviewed-candidate bytes:

- finite_solve.py SHA256 `20b1b9e1e7ba8653d3268c4956dc5415b91670e23f07e35ab381d2091f84b044`.
- test_refined_solve.py SHA256 `b312ec1223ca1e13fcf23bc2bfa1c706ff997f1e20e00e5c51731bffad4508f0`.

Root will independently review, commit with retained evidence, and prepare exactdiagnostic8 for the actual96AGND unit under unchanged180s/2GiB/no-swap before final baseline packet. No benefit is assumed for unexecuted nets/cases or fullbaseline.
