# Smallest admitted-later comparison

**Request only. No admission or native execution.** The executable argv, complete
input bindings, exact pad polygons/open groups, image, phase caps and stop rules
are in `minimum-native-request.json`. The method epoch is immutable
`29140d4e19d526eed3a02a73c33f8ce4219c78f0`; later source packaging does not change it.

**Correction to the82b9f469/36e321b4 request:** the host-only route argv would fail
the guard's mandatory Docker observation. Its corrected300-second payload is
`bash -c 'bash scripts/kicad/run.sh kicad-cli version && exec "$@"' epic242-route-probe`
followed by the unchanged host Python/router argv. The pinned version probe runs
inside the same guard before routing. `run.sh` also performs its own preflight,
so two retained, gated, successful Docker containers are expected. Probe/setup
consume the same300-second allowance on both cases; no budget or routing method
is expanded. Independent source review confirmed compatibility; neither command
has been executed here.

The minimum comparison is two separate O1 fixtures: K1402 and two-A. Both use
the same four predeclared open demands, endpoint masks, native rectangle
`[104.76,202.23,142.23,232.29]` mm and routing budget:

| Net | Exact matched landings |
| --- | --- |
| +12V | U1109.4 → C1134.1 |
| −12V | U1109.11 → C1135.1 |
| AGND | U1105.12 → C1111.2 |
| /O1/TRI_SUM | R1177.2 → U1114.6 |

Authenticate all six preparation ZIPs, then prepare each private fixture using
the packet's source-only command. Use a new output under
`design/partition/core-split/candidates/pilots/generated/`. Check the numerical
Python path/versions on the execution host. Each route, apply, after-settle,
fresh-settle and full-warning audit phase requires its own **new parent admission**
and resource-guard evidence JSON file (new path, not an existing directory). The packet specifies the guard syntax
without a standalone `--`. After after-settle, run the source-only fresh-copy
step before fresh-settle. Save evaluator stdout as `matched-result.json`.
Wrap each admitted guard invocation in
`bash "$HOME/.codex/scripts/heavy-guard.sh" -- ...` for the machine-wide queue.
This queue precedes the phase deadline and does not create an admission.

Run sequentially: one 6 GiB worker, within the shared two-worker/12 GiB cap and
2 GiB free-memory floor. Maximum phase walls are 300/300/600/600/300 seconds:
2,100 seconds per case, 4,200 seconds for the two-case comparison. These are
upper limits, not an admission or a promised completion time. No automatic
retry, budget increase, cuts, rip-up or fallback is permitted.
The guard additionally aborts early below2.5 GiB free and prohibits worker swap.
Preserve the existing43-minute/2,580-second enclosing job cap. Use separate case
batches;4,200 seconds is a sum across them, never authorization for one70-minute
job. Queue/setup uses its actual enclosing wall budget; exhaustion means stop
and preserve the checkpoint.

The fixed image is KiCad 10.0.6 at
`kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`.
Any missing admission/capability, identity drift, timeout/OOM, new warning,
preservation failure, missing proof or uncertain cleanup stops the attempt.
Zero copper additions mean **NO IMPROVEMENT**. Unattempted means **NOT EXERCISED**.
Source-connected return/rail debt blocks coupled success; repairing partition
debt earns zero incumbent-relative credit. Preserve negative evidence.

This produces a bounded comparison, not architecture adoption. Complete native
warning/fresh/preservation gates and independent review remain mandatory. No
canonical outputs, issue closure, PR merge or physical authorization follows.
