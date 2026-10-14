# Independent review of the constructive weighted increment

Reviewer: separate agent `/root/math_review`, 2026-10-15 JST. The coordinator
implemented the producer and weighted extension; this reviewer inspected the
implementation and authored the independent exact checks. No original numerical
inputs, keys, campaign request, production solver or physical design were touched.
The prior mathematics review and its negative results remain historical evidence.

**PASS for the bounded synthetic weighted verifier and coupled formulas.
REJECT the specified eight-pass producer as the proposed next original-data
method: its actual positive output fails the contraction inequality even on the
retained 4-by-4 grid, by exact rational arithmetic.** Production applicability,
resource eligibility and useful original-data field bounds are not established.
This is a new concrete producer counterexample, not a rediscovery of the earlier
unweighted tree obstruction or oracle-weighted theorem.

## Checked mathematical argument and implementation

Write F=LU, E=A-F, H=G|E|, G=C(U)^-1 C(L)^-1. Triangular absolute substitution
implies |F^-1|<=G entrywise, with G nonnegative, regardless of the stored signs
or symmetry of A. For exact positive binary64 p define

    ||x||p = max_i |x_i|/p_i,
    q >= max_i (H p)_i/p_i,
    k >= max_i (G 1)_i/p_i.

Then ||F^-1 E||p<=q. If q<1 the Neumann argument proves uniqueness and

    ||A^-1||inf <= max(p)*k/(1-q).

This is the earlier reviewed theorem; the increment implements it. The streamed
residual loop multiplies each outward |E_ij| by p_j, sums outward, applies the
nonnegative triangular comparisons and divides output component i by p_i.
The denominator 1-q is rounded down. No global residual, G or inverse is
materialized. The identity-permutation restriction remains explicit.

Signed factor solves enclose h=F^-1 B. In the SAME norm,

    ||A^-1 B[:,j]-h[:,j]||p <= q/(1-q)*||h[:,j]||p.

The code uses outward max_i magnitude(h_i)/p_i and multiplies by max(p) to
obtain a common infinity radius. Each Schur entry keeps signed-solve interval
width and adds this radius times its original absolute B column sum. Thus it
does not mix weighted contraction with the old unweighted correction. The small
interval Schur proof and disjoint-terminal global block bound are unchanged.
Both boards passing still does not imply Schur success.

Weight packets bind actual values, original A hash, factor hash, context and
method; separately expected packet hashes detect stale values. Finite built-in
binary64 values in [2^-400,2^400] are required, with shape and strict positivity
checked. Extreme scales are refused, not clipped. Accepted within-range uniform
rescalings are tested. Factor values, permutations and sparse patterns retain
their original validation. Global construction digests now include both factor
and weight identities. These are construction bindings, not admission signatures
or serialized independently reusable proof objects.

Arithmetic overflow refuses. Underflow is enclosed by existing nextafter interval
primitives, including a tested residual product below the minimum subnormal.
Approximate producer arithmetic is never used as a verifier premise. The optional
direct supersolution condition has not been implemented or qualified here.

## Producer rationale and concrete new failure

The producer deterministically starts at ones and performs exactly eight passes
p_next=G(1+|E|p), using approximate sparse row-streamed residuals and triangular
recurrences. This is a reasonable local trial because if rho(H)<1 its exact fixed
point solves p=G1+Hp and has positive slack. Neither starting below that fixed
point nor contraction within eight steps is guaranteed. There is no dense solve,
auxiliary system, oracle read or M-matrix assumption in the producer. Repeating
the full residual pass is charged work, not a free weight iteration.

The independent oracle computes the exact contraction of the ACTUAL emitted
binary64 p, interpreting A,L,U,p as exact Fractions. On the retained 4-by-4 grid
with ground1, the maximum occurs at row10:

    q_exact = 1532638432979940734553364559686659225993522634382765052007572175
              /1506282454128078137439755725727477437275406789073815244107677696
            = 1.0174973682921369 approximately.
    q_outward = 1.0174973682921387.

