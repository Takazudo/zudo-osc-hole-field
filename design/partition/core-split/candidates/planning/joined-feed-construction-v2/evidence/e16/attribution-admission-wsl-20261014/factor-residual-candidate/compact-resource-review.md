# Independent resource review: adaptive exact dyadic arithmetic

Reviewer `/root/resource_review`, 2026-10-15 JST. Source-only review and
independent bounded fixtures; no original numerical input, diagnostic, baseline,
admission or global host changes. Earlier fixed-exponent, row-only, weighted
producer and cost-obstruction results are retained.

**Decision:** accept the bounded compact exact-arithmetic increment. It reduces
actual significand widths and the declared width-aware bit-work envelope, while
increasing the number of explicit integer kernels. It does not establish
production eligibility, a20M-update fit, memory fit or original applicability.
The full scalar path now stays compact; the fixed representation remains a
separate control rather than being silently rewritten into the new result.

## Reviewed identities and execution

- `fixture/prototype.py`: `79b8fa4b57b2d38a3780496b9aeac5ba0aa7a1c696b770a2ceb43d7bad96fc44`
- `fixture/test_compact.py`: `52664ce766ba43d3027e0202867a7fe854f500a5a85dc71cdc7a152e4b1e12d9`

Independently executed the compact runner with the established numerical venv,
`python -B`, one thread and outer30s timeout; four tests PASS (0.293s).
Inherited limits remain order128, oracle order16,512MiB address-space and20CPU
seconds. The seeded300-value binary64 control covers exact decode/half-sum,
comparison and conversion against Fraction references, including subnormal,
full exponent span, negative/cancelled and malformed cases. Virtual coupled
strong/weak/nonsymmetric fixtures retain identical certified bounds between
representations and use the actual physical resolution functions. No original
matrix was sampled to obtain convenient exponent distributions.

## Accounting findings addressed

The initial row-only version recomputed absolute values and bit lengths without
including all of that repeated work in its declared count. Review requested
cached magnitude/width values and explicit normalization, alignment and
preallocation checks. The final code checks normalized exponent range, validates
canonical tuples and zero shortcuts, and checks aligned integer widths before
allocating shifts. Its range remains2176 bits with exponent bounds; compact
representation is not permission for unbounded exact arithmetic.

The scalar follow-up originally undercounted sign extraction/subtraction,
comparison branches and sign multiplication. Final charges include those
operations, fixed-representation comparison subtraction and the canonical-value
check. Two arbitrary-sign integers with equal leading position are aligned only
after a width bound; a difference in leading position can avoid that allocation.
No wide alignment is discounted merely because the final sum cancels or later
normalization shortens it. Coefficient conversion and ldexp remain visible in
the floating ledger, and exact comparisons independently establish floor/upper
conversion validity.

The old field `integer_operations` continues to mean declared bounded kernels,
not every Python instruction. Phase totals, kernel/width breakdown, bit-work
envelope, float primitive calls and access counters remain distinct. Index,
container and meter-bookkeeping work remains under actual runtime/memory limits.
The fixed200,000-unit synthetic cap is not increased. Earlier fixed-mode reports
retain their older hashes/counts; explicit comparison accounting adds units in
the present fixed control and must not retroactively change historical results.

## Width savings and additional kernel work, both visible

The independently run row-only intermediate, before compact root/edge dispatch,
showed order81 complete fixed control26,459 integer units and64,653,258,212
bit-envelope units, versus row-only compact111,627 and16,464,303,018. Both used
328 floating primitive calls. This intermediate already demonstrated that fewer
wide operations need not mean fewer declared kernels. Final complete compact
results supersede it as the implemented method, not as historical measurement.

Final independently executed comparison:

| Case | Float primitive calls | Declared integer units | Logical bit-work envelope |
| --- | ---: | ---: | ---: |
| Order81 fixed complete control | 328 | 27108 | 67726257636 |
| Order81 complete compact | 328 | 147440 | 115135235 |
| Joined strong fixed control | 53 | 1563 | 3890241327 |
| Joined strong complete compact | 53 | 8535 | 15527959 |
| Joined nonsymmetric complete compact | 53 | 8535 | 15776522 |
| Joined weak complete compact | 53 | 8535 | 15060343 |

For the isolated order81 row pass, fixed uses9693 units/24,137,959,689 envelope,
compact54329/43,484,546. The complete compact strong invocation peaks at23,099
traced bytes versus8149 in the fixed control; nonsymmetric compact peaks at23,654.
Whole process high-water reaches68,888KiB including imported libraries and
fixture/oracle work. These are bounded measurements, not native instruction
counts, full allocator peaks or extrapolated original execution times.

