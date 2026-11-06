# Stage16: executable A01 source handoff for future native verification

Preparation starts at `07d045df573b15e00259200259d44b04fe5f7e8a`. **Prototype availability is unconfirmed.** No schematic/PCB materialization, native execution, ERC/DRC, simulation or hardware acceptance is claimed. This packet is a reproducible input set and explicit work contract; it is not a ready-to-fabricate board.

## Runnable now: export the frozen candidate

From the existing checkout, with Python3 only:

```sh
python3 scripts/architecture278/implementation/stage16_inputs.py --check
python3 scripts/architecture278/implementation/stage16_handoff.py --check
python3 scripts/architecture278/implementation/stage16_handoff.py --export-run a01-preflight-001
python3 scripts/architecture278/implementation/stage16_handoff.py --verify-export a01-preflight-001
```

The export creates a **new**, local ignored directory at `design/architecture-278/implementation/stage16/runs/a01-preflight-001/`. Existing run directories are refused. It writes candidateJSON, BOMCSV, pin/net/NC CSV, a SHA256 manifest and exact copies of every bound input. The roughly90MB native reference files are copied only into that ignored bundle; they remain historical reference sources, not newly materialized candidate CAD. The exporter permits at most512MiB of source inputs and never invokes a native executable. The manifest is written last; partial exports cannot pass verification. Verification checks complete membership, current input hashes and semantic payload equality, not just a self-consistent edited manifest.

`inputs-report.json` is the full inspectable record. It binds86 circuit packages,291 physical pins (271connected+20NC),120 logical units and108power/return endpoints. The package partition is26core,51jack,2control and7fixedpanel packages; these source group names do not themselves establish finished PCB outlines or a full assembly BOM. Connector/harness/transport contracts are separately retained with the graph; connector populations, library binding and board-frame materialization remain explicit adapter obligations. Allocated graph lengths remain distinct from routed copper.

## Exact candidate inputs and native differences

| Candidate authority | What must be carried into the isolated native design |
|---|---|
| Stage10 inventory + Stage15 package overlay | Exact fitted circuit population, unit/power-pin coverage and retained roles. Selected MPN may be null; do not choose an unspecified part silently. |
| Stage13 capacitor input/package report | C7101 KEMET T491C475K050AT and C7102 T491D226K035AT, declared polarity, frozen pad/land geometry and poses. Old captured C0603 assets are explicitly **not** candidate footprints. |
| Stage15 package input/report and candidate footprint | RN7101/RN7102 Analog Devices LT5400AIMS8E-2#PBF; six former R7121–R7126 removed; all12old endpoints mapped to resistor elements. Both EP9AGND; unused RN7102 element endsNC. EP9 is outside the four resistor-element units, not an omitted pin. |
| Stage15 interfaces/paths/rebudget | Full pin/net/NC graph, connector/header/DIN/wire relationships, upstream boundaries,271local paths/21crossings/108power-return targets and both resistance-domain comparisons. No copying of old routing claims. |
| Locked placements and candidate poses | Preserve exact fixed centres and all frozen candidate coordinates. Define and verify native board coordinate origin, face and rotation transforms; do not interpret worldXYZ as nativePCBXY without a checked transform. |
| Stage15 procedure/detent decision lineage | Manual OFFSET continuously set by ear/meter; exact Bourns PTV09A-4020F-B104 option0 has no centre detent. No knob-position voltage promise.2mV postfactory static and1mV same-setting load criteria unchanged. Proposed measurements remain unadopted/unexecuted. |

The packet hashes the existing `schematic/sheets/offset.kicad_sch`, `boards/osc-core/osc-core.kicad_pcb`, `boards/osc-jack-right/osc-jack-right.kicad_pcb`, and `boards/osc-control/osc-control-layout.kicad_pcb`, then extracts only relevant source fields without KiCad. They retain90old circuit packages, including the six discrete resistors and old capacitor assets, and lack RN7101/RN7102. Their coordinates, netlist and copper are **not bound to this split-board candidate**. Internal native net names are often hashed: a literal name difference is not diagnosed as an electrical defect without an independently established alias map. Isolated matching fields do not prove native parity.

The source packet exposes these concrete blockers to materialization:

- Two KEMET candidate footprints have not been materialized from the frozen scalar land geometry; polarized capacitor symbol binding is missing. Reusing the captured0603 reference would be wrong.
- The LT5400 candidate footprint exists, but native symbol/unit/EP binding has not been materialized. It must retain all four elements and the shield pin, including unused ends.
- Nineteen exact passive MPNs remain unspecified: C7104,C7105,R7101,R7102,R7103,R7106,R7108,R7110,R7112,R7113,R7114,R7115,R7116,R7119,R7120,R7130,R7131,R7132,R7135. Their retained values/pins/footprints are exported; no new component selection occurs. They may remain marked unresolved for source capture, but cannot constitute an exact procurable prototype BOM.
- No candidate-specific schematic/PCB adapter currently consumes all86package rows plus transport into isolated native files. Library tables, connector representations and native frame/face transforms must be materialized and source-reviewed before native parity can be assessed. No route/board completion is implied by this packet.

