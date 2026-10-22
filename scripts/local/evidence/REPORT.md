# OSC +12V connection diagnosis on WSL (local containment)

Branch `claude/osc-synthetic-local-wsl` on top of PR #293 head 8bdf7703. Frozen
input commit fa16c6ff; `boards/osc-core/osc-core.kicad_pcb` SHA256
fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10 (identical on
main, at the frozen commit, and in the Windows reference copy). Every native run
used `kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`
with kicad-cli and pcbnew exactly 10.0.6, 1 CPU, 2 GiB, zero extra swap, 64 PIDs,
network none, read-only root and source mounts, owned-container records with
confirmed removal, through the machine-wide heavy guard. The original board was
never written; all CAD writes went to a container tmpfs. No DRC was run (out of
scope for this two-pair diagnostic). Nothing here is board acceptance.

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
No wiring repair candidate is needed for these two pairs; the next minimal step
is a zone refill before save in the canonical flow, which is not authorized here.

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
