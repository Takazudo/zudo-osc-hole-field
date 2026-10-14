# Independent native forest mathematics and ABI review

Reviewer `/root/math_review`, separate from the implementation coordinator.
2026-10-15 JST. No original operator, production solve, signer/admission operation
or campaign charge. The previous Python and native-helper evidence is preserved.

**PASS for the bounded native virtual-operator forest certificate and complete
terminal-interval enclosure.** This is not original-size qualification, a180-second
fit, an original physical disposition or permission for a diagnostic.

## Exact recurrence and selected tree

The native code borrows the existing board CSR and dense coupling buffers. Free
rows traverse the actual board entries and mapped coupling coefficients; terminal
rows scan the corresponding coupling columns and the small midpoint table. No
joined CSR or full coupling transpose is constructed. Native validation checks
finite/nonzero stored CSR coefficients, sorted unique in-range indices, row-pointer
ranges, terminal maps and finite coupling/midpoint values. Structural reverse
lookup remains mandatory; one-sided support refuses.

Each exhaustive row computes its exact symmetric part and diagonal-dominance
margin through the independently reviewed34-limb compact dyadic helper. The
triangle used for selection does not restrict the row proof. Every selected
negative edge is derived from an exact checked symmetric coefficient and a
verified positive downward-rounded conductance. Root margin and maximum deficit
are exact. The native union-by-size forest preserves the previously reviewed
oriented-root invariant and reverses conductances together with parent pointers.
Final rerooting and memoized root paths preserve the selected tree.

There is no externally supplied row summary, edge witness or proof-skipping path.
The correctness argument remains S+delta*I−T SDD, hence S>=T−delta*I. With
r>=max_i(T^-1)_ii, b=up(n*r), and q=up(delta*b)<1, the native result bounds

    ||A^-1||inf <= up(b/down(1-q)).

The implementation pays its own b in the deficit factor. It neither imports the
older refined denominator nor assumes original M-matrix signs or symmetry.

## Outward floating arithmetic and interval terminal block

Every positive reciprocal, addition and multiplication is followed by nextafter
toward positive infinity and rejects nonfinite results. Denominators are rounded
down and must remain positive. The compile flags prohibit fast-math and request
rounding-aware behavior. No trial approximate inverse or residual size is accepted
as proof. Tiny zero products can become the smallest positive subnormal; this
adds conservative widening relative to the Python implementation.

The terminal midpoint remains a separate witness. For every exact supplied
interval entry, the native code encloses both endpoint-minus-midpoint differences,
sums their absolute radii by row upward, and obtains rho>=||Delta||inf. It requires
K*rho<1 and returns up(K/down(1−K*rho)). This supports nonsymmetric independently
varying terminal intervals; it makes no row-norm-to-spectral-norm inference.
Separately rounded original terminations are therefore covered by the complete
operator interval, not replaced by an assumed exact rank-one identity.

Actual residual, whole distributed termination energy and reaction evaluation
remain in the existing resolution functions used by the bounded fixture. A valid
inverse bound can still yield INCONCLUSIVE in the weakly grounded case.

## Python/native boundary and binding

A pointer-capacity gap was identified and closed during the implementation/review
round. The adapter now checks exact metadata before entering C: CSR dimensions,
actual data/indices lengths, indptr length n+1, one-dimensional contiguous aligned
buffers with exact dtypes, coupling shape, terminal maps and live virtual layout.
The descriptor uses actual data.size rather than trusting a.nnz derived from an
unvalidated row-pointer endpoint. Strict midpoint/interval float types are checked
before creating the small copies, so extended/Fraction inputs are not silently
rounded. Native code owns the full coefficient and canonical-index scans.

The adapter binds original input bytes, context and intervals before the call,
then validates metadata and hashes the CURRENT live objects afterward. It does
not compare a stale alias when a.intervals is reassigned. Persistent coefficient,
context and interval-object changes refuse. The witness digest includes actual
returned parent/edge bytes, root and ground plus the bound identities.

