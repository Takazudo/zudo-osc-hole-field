# Issue 189 resumable implementation checkpoint

**Incomplete, unvalidated draft. Keep #189 open.** No fabrication, release,
merge, or physical/electrical qualification. Snapshot: 2026-10-08 20:00 UTC.
Branch `agent-fix/189-obstacle-transactions`, draft PR #190. Last published head
before this checkpoint: `5932578181ca9fa88991ae5067d6ec1ac6ed6f86`.
Main remains `1fe06ad50248d6434876fbf2bd6e32e1bfbb13bb`.

## Current accepted copper

| Board | Native open edges | Signal | +12V | -12V | +5V | AGND | Native errors/parity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| JL | 139 | 108 | 3 | 5 | 0 | 23 | 0 / 0 |
| JR | 162 | 128 | 0 | 5 | 0 | 29 | 0 / 0 |
| Core | 1509 | See baseline | See baseline | See baseline | See baseline | 252 | 0 / 0 |

Core's single-refill CLI report of 499 is a capped report, not the complete native
connectivity count. Read the full native dump. Completion requires all remaining
JL/JR/core connectivity obligations plus the issue's verification criteria.

JL adoption run **37826672368** passed independent native replay and committed
`e0efa3152f01bd343eb8597cedeb146d2d0ae4f3`. Canonical JL SHA256:
`09745a4e0d04dbfc7c1af6fcffb65430034d63e21434d2240f41944daba5607c`.
It retained **32667 physical copper objects**, removed 78 and added 117;
29946 tracks + 2838 vias remain. Eleven pre-existing duplicated UUIDs explain
why the original benchmark's unique-ID metric was 32656, not 32667. Full object
multiplicity is now checked. No legacy IDs were renumbered. All 1099 footprint
blocks, setup/outline, 128 source zone definitions (excluding derived fill caches),
and 250 other frozen context files including fixed panel requirements are unchanged.
See `jl-preservation.json` and `jl-retention-audit.json`.

JR retains all 50311 original copper objects (47236 tracks, 3075 vias). Its board
SHA256 remains `3d9bfccb3e201756fb7a32847f4b3c754f1a92bf22315115e150c239dbcc7f7e`.
Core remains SHA256 `34955f1f1ca3a31d897e54d890f4d2eac1877aacc828961624226366bf3e5382`.

## H1/H2 and implementation

`hypotheses-before.txt` records two failures against unchanged main:
H1 left removed routing-via drills in the hole mask; H2 softened fixed foreign
terminals. Regression tests now pass. Raster transactions distinguish fixed
terminal/drill ownership, surviving removable objects and committed paths;
rollback restores all occupancy and fill guards. Soft probes keep fixed foreign
pads and drills hard. Victim order is deterministic. Diagnostic causes are
explicit or `unknown`, never inferred merely from an exhausted search.

Native acceptance requires zero rule/parity errors, strict edge improvement,
no previous connected pad-group splits, no new warning identities, three settled
complete island-membership passes, and an independent saved-copy agreement.
Accepted copper has a base-hash-bound replay. New UUID collisions are rejected;
legacy duplicate IDs cannot silently collapse geometry in comparisons or deltas.

## Identical-input benchmark

Both variants use one frozen independently rechecked native input, pinned native
C A*, ten deterministic signal nets (short/long/high-island), 0.1 mm grid,
100000 expansions, one rip-up round, four victims, unchanged electrical rules.
The original exact result JSONs are preserved; corrected physical-object metrics
are separate retention audits, so result hashes remain valid.

| Board/run | Old native edges / stage seconds | New native edges / stage seconds | Useful accepted edges/hour |
| --- | --- | --- | ---: |
| JL / 37824198833 | 140→140 / 325.5136 | 140→139 / 328.8692 | 10.9466 |
| JR / 37824203279 | 162→162 / 327.2931 | 162→162 / 321.9534 | 0 |
| Core / 37824207235 | RUNNING | RUNNING | Not known |

JL routing-only times: 18.0550 / 24.3133 s; JR: 17.3206 / 35.0349 s.
Baseline native checks: JL334.0319 s, JR319.2444 s. These are bounded single-input
samples, not a broad speed claim. RSS measures Python only, not host/native peak.
`benchmark-artifacts.json` records artifact/result hashes and IDs. Core run uses
source `ba3aaba0bf651f3934904836737529bd0518241d`; do not duplicate it.

JL bounded follow-on **37828529257** finished 139→139 with zero added/removed
copper; its negative receipt is committed at 5932578. JR's three changed-method
local probes also produced no copper: finer-grid fill-guard rejection, protected
victim reconnect failure, and B.Cu-only no-path. See `jr-probes/README.md` for exact
inputs, commands and negatives. Native checks were NOT RUN for those empty
proposals. Stop these configurations; do not merely increase global budgets.

## Recovered concurrent core work

