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

### Open items after this phase

- C1111.2 <-> U1105.12 (AGND) stays `UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN`: it
  is decided by the F.Cu AGND fill, which does not finish in 260 s at 1 CPU.
- The derived boards (+12V In4 at b9de2114..., AGND In1 at a0a57558...) are
  reusable through the identity key with recomputed checks; chaining them is
  implemented and tested offline but has not been run natively.
- Resident exited containers named `osc-task-*` from 2026-10-20 belong to an
  earlier session and were left untouched.
