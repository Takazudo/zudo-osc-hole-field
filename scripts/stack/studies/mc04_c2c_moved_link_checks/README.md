# Task C step 2c: the five moved links pass the retained cable, compliance and class checks; coupling is unchanged

```sh
python3 -B checks.py --output new-result.json   # about 3 minutes
```

The script reads the five improving geometries from `../mc04_c2b_link_shift_replace/result.json`,
pinned by hash in the output. It recomputes each moved link's figures with the retained
`links_gate` functions.

Result (`result.json`, SHA-256 `82effef13a33e7e569978d982998425c2bb0e96be7cf39c4147dc8e1544c6f59`):

| Link | Loop mm (recorded → moved) | Compliance mm/N | Hold K by hand | Leads to trim (moved) |
| --- | --- | --- | --- | --- |
| JL-K-JL-L08 | 2.66 → 6.66 | 0.065 → 0.083 | no | J604, J605 |
| JR-K-JR-L06 | 10.66 → 6.66 | 0.032 → 0.026 | no | J1308, J1309, J1310 |
| P-K-P-L02.01.01 | 6.66 → 0.66 | 0.353 → 0.402 | yes, as recorded | SW1703, SW1704 |
| P-K-P-L12.02.01.02 | 2.66 → 12.66 | 0.110 → 0.171 | no | RV1006, RV906 |
| P-K-P-L13.01.01.02 | 6.66 → 12.66 | 0.027 → 0.022 | no | none |

Checks:

- **Cable.** Every cable still fits its stock length. P-L02.01.01 needs a 12 mm lengthened front tail
  and leaves only a 0.66 mm loop.
- **Compliance.** Every link is within the DS-87 1.0 mm/N limit.
- **Class distance.** Every link passes the class-distance accept.
- **Coupling.** The retained ratio uses only the stock cable length and the conductor order
  (`link_ratios.py`). Both are unchanged, so each link keeps its recorded coupling verdict.

These must be reworked if the moves are adopted: the trim lists, the threading lowering stages,
the latch verdicts and the holding-hand list. The moved latch margins are cleared by re-placement
in step 2b. Not done: electrical review of the 101 re-placed parts, and any canonical write.
