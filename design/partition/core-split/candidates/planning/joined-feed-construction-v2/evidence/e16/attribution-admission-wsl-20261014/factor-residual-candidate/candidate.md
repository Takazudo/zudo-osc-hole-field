# Stored-operator factor-residual candidate

This is the continuation of WORK.md, not an admission or resource qualification.
The production executor still selects the reference/frontier/RCM certificate.
The candidate below is a source-only investigation of a different algebraic proof.
No original operator, reduction or mesh archive was decoded for this investigation.

## Reconciliation and scope

On 2026-10-14/15 JST the executor worktree and published branch both had HEAD
`df58a3a043d81ebac973cbde9d569a7af912be8a`. Tracked state was clean. The two
ignored frontier/ordering prototypes remained present; the repo-scoped cclogs
survey found no E16-named artifact. Process and tmux inspection found the present
coordinator and no competing E16 executor. The canonical ledger hash was still
`533ca512fc06ae6742e6e02dce3cc1a8aee83ec49fc13ebabf691a6b0c4cc4f5`:
seven terminal INCOMPLETE attribution charges, live_owned_work=false, 15/24
diagnostics and 2/3 baselines. Nine diagnostics remain; no additional baseline.
PR277 and PR260 were OPEN/draft; issue253 OPEN. No key or signer change occurred.

## What the existing pipeline needs

Let A=diag(Aa,Ab) contain the exact stored free-node board blocks; let B contain
the exact stored free-to-terminal blocks, and C=D+W the terminal blocks plus
the exact stored wire conductances. The original problem is

    M = [ A    B ] ,  M x = f.
        [ B^T  C ]

This notation does not authorize a global matrix allocation. Original Af can be
nonsymmetric. Neither its symmetric part nor a factor product replaces it.
finite_solve.board_parts computes each termination's outer-product coefficients,
B and D in binary64 separately. They need not form an EXACT real rank-one matrix
after those separate roundings. Physical accounting still evaluates the entire
distributed functional (w^T v-t)^2/Rt; it is not a sum of independent edges.

1. **Nonsingularity:** certify both exact stored A blocks and their exact joined
   Schur complement S=C-B^T A^-1 B. Approximate retained Y and S do not suffice.
2. **Selected field error:** attribution_resolution.residual_bound encloses every
   original free and terminal equation, including wires. If its infinity bound
   is rho and a certificate gives J >= ||M^-1||inf, delta=up(J*rho) encloses the
   existing computed selected field's error. Original solve/refinement and RHS
   remain unchanged. No extra physical excitation is introduced by this proof.
3. **Physical outputs:** energy_interval evaluates each original reconstructed
   local quadratic form on field intervals; the sum encloses total copper and
   every original interval of the named barrel. reaction_interval evaluates K's
   held rows and whole distributed termination functionals at TP990026. Their
   validity depends on the existing complete mapping/partition checks too.
4. **Disposition:** failure to prove uniqueness, failed binding, overflow or caps
   refuses certification; none means rejected intervention. With uniqueness,
   copper lower <=0, a share crossing 10%, or an unresolved reaction can leave
   Stage C INCONCLUSIVE. screen can reject with share upper <10%; support needs
   share lower >=10% AND reaction excluding zero. Exactly zero reaction is a
   separate rejection case after the positive-copper gate. No new tolerance.

Bare positivity is not useful enough. For a local form Q, the existing naive
interval products have a conservative first-order sensitivity proportional to
sum_ij |Qij|(|vi|+|vj|), even when the physical energy has strong cancellation.
A certificate must demonstrate its resulting delta against the actual energy
and reaction enclosures, not merely print a finite inverse bound.

For planning a useful margin, enclose the computed centers T0,C0,J0 and arithmetic
radii eT,eC,eJ. Bounds DT(delta), DC(delta), DJ(delta) on perturbations must satisfy
C0-eC-DC>0 and either

    T0-eT-DT >= .1*(C0+eC+DC),  |J0| > eJ+DJ  (support), or
    T0+eT+DT <  .1*(C0-eC-DC)                  (share rejection).

