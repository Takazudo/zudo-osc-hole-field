# Independent follow-up: cheap weights do not by themselves establish fit

Reviewer: separate `/root/resource_review` agent, 2026-10-15 JST.
Base: `67d120079b8a3ffaf0e915b8ffeebfea7611fc7e`.
Source-only review, no original arrays, numerical probe, diagnostic or baseline.
This is additional evidence; earlier positive/negative fixtures and resource
reviews remain intact. No prototype or production source was changed.

Reviewed source SHA256:

- `attribution_uniqueness.py`: `828ec3e48ca7e05b094c32b9d8927bf10439623be80300a903d0ad7c8613da8f`
- `fixture/prototype.py`: `78c5e38f29a065010bdb42f7ffd042e666c7465b60166d700e0c0e180944fe33`

**Decision:** the current connected-factor weighted verifier cannot fit 20M
under its existing primitive meter, even with free weights. A one-pass producer
alone cannot fix that obstruction. Under a proposed uniform contribution
convention, a one-counted-operation-per-node producer also exceeds 20M with the
minimal useful signed lift. The literal exhaustive stored-row version is already
over that proposed bound with free weights. These statements have distinct
hypotheses below; they do not prove all weighted-certificate architectures
impossible under the actual production update convention.

## Actual production semantics, not an invented FLOP budget

`Work.check(entries, updates)` accumulates whatever its caller supplies. In
`attribution_uniqueness._eliminate`, the only increment is in the nested
adjacent-destination loop, immediately before

    new = sub(old, div_positive(mul(row[i], row[j]), pivot))

`_eliminate_frontier` does the same for each target entry. This compound interval
rank-one destination update is one production update despite several primitive
operations. Neither implementation increments for factor division, forward and
backward comparison multiply-add sweeps, norm reductions, final inverse-bound
arithmetic, input conversion, validation or hashing. Those still consume memory
and wall/CPU time. The source does not define a generic FLOP counter or an
already-qualified mapping for new certificate methods.

A defensible elementary correspondence is one scalar residual accumulation
`E_ij <- E_ij - L_ik U_kj` to one destination contribution. A scalar incomplete
factor update has the same correspondence, including attempted products that
are discarded. One cannot use one charge for an entire row, triangular solve,
vectorized expression or library factorization.

Charging every weighted row and triangular multiply-add contribution one each
is a conservative, explicit candidate convention, used for bounds below. It is
**not** literally the existing production convention: the production norm
sweeps are uncharged. No blanket remapping or fit claim is approved by this
review. A future production request must name each loop, preserve the finer
primitive counts, state counted and uncounted work explicitly, and receive
review of the complete resource envelope. Calling all candidate triangular
work free merely because old LDL norm sweeps were uncharged would not establish
runtime or memory fit, nor authorize a new method.

## Exact primitive lower bound for the existing weighted verifier

For board order n, let E be the number of stored strict-L and strict-U entries,
F=n+E, W the exhaustive LU-product count, and S the number of dictionary entries
visited over the streamed residual rows. For connected factor union graphs,
E >= n-1 and W >= F >= 2n-1. For a successfully certifiable nonsingular board,
S >= n. All quantities are per board; implicit unit L is included in W.

The implementation charges at least:

| Phase | Primitive lower count |
| --- | ---: |
| Exhaustive LU residual multiplication/subtraction | 2W |
| Weight multiplication and residual row accumulation | 2S |
| Two comparison applications | 4E + 2n |
| Two weighted ratio scans | 2n |
| Total verifier before final scalar correction | 2W + 2S + 4E + 4n >= 14n-6 |

This excludes all factor and weight production. With
N=nKA+nKB=1,513,837+1,541,278=3,055,115, the shared verifier lower bound is
**14N-12 = 42,771,598**.

