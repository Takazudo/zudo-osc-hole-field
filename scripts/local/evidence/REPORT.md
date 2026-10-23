# OSC +12V connection diagnosis on WSL (local containment)

This report is cumulative. Sections are kept in the order they were written, as
history; where a later stage superseded an earlier statement, the earlier text
stays and carries a `[superseded: ...]` marker pointing to the current conclusion.

## Current conclusions (2026-10-23)

- The two +12V pairs are connected once the +12V In4.Cu zone is filled; their
  open state on the published board is a missing fill cache, not a wiring gap
  (stages 2 and 3).
- A bounded native DRC was run on the unfilled control and on the single-zone
  candidate (stage 3); counts are capped and identical, and the identity delta is
  AGND ratsnest re-pairing only. No defect or improvement is claimed from DRC.
- The canonical flow fills before saving; the publication step strips fills on
  purpose above 95 MiB. No canonical writer fix is needed. The adopted response is
  option C: the diagnostic side fills selected zones on disposable derived copies
  and reads those (derived-fill path below).
- The AGND F.Cu zone fill (derive run 3) reaches U1105.12 only on an island with
  no via or track, so C1111.2 <-> U1105.12 is not explained by a missing fill
  cache; it is a candidate for human review, classified `UNEVALUABLE` while the
  B.Cu and In1.Cu AGND zones remain unfilled.
- Nothing in this report is board acceptance or a repair verdict.

Branch `claude/osc-synthetic-local-wsl` on top of PR #293 head 8bdf7703. Frozen
input commit fa16c6ff; `boards/osc-core/osc-core.kicad_pcb` SHA256
fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10 (identical on
main, at the frozen commit, and in the Windows reference copy). Every native run
used `kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`
with kicad-cli and pcbnew exactly 10.0.6, 1 CPU, 2 GiB, zero extra swap, 64 PIDs,
network none, read-only root and source mounts, owned-container records with
confirmed removal, through the machine-wide heavy guard. The original board was
never written; all CAD writes went to a container tmpfs. No DRC was run in
stages 1-2 (out of scope for the two-pair diagnostic) [superseded: stage 3 ran a
bounded native DRC on a disposable candidate, see below]. Nothing here is board
acceptance.

## Result: both pairs are open only because the +12V In4.Cu zone was unfilled

After filling only zone `265b1369-38aa-5a3a-b488-eb0aae22e998` (+12V, In4.Cu)
on a disposable copy of the whole frozen core, native connectivity reports:

| Pair | Before fill | After fill | After save + reload |
| --- | --- | --- | --- |
| C1129.1 <-> U1105.16 | separate clusters (3 and 4 items) | same cluster (1997 items, zone member) | same |
| C1131.1 <-> U1106.8 | separate clusters (4 and 3 items) | same cluster (1997 items, zone member) | same |

Path per endpoint (native cluster members before the fill, vias downcast with
`Cast()`, via positions in mm from the saved board):

- C1129.1 (F.Cu) -> 1 track -> via `b8ef9367-a253-51bc-a1c6-081b159913b4` at (123.8, 217.3), all copper layers, inside the selected fill.
- U1105.16 (F.Cu) -> 2 tracks -> via `124a4a80-065e-5fc9-8a64-4c25e5f56be2` at (123.3, 216.4), inside the selected fill.
- C1131.1 (B.Cu) -> 2 tracks -> via `d061a0b1-f9a5-50dc-80b9-4fa3b9b91b59` at (121.8, 209.1), inside the selected fill.
- U1106.8 (B.Cu) -> 1 track -> via `4eb15aa5-9666-5496-87ed-11a7491196b2` at (123.0, 209.8), inside the selected fill.

The layer transition is F.Cu or B.Cu -> via -> In4.Cu plane -> via -> F.Cu or
B.Cu. The merged cluster also contains all 490 +12V vias (488 of them inside the
fill) and 501 +12V pads; the board-wide unconnected count fell from 4283 to 3802.
No wiring repair candidate is needed for these two pairs. The stage 2 text
originally continued "the next minimal step is a zone refill before save in the
canonical flow" [superseded: the canonical flow does fill before saving and the
published copy is stripped on purpose, see "Why the published core is unfilled";
the adopted response is option C, the derived-fill path].

