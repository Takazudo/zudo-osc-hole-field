# X0X bounded native validation: evidence retention failed

**Native version and export outcome UNKNOWN. Native parity NOT RUN.** This
record does not complete Stage17 native validation or establish electrical
acceptance. No further native attempt was made.

The owner approved capability checks and one isolated exact KiCad 10.0.6
netlist export against source commit
`5469def6cdf2a5f0f9d4a61cec88efbc7ac2130b`. The circuit root SHA256 is
`2d7530895ab55e5b7dd1e41d416f1cb9b295fd716b3b07aa83c83e6dbf195538`.
All 61 generated assets and 66 source hashes matched. PR286's head was checked
again immediately before admission and still matched. No input was repaired.

X0X has Windows 11 Pro 10.0.26200, running Ubuntu 24.04.4 WSL2 and Linux Docker
Engine 29.3.0. Windows Docker Desktop was stopped, but the independent Ubuntu
Docker engine and exact pinned image already existed. Nothing was installed,
downloaded as a runtime, enabled, or reconfigured. Initial sandbox-only access
failures were resolved with approved read-only host checks, not permission edits.

The existing machine-wide heavy guard serialized this task with other work.
`capability.json` and `docker-inspect.json` retain actual 2 CPU, 4 GiB RAM,
zero-swap, network-none and read-only input enforcement. A single 250 MiB tmpfs
held outputs/config/cache/logs; at most another250 MiB for retained copies plus
12 MiB of host metadata conservatively bounded total output by512 MiB.
The600-second container timeout covered the whole lifecycle. The independent
reviewer approved actual controls before `admit.json` released the supervisor.
The only possible native argv were the version probe, then the one specified
export only if version stdout equalled10.0.6. Actual native argv execution,
version, exit status, timing, resource usage and output hashes were intended
for tmpfs logs but did not survive; command templates are not execution proof.

## Failure and honest evidence boundary

The host saw a done marker and `docker cp` returned success, but the retained
directory was empty (`result.json`:0 bytes). The runner then killed and removed
its container. Its tmpfs is gone. The exact cause of the empty copy has not
been established. The concrete orchestration defect is accepting copy exit0
without verifying required files and their hashes before destroying the source.
The done marker is also written on supervisor exceptions. Therefore the raw
`native_done: true` field is not proof that either native command succeeded or
even began. Container exit137 is the deliberate cleanup kill, not a native
exit code. Guard PASS describes the host wrapper's exit only. Do not promote
any of these to KiCad success. The independent review acknowledges missing
this retention-verification requirement.

No netlist remains for the118-reference/561-pin/154-unit comparison. The
independent comparator and12 mutation tests are retained as source snapshots,
not native results. They cover complete references, pin/library inventories,
unit UUIDs, identity/value/footprint bindings and explicit unconnected-pin
omission handling. The snapshot test assumes the original workspace layout:
these files beside an `osc-validation` checkout. No compatibility with an
actual native export has yet been demonstrated.

## Next separately admitted operation

Before asking to spend another native attempt, repair retention and test it
with nonnative sentinel files in an equivalent bounded container. Stream from
the live container using `docker exec`, bound all archive/extract/duplicate
bytes within512 MiB, verify required logs/netlist and every output hash, then
destroy the container. Retain supervisor failures as failures, not done=true.
Bind a fresh unique run/admission and review the exact scripts and current
source hashes. Obtain separate approval for another native attempt; do not
reuse this admission or silently retry. These recorded runner snapshots are
historical defective evidence and MUST NOT be replayed.

The19 null passive MPNs and unbound DIN/source-land footprints remain. No ERC,
DRC, PCB generation/routing, simulation or hardware action was performed by
this task. Canonical source, locked placements, decision.json and
KEEP_K1402_INCUMBENT remain unchanged. PR286 remains draft/unmerged;285/260/277
remain parked. Source or netlist parity would not be electrical acceptance.
