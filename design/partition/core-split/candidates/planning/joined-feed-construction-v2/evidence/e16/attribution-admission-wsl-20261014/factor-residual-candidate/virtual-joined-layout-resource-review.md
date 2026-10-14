# Independent resource design: virtual joined input and packed tree

Reviewer `/root/resource_review`, 2026-10-15 JST. Base checkpoint
`94450d792f05470293645e93965ca31e6b738f5a`. Source/retained-metadata analysis only:
no original arrays, numerical archives, characterization, diagnostic or baseline.
This report adds to rather than replaces earlier resource decisions.

**Decision at design review:** virtual joined rows and packed tree vectors remove
specific allocations and are appropriate bounded source work. They do not prove
complete operation fit. The literal refined trace/path-Cauchy implementation is
already over20M in its existing primitive convention before any integer work.
A root-path-only norm changes the algorithm and can evade that particular
floating lower bound, but its exact row verification and original pipeline
remain unqualified. No original-data characterization is justified by a packed
vector byte total alone.

## Audited pipeline source

SHA256 identities:

- `attribution_executor.py`: `d974de2fc67927775f80f7521e910ad7891e6d2d1860a2eafd6f2050684d4896`
- `finite_solve.py`: `20b1b9e1e7ba8653d3268c4956dc5415b91670e23f07e35ab381d2091f84b044`
- `finite_adapter.py`: `f313a87719aba83b169a363c05d36daa5c79cd28ad41620e5d45c5d8eca613f4`
- `attribution_transport.py`: `c122e14552447ee495f91840100f9e0dc703bd7cda6ce64d9cb726a246ca0d50`
- `attribution_uniqueness.py`: `828ec3e48ca7e05b094c32b9d8927bf10439623be80300a903d0ad7c8613da8f`

The retained free orders are nA=1,513,837 and nB=1,541,278. Define
N=nA+nB=3,055,115, k terminals per board, n=N+2k joined order, mA=7,818,329
retained KA stored entries, mB the unknown KB stored count. These are metadata,
not newly decoded numerical observations. Do not substitute historical factor
counts for mB or assume absence of explicit zeros.

## Concrete typed layout, with both boards included

All original orders and indices fit uint32; the implementation must check that
before allocation and reserve a distinct sentinel. Parent/order uint32, edge
binary64 and a uint32 subtree mass require20n bytes; a binary64 path vector and
uint8 seen vector make29n bytes. At the free-node N this is88,598,335 bytes
(84.494MiB), plus29*2k terminal bytes. The serialized in-memory tree packet
(parent/order/edge) alone is16n bytes (46.617MiB at N). No duplicate Python integer
lists or JSON number arrays may be smuggled into this packed estimate.

Root-path-only verification needs no subtree mass: parent/order4+4, edge/path8+8,
seen1 gives25n bytes, or76,377,875 bytes (72.840MiB at N), plus terminals. A FIFO
BFS can use the existing order vector with integer head/tail indices; an
additional order-length queue is unnecessary. Streamed row accumulators are a
constant number of bounded-width integers, not an n-length bigint array. Packet
hashing must stream typed array bytes with canonical dtype/shape binding rather
than call `.tolist()` or serialize millions of Python integers.

For int32 sparse indices, two original CSR matrices require at least

    12(mA+mB) + 4(N+2) bytes.

Nonsingularity gives only mB>=nB, yielding124,535,752 bytes (118.767MiB). A
hypothetical aggregate16M-entry allowance gives204,220,468 bytes (194.760MiB).
That second number is conditional, not a newly imposed interpretation: existing
`certify` checks each input matrix against `max_input_nnz`, while both-board
entry/update caps are cumulative. The actual request binding and future joined
input check must make aggregation explicit without changing the authorized cap.
Using the existing per-matrix KB upper16M with known mA instead gives298,040,416
bytes (284.233MiB). None of these numbers includes B, Y, source operators or
conversions. int64 sparse indices require16 bytes per entry and8-byte pointers;
int32 storage must be checked rather than assumed.

