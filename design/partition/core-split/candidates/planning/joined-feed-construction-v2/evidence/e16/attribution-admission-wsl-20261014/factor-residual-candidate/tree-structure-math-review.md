# Independent mathematical review: tree barriers and tree coercivity

Reviewer: `/root/math_review`, separate from the implementation coordinator.
Date:2026-10-15 JST. Source-only synthetic continuation of the constructive
weighted increment. No original numerical input, request, signer or campaign
operation is involved. The prior eight-pass and unweighted negative evidence
remains in place.

## Stored-tree Poisson weight construction: concrete rejection

The new bounded producer checks stored symmetric negative off-diagonals and
nonnegative approximate row sums, selects the largest positive approximate
row sum as a root, and chooses a deterministic CSR-order BFS tree. These are
producer restrictions, not assumptions trusted by the weighted verifier.
Writing c_e for the retained tree edge and g for the root ground, the explicit
auxiliary tree equation has the solution

    p_root=n/g,
    p_child=p_parent+subtree_size(child)/c_edge.

This follows by summing the unit loads below each edge. The construction is a
full-order AUXILIARY TREE solve by traversal; it is not an original-system solve
or an oracle. Every pass, vector, tree edge and auxiliary operation needs its own
resource charge. Its identity says T*p=1 for the tree, not A*p>=1 for the original
matrix. Rounded producer coefficients need not satisfy that identity exactly;
independent original-matrix verification remains mandatory.

The [independent sparse exact check](independent-tree-oracle.py) consumes actual
emitted weights and then computes the contraction with Fraction arithmetic.
It materializes no dense matrix or inverse; orders64/81 remain sparse checks.
[Retained results](independent-tree-results.json):

| Grid | Exact q approximately | Outward q | min(original A*p) |
| --- | --- | --- | --- |
|4×4|1.3602693602693603|1.3602693602693625|-11|
|8×8|1.4481620643724777|1.4481620643724804|-55|
|9×9 held out|1.4550581850536126|1.4550581850536153|-71|

All refuse by exact arithmetic, not rounding pessimism. Omitted grid edges carry
negative flux under the tree's large directional gradients. A tree Poisson
barrier is therefore not a componentwise original-operator supersolution. Simply
averaging the column-comb barrier and its transpose also fails: on4×4 the minimum
A*p is-5 and outward q is1.1158900836; on8×8 they are-27 and1.1065290111. That
narrow analytic control does not justify a new production variant.

## Shell-constant direct supersolutions have an exponential obstruction

This paragraph concerns the DIRECT condition A*p>=1, not all possible weights
accepted by the earlier G|E| contraction. The latter can smooth negative A*p
components, so the two conditions must not be conflated.

For the unit m×m grid, m>=3, grounded at the origin by g>0, suppose
p(x,y)=f(x+y). Let delta_d=f(d)-f(d-1). At axis nodes(0,d),1<=d<=m-2,
the direct supersolution condition requires

    delta_d-2*delta_(d+1)>=1.

The far corner gives2*delta_(2m-2)>=1. Along the far boundary, descending from
that corner,2*delta_d-delta_(d+1)>=1. At the corner(0,m-1),
delta_(m-1)-delta_m>=1. These imply delta_(m-1)>=1, and the axis recurrence gives

    delta_1>=2^(m-1)-1.

At the grounded root g*p_root-2*delta_1>=1, hence

    p_root >= (2^m-1)/g.

Thus even the best shell-constant DIRECT supersolution has an exponentially
large max(p), whereas the earlier path-energy argument bounds the actual inverse
norm polynomially by m³*(1/g+2(m-1)). This rejects shell compression as a scalable
useful direct supersolution recipe. It is not a theorem against every weighted
factor certificate using shell-shaped vectors.

## Next architecture: tree coercivity rather than tree supersolutions

The following independent proof supports a bounded synthetic implementation;
it does not establish original applicability or production cost.

