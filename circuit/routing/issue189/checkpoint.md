# Issue 189 resumable implementation checkpoint

**Incomplete, unvalidated draft. Keep #189 open.** Snapshot:2026-10-09 03:17 UTC.
PR#190 merged normally at `da615cc059e56709c47c38a9af7ab175d55ca2c0` after all
five checks passed on `489c7d18af5be3d1ebef5f8ca901136bd9bce029` (run37877192529).
The user explicitly authorized incremental merging during development. No release,
deployment, fabrication or hardware qualification. Main was refreshed to that merge;
continuation branch is `agent-fix/189-routing-followup`.

## Active continuation after incremental merge

- Core reviewed replay37872907194 is still the sole core writer on retained branch
  `agent-fix/189-obstacle-transactions`. Do not delete that branch, overwrite its
  results, or dispatch another core writer. Inspect its terminal receipt/artifact,
  then bring any eligible result into a follow-up PR through normal checks.
- Main-push CI37878383977 is running and includes post-merge aggregate regeneration.
- JL coupled pilot37877201397 finished but was rejected:139→140. Its target improved
  by one while -12V5→6 and AGND23→24. Newly detached supply pads:
  U2102.4/U2117.11/C2148.1/C2118.1; ground pad:C2148.2. Zero native errors/parity and
  no new warnings. Original supply membership was not restored by plane fanout.
- A changed-method direct rail-link raster probe on that exact saved JL candidate
  found two paths/20 objects at the existing0.4mm width and0.25mm clearance, including
  the newly detached supply group. Four other original supply groups remain no-path.
  This is NOT native acceptance. The revised JL plan selects existing `rail-links`
  instead of repeating `rail-fanout`; all original-baseline acceptance gates remain.
- Canonical counts remain JL139/JR162/core1509 complete experimental edges. The
  committed core DRC report still has499 capped records. No new candidate adopted.

The read-only next command, once this continuation branch is pushed, is:

```sh
gh workflow run 378789207 --ref agent-fix/189-routing-followup \
  -f board=osc-jack-left -f local_repair=true -f local_mode=coupled
```

Check existing runs before dispatch; do not duplicate an active pilot. Exact
rejected results, verified artifact digests and probe scripts are retained beside
this checkpoint. See `return-repair-probes.md`. The sections below retain history;
the current merge/branch and terminal statuses above supersede older pending text.

## Current execution — 2026-10-09 03:00 UTC

Integrated CI37875608789 passed on52b3855, including all native fixtures,
aggregate regeneration, documentation and the three native DRC gates. The JR
coupled pilot37875619974 completed but was rejected: signal target closed,
-12V5→6 and AGND29→30, total162→163. Detached -12V pads are U4603.4/C4618.1;
AGND pad C4675.2 also split. One new dangling track warning remains. The existing
rail-fanout stage did not restore supply membership. Exact rejection, component
identities, gate and verified artifact digest are retained in jr-coupled-*.json
and benchmark-artifacts.json. No canonical board changed.

A bounded raster probe of the existing0.4mm/0.25mm rail-link stage on that exact
candidate also found zero paths (six failures,31.04s); no native claim or adoption.
Do not repeat the same fanout/link configurations. A next JR transaction needs a
different signal escape or explicitly source-defined local circuit repair.

JL has a separate hash-bound79-object proposal removing the three original local
segments. Three signal paths were found; J900001.7 remains unresolved. It is NOT
native checked yet. The read-only coupled CLI now accepts the explicit JL plan,
with the same supply restoration, independent reload and original-baseline gates.
Core reviewed replay37872907194 remains the sole canonical writer. The accepted
counts remain JL139/JR162/core1509 complete experimental edges (core committed
DRC file still499 capped records). Older sections below are historical.

## Terminal jack pilot results — 2026-10-09 02:35 UTC

JR37873299470 finished: baseline162, cut168, repaired/fresh163. Rejected for no
strict improvement, one split victim pad group, and new dangling track/via warning
identities. JL37874044551 finished: baseline139, cut141, repaired/fresh139; no
native errors, no new warnings or pad splits, but no strict improvement. Neither
pilot wrote canonical copper. Exact result/replay JSONs and verified archive
SHA256 digests are committed alongside `benchmark-artifacts.json`. Stop these
unchanged cut configurations.

