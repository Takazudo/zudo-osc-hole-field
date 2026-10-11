# Proposed exact pilot commands — NONE ADMITTED

The guard implementation/wiring is commit `aa618e71c6bd31e25b1d475305f94bc15eb064e1`; parent-cap test refinement is `103840c334808cf65f6ec07f528f9ebb834d6ccd`. The following commands pin the reviewed code at `3b00fd45857990bcc2769e150a4e009388c442fc`. They are future admission proposals, not commands executed in this session. A later documentation-only commit does not change this code pin. Any source/hook/candidate change requires review and a new full SHA.

## Required runner and admission

Use an explicitly authorized disposable Linux amd64 runner with PID1 systemd, cgroupv2 memory controller and writable resource controls, local Docker endpoint `unix:///var/run/docker.sock`, Docker systemd cgroup driver, memory/swap support, and approved noninteractive systemd transient-unit privilege. Do not change security policy/access controls to make this session fit; select an already capable runner. The exact digest image in scripts/kicad/pin.env must be preloaded and authenticated locally; admission never pulls it. A harmless qualification below does not invoke KiCad; preflight only inspects that preloaded image.

Require clean tracked checkout at the pinned SHA, unique worker/admission identity and fresh evidence destination. Parent reserves global native capacity (maximum2workers/6GiB each/12GiB aggregate), excludes unaccounted native work and accounts for colocated overhead. Local mutex/populated-slice checks cover this host only. Require8GiB available for first worker; reserve unconsumed existing worker headroom before another (up to14GiB available for two initially idle workers). The early2.5GiB abort protects the mandatory2GiB floor; sampling cannot prove an instantaneous never-crossed floor. Existing managed-machine heavy-guard requirements still apply through an authorized accessible path; no denied home access or fallback is implied.

Bind these operator-supplied values only after explicit admission:

```sh
PILOT_SHA=3b00fd45857990bcc2769e150a4e009388c442fc
HOOK_SHA256=8631e1222942b8396bf566c88deaed0e287234146c4adb1afa9aa87d0d1055a5
: "${PARENT_ADMISSION_ID:?explicit parent reservation required}"
: "${EVIDENCE_DIRECTORY:?fresh retained evidence directory required}"
```

## Priority0: harmless whole-worker control qualification

The actual64MiB Docker memory/one-second cleanup proof is already retained in resource-control-kernel-proof.json. Systemd membership/deadline/independent-supervisor behavior remains NOT RUN. On the capable admitted runner, prepare this tiny image from reviewed source, without network downloads:

```sh
fixture_dir=$(mktemp -d /tmp/epic242-qualification-XXXXXXXX)
cc -Os -static -o "$fixture_dir/fixture" scripts/kicad/fixtures/resource_guard_fixture.c
tar -C "$fixture_dir" -cf "$fixture_dir/rootfs.tar" fixture
FIXTURE_IMAGE_ID=$(docker image import --change 'ENTRYPOINT ["/fixture"]' "$fixture_dir/rootfs.tar")
sha256sum scripts/kicad/fixtures/resource_guard_fixture.c "$fixture_dir/fixture" "$fixture_dir/rootfs.tar"
```

Membership/process-tree observation, one worker,20seconds;80MiB child allocation fits6GiB. Expect COMMAND PASS ONLY plus inspected membership and real peak/current/events, not electrical/native acceptance:

```sh
python3 scripts/kicad/native_resource_guard.py \
  --admission-id "$PARENT_ADMISSION_ID" --worker qualify-smoke-a1 \
  --sha "$PILOT_SHA" --hook-sha256 "$HOOK_SHA256" --seconds 20 \
  --evidence "$EVIDENCE_DIRECTORY/smoke-a1.json" -- \
  bash -c 'exec docker run --rm --pull=never --network=none --cpus=0.5 --pids-limit=16 --memory=6442450944 --memory-swap=6442450944 --cgroup-parent="$EPIC242_NATIVE_SLICE" --label "epic242.native.worker=$EPIC242_NATIVE_WORKER" "$1" aggregate' \
  harmless-fixture "$FIXTURE_IMAGE_ID"
```

Deadline/process-tree cleanup, one worker,2seconds; the fixture sleeps30seconds. Expect nonzero timeout/watchdog status and verified no producer/labeled-container survivors. Nonzero is the intended control-test outcome, never a pilot pass:

