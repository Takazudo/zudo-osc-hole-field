# KiCad 10 oracle

All headless KiCad commands for `zudo-osc-hole-field` run through `scripts/kicad/run.sh`. The wrapper requires KiCad 10.0.x and selects an available oracle in this order: `KICAD_CLI_BIN`, Docker with the digest in `pin.env`, then the standard macOS application path. If it cannot find a compatible oracle, it exits with an error. Missing KiCad is never treated as a skipped check.

## Use

From the repository root:

```sh
bash scripts/kicad/run.sh kicad-cli version
bash scripts/kicad/run.sh python3 -c 'import pcbnew; print(pcbnew.GetBuildVersion())'
bash scripts/kicad/run.sh ngspice -b path/to/model.cir
bash scripts/kicad/extract-stock.sh Device R
bash scripts/kicad/smoke.sh
```

`run.sh` mounts the repository at `/work`, sets it as the working directory, uses the caller's UID and GID for Docker, and gives KiCad a temporary writable home. Docker runs with `--rm --platform linux/amd64 --network none`. The temporary home is removed after each command, and files written into the repository remain owned by the caller.

## Opt-in Epic 242 resource guard

`native_resource_guard.py` is an opt-in launcher for a separately admitted Linux worker. It requires a clean checkout at an explicitly admitted SHA, a reviewed SHA-256 of the installed `run.sh`, PID 1 systemd, a local systemd-cgroup-v2 Docker daemon, an available memory controller, and at least 8 GiB MemAvailable before launch. A unique worker identity can be used only once. A systemd worker slice caps the whole checks service plus labeled KiCad containers at 6 GiB with no swap; its shared parent caps admitted workers at 12 GiB with no swap. Admission counts populated slices, including stale runs, under a startup mutex; the external watchdog stops producers, removes only containers with that worker label, checks for survivors, then stops itself last. The whole-command deadline, free-memory floor, OOM events, container membership and caps are checked during execution. A parent admission must reserve at most two native slots globally across hosts and exclude all other native work; the local lock alone cannot establish global admission.

The wrapper enters bounded mode only when the launcher sets `EPIC242_NATIVE_SLICE`, `EPIC242_NATIVE_WORKER`, and `EPIC242_NATIVE_DEADLINE`. It refuses native CLI fallback and remote Docker in that mode. Its version probe and requested command both receive the memory and cgroup options and an inner absolute deadline. CI routes its existing native Python checks and all three board DRC checks through `ci_native_admission.py`. This entry refuses execution unless repository variables `EPIC242_PARENT_ADMISSION_RUN_ID`, `EPIC242_PARENT_ADMISSION_SHA`, and `EPIC242_REVIEWED_HOOK_SHA256` match the current run, checkout, and reviewed hook. The parent must reserve both global native slots for this workflow before setting those values. CI runs Python before board DRC and limits board DRC to two workers. A standard runner with under 8 GiB MemAvailable fails closed; the workflow does not select a larger runner automatically. Before a native check, an authorized operator must separately prove actual cgroup membership, Docker/daemon child containment, watchdog death and cleanup behavior on the selected runner using a bounded harmless pilot. Source tests and mocked Docker arguments do not provide that proof.

`extract-stock.sh Library Name` prints a stock symbol S-expression if that symbol exists, or a stock footprint S-expression otherwise. For example, `bash scripts/kicad/extract-stock.sh Device R` prints the resistor symbol and `bash scripts/kicad/extract-stock.sh Resistor_SMD R_0603_1608Metric` prints that footprint. The command does not copy or modify project files.

## Platform notes

- **WSL/Linux:** install Docker and use the pinned image from `pin.env`.
- **macOS:** Docker Desktop runs the pinned `linux/amd64` image with emulation. A native KiCad 10.0.x CLI can be selected by setting `KICAD_CLI_BIN` to its executable path. Native `python3` and `ngspice` commands also need to be available on `PATH`; for Python board generation, that Python must import `pcbnew`.
- **CI:** install Docker and run the same scripts. Do not silently skip oracle checks when Docker or the image is missing.

The schematic and PCB files produced by these tools are unvalidated drafts. A clean ERC or DRC result reports rule checks only; it does not validate circuit behavior or board fit. Never generate or send fabrication order files from this workflow.

## Known pitfalls