## Confinement evidence: the selected fill changed nothing else

Saved copy equals the input under the non-fill semantic hash; only the selected
zone carries `filled_polygon` (one outline, 404268 vertices); pinned counts
(123905 segments, 9646 vias, 351 zones, 5 copper zones) and the six duplicate
segment UUIDs with distinct geometry are preserved before, after and after
reload; zero pad/via flashing overrides; non-selected zones unfilled throughout.

Run timings: fill 69.8 s (run 1) and 79.9 s (run 2); payload 182 s and 194 s;
memory peak 1.57 GiB and 1.55 GiB with zero OOM events.

## Synthetic qualification: PASSED on run 4 after two fixture defects

Runs 1-3 failed the strict persistent-confinement check for reasons unrelated to
the core board: (1) pads and vias with `remove_unused_layers yes` persist
board-wide `zone_layer_connections` after a selected fill (confirmed in
`pcb_io_kicad_sexpr.cpp` 10.0.6; the core has none of these); (2) undeclared
footprint field UUIDs are regenerated on every load. Fixture v3 removes both;
run 4 passed every strict check including observable custom-rule effect and
positive/negative connectivity controls. Checks were never weakened.

## Evidence

`scripts/local/evidence/osc-synthetic/run-{1..4}` and
`scripts/local/evidence/osc-single-zone/run-{1,2}`: controller receipts, payload
receipts, capacity/resource and cleanup records, post-stop cleanup, wrapper logs.

## Stage 3: candidate exported and bounded DRC run; no +12V-related DRC change is observable

Candidate run 2 (tooling 18a3a6bd, 218 s, fill 57.9 s, peak 1.51 GiB) regenerated
the single-zone fill on a disposable copy and exported both boards with the pinned
project and rules to the host, where they were re-verified:

| Board | Bytes | SHA256 | filled_polygon zones | non-fill semantic hash |
| --- | --- | --- | --- | --- |
| before (load/save control, unfilled) | 49,818,236 | 6de99d66c171ee00... | none | a97c70f0809d8d43... (= input) |
| after (+12V In4.Cu zone only) | 60,880,206 | b9de2114a45c5d66... | 265b1369 only | a97c70f0809d8d43... (= input) |

The after board hash is byte-identical to both earlier diagnostic runs (the fill is
deterministic) and 60.9 MB is under the 95 MiB publication cap. Candidate run 1
exported the same files but its payload receipt exceeded its own output bound and
was refused; it is not counted. Artifacts with checksums are in the Dropbox cclogs
directory `zudo-osc-hole-field/osc-local-wsl/{candidate-run-2,drc-run-1}` (CAD
candidates are not committed).

DRC run 1 (tooling 18a3a6bd, 158 s, `kicad-cli pcb drc --format json --severity-all`,
no `--refill-zones`, 170 s cap per run, peak 1.99 GiB with zero OOM events; host
recomputation of both reports matched the payload summaries):

| Report | DRC time | Counts |
| --- | --- | --- |
| before (unfilled control) | 68.1 s | unconnected 499; hole_to_hole 199; lib_footprint_issues 199; silk_over_copper 199; silk_overlap 199; via_dangling 199; track_dangling 12; silk_edge_clearance 6; text_height 4 |
| after (+12V zone filled) | 87.5 s | identical counts |

The before counts equal the hosted prefill checkpoint of run 39793075070. Every
199 and the 499 are KiCad report caps, so counts cannot show the +12V change; the
+12V pair pads and the four bridging vias never appear in either capped unconnected
list. The identity delta is 6 removed and 6 added unconnected entries, all AGND,
with the same AGND pads (U1411.10, U1107.5, C2139.2, U2216.12) re-paired with a
different partner item: ratsnest re-pairing after reconnectivity, attributable to
the still-unfilled AGND zones, not to the +12V fill. No violation identity related
to +12V or the selected zone was added or removed. No new defect or improvement is
claimed from DRC; the quantitative +12V signal remains the native unconnected count
4283 -> 3802 and the two pairs' cluster merge. Memory peak 1.99 GiB during the
after DRC is at the 2 GiB cap and must be respected in any repeat.

