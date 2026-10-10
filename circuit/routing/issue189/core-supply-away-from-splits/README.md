# Terminal core supply trial: rejected

Run **38023611361**, source **47bb19a42f6612a114e4aff51c4b120301fe5e71**, timed out during supplemental zone-warning audit. Its native **1402→1311** count is not acceptable: two original AGND groups split, despite zero native DRC/parity errors. No canonical core copper was published; accepted core remains1402 with PCB SHA256fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10.

The1988-pad group becomes1985+3: **C4170.2 / U4145.12 / C4171.2** detach. A9-pad group becomes7+2: **C4270.2 / J900155.2** detach. Exact UUIDs, positions and membership are in `native-split-pads.json`; proximity alone does not prove which added supply case caused either split.

The source-bound118-segment proposal retains all133551old copper objects, removes none, and preserves3807nonrouting objects. Saved settled native snapshots are1402×3→1311×3/fresh1311×3. Artifact **11666004488**, ZIP SHA256 **0855bdbccdc250a3a273511b8d519cedc3f110a86cc0c887ac08a5f94596d8e4**. Before PCB b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66; merge/fresh4f90bfc16d5e338cc31adc3a41f0da8ff8f289a24b963ab8f9c9caf9d98cec10. Full warning proof and publication are absent. Do not resume the unchanged candidate's warning audit or adopt its lower count.

`reconcile_terminal.py` verifies this rejected immutable artifact without extracting all2.3GB. Place the verified ZIP at `/tmp/issue189-core-supply-terminal.zip` and run from the checkout:

```sh
bash "$HOME/.codex/scripts/heavy-guard.sh" -- /workspace/zudo-osc-hole-field/.circuit-cache/route-venv/bin/python circuit/routing/issue189/core-supply-away-from-splits/reconcile_terminal.py
```

The checker writes `/tmp/issue189-core-supply-partial-proof.json`. It verifies completed fixture/report hashes and ordered partial progress, not unrun native reconstruction or complete audit acceptance.

The new regression reproduces four unnecessary audit calls before the fix. `route_shards.merge` now rejects native errors, original-group splits, fresh disagreement and missing gain before supplemental audits. Eligible candidates still require complete warning evidence. All33affected tests and the circuit contract check pass; native CI remains required.

Continuation: use these exact split memberships to identify and repair or omit **whole** offending supply cases on an isolated branch based on current main. Preserve all accepted copper and0.25mm supply width. Require bounded native snapshots proving both original groups stay connected before the full warning/publication gates. Do not rerun this unchanged proposal with a larger budget. Issue189 stays open; no hardware qualification.

## Historical preparation (superseded by terminal evidence above)

# Supply subset after the accepted ground transaction

The original core143 native trial37925863664 joined109 supply edges but was rejected for original AGND group splits and a new warning identity. This saved subset excludes15 of109 supply transactions within3mm of pads in the smaller split pieces and all four ground fanouts. Its original94cases/120segments are full-width0.25mm outer copper, without vias or cuts. Proximity is a heuristic, not causal attribution or a native safety proof.

Ground worker38011194282/source44d1151cd41f285d5168c433c76664c44a3d97ac is now terminal and independently validated:1441→1402, all133169prior copper objects retained plus344segments/38vias, zero cuts/native DRC/parity errors. Botcebde33e63436b22e257ee29c419c305f8bed08f publishes PCB SHA256fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10. All five exact-head checks passed. PR218 and JR PR220 are integrated at maind25854092d89fa1253d05c95c21a225629f8c3f9 (JL118/JR133/core1402); post-main CI38023410816 is running. The guarded rebase completed (PASS18s), retaining all133551current core copper objects and selecting93cases/118segments. Native serialization, dispatch and acceptance remain UNRUN.

The committed proposal is reproducible against the integrated board with:

```sh
.circuit-cache/route-venv/bin/python circuit/routing/issue189/core-supply-away-from-splits/rebase_proposal.py --accepted-sha256 fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10
```

The helper retains every original full copper block and permits only exact whole known ground382 and/or short-signal19 additions. It checks geometry as well as UUIDs, rejects unknown or partial batches, excludes whole unaccepted supply cases below0.25mm separation, and records each exclusion. Against the accepted ground382 geometry it omits the entire U4439.4 +12V two-segment case (gap0.1947073557mm), leaving93cases/118segments. Never remove accepted ground copper to fit the proposal. Five existing guard regressions cover partial/unknown additions and missing membership.

The replay workflow now requires `--complete-native-warnings --native-zone-batch-size 16`, preserving all four audits, source-derived additive scope, all original findings, settled/fresh connectivity, original pad groups and native publication equivalence. Its argument regression failed before this fix and passes afterward;33 targeted tests pass. The source-scope fix3553574 is required because the old standalone382/38 mask defaults cannot validate this118-segment scope.

Review and commit generated proposal/plan/rebase receipts on an isolated branch based on integrated main, then check that no other core writer is active before dispatch:

```sh
gh workflow run routing-benchmark.yml --ref NEW_WORKER -f board=osc-core -f recover_core=true -f core_replay=supply-away-from-splits
```

Record the exact commit, input/output/artifact hashes and run ID. Own the run through terminal artifact reconciliation and all complete warning audits; workflow success alone is insufficient. CLI currently returns401 and the connected app has no dispatch tool, so dispatch needs the existing authorized host/user path. Do not change credentials or omit any native gate. Keep issue189 open; this trial does not imply hardware qualification.

The resulting proposal SHA256 is56121445db0986dbf846fd4e7f95339bd195f101ae876b8106353f4112b1564d. All118objects are0.25mm outer segments; zero vias or removals. The complete U4439.4 case is recorded in rebase.json as excluded; the current accepted ground382objects are retained exactly. All33 targeted tests and five rebase guards pass on this refreshed branch. Main PCB files remain byte-identical.
