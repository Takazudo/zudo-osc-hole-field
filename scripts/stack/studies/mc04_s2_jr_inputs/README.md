# JR's three input buffers fit on JR only 90 to 131 mm from their jacks; a TSSOP-14 body would find room 23 to 32 mm away

Stage 2 room check, 2026-11-21. The stage 1a draft limits keep U4346, U8314 and U8417 (JR input buffers with
10 kΩ protected inputs) off the cable. This asks whether JR has room for them once JR's other three
unresolved ICs (U4347, U4348, U8318) go to K.

```sh
python3 -B scripts/stack/studies/mc04_s2_jr_inputs/jr_inputs.py --output scripts/stack/studies/mc04_s2_jr_inputs/result.json
```

`result.json` sha256 `d61e83da5a3bc07d3e3b91db688d5c50c843c5ac8b8a45b2ad53281bb2d6aa25`. The run takes a few minutes.

## All three SOIC-14 bodies fit together, but only far from where they are now

With all six JR unresolved ICs vacated, every one of the six placement orders fits all three input buffers
on JR's rear face, 89.8 to 131.0 mm from their current origins (unrotated placements pass the exact
predicate; rotated ones are raster-only). Each one alone is no closer: 95.0, 89.8 and 104.2 mm. That is
room in principle, not a local position for an input stage.

## A smaller body would find room much closer

OPA4196 is orderable only in SOIC-14 (SBOS869 package addendum). As a what-if, the project's TSSOP-14
OPA4197IPWR body (U4341's courtyard) finds raster room 22.6 mm (U4346), 32.1 mm (U8314) and 26.3 mm (U8417)
from the current origins, rear face. That is raster only, not exact-checked, and it would be a part
substitution. That needs the component evidence workflow and an electrical review of OPA4197 in these
input stages. Nothing is selected.

## Scope

IC courtyards only, without decouplers or block passives; greedy raster. Room only, with no electrical,
routing or substitution claim.