## Why the published core is unfilled: fills are stripped at publication by design

`scripts/pcbgen/adopt_obstacle_benchmark.py` `publication_copy` (lines 48-64) strips
every `filled_polygon`/`fill_segments` via `scripts/pcbgen/zone_cache.py` when the
native-filled board exceeds 95 MiB, after a native refill-equivalence gate; the
receipt `boards/osc-core/reports/grid-routing/shards-issue189-finer-ground-batched-warnings.json`
records 440 fields removed (104,621,696 -> 49,819,556 bytes) for the current core
SHA. Every canonical writer fills before saving (`route_shards.py` merge via the
driver check at `route_jack_grid.py:116` with `--refill-zones --save-board`,
`route_kicad.py:77/99`, `prepare_source_planes.py:28`); the strip happens at
promotion (`route_shards.py:313-326`). The frozen OSC readers
(`scripts/ci/osc_frozen_topology.py`) read the published board without refilling,
which is the direct cause of the two open +12V pairs. Fix candidates considered: (A) let
`without_zone_cache` keep a chosen zone set (the +12V In4 fill adds 11 MB, well
under the cap) inside `publication_copy` with the existing equivalence gate; (B) a
one-time per-zone (never all-zone) refill script with the existing settled-fill and
fresh-SHA promotion gates; (C) refill the selected zones on a disposable derived
copy on the diagnostic side, leaving the canonical file and the publication
unchanged. Decision (user, 2026-10-23): C, with B-style shared helpers as internal
implementation; A stays deferred until a concrete reason appears that the
diagnostic side cannot solve. No canonical writer or publication change was made.

## Derived-fill path (option C): the diagnostic side now separates "unfilled, cannot evaluate" from "open with every net zone filled"

`scripts/local/osc_derived_fill.py` (pcbnew-free, shared by host and payload),
`scripts/local/osc_derived_fill_payload.py` (container, modes `derive` and
`evaluate`) and the `derive`/`evaluate` modes of the local controller implement
the decision: the canonical board and the publication are untouched; the
diagnostic fills only the zones named in a spec on a disposable copy, saves,
reloads, re-observes and exports the derived board with a composite identity.

- Identity key = SHA256 over the pinned source pcb/pro/dru hashes, the image id,
  KiCad 10.0.6, the sorted selected zone UUIDs, the process version and an
  optional parent derivation key. Any change yields a different key.
- Reuse of a saved derived board recomputes the real file hashes, the non-fill
  semantic hash against the current source and the fill ownership before anything
  native runs; a stale, altered or differently derived copy is rejected with a
  reason (`DERIVED_REUSE_REJECTED_NOT_ACCEPTANCE`), never used as evidence.
- Pair status vocabulary: `CONNECTED_ON_INPUT`, `CONNECTED_VIA_SELECTED_FILL`,
  `UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN`, `OPEN_WITH_ALL_NET_ZONES_FILLED`,
  `OPEN_WITHOUT_NET_ZONES`. Every row carries `repair_basis: false`; the host
  recomputes each class from the exported native observations and the full
  exported zone table.
- Offline regression tests (`test_osc_derived_fill.py`, 27 tests, with the fake
  worker integration flow) cover normal reuse, stale cache, changed source,
  chained derivations, mid-run worker failure, stage-cap timeout, incomplete
  receipts, tampered classifications and legacy adoption. Review (`/code-review`
  high) found ten items; the defects were fixed before the native runs, and the
  two de-duplication suggestions against the proven single-zone payload were
  deferred so its evidence-pinned output format stays untouched.

### Evaluate run 1: the saved +12V board was reused, not regenerated (PASS, not acceptance)

