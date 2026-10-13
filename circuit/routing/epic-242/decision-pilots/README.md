# Issue 253 decision checkpoint

Interim disposition: BLOCKED_ARCHITECTURE_SELECTION / KEEP_K1402_INCUMBENT.
See `design/partition/core-split/decision.json`, `contract.json`, and the authored
`doc/src/content/docs/decisions/osc-core-split.mdx` decision matrix.

`check.py` is a read-only source join and saved-dump reader. It neither downloads
nor launches native tools. `source-lock.json` binds the reviewed integrated
10c51e44 input bytes. `artifacts.json` supplies durable run/artifact identities,
filenames and full ZIP SHA256 values; put authorized existing copies in any local
directory. No artifact is committed and no Git LFS is used.

```
python3 circuit/routing/epic-242/decision-pilots/check.py --check
python3 circuit/routing/epic-242/decision-pilots/check.py --check --artifacts /path/to/verified-zips
python3 -m unittest discover -s circuit/routing/epic-242/decision-pilots -p 'test_*.py' -v
python3 circuit/routing/epic-242/baseline/verify_inputs.py
pnpm circuit:check
pnpm check
```

`--check` compares recomputed fields with `verification.json`; without artifacts
it checks only the source section and does not imply a fresh artifact replay.
Missing ZIPs or wrong full hashes fail. The dump reader checks exact pad identities,
complete-set coverage, duplicated blank-net pads, ownership domains and recorded
open island memberships. It classifies all existing manifest targets against
candidate and K without inventing a landing or routing success. Replacing any
input requires reviewed source-lock/contract/report changes. Promoting this interim
decision requires a reviewed checker change too; editing a readiness flag cannot
silently admit production work.

Historical checkpoint result: four sensitive-signal samples have no recorded open demand.
Only three-C currently supplies an open signal pair; two-B's return pair is an
added partition obligation rather than a matched K repair. Remaining one-pad
supply/return samples require remote landings. Current manifests are not ready
for the useful-progress comparison; no native admission is requested now.

No new native evidence, uncapped warnings, full original-group preservation,
migration eligibility, #249 native annotation acceptance, panel-receipt refresh,
installed fit, calibration, order or energization is claimed. Aggregate
`regen-all.sh` is NOT RUN because it invokes native commands and changes canonical
outputs; no new parent admission exists. The historical panel provenance CI
failure remains independent and open. Current-head CI is not claimed by local
checks.

## Corrected source method

`matching-spec.json` and `matched-demands.json` now replace those unsuitable samples
for the proposed comparison, without rewriting historical lane manifests. All12
predeclared exact pairs are open on their K/two/three owners (nine board/domain
cases). Full group and touched-package/bypass obligations remain separately
recorded. `matching.py --artifacts /path/to/verified-zips --check` replays this
source result. `prepare_matched.py` creates a new private fixture; it performs no
native work. `route_matched.py` refuses to search without an admitted guard.
`evaluate_matched.py` replays raw full-warning proofs and tests exact closures
plus every return/rail obligation after and fresh. It never grants adoption.

See `native-proposal.md` for the complete minimal transaction, exact budgets and
stop rules; it is NOT ADMITTED. `owner-exchange.json` records disjoint path owners.
The original decision/verification files remain an explicitly historical source
checkpoint; the corrected method does not retroactively change their measurements.
