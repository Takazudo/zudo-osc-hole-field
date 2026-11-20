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

## Correction after independent review: room exists for each IC alone, but JR lacks joint room for 3 of its 6

`room_on_own_board_each_alone` (26) tests each IC alone against a frozen scene. The six JR ICs all
find their nearest room in one pocket near (260, 147). `joint_first_fit` vacates every unresolved
body of a board and places the ICs one by one at the first raster fit (own face first, then the
other face; four rotations), blocking each placed box grown 0.35 mm. Results:

- **JL:** all 6 placed.
- **K:** all 14 placed.
- **JR:** 3 placed. U8314, U8318 and U8417 find no room (JR.F has no raster position).

First-fit is greedy and raster-only, so it is a lower bound, not proof that JR cannot hold all six.
Even so, JR is the board where capacity, not only locality, is in doubt. Own-face `nearest_mm`
values are upper bounds, because the IC's own frozen body still blocks its face in that search.

Retained result SHA-256: `efe67c836939643450e66750918c0864ba880bef6e8ef92c462fb529c656ffd3`.