The candidate run 2 output was adopted through a sidecar (`derived-identity.json`,
image id from its receipt, KiCad version attested by the payload hash 899d5082 at
tooling 18a3a6bd) and evaluated against the current source: all recomputed checks
matched (identity 58088594..., board b9de2114..., non-fill a97c70f0...). 157 s
total, payload 134 s, peak 1.20 GiB, zero OOM, two owned containers removed.

| Pair | Before | After | Class |
| --- | --- | --- | --- |
| C1129.1 <-> U1105.16 (+12V) | open | connected (1997-item cluster) | CONNECTED_VIA_SELECTED_FILL |
| C1131.1 <-> U1106.8 (+12V) | open | connected (1997-item cluster) | CONNECTED_VIA_SELECTED_FILL |
| C1111.2 <-> U1105.12 (AGND, control) | open | open | UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN (601e02b2, e389d344, e67a5bc7 unfilled) |

Both AGND pads sit alone in clusters of size 1: F.Cu SMD pads with no attached
track, reachable only through the F.Cu AGND zone.

### Derive run 1: AGND In1.Cu zone alone leaves C1111.2 <-> U1105.12 unevaluable (PASS, not acceptance)

Spec: zone `e67a5bc7-b575-52b6-a78a-9c84381053da` (AGND, In1.Cu), pairs
C1111.2 <-> U1105.12 and the +12V pair as negative control. Fill 131.9 s (In1 has
no segments; 177 AGND vias and 5 through-hole pads connect), payload 259 s, peak
1.47 GiB, zero OOM; derived board 61,154,387 bytes, identity 682af66e..., only the
selected zone carries `filled_polygon`, non-fill semantics equal to the source.
Unconnected count 4283 -> 4103. Both pairs classify as
`UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN` (AGND: F.Cu 601e02b2 and B.Cu e389d344
unfilled; +12V: In4 265b1369 unfilled). No wiring claim follows from either pair.
Artifacts with checksums: cclogs `osc-local-wsl/{evaluate-run-1,derive-run-1}`.

### Derive run 2 (AGND F.Cu zone probe): FAILED at the 260 s fill stage cap; not rerun

Spec: zone `601e02b2-8ccb-5c28-83e5-03789d47fbbd` (AGND, F.Cu), same two pairs.
Prediction recorded before launch: the fill was expected to exceed the cap (22,481
F.Cu segments, roughly 6,700 F.Cu pads and 334 keepouts as obstacles, about 1,086
thermal connections, versus In1.Cu at 131.9 s with no segments). Observed: load
13.2 s, before-observation 15 s, fill started at 28.5 s and was still running when
the 260 s fill-group cap killed the worker (SIGKILL, exit -9) at 289 s; payload
295 s; peak 1.07 GiB, zero OOM; source hashes unchanged; both owned containers
removed and confirmed. No derived board was exported and nothing from this run is
evidence about connectivity. Time, not memory, is the binding limit for the outer
AGND zones at 1 CPU. A repeat needs a cause-addressing change (longer fill cap or
more CPUs, which exceed the delegated resource envelope, or a different confinement
strategy) and is therefore a decision item, not an action taken here. The B.Cu AGND
zone (1,204 pads, 21,730 segments) is in the same class and was not attempted.
Evidence: `scripts/local/evidence/osc-derive/run-2-failed`, cclogs
`osc-local-wsl/derive-run-2-failed`.

### Probe budget profile (fill 520 s): implemented and tested offline; the probe itself has NOT been run

The user approved (2026-10-22 19:56 UTC, relayed through the file-based
coordination channel) exactly one further attempt at the AGND F.Cu zone with a
longer fill cap and every containing layer grown to hold it. The chain is now a
named budget profile rather than edited constants, so the proven standard chain
stays byte-identical for every other run and the probe chain can only be selected
for its approved mode and zone:

