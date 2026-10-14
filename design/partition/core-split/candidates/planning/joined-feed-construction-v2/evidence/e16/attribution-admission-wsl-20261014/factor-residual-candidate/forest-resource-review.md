# Independent resource review: verifier-owned forest

Reviewer `/root/resource_review`, 2026-10-15 JST. Source-only inspection and
independent synthetic tests; no original numerical input, characterization,
diagnostic, baseline, grant or outward action.

**Decision:** accept the bounded single-pass forest increment and its explicit
proposed contribution correspondence for further local engineering. No original
production fit, admission or live-entry remapping is established. Earlier
primitive/fixed/compact kernel counts remain intact. This implementation removes
a real complete producer margin pass and a repeated selected-edge validation
pass; its smaller proposed count is not obtained by resetting those counters.

## Frozen source and independent tests

- `fixture/prototype.py`: `738774acdddb70b7e6e88830a450acc19a8c86fa5d8885e66113c67ed7074494`
- `fixture/test_forest.py`: `b76eca4128833f5ff151348ea328c592172bec4e596a3c282709fbb15edaf843`

Independently executed four tests: PASS (0.379s), established numerical venv,
`python -B`, one thread, outer30s timeout,512MiB address-space and20CPU seconds.
Order remains<=128; exact dense references remain tiny. Cases include retained
and held-out grids, heterogeneous nonroot rerooting, whole joined strong/weak/
nonsymmetric intervals, disconnected/singular/one-sided refusals, failed
contribution scopes, wide cancellation, cap failure and weak-reference lifetime
checks. Independent mathematics/oracle review is separate from this report.

Final measured cases:

| Case | Float calls | Proposed contributions | Integer kernels | Bit-work envelope | Index events | Actual typed-buffer allocation bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Grid4 | 68 | 85 | 12452 | 8293424 | 1151 | 777 |
| Grid8 | 260 | 357 | 56076 | 37391152 | 5047 | 1977 |
| Held-out grid9 | 328 | 455 | 71857 | 47916579 | 6446 | 2402 |
| Strong joined interval | 53 | 42 | 4204 | 7148031 | 348 | 527 |
| Weak joined interval | 53 | 42 | 4204 | 6752915 | 348 | 527 |
| Nonsymmetric joined interval | 53 | 42 | 4204 | 7320725 | 348 | 527 |

The held-out9 invocation used0.16831s with17,111 traced peak bytes. The strong
joined invocation used0.01127s with25,119 traced bytes. Process high-water reached
70,964KiB including imports/oracles/control fixtures. Allocation numbers in the
last column are `sys.getsizeof` sums for actual simultaneously live typed
buffers, including their object headers; they are not whole-process peaks.
Tracemalloc omits some native allocations and excludes caller input construction
and subsequent physical/oracle work. These observations do not prove original
180-second fit; interpreted exact-arithmetic latency remains material.

## Actual numerical and index loops

Each original row begins with a direct checked diagonal read and exact decode.
Each strict coefficient performs the explicit recurrence

    margin <- margin - abs((a_ij + a_ji)/2).

The average uses both actual stored directed coefficients, exact compact
arithmetic, and the existing structural-symmetry refusal. All row contributions
are verified, including the opposite triangle. Only forest selection considers
one triangle. A negative edge joins components only after its original exact
coefficient has been checked and its binary64 conductance independently rounded
inward. Thus the private tree contains checked edges; no externally supplied
summary/edge list or skip-verification interface exists.

Union by size reroots the smaller oriented component's parent path, transferring
the old edge conductance as each link reverses, before attaching the selected
edge. The DSU representative stays the larger component's oriented root.
Size/range/orientation checks precede uint32 writes. Each vertex can belong to
the smaller component at most O(log n) times; actual DSU find/compression, parent
and conductance reads/writes, union sizes and discarded cycle edges are recorded.
That asymptotic fact does not make those visits free.

After the complete row pass, the forest must contain n-1 checked edges and have
a positive exact root margin. Final rerooting establishes the proven ground.
DSU and size buffers are explicitly deleted before the path buffers are
allocated; weak references independently verify actual destruction. Memoized
parent walks use bounded stack/state buffers and evaluate each root-to-node
recurrence once. Maximum path radius is now computed once, with reads and
comparisons counted and the value reused in output. No adjacency list, full
joined CSR, transpose, factorization, original-system solve, global inverse or
unreported ordering search is constructed.

Before/after operator and context hashes reject persistent mutation during the
proof. This is not claimed to defeat adversarial transient edits; stable owned
inputs remain the execution contract. Input hashing is reported as two passes;
typed witness hashing reports12n bytes (parent plus edge). Virtual-input access
counters separately retain validation, coefficient, binary-search and hash work.

## Contribution correspondence: precisely what is accepted