Stable exclusive input ownership remains a prerequisite: ctypes CDLL releases
the GIL, and before/after hashes alone cannot prevent concurrent resize/use-after-
free or detect every adversarial transient mutation. Raw C callers must provide
buffers with the declared capacities; the Python boundary is the capacity gate.
The prototype does not claim a production snapshot/admission protocol.

Nonzero native status is always refusal; no partial numerical output is promoted
by the adapter. Invalid counts, pointers, layouts, coefficients, connectivity,
grounding, deficit or interval gates leave failed work visible. Fixed128 scratch
is conservatively charged throughout the invocation; no fictitious buffer release
or original-size byte fit is claimed.

## Independent oracle and adversarial coverage

[independent-native-forest-oracle.py](independent-native-forest-oracle.py) declares
an independent raw ctypes ABI. Its structural reference uses component SETS and
explicit tiny Fraction adjacency, not the native union-find, pointer reversal or
path routine. It verifies actual native parent/edge sets and paths, in addition to
inverse bounds.

104 structural/energy cases pass: heterogeneous forced nonroot reroots,100 seeded
mixed-sign nonsymmetric graphs with real small deficits, and a single-vertex
control. All actual selected edges agree with the independent selection, every
parent chain reaches the correct root, and exact tree-energy and original inverse
bounds are enclosed. Widely differing conductances ensure that edge-rotation bugs
cannot hide behind unit-grid tests.

Three coupled fixtures and all16 terminal-interval endpoint combinations each
supply51 exact complete-operator checks:PASS. A separate shared-terminal,
noncontiguous-mapping fixture also passes its exact inverse check. The raw API
passes12 refusal controls covering malformed counts/pointers, one-sided support,
singular/disconnected/indefinite systems and malformed/nonfinite terminal data.
Six malformed capacity/type cases are independently blocked BEFORE native entry;
a NaN coefficient reaches native validation and is refused there as intended.
Three persistent mutation injections—matrix, context and replacement of the live
interval object—are independently rejected.

The entire oracle passes both the optimized build and an additional UBSan build
with halt-on-error and no sanitizer diagnostics. Four author tests were separately
rerun:PASS, observed0.900s. All runs retain the established512MiB address-space,
20CPU-second,30wall-second and one-thread constraints. Temporary shared objects
are deleted; compiler, flags and actual binary hashes are retained in
[optimized results](independent-native-forest-results.json) and
[UBSan results](independent-native-forest-ubsan-results.json).

## Scope of acceptance

The exact helper, forest recurrence, virtual operator access, outward bounds and
binding checks have independent bounded evidence. The tested native entry remains
limited to128 total coordinates and eight terminals. Payload counts and these
small timings do not prove full retained-pipeline memory, aggregate reserve,
original input preallocation, guard deadlines or production counter eligibility.
Those require the separate resource/admission work; no original-data probe is
justified by mathematics acceptance alone.

| Reviewed file | SHA256 |
| --- | --- |
| fixture/native_forest.cpp | ac3b909e2e8ed2bce7b4bafe4328b19421f710868b20c006c1ae50cedabb2e3e |
| fixture/native_forest.py | 39cf24680a643cf240b845c05224d5b0ac647fd3958956734a3a1b12c4a807f7 |
| fixture/test_native_forest.py | a1ddb30b983306c97576f07fbe8c711c1d50c05adca76faf92dda41ca3cb43da |
| fixture/native_exact.cpp | 9d210ba9b29a2c463b814cd9ed3f50f4a45989ad27fb076d3d43db7f01a0aff3 |
| independent-native-forest-oracle.py | ea162810cb1d3315d6d6c2d3b0222d161d0f617929217e024e579559a81c270d |
| independent-native-forest-results.json | e7e04976e2baaa35b7f5a84c78ffacc7a100e16bef244086de434efd69f41d5d |
| independent-native-forest-ubsan-results.json | a49114017cc8db19a85a97573a2ed873168cd8d9dcf3fad7a907ac7fd417971d |
