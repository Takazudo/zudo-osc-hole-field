# Source review: minimal raw-stamp preallocation guard

Reviewer `/root/resource_review`, 2026-10-15 JST. Source inspection only; no
original operator/support arrays were decoded or inspected. No pinned solver,
refinement, assembly, admission state or host configuration was changed.

**Decision:** implement a pure structural preflight before the existing
`board_parts` calls, leaving their numerical implementation and summation order
unchanged. The guard can establish safe upper counts from already decoded
shape/length/dtype metadata inside the existing admitted worker. It cannot turn
an unsupported native-workspace multiplier or current RSS reading into a proven
1216MiB complete-operation bound. Report this narrower distinction explicitly.

## Exact structural upper counts

For one board let:

- N be the declared original node count, checked against both class matrix shapes.
- f/i be stored data-array lengths of Kg_face/Kg_inner (using allocated stored
  lengths is at least as conservative as logical nnz and avoids coefficient reads).
- b=sum(max(len(barrel['taps'])-1,0)) over the actual barrel metadata.
- q=4b be the exact number of raw barrel coordinate triples produced by
  `finite_adapter.laplacian` before duplicate summation.
- T be the actual terminal count and s_t the length of each corresponding
  support node vector, checked equal to its weight-vector length.

Then the constructor's whole-K stored count is bounded by

    K_upper = f+i+q,

and its raw free/stamp coordinate tuple count is bounded by

    R_upper = K_upper + sum_t s_t^2.

The free-node filter can only reduce these counts. Using all N and all support
nodes avoids allocating a held mask or reading node/weight values merely to
preflight. Independent terms may overlap or contain duplicates/explicit zeros;
none of that permits reducing the raw count before original construction. Do not
replace sum(s_t^2) with canonical Af nnz. The largest individual outer product
is s_max^2, even if its eventual canonical contribution disappears.

The formulas follow the literal source: scaled class CSR addition, four raw
barrel entries per consecutive tap interval, then the retained K coordinate
triples plus one `repeat`, `tile` and `outer(...)/Rt` term per terminal. They do
not invent element identities, exact conservation, disjoint support sets or
original coefficient signs.

The guard needs only Python integers, array shapes/sizes/item widths, format and
dtype tags, terminal keys and barrel tap-list lengths. No coefficient, coordinate,
support-weight or node-index value is needed. Metadata traversal must call the
existing operation budget/checkpoint and record item counts; it runs inside the
same guard entry deadline, never an unguarded original-data probe.

## Safe validations before allocation

Extract a small immutable metadata record, then pass it to a pure arithmetic
helper. Validate exact integer N/counts (reject booleans), nonnegative sizes,
matching square class shapes, supported CSR format/binary64 values/integer
indices, index/data length consistency and pointer-array shape. Validate actual
terminal identity coverage and paired one-dimensional support lengths. Do not
call `np.asarray`, sparse conversion, held-node selection, `.toarray`, numeric
reductions or coefficient validation as part of this metadata preflight.

All count arithmetic uses Python integers and rejects out-of-range counts before
NumPy allocations or uint32/int32 casts. Return scalar counts and decisions;
never allocate an R-length list to prove its bound. An empty/zero-length support
must follow the unchanged original input contract rather than being silently
repaired. Unknown formats/dtypes/shape inconsistencies refuse explicitly.

A conservative raw-entry gate may require R_upper<=the separately explicit
admitted raw-construction ceiling, no larger than the existing input quota.
Reusing16M as a conservative raw ceiling is a new stricter preallocation check,
not a claim that existing `max_input_nnz` already measures raw tuples. Name both
fields distinctly. If that conservative upper bound refuses, do not decode
values to sharpen it outside an explicitly reviewed characterization operation.
No cap is raised to make an input fit.

## Named array overlap, not a guessed heap proof

Let C64(s)=16s+8(N+1) represent a conservative sparse binary64/int64-array
payload. Using actual int32 metadata may tighten a separately verified branch;
using64-bit widths is safe for structural planning.

At raw Af conversion, the source holds24r bytes of original int64/int64/float64
coordinate arrays, then all three concatenations (another24r), while compressed
output may require C64(r). The pinned SciPy compressed constructor can additionally
cast COO major/minor index arrays (up to16r). Thus the following named-array
allowance is justified as a conservative envelope for those simultaneous arrays:

    coordinate_conversion_arrays <= 80 R_upper + 8(N+1).

This deliberately assumes original triples, concatenated triples, both copied
index arrays and compressed output coexist. It is not yet a full allocation
upper bound: native sorting workspace, pruning copies, allocator overhead and
Python containers must be added separately. Terminal outer-product temporaries
need an additional allowance based on s_max^2; even16 s_max^2 bytes is only the
named floating outer/division buffers, not all support masks/index vectors.

