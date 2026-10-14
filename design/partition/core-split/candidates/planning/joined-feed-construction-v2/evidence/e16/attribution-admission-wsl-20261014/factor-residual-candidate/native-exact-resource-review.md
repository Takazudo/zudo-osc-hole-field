# Independent resource review: bounded native exact scalar/row helper

Reviewer `/root/resource_review`, 2026-10-15 JST. Source review and independent
bounded local compilation/tests only. No original arrays, diagnostic, baseline,
qualification, request reuse, pinned solver edit or host change.

**Verdict:** accept this native helper increment for bounded local differential
work. It exposes actual limb loops and finite storage rather than charging one
native call as one operation. It is not a complete native forest implementation,
not an original-size throughput qualification and not a production fit claim.
The next integration must retain complete-loop counters and original pipeline
preallocation constraints, rather than extrapolate from these scalar tests.

## Reviewed source and independent build

- `fixture/native_exact.cpp`: `9d210ba9b29a2c463b814cd9ed3f50f4a45989ad27fb076d3d43db7f01a0aff3`
- `fixture/native_exact.py`: `2b864bdcda4beec10fd556bad751d4c8e2493316876e5746f2c5acab24a8d06b`
- `fixture/test_native_exact.py`: `30f4aa2c3f1161b52de99fe8e25cdcac70bbc850ebe2c87ba301223fb985d2ff`

Independent freshly compiled binary SHA256:
`b3d26f3ab2c6e5bc3d028f9245fff945afe004b3c94dfc5b3381dafcd34dd23a`.
Compiler: Ubuntu GCC13.3.0 (`c++ 13.3.0-6ubuntu2~24.04.1`). Flags:
`-std=c++20 -O2 -fno-fast-math -frounding-math -fPIC -shared -Wall -Wextra -Werror`.
The test-owned temporary directory and shared library are cleaned after the run;
no generated binary is retained in the repository or installed globally.

Four tests PASS independently (0.414s unittest time, including fresh build),
established numerical venv, one thread, outer30s timeout and inherited512MiB
address-space/20CPU-second limits. The helper row count remains<=128 and the
cumulative native arithmetic cap200,000 declared units. The500 seeded finite
binary64 cases plus exact carry/borrow/cancellation/floor/extreme controls use
independent Fraction references. Grid rows retain exact equality with the fixed
Python verifier; malformed ABI values, nonfinite input and cap exhaustion refuse.
Independent mathematical review is a separate record.

## Native memory and ABI boundary

An exact value has a fixed34-word uint64 buffer (2176 bits), used-word count,
sign and exponent. There is no arbitrary-precision heap library, dynamic limb
array, matrix factorization or system solve. Alignment refuses before exceeding
the fixed buffer; exponent and canonical-value checks precede arithmetic.
`used<=34` is checked before indexing the last active word, and finite binary64
and top/low-word invariants protect width/normalization operations.

On the reviewed build, the value ABI structure is288 bytes and Stats is72 bytes;
ctypes verifies those C-reported sizes before calls. The wrapper owns valid
buffers and checks matching row lengths/count<=128. At that cap the two copied
binary64 row arrays occupy2048 bytes, plus output value and temporary Python
objects. That row-copy ABI is deliberately tiny; it is not a zero-copy original
CSR implementation. C functions cannot independently discover arbitrary pointer
buffer lengths, so ownership/length validation remains the caller contract.

The native arithmetic uses a bounded number of fixed-size local values; there
are no order-dependent native allocations. Exception/runtime/loader and Python
conversion overhead remain under actual process limits, not falsely included in
a fixed34-word value claim. A complete native forest still needs its own stack,
array, source-input and interface lifetime accounting.

## Accounting fixes established by review

The initial version folded double conversion/ldexp into integer units. They now
appear in a separate cumulative `floating_calls` field. Return/assignment/sign
helper traffic was also incompletely visible: by-value sign helpers were removed
from the row loop, ABI output zeroing is charged, and a conservative fixed-buffer
copy-word envelope is recorded. Compiler copy elision may reduce actual traffic;
it cannot justify removing that envelope.

