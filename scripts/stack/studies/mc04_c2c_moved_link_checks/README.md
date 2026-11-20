# Task C step 2c: the six moved links pass the retained cable, compliance, class and rider checks

```sh
python3 -B checks.py --output new-result.json   # about 3 minutes
```

The script reads the six IC-improving geometries from `../mc04_c2b_link_shift_replace/result.json`,
pinned by hash in the output. It recomputes each moved link's figures with the retained
`links_gate` functions. The clean three-move set is a subset of these six.

Result (`result.json`, SHA-256 `54147745b59439c87df84f9da348b0fcf46c4310b575cf6686bf3cbc734f0113`):

| Link | Loop mm (recorded → moved) | Compliance mm/N | Hold K by hand | Leads to trim (moved) | Riders (moved / limit mm) |
| --- | --- | --- | --- | --- | --- |
| JR-K-JR-L02 | 10.66 → 10.66 | 0.055 → 0.243 | no | none | none |
| JR-K-JR-L04 | 4.66 → 10.66 | 0.073 → 0.084 | no | none | none |
| JR-K-JR-L06 | 10.66 → 6.66 | 0.032 → 0.026 | no | J1308, J1309, J1310 | none |
| P-K-P-L02.01.01 | 6.66 → 0.66 | 0.353 → 0.402 | yes, as recorded | SW1703, SW1704 | none |
| P-K-P-L12.02.01.02 | 2.66 → 12.66 | 0.110 → 0.089 | no | RV1004, RV904 | 27.4 / 35.0 / 45.7 of 55 |
| P-K-P-L13.01.01.02 | 6.66 → 12.66 | 0.027 → 0.022 | no | none | 39.2 / 39.2 of 45 |

Checks:

- **Cable.** Every cable fits its stock length. P-L02.01.01 needs a 12 mm lengthened front tail and
  leaves only a 0.66 mm loop.
- **Limits.** Every link is within the DS-87 1.0 mm/N compliance limit, its member class distances
  and its riders' class distances.
- **Coupling.** The bare ratio in `link_ratios.py` uses only the stock length and the conductor order,
  and both are unchanged.
- **c6 contract.** It pins a geometry digest, so its verdicts must be re-run for any adopted move.

These must also be reworked on adoption: the trim lists, the threading lowering stages, the latch
verdicts and the holding-hand list. Not done: electrical review of the re-placed parts, and any
canonical write.