Dense B storage for both boards is8Nk bytes. Retained Y is extended precision,
not binary64: `refined_interface_solve` and retained receipts specify float128,
16Nk bytes on this runtime. At k=1 those are23.309MiB and46.617MiB. Both free-index
vectors use8N bytes (23.309MiB); the retained selected KB u0 uses16nB bytes
(23.518MiB). Terminal matrices are O(k^2), but whole-array finite checks and
source/target dtype conversions can add temporary buffers.

For illustration only, refined29N vectors + two minimal CSR inputs + B/Y for
k=1 + free vectors + selected KB u0 already total335,558,215 bytes (320.013MiB).
Using the conditional aggregate16M CSR case gives415,242,931 bytes
(396.007MiB). These are partial sums, not peak estimates; k is not asserted to
be one in the original experiment. Increasing k adds24N bytes per terminal
pair. The worker limit is1,275,068,416 bytes (1216MiB), not the full2GiB aggregate.
The external64MiB reserve and supervisor/bootstrap/scope allocations remain
outside this worker allowance and cannot be reassigned to it.

## Source-visible overlap that the partial sum omits

`_board_selected` currently reconstructs Af/B/D, verifies the retained Y residual,
then performs the unchanged selected KB SuperLU/refinement and drops Af/B/D.
It retains Y/free/selected u0 for the later physical pipeline. A whole joined
certificate needs both board operators simultaneously or an explicit bounded
row-access schedule; that lifetime is new relative to the serial existing
certificate. Retaining a KA CSR while building/factoring KB increases overlap.
Converting the CSC produced by `board_parts` to CSR temporarily retains both;
releasing or changing the original solver's CSC input cannot be assumed.

`board_parts` retains decoded class operators while assembling K/Kb, COO,
free/pos masks, raw coordinate vectors, dense B and CSC. Its raw tuple count r
includes distributed support outer products, sum(support_size^2), before
canonical duplicates are summed. `rows`/`cols` are int64 and values binary64;
original24r-byte coordinate lists and their24r-byte concatenations coexist
while the sparse constructor builds output. Additional index narrowing/COO/CSC
scratch and source operators overlap. Canonical final nnz does **not** upper
bound r. Merely using mA for48r gives357.895MiB; actual r can be larger. A
16M final-input gate therefore does not prebound this constructor's temporary
memory. This is a concrete missing preallocation bound, not proof of a historic
breach. A complete design needs a raw-stamp count guard before allocation or an
already-proved constructor allowance, preserving every independently rounded
termination coefficient and original solver behavior.

Transport streams compressed bytes but `pickle.load` still retains a memo/object
graph; the512MiB decoded-byte limit is not a heap-size proof. `_board_selected`
decodes the whole retained reduction before discarding unrelated load fields.
Both Y matrices remain live across later stages. `_extended_residual` allocates
float64 output plus one long-double node residual per RHS and bounded sparse
scratch. SuperLU transient factor/permutation/workspace memory still belongs to
the unchanged physical selected solve; the new certificate removes none of it.

Mapping/accounting reconstructs the full field, then decodes original operators
and runs `Assembly`. Assembly retains geometry arrays, concatenate/unique
scratch and value arrays from earlier streamed chunks in `vv`; one yielded
chunk does not mean one chunk of live values. Eight mesh passes construct/check
Assembly and another performs physical accounting. Historical separate assembly
observations near1002/1010MiB are warnings, not combined-pipeline measurements.

`_account_board` retains original class operators, reconstructed K/Kb, a copied
CSR in `PatternSum`, and a long-double value array of that copied pattern. For a
KA-sized pattern, PatternSum alone is28mA+4(nA+1)=224,968,564 bytes
(214.547MiB), before K itself, geometry, field, current/original/RHS long-double
vectors, component scratch and held-reaction work. The exact K pattern may
differ from Af, so this is a dimensional illustration, not a measured original
allocation. Certificate vectors should be released before mapping if not needed,
but the unchanged live source/physical allocations still require their own peak
proof. No memory saving justifies skipping whole distributed termination energy
or the selected reaction bounds.