- KiCad 9 cannot open the project's KiCad 10 file formats. The wrapper rejects versions outside `10.0.x`.
- ERC results can change when a fresh user home has no KiCad library tables. Keep project-local symbol and footprint library tables in fixtures and projects that reference stock libraries.
- KiCad CLI has no command to update a PCB from its schematic, and the IPC API needs a running GUI. Build or synchronize boards through `pcbnew` in the oracle.
- The pinned image contains KiCad, `pcbnew`, and `ngspice`, but no Java. Java-dependent tools do not belong in this oracle workflow.
- On macOS, native `KICAD_CLI_BIN` selection checks the CLI version. Commands such as `python3` and `ngspice` still use the corresponding executables on `PATH`.

The explicit harmless proof helper `prove_resource_limits.py --run-harmless-proof --evidence FRESH.json` compiles a small static C process tree and imports it locally into Docker, without pulling any image or running KiCad. Two children each allocate 40 MiB beneath a shared 64 MiB cap; a separate sleeping process tree must be terminated after one second. The helper checks actual OOM/exit state and removes its owned containers and image. This proves Docker kernel controls only; it cannot qualify systemd whole-worker membership, independent supervisor or the 6 GiB/12 GiB native setup.

The separately admitted `qualify_resource_guard.py` uses a locally compiled/imported tiny static fixture and requires no KiCad image. Its restricted launcher mode accepts only the reviewed fixture command and exact local image ID. On the existing manual `routing-benchmark.yml`, `resource_qualification=true` disables every routing job and enables only a ten-minute qualification job. Read-only capability checks precede control/image changes; sequential smoke, whole-command timeout, frontend death and watchdog death phases retain actual membership and cleanup receipts. This chosen implementation requires systemd and a local systemd-cgroup-v2 Docker daemon; those are implementation prerequisites, not universal Epic 242 architecture requirements. Source publication does not grant execution admission.

Bounded native helpers use `docker create` followed by `docker start --attach`.
Each helper (including the version probe) waits in a read-only startup gate
outside the writable repository. The guard binds the full container ID, worker,
unique gate, pinned image, command and original absolute deadline, verifies live
PID/cgroup membership and memory caps, then atomically acknowledges admission.
The gate executes the command with the remaining deadline; admission never resets
the budget. Containers are retained until the guard checks every request against
the admitted and labeled inventories and records each successful terminal status.
Missing containers, unadmitted exits, failed exits and unknown states fail closed.
The existing producer-first cleanup then removes only owned containers and proves
final absence. The separate harmless qualification fixture retains its existing
control protocol; its results do not qualify this new native handshake. Native
execution remains on hold until independent source review and explicit parent
admission of an immutable source SHA.

## Local WSL admission (preparation is not execution authority)

`local_native_admission.py` adds an explicit local lane without inventing a GitHub
run. CI admission, `run.sh`, the resource guard, native gate and their limits are
unchanged. Preparation requires a clean immutable checkout and writes a fresh
request with a 32-hex run nonce, positive attempt, exact checkout/UID, command,
input/method hashes, evidence path, shared heavy guard and resource contract.

Only these operations are accepted:

| Kind | Target | Command inside the existing guard | Deadline |
| --- | --- | --- | --- |
| `startup-success` | `startup-success` | `bash scripts/kicad/run.sh kicad-cli version` | 60 s |
| `startup-failure` | `startup-failure` | `bash scripts/kicad/run.sh /bin/false` | 60 s |
| `oracle` | `python` | The one deferred precision-vendor unittest | 1,680 s |
| `e16` | `KA-t2`, `KB-t2`, `KB-p1` separately | Existing E16 worker | 2,580 s |

Each operation needs a separate operator attestation. The local lane reserves one
global native slot, uses the existing shared heavy queue, and retains the 6 GiB
worker / 12 GiB aggregate / zero-swap native limits. The shared guard can impose an
earlier deadline (its configured default is 1,800 s); no limit is raised. Local
execution must be launched directly, because it wraps itself in the shared guard;
a caller-supplied nested-guard bypass or alternate queue is refused. Its existing
configuration is sealed at preparation and must match at execution. A missing
flock backend or unavailable queue fails closed before launching the helper.

### Prepare a request

Create a fresh ignored output directory, choose a fresh nonce (for example
`python3 -c 'import uuid; print(uuid.uuid4().hex)'`), and run from the integration
checkout, substituting the actual nonce and fresh path:

```sh
python3 scripts/kicad/local_native_admission.py prepare \
  --kind startup-success --target startup-success \
  --run-id <32-hex-nonce> --attempt 1 \
  --output .circuit-cache/<fresh>/startup-success.json \
  --evidence .circuit-cache/<fresh>/startup-success-guard.json
```

