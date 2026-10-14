# Independent native exact-helper mathematics review

Reviewer `/root/math_review`, separate from implementation,2026-10-15 JST.
Synthetic continuation after6832a1e2. No original inputs, original-size forest,
request, signer, admission or campaign operation. No dependency was installed.

**PASS for the bounded native exact scalar/row helper and checked C ABI.** This
is not a native complete certificate, native forest,180-second fit or original
qualification. Those remain unimplemented/unestablished by this increment.

## Reviewed representation and operations

The native compact dyadic is a fixed34-word unsigned64-bit magnitude, used length,
sign and exponent, representing the same exact m*2^e as the Python prototype.
Validation checks used<=34 before any width lookup, canonical sign/zero, odd low
significand bit, nonzero highest used word, zero unused words and exponent bounds.
Compile-time assertions explicitly require IEEE binary64 radix2,53 significand
bits, exponent range and eight-byte storage. ABI sizes are checked by ctypes.

The review checked these implementation details against the exact representation:

- clz/ctz are reached only with nonzero words. Whole-word and partial shifts
  explicitly avoid shifts by64 and check output width before array insertion.
- Addition carries are formed from two unsigned additions and their overflow
  comparisons; subtraction borrows use two unsigned subtractions and comparisons.
  No signed overflow is used to implement exact magnitude arithmetic.
- Normalization preserves the value while removing zero high words and powers of2.
  Exact cancellation resets both sign and exponent to canonical zero.
- Symmetric half-sums operate on the exact integer sum. In particular,
  half(maxfinite,maxfinite) works despite its intermediate sum exceeding the
  binary64 finite range; no floating sum replaces that exact intermediate.
- Exact comparison uses sign and leading-bit positions before bounded alignment.
  A2176-bit comparison is supported, while an addition requiring an extra
  out-of-cap carry slot conservatively refuses before allocation.
- The floor helper extracts at most53 significand bits, performs binary64 scaling,
  and independently decodes/compares its finite positive result to the exact
  input. Upward subnormal rounding, underflow and overflow refuse rather than
  becoming false downward bounds.

The row helper computes the exact diagonal minus the sum of absolute exact
symmetric half-sums for up to128 supplied off-diagonal pairs. It does NOT prove
that those supplied pairs correspond to an original matrix; the full operator
binding and traversal proof remain the later certificate layer. This helper
neither factorizes nor solves a matrix and reads no oracle result.

## C ABI and failure semantics

All exported arithmetic calls return a status; the Python wrapper checks it
before interpreting any output. Exceptions are caught at the C boundary. Nonzero
status means no result is accepted, whether an output buffer was zeroed or retains
previous bytes. Null arguments, malformed raw structs, nonfinite binary64 values,
row-count overflow and cumulative kernel-cap exhaustion refuse.

Stats remain cumulative. Failure does not reset consumed kernel units. Preloaded
near-UINT64_MAX counter values are rejected before counter addition, preventing
wraparound. Native declared kernel units, limb visits, initialization, conservative
copy-word envelope and floating calls are separate measurements. They cannot be
numerically substituted for Python kernel counts or production scalar updates.

During review, full operand width was restored to proposed contribution tracking
for zero shortcuts: a wide running margin followed by an exact-zero term must not
collapse to one word. The independent regression1−2^-100 followed by a zero term
records four word contributions. Fixed-buffer copies are exposed as a conservative
envelope rather than assuming compiler copy elision.

## Independent raw-ABI oracle and sanitizer

[independent-native-exact-oracle.py](independent-native-exact-oracle.py) declares
its own ctypes structs/call signatures and constructs raw limbs, bypassing the
wrapper's from_pair validation for malformed tests. Fraction is its independent
reference; Python compact operations provide an additional cross-check.

The optimized build passes:

-1000 raw-bit IEEE decode checks and1002 exact half-sums, including signed zero,
subnormal boundaries, largest finite values and exact cancellation.
-17 explicit long carry/borrow successes and two bounded-width refusals, including
64-bit boundaries and near2176-bit limits.
-1000 exact comparisons across full-width canonical operands.
-232 accepted floor conversions checked against Fraction/Python and268 conservative
conversion refusals, plus explicit smallest-subnormal and largest-finite controls.
-200 exact row margins with0 through128 off-diagonal terms and widely separated
exponents.
-11 raw malformed-struct/nonfinite refusals, nine preloaded-counter overflow
refusals, a129-term row refusal, null-stats refusal and cap persistence.

The same independent oracle passes a second build with undefined-behavior
sanitization and halt-on-error. No sanitizer diagnostic occurred. The main four
native tests also independently pass, observed0.403s. Runs retain512MiB address-space,
20CPU-second,30wall-second and one numerical-library-thread bounds. Builds use
C++20/O2, no fast-math, rounding-math awareness and warnings-as-errors. Compiler
identity and actual binary hashes are retained in the result files. Temporary
shared objects are deleted by their owning temporary-directory scopes.

[Optimized results](independent-native-exact-results.json) and
[UBSan results](independent-native-exact-ubsan-results.json) preserve actual runs.
These are correctness tests, not original-size runtime extrapolations or a
full-pipeline memory measurement. Original applicability and attribution remain
unresolved, and no diagnostic is warranted by this helper review alone.

| Reviewed file | SHA256 |
| --- | --- |
| fixture/native_exact.cpp | 9d210ba9b29a2c463b814cd9ed3f50f4a45989ad27fb076d3d43db7f01a0aff3 |
| fixture/native_exact.py | 2b864bdcda4beec10fd556bad751d4c8e2493316876e5746f2c5acab24a8d06b |
| fixture/test_native_exact.py | 30f4aa2c3f1161b52de99fe8e25cdcac70bbc850ebe2c87ba301223fb985d2ff |
| independent-native-exact-oracle.py | 4b4202e0190b93dc0a17ec04c37e3864dce1becc9165a2cc49c00bca2b1d9faa |
| independent-native-exact-results.json | 6926bc0e70da5da06fea001ef0ab42295dd350ff720bfd909d6b5f6f00ca4e4d |
| independent-native-exact-ubsan-results.json | e99f288cf0e60efadd8870cabfb718a9ffb00fce3607c9e719d3e10c167652d2 |
