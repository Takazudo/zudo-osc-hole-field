# Constructive weighted-certificate increment — 2026-10-15

## Decision

The existing prototype now has a deterministic non-oracle eight-pass positive
weight producer, independent outward weighted verification, and a weighted signed
factor-solve/Schur bridge. The producer is **rejected for original-data use**:
its actual output fails the weighted contraction on the retained rooted-tree grids
and the held-out 9x9 grid, and its repeated full residual passes exceed the
original work budget before verification. The weighted theorem remains valid.
No diagnostic is spent on this rejected recipe.

This is new implementation and counterexample evidence, not a restatement of the
previous weighted exact-oracle demonstration. The old 18-test results, original
mathematics/resource reviews, tree counterexample and exact oracle are preserved.

## Reconciliation before edits

The supplied root checkout was clean main `65cefd41`; the existing executor
worktree was clean at `db742dcfc5022aa037895a3c30bf7b76309a9529`, matching live
PR277's head. No local changes were reset. Ignored frontier/ordering prototypes
and the explicitly superseded factor prototype remain intact. The repo cclogs
survey found no E16 entry. Worktree/process/tmux, systemd unit and lock inspection
found no competing executor or live E16 numerical operation. PR260 was OPEN/draft
and issue253 OPEN. This local WSL CLI has no managed-cloud profile selection;
no cloud startup loader, runtime restoration or global host change was performed.

The canonical campaign-note.json still hashes to
`533ca512fc06ae6742e6e02dce3cc1a8aee83ec49fc13ebabf691a6b0c4cc4f5`:
15/24 diagnostics, 2/3 baselines, seven terminal attribution charges with cleanup,
`live_owned_work=false`. Nine diagnostics remain, zero additional baselines are
authorized. This increment consumes zero and does not prepare requests or grants.
Signing ownership and keys remain unchanged. No original numerical archive was
opened, decoded or probed.

## Producer choice and preliminary cost rationale

Fix the existing factors F=LU, E=A-F and nonnegative comparison operator
G=C(U)^-1 C(L)^-1. The only selected producer starts with p=1 and performs exactly
8 approximate binary64 passes

    p_next = G(1 + |E|p).

If the nonnegative operator H=G|E| has spectral radius below one, its fixed point
is (I-H)^-1 G1. That motivates the iteration, but does not establish that eight
steps work, that the p=1 start is monotone, or that original A has M-matrix signs.
No such facts enter acceptance. This narrow experiment intentionally tests a
bounded attempt before any universal convergence argument. No adaptive pass
search, oracle solution, expected output, auxiliary full-size system, dense E/G,
opaque factorization, original element metadata or fallback is used.

Each pass recomputes E a row at a time from every A entry and logical LU product,
forms the weighted absolute row sum, adds one and applies two triangular
recurrences. Space is O(F+pattern+n+largest residual row); recomputation trades
space for eight full product traversals. Order<=128, degree<=128, exactly 8 passes,
512MiB address space, 20 CPU seconds, outer 30-second timeout, one BLAS thread,
and the shared Meter's 100,000-slot/1,000,000-kernel defaults bound this synthetic
experiment. Every attempt shares its Meter with factor production and verification.
The producer fails closed on nonpositive/nonfinite/out-of-scale output. It may
emit positive weights that the verifier subsequently refuses.

Preliminary independent resource review identified the original-size obstruction
before the synthetic run: even an optimistic fused-contribution lower bound for
these eight passes exceeds 73M across connected KA/KB factors. The fixture is
therefore source-only method evidence, not a preliminary real qualification.

## Verification and binding

Actual weight values, context, original canonical binary64 CSR bytes and complete
factor witness digest are bound. The factor verifier is reused. Weights require
an exact list of n built-in finite floats in [2^-400,2^400]; zero, negatives,
subnormals and extreme scales are explicitly refused, not clipped/normalized.
Moderate power-of-two rescalings are tested. A claimed origin is descriptive and
never a proof. Digests are construction bindings, not signatures or admission.

For exact positive p, the verifier independently streams outward
r_i >= sum_j |(A-LU)_ij|p_j, then computes z>=Gr and y>=G1. It verifies
q=max_i z_i/p_i <1 and k=max_i y_i/p_i with outward division. It returns

    ||A^-1||inf <= max(p)*k/down(1-q).

