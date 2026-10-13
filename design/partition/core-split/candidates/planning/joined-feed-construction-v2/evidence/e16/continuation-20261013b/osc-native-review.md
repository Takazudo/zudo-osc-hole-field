# E16 source-only native request packet

Delivered source files: `/tmp/osc-native-source/native_validation.py`, `native_descriptor.py`, `test_native_validation.py`.
Full patch against dd3ef71: `/tmp/osc-native-packet.patch`.
Integration followup against manager-installed initial packet: `/tmp/osc-native-authority-followup.patch`.
The manager is the repository integration writer. This worker made no tracked repository edits, commits, pushes, native calls, or guard changes.

## Implemented behavior

Preparation accepts materializer output directories or exact individual `e16-source-materialization-v1` manifests for KA-t2, KB-t2, and KB-p1. Each target requires its own actual source graph. It verifies materializer original input seals, actual source object content digest, all output hashes, matching PCB/project/rule sidecars, complete original UUID pad mappings including CS terminal aliases, every source graph input seal, and exact graph normalized source recipe after existing staged cap materialization. A t2 graph cannot stand in for the changed P1 recipe.

Preparation stages exact files under a fresh git-ignored repository `.circuit-cache` directory, because the pinned Docker runner mounts the repository only. It rejects stage reuse and cache paths outside the real repository mount. A staged index retains graph/materializer original seal mappings and is checked again during execution. The descriptor binds SHA, exact GitHub run attempt (default 1), worker source, runner/guard/admission/pin hashes, all inputs, concrete admitted commands, process boundaries, report paths, and canonical boards/placements/decision preservation hashes. It prepares no admission token.

Execution requires the parent's actual run ID, SHA, reviewed hook and **exact externally approved `EPIC242_PARENT_REQUEST_SHA256`**, plus exact request run attempt. The source does not mint that variable. A rerun cannot reuse an earlier attempt's packet. Since systemd-run does not inherit GitHub/admission environment, execute explicitly forwards already-verified authority values into its guard-owned worker command; native containers receive the same verified values.

The host worker proves exact checks.service membership under its worker slice and actual 6 GiB/no-swap plus 12 GiB/no-swap aggregate limits before invoking run.sh. Native modes verify actual checkout HEAD, full worker run/attempt/target identity, parent request digest, actual read-only private gate/start mounts, full container ID/token acknowledgement, exact gate command/pinned image/deadline, and actual container memory/swap caps before importing pcbnew. Existing reviewed guard and startup-gate controls are unchanged.

The admitted board worker runs separate fill, full-severity DRC, and connectivity processes under `ci_native_admission.py --phase board --board e16-{target} --seconds 2580 --evidence ... -- ...`.
Fill saves the board once. DRC uses `--severity-all --format json` with no refill/reset flag. Both analysis phases inspect that preserved filled board. Each phase records commands and actual input/output/log hashes in a chain; immutable sidecars/canonical inputs and unchanged filled-board hashes during analysis are checked. Partial failures retain logs, board and receipt without acceptance.

Connectivity performs the complete existing native cluster/ratsnest census, requiring all-net per-net counts to sum to GetUnconnectedCount(False). It then enumerates **every** four-rail/AGND pad by original UUID, checks reference/pad/net identity, and records each source modeled component, native copper cluster, source/native feed status and peer-group differences. Full source/native group membership is retained; analytic clipping differences remain evidence. It does not claim native copper reproduces every source fragment, finite current/resistance, physical process qualification, or fabrication readiness.

## Verification

`E16_TEST_REPO=/workspace/zudo-osc-hole-field python3 -m unittest discover -s /tmp/osc-native-source -p test_native_validation.py -v`: **16 tests PASS**.
`python3 -m py_compile` on all three delivered source files: **PASS**.
The tests exercise exact executable phase planning, full DRC severity/no refill, missing authority refusal before pcbnew, full UUID mapping, source/native difference retention, stage exact hashes/reuse refusal, source recipe mismatch, materializer input seal refusal, staged tampering, exact attempts/run identity, parent digest/reseal refusal, host cgroup proof checks, private native gate acknowledgement/command checks, and receipt chain integrity.

Read-only verification against actual manager materializations and fresh graph inputs: **PASS for all three targets**, 74 exact sealed files collected. KA/KB t2 physical pad mappings cover 1568/2281 pads respectively; KB P1 is separate.
Actual graph SHA-256:
- KA-t2: `20d91e5f32c69786cc02b83fe49e41f56c6a3674dfedb369a91aacc1d15ce5b7`
- KB-t2: `4ba5cccb718310468fb7428d777a8819a21badd397c9d0756f8ecceab0bb9851`
- KB-p1: `79a20192c9ef724545b73e9ae4d35d8fd272227b8fb16c157b2a467bf340370f`

The integration owner reported startup and initial circuit check PASS. This worker did not repeat startup, heavy commands, or native checks.

## Remaining execution gates

Native fill/DRC/connectivity: **NOT RUN**; no parent admission exists for this source-only continuation. No runtime qualification result is claimed. The selected native host must independently satisfy the unchanged guard prerequisites and previously required harmless resource/cleanup qualification. After committing immutable reviewed source, prepare a fresh request at that exact SHA, review its digest, and admit actual run ID/SHA/hook/request digest and exact attempt with the reserved global slots. Native container read-only gate/cgroup checks fail closed if the runner does not expose the required proof.

Example source-only preparation (integration owner):

```sh
python3 design/partition/core-split/candidates/planning/joined-feed-construction-v2/native_descriptor.py \
  --materialized /tmp/osc-materialized-KA --materialized /tmp/osc-materialized-KB \
  --graph KA-t2=/tmp/osc-e16-source/KA-eval-t2/port-graph.json \
  --graph KB-t2=/tmp/osc-e16-source/KB-eval-t2/port-graph.json \
  --graph KB-p1=/tmp/osc-e16-source/KB-eval-p1/port-graph.json \
  --stage .circuit-cache/e16-native-request-FRESH \
  --run-attempt 1 --output /tmp/native-descriptor-v2-FRESH.json
```

The descriptor's execution commands invoke only the fail-closed execute mode. Preparation does not authorize running them.
