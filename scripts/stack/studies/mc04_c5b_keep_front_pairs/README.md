# Keeping protection and isolation pairs on the front board moves the 29 crossings to the IC side; it does not remove any

Task C step 5b, 2026-11-20. Re-runs the step 4 block packing (`../mc04_c4_blocks/blocks.py`) with a variant
boundary: a one-hop neighbour that sits on any net whose name contains one of the `--keep-front` fragments
stays on its source board. The default boundary and the retained step 4 result are unchanged (the option is
off by default, and the default output hash is unchanged). Each variant's new crossings are then classified
with `../mc04_c5_crossing_nets/nets.py --source`.

```sh
python3 -B scripts/stack/studies/mc04_c4_blocks/blocks.py --keep-front _PROTECTED ISO_MID --output scripts/stack/studies/mc04_c5b_keep_front_pairs/result-protect-iso.json
python3 -B scripts/stack/studies/mc04_c4_blocks/blocks.py --keep-front _PROTECTED ISO_MID LED --output scripts/stack/studies/mc04_c5b_keep_front_pairs/result-protect-iso-led.json
python3 -B scripts/stack/studies/mc04_c5_crossing_nets/nets.py --source <result> --output <nets file>
```

| File | sha256 |
| --- | --- |
| `result-protect-iso.json` | `9197e4e7b7e433c7762f47e7060627c1f2134f268deb307b3ab160c93f3403d6` |
| `nets-protect-iso.json` | `62b178e9f94c2fa5a4ef869d46a2d8a750a04744382d39d32f63910c0a26e675` |
| `result-protect-iso-led.json` | `0db2d7e111505152d4612141817ba3903fdc6bc0c96116fbd01bd2094e95a4b9` |
| `nets-protect-iso-led.json` | `a51e2bc9d6e59a50148965ca9cb8ea31cfed462263210541fddd609829017450` |

## All three boundaries cross the same number of nets

| Boundary | Packs on K | JR new / removed | JL new / removed | Raw-sensitive crossings | ICs beyond 25 mm |
| --- | --- | --- | --- | --- | --- |
| Step 4 default | yes | 31 / 15 | 24 / 16 | 0 | 13 |
| Keep `_PROTECTED`, `ISO_MID` parts | yes | 31 / 15 | 24 / 16 | 0 | 13 |
| Keep those and `LED` parts | yes | 31 / 15 | 24 / 16 | **13** | 13 |

Every position in every run passes the exact predicate (except the displacement cap, as in step 4).

## With the pairs kept, the crossing node becomes the clamped IC input or the IC output

Keeping the series resistor on the front board makes the IC-side node cross instead: for example
`/E3/C33e306_SENSE` (U4346 and clamp D4301 move; series R4308 stays). The 15 protected nodes and 14
isolation midpoints are replaced by `*_SENSE` and `*_DRIVE` nets one component closer to the IC. Whether a
cable on a clamped high-impedance input is acceptable is an electrical question this study does not answer.

## Keeping the LED resistors on the front board is worse

It makes 13 `*_SENSE` nets that the partition lists as local raw-sensitive cross the cable (E3 3, M4A 4,
M4B 2, F1 4). That variant should not be developed.

## Scope

Room and count only, as step 4. No allocation, coupling, electrical review or canonical write.
