# P source epoch diagnosis for the aggregate boundary manifest

## Actual failure and scope

`current_source_boundary_manifest.py` snapshot `05f9d22faa3e7efac6f3cd7b3771d3e92b591657a30ef0fd64f6202b5b8afa9c` correctly fails at the live P native gate. The failure is not evidence of a disconnected P contact, but the old receipt cannot simply be relabeled current. No aggregate PASS receipt should be emitted from the failed run.

Independent hash comparison of the retained P v3 native receipt found exactly three changed source dependencies; all retained native artifact hashes matched:

| Source | Original expected SHA | Current SHA |
|---|---|---|
| design/reports/io-partition.json | ae6955604c343a1be2bb17c0a5af38e619424128ec8a712567973c8989980402 | fa91a087550d6fe6abbfb3604650c8d1bb0616abb0fbc2178302c8a1741ddcbf |
| scripts/pcbgen/extract_power_geometry.py | 092f54e1f24c45545ad74c8105dd148d070043d6633ab09adb0bbe9f04ff993c | 3274c1139237522a1811ac4d118e3740798c4f141306869aac1dcf2ed8c3cbfc |
| scripts/pcbgen/native_stack.py | 3de2f981b7af80500b37245ff74fa29a5f08ee1423d04cdafe336635892556d0 | f108bb4eeb4bd5fc446a10a4d956e838b8ff2b57a81100c8067b02e048857d13 |

## Exact old bytes and actual source projection

The original IO is retained at `.circuit-cache/issue38-recovery/white-land-review/io-partition.json` and independently matches ae695560…. The two original helper files are retained and independently hash-valid at:

- `design/partition/model-history/pre-two-layer/sources/092f54e1f24c45545ad74c8105dd148d070043d6633ab09adb0bbe9f04ff993c.py`
- `design/partition/model-history/pre-two-layer/sources/3de2f981b7af80500b37245ff74fa29a5f08ee1423d04cdafe336635892556d0.py`

Their original paths, hashes and retained paths are recorded in `design/partition/model-history/pre-two-layer/manifest.json`. This is audit evidence, not a silent alternate current solver implementation.

Independent exact comparisons:

1. Old/current IO differ ONLY in `physical_packages`.
2. Exactly104 full package records differ; none belong to the285 P-assigned package references. Every complete P package record is identical.
3. All non-package IO fields are globally identical; the P-restricted allowed-crossing member projection is also identical.
4. With the same bound native P v3 geometry and source partition, complete `source_flux_boundary_inventory.inventory` outputs are identical under old/current IO. All214 own contacts match field-for-field, with94 convex SMD and120 PTH. This is stronger than matching aggregate counts.

These checks support a narrowly scoped current-P-source/retained-native-geometry bridge. They do not create new native execution, physical material/contact acceptance, or electrical equivalence of historical operators.

## Minimal safe repair

Create a separate source-geometry bridge helper/receipt; keep `control_model_gate` strict. Verify the original v3 receipt, DRC/native export/board/copied companions and original source dependencies using the exact retained old IO/helper bytes. Explicitly retain original-path→archived-path→expected-hash evidence for those three historical inputs. The source gate's other dependencies must still match exactly. Recheck the complete current P package/pin/net/DNP projection, source geometry/stack/outline/hole/UUID identity and complete current P inventory against that retained authority. Bind both source epochs and the bridge's own/helper hashes before checking; recheck them before publishing.

The bridge must not replace the original receipt's ae695… with fa91…, replace exporter/native_stack digests with current ones, or catch-and-ignore live gate failures. Record the old native receipt/export epoch honestly. Map historical expected bytes to their distinct retained paths; never merge old and new IO expected digests under one current path. Feed this new limited authority to the aggregate manifest, which continues to recompute all4143 current source identities and family splits. Capture the manifest's classification/helper hashes at entry as well as at exit; first hashing classification code after use cannot establish its execution epoch.

A fresh pinned P export/native source receipt is an alternative. The exact projection bridge above can discharge this inventory-only need without a new full numerical solve, subject to its independent implementation review. It does not admit historical P matrices as current-source reruns.

No shared source edits, native run or full solver run performed by this reviewer. Current source flux/contact/process/material, 3D dual/primal and joined electrical acceptance remain OPEN.