## Literal-code floating obstruction and an algorithmic alternative

For a successful emitted n-node coercivity tree, coefficient int-to-float plus
ldexp costs2n primitive charges. Trace verification needs at least3n+4 more
(conversions, divisions, additions and scalar corrections). Thus trace-only
costs at least5n+4, excluding every exact-integer kernel and input scan.

Path-Cauchy refinement adds at least5n+2: three root operations, five per
nonroot path/mass contribution, then product, sqrt trial, one outward square
and refined division. Therefore the literal refined method requires at least

    10n+6 >= 10N+6 = 30,551,156 primitive charges.

Terminal nodes add20k. This is an unconditional rejection of direct original-size
execution of this literal refined primitive-meter algorithm, even with free
exact row arithmetic and every other pipeline stage omitted. Packing arrays or
virtualizing joined rows cannot change that arithmetic result. The earlier
reported primitive counts remain authoritative.

A proposed root-path-only bound uses rmax=max_i(1/g+sum_path 1/c),
tau<=n*rmax and sum(T^-1)<=n^2*rmax. Subject to separate mathematics review, it
can use inverse bound n*rmax/(1-delta*n*rmax), avoiding subtree mass, trace and
squared-mass passes. Its producer/path floating count is4n+O(1), about12.22M
before integer/input/interval/physical work. This is a different algorithm,
not a silent counter change or a fit claim. It leaves a nonzero arithmetic
margin in a dimension-only float bound; it does not make exact row arithmetic
free or prove usefulness for the original field screen.

## Strict proposed accounting correspondence and decision gates

Retain three separate ledgers: (1) existing primitive floating/interval calls,
(2) declared exact-integer kernels by width and phase with the existing bit-work
envelope, (3) index/row visits and reverse-search comparisons. Also retain actual
wall/CPU/peak bytes. No reset between producer, verifier, failed attempts, both
boards, interval wrapper or original physical work.

The source production scalar unit is an LDL destination update
`old - row_i*row_j/pivot`; factor divisions, comparison norm sweeps and scans
are not charged by that implementation. A minimal proposed new correspondence
may charge one explicitly bounded scalar destination accumulation once, but
must enumerate its multiplications/divisions/additions and preserve the finer
counter. It cannot charge a complete row, vectorized kernel or factorization as
one. Wide exact integer kernels must receive a separately reviewed bound; a
2176-bit addition is not silently one existing binary64 scalar update.

For a strict audit envelope, charge every declared integer kernel at least one
64-bit limb visit per ceil(width/64), in addition to primitive floating calls,
and count reverse-search comparisons separately. This conservative proposed
mapping decisively rejects the literal repeated fixed-exponent decode/row
implementation at original dimensions; several wide operations per coefficient
and two complete row scans already overwhelm20M even before the norm bound.
This is an audit obstruction under that declared mapping, not an approved
replacement of the production convention or a universal lower bound for all
possible exact-accumulator implementations. A genuinely different bounded
accumulator or fused implementation must expose its loop and limb work, rather
than change the count label. No mapping has been approved for a fit claim here.

The next source review must therefore establish a concrete virtual-row/packed
implementation on synthetic inputs, raw input-construction prebounds, and a
complete kernel/byte/lifetime schedule under unchanged original pipeline stages.
Only after an arithmetic design and full worker envelope remain viable can an
unknown original applicability property justify characterization. Currently a
positive original structural-symmetry/deficit answer would still leave the
literal refined algorithm rejected and the root-path/exact-arithmetic layout
unqualified. **No diagnostic or characterization is authorized by this report.**

## Final bounded implementation review