These are sufficient conditions, not altered screen criteria. A linear functional
has DJ <= delta*sum|coefficients| with held errors zero. For a quadratic form,
DT <= delta*(||Qv||1+||Q^T v||1)+delta^2*sum|Qij| with outward arithmetic and the
held-coordinate mask. This centered alternative is a theorem only here; production
still uses its original interval evaluator. Actual original T0 and J0 have not
been computed by this campaign, so original-data usefulness is not claimed.

## Rump source and applicability decision

Primary source: S. M. Rump, DOI
[10.1137/25M1722573](https://doi.org/10.1137/25M1722573), author-hosted
[final manuscript](https://www.tuhh.de/ti3/paper/rump/sparselss_I_final.pdf),
49 pages, SHA256 `aaf94ce47e5023f6e22bdcd3f80c984669b69ceb1bd709e62fc276bb54df8a34`,
3,111,700 bytes. Retrieved 2026-10-14 UTC; read Theorem6.1 (physical index20),
Sections7–9 and Tables5/6 (indices24/27), not just the abstract. The old submitted
PDF URL redirected to HTML and was not treated as the paper. The local PDF is a
working cache; it is not redistributed in Git.

Theorem6.1 bounds a symmetric matrix through shifted Cholesky and a rigorous
factorization residual. Its a priori estimate requires operation/rounding and
sparsity hypotheses, including absence of underflow/overflow. Tables5/6 also
form split factors, a Gram product, its error bound, and shifted Cholesky; success
requires the shift to exceed three certified error terms. General matrices use
a doubled symmetric augmentation. An eigenvalue estimate or successful LU alone
does not establish these inequalities. Our existing nextafter arithmetic is not
a proof that a library Cholesky satisfies that algorithm's hypotheses.

**Project decision:** do not port the full algorithm or install its numerical
stack. Existing retained reductions contain Y/S and LU counts, not reusable LU
factors. The measured original nominal LU has 21,097,522 entries for KA and
21,002,074 for KB. Even excluding both diagonals leaves 18,069,848 and at least
17,919,518 entries, respectively, beyond 4M before verification scratch. This
rejects reuse/recreation of those full-size factors as retained witnesses. It is
not a theorem that every alternative split factor or every Rump implementation
is impossible. No original factor counts for the paper's Gram/shifted stages
exist; they cannot be equated to the historical LU counts.

## Selected alternative: a capped incomplete-factor residual

The following elementary argument is derived here; it is not represented as an
implementation of the paper. Fix exact row/column permutations P,Q (initial
prototype identity only). Let L have an implicit unit diagonal and strict-lower
binary64 entries, and U be upper triangular with finite nonzero diagonals.
Both factors are analysis witnesses. Define E=P A Q-LU for the exact stored A.
The executable prototype and the selected Schur lift below RESTRICT P=Q=I.
For future nonidentity permutations, h in original coordinates must instead be
Q*(LU)^-1*P*B; original B^T must multiply that original-coordinate h. No such
permutation extension is implemented or authorized by this prototype.

For triangular T let C(T) have diagonal |Tii| and off-diagonal -|Tij|. Absolute
forward/back substitution proves |T^-1| <= C(T)^-1 entrywise; the right side is
nonnegative. This does NOT assume signs of A or equality to a signed solve.
Stream exhaustive outward intervals for each residual row and retain only
r_i >= sum_j |Eij|. Positive triangular recurrences give

    z >= C(U)^-1 C(L)^-1 r;       q = max(z),
    y >= C(U)^-1 C(L)^-1 1;       k = max(y).

If q<1, ||(LU)^-1 E||inf<=q and PAQ=LU(I+(LU)^-1 E) is nonsingular by the
Neumann series. Therefore ||A^-1||inf <= up(k/down(1-q)). Permutations preserve
the norm. Every quantity used by this argument is directly obtainable from
stored coefficients and finite factors; no original element metadata is needed.
q>=1 refuses this certificate, including for matrices that are actually invertible.

### Witness production and verification map

| Hypothesis/witness | Exact procedure | Refusal | Pipeline result |
| --- | --- | --- | --- |
| Original matrix/context identity | Bind canonical sparse data, dimensions, held/free maps, board/case/depth, B/D, source/config/method digests; never infer identity from factorization success | Missing, stale, noncanonical or mismatched binding | Original A is the certified target |
| Finite triangular factors, implicit unit L | Fixed pattern, bounded row-by-row incomplete elimination; check all diagonals/indices and account every production update, including updates later dropped | Bad pivot, invalid index, fill/work/storage overflow | Algebraic invertible LU witness only |
| Full residual E | For each row accumulate every A entry and every logical LU product with outward intervals; take absolute values after cancellation, then discard the row | Omitted term, nonfinite endpoint or pre-insertion cap | r >= |E|1 |
| Triangular comparison | Outward positive recurrences for r and ones, including division by exact absolute U diagonals | Overflow or bad divisor | q and k upper bounds |
| Contraction | Strict q<1 and outward positive denominator | q>=1 or unresolved subtraction | Original nonsymmetric A nonsingular, inverse upper bound |
| Exact joined Schur | Enclose h=(LU)^-1 B with signed interval solves; add q/(1-q) column errors; enclose D-B^T*h and exact wire g | Missing column, wrong terminal mapping, excessive interval width | Interval containing exact nonsymmetric S |
| Small Schur certificate | For a fixed small approximate inverse K, enclose every entry of I-K*S and require its infinity norm <1; include interval radii | Singular/uncertain Schur, overflow or caps | Bound ||S^-1||inf |
| Global inverse/error | Block factorization norm bound below, then unchanged original residual and physical accounting | Any failed original identity/partition/numerical gate | Selected field, energy/share/reaction enclosure or INCONCLUSIVE |

No original-data witness producer is selected by a tiny positive fixture. Pattern
selection itself has time/memory costs. No generic spilu followed by truncation:
that would produce oversized factors and hide preprocessing. A real proposed
pattern must have a structural reason for useful contraction under severe dropping.

### Rejected first Schur lift: certified retained-basis residual

The following is mathematically sound but its explicitly charged implementation
is rejected by the lower bound below. It is retained to explain the concrete
change of method, not as another implementation in flight.

For each board set R=B-A*Yhat using the bound retained basis with its actual
longdouble entries enclosed by pair(). Since A^-1 B=Yhat+A^-1 R, each error
column is bounded by a_i*||R_col||inf, where a_i is the certified board inverse
bound. Multiplication by each column's absolute B sum encloses B^T A^-1 R.
This produces intervals for exact S, not a certificate for the approximate
retained Schur. Arbitrary nonsymmetric small Schur intervals must be supported;
the current symmetric certify_coupled API cannot be silently reused.

Let a=max_i a_i, b=max_i ||B_i||inf, with tighter per-board products permitted;
let f=max_i a_i||B_i||inf and g=max_i a_i||B_i^T||inf. If s bounds ||S^-1||inf,
block factorization gives

    ||M^-1||inf <= (1+f)*max(a,s)*(1+g).

There is no sqrt(N) coercivity penalty for this direct nonsymmetric proof.
The retained original basis remains a bound input, not newly produced factors
hidden as input. Newly allocated Schur residuals, interval columns and factors
must be counted with their actual overlapping lifetimes.

## Work and storage, before any original-data characterization

The existing Work.updates is **not a FLOP counter**: it charges a scalar interval
Schur update in LDL. It is shared across both boards and small coupled checks.
Hashes, CSR conversions, ordering, norm sweeps, original residual and accounting
passes are not increments of that counter, but remain subject to deadline/memory.

For this candidate, conservatively charge factor-generation multiply/subtract
updates, every logical LU product contribution (including implicit identity
copies), and both triangular comparison sweeps to the same 20M ceiling. Record
phase counts separately without resetting the cumulative counter. Also report
diagonal divisions, input reads, row reductions, binding and conversions. There
is no claim that this extended definition retroactively changes prior counters.

If F=nnz(strict L)+nnz(U), Eoff=F-n, and
Wprod=sum_k (1+nnz(strict L[:,k]))*nnz(U[k,:]), the board verifier needs at least
Wprod+2*Eoff such charged contributions, plus producer Wgen. New certified basis
residuals cost kterminal*nnz(A) contributions per board if charged under this
explicit extension. Original pipeline residuals remain separately reported.
The small Schur proof and both boards share the remaining allowance.

F plus all live residual-row entries and any producer row scratch must fit4M
BEFORE insertion. A single residual row may be dense despite sparse factors;
row and column degree limits or an early symbolic product bound are necessary.
Vectors, dictionaries, indices, original arrays, factor conversion copies and
temporaries additionally count toward actual worker memory, even when not sparse
entries. Full producer factors cannot be generated before checking this cap.

KA has order1,513,837 and stored nnz7,818,329. Literal stored-pattern ILU with implicit
unit L still needs7,818,329 slots, already >4M. Stored nnz can include explicit
zeros: this is not by itself proof that nonzero-pruned ILU needs that many slots.
The retained symmetric nonzero structural-union count is also7,818,329, but
without an exact nonzero-diagonal count it only implies a one-sided nonzero
count >=3,909,165. Do not infer exact symmetry from those equal totals. One U diagonal leaves at most
2,486,163 off-diagonal entries minus scratch. A full original strict triangle plus
that diagonal is about4,666,083 entries IF the pattern is symmetric with all
those diagonals nonzero; those additional hypotheses are not established by
the retained counts alone. That conditional calculation does not establish an unconditional rejection of
a zero-pruned one-sided factor pattern. Aggressively incomplete factors
are not ruled out by dimensions alone, but dropping enough structure may destroy
contraction or leave an unusable error bound. Tiny timings cannot resolve this.

Original pipeline obligations remain: input verification; board_parts conversions
and overlaps; retained Y for both boards; original KB LU/refinement; small solve;
complete original residuals; eight mesh replays per board inside Assembly and a
ninth for accounting, including all chunk validation; original partitions,
energies, reactions, output retention and cleanup. Historical reconstruction
times34.047/45.241s and roughly1002/1010MiB are separate-job observations, not a
combined-lane qualification. The180s shared-entry deadline includes startup/input
verification and reserves15s host tail plus10s cleanup, leaving at most155s to
the numerical-worker deadline. 1216MiB worker, 2GiB aggregate including reserve,
zero swap,64MiB output,16M input and4M live-entry caps remain unchanged.

### Selected factor-only Schur lift

Avoid the extra A*Yhat pass by enclosing h=(LU)^-1 B directly with SIGNED interval
forward/back substitution. This is a witness calculation, not a changed selected
physical RHS or production solver. Let T=(LU)^-1 E, so ||T||inf<=q<1. Then

    A^-1 B = (I+T)^-1 h,
    ||A^-1 B[:,j]-h[:,j]||inf <= q/(1-q)*||h[:,j]||inf.

Use the outward upper magnitude of the entire interval h column on the right.
For each Sij enclose Dij-B[:,i]^T*h[:,j] and widen by
(sum|B[:,i]|)*up(q/down(1-q)*max magnitude(h[:,j])). Keep both the interval solve
width and Neumann correction. Wires and the small interval inverse proof are as
above. A wide Schur interval refuses; a tiny factor residual is important here.
This proof also preserves independently rounded original B/D and nonsymmetric A.

The first lift has a newly demonstrated cost conflict. Let nA=1,513,837 and
nB=1,541,278 (KB has no held sources). If the undirected union of each factor
pattern is connected, Eoff>=n-1. Wprod>=F=n+Eoff, hence both-board factor
verification alone needs >=4*(nA+nB)-6=12,220,454 contributions under the lower
counting convention above. The specified retained-Y loops visit all7,818,329
KA stored entries, even explicit zeros. Certifiable KB needs at least nB entries.
Thus the combined lower bound is21,580,061 BEFORE production, small Schur, etc.
That architecture cannot meet20M. This is conditional on connected factor patterns
and those exhaustive stored-entry loops; it is not a universal impossibility proof.

The factor-only lift instead adds at least one Eoff traversal per terminal column.
For one terminal per board, its connected-pattern dimension floor is
5*(nA+nB)-8=15,275,567, leaving at most4,724,433 contributions for production,
B contractions, the small proof and all other newly charged certificate work.
This is a LOWER bound, not a complete fit prediction. More degree/fill, narrower
interval arithmetic choices, or tiny pivots can make the actual cost much higher.
The prototype intentionally charges more individual scalar steps than this floor;
its printed counters are not a promise of production fit.

## Admission decision

Synthetic verification can establish theorem-to-code correctness and demonstrate
failure. It cannot authorize real execution or prove original-data usefulness.
The current compiler/worker has no characterization branch; a future bounded
diagnostic needs an explicit exact scope and reviewed integration into genuine
admission, not a direct Python invocation or a false full-qualification label.
No new request, grant, baseline, diagnostic charge or production claim is made
by this note. Tests, separate reviews and the actual next decision are retained
beside it and linked from the canonical WORK.md checkpoint.


## Completed experiments and current technical boundary

The retained [fixture](fixture/README.md) contains the single frozen experimental
implementation,18 adversarial tests and outputs. Separate actual
[mathematics review](math-review.md) and [resource review](resource-review.md)
identify their inspected hashes and independent executions. Neither reviewer is
represented as a signing authority. No production source changed.

The independently checked strong-ground six-variable fixture certifies the
original joined operator with inverse upper31.4506053 versus exact12.5240741.
The same fixture with diagonal approximate factors certifies BOTH board blocks
(q=.617834/.849246), yet the joined Schur test refuses at q=1.4885361543.
This is a concrete counterexample to accepting a board-only certificate.
Weak grounding2^-30 remains unique but has global bound1.895456e10. Actual
resolution routines and exact Fraction oracles check field, local energy and
whole distributed reaction enclosures; a valid inverse bound can still produce
INCONCLUSIVE. The original experiment has not supplied a useful bound.

The prototype's actual stricter scalar accounting cannot be scaled directly:
for connected factors its LU residual and two comparison sweeps alone charge
at least2*Wprod+4*Eoff+2*n >=10*n-6 per board. Across both boards that is
30,551,138>20M, before producer/Schur/row sums. A lower contribution-count model
cannot silently replace this meter. Any future kernel must explicitly bind and
review its primitive definition against the existing scalar Schur-update policy;
vectorization does not change logical work. There is no production port here.

### Fixed low-storage tree rejected by an exact scalability bound

A predeclared rooted-tree pattern is small enough in principle: keep each grid
node's diagonal and one lower parent (up, or left on the top row), giving2n-1
factor entries. Unlike the ILU0 toy, this matches the desired entry density.
It still has a demonstrated precision failure: on8x8 with ground1 the certificate
inverse bound is20,159,998.5, while ground2^-30 refuses with q>1.

This is explained analytically, not by timing extrapolation. For an m-by-m unit
conductance grid, grounding g>0 at (0,0), let F be that lower-tree splitting.
Then F^-1>=0, A-F<=0, r=|A-F|1=F1-g*e0, and the exact comparison residual is
z=1-g*F^-1*e0. The path to (m-1,m-2), m>=3, has diagonal product

    Dpath=(2+g)*3^(m-1)*4^(m-2).

Therefore1-q <= g/Dpath, and K>=1/max(4,2+g), so the certificate bound is at
least Dpath/[g*max(4,2+g)]. For m=16,g=1 it exceeds2.8e15. In contrast, ordinary
root-path Cauchy gives lambda_min(A)>=1/[m^2*(1/g+2*(m-1))], hence
||A^-1||inf<=m^3*(1/g+2*(m-1))=126,976 for that same system. The method loses
exponentially while a proved true bound grows polynomially. The fixed tree is
rejected as a scalable useful-bound producer, without spending a diagnostic.
This is not an impossibility proof for every sparse or weighted certificate.

### Follow-through on the floating-KB Schur loss

The independent oracle tests an actual cancellation-preserving algebraic witness
rather than restating missing original-element metadata. For one terminal and
identity permutations, directly enclose r=B+A*1. Then exactly

    A^-1 B = -1 + A^-1 r,
    s = D+B^T*1-B^T*A^-1*r.

This requires NO exact row-sum, symmetry, grounding or rank-one assumption.
Enclosing r from every original stored coefficient covers all separate stamp
rounding. With a certified inverse a, the last scalar has radius at most
||B||1*a*||r||inf, plus outward arithmetic. On the same tiny fixture with KA
full factors and KB diagonal factors, KB's factor-only correction radius2.10855
shrinks to2.66454e-15, and the joined proof succeeds with inverse bound50.55.
The [independent oracle](independent-schur-oracle.py) retains exact checks and
bound values. This is a concrete improvement, not a real-input certificate.

The additional signed row sums must be charged even if fused with another read.
For connected factors, the base plus KA factor solve already costs at least
13,734,290 contributions. A KB stored-entry row-sum pass exceeding6,265,710
entries would exhaust20M before all other phases. Actual KB Af nnz is not in the
retained metadata; LU fill is not a substitute. More importantly, no accepted
useful low-storage factor producer exists yet, so measuring this number alone
would not justify a real diagnostic now. No characterization request is sealed.

### Follow-through on tree attenuation: weighted residual proof

The next source-only action was carried out mathematically on the SAME4x4 tree
fixture. For a positive weight vector p, let r_i>=sum_j|Eij|p_j and propagate it
through the same comparison factors. Set q=max_i z_i/p_i and
k=max_i (C(U)^-1 C(L)^-1 1)_i/p_i. The induced weighted infinity norm gives

    ||A^-1||inf <= max(p)*k/(1-q),  provided q<1.

The factor-only Schur correction also needs this scaling: each column radius is
max(p)*q/(1-q)*max_i magnitude((LU)^-1B[:,j])_i/p_i. Mixing an unweighted Schur
radius with this q would be unsound. Weight entries and all additional weighted
products/recurrences must be bound and charged; they cannot be a free heuristic.

With the exact tiny oracle p=A^-1*1, max(p)=216/7. The weighted q=22151/22410,
k=56/2187 and inverse bound53120/777=68.3655 improve on the SAME unweighted
bound989.3333 (true inverse norm216/7). For this M-matrix GRID FIXTURE only,
p>=F^-1*1>=1/maxdiag and k<=1, yielding a polynomial bound
maxdiag*max(p)^2. This is not an M-matrix assumption about original boards.
The rational oracle computed p through a dense16-variable solve; it is explicitly
not an allowed full-data witness production strategy. No new weighted production
checker was implemented without a credible production cost argument.

### Locally owned next action

Do not port the rejected full/LU0/tree recipes or rerun an ordering. The weighted theorem and tiny improvement are now demonstrated. The next
specific mathematical question is how to produce a useful positive weight vector
from the stored problem while keeping its own production, weighted products and
all coupled checks within the same work budget. It must be constructive:
solving an uncharged global system to obtain a weight vector is not a solution.
Keep the exact tree counterexample and floating-KB Schur test as acceptance cases.
No additional implementation is justified until that witness/cost argument exists.
The numerical lane remains NOT ELIGIBLE, qualification NOT_QUALIFIED, production
NOT_ADMITTED/NOT_RUN, Stage C NOT RUN. This checkpoint records a rejected scalable
producer and two verified algebraic improvements, not completion of the original
engineering objective or a promise of unattended work.

## Constructive increment superseding the previous next-action boundary

The requested bounded producer and rigorous weighted prototype have now been
implemented in the existing fixture, with separate mathematics/resource reviews.
[Weighted increment](weighted-increment.md) retains the new exact eight-pass
counterexample, held-out results, corrected row lifetime accounting, full coupled
case comparison and reviewed original-cost rejection. Earlier results and next
steps above are historical. No original-data characterization is needed to reject
this exact producer; no diagnostic was consumed. The next local method change must
remove repeated full residual production passes before any fit claim or admission.


## Standing-assignment structured continuation

The [structured/coercivity increment](structured-coercivity-increment.md) preserves
the failed weighted recipes, adds an exact tree-flux counterexample, and implements
a different complete-operator tree-energy proof with bounded exact row arithmetic.
Its reviewed synthetic improvement does not establish original applicability or
resource fit. Continue from WORK.md; this checkpoint does not end the assignment.
