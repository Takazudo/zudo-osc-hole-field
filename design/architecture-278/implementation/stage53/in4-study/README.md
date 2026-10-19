# Stage53: In4 target-only routing study

Bounded disposable native repair; **no canonical adoption or hardware qualification**.
Start head d0d908ce2d09fa196febdf9ae4e93e26ee515163, existing draft PR287.
Parent286 and all prior stages remain unchanged. Starting board is the accepted
Stage49 disposable baseline `05f85d8cb27dcbeec76327065e91526f0112ebc316054a1cec5cae5cbc80c441`;
Stage50 assembly qualifications remain conditional. Neither rejected Stage51 nor
Stage52 copper is adopted.

## Scope and preliminary screen

Target `/F3/C945bba_SENSE` / native `XED7C19D453619667580D` connects isolated
R2316:2 to the existing 50-object group containing U2317:10 and D2303:3.
The one proposed new 0.60/0.30 mm ordinary through via is at
(227.980882,113.013236)mm, reached by a 0.20 mm B.Cu escape from R2316:2.
The onward path uses existing In4.Cu only, terminating at existing target via
(235.3,95.7)mm. It adds 19 In4 tracks, one B track and one via: 21 objects total,
no removals. Every added track is 0.20 mm. All footprints, positions, netlist,
stackup, rules, zone definitions, dependencies and unrelated routed copper stay fixed.

Before searching, `preflight.py` verified the prior seed's complete retained
partitions, screened the entry, and identified six existing target exits. New
seed geometry matches the earlier diagnostic; new UUIDs distinguish this proposal.
Entry copper/hole screen surplus is 0.013518 mm, B-track surplus 0.226141 mm.
These are design-rule geometry margins, not manufacturing tolerance budgets.
+12V has one 1025-object baseline partition; In4 is occupied by its pour.

Independent native fill inspection found one In4 +12V filled outline with 0.25 mm
clearance and 0.15 mm minimum thickness. A preliminary geometric cut toward the
closest exit leaves one normalized polygon; the direct track itself fails fixed
copper clearance, so it was never a routing proposal. The farther-exit cut creates
a tiny geometric island. `topology.json` records this approximate plausibility
screen; fractured polygon normalization and default polygonal buffers do not prove
native thermal/partition preservation. Actual routing was attempted only after
this screen. The retained grid dump omits fill geometry; its missing +12V island
entry does not mean free space.

## Native acceptance and limits

The 0.1 mm bounded source search succeeds without extra layer changes. Source replay
recreates proposal and search evidence byte-for-byte. The first fresh native build
passes 116→115 opens, zero rule errors, zero parity errors and 476 warnings.
The intended 1+50 retained target members merge. All other retained partitions
remain unchanged, including +12 V 1025, −12 V 1015 and every AGND component.
Complete native identity and dependency gates pass; uncapped warning inventory is
unchanged. Capped silkscreen identity nonregression remains unresolved.

Two separately applied fresh baseline builds have identical board bytes, complete
connectivity snapshots and acceptance results. `settlement.json` binds both native
runs and re-evaluates their gates. Accepted disposable board SHA256:
`27d2214492f9dd88483be014df4197fdb936cbbc7c445f17c8178cce97126560`. Source tests,
refill/DRC and independent review concern the disposable design only. 115 opens
still remain; no instrument or manufacturing validation is implied.

## Assembly and decisions

Only the seed adds a hole; the exit reuses an existing through via. The seed's
0.30 mm radius annulus intersects U2202 front and R2316 rear courtyards; its center
lies 0.225882 mm and 0.124118 mm from their respective boundaries. Courtyard overlap
proves neither collision nor acceptance. Exact populated bodies/terminations,
placement/solder tolerances and selected mask/tenting process remain unresolved.
No tenting override, special process or unsupported stiffness/current data is added.
Stage50 R8270 and earlier mechanical, harness/wire/flex/service unknowns persist.

Before any adoption, an unpowered integrated layout/mock-up review must:

- Bind exact U2202/R2316 body and termination envelopes and population face.
- Measure seed-annulus/drill clearance against bodies, solder and assembly access,
  including placement, board and process tolerances; require positive worst-case
  clearance under the selected assembly criteria. No threshold is invented here.
- Select and verify mask/tenting treatment without obstructing contacts or service.
- Resolve the independent Stage50 R8270 and earlier harness/service measurement gates.

Parent may retain this accepted disposable baseline for a separately selected
routing task; canonical adoption is a separate decision after unresolved assembly
and wider gates. No further routing target is started here. If parent chooses to
reject the assembly site, the practical choices are a separately scoped alternate
entry/process study, explicitly authorized local rerouting/placement changes, or
leaving this target open and selecting another. More micro-experiments are not
started automatically. No fabrication, order, energisation, release or merge.

[Power budget and distribution pointers](POWER-BOUNDARY.md) keep the separate
zudo-pd capacity audit explicit. Topological +12V preservation is not ampacity,
voltage-drop, thermal, startup or power-source qualification.
