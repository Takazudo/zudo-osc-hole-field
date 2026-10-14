# Separate resource review: stored-coefficient tree coercivity

Reviewer: `/root/resource_review`, 2026-10-15 JST. Source-only inspection and
independent bounded synthetic execution; no original-data decode, admission,
diagnostic, baseline or external action. This review follows the concrete
weighted-producer and unchanged-verifier obstructions retained in
`structured-weight-cost-review.md`. Those negative results remain valid.

**Decision:** accept this bounded local architecture experiment and its honest
resource scope. No original-data port, scalar-count mapping, complete resource
qualification or production fit is approved. Small floating update totals do
not make the separate exact-integer work free. The new method removes specific
LU residual/comparison loops and provides useful synthetic evidence; it does
not establish the original operator's required properties or complete cost.

## Identities, ownership and independent execution

Reviewed SHA256:

- `fixture/prototype.py`: `762257f82db7d6b0abfdb545af2c6408687ec66bb56f114d6d197d7db50fba6d`
- `fixture/test_coercivity.py`: `cf4f91819066fd9a36ec79c345ac4c585d5e51c6b458d5155a36bfcf6905b608`

At the coordinator's request this reviewer authored the exact-decode/accounting
helper correction and the final integer-to-float conversion charges. This is
disclosed rather than represented as independent review of my own changes.
The separate mathematics reviewer was asked to inspect those helpers; the
resource execution and architecture assessment here are separate from the
coordinator's fixture run.

Independently executed `test_coercivity.py` using the established numerical
venv, `python -B`, one thread and outer30s timeout. All seven tests PASS (0.574s)
under the runner's512MiB address-space and20CPU-second limits. Matrix order
remains<=128 and dense exact reference order<=16. Additional independent helper
checks compared twelve fixed binary64 values against exact Fraction-scaled
integers (including both signs of zero, minimum subnormal/normal and maximum
finite); three half-sums including half a subnormal and maximum cancellation;
and explicit overflow refusal/accounting identities. These checks passed.

Representative final-run measurements:

| Case | Result/inverse upper | Floating kernel charges | Declared integer units | Reserved-slot peak | Traced invocation peak bytes |
| --- | --- | ---: | ---: | ---: | ---: |
| Rooted4, trace | CERTIFIED /256.00000000000074 | 84 | 4668 | 208 | 6697 |
| Rooted4, path refinement | CERTIFIED /61.25357132445439 | 168 | 4684 | 208 | 6664 |
| Rooted8, path refinement | CERTIFIED /461.1290491825498 | 648 | 20812 | 784 | 10871 |
| Held-out9, path refinement | CERTIFIED /650.8893915251704 | 818 | 26624 | 988 | 12141 |
| Whole joined interval fixture | CERTIFIED /23.101526258322217 | 81 | 1514 | 116 | 8241 |
| Nonsymmetric joined interval fixture | CERTIFIED /22.49836077561593 | 81 | 1514 | 116 | 7753 |
| Weak-ground joined interval fixture | CERTIFIED /6442503572.111362 | 79 | 1514 | 116 | 7753 |
| Nonadjacent distributed stamp | REFUSED | 22 | 1134 | 64 | 5926 |

Process high-water RSS reached67,768KiB including imports and reference work.
Traced bytes measure only the invocation, omit some native allocation and
exclude caller input construction/independent oracles/physical evaluation.
The separate process address-space cap covers the whole runner. These are
bounded fixture measurements, not original-system forecasts. The weak-ground
case still has inconclusive physical screening; a finite uniqueness bound does
not change that disposition.

## Changed architecture and lifetimes

The producer scans actual CSR coefficients, uses exact row-local dyadic sums
of the stored symmetric part, selects a root and a deterministic negative-edge
BFS tree, and emits only parent, conductance and order vectors. Structural
symmetry is explicitly required: one-sided entries refuse, rather than being
silently omitted or supplied. Coefficient symmetry is not assumed; stored
reverse values may differ. The original nonsymmetric operator remains the
subject of the inverse bound.

The independent verifier rescans original coefficients and checks actual tree
edges, root ground and exact diagonal deficit. It computes a tree inverse trace
by subtree counts; there is no original-system factorization or solve, dense
S, global inverse or retained global residual. The optional path-Cauchy bound
adds one path vector, subtree-square sums and a square-root trial whose outward
square is independently checked, at most four attempts. The final code also
requires a finite nonnegative root trial before squaring; adversarial negative,
NaN, infinite and underestimated trial tests preserve the trace fallback. Failed refinement work
remains charged; the previously established trace certificate can survive an
arithmetic refinement refusal, but resource-cap failures propagate.

The interval wrapper binds the actual finite sparse coefficient replacements
and establishes a whole-operator infinity-norm perturbation bound. It does not
claim that the midpoint alone certifies the original interval block. Both
boards and their coupling are contained in the same tiny CSR input; there are
no separate board counters or free Schur solves.