The virtual-row, packed-vector and root-path implementation was then inspected
and independently executed. Final reviewed source identities:

- `fixture/prototype.py`: `d5dfc727f8f64c75f9e38bd868933e0ffbb8f31f63807e27491013d977b25930`
- `fixture/test_virtual.py`: `c01b8f410a9d2ddf1849f67025a33083130d0189d29fc5322d471cec6f804c7c`

Four tests PASS independently (0.075s unittest time) under the established
outer30s timeout,512MiB address-space,20CPU seconds and one-thread limits.
Exact stored virtual rows and reverse lookups match the tiny joined CSR oracle;
cases cover nonsymmetry, weak grounding, shared terminal columns, malformed
layout and changed inputs. Oracle CSR construction belongs to fixture control,
not the nonowning candidate view. The original order128 ceiling remains.

`JoinedRows` references existing CSR/B inputs and stores only the small terminal
midpoint/mapping metadata. There is no global joined CSR or transpose.
Terminal-to-free incidence scans actual dense B columns, including zero-value
visits; it does not claim those scans are free. CSR reverse search now has an
explicit bounded binary-search loop with a comparison counter. Repeated CSR/B
validation scans and hash bytes are recorded. Hashing streams actual typed
buffers, preserving mutation detection without a full JSON copy.

Packed producer arrays check uint32/double item widths and sentinel range before
allocation. BFS reuses its fixed order buffer. The temporary order-permutation
bytearray is deleted before the independent tree-seen bytearray is allocated.
Root-path mode allocates neither subtree mass nor trace/squared-sum vectors.
Its claimed25n bytes exactly describe the live typed parent/order/edge/seen/path
payload; object headers, row scratch, inputs and metadata remain excluded and
subject to actual process bounds.

The packed root-path4/8/9 grids certify inverse bounds approximately112,960,1377
with68,260,328 floating kernel charges respectively. These are weaker than the
path-Cauchy refined bounds but eliminate specific charged operations. The strong
joined packed fixture certifies inverse<=36.90000000000181 with53 floating
kernel charges,1499 declared exact-integer units,130 reserved slots and150 typed
tree payload bytes. Invocation traced peak is9122 bytes and wall time0.00645s;
weak joined traced peak is8954 bytes and remains physically inconclusive.
Process high-water is68,368KiB including imports/control work. These observations
have the same limited resource scope as earlier reports, not production scaling.

Review found that early view-access totals mixed candidate accesses with oracle
row-equivalence prechecks. Final outputs now retain the cumulative total, the
pre-invocation baseline and the certificate delta, without resetting counters.
For the strong packed certificate the delta is35 A entries,73 B entries,23 D
entries,33 binary-search comparisons,59 lookup calls,18 row calls,736 hash bytes,
64 validation entries and16 validation rows. The constructor's earlier16
validation entries/four rows remain in the cumulative total. Index comparisons
are search comparisons, not all Python/index/control instructions; the distinction
is explicit.

**Implementation verdict:** accept this bounded representation and root-path
increment; retain all earlier literal refined-meter rejections. No original-size
fit, qualified execution or characterization follows.

The next concrete source action is now the exact row kernel, rather than another
representation prototype: implement a bounded row-local dyadic accumulator with
explicit exponent tracking and charged rescaling, then compare every result to
the existing independent exact oracle across cancellation, subnormal, extreme
exponent-span and nonsymmetric cases. Fixed exponent-1075 turns ordinary unit
values into1076-bit integers; adaptive representation can remove real wide work
on ordinary rows without assuming any original exponent distribution. Preserve
the2176-bit bound, finite term/scan limits and every rescaling/width/limb charge;
refuse or retain the bounded wide path when extremes require it. This changes
actual kernel representation and loops, not counter names or resource caps.
Only a complete reviewed mapping and original-pipeline allocation schedule can
turn that future source result into an eligibility decision. No original probe
is justified at the present checkpoint.