For each terminal column evaluated, the signed factor solve adds 2E+n primitive
charges, and its weighted norm adds n divisions. Thus one useful local terminal
column per board gives at least **18N-16 = 54,992,054**. The actual implementation
evaluates both global columns on each board, including a zero column, giving at
least **22N-20 = 67,212,510**. These omit coupling products, tiny Schur production
and verification, corrections, factor generation and every weight operation.
They are lower bounds, not measured extrapolations or production-counter claims.

The conclusion is decisive for this exact implementation/meter: substituting
free or one-pass weights cannot make it fit the original arithmetic limit.
Toy vector/pattern reserves likewise are not a million-node storage design.
Changing their definitions is not a resource improvement.

## Conditional uniform contribution model

Suppose one conservatively counts every scalar multiply-accumulate contribution
once, including LU residual, weighted row reduction, each comparison sweep and
signed solve. Even granting all diagonal divisions, scaling scans, scalar
corrections and producer work free, a verifier plus one local signed lift needs

    W + S + 3E >= 6n-4.

Both boards therefore need at least **6N-8 = 18,330,682**, leaving only
**1,669,318** before all factor/weight production, coupling and Schur work.
A structured weight producer that costs just one counted operation per node
adds N, yielding **7N-8 = 21,385,797**, already beyond 20M. The conclusion requires
that operation actually be in this declared contribution convention; copying
predefined constants or a different bound representation cannot silently be
assigned that cost or assumed to be free.

The retained KA metadata report 7,818,329 stored coefficients. The literal
exhaustive-row implementation retains every original stored position before
LU cancellation; a certifiable KB needs at least 1,541,278 stored positions.
For that literal stored-row algorithm, S_KA+S_KB >= 9,359,607, hence

    Wsum + Ssum + 3Esum >= 5N-8 + 9,359,607 = 24,635,174.

This rejects even free weights in that version of the uniform model. Explicit
zero pruning is a distinct representation change: the retained stored count
does not prove its post-pruning mathematical support size. The current toy
rejects explicit-zero A inputs rather than implementing such a production
pruner. No new original-data read was made to bridge that gap. Source-level
pruning/preflight must itself be bounded and reviewed, and pruning cannot
rescue the existing primitive-meter lower bound.

If both global columns are retained instead of skipping the known zero column,
the uniform-model signed-lift cost adds another E per board. Even using S>=n
rather than the retained KA count then gives **7N-10 = 21,385,795**, before any
producer. Skipping zero columns is a concrete local optimization but does not
by itself establish the complete-operation budget.

## Actionable next local direction

Do not spend a diagnostic on a structured-weight substitution into the current
verifier unchanged. The arithmetic obstruction is already local; no original
property is essential to this decision. A better synthetic weight may be useful
mathematical evidence but cannot be represented as an eligible full-data method.

The next method design must jointly specify weight production, residual proof,
comparison applications and useful terminal columns, rather than optimizing
only the producer. Before further original eligibility work it needs a
loop-level budget for both boards, an explicit reviewed production mapping,
and a packed byte/lifetime budget including original inputs, retained factor
witnesses, patterns, vectors, scratch and complete physical accounting. A
candidate that changes residual proof or reduces comparison passes needs its
own theorem and independent review; no sign, conservation or element-metadata
assumption can replace the original stored coefficients. Restricting to known
nonzero terminal columns is justified by actual B coefficients and should be
included in any such local design.

This review does not reopen the rejected full-factor/retained-Y recipes, propose
literature search, or authorize a different baseline. All live-entry, input,
update, 180-second guard-entry, 1216 MiB worker, 2 GiB aggregate, zero-swap and
64 MiB output limits remain unchanged. Qualification and production remain
NOT RUN / NOT ADMITTED. No fit claim has been made under a revised convention.

## Narrow next architecture assessment: direct weighted row dominance

A source-local alternative to assess is an outward stored-operator check of

    d_i = |a_ii| p_i - sum_(j != i) |a_ij| p_j > 0, p_i > 0.

