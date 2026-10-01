# Full K extraction preflight v1 — bounded review

Receipt `.circuit-cache/issue38-recovery/core-feasibility-v7/full-ground-preflight-v1.json`, SHA `08cae0f5cc93f6af603b512c19032bf864224333d07a8a4b0a9cfc459003e120`, reports2287 balanced functions,9 mains,219 barrels,2296 native AGND pads (including8 DNP), and TP990008:1/F.Cu reference. Its82 native/entry dependency hashes independently matched. Native export a5b6ab06… and entry494165de… match the previously reviewed v7 authority. Parent's guarded110s execution was not rerun.

The count/native admission logic is coherent: immutable native snapshot, complete source port selector, ordered balanced profiles, all2288 contacts/9mains/2287functions checked, final native/entry recheck. No solve or physical/electrical acceptance is claimed.

**v1 provenance gap:** the original script SHA `84506755cfc6c48b60b435e296a2547c32d9e95faa7c4357052127d993e3aa32` first records its own hash after extraction; its authority map does not include actual extraction/profile dependencies such as ground_volume_geometry, ground_reference, barrel_volume, copper_envelope or contact_transfer and contact-transfer-proposal.json. Their changes during the run could alter supports/collars without a receipt gate. v1 is historical execution evidence, not a fully frozen reusable extraction certificate. Do not append current hashes and call them original run inputs.

Root's subsequently observed script16841696… now freezes a source list and contact proposal at entry and exit-checks it. That is the correct repair direction. Complete the dependency closure: BarrelVolume uses conserved_flow.FlowForest; contact_transfer imports sheet_mesh/sheet_flux and their transitive helpers. Freeze the actual loaded repository module closure (or a complete explicit transitive list), retain immutable expected hashes, reject merge conflicts, and record the fixed extraction parameters/rho. An ordered profile-support digest makes the exact function set independently identifiable; counts alone do not freeze patch locations. A fresh guarded preflight receipt or an independently justified original-start snapshot is needed for final provenance closure. No rerun was performed here.

The future complete model still requires unchanged numerical/conservation/profile gates and physical source/contact/material/3D/primal/common+K acceptance. This preflight does not establish a finite-current bound or qualify the actual219 barrels.

Independent native count follow-up: all219 AGND holes belonging to the actual main component are unique, circular, plated and span F/In1/In2/B; they match the reported219 physical barrels. No hole was removed for this count check.


## Fresh preflight v3 provenance closure

**The v1 source-binding finding closes for fresh v3; v1 stays historical.** Script SHA `14084adb45feb841bde56040296523e933c4923e8295e6ff86a4fb7c3ed73979`; v3 receipt SHA `33f61b48cdb9f1337bae69aa9a31d019adedd6f0cf1d44ec915955624e34116a`. All102 declared dependency hashes independently match, including conserved_flow, sheet_mesh/sheet_flux/shared_interface, the loaded repository helper closure, preflight itself and contact-transfer-proposal.json. Startup expectations are conflict-checked against native authority and exit-checked without rebinding. The lazily used contact helper is explicitly imported before capture.

Receipt identifies refinement1/include_loads=True/main_strands=True/port_limit0, rho2.0643511349999997e-5 ohm mm, Python3.10.19/Shapely2.1.2, exact ordered profile-support SHA `14a2c34316988149b10cc1e21eb5510e274182ce902700489e2291e97ccd3d0a`, TP990008:1/F.Cu reference and all four active foils. It reports the previously reconciled1903 own+376GH+9main=2288 contacts/2287 functions,219 barrels,2296 native pads including8 DNP.

Two bounded mocked extraction fixtures independently reject a post-extraction change of conserved_flow.py and of contact-transfer-proposal.json before publishing any preflight receipt. Source admission and extraction were mocked only for these mutation tests; no full extraction/native/solver was run. Actual v3 execution is root's retained guarded evidence, not independently replayed. Support hash is checked as a retained identifier; this review did not regenerate the full patch list. Evidence: `38-boundary-manifest-preflight-repair-checks.json`.

No remaining concrete extraction-preflight provenance blocker found. The preflight remains a nominal geometry/function-basis check, not an FE energy/conservation result or physical/electrical qualification.
