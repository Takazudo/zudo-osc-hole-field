# Bounded native exact scalar/row kernel

Continued after6832a1e2. The same compact dyadic arithmetic now has a bounded
C++20 implementation using34 fixed64-bit limbs, with no Boost/package install,
original-data reader or matrix solve. A small ctypes adapter builds in a fresh
owned temporary directory, checks ABI sizes and all return statuses, binds
source/compiler/flags/binary hashes, and removes build artifacts after tests.
The temporary manual compiler output was also removed. No host setting changed.

Native arithmetic verifies IEEE binary64 assumptions, guards zero before bit-count
intrinsics and avoids shifts by64. Carry/borrow use defined unsigned64 arithmetic.
Width is checked before alignment; cancellation canonicalizes zero. Coefficient
flooring is accepted only after exact comparison. Nonfinite values, malformed
rawABI structs, overflow/underflow and cumulative budget violations refuse.
Near-UINT64_MAX metric states are rejected before counters can wrap.

The helper retains explicit limb-kernel, limb-visit, fixed-buffer initialization,
conservative copy-word, floating-call and proposed width-weighted contribution
metrics. Its native limb-width squared envelope is NOT the Python whole-significand
envelope or a CPU instruction count. Full operand width is captured even when
adding zero avoids limb work: a wide margin followed by a zero term still pays
its two-word contribution. This accounting finding was fixed and independently
tested. Struct-copy/init word counts describe34limb payload words; a full dyadic
struct is288bytes including metadata/padding, so converting struct traffic to
bytes must include those bytes rather than multiply payloadwords by8 alone.

Validation:4 native helper tests PASS, compiling with C++13.3.0,O2,no-fast-math,
frounding-math and warnings-as-errors. Independent optimized and UBSan oracles
check1000 IEEE decodes,1002 half-sums,17 carry/borrow cases,1000 full-width
comparisons,232 accepted floors/268 conservative refusals,200 exact rows,
rawmalformed/null/cap cases and9 near-wrap metric inputs. Scalar/row order remains
bounded128;2176bit and200000 native kernel ceilings remain enforced. No native
call is counted as one opaque numerical operation.

See native-exact-math-review.md and native-exact-resource-review.md plus separate
optimized/sanitizer oracle results and fixture/native-exact-results.json. Python
forest/proof source and its prior tests are unchanged by this helper-only increment.
The native scalar/row helper is correct within this bounded scope; it is not yet
the complete native forest, original qualification or production attribution.

Parallel source review derived the raw preallocation count
R<=Kg_face.nnz+Kg_inner.nnz+4*sum(max(len(taps)-1,0))+sum(terminal_support_length²).
It uses actual decoded metadata under the eventual guard, not original-data
probing now. The reviewed insertion points precede held-mask and board_parts
allocations; finite_solve/finite_adapter numerical construction stays unchanged.
The named conversion-array envelope is only part of worker memory; unknown
SciPy/Python workspace and retained-input/solver/Y/B/mesh overlap cannot become
acceptance. See preallocation-guard-design-review.md. This guard is not yet coded.

Next active work: implement the native complete virtual-row/verified-forest/path/
interval loop with the same complete counters and input bindings, then implement
and review the metadata-only raw-stamp guard and full resource envelope. Keep
fixture limits and all original operation caps. No original characterization,
qualification or production is eligible from helper success alone.

Ledger remains15/24 diagnostics,2/3 baselines; no new baseline or diagnostic,
request, grant, key operation or cleanup debt. KEEP_K1402_INCUMBENT. The selected
attribution objective and local development assignment remain active.