Strict row dominance of A diag(p) implies nonsingularity and the candidate
bound max(p)/min(d_i). This is a proposed theorem-to-code direction requiring
mathematics review, not a newly accepted implementation. It requires no assumed
M-matrix signs: the verifier must use absolute values of the actual stored
coefficients, outward arithmetic and actual positive margins. Approximate row
sums, topology or a connected grounding story cannot replace those margins.

A straightforward primitive implementation uses one product and subtraction
for each diagonal and one product/add for each strict stored coefficient:
2 nnz(A) primitive charges before final division, weight production and coupled
work. This removes LU residual expansion and the two comparison sweeps. The
retained KA stored count plus minimal nonsingular KB count gives a free-weight
row-check lower bound 2(7,818,329+1,541,278)=18,719,214, which alone is below20M.
This does not establish fit: actual KB nnz is unknown in the retained metadata,
and coupling/Schur, production and physical operations remain. The current tree
producer costs nnz(A)+3n-2 primitive charges per board and therefore exceeds20M
with this row verifier even at that optimistic lower input size.

Under a hypothetical off-diagonal contribution model the row accumulation
alone costs nnz(A)-n contributions, while diagonal operations, construction,
binding and complete coupled work still need explicit treatment. The different
number is a change of accounting model, not a measured speedup. This architecture
is worth a bounded source-only mathematical/fixture assessment because it
removes concrete loops; it is not eligible for a diagnostic based on these
incomplete bounds. No original-data characterization is needed before that
local proof, useful-weight evidence and complete-operation resource design.

## Stored-tree producer implementation follow-up

Independently inspected and executed the separate bounded stored-tree producer
added after the base revision above. Reviewed identities:

- `fixture/prototype.py`: `425dc9ff6d85d1d423efa7251697c193d511c0c999e4f711ff17b105b5d22de2`
- `fixture/test_structured.py`: `0dc3bb5e38b15f7a9aded5fb367faf45e73536caf9b8a2714802445abdcc1c88`

Three structured tests PASS (0.099s) under the established outer30s,
512MiB address-space,20CPU-second, one-thread fixture limits. The order3 path
control emits [3,5,6] and certifies (63 cumulative primitive charges); the
rooted4/8/9 grids emit weights but refuse q=1.3602693602693625,
1.4481620643724804,1.4550581850536153, respectively. Their complete factor,
producer and verifier counts are439/1879/2394. The held-out9 grid peaks at2104
reserved slots and49,925 traced invocation bytes. Process high-water reaches
68,164KiB including imports/control fixtures, not an isolated allocation peak.

The auxiliary is explicitly an order-n tree, not a hidden original-system
solve. Approximate ground selection scans all stored coefficients, symmetry
checks use bounded reverse CSR binary searches, subtree mass requires n-1
additions, and integration requires one root division and n-1 divide/add pairs.
Its floating count is exactly nnz(A)+3n-2 when completed. Ground row additions,
subtree work and integration remain separate phases. Integer BFS/index scans
and binary searches are real runtime work outside the floating count; no scan
is represented as a single scalar update.

Review found two `order[1:]` list slices that would introduce another order-n
index list beyond the explicitly named six auxiliary arrays. They were removed:
reverse/forward iterators skip the root without slicing. Grounds, parent,
conductance, BFS order, subtree mass and output are pre-reserved; scratch arrays
are deleted before reducing the reservation, with output retained in the
packet/base reserve. Failure reporting now distinguishes requested auxiliary
order from successfully emitted tree order and preserves producer failure
reason and all consumed arithmetic. A partial failed tree is covered by the
peak reserve even when no complete auxiliary witness is emitted.

No coupled implementation is necessary to establish rejection of this exact
board-weight strategy: retained positive controls demonstrate implementation,
while the retained target grids fail independently and the unchanged verifier
has the cost obstruction proved above. The new evidence motivates a change of
certificate architecture, not a larger diagnostic or additional baseline.
