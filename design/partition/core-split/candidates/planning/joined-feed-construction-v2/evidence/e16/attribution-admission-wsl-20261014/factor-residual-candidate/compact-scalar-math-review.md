# Independent complete compact-scalar mathematics review

Reviewer `/root/math_review`, separate from implementation,2026-10-15 JST.
No original data, signer/admission operation or campaign work. The preceding
row-only oracle/results and review remain historical evidence.

**PASS for the complete compact exact-scalar path, bounded helper validation and
unchanged tree-coercivity/interval proof.** Production cost, original applicability
and attribution remain unresolved; reduced synthetic bit-work is not admission.

## Representation and exact proof integration

The complete path retains the canonical exact dyadic(m,e) representation reviewed
in compact-row-math-review.md, and now carries it through root selection, maximum
deficit, symmetric tree-edge values, conductance checks and directed conversion.
Compact row output no longer needs a full fixed-denominator shift in that path.
The optional as_fixed=True interface remains an arithmetic control; the fixed
implementation remains selectable and independently comparable.

Every compact tuple is validated before zero shortcuts, arithmetic or shifts.
Nonzero significands are odd, zero is(0,0), both components are built-in integers,
width is<=2176 and exponent is within[-1075,2048]. Normalization checks the OUTPUT
exponent as well. Oversized negative inputs are width-checked before allocating
their absolute-value copies. Raw IEEE decoding and every alignment are exact.

Comparison first compares signs. For equal nonzero signs it compares the exact
leading-bit positions e+bit_length(m). Unequal positions determine magnitude
order without alignment. If positions agree, exact significands align at the
smaller exponent, with the required width checked before either shift. Negative
sign reverses magnitude order. This returns exact order, including zero, negative
values, widely separated exponents and cancellation-generated small margins.

The positive conversion truncates the significand to at most53 bits, converts that
integer exactly to binary64 and applies a power-of-two scale. It does NOT assume
that libm scaling rounds downward: the resulting finite positive binary64 is
independently decoded and compared to the exact compact input. A result above
the input refuses, including upward-rounded subnormal cases. Underflow to zero
or overflow refuses. This accepted downward witness is sufficient for positive
root ground and tree conductance; maximality is not a theorem requirement.

For the nonnegative deficit upper bound, exact zero returns zero. Otherwise the
conversion is followed, when necessary, by one nextafter toward infinity and an
independent exact check that the finite result is >=the exact deficit. If a useful
upper conversion is unavailable, the certificate refuses. No tiny deficit is
clamped away. Root/deficit comparisons and edge verification therefore preserve
all premises of the preceding shifted-tree proof with no new rounding premise.

The same exact values produce the same chosen root, tree coefficients, packet
hash and final bound in the fixed and compact modes on the tested controls.
Public certificate binding and virtual input validation are unchanged.

## Separate independent oracle

[independent-compact-scalar-oracle.py](independent-compact-scalar-oracle.py)
retains its own results in
[independent-compact-scalar-results.json](independent-compact-scalar-results.json),
without overwriting the row-only result. It checks:

-3000 exact comparisons on1000 canonical pairs spanning up to2176 significand
bits and exponents[-1075,2048], using Fraction as the independent reference.
-450 accepted downward conversions and449 accepted upward conversions satisfy
exact bounds.1101 conservative underflow/overflow/rounding conversion refusals
are retained rather than reclassified as successful arithmetic.
-24 malformed tuple/type/exponent inputs to the new helpers refuse.
-The retained independent controls pass again:2000 IEEE decode checks,6000 exact
operations,300 exact nonsymmetric row margins and200 exact inverse bounds on
100 signed/nonsymmetric matrices with actual small deficits.
-Six complete virtual coupled fixed/compact results (strong grounding, weak
 grounding and nonsymmetry) have identical witness hashes and bounds and contain
the exact original inverse norms. Their physical interpretation remains the
separately tested original resolution-function path; no original-data result is
inferred.

Four main compact tests independently pass, observed0.292s. The oracle runs under
512MiB address-space,20CPU seconds,30wall seconds and one numerical-library thread.
Exact references and dense tiny inverses are test-only and never read by production.

## Findings and boundaries

The row-only malformed-shortcut and normalization-output range findings were
fixed before this complete-path review. The preallocation absolute-value finding
is also resolved. No remaining mathematical blocker was found in comparison,
conversion, representation normalization or proof integration.

Resource accounting remains a separate review: compact validation, normalization,
alignment, comparisons and conversions are actual work even when coefficients
happen to be small. Operand-dependent bit envelopes are not hardware instruction
counts or an approved production scalar-update mapping. A kernel width reduction
does not establish full-pipeline memory/time eligibility or justify a diagnostic.

A possible next one-pass architecture is mathematically sound only if its public
entry owns exhaustive original-row evidence, stable bound inputs and subsequent
independent tree validation. Removing the redundant row pass does not permit a
public untrusted summary/skip-proof flag, a free preprocessing phase or a dropped
cost. That architecture is not implemented or qualified by this review.

## Inspected identities

| File | SHA256 |
| --- | --- |
| fixture/prototype.py | 4c0601b03f061cdb73186577520df39c789053c47a5ef1a27db6bc4a7a6f0808 |
| fixture/test_compact.py | 52664ce766ba43d3027e0202867a7fe854f500a5a85dc71cdc7a152e4b1e12d9 |
| independent-compact-scalar-oracle.py | 3423b442783496c6bb472ccd9026c1c5e7801cb35f722dd3fd83412593f4834f |
| independent-compact-scalar-results.json | 1c275bfb6a45587cc55c0705067a415b14d61461616e49d60ba77f0f7fd5e16b |
| retained independent-compact-oracle.py | a2e84dee7074564fa2071ddc89e9f18facd6d2505b0936235fc71a87b57954db |

Doc-only receipt: the coordinator subsequently clarified the compact row helper's
docstring; prototype SHA256 became
f6a9b7582320414adc607a97e2c046f68ccd3c49dc3b5e758891e1dec38e6dd6.
No executable mathematics changed. The retained independent result identifies
its actually executed4c0601b0... version; it is not rewritten to imply execution
of another source hash. The coordinator reports all44 tests passing and the four
compact tests rerun after that clarification.

Metadata-only receipt: subsequent result fields explicitly name auxiliary tree
order, edges and construction float/integer work, superseding misleading generic
test snapshot zero-auxiliary fields. Prototype SHA256 became
79b8fa4b57b2d38a3780496b9aeac5ba0aa7a1c696b770a2ceb43d7bad96fc44.
No numerical formula changed; the coordinator reports the four compact tests
passing. The independent result above remains tied to its actual execution hash.
