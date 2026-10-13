# Synthetic residual-performance experiment

Scope: cache-only synthetic matrices, no production geometry/operators/pickle, no production diagnostic units, no tracked source edits. Current source SHA256 `dfd3578cd6c7ca822e15766ea019aeecf43967c4d6393bf5ad145e32633506f6` at c4de08d. Numerical unit5's actual AGND timeout motivates investigation, but this experiment does not identify the production bottleneck; diagnostic6's real first16 cProfile is required before production editing.

`benchmark.py` AST-loads actual `_extended_residual` and compares it with a bounded CSC-kernel prototype. Matrices are synthetic SPD band graphs with1e5S nearest-neighbor edges,13S37-node edges, and finite shunts; eight RHS. NumPy and the existing pinned SciPy1.15.3 are used, no new dependencies.

| Nodes / nonzeros | Original residual | Compiled CSC prototype | Speedup | One LU solve | e projection |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2,000 /9,924 |0.002065s|0.001190s|1.74×|0.000457s|0.000268s|
|20,000 /99,924|0.031651s|0.007144s|4.43×|0.006594s|0.001784s|
|100,000 /499,924|0.115451s|0.039910s|2.89×|0.028512s|0.007755s|

These short timings are one synthetic sample per size, not production performance guarantees. The largest sample makes residual cost significant relative to triangular solve/projection, consistent with the suspected bottleneck but not proof for actual AGND. Every candidate residual equals original float64 result bytes on these fixtures.

Mechanism: the original CSC loop computes a per-entry column-index array by searchsorted, extended product vector, then NumPy scatter `np.add.at`. The existing compiled `scipy.sparse._sparsetools.csc_matvec` can accumulate directly into the single extended node residual vector. Supply negated extended coefficients and bounded extended x-column view; initialize output with b. CSC row additions remain in original stored-entry order, including duplicate entries and split columns. The matrix coefficients and node values retain original precision; no full extended sparse matrix is constructed.

Bound both dimensions of scratch: at most65,536 stored entries per coefficient chunk AND at most65,536 columns per outer span. This handles pathological long empty column spans without allocating an unbounded temporary indptr or x copy. Clip/rebase original indptr for each entry chunk; use original indices as a view. The compiled kernel's output is the same single longdouble N-vector for all chunks. Keep CSR on the unchanged original implementation; CSR compiled reduction can regroup row arithmetic and is unnecessary for production factor CSC.

`edge_tests.py` independently verifies13 synthetic cases, retained in `edge-test-results.json`: signed-zero finite result bytes, nonfinite propagation positions, extended cancellation, unsorted duplicate rows, an individual70,001-entry column split over chunks,70,002columns with a large empty span, empty matrix, and a kernel spy proving entry/column caps and same output vector acrosschunks. Zero×infinity and zero×NaN propagate NaN as the original path does. The spy records1MiB maximum longdouble coefficient scratch for65,536entries; no full extended matrix.

Practical boundary: local import of `_sparsetools` in CSC fastpath, retain all wider-than-float64 and CSR/CSC checks and vector/matrix result shapes. It is a **private API in already pinned SciPy1.15.3**, not a new dependency or promised stable public interface. Toolchain/package hashes already bound by requests must remain bound; regression tests must fail if that API contract changes. No fallback to float64 residual computation. Any unavailable kernel or numerical discrepancy is a failure, not an excuse to alter tolerances or unit limits.

Await the real source-bound profile. If it confirms residual work dominates, this is a narrow performance candidate preserving bounded scratch, exact current CSC arithmetic results in fixtures, three refinement steps, e/q types, scheduler,180seconds,2GiB and no-swap. It still requires independent source review and the same actual complete-unit guarded test before a new baseline execution.