Separate branch `agent-fix/core-rrr-escalate` remains
`8315af554132b283e4e6e9b62d76bbfdcea560c0`, untouched. Run37775496177 finished with
seven failed shards, but retained partial deltas from all eight. The aggregate
failed to push its 100.11 MB filled board. All artifact digests were verified;
exact replay, original receipt and source deltas are under `concurrent-core/`.

The initial candidate1390 had failing copper; reverting eight nets produced1400.
This was **not** fresh-copy drift. The final historical native receipt had zero
rule/parity errors but AGND252→272; it is **NOT ADOPTED** under current membership
and warning gates. It adds1413/removes29 objects and retains132924 physical
objects (132916 unique UUIDs; eight legacy duplicate IDs).

Prepared recovery mode replays this exact aggregate, tries the existing AGND
stitching routine, then requires current settled/fresh native gates. This mode is
**NOT RUN**. Rejected proposals are retained. If a native-accepted board exceeds
95 MiB, publication removes only derived zone-fill caches, then requires native
refill equality of connectivity, warning identities and all pad/copper geometry.
The local cache-removal probe shrank104475412→49724128 bytes, but its native
refill equivalence is **NOT RUN** (`core-cache-probe.json`). No LFS or canonical
cache stripping has occurred.

## Verification and environment

Full CI **37825997275** at `19f1a9c181da76a6ff1509ff1bb1d2023e14ab9f` passed:
1211 Python tests, native fixtures, aggregate regeneration, documentation/site,
JL/JR/core native DRC/parity gates, P/EL and all five octave checks.
See `ci-19f1a9c.json`. This predates JL adoption and the later collision/cache/core
recovery changes; final integrated native CI is still required.

Current focused routing suite: **114 tests PASS**, including H1/H2, rollback,
complete membership/fresh-copy rejection, duplicate IDs, native cache-equivalence
rejection, and recovered-return gating. `pnpm check`, guarded `pnpm build`,
`pnpm check:site`, and `git diff --check` pass; the site scanner's one historical
workbench link remains explicitly allowlisted. No test or requirement weakened.

Local KiCad9.0.2 is not the required native oracle. Pulling pinned KiCad10.0.6
exhausted this32GB overlay; only this session's unused image was removed. Native
acceptance therefore runs in CI. Initial all-repository local Python discovery
stopped at an image-dependent fixture; it was not claimed passed locally.

At19:35UTC `gh` began returning401 Bad credentials; Git push could not obtain
credentials, including the exact supported escalation. GitHub connector reads
and branch APIs still work, but it exposes no workflow-dispatch action. Credentials recovered after environment restart at19:59UTC; authenticated reads
and git fetch now succeed. Workspace, staged files and prior personal context
survived. The interrupted blob upload never advanced the remote branch. Normal
Git publication and workflow dispatch can resume; do not substitute KiCad9 acceptance.

Personal startup context loaded completely once; do not rerun in this chat.
Snapshot `a4fd2a5bdfd2f137dce3bd5cc2af1d593d85ce4971449fe4fd163db0690d6b94`.
Runtime bridge restoration succeeded separately. This does not prove native
host discovery or delivery through a saved environment startup field.

## Exact continuation

1. Read current PR190/main/other branch heads and run37824207235. Preserve concurrent
   copper. Do not launch another same-input core benchmark while it runs.
2. When core finishes, download its artifact, verify GitHub's SHA256 digest, save
   exact result/proposals and inspect full component memberships, native errors,
   warnings and retained geometry. The single-refill CLI499 is not a final result.
3. Decide benchmark promotion versus recovered-core repair with explicit source
   hashes. Both start from the current unchanged core. A changed canonical core
   makes the preserved aggregate stale; reconcile disjoint source deltas without
   overwriting successful copper before any further replay.
4. With a working authenticated CLI, run one reviewed writer at a time:

```sh
gh workflow run 378789207 --ref agent-fix/189-obstacle-transactions \
  -f board=osc-core -f recover_core=true
# Native-capable local equivalent, under the required heavy guard:
bash "$HOME/.codex/scripts/heavy-guard.sh" -- .circuit-cache/route-venv/bin/python \
  scripts/pcbgen/route_shards.py merge osc-core \
  circuit/routing/issue189/concurrent-core/aggregate-copper.json \
  --label issue189-recovered --repair-ground
```

Recovery has a335-minute compute cap because measured core native refills take
about9minutes each. Search/electrical constraints are unchanged. Read final gates
and cache equivalence, not just a lower total. Fetch the resulting branch commit
before editing. Preserve failed receipts and exact replay even on rejection.
5. Continue source-defined local repair for JL/JR and remaining core obligations;
   do not repeat the documented zero-progress methods unchanged. Fixed panel,
   local bypass/circuit constraints and previous successful copper remain binding.
6. Run full integrated CI on the final branch head, including P/EL/octave gates,
   aggregate regeneration and documentation. Keep #189 open until all completion
   criteria are met; this checkpoint is not completion.
