# Independent resource review: sparse factor-residual candidate

Reviewer: `/root/resource_review`, 2026-10-14 UTC / 2026-10-15 JST.
This review inspected source, retained JSON/Markdown metadata and the synthetic
prototype. It did not decode original operator/reduction/mesh archives, run
original numerical work, issue grants, or alter campaign state.

**Decision:** the tiny algebraic experiment is appropriate source-only work.
The original retained-basis residual lift has a demonstrated conditional work
conflict below. The replacement factor-solve lift is not ruled out by dimensions,
but original-data execution remains **NOT ELIGIBLE**: no useful, cap-fitting
production factor pattern or complete combined resource qualification is proved.
This is not permission to execute a generic incomplete factorization or another
ordering trial. No additional diagnostic or baseline is justified by this review.

## Existing accounting and actual reusable artifacts

`attribution_uniqueness.Work` shares one 20M update count across both boards and
the coupled checks. Its update is one scalar interval Schur update, not one FLOP.
The existing norm sweeps, hashes, sparse conversions, permutation analysis,
original residuals and physical accounting do not increment that counter; they
still consume the same wall time and kernel memory. The 4M quota includes live
interval entries and retained certificate factors, including pivot-row overlap.
Read-only original CSR, vector and object storage also consume kernel memory.

`finite_solve.reduce` serializes Y, S, selected reduction fields and scalar LU
statistics, but does not serialize L/U. The current executor only creates an
original KB SuperLU factor transiently for the selected solve, then deletes it.
The retained inventory contains no reusable factor artifact. A new witness must
be produced and verified inside a genuinely admitted operation; historical LU
success is neither a witness nor free preprocessing.

The retained `attribution-reconstruction-wsl-20261014/resource-inventory.json`
and `campaign-wsl-20261014/result-summary/attempt5-final/summary.json` report:

| Quantity | KA | KB |
| --- | ---: | ---: |
| Original node count | 1,515,457 | 1,541,278 |
| Free-node count | 1,513,837 | 1,541,278 |
| Historical nominal-average L+U stored entries | 21,097,522 | 21,002,074 |
| Historical factor seconds | 3.28 | 3.36 |
| Historical complete reduction peak RSS, KiB | 1,625,624 | 1,673,712 |
| Selected reduction compressed bytes | 33,730,898 | 28,517,859 |
| Original operator compressed bytes | 53,422,146 | 54,326,840 |

KA free order and stored nnz 7,818,329 are independently retained in attempt4;
attempt7 records the same order and structural-union graph nnz 7,818,329. KB has
no held nodes under the unchanged source configuration, hence its free order
equals its retained original node count. Historical reduction peaks exceed the
current 1216MiB worker ceiling, but those jobs included different simultaneous
fields: this is a warning, not proof every new minimal producer exceeds memory.

Full historical factor representations exceed 4M by more than fivefold on each
board. Even removing both diagonals leaves 18,069,848 / 17,919,518 stored entries.
Their binary64 values plus int32 indices alone need about 253.2 / 252.0MB before
pointers, copies or interval objects. These byte figures do not rescue the entry
quota. One KA original CSR/CSC with int32 indices requires at least 99,875,300
bytes. A dense joined inverse would require about 74.67TB in binary64.

**Explicit-zero correction:** stored nnz is not necessarily mathematical
nonzero count. Literal original-stored-pattern ILU is over 4M, but the metadata
alone do not prove that a zero-pruned original pattern exceeds 4M. The union
graph count implies at least 3,909,165 directed nonzeros; a stronger 4,666,083
bound requires all original diagonal positions to be nonzero. Neither exact
structural symmetry nor absence of explicit zeros follows merely because stored
nnz and union-graph nnz happen to match. New claims must retain this distinction.

## Work bounds that change the method decision

Let n be board order, E the strict-L plus strict-U entry count, and F=n+E.
With implicit unit L, exhaustive logical LU multiplication has

    Wprod = sum_k (1 + nnz(strict-L column k))*nnz(U row k) >= F.

The proposed two comparison recurrences require at least 2E off-diagonal
contributions. Factor production additionally costs Wgen, counting every
attempted update, including contributions subsequently dropped. Degree/fill
limits must bound Wprod before numerical work: a small total F does not prevent
one high-degree column/row pair from generating quadratically many products.

For a connected union of factor off-diagonal graphs, E>=n-1. Thus the verifier
alone costs at least 4n-3 contributions per board under the candidate's stated
conservative contribution accounting. Across both boards this is 12,220,454.
The initial Schur lift additionally evaluates B-A*Y on both boards. Visiting all
stored KA entries costs 7,818,329 contributions. Any successfully certifiable
nonsingular KB matrix needs at least nKB=1,541,278 stored entries. Therefore:

    12,220,454 + 7,818,329 + 1,541,278 = 21,580,061 > 20,000,000.

