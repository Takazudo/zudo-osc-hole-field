# Independent mathematics and source review

Reviewer: `/root/math_review`, separate from the coordinator and prototype author.
Date: 2026-10-15 JST. Scope: source, retained reports, generated synthetic matrices,
exact-rational calculations and the existing resolution functions. No original
operator/reduction/mesh archive was opened, no campaign claim was made, and no
production source or physical design was changed by this reviewer.

**Verdict: PASS for the stated identity-permutation synthetic certificate and
its tested Schur lift. Original-data applicability, useful original-data error
bounds and full-pipeline resource qualification remain NOT ESTABLISHED.** The
retained-Y lift has a separate resource rejection; the fixed rooted-tree producer
has the quantitative usefulness failure proved below. Neither is a reason to
promote a different untested producer.

## The proof checked against code

For exact stored A and finite triangular witnesses F=LU, the verifier encloses
every entry of E=A-F before summing absolute row bounds. If C(T) has diagonal
|Tii| and off-diagonal -|Tij|, absolute triangular substitution proves
|T^-1| <= C(T)^-1 entrywise. C(T)^-1 is nonnegative. Therefore the implemented
positive recurrences give q >= ||F^-1 E||inf and k >= ||F^-1||inf. Strict q<1
implies A=F(I+F^-1 E) invertible and ||A^-1||inf <= k/(1-q). The denominator and
all recurrences are outward enclosed. An unresolved pivot, overflow or q>=1
refuses this proof; it does not establish singularity.

The prototype refuses nonidentity permutations. For a later PAQ factorization,
the board norm proof remains valid, but its Schur witness must be mapped as
h_original=Q(LU)^-1 P B. Multiplying original B^T by an unpermuted factor solve
would be incorrect. This review does not authorize that extension.

For the selected factor-only lift, signed interval solves enclose h=F^-1 B.
Writing T=F^-1 E yields

    A^-1 B - h = -(I+T)^-1 T h,
    ||A^-1 B[:,j]-h[:,j]||inf <= q/(1-q) ||h[:,j]||inf.

The code keeps both the signed-solve interval width and this correction, then
encloses each exact Schur entry D_ij-B[:,i]^T A^-1 B[:,j]. It certifies the small
interval Schur with an independently enclosed I-R*S residual, rather than
trusting the approximate inverse R. Negative U diagonals are handled by signed
interval division; positive comparison recurrences use absolute diagonals.

The global block bound (1+f)*max(a,s)*(1+g) is correct with
f=max_i a_i||B_i||inf and g=max_i a_i||B_i^T||inf for the project's disjoint
KA/KB terminal blocks. The prototype explicitly refuses a terminal column
shared by boards. Without that condition, the backward row norm could need a
sum across boards and the maximum would be unsafe.

## Findings resolved during this review

1. Factor coefficient validation initially allowed integers/other numeric types
   despite the exact-binary64 theorem. A mixed-type conversion can introduce
   rounding not covered by a singleton interval. Factors now require built-in
   finite floats; fresh-hash malformed witnesses are tested.
2. B, D and signed-solve RHS initially permitted silent conversion of extended
   precision inputs. B now requires a finite binary64 ndarray; D requires exact
   binary64 singletons or ordered finite float interval endpoints; signed RHS
   rejects extended inputs. New tests exercise each refusal.
3. The source initially lacked a complete B/D/context digest at the block
   boundary. The final result binds those inputs along with original A hashes.
   It is explicitly a construction digest, not an admission signature or a
   reusable production authority token.
4. A signed triangular solve of the all-ones vector is not an inverse norm
   bound. For L=[[1,0,0],[1,1,0],[1,1,1]], U=I, its signed result is [1,0,0],
   although exact ||L^-1||inf=2. The implemented comparison recurrence returns
   a safe bound >=4; the adversarial test would catch the unsafe substitution.

## Independent quantitative Schur checks

[independent-schur-oracle.py](independent-schur-oracle.py) implements the lift
independently of the prototype's block_certificate function. It uses the
prototype only for board factor production/verification and the existing outward
scalar primitives. Exact Fraction inversion checks each board's exact Schur
value and the original joined inverse norm. The generated fixture uses two
2-node copper blocks, grounded KA and floating KB, weights (.25,.75) and
(1/3,2/3), Rt=.7 and wire conductance4. The terminal diagonal is the exact sum
of separately stored D and wire coefficients, not a newly rounded singleton.

