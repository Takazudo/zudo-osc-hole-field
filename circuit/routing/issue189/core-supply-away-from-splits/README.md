# Supply subset after the accepted ground transaction

The original core143 native trial37925863664 joined109 supply edges but was rejected for original AGND group splits and a new warning identity. This saved subset excludes15 of109 supply transactions within3mm of pads in the smaller split pieces and all four ground fanouts. Its original94cases/120segments are full-width0.25mm outer copper, without vias or cuts. Proximity is a heuristic, not causal attribution or a native safety proof.

Ground worker38011194282/source44d1151cd41f285d5168c433c76664c44a3d97ac is now terminal and independently validated:1441→1402, all133169prior copper objects retained plus344segments/38vias, zero cuts/native DRC/parity errors. Botcebde33e63436b22e257ee29c419c305f8bed08f publishes PCB SHA256fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10. Its exact-head CI is running; canonical main still holds core1441. This supply proposal is NOT rebased, dispatched or native accepted.

After the ground increment is integrated and its exact accepted bytes are refreshed, run:

```sh
.circuit-cache/route-venv/bin/python circuit/routing/issue189/core-supply-away-from-splits/rebase_proposal.py --accepted-sha256 ACTUAL_ACCEPTED_SHA256
```

The helper retains every original full copper block and permits only exact whole known ground382 and/or short-signal19 additions. It checks geometry as well as UUIDs, rejects unknown or partial batches, excludes whole unaccepted supply cases below0.25mm separation, and records each exclusion. Against the accepted ground382 geometry it must omit the entire U4439.4 +12V two-segment case (gap0.1947073557mm), leaving93cases/118segments. Never remove accepted ground copper to fit the proposal. Five existing guard regressions cover partial/unknown additions and missing membership.

The replay workflow now requires `--complete-native-warnings --native-zone-batch-size 16`, preserving all four audits, source-derived additive scope, all original findings, settled/fresh connectivity, original pad groups and native publication equivalence. Its argument regression failed before this fix and passes afterward;33 targeted tests pass. The source-scope fix3553574 is required because the old standalone382/38 mask defaults cannot validate this118-segment scope.

Review and commit generated proposal/plan/rebase receipts on an isolated branch based on integrated main, then check that no other core writer is active before dispatch:

```sh
gh workflow run routing-benchmark.yml --ref NEW_WORKER -f board=osc-core -f recover_core=true -f core_replay=supply-away-from-splits
```

Record the exact commit, input/output/artifact hashes and run ID. Own the run through terminal artifact reconciliation and all complete warning audits; workflow success alone is insufficient. CLI currently returns401 and the connected app has no dispatch tool, so dispatch needs the existing authorized host/user path. Do not change credentials or omit any native gate. Keep issue189 open; this trial does not imply hardware qualification.
