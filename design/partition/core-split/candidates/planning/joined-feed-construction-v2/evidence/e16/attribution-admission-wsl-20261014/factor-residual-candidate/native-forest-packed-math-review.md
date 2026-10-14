# Independent mathematics review: packed native forest scratch

Reviewer: separate mathematics agent, 2026-10-15. Verdict: PASS for the bounded synthetic implementation reviewed below. No original archives were accessed. This is not qualification, an original-data eligibility grant, or a production fit claim. Previous native evidence remains unchanged.

## Scope and proof

Inspected the current native C++ implementation and ctypes boundary, and ran a separate raw-ABI/Fraction oracle with optimized and undefined-behavior-sanitized builds. The storage change preserves the existing exact row proof, verified negative symmetric edge selection, forest orientation, root choice and outward path/interval calculations. No new mathematical theorem is claimed.

The exact row margins establish S + delta I >= T for S=(A+A^T)/2 and the grounded selected tree T. Downward ground/conductance conversion and upward root-path resistances give b >= n max diag(T^-1). The existing positivity check delta b < 1 and outward denominator establish the infinity inverse bound b/(1-delta b). The complete terminal-interval perturbation uses the existing generic infinity norm bound K/(1-K rho). Scratch relocation does not alter any premise or arithmetic operation in these arguments.

## Allocation lifetime inspection

OwnedArray owns each actual typed allocation through unique_ptr. Release resets that pointer before decrementing live payload. The two selection arrays remain live through final reroot, then are released before any path arrays allocate. Path, state and stack are automatically destroyed on both normal and exceptional exits. The result reference outlives every owner. Deleted copy operations prevent duplicate release accounting. Successful zero initialization is charged immediately after allocation, so an exception from a later allocation cannot erase earlier initialization work.

These observations apply to payload ownership, not allocator metadata, exact arithmetic stack frames, caller arrays, borrowed input buffers, or process RSS. The reported 13N peak is only the owned scratch payload. Parent/edge caller output arrays remain live separately. Total order remains capped at 128; no larger-input memory claim follows.

## Independent execution

Both optimized and UBSan runs passed the separate retained oracle: 103 heterogeneous/random exact tree and inverse cases plus a single-vertex control; forced nonroot endpoint reroots; 51 full coupled inverse/corner checks covering strong grounding, weak grounding and nonsymmetry; shared/noncontiguous terminal mapping; twelve raw refusal cases; malformed metadata refusal before the native boundary; and persistent matrix, context and live interval replacement detection. Fraction reference selection uses component sets and independent adjacency path evaluation rather than the native DSU/orientation algorithm.

The new raw Result declaration independently includes the appended lifetime ABI fields and checks the exported size. Every raw call, including refusals, checks zero live payload and equal completed allocations/releases. Every accepted call checks five allocations, 8N selection payload, 13N path payload and 13N peak: selection/path payloads do not overlap.

Injected failures independently cover all five allocation positions, in both builds. Completed/released counts are respectively 0,1,2,3,4; all return code 11 with zero live payload. For order 16 their observed peak payloads are 0,64,128,128,144 bytes. The second and fourth failures also verify retained initialization charges. These are deterministic injected allocation exceptions, not measurements of actual host exhaustion.

The author's current five-test suite also passed independently (2.796 seconds); this supersedes the earlier four-test description for this snapshot. No UBSan report appeared. Native binaries were built in temporary directories and removed.

## Remaining limits

The adapter still requires stable caller ownership across the native call. ctypes releases the GIL; before/after hashes detect persistent mutations but do not make concurrent resizing or transient mutation safe. This prerequisite is unchanged. Metadata capacity validation remains before native pointer traversal, with full coefficient/pattern checks in native code. No binding regression was found. Production source allocation and native order expansion require their own review; this review does not authorize them.

## Snapshot hashes

- `fixture/native_forest.cpp`: `07ece3a05b04515902f030fc817c96b3ff84c103eb1f540f794a257970c3a887`
- `fixture/native_forest.py`: `743da2678795e817a224924941a7c0195b4d143dd946daeeab7a4a7a23fef79e`
- `fixture/native_exact.cpp`: `9d210ba9b29a2c463b814cd9ed3f50f4a45989ad27fb076d3d43db7f01a0aff3`
- `fixture/test_native_forest.py`: `6a9aa6610dc37a9cfb6a56424ebd60b6218347d4130209877c63da2ce097c741`
- `independent-native-forest-packed-oracle.py`: `65654875a95950710b1efb655ff7a101e6d55e51cbdec6844f20cf52a70894fa`
- `independent-native-forest-packed-results.json`: `100db717fb188c29ca6029cbb3578d8a4c1b4e404b5a542e62e1a1500683fd1a`
- `independent-native-forest-packed-ubsan-results.json`: `ff9a1b5a6fa2da4ab69c3303592dc5f785efb501e4026be7c228f77c270079d6`
