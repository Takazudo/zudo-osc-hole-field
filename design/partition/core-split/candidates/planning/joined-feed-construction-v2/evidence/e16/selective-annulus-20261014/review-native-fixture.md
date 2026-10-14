# Independent native-fixture source and admission review

Reviewer: independent DRC workstream agent, separate from both admission and fixture authors. Date: 2026-10-14. Disposition: no remaining findings after the corrections below. This review covers source semantics and admission construction only. It is not operator approval, runtime containment qualification, native execution or candidate acceptance. A fresh exact request still requires independent binding review and separate applicable authorization.

## Reviewed scope

The added local operation is fixed to kind `annulus-fixture`, target `annulus`, no production stage, and a 60-second existing guarded worker. The only command is the fixed fixture worker; callers cannot select a board, script or arbitrary command. The request seals the fixed PCB fixture, fixture script and existing local/guard/wrapper/pin/terminal methods. Output derives solely from the bound evidence path with `.annulus` appended. Canonical path, symlink, fresh-directory and request/output alias checks reject reuse; freshness is checked at preparation, launch and host-worker boundaries. Existing persistent claim consumption and no-self-approval rules remain intact.

The fixture worker checks exact local request/approval identity, command, output, worker/slice and deadline; actual host cgroup membership and memory/swap limits precede launch. It transports all guard and local-authority variables through the pinned `run.sh`. The native phase checks the read-only gate/startup mounts, exact container acknowledgement, pinned image, worker/deadline/command and actual container memory/swap caps before importing `pcbnew`. No admission limit is raised, no approval is created by preparation or execution, and no baseline/candidate execution scope is borrowed.

The tiny six-layer PCB contains two original through vias, three functional F.Cu/In1.Cu/B.Cu tracks and one Edge.Cuts rectangle. Its custom In3 diameter is a negative control: a smaller still-flashed pad is not exact selective-annulus omission. Exact KiCad 10.0.6 is required. Initial/reloaded snapshots enforce via UUID/net/center/drill/end-span and per-layer diameters/flash state, functional-track UUID/endpoints/width/layer/net and owner artwork identity/geometry; serialized UUID inventory and immutable input bytes are checked. Successful characterization would still report `NOT_EXACT_ANNULUS_REMOVAL`, native acceptance `NOT_ESTABLISHED`, adoption false, DRC NOT RUN and refill NOT RUN. No production repair or native acceptance follows.

## Resolved findings

1. Initially only `FlashLayer` availability was checked, leaving a missing `GetWidth(layer)` binding to emit an unclassified TypeError. Snapshot API AttributeError/TypeError now becomes an explicit `UNSUPPORTED_NATIVE_API` failure. A synthetic unavailable-overload test verifies refusal before SaveBoard. Actual pinned-library API behavior remains unexecuted until admitted.
2. Initially round-trip preservation compared only via geometry and aggregate identities. Snapshots now also check all three exact functional tracks and the owner rectangle before/after reload. This prevents an unchanged UUID set from hiding modified functional geometry.

## Independent verification

Read the implementation, admission changes, fixed PCB source, test bodies and inherited authority/claim/guard path. Independently executed these focused source-only suites:

```sh
python3 -m unittest scripts.kicad.test_local_native_admission -q
python3 -m unittest discover -s design/partition/core-split/candidates/planning/joined-feed-construction-v2 -p test_annulus_native_fixture.py -q
```

Results: 27 admission tests PASS; final 7 fixture tests PASS. Tests use disposable files, mocked launches and mock authority records. They neither import the real native library nor launch Docker/KiCad, reserve a heavy/native slot, create an actual operator approval or consume campaign/native execution quota. These are source tests, not native acceptance. Runtime cleanup/containment and exact request binding must be assessed on any separately admitted execution.

## Reviewed source SHA-256

| File | SHA-256 |
| --- | --- |
| `scripts/kicad/local_native_admission.py` | `a3cedbad4518bd96d1cf8b4d97732530768e5812df4734a87f469cd732d816a6` |
| `scripts/kicad/test_local_native_admission.py` | `dc67455427284e9432fc99ba3a752f7c3aa957a837c44cd094a7ed107a459f7b` |
| `scripts/kicad/README.md` | `2df931b8499ced900beb3356c2f7d7de854223fa6784cf0d8f9f779bc7535140` |
| `design/partition/core-split/candidates/planning/joined-feed-construction-v2/fixtures/selective-annulus/native_roundtrip_characterization.py` | `a82f572a7926f69152af47e40cb7c0bb8ff49f97ab868790283cc1d2d1cc1173` |
| `design/partition/core-split/candidates/planning/joined-feed-construction-v2/fixtures/selective-annulus/native-negative-control.kicad_pcb` | `55e23a38b52cc776c3327af1b27f138099eb4d32dbbcdd69332ba5e7ebb175e5` |
| `design/partition/core-split/candidates/planning/joined-feed-construction-v2/test_annulus_native_fixture.py` | `a5bb399dadd296a6574727d658aebdd57710f31835e6ce0e201a072fa8cd6a48` |
