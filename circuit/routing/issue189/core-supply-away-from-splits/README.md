# Supply subset away from observed ground regressions

Core143 native run37925863664 was rejected, despite109 joined supply edges, because existing AGND groups split and a new warning identity appeared. This saved subset excludes15 of109 supply transactions within3mm of pads in the smaller split pieces and excludes all four ground fanouts. It retains94targets/120segments, all0.25mm wide, without vias or cuts. Proximity is an explicit heuristic, not causal attribution or a safety proof.

The subset is tied to the original acceptedcore1441 input. It is NOT rebased, dispatched or accepted. Reconcile active core37950004600 first, preserve every accepted addition, then recheck compatibility and full native topology. Prefer the separately prepared ground batch as the next core experiment; do not launch competing writers. The existing reported hole-warning pair is unchanged in native input/output, but the warning gate is not waived.

Core26 is now rejected and canonical core remains1441; the active successor is ground run37950004600. Static comparison of this94-case/120-segment supply subset against its382ground objects finds one conflict: the entire U4439.4 +12V case (two segments) has minimum gap0.1947073557mm, below the conservative0.25mm requirement. If and only if those ground objects are accepted, omit or redesign that complete unaccepted supply case before rebasing (93cases/118segments would remain). This is not causal proof of fill preservation or native acceptance; the source proximity heuristic and all original native gates still apply. Never remove accepted ground copper to fit this proposal. Exact case UUIDs and both proposal hashes are in pending-ground-gaps.json.


A guarded future replay is now prepared, but has NOT been rebased or dispatched. After reconciling the sole core writer (and any intervening short-signal trial), run:

```sh
.circuit-cache/route-venv/bin/python circuit/routing/issue189/core-supply-away-from-splits/rebase_proposal.py --accepted-sha256 ACTUAL_ACCEPTED_SHA256
```

The helper retains every original full copper block and accepts only exact whole known ground382 and/or short-signal19 additions, with native geometry checked rather than UUIDs alone. Unknown changes or partial known batches require explicit reconciliation. It excludes whole unaccepted supply cases with less than0.25mm gap to accepted new copper and records every exclusion. It never removes accepted copper. On unchanged core all94cases remain; against the exact ground382 proposal it excludes U4439.4's entire two-segment case, leaving93cases/118segments. Five regression tests pass, including partial/unknown accepted additions and missing case membership. Workflow YAML and all12shell steps pass syntax checks. Actual native serialization and native acceptance are still unrun.

After reviewing generated proposal/plan/rebase receipts, commit and push a dedicated worker and use `gh workflow run routing-benchmark.yml --ref NEW_WORKER -f board=osc-core -f recover_core=true -f core_replay=supply-away-from-splits`. The short19 signal trial remains the preferred immediate successor. Do not overlap core writers; all original native gates apply, including preservation of AGND fill and warning identities.
