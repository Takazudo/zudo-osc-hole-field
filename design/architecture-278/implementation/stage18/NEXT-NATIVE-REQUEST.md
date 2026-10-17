# Proposed next native observation — no admission granted

The source implementation and executable request generator are in this checkpoint.
The final PR checkpoint pins their exact commit. Generate a proposal only:

```sh
python3 scripts/architecture278/implementation/stage18_request.py --commit <full-implementation-commit>
```

This source-only command refuses stale source reports or a commit whose input
bytes differ. Its JSON binds all original and repaired native inputs, source
and verifier code, exact image, argv, output and resource ceilings. It does not
create admission, invoke Docker/KiCad, or reuse any previous permission.

After fresh owner approval and independently reviewed live admission, the only
proposed native commands are:

```sh
kicad-cli version
# Only with exact stdout 10.0.6, once:
kicad-cli sch export netlist --format kicadxml -o /output/netlist.xml /inputs/stage18/generated/a01.kicad_sch
```

The required read-only input tree contains both `stage17/generated/` (all61
immutable files) and `stage18/generated/` (the repaired hierarchy and tables).
The root SHA256 happens to remain
`2d7530895ab55e5b7dd1e41d416f1cb9b295fd716b3b07aa83c83e6dbf195538`
because the root still references eight sheets; **the child sheets changed**.
Root hash alone is insufficient. Use the complete request manifest and hashes.

Prefer Codex Cloud. X0X is only a fallback if Cloud cannot prove the required
existing native capability and resource enforcement. No capability or native
readiness is claimed here. The existing image digest remains
`kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`.

One run and one export opportunity,2CPU,4GiB RAM,no swap,600seconds total,
network none,read-only inputs/root. Configuration/cache/tmp/logs share250MiB
live tmpfs; bounded verified retained stream copy250MiB; host metadata12MiB;
total512MiB. Shared heavy guard plus independently inspected actual cgroups,
mounts,network and timeout are required before native execution. Use fresh absent
run paths and a new approval/admission bound to exact checkout, code, input map,
argv, output destination and resource receipts. No installations, service,
security, credential changes or automatic retry.

The old Stage17 host/container runners hardcode original inputs and kicadsexpr.
**Do not invoke them for this request.** A compatible supervisor must be adapted
and independently reviewed with synthetic retention tests and actual capability
proof before admission. Native command success requires version/export exits,
logs and result semantics; retained inventory/size/SHA256 must be independently
verified before cleanup. Preserve failures and partial receipts honestly.

Then run the source-only comparator on the retained XML:

```sh
python3 scripts/architecture278/implementation/stage18_observation.py \
  --netlist <fresh-run>/retained/netlist.xml --output <fresh-run>/xml-parity.json
```

Expected coverage remains118references/561observedpins/154unitUUIDs, including
22excluded annotations and all196explicit NC endpoints. Missing coverage, wrong
identity, metadata substitution, rewiring, NC shorts or collision fails closed.
Obtain independent review of actual retained results. RUN002's historical FAIL
is immutable and cannot become PASS through synthetic XML or this source repair.
No ERC/DRC/PCB/routing/simulation/hardware action is authorized.19passiveMPNs and
DIN/land footprints remain procurement/PCB blockers. No electrical acceptance.
PR286 remains draft/unmerged and PR260/277/285 remain parked.