`ProposedContribution` adds a separate ledger; it never substitutes for Work's
existing primitive calls or the explicit integer/index ledgers. Each scope is
charged at least one64-bit word and at ceil(maximum recorded arithmetic operand/
alignment/result width/64). Compact addition reports its pre-normalization
result width, so cancellation does not reduce the scope charge. The wide
cancellation regression returns a one-bit answer from101-bit aligned inputs but
charges two word units. Exceptions finalize the partial scope; nested scopes
refuse. Cumulative phase totals and width histograms remain visible.

This correspondence is defensible against the old production source, which
charges one compound scalar Schur destination update rather than every endpoint
multiply/divide/subtract or bit/index instruction. Diagonal initialization is a
copy/decode, with all work retained in fine ledgers. Root/deficit max, sign and
proof comparisons remain separately counted exact control work, consistent with
old norm-max/control work being outside destination-update counts. Selected-edge
floor conversion, path recurrences, root conversion, final bounds and interval
perturbation contributions are explicitly included, conservatively extending
that destination convention. This does not allow an opaque row/library solve to
be counted once, nor does it approve a numerical execution request.

For one-word contributions and m nonzero entries in the complete represented
operator, the actual certificate skeleton is

    (m-n) strict-row contributions
    + (n-1) selected-edge floors
    + 1 root floor
    + n root/path contributions
    + 5 final norm contributions
    = m+n+5.

Every wider scope increases this total. Interval replacement adds one contribution
per replacement and three final perturbation contributions. Review found the
small virtual D midpoint constructor initially lacked contribution scopes; the
final source directly charges each three-operation midpoint destination at
construction time, one scope per terminal entry, with no replay or manual
deferred charge. The strong joined total is therefore42 proposed contributions:
31 forest +7 interval perturbation +4 midpoint preparation. Its fine floating
count remains53. Original board construction, retained-Y checks and physical
operations still cannot disappear from a complete resource envelope.

The original20M cap is not increased or reinterpreted as a bit-operation cap.
This review accepts the new named ledger's source correspondence for local
experimentation only. Using it for an original fit claim still requires a
complete actual-loop budget, all width penalties, native/runtime evidence and
pipeline overlap. Previous187,969,188 compact-kernel lower counts remain true
under their stated stricter declared-unit convention; they were never a claim
that production Schur units and decode kernels were identical.

## Entries, payload bytes and real allocation

The selection stage holds parent4n + edge8n + DSU4n + size4n =20n payload bytes.
Arrays are preallocated then filled, avoiding capacity growth from range-iterator
construction. After DSU/size release, parent4n + edge8n + path8n + state1n +
stack4n =25n payload bytes. The actual allocation metric includes array headers:
for n=81,2025 logical payload bytes become2402 allocated typed-buffer bytes.
Objects, exact-row scratch, virtual small-D ownership, input CSR/B/Y, hashing
metadata and allocator overhead remain additional. The toy slot meter deliberately
retains its conservative4n/5n-plus-scratch reservations and is not silently
redefined to match production entry policy.

A proposed production numerical-entry correspondence is also defensible locally:
count n-1 retained checked conductances, one ground scalar, bounded live exact
row scalars and owned small terminal/interval entries. The old frontier policy
counts retained interval/factor entries but explicitly puts index scratch and
forward/backward norm vectors in the byte budget rather than4M sparse fill.
Consistently, parent/DSU/size/stack/state and path-norm buffers would remain in
full byte accounting while excluded from the numerical-fill number. This would
be n+O(1)+smallD numerical entries, not a proof that the whole worker fits. It
must be separately specified/reviewed before production use; the old toy slot
metric and all memory limits remain unchanged.

## Remaining concrete eligibility work

The representation now removes the duplicated exact verification passes and
adjacency-storage uncertainty. It still does not establish executable original
runtime. Tens of thousands of interpreted exact kernels occur on order81;
small-width contribution totals cannot erase their real cost. The next justified
source step is a bounded native implementation of these same explicit exact
loops, using fixed-capacity2176-bit/34-limb storage with actual-width tracking,
retaining primitive, integer/limb, contribution and index counters and failure
semantics. Differential tests must cover all current exact/rounding/reroot/
mutation/cap cases. A native entrypoint is not one operation, and no opaque
factorization or vectorization discount is permissible.

In parallel with that source work, implement/review the raw distributed-stamp
preallocation bound before `board_parts` allocates coordinate lists and sparse
conversion scratch. Its raw tuple count can exceed canonical nnz; the16M final
CSR gate is insufficient. Retained original inputs, B/Y, unchanged KB SuperLU/
refinement, CSR/CSC overlap, transport object graph, Assembly passes, PatternSum
and physical energy/reaction accounting must share the unchanged1216MiB worker,
2GiB aggregate,180-second guard deadline, zero-swap and64MiB output limits.

Until the native loops and complete allocation schedule are reviewable, a
positive original applicability answer would leave no cap-qualified executor.
**No original-data characterization or qualification is justified now.** The
next work is concrete authorized source development, not another external plan,
new baseline, cap increase or consumed-request reuse.