This command only reads source and writes the request. It does not approve, pull
an image, invoke sudo, create a service or run native tools. The other startup
phase is a separate request. `oracle --target python` prepares only
`design.spec.cells.test_sweep_precision_vendor.PrecisionVendorSweepGate.test_original_network_returns_nonzero_for_supported_failure`;
no aggregate discovery is allowed. Its existing TI ZIP/library bytes must be
available and are sealed in the request.

For the three matched E16 targets, use the existing `native_descriptor.py`
materializations, graphs, fresh stage and `--run-attempt`, adding
`--local-run-id <32-hex-nonce>`. This produces one `local-request.json` under each
target directory. No `GITHUB_*` values are needed or synthesized. Each envelope
binds the full E16 request, all staged inputs, the target's initial PCB/sidecars,
protected files and the local/guard methods. Changed HEAD, paths, inputs, method,
attempt or run identity require new requests and approval.

### Separate operator action

Preparation and execution never call `approve`. Only after independent review,
actual global reservation, and the applicable qualification work, the operator
may run the following with the **exact reviewed digest** and genuine references:

```sh
python3 scripts/kicad/local_native_admission.py approve \
  --request .circuit-cache/<fresh>/startup-success.json \
  --request-sha256 <reviewed-request-sha256> \
  --output .circuit-cache/<fresh>/startup-success-approval.json \
  --operator <operator-name> \
  --reservation-reference <separate-global-reservation-reference> \
  --qualification-reference <applicable-prior-control-evidence-reference>
```

For startup qualification itself, the qualification reference identifies the
prior harmless whole-worker/control evidence and the approval to test the native
startup protocol; it does not assert that the startup test has already passed.
For oracle and E16 work, it identifies completed applicable runner/control and
native-startup evidence. The existing `qualify_resource_guard.py` already accepts
an explicitly admitted local identity; it remains a separate operator-approved
procedure. No qualification routine is automatically launched by request
preparation or approval.

An approval file is an **operator attestation**, not cryptographic identity or a
security boundary against another process using the same Unix account. Agents
must not create it merely because they can read the request digest. The file
binds the exact request, run, attempt, target, checkout and source SHA. References
must describe actual approval/evidence, not placeholders. This implementation
validates their presence and binding; independent review establishes their truth.

The operator then authenticates and executes in the **same WSL terminal**:

```sh
sudo -v
sudo -n systemctl show --property=Version --value
python3 scripts/kicad/local_native_admission.py execute \
  --request .circuit-cache/<fresh>/startup-success.json \
  --approval .circuit-cache/<fresh>/startup-success-approval.json
```

Successful authentication is only a prerequisite: it does not prove every
privileged guard operation or grant exact-run approval. Short-lived sudo authentication can expire before a long run finishes; the approved runner context must retain the required privilege through final cleanup. This procedure changes
no sudo policy or permanent service configuration. No password is passed to an
agent. For E16, approve each target envelope at its `operator-approval.json` path;
then the existing `native_validation.py execute --stage ... --target ...` routes
to the local launcher. Approval of one target does not approve the other targets.

### Execution evidence and retry rules

The launcher rechecks all inputs, writes an exclusive persistent claim under
`~/.local/state/epic242-native-admission/`, and calls the existing guard through the
shared heavy queue. A host worker rechecks authority and actual service cgroup,
limits and deadline after queueing. All guard stdout/stderr is retained in
`<guard-evidence>.driver.log`; the claim's `.result` records the raw exit status,
exact command, request/approval/log hashes and post-run immutable-input check.
A failed launch remains consumed. Never remove claims to retry: prepare a new
attempt and obtain new approval. Existing `/tmp` guard claims, native receipts
and filled-board preservation checks remain in effect as additional checks.

Startup phases reuse the complete existing lifecycle verifier, permitting only
the exact local host-worker outer command. Helper identities, actual membership,
acknowledgements, terminal states and cleanup evidence stay mandatory. An expected
`/bin/false` result retains the original failure receipt and produces a separate
`<guard-evidence>.qualification.json`; an unrelated failure is not relabeled a
pass. Both phases and the separate whole-worker/control qualification are needed;
a single startup phase is not complete runner qualification.

Inside Docker, a WSL worktree's `.git` pointer can refer outside `/work`. Local
native entry therefore verifies the actual read-only startup gate first and then
checks the host-guard-bound source SHA, exact request/approval and sealed methods.
It does not invoke Git through that inaccessible pointer. Host entry still checks
clean Git HEAD. Existing fill/DRC/connectivity hash chains and cap checks remain
mandatory; a local envelope cannot turn source preparation into native acceptance.