| layer | standard | fill-520-probe |
| --- | --- | --- |
| derive stage caps prepare / fill / verify | 60 / 260 / 100 | 60 / 520 / 100 |
| worker deadline (payload - 40 s reserve) | 380 | 720 |
| payload | 420 | 760 |
| docker start --attach | 430 | 780 |
| wrapper (run.sh command) | 450 | 800 |
| controller | 590 | 890 |
| outer stop (process-group SIGKILL) | 600 | 900 |
| post-stop owned cleanup | 60 | 60 |
| heavy-guard --max-run | 720 | 1020 |
| output board bound | 64 MiB | 128 MiB |
| CPU / memory / extra swap / PIDs / network | 1 / 2 GiB / 0 / 64 / none | unchanged |

Containment of every layer is checked by `osc_derived_fill.budget()` and a
profile whose layers do not nest is a defect (tested). The wrapper selects the
profile through `OSC_BUDGET`, exports the outer stop it enforces, and the
controller refuses a profile whose outer stop differs from that export, so the
controller can never run a longer chain than the kill it sits under. The probe
profile covers only `--payload derive` on the published source for zone
`601e02b2-8ccb-5c28-83e5-03789d47fbbd`; evaluate, other zones, zone sets and
chained derivations fall back to the standard chain or are refused. The hosted
adapter is unchanged: only its `docker start --attach` ceiling is swapped for the
profile's attach seconds, with the same ownership record, labels and resource
flags. The payload reads the profile from `/spec/context.json` before any native
work, echoes it, and the manifest records it; the controller validates the echo
and the manifest against its own profile.

Two technical judgments were made here and are reported as such:

- The output board bound grows to 128 MiB for the probe only. The In1.Cu fill added
  11.3 MB (420,024 polygon points) to the 47.5 MiB source; the F.Cu fill has
  22,481 segments and about 1,077 SMD pads as extra obstacles and will add more.
  The standard 64 MiB bound leaves 17.3 MB and would kill the worker after a
  successful fill. 128 MiB plus the 47.5 MiB input copy fits the 256 MiB scratch
  tmpfs; the 2 GiB memory cap is unchanged (tmpfs pages count against it).
- The approved verify cap of 100 s is predicted to be tight. On derive run 1 the
  verify group took 91.9 s on a 61 MB board (after 12.2, save 16.6, reload 49.9,
  verify 13.2 s) and on candidate run 2 64.8 s on a 60.9 MB board; the
  F.Cu-filled board will be larger and reload time grows with it. The approved
  value is kept as approved. Whether to raise it (180 s fits the unchanged worker
  deadline of 720 s even when the fill uses its full 520 s) is a decision for the
  user, raised through the coordination channel before any launch.

Offline evidence: local suites 83 tests pass (`-B` and `-B -O`), hosted
`scripts/ci` 123 pass; logs in cclogs `osc-local-wsl/probe-budget-tests/`. No
native run was made for this section.

An independent `/code-review medium` of that commit returned seven findings;
six were fixed in the follow-up commit and one is deferred:

- The heavy-guard cap was recorded but never required. The wrapper now refuses to
  start unless `HEAVY_GUARD_MAX_RUN` (which heavy-guard reads as its `--max-run`
  default) is at least the profile's cap, and exports it; the controller records
  it and refuses a cap below the profile. The launch recipe sets the variable and
  passes no `--max-run` flag.
- The exported outer stop was an unauthenticated variable while the text claimed
  the controller "cannot" outrun the group kill. The controller now also refuses
  an exported outer stop unless it is the session leader that the wrapper's
  process-group kill targets, and the text says what the mechanism is: a
  consistency check between cooperating scripts, not authentication.
- The nesting proof used re-declared constants. The helper now imports the
  worker reserve and the output bound from the payload it governs; the two hosted
  values the bundle cannot import (cleanup reserve, scratch tmpfs size) are
  asserted against the hosted module when the controller loads, and the source
  board size assumption is checked against the real file on every run.
- The wrapper's second copy of the outer-stop table is gone; it reads the outer
  stop, the required heavy-guard cap and the cleanup window from the budget
  table through the controller's `budget` subcommand.