Let A be the exact stored real square matrix, possibly nonsymmetric, and
S=(A+A^T)/2. Construct a connected positive-conductance tree Laplacian plus one
positive root ground,

    T=L_tree+g*e_root*e_root^T,  g>0.

Independently verify R=S-T is symmetric diagonally dominant with nonnegative
diagonal: R_ii>=sum_(j!=i)|R_ij|. This implies R is positive semidefinite, so
S>=T>0. No assumption of symmetry, M-matrix signs or physical element identities
for the original A is needed once that exact inequality is established.

Tree injection at vertex i gives the diagonal Green value
(T^-1)_ii=1/g+sum_(e on root-to-i path)1/c_e. Therefore

    trace(T^-1)=n/g+sum_edges subtree_size(e)/c_e.

Because lambda_max(T^-1)<=trace(T^-1), lambda_min(S)>=1/trace(T^-1).
For every real x,

    ||A*x||2*||x||2 >= x^T*A*x=x^T*S*x
                    >= ||x||2²/trace(T^-1).

Consequently A is invertible, ||A^-1||2<=trace(T^-1), and

    ||A^-1||inf <= sqrt(n)*trace(T^-1).

All reciprocal terms and the final product must be bounded upward. Integer
ceil_sqrt(n) is a safe replacement for sqrt(n), avoiding an additional floating
square-root enclosure premise. For the retained unit rooted m×m grid, BFS root
distances sum to m²(m-1), so the bound is m³/g+m³(m-1):256 for4×4,g1;
4096 for8×8;6561 for held-out9×9. The exact4×4 inverse norm is216/7. The new bound
is loose but polynomial and requires no approximate inverse weights or factor
residual. This is a genuinely different proof use of the same tree.

The entire joined free/terminal matrix can be treated this way, preserving
nonsymmetric original free blocks and independently rounded B,D and wire stamps.
Then there is no separate Schur claim: the full original operator is the certified
target. Full-operator binding, one selected physical RHS and original residual,
energy/reaction functions still apply. Tiny joined success is not original-data
eligibility.

## Necessary limitations and verification requirements

1. Tree T is itself symmetric diagonally dominant. If S-T is SDD, S must be SDD,
   since sums preserve that cone. Tree subtraction therefore cannot cure a true
   diagonal-dominance deficit in the original symmetric part. Distributed
   terminations across nonadjacent support vertices can create positive
   off-diagonals and such deficits. Include a nonadjacent-support adversary;
   two-node fixtures may hide it because strong negative copper cancels the
   positive distributed off-diagonal.
2. Exact zero-margin Laplacian rows are common. Naive nextafter interval sums can
   produce a negative lower margin even when the exact margin is zero. A negative
   margin cannot be clamped or tolerated. An exact dyadic accumulator is a valid
   rigorous alternative if its bit width, work and storage are explicitly
   bounded. Binary64 numbers and halves fit a common denominator2^1075; bounded
   row sums add only bounded numerator bits. Big-integer limb work is not one
   uncharged production scalar operation.
3. The retained source uses approximate row sums solely to choose a tree.
   Verification must bind actual tree coefficients and check exact S-T, rather
   than accepting producer metadata or the tree identity as proof.
4. Positive tree edges, a connected acyclic tree, finite positive root ground,
   all original coordinates and every original stored coefficient must be bound
   and validated. No factor/Schur applicability is inherited automatically.
5. This proof trades stronger structural hypotheses and potentially looser
   inverse bounds for simpler certificate work. Resource review and actual
   synthetic field/energy/reaction dispositions are necessary before selecting it
   as the next method. Original qualification and production remain separate.

## Implemented refinement: exact diagonal deficits and interval inputs