This rejects **connected factors plus an exhaustive stored-entry retained-Y
residual lift** before producer work, B contractions or the small Schur proof.
It needs no original KB nnz measurement. Its hypotheses matter: disconnected
factor graphs, a different verified lift, or a genuinely zero-pruned residual
representation are not ruled out by that argument. Explicit-zero pruning must
be charged and cannot be assumed to supply a sufficient reduction.

The coordinator subsequently proposed the same factor candidate with a different
Schur witness: enclose the exact factor solve h=(LU)^-1 B and use
q/(1-q)*||h||inf to bound A^-1 B-h. This avoids a second full A product. For one
terminal column it adds at least E off-diagonal factor-solve contributions, so
connected factors give at least 5n-4 per board, or **15,275,567** across both.
At most **4,724,433** updates remain for Wgen, B contractions, small Schur work
and any other charged operations. This is a lower bound, not a fit estimate.
A lower-tree/diagonal pair can have F=2n-1 and Wprod=2n-1, so dimensions alone
do not reject this route. Such sparsity does not prove contraction or a useful
Schur enclosure; a tiny contraction margin may make the result unusable.

The specific source-only task identified by this bound was to verify that
factor-solve lift on exact-rational joined fixtures, including floating KB and
weak grounding. That fixture work is completed in the follow-up below. A useful
production factor pattern with an explicit Wgen/Wprod/row-workspace bound and
quantitative q/Schur/usefulness argument remains required. No generic spilu-then-truncate
step is permissible: its transient fill and hidden work would be unaccounted.

## Prototype actually inspected and executed

The independent reviewer ran the fixed synthetic test command with its built-in
512MiB address-space, 20 CPU second, order128 and one-thread limits, under an
outer 30-second timeout. All **12 tests passed** (unittest reported 0.025s).
This timing is not a full-data performance estimate.

Reviewed local prototype hashes:

- `__inbox/e16-factor-residual/prototype.py`:
  `e98e9be3875d40b11eae8b192cb01b64290b25676f2903d34e9b291e42b27ca2`
- `__inbox/e16-factor-residual/test_prototype.py`:
  `ab437c2daf2efa5a8f4fca551a4e8e1ec2ba21729922652109df5841a22e72a1`

The prototype charges more than the contribution lower bounds above: each LU
term has a multiplication and subtraction charge, comparison recurrences charge
both multiplication and addition, and divisions/row reductions are charged too.
Its phase totals agree with its cumulative counter. It reserves pattern entries
and 8n additional slots, a deliberately conservative toy model. It must not be
described as a production storage layout. In particular pattern_of constructs
the bounded tiny pattern before Meter.entries checks it; production pattern
construction still needs a real pre-allocation bound. Packed arrays and explicit
conversion lifetimes are needed for a credible million-node implementation.

Under this toy's stricter scalar counter, connected factors already need at
least 2Wprod+4E+2n >=10n-6 charges per board for the LU residual and two comparison
passes, even before row reductions, producer or Schur lift. Across these boards
that is30,551,138>20M. Thus this actual toy meter/layout cannot be scaled directly
into production. The proposed contribution-based model must be explicitly bound
and independently reviewed against the existing Schur-update convention; changing
the toy's counter is not evidence that its full-data workload fits.

The 4x4 dropped-grid fixture certified with inverse upper about74.69; the 8x8
weakly grounded dropped-grid fixture refused at q=1.0000000000000067. Valid
uniqueness with a roughly2.147e9 inverse bound left the downstream screen
INCONCLUSIVE. These are concrete negative/usefulness observations, not a reason
to try the same unchecked pattern on original data. The current prototype tests
the complete tiny joined matrix. That initial revision did not implement the
serial-board factor-solve Schur lift; the following reviewed revision supersedes
that implementation limitation.

### Frozen factor-solve bridge follow-up

The retained `fixture/prototype.py` and `fixture/test_prototype.py` were inspected
and independently executed after the bridge was added. All **17 tests passed**
(0.062s unittest time), under the same explicit fixture limits and outer timeout.
Their respective SHA256 values are:

- `dc79161081bf48ba993cbdcafc2dcd6b201ec24915275bdc6fb644bcfdb98d4c`
- `d39295ae2447b3b4e6318d6540afeb57c43f998f9032022f12396a6414d2d3d7`

The bridge shares Work across both producers, board certificates, signed factor
solves, small inverse witness production/verification and global bound. Its
offset conservatively retains previous board allowances rather than resetting
work or hiding overlaps. Temporary factor-row dictionary copies were removed;
producer row scratch is deleted before lowering its live-entry count. The toy
pattern allocation remains explicitly bounded by order128 before construction.
It is still not a production layout or a claim that the prototype's scalar meter
fits20M on original dimensions.

