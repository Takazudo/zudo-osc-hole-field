# Stage57: /M5B/C819409_SENSE target setup and outer-layer search (no path found)

**No proposal, no accepted repair, no canonical adoption.** Canonical boards, the placement lock and `decision.json` are
unchanged; KEEP_K1402_INCUMBENT stands. No zudo-pd edits, order or energisation.
The bounded outer-layer search found **no path** (below). Any route needs inner-layer
copper, which the frozen criteria reserve for a new owner approval.

## Baseline

The accepted Stage53 disposable board, reconstructed from Stage42 through Stage53:
`27d2214492f9dd88483be014df4197fdb936cbbc7c445f17c8178cce97126560`
(`.circuit-cache/stage53-fresh/`). Its native connectivity snapshot was re-run with
KiCad 10.0.6 and matches the Stage53 settlement byte for byte
(`21e30506…a3a6e0`, 37,800 objects, 115 opens).

## Frozen target (`target.json`, from `freeze.py`)

| Item | Value |
| --- | --- |
| Net | `/M5B/C819409_SENSE`, native `X1B64D2A971AB89E1AF19` |
| Source | R8248:2, F.Cu R0603 pad at (260.29, 110.81) mm, a 1-object component |
| Target | the 162-object component: U8215:3 (B.Cu SOIC-14, 257.19, 139.35), D8212:3 (F.Cu SOT-23, 209.97, 155.81), 149 tracks, 11 vias |
| Target copper layers | F.Cu 56, In2.Cu 49, B.Cu 44 segments; 11 through vias |
| Nearest target object | U8215:3 pad centre, 28.71 mm from the source pad centre |
| Rails at baseline | +12V one 1025-object partition, −12V one 1015, AGND 14 components (1425, 6, 3, eleven singletons) |

Distances are pad-centre to object centreline, not routable length.

## Exclusions

- **In3 −12 V necks.** Stage51's full In3 route split −12 V (1015 → 15 + 23 + 977);
  Stage52 refill diagnostics placed the interacting cuts at Stage51 copper indices
  16, 17 and 25 (In3 bbox X 227.2–236.0, Y 95.7–113.0 mm). No new In3 copper; −12 V
  must remain one 1015-object partition.
- **Stage53 In4 corridor** (bbox X 227.98–236.0, Y 95.7–113.39 mm). Stage53's In4
  use was approved for `/F3/C945bba_SENSE` only. Stage53 copper stays unchanged, no
  new In4 copper, and +12 V must remain one 1025-object partition.

Both regions are also more than 24 mm from the source pad, so neither is a
shortcut for this net.

## Acceptance criteria (`accept.py`, `settle.py`)

1. Proposal bound by SHA256 in `accept.py`; until then every evaluation fails with
   "route search NOT RUN".
2. Additive only: no removed copper, footprints and every other board object
   unchanged (Stage53 identity helpers, reused unchanged).
3. New tracks on F.Cu or B.Cu only, all on the target net; inner-layer tracks need a
   new owner approval. Ordinary through vias are allowed; their inner antipads are
   covered by the partition gate, not assumed harmless.
4. Native opens 115 → 114; exactly the 1 + 162 components merge; every other net
   partition is preserved, with +12 V 1025, −12 V 1015 and AGND checked explicitly.
   No new copper forms its own island or joins another component.
5. KiCad 10.0.6 DRC: rule errors 0, schematic parity 0, 114 unconnected items, no
   added uncapped warning, no `lib_footprint_issues`, dependencies unchanged.
6. Courtyard contact is reported, never used as clearance or assembly proof.
7. Two independent builds (`pass1`, `passfresh`) with identical board bytes,
   snapshots and acceptance, bound by `settle.py`.

Capped silkscreen identity non-regression stays UNRESOLVED as in Stage53.

## Outer-layer search (`search.py`, after the approved install)

Router libraries numpy 2.2.6, scipy 1.15.3, shapely 2.1.2 (the pinned CI set) in a
scratch venv outside the repo. Router input `grid_dump.py` on the Stage53 board
(oracle; dump binds `27d22144`, islands 1 + 162). F.Cu and B.Cu with ordinary
0.60/0.30 mm through vias, 0.20 mm tracks, bounds X 238–276 / Y 100–160 mm:

| Grid | Cells expanded | Result |
| --- | --- | --- |
| 0.10 mm | 10,341 of 1.5 M budget | search exhausted, no path |
| 0.05 mm | 50,950 of 1.5 M budget | search exhausted, no path |

The reachable region around R8248:2 is about 1 cm²: the source pocket is enclosed
on the outer layers. Search records are `evidence/outer-*.search.json`. This is a
bounded raster search, not proof that no continuous outer-layer route exists.

Diagnostic searches (not proposals, not committed as copper) with one inner layer
added find a path only via In1.Cu (AGND plane) or In4.Cu (+12 V plane), both the
same geometry: F.Cu 7.29 mm, one through via at (262.8, 117.4) mm, 24.38 mm on the
inner layer, bbox X 258.4–262.8 / Y 111.2–139.9 mm. In2.Cu or In3.Cu alone fails.
The dump omits pour fills, so either inner route would cut that plane's pour;
only native refill and the partition gate can decide whether the plane stays one
component. This location is outside the Stage53 In4 corridor, but the frozen rule
still forbids new In4 copper without approval.

## Commands

```sh
bash scripts/kicad/run.sh python3 design/architecture-278/implementation/stage57/m5b-sense/geometry.py \
  .circuit-cache/stage53-fresh/osc-jack-left.kicad_pcb design/.../stage57/m5b-sense/evidence/target-geometry.json
python3 design/.../stage57/m5b-sense/freeze.py --check     # PASS
bash design/.../stage57/m5b-sense/setup.sh                 # disposable stage57-pass1 / stage57-fresh
bash scripts/kicad/run.sh python3 scripts/pcbgen/grid_dump.py .circuit-cache/stage53-fresh/osc-jack-left.kicad_pcb .circuit-cache/stage57/dump.json
PYTHONPATH=. <venv>/bin/python design/.../stage57/m5b-sense/search.py .circuit-cache/stage57/dump.json .circuit-cache/stage57/coarse.json coarse   # no path
PYTHONPATH=. <venv>/bin/python design/.../stage57/m5b-sense/search.py .circuit-cache/stage57/dump.json .circuit-cache/stage57/fine.json fine       # no path
bash design/.../stage57/m5b-sense/trial.sh .circuit-cache/stage57-pass1 pass1   # NOT RUN: no proposal
python3 -m unittest design/.../stage57/m5b-sense/test_stage57.py   # 9 tests OK; also with -O
```

## Status

| Check | Status |
| --- | --- |
| Baseline reconstruction and snapshot replay | PASS (hash match) |
| Target record freeze and replay | PASS |
| Gate unit tests | PASS (synthetic snapshots) |
| Outer-layer route search (0.10 and 0.05 mm) | RUN: no path found (bounded) |
| Inner-layer route trial, proposal, native DRC/connectivity, settlement | NOT RUN (needs owner approval) |
| Analog, thermal, assembly, hardware | NOT RUN |
