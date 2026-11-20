# MC04-C1 capacity census (Task C, step 1)

Asks whether the 26 unresolved ICs (JL6, JR6, K14) lack board capacity or only room near their
original place. It rebuilds the retained cumulative scene exactly as `mc04_r1` does (412 accepted
moves, the other unresolved bodies frozen, links, slots, fields, latch margins, fixings and outlines).
Then it rasterises each board face at 0.25 mm and searches each IC's own board, both faces and four
rotations, with no distance limit. The nearest raster position on each face, in the original
rotation, is confirmed with the retained exact predicate; only the displacement cap is ignored.

```sh
python3 scripts/stack/studies/mc04_c1_capacity/capacity.py --output new-result.json   # about 1 minute
python3 -B scripts/stack/studies/mc04_c1_capacity/test_capacity.py
```

`result.json` is the retained run. It is room-only: no decoupler or neighbour moves with the IC, no
routing, timing or electrical acceptance, and no change to canonical geometry.
