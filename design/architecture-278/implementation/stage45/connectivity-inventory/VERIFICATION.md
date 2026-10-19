# Stage45 verification

Scope is source inventory/reuse analysis plus two failed bounded routing
proposals. No Stage45 candidate PCB exists and no Stage45 DRC, parity, zone refill,
manufacturing check or physical test is claimed. Stage44's accepted four-pass
native evidence remains historical evidence, not a rerun at this stage.

## Executed checks

```
python design/architecture-278/implementation/stage45/connectivity-inventory/generate.py --export
python design/architecture-278/implementation/stage45/connectivity-inventory/generate.py
python design/architecture-278/implementation/stage45/connectivity-inventory/generate.py --check
python -O design/architecture-278/implementation/stage45/connectivity-inventory/generate.py --check
python -m unittest scripts.checks.test_connectivity_inventory scripts.checks.test_b2_specific scripts.checks.test_b2_specific_settlement -v
python -O -m unittest scripts.checks.test_connectivity_inventory scripts.checks.test_b2_specific scripts.checks.test_b2_specific_settlement -v
python design/architecture-278/implementation/stage45/connectivity-inventory/verify_bindings.py
python -O design/architecture-278/implementation/stage45/connectivity-inventory/verify_bindings.py
pnpm circuit:check
pnpm check
git diff --check
```

Focused tests: **40 pass in normal and optimized Python**, including 12 Stage45
tests and 28 retained Stage44 gate tests. Stage44 gate tests use synthetic native
fixtures; their printed acceptance/hash is not a newly accepted hardware result.
Local Stage45 tests replay the complete open projection and geometry export from
the actual accepted ignored files. On CI without those large files, the two
local replay tests explicitly skip; the portable source tests still run.

Seven historical checkpoint bindings and all four Stage41–44 review manifests
pass in both Python modes. This is bounded binding verification, not a repeated
full historical test execution. Exact-head CI supplies full historical/current
tests and aggregate regeneration. CI results are reported externally after push,
with exact tested SHA, rather than predicted in this pre-push file.

Both pnpm checks pass. The component check still reports 68 manual lines,
**0 declared placements**, and no schematic/placement binding; pin-asset checking
is performed. No new inventory or sourcing qualification follows.

## Real failures retained

```
bash /home/agent/.codex/scripts/heavy-guard.sh --label stage45-ground-proposal -- bash .circuit-cache/stage45/propose.sh
bash /home/agent/.codex/scripts/heavy-guard.sh --label stage45-ground-proposal-v2 -- bash .circuit-cache/stage45/propose-v2.sh
```

The first driver uses the existing pinned native KiCad 10.0.6 environment and
`scripts/kicad/run.sh` for `grid_dump.py`. The dump reports 3925 pads, 30975 tracks,
2890 vias and 117 native open edges. Numerical route proposals use the existing
`/workspace/shared/osc-ci-python/bin/python` environment. No tool installation.
Both guarded attempts exit 1 with NOPATH; guard verdict FAIL, approximately 11s
and 2s, minimum available memory 16676/16915MB respectively. This is not an
ENV_SUSPECT or deferred check. Empty proposal copper was never applied.
See `evidence/REPLAY.md` before replaying historical commands.

First source execution used incorrect octave netlist basenames and stopped with
FileNotFoundError before creating an inventory. The names were corrected to
`osc-octave-N.net` and `osc-stage-optical.net`. The first semantic hash gate
mistakenly hashed rail identities; it failed before running tests. The preserved
`evidence/first-source-test-failure.log` records that error. The gate now preserves
only the explicit generator rail allowlist and validates all other SHA256 tokens.
These were implementation failures, not hardware observations or waived checks.

Independent review found two portability/provenance issues: optional replay
needed both snapshot and PCB prerequisites, and the first historical driver
referenced a live helper later changed to three layers. Both replay tests now
check both prerequisites; the original helper is preserved and final replay has
an explicit rear-only switch and instructions. Final review covers these fixes.

## Preserved state and limitations

Only Stage45 files and its test-discovery wrapper are added. Accepted board hashes,
canonical manufacturing outputs, historical stages, fixed panel hardware,
interface assignments and parent PR #286 remain unchanged. Stage44's 117 opens and 476
warnings are not passed or waived. Its capped silk samples remain incomplete.
Local native dump/search hashes are in `evidence/local-bindings.json`; oversized
native artifacts remain ignored, with no Git LFS.