Other required named terms include at least:

- Dense B/D:8NT+8T^2.
- New fixed/free/pos/index vectors and masks: bound with N, not unknown actual
  free size; account the caller's already retained fixed/free copies separately.
- Class-scale/addition and K/Kb/COO overlap, bounded using f/i/q/K_upper and
  actual index item widths.
- Barrel Python coordinate lists and interval records, bounded by q/b with
  platform-specific object/list allowance; they are not packed numeric arrays.
- One terminal's active support mask/selected node/weight/division temporaries.
- Sparse sort/prune/native workspace and a separately justified allocator/
  Python-object allowance under the pinned runtime.

The memory-admission condition must be explicit:

    complete_live_baseline_upper
      + preflight_constructor_increment_upper
      + independently_reviewed_workspace_and_tail_reserve
      <= 1216 MiB worker allocation.

The baseline includes decoded op/reduction objects, retained other-board CSR/B/Y,
free vectors and selected u0 actually alive at that call. It cannot use compressed
artifact bytes as decoded heap size. Current RSS/cgroup residency alone is not a
complete logical live-allocation bound, and no caller may pass zero as a fictitious
baseline. Missing baseline/workspace bounds mean NOT_QUALIFIED for full memory
fit, even if the raw-entry preflight passes. The actual cgroup hard cap remains
in force; this guard neither changes it nor replaces it with a model.

## Pinned dependency evidence and limits

The installed numerical venv reports SciPy1.15.3. Read-only source inspection of
`_compressed._cs_matrix._with_data` confirms scalar scaling copies indices and
indptr by default. `_binopt` allocates data/indices up to the sum of both stored
counts plus indptr; dtype/index conversions can add inputs. `_coo_to_compressed`
casts major/minor arrays and allocates output indptr/indices/data.
`sum_duplicates` invokes in-place sort and duplicate summation then `prune`;
prune may copy sliced storage. No claim is made here that the native sort's
allocation bound has been independently established. Therefore an arbitrary
coefficient such as128R must not be called a proven full heap bound merely
because it exceeds the visible Python arrays. Retain a named, reviewed native
workspace allowance or refuse full memory eligibility until it exists.

The pure raw-count gate remains useful without that stronger claim: it catches
rank-one outer-product explosion before its allocations, and produces the
precise conservative counts needed by a complete resource review.

## Insertion points without changing the pinned solver

1. At the very beginning of `attribution_executor._board_selected`, before
   `S.held_nodes`, `np.flatnonzero`, retained-Y finite masks or `S.board_parts`.
   This includes the preliminary vector allocations in the guarded envelope.
2. In `run_pipeline`'s whole-free-operator residual loop, immediately after the
   admitted operator decode and before its second `S.board_parts` invocation.
   Its baseline differs: both retained fields/Y and selected KB u0 are then live.
3. Any future joined-certificate builder must use the same helper before its
   original board constructor; it must additionally reserve the previously
   retained board input. No alternate unguarded construction route is permitted.

Keep `finite_solve.board_parts`, `finite_adapter.laplacian`, the original
solver/refinement and all summation/coefficient-generation code byte-identical.
The guard is a precondition/wrapper and evidence record, not a substitute builder.
It does not change physical RHS, sources, tolerances, terminations or operator.
A separate accounting-stage `A.laplacian` call still requires its own whole-pipeline
allocation allowance; guarding board_parts alone is not a complete phase audit.

## Concrete bounded tests for the helper/wrapper

- Pure metadata cases prove K_upper/q/sum(s^2), including zero/one/many barrel
  taps, multiple overlapping supports and counts near the raw ceiling.
- Huge advertised support lengths refuse by integer arithmetic without creating
  corresponding matrices/vectors; do not enlarge numerical fixture limits.
- Held supports and duplicate/zero coefficients do not reduce the metadata-only
  bound. No test relies on invented uniqueness/disjointness properties.
- Malformed shape/dtype/count/key records refuse before constructor calls.
- Spy the numerical constructor and held-node allocator to prove refusal precedes
  either call; sentinel metadata objects can raise on any value read/copy.
- A tiny accepted wrapper run calls the original `board_parts` unchanged and
  checks exact CSR/CSC bytes and B/D/free/mapping equality against the unwrapped
  call. No reordered summation or alternative assembly is introduced.
- Reports distinguish raw-preflight PASS from complete-memory NOT_QUALIFIED and
  retain the counted metadata visits and current operation deadline.

This is authorized source work only. The helper's existence does not authorize
another baseline, original diagnostic, full qualification or request reuse.