[Retained results](independent-schur-results.json):

| Case | Board q values | Joined result | Global inverse bound / exact norm |
| --- | --- | --- | --- |
| Ground1, full factors | 5.67e-16 / 1.59e-15 | Schur q=2.49e-14; certified | 31.4506053 / 12.5240741 |
| Ground2^-30, full factors | 1.19e-15 / 1.59e-15 | Schur q=1.53e-5; certified | 1.89543e10 / 6.44245e9 |
| Ground1, diagonal factors | .617834 / .849246 | Schur q=1.488536; refused | No joined bound |
| Ground1, full KA / diagonal KB plus constant witness | 5.67e-16 / .849246 | Schur q=2.13e-14; certified | 50.55 / 12.5240741 |

The third row is decisive: both boards certify yet the exact joined Schur lift
refuses. Its correction radii .88262/2.10855 lose the cancellation that makes
floating KB's Schur small. No board certificate alone supports attribution.
The second row is a separate limit: valid uniqueness can leave a huge selected
field error and an INCONCLUSIVE intervention.

### Concrete constant-vector improvement, with charged work

For one terminal, form an independently verified r=B+A*1. Exactly,

    A^-1 B = -1 + A^-1 r,
    S = D+B^T 1-B^T A^-1 r.

Thus the scalar Schur is enclosed around D+B^T1 with radius
a*||B||1*||r||inf. This uses the original stored coefficients and requires no
assertion of exact conservation, exact symmetry or physical element metadata.
The identity is valid even when r is not small; usefulness then fails honestly.

On the same fixture, diagonal KB factors give inverse bound2.10. The new verified
||r||inf is8.881784197e-16, reducing the KB Schur correction radius from2.108546
to2.664535259e-15. Full KA plus this KB witness certifies the original joined
operator with bound50.55. This is a tested cancellation-preserving improvement,
not a claim that actual KB has a sufficiently small residual or an eligible cost.

The fixture explicitly records four additional A-row additions, plus scalar
B/D contractions and bound arithmetic. Fusing these sums into an existing scan
saves input traversal, not their arithmetic charge. On original KB, an exhaustive
row-sum implementation still has an additional nnz(A_KB)-scale work requirement.
For multiple terminals the one-vector identity alone does not determine every
Schur column. No original-data use or production implementation is approved here.

## Fixed rooted-tree producer: a scalable adverse bound

Consider an m by m unit-conductance grid, m>=3, grounded at node(0,0) by g>0.
The proposed fixed pattern chooses the node immediately above as parent, or the
left neighbor for top-row nodes. Let F retain A's diagonal and only its negative
parent entries; it has a unit-lower/diagonal factorization. F^-1 is nonnegative.
Because A*1=g*e_root and A-F has only nonpositive omitted entries,

    r=|A-F|*1=F*1-g*e_root,
    F^-1 r=1-g*F^-1 e_root.

At node(m-1,m-2), the unique parent path has root diagonal2+g, m-1 factors3
and m-2 factors4. Set D=(2+g)*3^(m-1)*4^(m-2). The exact comparison contraction
therefore has 1-q<=g/D. Since K>=1/max(4,2+g), the certificate's inverse bound
must be at least D/[g*max(4,2+g)]. Outward rounding can only worsen this result.
For g=1, m=8, the margin is at most1/26,873,856. At m=16 it is at most
1/11,555,266,180,939,776 =8.654062869e-17, and the certificate bound is at least
2,888,816,545,234,944 even before additional enclosure error.

This is not intrinsic ill-conditioning at that exponential scale. For each node,
use a root path of length <=2(m-1). Weighted Cauchy gives

    x_i^2 <= (1/g+2(m-1))*x^T A x.

Summing over m^2 nodes yields lambda_min(A)>=1/[m^2*(1/g+2(m-1))] and hence
||A^-1||inf<=m^3*(1/g+2(m-1)). At m16,g1 the actual norm is therefore <=126,976.
The fixed tree's certificate lower bound is more than ten orders larger than
this rigorous upper bound for the true norm. A positive tiny fixture cannot
justify this producer as a scalable useful certificate. This counterexample
rejects the specified pattern, not every possible capped incomplete factor.

### Next proof direction: positive weighted contraction