```sh
python3 scripts/kicad/native_resource_guard.py \
  --admission-id "$PARENT_ADMISSION_ID" --worker qualify-timeout-a1 \
  --sha "$PILOT_SHA" --hook-sha256 "$HOOK_SHA256" --seconds 2 \
  --evidence "$EVIDENCE_DIRECTORY/timeout-a1.json" -- \
  bash -c 'exec docker run --rm --pull=never --network=none --cpus=0.5 --pids-limit=16 --memory=6442450944 --memory-swap=6442450944 --cgroup-parent="$EPIC242_NATIVE_SLICE" --label "epic242.native.worker=$EPIC242_NATIVE_WORKER" "$1" hold' \
  harmless-fixture "$FIXTURE_IMAGE_ID"
```

Retain complete stdout/stderr, image/compiler/source hashes, receipts and actual unit/cgroup limits. Parent must additionally review/admit two-worker aggregate/stale-slot, supervisor death and guard-parent crash/floor-read-failure cases, and prove cleanup from independent observers. The two commands above alone do not qualify all those paths. Remove the owned image after qualification via `docker image rm "$FIXTURE_IMAGE_ID"`; retain fixture source/build hashes. No automatic retry or native jobs follow.

## Priority1: #249 label load/render/reload — HOLD

Current entry command is exact, but it deletes temporary SVG/reload evidence and lacks complete saved/reloaded text/pose/mirror comparison. Owner must fix those source/evidence gaps and return a reviewed immutable SHA before execution. The proposed one-worker300second invocation is:

```sh
python3 scripts/kicad/native_resource_guard.py \
  --admission-id "$PARENT_ADMISSION_ID" --worker labels-249-a1 \
  --sha "$PILOT_SHA" --hook-sha256 "$HOOK_SHA256" --seconds 300 \
  --evidence "$EVIDENCE_DIRECTORY/labels-249-a1.json" -- \
  bash scripts/kicad/run.sh python3 scripts/pcbgen/trimmer_labels_native_regression.py
```

This pins current code for review only. Replace SHA/hook bindings after approved retention/semantic corrections; do not run the defective current fixture for a claimed complete result. Qualification establishes fixture behavior only, not full-board clearance/fit.

## Priority2: #245 complete three-A settle — HOLD

On an approved source interpreter matching scripts/pcbgen/numerical-requirements.txt, materialization is source-only:

```sh
: "${SOURCE_PYTHON:?approved absolute source interpreter required}"
"$SOURCE_PYTHON" scripts/partition/core_split_candidates.py materialize \
  --pilot three-A \
  --output design/partition/core-split/candidates/pilots/generated/decision-three-A-admission-a1
```

Verify complete293-file tree/291portable seals and beforePCB SHA256 `4d8e238d5d504d55a0f5defe19671d7825f3a356a56ab143e38dd9c918110819`, bind the exact materialized sha256.json, then proposed one-worker300second command:

```sh
python3 scripts/kicad/native_resource_guard.py \
  --admission-id "$PARENT_ADMISSION_ID" --worker three-a-settle-245-a1 \
  --sha "$PILOT_SHA" --hook-sha256 "$HOOK_SHA256" --seconds 300 \
  --evidence "$EVIDENCE_DIRECTORY/three-a-settle-245-a1.json" -- \
  "$SOURCE_PYTHON" scripts/partition/core_split_candidates.py settle \
  --board design/partition/core-split/candidates/pilots/generated/decision-three-A-admission-a1/before/osc-core.kicad_pcb
```

At most6refill passes/3equal complete signatures; parse/parity/stability evidence only, no routing/architecture acceptance. No focus/search/apply command is admitted. Prefer retained #251 negative evidence unless parent requests a new topology observation. #252 remains source-only pending explicitly authorized delivery of the already-authenticated K1402 archive and reviewed replay provenance/bounds. #244 transport/waves remain prohibited.

## CI wiring

Every former native Python check and all three DRC board entries now use ci_native_admission.py. Parent must supply exact EPIC242_PARENT_ADMISSION_RUN_ID, EPIC242_PARENT_ADMISSION_SHA matching current run/GITHUB_SHA/clean HEAD, and EPIC242_REVIEWED_HOOK_SHA256. Values are not set here. Python28minute command runs before at most2board43minute commands; job30/45minute limits and all original gates remain. Standard ubuntu-latest placement is not automatically upgraded to a capable runner; absent capacity/control capability fails closed.
