# E16 reconstruction source checkpoint — 2026-10-14 WSL

This is a tested source checkpoint, **not a completed real-data experiment**. The branch starts at verified PR275 head `0159f8acdb9295662810e63dd8a50b96a12a756b` and targets `topic/e16-resistance-attribution`. PR274 remains at `a811c2dd`, integration PR260 at `5af0e7b6`, and original numerical execution source at `852ffac7`. No dependency incorporation, integration ownership or merge is claimed. See [provenance](provenance.json).

## B0 — implemented and independently tested

`attribution_reconstruction.py` implements one selected observation RHS using the existing `board_parts`, SuperLU settings, three-step extended refinement, retained interface basis and `small_system` conventions. It does not substitute simultaneous-load `u0/g` for the selected excitation. Tiny fixtures reconstruct original Assembly numbering from original mesh items, verify persisted stiffness/rings/all support UUID-to-node/weight/interior mappings, reconstruct potentials and feed the complete result into PR275's unchanged reporter. Independent class energies come from original operator applications, not the proposed partition.

The new `copper_stream` uses a structured coordinate-key map and local sparse matrices for every union tile and exact consecutive barrel interval. `PatternSum` checks the entire partition against one board's existing CSR pattern. `account_copper` uses one shared board-current accumulator and one original-operator application, instead of a full-board vector/matrix per small component. No small component is dropped. Overlapping member identities remain provenance, not additive shares. Distributed terminations and globally once-only live-wire bulk retain predecessor semantics, including end terminations of removed wires.

The end-to-end entry point deliberately remains **tiny-source-only**: combined order <=256, bounded actual sparse/array/geometry/support payloads, bounded original mesh vertices/items/entries and output. It builds a tiny complete packet solely for parity with the existing reporter and its independent free-operator eigenvalue check. The cap is not a production scaling solution; do not raise it to run the real model. There is no production artifact loader, executor or authorization switch.

Independent numerical review found and closed actual-storage resource bypasses, a missing standalone current-reconciliation gate and missing connected removed-wire coverage. Final [numerical review](numerical-review.md) independently passes **57 tests: 23 new bridge and 34 existing reporter tests**, at exact source/test hashes. Full E16 final run passes **296 tests**. [Resource review](resource-review.md) covers artifact availability, state, lifecycle and production boundaries; its earlier source hashes are explicitly superseded by the final numerical/resource closure. [Checks](checks/summary.json) records final hashes/counts and unavailable gates.

## B1 — exact target retained; not executable or admitted

Stage B remains KB U7105.4, UUID `e97b2d02-463a-5a6d-ab37-748ce29d7cf8`, +12V, nominal-average / uniform-dielectric / all-present, one selected 1 A RHS over unchanged KA + interfaces/wire + KB. TP990002, TP990014 and TP990026 remain held exactly. TP990026 is not the observation. Named transfer via `87d2de81-b7e7-5e5c-9063-52b28f51939e` and all its exact consecutive layer intervals remain unchanged.

**Fresh numerical request digest: null — no executable request exists.** [Readiness](readiness.json) is a source-bound blocker report, not an approval/request packet. Assigning its hash as a numerical request digest would be false. Existing admission machinery was inspected; its retained full-baseline hook requires `maximum_units == 148` and cannot execute a relabeled single diagnostic.

Concrete unresolved operations, in dependency order:

1. Provide an independently reviewed exact free-operator positivity/uniqueness method and evidence. Neither graph connectivity, successful SuperLU, a self-generated matching hash nor positivity of the tiny coupled Schur matrix proves the real free-board operators positive definite. No applicable retained receipt exists. A block certificate must bind both actual free matrices, held sets, return state and checking method, including its computational cost.
2. Implement and review the production driver with serialized, bounded artifact decompression, original map recovery, one selected KB factor/solve, retained-basis reconstruction and complete local accounting. Tiny helpers are implemented; their current full-packet fixture wrapper must not become the production transport. Exact original map arrays are absent from operator pickles but recoverable from existing mesh bytes. The required recovery algorithm is exercised end to end on real tiny Assembly/ring data.
3. Qualify the combined lifetime/time/output plan, including the uniqueness operation, against **one diagnostic / one serialized unit / one RHS / 180 seconds after guard entry / 2 GiB / zero swap / one attempt / 64 MiB aggregate output**. [Operation plan](resource-plan.md) lists every phase and known storage requirement. Historical separate receipts make serialized work plausible, but establish neither feasibility nor impossibility under this combined packet.
4. Bind the completed one-unit operation through existing admission controls, independently review its immutable request, obtain genuine applicable numerical authorization and a current exclusive reservation. The terminated correctness campaign's delegation has not been shown to cover this physical-attribution experiment. The unrelated native negative control grants no authority.