The actual bridge loops all global terminal columns for each board, including
an all-zero column belonging to the other board. Therefore its actual work is
larger than the one-local-column lower bound above; the lower bound is not a
measurement of this code. Fraction tests now check exact board Schur intervals
and the complete joined inverse bound. Board certificates with diagonal factors
can succeed while the small Schur certificate refuses. Rooted-tree factors with
F=2n-1 give a roughly20,159,998.5 inverse upper bound on a strongly grounded
8x8 grid, and refuse the weakly grounded8x8 case. Storage feasibility remains
distinct from usable contraction/error bounds.

### Further KB-only near-null lift: resource question precisely located

The mathematics reviewer subsequently proposed r=B+A*1 and
s=D+B^T*1-B^T*A^-1*r for the scalar KB interface. This is the same candidate's
Schur witness, not a replacement physical operator or an assumption of exact
row-sum conservation. Its signed row additions are real witness work even when
fused with an already necessary matrix scan.

Keeping the factor-solve lift on KA, connected factors alone cost at least
12,220,454+1,513,836=13,734,290 contributions before the KB row-sum pass. Thus if
the actual stored KB Af nnz is at least **6,265,711**, this version already
exceeds20M before producer work, B/D contractions and the small Schur proof.
The retained metadata examined here do not supply exact KB Af nnz; historical
LU counts cannot substitute for it. The lower bound from KB nonsingularity alone
only gives15,275,568 total and does not reject this version. No unguarded array
inspection was performed to close that gap. Source-only exact fixtures and a
fixed useful factor-pattern argument remain necessary before any decision to
prepare an independently admitted characterization of that specifically bounded
unknown. A near-null numerical residual cannot be declared zero from topology.

## Complete operation costs remain

All of the following remain inside the original shared-entry deadline and
aggregate caps, in addition to witness production and verification:

- Exact source/toolchain/input verification and descriptor-bound decode, including
  compressed prehash/decode/posthash, memo/array overlap and output accounting.
- Original board_parts coordinate arrays and sparse conversions, retained Y for
  both boards, original KB factorization/refinement, terminal solve and actual
  original nonsymmetric residual evaluation.
- Eight complete mesh passes per board in Assembly, followed by a ninth physical
  accounting pass. Each pass decodes all chunks and hashes compressed bytes
  twice. Earlier value arrays survive through Assembly's vv lists; one chunk
  container does not imply one chunk's memory.
- Complete mapping, partition and class-current/energy reconciliation, interval
  energy/share and TP990026 reaction evaluation, serialization, retention copies,
  terminal validation, hashing and owned cleanup.

Retained original assembly observations were34.047/45.241 seconds and about
1002/1010MiB RSS in separate jobs. They are not combined-pipeline timings.
The worker deadline is at most155 seconds after shared-guard entry: 180 seconds
minus15 seconds host tail and10 seconds cleanup. Startup and input checks already
consume part of that interval. The 1216MiB worker ceiling, 2GiB aggregate including
the external reserve, zero-operation swap,64MiB aggregate output,16M input,
4M live entries and20M certificate updates are unchanged.

The current request compiler and worker accept only the fixed complete experiment;
there is no existing characterization branch. If a later, precisely scoped
original-data unknown becomes necessary, implement and review that admitted path
first, with fixed limits and explicit outcome-dependent decisions. This review
does not justify an unguarded numerical probe or a misleading FULL qualification.
Stage C remains NOT RUN; resource qualification remains NOT_QUALIFIED and
production remains NOT_ADMITTED.

## Final frozen-fixture resource delta review

The reviewer inspected the subsequent exact-type and whole-input binding changes
and independently reran the retained fixture once. **18 tests PASS** (0.063s
unittest time) under the same512MiB/20CPU-second/order128/thread limits and outer
30-second timeout. Final reviewed identities supersede the earlier fixture hashes:

- `fixture/prototype.py`:
  `3ce2ca1f693d65cb09df64da89e01ca99129a958c4672f8fd82ac1696c9b612e`
- `fixture/test_prototype.py`:
  `d232775271f3647cbe5a425a8a0d93ed4820f4c37c20d69a07e3c92951bd74e4`

B now must be a finite binary64 array with the exact expected shape. D scalars
and interval endpoints, and signed factor-solve inputs, refuse unsupported types
instead of silently narrowing them. A global digest covers the original board
matrix hashes, exact B values, D intervals and context. Changing B, D or context
changes the digest. This is a binding, not a signature or an execution grant.
The toy's B.tolist/JSON hashing adds real allocation/runtime work under its actual
address-space/time limits; it is not charged as floating certificate arithmetic
and is not a proposed million-node serialization implementation.

These changes leave the numerical phase counters, existing resource obstructions
and negative real-data eligibility decision unchanged. No production source was
integrated. The separate mathematical review's rooted-tree quantitative failure
is a reason to reject that concrete sparse producer as a scalable useful strategy,
not a reason to erase its retained positive and negative tiny results or increase
the cap. A different producer still requires its own quantitative proof and cost
argument; the general algebraic certificate is not itself a fit guarantee.