- Dead `PAYLOAD_SECONDS` / `DERIVE_CAPS` aliases in the derived payload are
  removed.
- Memory headroom for the larger output bound cannot be proven offline. The
  profile check now limits the tmpfs footprint (input copy plus output bound) to
  one eighth of the 2 GiB cap; the process peak for the F.Cu fill remains an
  observation the probe itself has to make, and an OOM kill would be a recorded
  result, not a surprise the chain is unprepared for.
- Deferred: the hosted adapter still sees the policy name `fill-430` while its
  attach ceiling is swapped to 780 s. The receipt records the swap
  (`adapter_execution_policy`); adding a named `fill-attach-780` policy is a
  hosted-controller change outside this local branch.

### Derive run 3 (AGND F.Cu zone, profile fill-520-probe): PASS as a diagnostic; both pairs still `UNEVALUABLE`; not acceptance

The single approved probe ran once, 2026-10-22 20:52:19Z to 20:56:41Z, under
coordinator slot `osc-moya-single-slot-dc40fc87-7c59-41a4-8451-984bd22d9aa7`,
tooling 4bc4a152, heavy-guard label `osc-derive-run-3-fcu-probe` with
`HEAVY_GUARD_MAX_RUN=1020`. Launch-time exclusion: 0 running containers, no KiCad
or heavy-guard process, LED session idle, no stop or cancel, 9.4 GiB available.

Observed: load 9.2 s, before 8.2 s, **fill 150.8 s**, after 8.1 s, save 8.3 s,
reload 12.8 s, verify 8.1 s; worker 208.5 s, payload 219.4 s, controller 238.9 s,
wall 261 s. Peak memory 1,692,078,080 bytes (1.58 GiB) under the 2 GiB cap, zero
OOM events. Both owned containers `REMOVED_CONFIRMED` with exit 0; post-stop
cleanup found no remaining records; the container set before and after the run is
identical; source hashes unchanged. Derived board 61,320,854 bytes (+11.5 MB over
the source), identity key `ecf170dbb48e07980d8c08e149ff6e5c223745b58cdd9f9abb09cfa4b5001d16`,
SHA256 `4a55e0c165efcc2215d920272da25476b54df1cc56ba59e95a31049b29ba4dc8`; only the
selected zone carries `filled_polygon` (236 outlines on F.Cu); non-fill semantics
equal the source; host re-verification passed. Unconnected count 4283 -> 3342.

Two predictions from earlier sections did not hold and are recorded as such:

- The fill finished in 150.8 s, well under the 260 s cap that killed derive run 2
  on the same zone, same image, same 1 CPU / 2 GiB container. The difference is
  not explained by this evidence; host contention during run 2 is a possibility,
  not a finding. The 520 s cap was therefore not needed, and neither was the
  verify cap question (verify group 37.3 s).
- The derived board stayed under the standard 64 MiB bound; the 128 MiB bound
  approved for this probe was not exercised.

Pair results (observation classes, not verdicts):

- `C1129.1 <-> U1105.16` (+12V, negative control): unchanged, both clusters as on
  the input; `UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN` because the +12V In4.Cu zone
  is unfilled on this derived board (it is filled on the +12V derived board, where
  this pair is `CONNECTED_VIA_SELECTED_FILL`).
- `C1111.2 <-> U1105.12` (AGND): still open after the F.Cu AGND fill. On the input
  both pads were clusters of size 1 (F.Cu SMD pads, no track, no via). After the
  fill, C1111.2 belongs to a 558-item cluster (447 pads, 85 tracks, 25 vias, the
  F.Cu AGND zone), while U1105.12 belongs to a cluster of exactly two items: the
  pad and the F.Cu AGND zone. The F.Cu fill therefore reaches U1105.12 but on an
  island that contains no via and no track. The class stays
  `UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN` because the B.Cu and In1.Cu AGND zones
  are unfilled on this board, and that is what the vocabulary says. The narrower
  observation for human review is this: an inner- or bottom-layer fill cannot
  reach an F.Cu island that holds no via, so on the current copper geometry the
  remaining AGND fills would not change this pad's cluster; a connection would
  need a via or track at that island, or a different F.Cu fill geometry
  (clearance, thermal relief, keepout or island-removal settings). This is a
  candidate for review, not a repair basis and not a defect verdict.

