# None of the 26 relocations has a sourced electrical budget; 13 also need the 25 mm rule relaxed

Task C step 5c, 2026-11-20. A per-IC function-boundary comparison, the source-only output the MC02 analog,
logic and precision briefs ask for before any geometry task. It joins the step 4 packing, the step 5b
keep-front variant and both crossing-net classifications (all four pinned by hash) and lists, per IC: the
IC shift on K, the farthest block member, the nets each boundary would put on the cable with their
front-board endpoints, the module test file that guards the function and the owning brief.

```sh
python3 -B scripts/stack/studies/mc04_c5c_function_boundaries/boundaries.py --output scripts/stack/studies/mc04_c5c_function_boundaries/result.json
```

`result.json` sha256 `be44828a4fd1309e6d01b276603816462ad827f87b21453b3ddfdbffecbd91d7`.

## The cable cost sits on the twelve JR and JL analog blocks

| Board | IC (instance) | IC shift mm | New cable nets (either boundary) |
| --- | --- | --- | --- |
| JL | U1216 (O2), U1416 (O4), U1417 (O4), U2218 (F2) | 0.0 to 10.8 | 4, 4, 3, 4 |
| JL | U2119 (F1) | 13.9 | 8 |
| JL | U1518 (O5, precision) | **27.2** | 1 |
| JR | U4347 (E3), U4348 (E3), U8417 (M4B) | 4.5 to 21.5 | 5, 4, 6 |
| JR | U8318 (M4A) | 12.6 | 8 (a block member lands 31.6 mm from the IC) |
| JR | U4346 (E3), U8314 (M4A) | **26.7, 30.5** | 4, 4 |

K's fourteen add no cable net, but ten of them move beyond 25 mm: U1415, U4324, U4417, U4433, U4524,
U4526, U4527, U4623, U4635, U8409. Seven of those ten are SN74HC00/HC74 logic packages (up to 49.4 mm).

## Every budget is UNRESOLVED

OPA4196 blocks need added length, vias, R/L/C, phase margin, summed error and noise, output load, thermal
and service envelopes. The logic packages need trace, delay, skew, setup/hold and synchronizer budgets.
U1518 and U4341 need their share of the 4.166667 mV tracking budget, feedback R/C, storage droop and
injection limits. No source assigns any of these, so this study assigns none (`budgets_resolved`: 0).

## Scope

Paper comparison only. No allocation, electrical acceptance or canonical write; not a stability model and
not an approved relocation set.