All original coefficient cancellation precedes the absolute residual enclosure;
fill outside the factor/original sparsity pattern is included. Existing nextafter
primitives enclose gradual underflow, with an explicit smallest-subnormal product
regression. Nonfinite interval endpoints/reciprocal overflow refuse. Approximate
producer arithmetic is never reused as a proof residual.

For h=F^-1 B from signed outward solves, each Schur correction uses

    max(p)*q/down(1-q)*max_i magnitude(h_i)/p_i.

The interval solve width remains in every B^T h product. The small nonsymmetric
Schur proof and global block inverse bound remain independently verified; the
existing disjoint-terminal gate stays in place. Returned certificates bind each
factor and weight digest plus full A/B/D/context inputs. No cached certificate is
accepted. The optional direct G(1+|E|p)<=p refinement is **not implemented** and
makes no acceptance claim.

## Allocation and arithmetic correction

Previously `verify()` lowered its entry count while its residual row dictionary
was still live; the last row survived into comparison work. `residual_rows()` now
deletes both the insertion closure and dictionary before lowering the count.
A weak-reference and caller-frame regression observes actual destruction for all
144 rows of the 8-pass 16-node producer plus verifier. One scalar interval may
survive under the explicit vector/scratch reservation. This fixes the toy; it
neither proves a production cap breach nor rewrites historical results.

The old arithmetic convention is retained: individual producer scalar arithmetic
and interval primitive invocations, with multiplication and subtraction separately
charged. The historical tiny Schur midpoint omitted its two products plus add;
these are now charged as 3*m*m in `schur_inverse_production`, documented as a toy
accounting correction. Historical recorded values remain historical. Absolute
value/max, comparisons, hashing, validation/serialization and allocation are not
floating kernel charges; they remain bounded runtime/storage operations.

Phases are cumulative: `production`, `weight_production_residual`,
`weight_production_rhs`, `weight_production_comparison`, `weighted_residual`,
comparison recurrences/scaling, `neumann`, coupling norms, signed solves, Schur
construction/correction, tiny inverse production/verification and global bound.
Dropped factor products and failed/capped work remain charged. Auxiliary system
construction is zero. Test-only oracle packet preparation has its own explicitly
reported cumulative meter and combined kernel total; it is not free candidate
work or an input to the producer. Exact reference calculations and physical
resolution calls are explicitly outside this certificate-kernel meter.

Slot reservation includes pattern, factors, residual scratch, 16n weighted
vector/index allowances and 12m² small Schur allowance, with prior board allowances
retained conservatively across the second board. This is not a Python-byte proof.
Per-case tracemalloc peaks cover the certificate invocation; process RSS high-water
includes imports, fixtures and exact oracles. Input arrays, containers, serialization
and oracle allocations also remain under the independent 512MiB address-space cap.
No claim that a small factor count fits original worker byte memory is made.

## Results

Complete per-case producer outcomes/refusals, phase/total work, live-slot peaks,
measured traced bytes/wall time/RSS, inverse/field bounds, coupled acceptance,
actual synthetic screen disposition and available independent references are in
[weighted-results.json](fixture/weighted-results.json). Oracle-weighted controls
are labeled `ORACLE_ONLY`; their weights come only from tiny Fraction inversion.
Larger grids have a connected-grounded-graph uniqueness reference, not a dense
exact inverse. Board-only cases have no invented coupled/physical screen.

| Candidate-weighted case | Result | Inverse upper or q | Kernel charges | Peak slots |
| --- | --- | ---: | ---: | ---: |
| Rooted tree 4x4, ground1 | REFUSED | q=1.0174973683 | 2,345 | 323 |
| Rooted tree 8x8, ground1 | REFUSED | q=1.0176145352 | 10,073 | 1,283 |
| Held-out rooted tree 9x9, ground1 | REFUSED | q=1.0169453662 | 12,840 | 1,623 |
| Rooted tree 4x4, ground2^-30 | REFUSED | q=1.0302093596 | 2,345 | 323 |
| Rooted tree 8x8, ground2^-30 | REFUSED | q=1.0177227482 | 10,073 | 1,283 |
| Retained incomplete grid4, ground1 | CERTIFIED | inverse<=51.5544447 | 4,757 | 391 |
| Retained incomplete grid8, ground2^-40 | REFUSED | q=1.0171011427 | 22,106 | 1,607 |
| Grounded KA + floating KB, independent stamp rounding | CERTIFIED | inverse<=31.4506053 | 658 | 130 |
| Same coupled case, weak ground2^-30 | CERTIFIED / INCONCLUSIVE screen | inverse<=1.895454e10 | 658 | 130 |
| Nonsymmetric coupled stored A | CERTIFIED | inverse<=28.0286799 | 658 | 130 |
| Mixed-sign coupled A | CERTIFIED | inverse<=19.0822664 | 658 | 130 |
| Diagonal factors: both boards pass | Schur REFUSED | Schur q=1.149421 | 438 | 122 |
| Disconnected wire | Schur REFUSED | Schur q=4.061918 | 648 | 130 |

