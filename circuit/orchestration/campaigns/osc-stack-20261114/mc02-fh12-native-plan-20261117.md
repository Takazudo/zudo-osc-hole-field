# Isolated FH12 native fixture admission

2026-11-17 UTC / 2026-11-18 JST. Coordinator: Codex on x0x WSL, delegated Moya
role. DS-141 governs scope. Implementation
39d456d380cb09e2ca16e0252c3d2d826ff498c3 passed13offline tests and independent
review. Native result: NOT RUN at this admission checkpoint.

## Inputs and deliberately limited meaning

Four selected SH(55) contact counts8/14/26/40, verified EDC3-150229-11 PDF
c3257beed2331e5c95e176bc28441b04b804301a44c11b462e486fb5cc649d07. Copy only the
three admitted data dependencies and generator/checker/spec into a fresh staged
root. Do not mount canonical boards, repository root, home or credentials.

Generate incomplete copper-land-only footprints:1..n signal pads, two unnumbered
mounting lands, no nets, courtyard, body, mask/paste apertures or3D. No physical
project registration is inferred. Verify F/B and four cardinal transforms for
all four variants:32cases. Expected pad geometry is constructed independently
of the generator from the reviewed source table. Check number, position, size,
orientation, exact copper layers, unconnected nets, incomplete description and
absence of unsupported graphics/models before and after native save/reload.

Only pinned image
`kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`,
with `--pull=never`. Both CLI and pcbnew must report10.0.6 inside that container.
No host pcbnew/ngspice or native executable substitution. No DRC,fill,aggregate,
production library registration, fabrication or hardware adoption.

## Composite limits and reviewed failure path

DockerDesktop runs in a separate VM; a WSL cgroup is not a Docker workload cap.
The admitted total workload ceiling is1CPU,2.5GiB,192PIDs,swap0. Host setup,
control and supervisor children must be included in the following WSL split:

| Group | CPU | Memory | PIDs | Role |
| --- | --- | --- | --- | --- |
| Guardian and canonical heavy guard |0.02|128MiB|16|Hold shared lock and perform final cleanup, independently of controller failure|
| Controller |0.03|64MiB|8|Orchestrate separately bounded worker|
| Worker |0.20|320MiB|40|Stage exact inputs and invoke bounded Docker control commands|
| Docker workload |0.75|2GiB|128|Pinned identity/fixture operation only|

Inspect actual cpu.max,memory.max,memory.swap.max,pids.max and termination
properties in each workload group. Initial/terminal systemd control-plane client
outside these groups only starts/waits on the bounded guardian; disclose it.
Docker daemon/VM baseline and machine-wide overhead are not capped by this table.
Recommended free-memory floor is waived by owner; actual observations and
workload caps remain required.

Total foreground deadline600s including cleanup. Container internal deadline is
230s TERM plus10s kill grace, independent of its host client. Bound writable
container storage and verify actual tmpfs options, read-only bind/root, image,
network isolation and ownership. Copy bounded tmpfs evidence while the container
is alive, then acknowledge completion; stopping first loses tmpfs contents.

The first lifecycle implementation was rejected before execution because
controller OOM could release the guard while worker/container continued. The
revised independent guardian must stop the worker and remove the exact owned
container after controller loss, then verify daemon absence and empty/inactive
host groups before normal lock release. No broad container deletion. Cleanup
uncertainty is nonzero, retains evidence and blocks further admission; it never
claims that a bounded exited process still owns its lock.

After offline failure tests and independent review, perform one controlled
identity-only preflight with no board mounts: retain CLI/pcbnew identity and cap
receipts, then terminate only its owned controller at a declared barrier. Verify
canonical lock inode/holder and independent nonblocking exclusion before/after
that termination; guardian must survive, clean worker/container and verify final
absence. Record EXPECTED_CONTROLLER_FAILURE_CLEANUP_VERIFIED, not native semantic
PASS. No memory-pressure stress test or unchanged failure retry. Then separately
admit one actual32case fixture transaction if the preflight passes.

## Evidence and continuation

Retain exact implementation/runner/container hashes, command arguments, staged
input and output hashes, identity, host/container effective caps, resource
observations, stdout/stderr, terminal states and cleanup receipts. Independent
result review follows actual execution. A successful fixture proves only native
serialization of incomplete candidate lands. Installed fit, source-to-field
registration, manual access, cable compliance, routing and26IC liabilities stay
open. Review the next ready task after reporting; this milestone is not automatic
campaign completion.
