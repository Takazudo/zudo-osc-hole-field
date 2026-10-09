# Prepared finer ground batch

The complete saved252-group screen yields39 positive groups. Deterministic pair-spacing selection retains38 groups/382objects/38vias and excludes J900215.2 because its proposed via center is0.025mm from another proposed via. Every ground segment remains0.3mm wide; vias remain0.6/0.3mm; no cuts. This is not native acceptance.

Wait for core run37936741388 to finish and reconcile its result. Then invoke the route-venv `rebase_proposal.py --accepted-sha256 ACTUAL_PUBLISHED_SHA256`. The helper permits only the exact known26-object U1513 addition or no change, preserves every prior complete copper block including duplicate UUIDs, and fails on unknown changes or cross-net conflicts. It has not been run on any future output. Never dispatch another core writer until the current writer is terminal. The pinned native prepare step and all ordinary merge gates are still required.

Static proposal/proposal checking found one conflict with the still-pending26-object U1513 proposal: J900237.2,minimum copper gap−0.3375mm. This is not an accepted-board rebase. If and only if that exact26-object stage is natively accepted, run `select_candidates.py --exclude-pad J900237.2` to omit that entire unaccepted ground transaction, then run the rebase helper with the actual published hash and inspect its complete retention/clearance proof. If core26 rejects, keep the38-group selection. Other original positive groups pass this static comparison, but full actual-output and native checks remain mandatory.

Core26 run37936741388 is now fully reconciled/rejected1441→1442 for two original ground splits, with no canonical core change. The complete38-group selection was rerun without the conditional J900237 exclusion and explicitly rebased on accepted a0e3cff1ebc211564b8be10f6a993d50fb6d4372edde86a056ebc8dda3ea5932. All133169accepted objects are retained;382ground-only additions/38vias/no cuts. plan.json pins the actual proposal. Native acceptance remains required.

## Terminal result and warning-cap blocker

Run37950004600 rejected1441→1402 solely for one newly reported hole_to_hole identity. All133169previous objects survive,+382/zero cuts,0DRC/parity,no original pad-group splits,fresh agreement. The two warning vias have exactly unchanged complete serialized blocks in baseline,candidate,fresh. Native pad/outline/keepout/layer geometry and project/rule bytes also match. `retention.json`, `rejection.json`, `artifact.json` preserve evidence; `reconcile.py` reproduces the proof from the artifact. Canonical core stays1441. No warning waiver or gate change was made.

Exact KiCad10.0.6 source (`warning-cap-sources.json`) hardcodes199 reports for hole_to_hole (drc_engine.cpp ERROR_LIMIT and RunTests); clearance/unconnected use499. All three native reports contain199 hole_to_hole,199 silk_overlap and199 silk_over_copper warnings. `--all-track-errors` does not remove this per-code cap. Thus unchanged totals cannot prove absence of new warnings, and newly selected old identities cannot safely be dismissed merely by counting.

Possible next engineering work: an uncapped, pinned-native hole audit with exact native rule/epsilon/layer/slot/microvia semantics, fixture regression tests and before/after full-board evidence. Installed local pcbnew exposes no DRC_ENGINE/EvalRules API; localKiCad9 is not acceptance. This audit is NOT implemented or validated. The ordinary strict gate remains unchanged. Do not rerun the same rejected proposal hoping report ordering changes; do not adopt1402.

The independent19-segment no-via signal successor has now rebased onto unchanged accepted core a0e3cff1 with all133169objects retained. It remains subject to all existing native gates.
