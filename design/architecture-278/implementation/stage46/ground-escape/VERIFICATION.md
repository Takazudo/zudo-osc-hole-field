# Stage46 verification and replay

The following commands passed using the installed numerical environment
`/workspace/shared/osc-ci-python/bin/python` (abbreviated `python` below):

```
python -m unittest scripts.checks.test_ground_escape scripts.checks.test_connectivity_inventory scripts.checks.test_b2_specific scripts.checks.test_b2_specific_settlement -v
python -O -m unittest scripts.checks.test_ground_escape scripts.checks.test_connectivity_inventory scripts.checks.test_b2_specific scripts.checks.test_b2_specific_settlement -v
python design/architecture-278/implementation/stage45/connectivity-inventory/verify_bindings.py
python -O design/architecture-278/implementation/stage45/connectivity-inventory/verify_bindings.py
pnpm circuit:check
pnpm check
git diff --check
```

45 tests passed in each Python mode (5 Stage46, 12 Stage45, 28 Stage44).
The Stage44 tests print acceptance for a synthetic fixture; that is not a newly
accepted board. Seven historical checkpoint bindings and four Stage41–44 review
manifests passed in both modes. Full historical suites were not rerun locally;
exact-head CI is the aggregate/history check. Both pnpm checks passed, retaining
68 manual inventory lines and zero declared placements; no sourcing qualification.

`analyze.py --export` generated geometry.json from the pinned local native dump
and corrected fill export; running it without --export generates results.json.
The tests replay every result and the complete local export, check area/witness
consistency, and verify that removing obstacles or adding a ground target changes
the result. Clean-checkout CI skips the full export replay when ignored native
inputs are absent. Portable geometry/results remain testable there; complete
native ancestry is locally verified with exact artifact hashes, not recreated
by that CI skip. Native and canonical board hashes remain unchanged.

## Native/search commands and first failures

Each evidence/*.sh driver was run under:

```
bash /home/agent/.codex/scripts/heavy-guard.sh --label <stage46-label> -- bash .circuit-cache/stage46/<driver>.sh
```

The guard serializes native/heavy work. probe.sh and fill-probe.sh are read-only
native runs with installed KiCad10.0.6 via scripts/kicad/run.sh. corridor.sh and
plane*.sh are proposal-only numerical searches. They create no PCB. Replay only
with the exact inputs in local-bindings.json and installed versions; do not
substitute canonical JL or overwrite historical/native evidence. On a checkout
without those ignored inputs, use the portable source tests instead.

Four searches return real NOPATH/exit1/guardFAIL; these are not environment
failures. Their logs and search exports are retained. No new DRC/parity/refill,
stable native candidate acceptance, manufacturing or physical check is claimed.

The first detailed native fill probe failed with a missing loop variable in its
perimeter calculation. Its traceback is retained; the corrected rerun passed
with 117 opens and zero fill-witness mismatches. The initial source fixture chose
an unsuitable synthetic target point; it was corrected to a point beyond the
source island inside reachable copper. The initial export comparison compared
Python tuples against JSON lists, creating an enormous unittest difference;
the task-owned run was terminated and comparison normalized through JSON.
`tests-first.log` preserves the partial first failure, not a completed test run.
All five corrected source tests subsequently passed independently and as part
of both 45-test runs. Neither correction changes the analyzed geometry.

The SVG was generated from the same portable geometry. Direct file-URL browser
navigation was blocked by browser policy; rendering uses page content instead.
Optional Cairo/ImageMagick renderers were unavailable. No tool installation.

No canonical manufacturing output, previous stage or parent286 file is changed.
No Stage46 copper exists; 117 opens remain, and 476 Stage44 warnings are neither
waived nor rerun. CI outcomes are recorded externally with the final commit SHA.
