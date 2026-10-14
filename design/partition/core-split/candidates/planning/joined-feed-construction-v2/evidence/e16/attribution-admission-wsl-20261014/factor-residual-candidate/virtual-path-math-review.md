# Independent mathematics review: virtual joined rows and path-only bound

Reviewer: `/root/math_review`, separate from the implementation coordinator.
Synthetic continuation after94450d79. No original operator, signer, admission
request, campaign charge or production solve was accessed or changed.

**PASS for the bounded virtual-operator representation, packed witness validation
and path-only coercivity formula.** This is a mathematical implementation review,
not approval of original-size cost, structural applicability or admission.

## Exact operator represented by the view

JoinedRows references existing board CSR A blocks and dense binary64 coupling B
blocks with explicit sorted global terminal-column mappings. It copies only the
small terminal midpoint table. A free row emits its original board row followed
by its actual mapped B values. A terminal row scans the relevant B columns and
emits their transposed coefficients followed by the small terminal midpoint row.
There is no full joined CSR or full B transpose in this certificate path.

Sparse omission of zero B/D values preserves exact matrix meaning. Both boards
may share terminal columns: the whole-operator proof has no old Schur maximum-
block restriction. Noncontiguous terminal mappings preserve their global indices.
Every nonzero original A coefficient still requires a structural reverse entry;
one-sided support explicitly refuses. This is conservative applicability, not an
implicit claim that the original matrix is symmetric.

The represented midpoint operator is bound by a fresh content hash of both A
arrays, each B array, terminal maps and the midpoint table. The terminal intervals
are bound separately through the existing interval-wrapper context and final
interval-operator digest. Thus a midpoint certificate is not mislabeled as an
interval-operator certificate. Both types of identity are recomputed when used.
The interval perturbation proof from the preceding review is unchanged.

Two findings were fixed before this review passed:

- Cached global offsets/shape could become stale after mutating a referenced CSR's
  dimensions. Validation now recomputes and compares the coordinate layout.
- Live terminal interval rows could be shortened or malformed after construction.
  Validation and interval_entries now recheck every row and ordered finite float
  endpoint tuple, rather than silently producing a different replacement set.

Input mutation between separate calls is therefore detected or rebound as a new
actual input. This review does not invent concurrent-mutation protection or an
original-data snapshot/admission mechanism for this local fixture.

## Path-only bound proof

Retain the same independently verified positive rooted tree T, exact symmetric-
part row deficits delta and negative-edge coefficient inequalities. Let

    r=max_i (T^-1)_ii=1/g+max_i sum_(root-to-i path)1/c_e,
    b=n*r, gamma=1-delta*b.

Since trace(T^-1)<=n*r, I<=b*T and
S=(A+A^T)/2>=T-delta*I>=gamma*T. For gamma>0, the earlier normalized-operator
Cauchy proof yields

    |e_i^T A^-1 f|<=sqrt((T^-1)_ii * f^T T^-1 f)/gamma.

For ||f||inf<=1, entrywise nonnegativity of the tree inverse gives
f^T T^-1 f<=1^T T^-1 1. Positive-semidefinite Cauchy bounds every entry of T^-1
by r, so 1^T T^-1 1<=n²*r. Consequently

    ||A^-1||inf <= n*r/(1-delta*n*r),  delta*n*r<1.

The implementation computes root-path resistances upward, multiplies their
maximum by n upward, and forms its OWN deficit factor delta*n*r. It does not
reuse the tighter trace/refined denominator without paying its computation.
The denominator is rounded down and must be positive. This mode needs no
subtree masses, trace accumulation, squared masses or trial square root.

For the unit rooted m×m grid with ground1, the bound is
m²*(1+2(m-1)):112 for4×4,960 for8×8,1377 for held-out9×9. These are looser than
the preceding refined bounds61.2536/461.129/650.889 but remain polynomial. The
older refined theorem, results and resource rejection remain historical evidence;
they are not overwritten or counted as new results.

## Packed witnesses

Parent/order use unsigned32-bit arrays and edges/path use binary64 arrays, with
actual item sizes verified. Byte hashing includes field names, array type codes,
lengths, item sizes and byte order. The verifier rejects mixed list/packed storage,
wrong widths, malformed permutations, invalid parent order, nonfinite/nonpositive
edges and excessive conductances. The root's self-parent and zero edge are checked.
A bytearray permutation check avoids sorting/copying the full order vector.

The mathematical tree and emitted path-only bound are identical for valid packed
and list representations. Buffer payload accounting is a separate resource claim:
25n bytes for parent/edge/order/seen/path excludes input storage, interpreter
objects, metadata, hashes, exact-integer scratch and retained physical-pipeline
state. This report does not promote that payload count into an aggregate fit.

## Independent oracle and execution

[independent-virtual-oracle.py](independent-virtual-oracle.py) constructs100
seeded(280) virtual operators with two nonsymmetric boards and mapped/shared
terminal columns. It compares4250 scalar row/reverse values against separately
assembled exact tiny references. Every row is sorted and duplicate-free.

For each case the refined-list, path-only-list and path-only-packed certificates
are compared against exact Fraction inverse norms at the midpoint and an
independently chosen terminal-interval corner:600 bound checks pass. Packed/list
path-only bounds are exactly equal. Dense matrices and exact solves occur only
in the tiny independent oracle, never in the candidate producer.

Additional independent tests cover stale A/B/midpoint coefficients, separately
changed interval identities, malformed live interval rows and endpoint ordering,
stale CSR dimensions, one-sided support and four fresh-hash malformed packed
witnesses. All refuse or rebind as specified. The four main virtual tests also
pass independently; they exercise grounded KA/floating KB, weak grounding,
nonsymmetric coefficients, actual residual/whole distributed energy/reaction
functions and shared terminals. Their synthetic physical dispositions do not
supply an original-data disposition.

Results and exact source identities are retained in
[independent-virtual-results.json](independent-virtual-results.json). The oracle
runs under the established512MiB address-space,20CPU-second,30wall-second and
single numerical-library-thread bounds.

## Admission boundary

No characterization request is proposed by this mathematics review. The literal
prior refined path already has a resource obstruction; the replacement's full
float, exact-integer, reverse-lookup, input and retained-pipeline costs must first
be reviewed. A small path-only float count or virtual input representation does
not establish that eligibility. Only after an executable cost-admitted path exists
should an unknown original structural property become a bounded characterization
question. Original attribution and admission remain unresolved.

## Final inspected identities

The final rerun passed all four virtual tests, observed0.075s, and the independent
virtual oracle. Explicit bounded binary reverse lookup, lookup/scan baselines and
preallocation width checks do not change the verified operator values or proof.
Circuit validation passed:68 manual inventory lines, no schematic/placement
binding, pin-asset check performed.

| File | SHA256 |
| --- | --- |
| fixture/prototype.py | d5dfc727f8f64c75f9e38bd868933e0ffbb8f31f63807e27491013d977b25930 |
| fixture/test_virtual.py | c01b8f410a9d2ddf1849f67025a33083130d0189d29fc5322d471cec6f804c7c |
| independent-virtual-oracle.py | f3efcc8fa5c34d9f8cd40fa1af21cbde46e0102d65b280ae830df2b5bc29959e |
| independent-virtual-results.json | a6647451fc9ad8779ee3268e557c712eddb3420e84032e55bd083cf01059cbfc |