The implementation now extends the unshifted theorem above rather than treating
small stored diagonal-dominance violations as zero. Let delta be an upper bound
for max_i(0,-margin_i(S)), determined by exact bounded dyadic row arithmetic.
The selected root ground remains <=its actual positive unshifted margin; each
selected edge c is <=the exact negative symmetric off-diagonal magnitude.
Subtracting such a Laplacian edge preserves its endpoints' SDD margins. Therefore
S+delta*I-T is SDD, and

    lambda_min(S)>=1/tau-delta,
    ||A^-1||inf<=ceil_sqrt(n)*tau/(1-delta*tau),
    tau>=trace(T^-1),  delta*tau<1.

The code independently recomputes margins, validates the connected tree by an
order permutation and earlier-parent check, and bounds trace upward. Its exact
deficit is converted upward to binary64, including a nextafter when needed;
the positive denominator is rounded down. An unrepresentably tiny deficit may
conservatively refuse in the floor-conversion helper; it is not silently erased.
The n<=128 gate makes all subtree integer masses exactly representable when used
in the final outward division. The common dyadic denominator is2^1075; each
binary64 numerator is even, so half_sum's integer division by2 is exact. No
exact matrix solve is hidden in this verification.

The generic interval-replacement wrapper binds the actual entry intervals and
midpoint CSR separately. For every represented M=A+Delta it independently
computes rho>=||Delta||inf and, from K>=||A^-1||inf, requires K*rho<1. It returns

    ||M^-1||inf<=K/(1-K*rho).

This is the ordinary infinity-norm Neumann perturbation proof, so it also covers
independently varying nonsymmetric terminal entry intervals. It avoids any
unsupported row-norm-to-spectral-norm inference. The midpoint is not substituted
for the original coupled operator; its interval discrepancy is paid explicitly.
The complete-operator path makes no Schur-certificate claim.

## Independent implementation checks

The [independent coercivity oracle](independent-coercivity-oracle.py) uses seed278
for100 small nonsymmetric mixed-sign exact inverse comparisons, including50
with nonzero exact diagonal deficits. Every certified bound contains the exact
Fraction inverse norm. A one-ulp grounded near-singular2×2 matrix is certified
conservatively; singular and indefinite controls refuse. Eleven malformed/stale
tree packet cases and three malformed interval-replacement schemas refuse.

For the grounded, weakly grounded and nonsymmetric independently rounded coupled
fixtures, the oracle verifies each original exact6×6 inverse norm and all16
terminal-interval endpoint combinations. All51 complete-operator inverse checks
pass. This checks the interval wrapper independently, including nonsymmetric
endpoint selections. [Results](independent-coercivity-results.json) retain the
bounds, exact reference norms, deficit factors, interval perturbation factors
and inspected source hashes. No oracle output is read by either producer.

I independently ran the three structured-weight tests and seven coercivity tests:
PASS. The structured tree-path positive control is valid, but does not overturn
the retained grid counterexamples. The coercivity tests certify the polynomial
grid bound, nonsymmetric/mixed-sign coefficients and complete coupled intervals,
and use actual residual, energy, whole distributed termination and reaction
functions. The weakly grounded actual synthetic screen is INCONCLUSIVE. A
nonadjacent distributed-stamp matrix which is independently SPD refuses this
certificate; no false singularity or intervention rejection is inferred.

**Mathematics verdict:** PASS for the bounded tree-coercivity/deficit/interval
prototype and its stated complete-operator scope. The componentwise tree-weight
recipe is REJECTED on the exact retained controls. Original usefulness,
production cost and admission eligibility remain separate resource and empirical
questions; this review authorizes no original execution. Exact integer arithmetic
must retain its own transparent operation/bit accounting and cannot be silently
mapped to a cheaper production counter.

## Reviewed path-energy refinement

The final source retains the trace bound as a valid control and optionally
improves it using the same verified tree. Since I<=tau*T,

    S>=T-delta*I>=(1-delta*tau)*T=gamma*T.

Set H=T^(-1/2)*A*T^(-1/2). Its symmetric part is at least gamma*I, hence
||H^-1||2<=1/gamma. Cauchy-Schwarz then gives, for ||f||inf<=1,

    |e_i^T*A^-1*f| <= sqrt((T^-1)_ii * f^T*T^-1*f)/gamma.