Therefore this refusal is not interval pessimism. The fixed eight-pass output
has the wrong componentwise shape for the required contraction. Its positivity
and plausible magnitudes do not rescue it. The order64 and held-out order81
fixtures also refuse; exact dense oracles are not used at those sizes. Tiny
oracle-derived weights remain separately labeled and are never supplied to the
candidate producer. This result rejects this exact recipe, not every weighted
method or every possible iteration count.

Combined with the separately reviewed repeated-pass cost obstruction, the next
local method change must eliminate repeated full residual passes before another
original request is considered. Trying another arbitrary pass count, falling
back to the already weak unit weights, or spending a diagnostic on this rejected
recipe is not justified by these results.

## Independent execution and coverage

The retained [independent-weighted-oracle.py](independent-weighted-oracle.py)
first calls the producer, then independently computes its exact q. It also runs
100 seeded (277) coupled cases, each with two nonsymmetric mixed-sign 2-by-2
boards, diagonal factors, and separately supplied nonuniform powers-of-two
weights in [1/4,4]. These weights are intentionally independent of candidate
output so omitted p_i or max(p) factors cannot hide behind nearly constant
weights. Exact Fraction checks passed for 200 board inverse bounds, 400 Schur
entries and 100 order6 joined inverse bounds. Dense inverses occur only in these
tiny oracle checks. Results are retained in
[independent-weighted-results.json](independent-weighted-results.json).

I independently reran the new eight-test suite: PASS, observed0.886s. It covers
retained and held-out grids, weak grounding, disconnected systems, nonsymmetric
and mixed-sign coefficients, independently rounded distributed stamps, floating
KB joined to grounded KA, board-pass/Schur-fail, actual resolution enclosures,
valid uniqueness with INCONCLUSIVE disposition, scale changes, malformed/stale
weights, underflow/overflow, failed-work retention and residual-row lifetimes. Deterministic reproduction with oracle APIs mocked
to fail also passes; mixed-sign coupled coefficients are included. On the
retained order16 ILU pattern, candidate weights improve the certified inverse
bound from74.6873 to51.5544; this is a bounded positive example, independently
checked against the exact inverse. Weak-ground order64 ILU still refuses with
q=1.017101. The positive example does not overturn the exact tree counterexample
or the repeated-pass resource obstruction.
The legacy18-test suite also passes, observed0.063s; these18 tests are historical,
not new findings. Tests and oracle run under the established512MiB address-space,
20CPU-second,30wall-second and one-BLAS-thread limits.

Actual residual_bound, energy_interval, reaction_interval and screen calls are
synthetic functional evidence. Whole distributed termination energy is preserved.
No result is a screen disposition for actual TP990026 or evidence that the
original full pipeline fits. The lifetime regression observes dictionary death
before the live count drops; this corrects a toy accounting defect without
claiming a production memory breach.

## Reviewed identities

| File | SHA256 |
| --- | --- |
| fixture/prototype.py | 78c5e38f29a065010bdb42f7ffd042e666c7465b60166d700e0c0e180944fe33 |
| fixture/test_weighted.py | 2d778f8722d1984f5174c0bb3150be99a7bd1f251a06bb89316c75f9291f07ac |
| independent-weighted-oracle.py | 34231147fa740c273c28ba1e75194464d12e185453db7b73e8f22109ef22d06a |
| independent-weighted-results.json | 81bbb1731964ee61f4f293b4bf8b48a02716798587883597fdc5e1120048edf9 |

Reproduce using the README's established numerical venv and outer30s timeout,
substituting independent-weighted-oracle.py or fixture/test_weighted.py as the
script. Circuit evidence check before reviewer edits passed: manual inventory,
68lines, no schematic/placement binding, pin-asset check performed. No source
claim here authorizes original qualification, production, geometry adoption or
any outward action. Resource eligibility is the separate resource review.
