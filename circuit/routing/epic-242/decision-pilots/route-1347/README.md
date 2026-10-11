# Admission1347 capability stop

Admission `epic242-o1-k1402-route-20261011-1347` covered only the first O1/K1402
route phase,300s including both gated Docker probes and the unchanged host
router, one reserved6GiB/no-swap worker `o1-k1402-route-1347-a`.

Local PID1 was `tail`, so the required systemd guard could not run locally.
Authorized ordinary Actions capability check [run38145097428](https://github.com/Takazudo/zudo-osc-hole-field/actions/runs/38145097428)
used isolated orchestration commit `5d2ace3fd3d7bc6334b4f030d62033dbd1903d87`
on `integration/epic-242-o1-k1402-route-1347`. Its workflow and read-only helper
are preserved at that commit. The method was checked out independently at
`29140d4e19d526eed3a02a73c33f8ce4219c78f0`, tracked-clean, with all12 expected
source hashes matching. No native method file was changed.

The preflight found systemd PID1, cgroupv2 memory control, Docker's systemd/v2
driver and noninteractive sudo. It failed closed because the applicable outer
`/home/runner/.codex/scripts/heavy-guard.sh` was missing and the exact pinned
KiCad image was absent locally. No replacement guard, installer, image pull,
retry, native phase, proposal application or canonical edit followed.

The reserved worker was **never started**:0native workers,0probe containers and
0task-created systemd units. No native cleanup action was needed; the parent
can release the reservation. SixZIP authentication, numerical binding and
fixture preparation were not begun, so there are no fixture lock, before-board
hashes, proposal or search diagnostics from this attempt. This is a capability
failure, not a routing result or NO IMPROVEMENT observation. Two-A and all
apply/settle/fresh/audit phases remain unadmitted.

`capability-receipt.json` is the exact downloaded artifact member. `actions-log.json`
stores the complete decoded job log as a JSON string obtained through connected GitHub, including
the failure and successful evidence upload. [Artifact11704591168](https://github.com/Takazudo/zudo-osc-hole-field/actions/runs/38145097428/artifacts/11704591168)
is4578bytes, SHA256
`a9e17909f736bd951f26714c90efd48c2abfa974225071702ed82b525b7d64b9`, verified
locally against the downloaded full ZIP. Direct gh transport returned403 both
normally and escalated; connected GitHub recovery succeeded without credentials
being created. ZIP bytes remain local; no LFS was used.

[Parent handoff](https://github.com/Takazudo/zudo-osc-hole-field/issues/253#issuecomment-6109780724)
reports the stop and release eligibility. The future request packet now correctly
requires `--evidence` to name a **new JSON file**, never a directory. An actual
route requires a runnable environment with reviewed applicable controls and
parent coordination; this checkpoint does not extend or renew admission.
