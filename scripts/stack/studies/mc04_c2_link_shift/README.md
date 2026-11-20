# Task C step 2a: inconclusive; 10 of 18 covering links tried, and JR-L02 is a real candidate

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
| JR-L01 | none | No position out to 48 mm (twice the retained radius); 1,264 otherwise legal candidates fail only on the protected courtyards. |
| JR-L04 | 19.0 / 17.0 | Frees U8314/U8318 and U4112/U4120/U4122, displaces U4102/U4124/U4145/U4148 (displaced ICs 10 to 9). |
| JR-L03 | 24.0 / 15.9 | Frees U4348, displaces 9 ICs. |
| JR-L02 | 11.8 / 10.2 | Frees U8417 and U8405 and adds no IC; higher cost is passives and distance. |
| JL-L08, JL-L02, JL-L01, JL-L07, JR-L06, JR-L07 | all higher | The cheapest candidate frees its target and displaces other parts; no re-placement was tried. |

## Correction after independent review

The first reading of this result ("zero-sum or worse") was overstated. Three problems:

- **Coverage.** Only 10 of the 18 links whose fields, slots or tails cover an unresolved IC were
  tried. Not tried: P-K-P-L07, P-K-P-L08 (U1415), P-K-P-L05.01.01 (U4417), P-K-P-L02.01.01 (U4433),
  JR-K-JR-L05 (U4623), P-K-P-L12.02.01.02 (U5110), P-K-P-L13.01.01.02 (U5209),
  P-K-P-L13.01.01.01 (U5210) and P-K-P-L03.01 (U8409).
- **JR-L02 does not trade ICs.** Its new candidate displaces only U4104, which the record already
  displaces. It frees U8417 (unresolved) and U8405 and adds no IC; its higher cost comes from
  passives and distance. JR-L04 also releases U4112, U4120 and U4122, so its distinct displaced ICs
  fall from 10 to 9.
- **No re-placement.** Displaced lists are computed against the original boards, not the cumulative
  re-placed scene. Newly displaced parts were not re-placed, and only the cheapest candidate per link
  was kept. "Displaced" is therefore not "unresolved".

Status: INCONCLUSIVE. The next study must cover all 18 links and re-run the retained re-placement
on each candidate's newly displaced parts. It must also keep the latch margin in the protection
check and stay within the retained 24 mm radius, or report beyond-rule results separately.
JR-L02 is the first candidate to carry forward.
Gate A check 5 stays NEEDS_DESIGN.