`initialized_words` and `copied_words_upper` count34-limb payload words. They do
not silently include the16 metadata/padding bytes in the288-byte structure. If
converting these complete-buffer counts to a full-structure traffic envelope,
use `(word_count/34)*288`, not `word_count*8`. Logical word visits and buffer
initialization/copy are reported separately, rather than pretending all writes
are arithmetic or every limb visit is a complete machine instruction count.

Review found that validating a wide value did not initially propagate its width
to a contribution scope when `add(wide,zero)` took a shortcut. The final code
records the validated operand width and peak before such returns. The regression
`1-2^-100` followed by a zero symmetric term charges four proposed word units
(two per term), despite the second term taking the shortcut. Additions likewise
record aligned/pre-normalized operation width before cancellation. Failed row
scopes retain their accumulated proposed contribution count.

Stats entry plausibility checks reject preloaded implausible uint64 totals before
unsigned wrap can hide work. Legitimate arithmetic stays far below uint64 range
under the fixed unit cap and bounded loops. A cap-exceeding charge remains
recorded; it is not rolled back. Repeated calls in a grid share Stats without
reset. Separate randomized scalar cases have separate explicitly identified
meters and a reported sum; they are not a split original operation.

Native `bit_work_envelope` is the sum of squared limb-kernel widths, normally
64-bit words, with actual limb loops charged. Python's earlier metric counted
whole-significand kernels at their full width. These are explicitly different
logical envelopes, neither machine instructions nor production Schur updates.
Their numerical ratio is not a speedup or approved production-counter conversion.
Peak arithmetic significand width, limb visits, initialized/copy words and
floating calls remain visible alongside proposed row contributions.

## Independent row-only resource evidence

| Grid | Native kernel units | Native limb bit-work envelope | Limb visits | Initialized words | Copy-word upper | Proposed row contributions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 5064 | 20742144 | 7618 | 14144 | 30464 | 48 |
| 8 | 23560 | 96501760 | 35554 | 65280 | 140352 | 224 |
| 9 | 30284 | 124043264 | 45713 | 83844 | 180234 | 288 |

These rows need no floating coefficient-floor conversion, hence their
`floating_calls=0`; the floor helper's conversions are separately exercised by
other tests. All three grid cases have recorded peak arithmetic width64. The
500 scalar-control cases sum78,611 independent-case kernel units. The table is
one exact row-verification pass, not forest selection, root/deficit reductions,
path recurrence, interval perturbation, hashing or complete coupled screening.

The native helper has not yet replaced those loops in the existing prototype.
Calling its current per-row ctypes wrapper from Python still copies row arrays
and converts exact outputs to Python integers. Do not present that wrapper as
an original-sized native execution strategy or hide its work behind a single
foreign-function call.

## Required next source work and admission consequence

Port the actual verifier-owned forest orchestration to a bounded native path,
with virtual original rows, checked reverse lookup, root/deficit reduction,
union-find/reroot/index accounting, fixed typed-array overlap and outward path/
interval calculations. Preserve every fine ledger and the proposed width-aware
contribution scopes; a whole library call is never one update. Differential
checks must cover all existing row, tree, nonroot weighted reroot, nonsymmetric,
whole-termination, weak-ground, failed-scope, mutation and resource-cap cases.
Original execution remains absent from this work.

The companion `preallocation-guard-design-review.md` gives the source-only
constructor gate: `R_upper=f+i+4*sum(max(taps-1,0))+sum(support_length^2)` before
held-mask/board_parts allocation. Implement the wrapper guard without modifying
pinned finite_solve/finite_adapter numerical code. Named array bounds and raw
counts are not a full heap proof: native sparse-sort/prune workspace, decoded
object baseline, other-board B/Y, original KB solve/refinement and full Assembly/
physical accounting still need a complete shared envelope.

Neither successful scalar tests nor the native row-only count establishes a
viable155-second worker computation within the unchanged180-second guard-entry
contract,1216MiB worker,2GiB aggregate, zero-swap,64MiB output and certificate
limits. **No original-data characterization or full qualification is justified
at this helper checkpoint.** The remaining authorized work is concrete native
orchestration and preallocation-source integration, not an external planning
prompt or a new baseline.
