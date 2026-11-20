# Task C step 2a: link shifts trade displaced ICs, they do not free them

Run from the repository root (about 2.5 min):

```sh
python3 -B scripts/stack/studies/mc04_c2_link_shift/shift.py new-result.json
```

For each of the ten links whose fields cover one of the 26 unresolved ICs, the study removes the
link from the final `link-gate.json` record, searches it again with the retained engine
(`links_gate.search`, class-distance accept from `links_gate_part2`) at radius 24 then 48 mm on
2.0/0.5 mm grids, and rejects any candidate whose slot, connector or tail overlaps a protected IC
courtyard grown 0.35 mm. It writes no geometry.

Result (`result.json`, SHA-256 `d74f63fcbaafc211aebf27d1aa20dbba16deb7b969f8b73a52a328522b95a5e1`):

| Link | Cost new / recorded | Outcome |
| --- | --- | --- |
| JR-L01 | none | No legal position; the protected U4346/U4324 courtyards and panel hardware block every slot. |
| JR-L04 | 19.0 / 17.0 | Frees U8314/U8318, displaces U4102/U4124/U4145/U4148. |
| JR-L03 | 24.0 / 15.9 | Frees U4348, displaces 9 ICs. |
| JR-L02 | 11.8 / 10.2 | Frees U8417 at the cost of other displaced parts. |
| JL-L08, JL-L02, JL-L01, JL-L07, JR-L06, JR-L07 | all higher | Each frees its target by displacing others. |

Conclusion: under the retained rules a single link shift is zero-sum or worse, so link reshaping
is not a remedy for the 26 unplaced ICs. The remaining candidates are block relocation with longer
runs, splitting or downsizing 40P links, and moving JR/JL circuit blocks to K (which changes the
partition and link signal sets). Each needs electrical review against the functional briefs.
Status of Gate A check 5 is unchanged: NEEDS_DESIGN.