The minimum next source work is therefore explicit: consume the exported package/transport contracts, materialize only the missing symbols/footprint bindings from existing approved geometry, implement the isolated A01 schematic/PCB adapter and its source parity tests, and keep unresolved identity dispositions visible. This does not authorize substitute parts or geometry changes. Any necessary new identity/geometry choice is a separate decision. Do not run aggregate regeneration to obtain a candidate: it writes canonical sources and invokes excluded simulation/native checks.

## Exact-run admission and local/native environment

[execution-contract.json](stage16/execution-contract.json) records command templates, required evidence, allowed outputs and **proposed**, not granted, resource ceilings. No native launcher is provided, and a preparation manifest is not admission. Before any native invocation—including a version probe—the authorized operator must bind the actual source commit, all input/artifact hashes, exact argv, unique runID, isolated output root, exact oracle, enforced resources and timeout. No old campaign receipt or self-authored boolean supplies that authority.

The project wrapper is `scripts/kicad/run.sh`, pinned Docker image `kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`. Require exact KiCad10.0.6: the existing wrapper only checks10.0.x. Docker useslinux/amd64 and networknone, but the wrapper has **no CPU/RAM/wall-time caps**. Proposed ceilings for one A01 command are one concurrent run,2CPU,4GiB RAM,600seconds and512MiB output. These are not an approved budget or enforced configuration; admission must specify host-level enforcement or an explicitly approved alternative. The actual machine-wide heavy guard is also required; its shared slot/free-memory gate is not a per-job resource cap. Never run an uncapped command merely because the wrapper exists.

| Lane | What can run and prerequisites |
|---|---|
| Cloud now | Python source parsing, packet export/verification, unit tests and preservation checks. Docker/KiCad executable paths are present but daemon,image,version andpcbnew readiness were not probed. No native admission. |
| Local WSL/Linux after admission | Pinned Docker daemon/image, exact10.0.6 andpcbnew, actual host heavy guard and enforced resource envelope. Appropriate next native lane once candidate inputs exist. |
| Local Mac after admission | Pinnedlinux/amd64Docker or exact native10.0.6 viaKICAD_CLI_BIN. PATHPython must separately support matchingpcbnew for board construction; wrapper selection does not establish that. No equivalence or readiness assumed. |
| Cloud native later | Possible only with the same proven capabilities, output isolation, resource enforcement and valid exact-run admission. This task does not grant it. |
| Physical prototype | Existence unconfirmed. Manufacturing,purchasing,assembly,energization and measurement remain separate authorization/equipment tasks. |

Once a reviewed isolated `native/a01.kicad_sch` exists, the **first native action to request admission for** is the exact netlist-export command template in execution-contract.json. After that, independently extract package/pin/net/NC/MPN observations and compare them with the frozen packet. ERC is a distinct admitted command; no inherited228-warning allowance is transferred. Only after actual candidatePCB and schematic bindings exist, request PCB pad/net/placement parity and DRC. Unrouted opens must be reported, not normalized into success. No fabrication output is permitted.

The source-only comparator is executable now for an independently produced JSON observation:

```sh
python3 scripts/architecture278/implementation/stage16_handoff.py --compare-observation path/to/observation.json
```

Its schema is `kind=schematic_pin_net_observation`, exact`oracle_version=10.0.6`, `candidate_input_sha256`, native artifactSHA256, and`packages={ref:{pins:{pin:net_or_null},selected_mpn:...}}`. It rejects missing/extra pins/packages, NC/EP mistakes, MPN drift, version and input mismatch for the86circuit-package subset. Transport connectivity, symbol-unit coverage, footprints, placement and graph-edge parity remain separate unverified lanes. A passing supplied observation comparison explicitly **does not attest provenance, authorize execution, or prove ERC/DRC/physical acceptance**. Native log/artifact extraction provenance remains a required independent check.

## Deliverable boundary

All historical candidate evidence, canonical boards, fixed placements and protected decisions remain unchanged; KEEP_K1402_INCUMBENT remains in force. The source-only preparation tests and independent reviews establish reproducibility, not native readiness. PR286 stays draft/unmerged; PR285/260/277 stay parked. No architecture adoption, new component substitution, geometry change or native execution occurred.