Evidence: `scripts/local/evidence/osc-derive/run-3/` (receipt, zone.json,
manifest, substages, post-stop cleanup, wrapper log, spec, cclogs checksum list);
cclogs `osc-local-wsl/derive-run-3/` (26 files including the derived board and
the state directory's resource records; `SHA256SUMS`
`c760369ae993081dc6ed543f55d1d29310c8c69c4e6e8a0e54d775704f42f88c`). No DRC was run.
Nothing here is board acceptance.

### Chained AGND profile (`chained-agnd`): prepared and tested offline for the approved single diagnostic; NOT run

The user approved (2026-10-23 02:46 UTC, relayed as coordinator instruction
`osc-moya-approved-queued-agnd-b6208767`, queue `osc-agnd-queue-26db12e7`) exactly
one chained Fill on the saved derive-run-3 copy: zones `e389d344` (AGND B.Cu) and
`e67a5bc7` (AGND In1.Cu), pairs C1111.2 <-> U1105.12 and C1129.1 <-> U1105.16,
the standard time chain (60/260/100, worker 380, payload 420, attach 430, wrapper
450, controller 590, outer stop 600, cleanup 60, heavy-guard 720), 1 CPU / 2 GiB /
zero extra swap, output bound 128 MiB. The run is queued behind an LED session's
reservation and has no OSC slot; nothing has been launched.

The profile is a table entry bound to its input, not only to its zones: it carries
the run-3 parent identity key (`ecf170db...`) and the parent board size
(61,320,854 bytes). The profile check requires the binding to be complete (key,
zones, input size), and the tmpfs and memory-share checks use the parent size
instead of the source size. `budget_allows` now refuses the profile for an
unchained derivation, for a parent whose identity key differs, and for any other
zone set or mode. The controller checks the parent's manifest identity and board
size before any side effect; the payload re-checks the parent key after its own
recomputed verification of the parent; the receipt records the bound parent key
and input size. Offline evidence: local 89 tests (`-B` and `-B -O`), hosted 123;
the chained integration test shows the expected outcome shape: with all three
AGND zones filled the AGND pair leaves `UNEVALUABLE` (to
`OPEN_WITH_ALL_NET_ZONES_FILLED` or `CONNECTED_VIA_SELECTED_FILL`) while the
+12V control stays `UNEVALUABLE` because In4.Cu is not filled. Logs in cclogs
`osc-local-wsl/probe-budget-tests/chained-agnd/`.

Unknowns stated before the run: no B.Cu fill has been measured; the combined
two-zone Fill from a 61.3 MB parent may exceed the 260 s cap, which would be the
recorded outcome of the single attempt; peak memory on the larger board is
unknown (1.58 GiB observed on run 3); this is the first native use of the chained
code path.

An independent `/code-review medium` of the profile commit (c4fa9f6e) returned
eight findings, all fixed in the follow-up commit:

- The binding now names the parent board file, not only its size: the profile
  carries the run-3 board SHA256 (`4a55e0c1...`); the controller checks the
  parent manifest's recorded hash, the real file hash and the size before any side
  effect, the payload checks the recorded hash and re-checks after its own
  verification, and the host post-run check compares the recomputed parent key
  and the mounted file against the table and against the receipt's recorded
  binding.
- `budget_allows` no longer passes a parent-bound profile when the parent key is
  unknown; callers read the parent's own manifest first.
- Unbound profiles may not declare an input size or parent hash; a bound profile
  must declare a positive integer size and a valid hash and be derive-only.
- One shared footprint check (input copies plus output bound against the tmpfs
  and the memory share) is used by the table, by every chained derivation
  including those under the standard chain (real parent size), and by evaluate
  (source plus derived copy); the receipt records the real input size.
