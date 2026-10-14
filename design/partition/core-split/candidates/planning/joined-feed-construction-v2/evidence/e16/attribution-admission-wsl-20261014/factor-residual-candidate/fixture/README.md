# Synthetic factor/residual experiment

This retained synthetic prototype reads **no original numerical inputs** and has no admission or production integration. `prototype.py` imports the existing interval primitives, `Work`, and resolution module. `test_prototype.py` creates only tiny fixtures; full tiny joined matrices and dense exact-rational inverses occur only in fixture/oracle code. The tiny block-separated Schur bridge is implemented and tested; no production integration or full-data resource claim follows.

Run from the repository worktree root:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 timeout 30s /home/takazudo/.cache/zudo-e16-numerical-venv/bin/python -B design/partition/core-split/candidates/planning/joined-feed-construction-v2/evidence/e16/attribution-admission-wsl-20261014/factor-residual-candidate/fixture/test_prototype.py
```

The runner sets 512 MiB address-space and 20 CPU-second limits before importing NumPy/SciPy, plus one BLAS thread. The shell enforces 30 wall seconds including imports. Matrix order is limited to 128. No library factorization is called.

## Theorem-to-code map

Let the exact real interpretation of the stored binary64 matrix be A. Let L be the implicit-unit-diagonal lower triangular factor and U be an upper triangular factor whose diagonal is finite and nonzero. E=A-LU. Define C(T) by absolute diagonal and negative absolute strict-triangular coefficients. Its triangular inverse is nonnegative, and |T^-1| <= C(T)^-1 follows by triangular induction.

| Hypothesis/witness | Verification | Refusal | Result |
| --- | --- | --- | --- |
| A is the exact bound original coefficient matrix | Canonical finite binary64 CSR; matrix hash over shape, dtype and every CSR byte | Nonfinite, duplicate/noncanonical CSR, unsupported order or binding | Fixed exact A, without symmetrization |
| Factor identities/context/pattern/permutation match | Caller supplies separately expected witness digest and context; complete serialized factor witness is hashed; only identity permutation supported | Incomplete, stale, wrong context, malformed triangular rows or unsupported permutation | Bound approximate factors; hashes are bindings, not signatures |
| L,U have exact binary64 coefficients and invertible diagonals | Strict lower L with implicit exact diagonal 1; U contains finite nonzero diagonal; type(value) must be built-in float | Missing diagonal, nonfinite/nonbinary64 or nontriangular entries | Exact LU is nonsingular |
| r >= |E|1 | Exhaustive row-streamed interval A-LU; every product including fill outside original pattern; sum magnitudes outward | Interval overflow, work/storage limit | Nonnegative row residual majorant |
| q >= ||(LU)^-1 E||inf | Nonnegative forward C(L) and backward C(U) recurrences on r | q>=1 | Neumann inverse existence when q<1 |
| K >= ||(LU)^-1||inf | Same outward comparison recurrences on ones | Overflow/cap | ||A^-1||inf <= K/(1-q), denominator rounded downward |
| Selected residual and original functionals | Tests call actual resolution residual, energy and whole distributed reaction enclosures; exact Fraction oracles independently check results | Error enclosure too wide | Valid uniqueness can still yield Stage C INCONCLUSIVE |

Fixed-pattern producer values are only candidate witnesses: their accuracy is never assumed. The producer performs bounded row-by-row incomplete elimination with no pivot search. Every attempted product is counted even when its destination is dropped. The verifier drops **nothing**, including cancellation fill. The producer cannot change the matrix or the original solver/refinement.

## Results and specific boundaries

Eighteen tests pass; `tests.txt` and `results.json` retain complete outputs. Tests cover a grounded KA and separately floating KB joined by independently rounded distributed termination stamps and wire conductance; nonsymmetric cancellation; weak grounding; disconnected/singular and nearly singular systems; stale/incomplete/type-invalid witnesses; work and entry refusal; exact selected-field/energy/reaction enclosures; and valid uniqueness with unusable Stage C precision.

The signed-sweep counterexample has L rows [1,0,0], [1,1,0], [1,1,1], U=I and A=L. Signed L^-1 times ones has infinity norm 1, while the exact inverse norm is 2. The correct comparison recurrence yields K>=4. This rules out signed-sweep cancellation as a norm certificate.

The distributed rank-one counterexample w=(1/2,1/2), v=(1,-1), t=0, Rt=1 has exact energy 0. Replacing it by independent positive edges yields energy 1. The fixture preserves the rank-one stamp. The joined non-dyadic fixture separately rounds wi*wj/Rt, -wi/Rt and 1/Rt and certifies those stored values, rather than assuming an algebraic rank-one identity that floating storage need not preserve.

Fixed-pattern ILU0 results demonstrate that successful factorization does not ensure certification:

| Tiny grid | Ground | q upper | K upper | Result | Counted updates | Peak entries | Dropped producer products |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4 by 4 | 1 | 0.9556137878634239 | 3.315087408296346 | inverse <=74.68732402971993 | 610 | 263 | 18 |
| 8 by 8 | 2^-40 | 1.0000000000000067 | 3.310625920405147 | REFUSED | 2840 | 1095 | 98 |

Both grids are mathematically nonsingular: their exact stored graph Laplacian is connected and has a positive exact dyadic ground. The second refusal is a limitation of this candidate bound, not a singularity claim. The first grid's inverse bound is independently checked by Fraction elimination (order 16); the order-64 grid uses the direct connected-graph quadratic-form argument only. The tiny timing is not a resource extrapolation.

## Accounting interpretation and omitted production work

One `Work` instance is cumulative across factor production, exhaustive residual and both sweeps; no board/reset tricks. Phase counts are retained. Retained factor entries, fixed pattern, eight order-length vector/index allowances and live row scratch are checked before insertion. Python/container overhead and serialization copies remain under the independent address-space bound; the entry metric is not a memory-byte proof.

A counted update here is a candidate arithmetic-kernel unit: a scalar producer multiply/subtract/divide or an interval primitive invocation (residual multiplication and subtraction charge separately). It is **not** a claim to count every floating instruction inside the existing interval primitive: `mul` evaluates four endpoint products, for example. This intentionally conservative prototype convention is not an unreviewed replacement of the production LDL product-update semantics. There is no hidden library factorization.

Input hashes and structural validation, pattern scans, JSON witness serialization, list/dictionary allocation, comparisons and integer indices are not represented as floating arithmetic updates; they remain actual runtime/memory work. The production proposal must separately bound these scans and bytes, both boards, coupled Schur witnesses and checks, residual passes, original mesh/energy/accounting, retention, cleanup and external reserve. The prototype supplies no full-pipeline 180-second/1216-MiB/20M-update fit claim and is not a resource qualification.

## Factor-only board-separated Schur lift

The additional bridge uses only signed outward triangular solves h=(LU)^-1 B, with the exact original B coefficients. For each column it encloses A^-1 B-h by radius q/(1-q) times the outward infinity magnitude of h. Interval widths of h remain in the Schur product. Each Schur entry is D_ij - sum_k B_ki h_kj, widened by sum_k |B_ki| times that column radius. This avoids a separate A-times-retained-Y pass. The input terminal block can contain intervals, preserving the exact original sum of stored D and wire stamps instead of first rounding that sum into a new singleton matrix.

A bounded fixed-pivot float Gauss-Jordan routine produces a small approximate inverse witness R (order <=8); its success is not assumed as proof. Exhaustive interval I-RS row sums must be below one; the certified Schur inverse bound is ||R||inf/(1-||I-RS||inf). All steps share the same cumulative Work instance with both board certificates. The original nonsymmetric block inverse bound is (1+max ai||Bi||inf) max(ai,s) (1+max ai||BiT||inf). This maximum backward-block formula requires each terminal column to belong to at most one board; the prototype explicitly refuses shared columns. Separate terminal nodes connected by wires satisfy that condition. No sqrt(N) reference conversion is used.

Exact Fraction tests independently form each tiny original block Schur complement and verify every interval entry, then verify the global inverse bound. Ground1 gives inverse <=31.45060526954466 (exact norm approximately12.5240741). Ground2^-30 gives inverse <=18954561637.577145 and a loose Stage C example. A nonsymmetric free block gives inverse <=28.028679869297278. Each case consumes 200 cumulative candidate kernel updates. On the SAME strongly grounded fixture, diagonal factors certify both boards, but Schur verification refuses at q=1.488536154309873. Board success does not imply joined certification. Disconnected wire and shared-terminal cases refuse. A signed triangular solve with negative U pivot is separately checked against exact Fractions.

## Fixed sparse connected factor pattern

A fixed rooted-grid-tree pattern keeps only diagonal plus one lower adjacent parent per row; U is diagonal and stored F=2n-1. This is a predeclared synthetic pattern, not an ordering search. Results show deterioration even when witness storage is small:

| Grid | Ground | q upper | Inverse bound/result | Factor entries | Updates |
| --- | --- | --- | --- | --- | --- |
| 4 by 4 | 1 | 0.9992283950617297 | 989.3333333349672 | 31 | 235 |
| 4 by 4 | 2^-30 | 0.9999999999989233 | 709476121952.8212 | 31 | 235 |
| 8 by 8 | 1 | 0.9999999627891148 | 20159998.514345407 | 127 | 987 |
| 8 by 8 | 2^-30 | 1.0000000000000016 | REFUSED | 127 | 985 |

The order-16 successful bounds have exact Fraction inverse checks; order-64 uses the established theorem and does not build a dense inverse. No conclusion about actual board pattern fit or useful full-data error follows.

## Toy allocation boundary

`pattern_of` refuses order >128 before allocating a pattern. The tiny pattern is allocated before the Work entry check; this is bounded by the explicit toy order, not an assertion of production admission correctness. Production would require packed, prebounded pattern allocation. Temporary dictionary copies of factor rows have been removed, and producer row scratch is deleted before lowering its live-entry count. The pattern-plus-eight-vectors reserve remains a toy conservative slot reserve, not a complete byte metric. Python object overhead, witness hashing, imports, fixture/oracle storage, allocations and metadata are governed by the separate actual address-space limit. The ignored original has been superseded by this frozen evidence fixture; there are not two maintained candidate implementations.


The block API rejects non-binary64 B arrays, foreign singleton D scalars, malformed/nonfinite D interval endpoints and foreign signed-solve RHS values. Freshly computed outputs include a global input digest over context, both original A hashes, every B coefficient and the full initial D interval entries. Mutation tests cover B, D and context. This is only a construction binding, not an authenticated or independently reusable certificate packet. A future serialized production witness must additionally bind the complete request, original wire identities/coefficients and all live source/input identities through the existing admission mechanism. The current block routine recomputes every witness from its actual inputs and does not accept a cached global result.

## Constructive weighted extension (2026-10-15)

The historical results above remain preserved. The same `prototype.py` now adds
fixed-eight-pass non-oracle weights, independent outward weighted validation,
weighted signed-solve Schur correction, and an actual residual-row lifetime fix.
See [weighted-increment.md](../weighted-increment.md) for the theorem mapping,
full case table, measured resource scope and reviewed **no-real-request** decision.

Run `fixture/test_weighted.py` under the same venv, thread settings and outer
30-second timeout as the legacy runner. Eight new tests pass; outputs are
`weighted-tests.txt` and `weighted-results.json`. The unchanged18 legacy tests
also pass, retained separately as `weighted-legacy-tests.txt` and
`weighted-legacy-results.json`; old `tests.txt`/`results.json` are not overwritten.
The separate reviewer runner is `../independent-weighted-oracle.py`.

The candidate emits positive weights but fails contraction on all tested rooted
trees, including held-out9x9; exact Fraction checking confirms q>1 on tree4.
A retained incomplete-grid4 case succeeds, and weighted tiny coupled proofs work,
but eight full residual passes already exceed original cost limits by a proved
lower bound. No oracle weights are presented as candidate output. The optional
direct supersolution condition is not implemented. This is a synthetic certificate
increment and a concrete rejected producer, not original-data qualification.

In the comparison JSON, the key `"None"` denotes the unweighted control. Missing
arithmetic-phase keys mean zero charges in that phase. Exact reference and
physical functional calls are outside the certificate-kernel meter, explicitly
labeled; reported kernel totals are not full production-pipeline operation costs.


### Structured continuation

`test_structured.py` retains the non-oracle BFS-tree weight failure and a path
positive control. `test_coercivity.py` exercises the subsequent whole-operator
tree-coercivity proof, exact stored deficits, interval-terminal wrapper and
path-energy refinement. Both import the same bounded fixture setup; run with
`OPENBLAS_NUM_THREADS=1 timeout 30s` and the established numerical venv's Python
`-B`, passing an output JSON path. Results and test transcripts have new names.
The old18+8 tests still pass; historical reports are unchanged.

The new exact arithmetic counter has separate declared kernel/width/bit-work
metrics, not production scalar updates. No original numerical input or production
entrypoint is enabled. See `../structured-coercivity-increment.md`.
