# Independent native forest resource review

Verdict: the bounded synthetic native port is reviewable and retains separate fine counters. It is not a production implementation, resource qualification or permission to read originals. No original-data operation was performed for this review.

Reviewed source SHA256:

- native_forest.cpp: ac3b909e2e8ed2bce7b4bafe4328b19421f710868b20c006c1ae50cedabb2e3e
- native_forest.py: 39cf24680a643cf240b845c05224d5b0ac647fd3958956734a3a1b12c4a807f7
- test_native_forest.py: a1ddb30b983306c97576f07fbe8c711c1d50c05adca76faf92dda41ca3cb43da
- included native_exact.cpp: 9d210ba9b29a2c463b814cd9ed3f50f4a45989ad27fb076d3d43db7f01a0aff3

Independent fresh temporary build and four tests PASS, 0.870 s, with one BLAS thread and outer 30-second limit. First invocation without thread environment failed loading the shared library under the fixture address-space limit before executing tests; native_forest imports numpy before downstream test fixtures configure thread counts. This was a test startup ordering finding, not a numerical failure. The final test entrypoint sets all three thread variables before numpy imports; an independent fresh invocation without external thread settings now passes all four tests (0.886 s). Temporary build cleanup completed.

## Actual work and lifetimes

The final adapter first validates exact ndarray buffer lengths, dimensions, native dtypes, alignment and contiguous layout before hashing or passing pointers to C. In particular, indptr must have n+1 elements and indices must have data.size elements. Descriptor nnz comes from data.size, not unchecked indptr values. Small terminal layouts and stale virtual offsets are checked independently. Native validation then checks indptr ranges, monotonic canonical column indices and every finite, nonzero stored coefficient before any numerical lookup. The repeated interpreted coefficient scans have been removed; the adapter retains two metadata validations and two input hashes. Final regressions include shortened indptr/indices and out-of-range column indices. This resolves the reported C pointer-capacity boundary gap. These checks assume input buffers are not concurrently resized or mutated during the call; final hashes detect persistent changes, not arbitrary adversarial transient writes.

The native implementation borrows these CSR and coupling arrays, validates all stored coefficients, then traverses original rows once for exact margins. Reverse entries use bounded binary search; terminal rows use borrowed coupling columns. It never builds a global joined CSR, transpose, residual or inverse. The row verifier itself selects checked negative edges, and union-by-size reroots smaller components. Root/path work occurs after this same checked forest; there is no uncharged auxiliary solve.

Six phases retain native exact-kernel units, per-limb bit-work envelope, limb visits, initialized and conservatively copied words, floating calls and proposed scalar contributions. Index visits and coefficient reads are distinct counters. Scope destruction charges failed partial work. Per-phase kernel caps and cumulative post-row/final checks bound this fixture; cumulative checks can detect an overrun after the current bounded row, not interrupt at exactly the aggregate limit. Counter units are not interchangeable with the old production scalar-update convention.

Fixed ForestScratch is **2688 bytes throughout**, including DSU, sizes, stack, paths and state simultaneously. Result is 608 bytes and each board descriptor 56 bytes. Parent and edge outputs add 12n bytes; copied terminal columns and midpoint/lower/upper arrays are separately reported. The compiled function also has fixed exact-number temporaries and compiler stack frames; these are not covered by ForestScratch alone. Adapter Python object/array headers, validation temporaries, digest serialization and witness tobytes concatenations remain outside payload sums. The report explicitly disclaims a full byte-memory proof. In particular, the Python port's release-based 25n claim does not apply here.

| Case | kernel units | float calls | proposed contributions | index visits | coefficient reads |
|---|---:|---:|---:|---:|---:|
| grid4 | 6376 | 144 | 88 | 2041 | 192 |
| grid8 | 28808 | 528 | 360 | 6793 | 864 |
| grid9 | 36926 | 664 | 458 | 8501 | 1107 |
| coupled strong | 2095 | 96 | 38 | 1064 | 80 |
| coupled weak | 2093 | 96 | 38 | 1064 | 80 |
| coupled nonsymmetric | 2086 | 96 | 38 | 1064 | 80 |

Coupled midpoint construction adds four proposed contributions, giving 42, and remains separately visible. Grid9 has 65,557 limb visits, 972 owned array payload bytes, 4756 borrowed payload bytes, traced Python peak 14,267 bytes and measured native-adapter invocation 0.000931 s. Process high-water RSS was 67,488 KiB; this includes runtime/imports and is not incremental forest memory. These timing and traced-heap values are retained from the first reviewed adapter; final metadata-only validation changes wrapper cost without changing the native counters in the table. These tiny measurements do not establish original-size latency. Refused cases preserve attempted phase work (e.g. deficit: 497 kernel units, nine proposed contributions).

## Mapping and engineering decision

The proposed coefficient-destination recurrence ledger remains a defensible *local proposal*: each off-diagonal exact average/absolute subtraction has one destination recurrence weighted by maximum actual operand/alignment/result width; floor conversions, paths, norms and intervals have separate scopes. Copy/decode/index and max-selection remain visible separately, matching the distinction in the old scalar-update convention. Native limb kernels must never be recast as one opaque library update. This review does not approve mapping that proposal into live admission or establish fit under 20M updates.

The present source unconditionally refuses n>128 and retains a 200,000 kernel-unit synthetic bound. It cannot run the original order. A production-sized implementation needs checked dynamic packed buffers, certified stack/workspace allowance, whole-pipeline overlapping B/Y/original inputs and physical verification, source-bound conversion/counter convention, and hard guard-entry deadline accounting. No extrapolation from the millisecond fixture supplies those prerequisites. Both-board memory and original raw stamp count remain necessary, not just the forest's small coefficient count.

One useful bounded characterization question is now precise: **what are each original board's descriptor-derived R and maximum terminal support square, before held masks or raw stamp allocation?** If this conservative named-array envelope exceeds the worker allowance, this preflight refuses the unchanged constructor path; the next source work must tighten the justified envelope or change allocation strategy. An upper bound exceeding a cap does not prove actual allocation exceeds it. If it fits, it only permits completing the missing native/Python/allocator/retained-pipeline envelope; it does not approve a certificate. No numerical coefficient values are necessary for that question. The new helper implements the source-only counting kernel, but no separately bound metadata-only admission path exists yet. Such a path must stop before all numerical construction, retain existing load/guard limits, prove metadata visit/output bounds, and obtain exact-request review/grants before consuming any diagnostic. Do not issue a full qualification to obtain this count.