For any exact positive vector h, enclose r=|E|h and
z>=C(U)^-1 C(L)^-1 r, and verify q=max_i(z_i/h_i)<1. With
y>=C(U)^-1 C(L)^-1*1 and k=max_i(y_i/h_i), weighted infinity norms give

    ||A^-1||inf <= max(h)*k/(1-q).

This is valid for arbitrary finite nonsymmetric A and the same triangular
witnesses; positivity of h and every weighted arithmetic step must be verified.
It does not make producing a useful h free. A positive approximate vector need
not satisfy A*h=1: that identity is used only in the following exact grid oracle
to demonstrate that the weighted approach can improve the bound.

For the exact rooted-grid fixture take h=A^-1*1, computed by a dense Fraction
solve of order16 solely as an independent oracle. Then r=F*h-1 and z=h-y;
q=1-min_i(y_i/h_i), k=max_i(y_i/h_i). On the same4x4 grid, maxh=216/7,
q=22151/22410, k=56/2187, giving bound53120/777=68.36550837, versus the
unweighted exact bound989.3333333 and actual inverse norm216/7=30.85714286.
The retained oracle and JSON include this calculation separately as
EXACT_PROPOSAL_CALCULATION_ONLY.

There is also a polynomial existence bound for this particular grid family:
0<y<=h and y_i>=1/maxdiag imply k<=1 and 1-q>=1/(maxdiag*maxh), hence the
weighted bound is <=maxdiag*(maxh)^2. The root-path bound above makes this
polynomial in m. This demonstrates a justified next mathematical direction;
it is not a source of real-data weights, a new numerical request, or an
implemented outward weighted verifier. Weight production, binding, additional
weighted residual products/divisions and useful original-data scaling remain
explicit work before any admission decision.

## Source mapping and actual resolution tests

Reviewed attribution_uniqueness.py, attribution_resolution.py,
attribution_executor.py, finite_solve.py, finite_adapter.py and the relevant
sheet_mesh assembly. Original Af entries can be nonsymmetric. Termination Af,
B and D are independently rounded; exact rank-one positivity cannot be inferred
for those stored blocks. Physical accounting correctly retains the whole
(w^T v-t)^2/Rt functional. The counterexample w=(1/2,1/2),v=(1,-1),t=0 has whole
energy0 but independent-edge energy1; its test is mandatory and passes.

The final 18-test fixture suite was independently rerun: PASS, 0.063s observed.
It includes exact-rational joined and nonsymmetric Schur checks, a disconnected
coupling refusal, weak grounding, cancellation, negative pivots, malformed/stale
witnesses and bound-input rejection. Its selected-field test calls the actual
residual_bound, energy_interval and reaction_interval functions; exact rational
selected-solution energy and a held functional including a distributed
termination fall inside their enclosures. A valid but loose bound returns
INCONCLUSIVE through the actual screen. These are synthetic functional tests,
not an execution of original mesh reconstruction or TP990026 production data.

The independent oracle also passed four Schur cases of order6 and the exact
weighted proposal calculation of order16, under512MiB address-space,
20CPU-second and one-BLAS-thread limits. The fixture suite caps order128,
512MiB, 20CPU-seconds and30 wall-seconds. Neither timing establishes original fit.

## Reviewed identities and remaining decision

| Retained source/result | SHA256 |
| --- | --- |
| fixture/prototype.py | 3ce2ca1f693d65cb09df64da89e01ca99129a958c4672f8fd82ac1696c9b612e |
| fixture/test_prototype.py | d232775271f3647cbe5a425a8a0d93ed4820f4c37c20d69a07e3c92951bd74e4 |
| independent-schur-oracle.py | 49ba395795dd8d67e285863774ae3aba1d14faf8da14715ffc1134654b817ced |
| independent-schur-results.json | 5ee5a2c353779c2a4493d1c685209811737fc7513a09b2e70c764981040f5d07 |

Reproduce from the executable source directory with the established numerical
venv's Python: run fixture/test_prototype.py and independent-schur-oracle.py
under this evidence directory. The latter prints its own and dependency hashes.
No production request or authority is accepted by either script.

The next unresolved mathematical decision is a fixed factor producer with a
quantitative reason for useful original-board contraction and error bounds,
possibly combined with the verified scalar constant witness if its explicitly
charged cost is eligible. Do not run the rejected tree, port the rejected
retained-Y architecture or use a general-purpose opaque factorization as an
uncharged shortcut. Resource review, original applicability, guarded admission,
all original accounting phases and useful Stage C enclosures remain separate.
