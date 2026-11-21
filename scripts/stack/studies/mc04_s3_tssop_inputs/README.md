# In a TSSOP-14 body, the six input buffers fit 13 to 32 mm from where they sit, versus 33 to 104 mm in SOIC-14

Stage 3 what-if, 2026-11-21, for the owner's choice "Try a smaller chip package". The six input-buffer ICs
that the stage 1a draft limits keep off the cable (`../mc04_s1_budgets/`) stay on their front boards. This
asks how close each could go with the project's TSSOP-14 OPA4197IPWR courtyard (U4341 on K) instead of its
SOIC-14 body.

```sh
python3 -B scripts/stack/studies/mc04_s3_tssop_inputs/tssop.py --output scripts/stack/studies/mc04_s3_tssop_inputs/result.json
```

`result.json` sha256 `06856a17a1263120dca2d231c82aa48f6cea960595cc65c0e2afca97831d77ce`. The run takes several minutes.

## All six fit together on their own boards, in every placement order

All of each board's unresolved ICs are vacated and the three input buffers placed greedily, nearest their
current origins. Footprint-origin distance from the current position:

| Board | IC | TSSOP-14 (best order) | SOIC-14, nearest alone (capacity census / stage 2) |
| --- | --- | ---: | ---: |
| JL | U1216 (O2) | 13.44, rear, rotated 180° | 33.23 |
| JL | U1416 (O4) | 13.44, rear, rotated 180° | 36.08 |
| JL | U1518 (O5, already OPA4197IDR) | 31.99, rear, rotated 180° | 35.32 |
| JR | U4346 (E3) | 22.60, rear | 94.95 |
| JR | U8314 (M4A) | 32.13, rear, rotated 90° | 89.82 |
| JR | U8417 (M4B) | 26.28, rear | 104.19 |

Unrotated placements (U4346, U8417) pass the retained exact predicate. The rotated ones are raster-only,
because the exact predicate here takes the body unrotated. Four of the six land beyond 25 mm, so the
retained 25 mm radius rule would still need a ruling for those.

## Scope

IC courtyards only, without decouplers or block passives. A part substitution is not selected: OPA4197 in
these input stages needs the component evidence workflow and an electrical review. Room only.