- Parent reads before launch fail closed as `ValueError` for a missing
  directory, a garbled manifest or a symlinked board.

### Derive run 4 (chained AGND B.Cu + In1.Cu on the run-3 copy, profile chained-agnd): FAILED at the 260 s fill stage cap; attempt consumed, not rerun

The single approved chained attempt ran once, 2026-10-23 03:03:27Z to 03:08:24Z,
under coordinator slot `osc-single-chained-agnd-slot-118af167-2010-486a-a864-ea51fc2dcf2f`
(attempt token `osc-attempt-854e7a08-7423-4578-abc5-8de0eff4781e`), tooling
a89bb69d, heavy-guard label `osc-derive-run-4-chained-agnd` with
`HEAVY_GUARD_MAX_RUN=720`. Launch-time exclusion: 0 containers, no KiCad or
heavy-guard process, no slot holder, 9.5 GiB available, LED slot released after
verified cleanup, no stop or cancel; source pins, parent board hash
(`4a55e0c1...`, 61,320,854 bytes), parent identity (`ecf170db...`), spec and image
re-verified immediately before launch.

Observed: the payload verified the parent copy (`reusable: true, all recomputed
checks match`), the worker loaded the 61.3 MB parent and started the two-zone
Fill at 22.3 s; the fill was still running when the 260 s fill-group cap killed
the worker (`TimeoutError: fill stage cap`) at about 282 s; payload 294.6 s,
controller 296.9 s, wall 297 s, guard verdict FAIL exit 1. Peak memory
1,770,110,976 bytes (1.65 GiB) under the 2 GiB cap, zero OOM events. Source hashes
unchanged. Both owned containers `REMOVED_CONFIRMED` (the payload container with
exit 1, the probe container with exit 0); post-stop cleanup found no remaining
records; the container set before and after is identical. Nothing was exported:
no derived board, no connectivity result, no classification. The causal first
failure is the payload fill-stage timeout; the controller's `normal container
exit unproven` is its consequence.

What this establishes: on this machine at 1 CPU, filling the B.Cu and In1.Cu AGND
zones together on the F.Cu-filled copy takes longer than 260 s (the In1.Cu fill
alone took 131.9 s on the unfilled source; the F.Cu fill alone 150.8 s). It does
not say anything about the connectivity of C1111.2 <-> U1105.12, whose class stays
`UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN` on the saved run-3 copy. The attempt is
consumed; no retry, extension or resource change was made.

Evidence: `scripts/local/evidence/osc-derive/run-4-failed/` (receipt, zone.json,
post-stop cleanup, attempt token, spec, cclogs checksum list; `*.log` files are
git-ignored, so the wrapper log lives only in cclogs); cclogs
`osc-local-wsl/derive-run-4-failed/` with the wrapper log, launch records and the
state directory's resource records.

### Open items after this phase

- C1111.2 <-> U1105.12 (AGND): the F.Cu fill alone does not connect the pair.
  U1105.12 sits on an F.Cu AGND island with no via or track (derive run 3), so
  the open is unlikely to be a missing fill cache; it is a candidate for human
  review of the copper around U1105.12. No repair is proposed here.
- A combined derivation (all three AGND zones) would move the class from
  `UNEVALUABLE` to `OPEN_WITH_ALL_NET_ZONES_FILLED` or
  `CONNECTED_VIA_SELECTED_FILL`. The one approved chained attempt (B.Cu + In1.Cu on
  the run-3 copy) failed at the 260 s fill cap at 1 CPU (derive run 4). Any
  further attempt would need a new approval and a cause-addressing change: one
  zone per chained run (two runs, each with an unmeasured B.Cu time), a longer fill
  cap, or more CPU; none is proposed here.
- The derived boards (+12V In4 at b9de2114..., AGND In1 at a0a57558...) are
  reusable through the identity key with recomputed checks; chaining them is
  implemented and tested offline but has not been run natively.
- Resident exited containers named `osc-task-*` from 2026-10-20 belong to an
  earlier session and were left untouched.