Tree coefficients, root/deficit comparisons and floor/upper conversion now use
compact pairs throughout via `ExactRowArithmetic`; a compatibility `as_fixed`
row mode remains for independent equality controls. Final margins no longer need
to become1075-shifted large integers in the compact certificate path. Big integers
remain row-local plus a bounded number of scalar root/deficit values; there is
no n-length arbitrary-precision vector. Packed tree buffers, virtual CSR/B inputs
and row/hash access retain the previously reviewed lifetime contract.

Review found inherited generic zero auxiliary fields could obscure actual tree
construction. Final direct results explicitly report tree order/edges, zero
auxiliary solve order, tree-construction floating and integer phase totals, and
a scope explanation for the legacy fields. The strong compact case reports
12 floating construction calls and4227 integer construction units; the fixed
control reports12 and780. Zero auxiliary solve order no longer implies free
tree construction.

## Literal count obstruction versus actual production semantics

A useful explicit lower bound remains despite width savings. Each compact
binary64 decode charges at least six declared units before normalization
(fixed-size decode plus bit extraction). For m stored matrix coefficients and n
diagonal positions, one exact margin pass decodes2m-n values, because each
strict coefficient also reads its actual reverse. Producer plus verifier use
at least4m-2n decodes. Thus declared integer units are at least24m-12n before
all normalization, sums, tree construction and scalar comparisons.

Using retained mA=7,818,329, minimum nonsingular mB=1,541,278, and free order
N=3,055,115 gives187,969,188 declared units even without terminal contributions.
This rejects direct literal scaling under an envelope that charges each declared
kernel at least one shared update. It does **not** prove impossibility under the
existing production update semantics: the old LDL counter charges scalar
Schur destination updates, not bit extraction/hash/index kernels. A zero-pruned
representation would also require its own charged construction/evidence; it is
not inferred from the retained stored count.

The source-based policy decision is therefore precise: a newly declared scalar
contribution mapping is defensible for local implementation and technical
review, rather than forbidden by the literal old counter. It must not be called
already approved or used to claim fit from these measurements.

A proposed correspondence may charge one scalar coefficient-accumulator
recurrence per actual contribution, weighted by
ceil(maximum actual aligned operand/result arithmetic width/64), while retaining
all primitive and exact-kernel/bit/access ledgers. Use the pre-normalized and
pre-cancellation widths, not the final short mantissa. Separately enumerate
coefficient conversion, normalization/rescaling, validation and search work
under the actual time/byte bounds. An outward path reciprocal-plus-accumulation
can be one explicit bounded contribution, analogous to the old compound
multiply/divide/subtract Schur update; it cannot turn a row, library solve or
factorization into one unit. Name the new ledger separately, e.g.
`proposed_scalar_contributions`, and preserve all previous counters. This review
accepts that as a proposal to implement and inspect, **not a production fit
mapping or execution authorization**.

## Next concrete algorithm and remaining eligibility

A verifier-owned single original-row pass can select already checked negative
edges into a spanning forest using union-find while establishing all exact row
margins. Rooting that owned checked tree and computing paths need not repeat an
untrusted producer's full margin scan or re-read every selected original edge.
This is a genuine algorithm change, not free preprocessing. Every original row
contribution must remain in the verifier; process each undirected candidate
once for forest selection while verifying both directed row contributions.
Rejected/skipped edges and union-find find/compression/rank operations remain
counted in explicit work ledgers. Ownership/input binding must prevent mutation
of checked coefficients before using the tree.

The forest needs additional typed endpoint/conductance and adjacency-conversion
storage before it becomes the final parent/order tree. Those overlaps must be
measured and prebounded; the existing25n final payload is not the forest peak.
No retained original sign or conservation assumption can replace exact checks.
Whether a claimed nnz+N contribution design actually holds is a question for
review of those exact loops, including wide alignments, failed work and both
boards; it is not established by this report.

The complete original execution representation still needs the raw distributed
stamp constructor prebound, CSR/CSC overlap, retained B/Y/selected-solve state,
unchanged SuperLU/refinement and Assembly/physical accounting schedule detailed
in the prior virtual-layout resource review. Current literal repeated-pass
code is not an eligible original run, and no original property is needed to
reach that decision. Implement/review the single-pass forest and its explicit
contribution ledger locally first. No original-data characterization, full
qualification, new baseline, consumed-request reuse or cap increase is justified
at this checkpoint.

A subsequent proposed implementation can avoid adjacency duplication by keeping
an oriented forest: union by size, reroot the smaller component's parent path
before attaching its checked edge, and retain the larger component's rooted
orientation. Each vertex can be in the smaller component only O(log n) times,
but every parent rewrite/find operation must still be recorded and bounded.
The proposed20n forest payload (parent4+edge8+DSU4+size4) and25n post-release
path payload (parent4+edge8+path8+state1+stack4) are plausible design figures,
not yet verified allocation lifetimes. Review the actual reroot conductance
transfer, DSU release and stack/memoized path loops before accepting them.