No real pickle was opened, no real field reconstructed, no baseline restarted and no numerical/native unit consumed. Campaign remains terminal at **2/3 baselines and 8/24 diagnostics**; actual ledger change **zero**. Source/test/build processes completed; no production process, scope, claim or reservation was created. The final state check is in checks/summary.json. Prior failures are preserved.

## Retained comparison and preservation

Independent streaming verification matched all **135 solver files / 844,803,369 bytes**, and all **60 original-request-bound +12V input paths**, including 22 original mesh chunks. The latter provide independent hashes but not independent size fields; observed sizes are not relabeled as independent expected sizes. [Artifact inventory](resource-inventory.json) records this distinction. Recover missing bytes only using the unchanged campaign attempt5 index/transfer instructions. Compressed request digest `3ac6356762419c653c8949adb1c2d12db58e109408d52246ef482e9a398adc54` remains separate from original decompressed request binding `ef0213b3b38f4de23804ad192043b082d8e1b2be3086c5e20e4343afea4052d6`.

[Retained comparison](retained-comparison.json) independently identifies the selected pad in the hash-verified original `all-present.driving_point.KB` result: total **7.173098523558 mOhm**, copper **5.992145292774 mOhm**. This establishes the original unit-current projection's identity and quantity through the actual `finite_solve.couple` source and bindings, rather than assuming the specification's rounded historical figure is an expected result. No new reconstruction was compared with it. Simultaneous-load watts and selected loaded potential are retained separately; no second loaded solve/reconstruction was admitted or performed.

[Preservation audit](preservation.json): all 539 topic protected files and 550 original protected files match; only 11 predeclared original-only UI files are absent from the topic. All 19 Mac browser bindings match. Existing browser evidence and failures are retained, with no redundant browser run. Canonical boards, accepted copper, 438 fixed centres, 33 modules, harness IDs/Refs/full pin order, sensitive groups, electrical limits, source/protection boundaries and `decision.json` remain unchanged. KEEP_K1402_INCUMBENT.

## C — NOT RUN

No real attribution result exists, so the mechanism is neither supported nor rejected. An incomplete experiment does not support the via. The predeclared screen remains at least 10% of nominal copper energy in the named original transfer barrel plus a numerically resolved nonzero TP990026 reaction. A future complete adverse result rejects this mechanism as the next repair for this observation and must retain the largest reconciled contribution. Unresolved share/reaction classification is inconclusive.

No Stage D action occurred. The proposed (141,175) mm, 0.6/0.3 mm additional via remains an unmaterialized conditional specification. The separate +5V KB U4330.14 problem remains open. Native negative-control request `f8da55c7…e3`, frozen at `b27391de`, is untouched and is not a B0 prerequisite. Selective-annulus refusal and incomplete-DRC rejection remain unchanged. Every electrical/whole-board acceptance and adoption flag is false.

## Next executable commands

From the E16 directory, reproduce the implemented source-only blocker (expected exit **2**, no production reads):

```sh
/home/takazudo/.cache/zudo-e16-numerical-venv/bin/python attribution_reconstruction.py --readiness
```

Reproduce the complete source-fixture bridge:

```sh
/home/takazudo/.cache/zudo-e16-numerical-venv/bin/python -m unittest test_attribution_reconstruction test_resistance_attribution -v
```

There is no truthful production execute command yet. Resolve the exact uniqueness/serialized-driver/resource operations above before preparing that request; do not infer admission from the source tests or from availability of retained bytes. PR260 stays draft/unmerged and issue253 stays open. No adoption, fabrication, procurement, energization or deployment occurred.