The independent reviewer computes exact q=1.0174973682921369 for the actual
produced tree4 weights (maximizing row10). Thus the refusal is a real contraction
failure, not interval rounding pessimism. On the same tree4, the old unweighted
bound is989.3333 and the separately supplied exact-oracle control is68.3655.
The new producer did not reproduce the oracle's benefit. Its incomplete-grid4
success improves the unweighted74.6873 to51.5544, but does not rescue the rejected
original-size recipe.

The coupled strong case's field error is <=3.145061e-7 for the synthetic perturbed
single-RHS solution; exact inverse norm is about12.5241. Its actual resolution
screen is SUPPORTED for the explicitly synthetic target=copper functional. Weak
grounding yields field error about38412 and INCONCLUSIVE through the real screen
because the energy interval includes zero. Neither is a real U7105.4/TP990026
Stage C result. Tests retain whole distributed termination energy and held
reaction functionals, including non-dyadic independent coefficient rounding.

Coordinator observed peak process RSS69,368KiB; maximum traced candidate invocation
57,366 bytes and wall0.1471s. These are bounded fixture observations, not original
memory/time predictions. Exact references are tiny independent checks, not part
of a proposed weight strategy.

## Reviewed cost decision and next local action

Let Eoff be strict-factor off-diagonals and Wprod the logical LU product count.
For each connected factor pattern Eoff>=n-1 and Wprod>=2n-1. Eight passes alone
cost at least8*(2Wprod+2Eoff+n)>=56n-32 under the actual kernel meter. Across
nKA+nKB=3,055,115 this is171,086,376, before weighted reductions, producer RHS,
verification, factor production and the coupled proof. Even mapping each logical
LU product and each off-diagonal comparison contribution to one hypothetical
production update gives8*(Wprod+Eoff), totaling73,322,728. The separate resource
review accepts these as rejection lower bounds, **not** an approved replacement
production counter or fit claim. No vectorization discount is used.

This recipe is rejected without needing any unknown original-data property.
A characterization probe cannot reverse this count or the exact fixture failure,
so no characterization admission path or full qualification is warranted now.
Do not spend a diagnostic, increase passes as another blind guess, relabel a
unit-weight fallback as new progress, or restart the alternative-factor survey.

The next justified local method change is to remove the repeated full residual
traversals from weight production: first derive a fixed, bounded structured
weight construction using only stored coefficients and a predeclared sparse
traversal, and symbolically account it together with exhaustive verification and
the Schur lift. Use the retained tree4 failure vector/row10 as its acceptance
counterexample and tree9 as held-out; a proof of useful local margins must explain
how it avoids this failed Picard transient. Keep the existing independent weighted
verifier and require an explicit production-update mapping review before a fit
claim. This is a local source-development decision, not an eligible real request
or a claim that such a construction has already been found.

## Checks and unchanged limits

Eight weighted tests and all18 legacy tests PASS. Separate reviewer exact checks
cover200 board inverse bounds,400 Schur entries and100 joined inverse bounds with
nonsymmetric mixed-sign coefficients and nonuniform weights. See
[mathematics review](weighted-math-review.md),
[resource review](weighted-resource-review.md), and
[independent oracle results](independent-weighted-results.json).
Pre/post circuit contract checks PASS: manual inventory68 lines, zero declared
placements, schematic/placement binding not performed; pin-asset check performed.

Native/aggregate regeneration, original archive decoding, full original numerical
qualification and production are NOT RUN: this scoped synthetic increment neither
changes their source nor authorizes native/canonical generation. The production
executor, original matrices/solver/refinement/RHS/held sources/barrel intervals,
tolerances/normalization and admission contract are unchanged. Preserve180 seconds,
1216MiB worker,2GiB aggregate with reserve, zero operation swap,64MiB output,
16M input/4M live entries/20M updates, single-use identities and cleanup.
KEEP_K1402_INCUMBENT; PR260 draft/unmerged; issue253 open. No merge, deployment,
fabrication, purchases, energization or original hardware acceptance.