JR diagnostics show the target and failed victim first finding paths rejected by
the -12V fill guard; fallback searches did not exhaust expansion budgets. A
bounded disposable signal probe found all seven local paths without treating that
intermediate signal-only topology as acceptable. `jr-coupled-plan.json` and its
hash-bound87-object proposal now define a read-only joint signal/supply pilot.
It requires native DRC/parity after the fixed signal replay, one existing-dimension
-12V restoration if native supply membership/count worsens, optional existing AGND
stitching, independent final reload and the full original-baseline promotion gate.
Ordinary routing's fill guard is unchanged. Failure to restore returns rejects
all candidate copper. This coupled native pilot is NOT RUN yet.

Core reviewed replay37872907194 remains the sole writer. Integrated CI37874044502 **passed on7e2ad15**, including aggregate regeneration,
native fixtures, docs and all three DRC gates (`ci-7e2ad15.json`). Do not duplicate either run. The committed core DRC file
has499 capped unconnected records and620 warnings (zero errors/parity); the
experiment measured1509 complete open edges at the exact canonical PCB hash.
Those reports/metrics remain distinct. Latest local focused suite:122 tests PASS.

## Resumed execution — 2026-10-09

Workspace and prior context survived restart; Git credentials work. Refreshed
main remains1fe06ad; current topic head9c7702bd adds only rejected recovery evidence,
no PCB. Integrated CI37836142683 **passed on7ca5bed**. CI37864988038 initially had
`action_required` with no jobs; the supported GitHub run-approval endpoint accepted
approval and its jobs are now running. No approval bypass or duplicate rerun.

Core benchmark37824207235 **completed**: old/new both1509→1499, both ineligible
because two prior AGND pad groups split. Neither introduced warning identities.
Old/new routing seconds117.2721/189.0070; complete stage3545.3150/4729.8022;
accepted progress/hour0 for both. Exact3.4MB result is `core-benchmark.json`;
artifact/digest and timing provenance are in `benchmark-artifacts.json`.

Recovery37836277044 **completed but rejected**:1509→1391, AGND252→263,
four split prior AGND pad groups, one new hole-to-hole pair and one new dangling
signal via. Native errors/parity0/0 and independent agreement were necessary but
insufficient. The canonical core remains1509. Exact replay/receipt were pushed
at9c7702bd; archive11587449567 digest is recorded in `core-reviewed/README.md`.

Next changed-method pilot is materialized under `core-reviewed/`: omit ten new
net transactions nearest detached AGND fragments, preserve all other recovered
rows and stitch links, and replace the overlapping eight-via signal cluster with
one retained via plus0.2mm fanout on existing signal layers. Hash-bound source
plan and generator produce1085 additions/29 removals. The source topology screen
and117 focused tests pass. Native run **37872907194** is now executing source `f637cc9`; no copper has
been adopted. Do not duplicate that writer. Read its complete receipt/artifact
before adopting another core proposal.

A separate **read-only** JR local repair is prepared in `jr-local-plan.json` and
`local_repair_pilot.py`: target RB4611.1, cut23 local objects from four blocking
signal nets within1.2mm, obtain native topology, keep padless fragments as boundary
obligations, and route only the target plus those four nets. It restores the -12V
fill guard and does not move parts or promote automatically. This is a changed
local branch method after the failed whole-net rip-up probes. JR native read-only run **37873299470** is in progress at `cca3c22`; do not
duplicate it. A JL plan uses the same bounded method for U2119.12↔U2117.13,
cutting only three local objects on one blocker net. `jl-short-connections.json`
records20 current native endpoint pairs against the exact accepted JL board SHA.
The JL pilot is not dispatched yet. Workflow input for future read-only pilots
is `local_repair=true`; the older running JR request used `local_jr=true`.

Concurrent branch `agent-fix/jack-replace-region-2` advanced to30db43e with JL140→140
and JR162→162 region attempts. It was read, not changed. Do not repeat that
unchanged strategy or overwrite this branch's accepted JL139 copper.

The sections below retain earlier evidence and commands; the resumed status above
supersedes statements that the core comparison/recovery or7ca5bed CI are pending.

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