The grounded tree inverse is entrywise nonnegative, so
f^T*T^-1*f<=1^T*T^-1*1. Root-path resistance and unit-load tree energy give

    rmax = max_i (T^-1)_ii = 1/g + max_i sum_(root-path i) 1/c_e,
    s = 1^T*T^-1*1 = n²/g + sum_edges subtree_size(e)²/c_e,
    ||A^-1||inf <= sqrt(rmax*s)/gamma.

Both rmax and s are computed upward by bounded tree passes. At unit grid4,
rmax=7,s=536, so the refined bound is sqrt(3752), approximately61.2536,
compared with the trace control256 and exact inverse216/7. Grid8 and held-out9
have products212640 and423657, giving about461.13 and650.89 instead of4096 and
6561. This uses the verified tree as an energy comparison, not its failed
componentwise Poisson barrier.

The trial library square root is not trusted as proof: a finite positive output
must pass an independent outward lower-square >= upper-product check. At most
four nextafter attempts are allowed. Failure retains the valid trace bound with
all attempted work retained; operation-cap failures propagate. During review I
found the initially missing positivity check: a negative trial could pass a
squared inequality and yield an invalid negative bound. The coordinator fixed
this before final acceptance. Independent zero, negative and half-size trial
mocks now refuse the refinement and return the valid trace bound, with cumulative
phase totals intact. The main suite additionally covers NaN trial and caps.

The final independent100-case inverse comparisons use refine=True, and the
51 complete coupled/interval-corner checks use the refinement through the wrapper.
All pass. The retained weak coupled interval bound remains large because the
exact operator is ill-conditioned; a tighter uniqueness bound does not change
that fact or promise a useful physical disposition.

## Final exact-arithmetic review and inspected identities

The IEEE decoder independently matches Fraction for1000 finite binary64 bit
patterns, including signed zero, smallest subnormal, normal/subnormal boundary
and largest finite values.999 half-sums also match exactly. Normal stored exponent
e produces integer significand<<e at denominator2^1075; subnormals use fraction<<1.
This verifies the decoder's arithmetic meaning independently of its implementation.
Fixed-width kernel and squared-bit-work accounting is exposed separately; neither
this test nor the mathematical proof approves a production scalar-update mapping.

Final independent coercivity suite:7 tests PASS, observed0.573s. Independent
coercivity oracle and tree oracle PASS under30s outer timeout,512MiB address-space,
20CPU seconds and one numerical-library thread. The reviewed source identities are:

| File | SHA256 |
| --- | --- |
| fixture/prototype.py | 762257f82db7d6b0abfdb545af2c6408687ec66bb56f114d6d197d7db50fba6d |
| fixture/test_structured.py | 0dc3bb5e38b15f7a9aded5fb367faf45e73536caf9b8a2714802445abdcc1c88 |
| fixture/test_coercivity.py | cf4f91819066fd9a36ec79c345ac4c585d5e51c6b458d5155a36bfcf6905b608 |
| independent-tree-oracle.py | 86635ac05a7568ea1afde7c7417732c0f6a7f3c1eeca9ca0b152bfb0b9c9fcef |
| independent-tree-results.json | 163783db394e47213ec1e8a2041d3ec8e6382be5c9fc5fb81ab3172843a7def9 |
| independent-coercivity-oracle.py | 04e9c2ce2014ecf6ed7fcfa5149433f538e8492aca12bfdfa03cccbb4f855fe3 |
| independent-coercivity-results.json | 4e90bfc798b51504993446b8bb0357070c705b9295557016d79c51d9cc56f2c1 |

The synthetic mathematics increment is reviewed. The whole attribution objective
remains unresolved: original structural applicability, useful original energy and
reaction enclosures, resource fit and genuine admission have not been established.