The producer reserves8n+16 slots and the verifier12n+16. Packet arrays occupy3n;
seen/subtree/path vectors and temporary permutation-validation arrays fit the
explicit vector reserve. Only a bounded number of<=2176-bit integers are live
per row; there is no order-n bigint array. Producer best-margin scratch is
released after root selection; verifier margin scratch is released before tree
work. Path scratch is explicitly deleted after refinement. The interval wrapper
adds a row vector and bounded replacement/key scratch under14n+16+4k slots.
These are logical reserves, not Python-byte proofs; tuple/list/dictionary,
hashing and source CSR storage remain covered by the actual worker bounds.
A future original-size layout still needs a separate packed-byte overlap proof.

## Exact arithmetic is visible, bounded and not relabeled scalar work

The exponent unit2^-1075 represents every binary64 value and exact average of
two binary64 values. The helper decodes fixed eight-byte IEEE binary64 directly.
Its finite input bound gives at most2099 significant integer bits before shift;
row sums and differences are checked against2176 bits. The order128 restriction
bounds accumulation width independently of data values. Every large shift has
an a priori finite-width bound; it cannot allocate an attacker-selected huge
integer before validation.

The initial helper-call counter was ambiguous and omitted coefficient conversion
cost. The corrected meter explicitly records bounded arithmetic/shift/width/
comparison/decode kernel units by kind and operand-width bound, cumulative
phase totals, and a width-aware logical bit-work envelope of sum(count*bits^2).
The legacy field name `integer_operations` is a compatibility name for these
declared kernel units, **not** full Python operations, FLOPs or CPU instructions.
The fixed200,000 declared-unit fixture cap is separate from Work. The envelope
is not a production scalar mapping or a claim about native execution speed.
For example the held-out9 refined fixture has26,624 units and a logical envelope
64,653,284,324; the joined interval fixture has1514 and3,620,322,422. Both metrics
remain visible. No wide-integer helper is described as one production scalar
update.

Numerical int-to-float conversions, coefficient ldexp scaling, outward interval
primitives, square-root trial and nextafter attempts are in the floating kernel
counter. Index decoding, reverse CSR binary searches, boolean schema checks,
container allocation, sorting, JSON and hashing remain real runtime work outside
that arithmetic counter, just as in the retained prototype. Their omission
from floating counts is explicit, not a vectorization or opaque factorization
discount. Root/edge construction and all discarded attempts remain cumulative.

Review corrected two inconsistencies before the final run: coefficient float
conversion/ldexp now consume two floating kernel charges; subsequent exact
bounded integer-to-float trace/refinement conversions are charged consistently.
The bounded integer sqrt/square/comparison/add group is four declared units.
Oversized exact-to-float coefficient conversion refuses explicitly instead of
escaping as an unreported overflow. This changes only the new lane's counts,
not historical weighted results or the numerical bounds.

## Complete original-size decision and next executable step

Two CSR traversals are not a complete cost proof. Producer/verification row
scans each decode original and reverse coefficients, construct exact averages,
accumulate magnitudes and check widths; BFS and tree verification perform more
reverse lookups. Those lookups are O(log degree) index work. Original structural
symmetry, diagonal deficits, acceptable ground/tree coefficients, useful final
bounds and the actual input representation remain unestablished. The original
KA stored count alone is7,818,329: a small number of floating trace updates
cannot hide several exact-integer kernels per stored coefficient per scan.
No approved equivalence to the existing production LDL destination-update
counter follows from this implementation. Even the minimal literal destination
correspondence does not account for wide exact additions, decoding, comparison
and reverse lookup. Treating each as a scalar or omitting them requires an
explicit new kernel/resource contract; neither option has been approved.

The immediate justified local engineering step is a predeclared packed-layout
and loop-level cost design for this exact stored-operator method: enumerate both
original scans and reverse lookups, root/tree construction, verification,
refinement, interval replacement and complete physical accounting; retain a
separate width-aware exact-arithmetic budget; and bound simultaneous CSR,
packet/vector/scratch/output bytes for both boards. Audit each proposed fused
kernel against the existing scalar-update semantics with independent resource
review. Expand bounded synthetic applicability tests against the already known
positive distributed-stamp and one-sided-pattern obstructions before claiming
that original characterization would alter a viable engineering decision.

If the cost design or fixtures reject the method, retain the precise obstruction
and change the local method without a diagnostic. Only after usefulness and a
complete cap-respecting design are established could an essential unknown
original property justify a separately implemented/reviewed bounded
characterization request. This review does not authorize such a request now.
The180-second entry deadline,1216MiB worker,2GiB aggregate including reserve,
zero swap,64MiB output and certificate caps remain unchanged. Qualification and
production remain separate, NOT RUN / NOT ADMITTED requests.

The first concrete deliverable for that next local step is a virtual joined-row
iterator over synthetic board CSR, B and exact terminal interval entries, with
no copied full joined CSR or transpose, plus a packed parent/edge/order vector
layout and an explicit lookup strategy for one-sided/reverse entries. Bind and
verify the same physical stored coefficients and compare every emitted row to
the tiny independent oracle. Then tabulate the exact worst-case integer kernel,
bit-width and float counts of producer and verifier against retained node/nnz
metadata, including source/input storage overlap and required physical work.
This directly resolves the missing execution representation and full work
contract; it is not a new general search or a reason to repeat solved fixtures.
Until that exists, a positive original SDD/deficit characterization result would
still leave no executable cap-qualified candidate. Therefore **no minimal
original-data characterization is justified at this checkpoint**.
