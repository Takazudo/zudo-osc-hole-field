# JL bounded layer-domain pilot

Canonical JL remains118, board a01df89dcab3d4fab8eb0ae80195b2825d2d47adc517cd73452d9b9aa6ea079a. No canonical board changes. Related #189 remains open.

Four immutable saved obligations hit300000expansions with F/In2/In3/B. Eight same-input trials retain the0.025mm lattice,300000budget,6mm bounds, full obstacle/fill guards and existing electrical rules, but use F/In2/B or F/In3/B. GuardPASS43s. One F/In2/B trial succeeds for U2119.12–U2117.13:111segments/4vias, zero cuts/moves. The other seven failures are preserved. Narrowing the layer domain avoids competing search branches; this is not a router-wide speedup claim or native acceptance.

`probe.py SAVED_JL_DUMP` pins the accepted dump and baseline evidence from immutable35535749cf7f9f10dc3f2257767e3346250b3de1. `prepare.py` pins the sole whole candidate and read-only `jl-coupled-plan.json`. No ground restoration is inferred: any native original-group split rejects the pilot. The fixed panel, layers, source placement, electrical requirements and all successful copper remain unchanged.

Run the existing read-only native workflow on this exact branch with `board=osc-jack-left`, `local_repair=true`, `local_mode=coupled`. Check current runs first, record immutable source/run, and own through terminal artifact reconciliation. A positive ordinary pilot still requires fresh complete source-bound warning audits and all native publication/retention gates before adoption. Do not use raw capped-warning eligibility as complete acceptance. Never duplicate the independent core38011194282 or JR38018592247 writers.


## Native rejection and bounded return repair

Pilot38023623800 atc6fda679ba8cb58b9b1e3a85b1db2b08f7d0bda9 is terminal. Workflow success contains a REJECTED/NOT ADOPTED receipt: original C2148.2 AGND connectivity splits. The signal joins but net open edges remain118→118. Independent reconciliation PASS52s verifies all33421old copper objects retained+111segments/4vias, zero cuts,1111nonrouting objects unchanged, zero DRC/parity errors and477raw warnings. Candidate19f46a21e720c2d58156dedad30ea95d12f6d01047aac781cc3d115588297afe. No independent fresh stage or complete warning audit was run after the rejection, so neither is claimed passed. Original raw AGND group1387splits into1386+1; C2148.2 is the single isolated pad.

Artifact11660126174 is17118687bytes, SHA2565ac42049f7f6685e1b54f9f79eea0a640739e4bb2817fcbd2b6795011967a90e. native-rejection.json and reconcile_pilot.py preserve the independent check. Download through the GitHub app if the CLI artifact redirect is forbidden; verify the ZIP hash before running the checker under heavy-guard from this checkout.

repair_probe.py uses that exact rejected native geometry to try a full-width0.3mm direct AGND route and0.6/0.3mm plane fanouts at3mm/6mm, with0.25mm clearance,0.025mm grid,300000expansions and6mm bounds. All three are negative (PASS7s). repair-result.json preserves diagnostics and exact input hash; no repair proposal or follow-up native worker exists. Its initial preparation assertion compared raw island UUIDs against filtered pad-only memberships and failed before routing; corrected to exact raw original island equality. No production/native gate changed. Do not repeat these exact settings unchanged or claim physical impossibility. Main remainsJL118.


Three stronger search-only B.Cu protection squares around C2148 (half-width0.8/1.2/1.6mm) also fail on the exact original JL118 dump9d193cd9, with the same F/In2/B domain,0.025mm lattice,300000expansions and6mm bounds (PASS14s). protect_return_probe.py and protect-return-result.json preserve all negative trials. No physical keepout, changed PCB or new native candidate was produced. The initial invocation used the later pilot dump and correctly stopped at the immutable input-hash assertion before routing; rerun used the original saved input. Do not repeat these unchanged tests or infer physical impossibility.
