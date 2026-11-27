# MC04-S13: node capacitance budgets (study, model evidence only)

MODEL EVIDENCE ONLY, STUDY, NOT ADOPTED, UNVALIDATED DRAFT. Brief:
`circuit/orchestration/campaigns/osc-stack-20261114/mc04-s13-node-capacitance-budget-brief-20261127.md` (Revision 3),
decision rows DS-161 to DS-169. Report: `mc04-s13-report-20261127.md` in the same campaign directory.

| File | Role |
| --- | --- |
| `cells.py` | netlist from `design.spec.instrument.specification()` (checked pin for pin against `io-partition.json`), census (P6), cell extraction rule, deck builders |
| `runner.py` | multi-analysis runner (one deck is one `bash scripts/kicad/run.sh ngspice -b` invocation) and the criterion measurements |
| `budget.py` | driver: `--census`, `--controls` (P5, P7, P8, M3), `--run` / `--resume` (25 min slices), `--evaluate`, `--check` |
| `guard.py` | copy of the S12 guard: 4 GiB on tree RSS plus `docker stats`, MemAvailable floor 8 GiB, `docker kill` of the pinned image on abort |
| `test_s13.py` | P6 and mutations M1, M2, M4 to M8 (offline); M3 reads the recorded control run |
| `census.json`, `results.jsonl`, `budget.json`, `result.json`, `checkpoints/` | outputs |

Decks and data stay in the ignored `.circuit-cache/sources/mc04-s13/`. The OPAx196 and OPAx197 libraries stay in their
ignored caches and are pinned by hash; no model file is committed.

Run (one heavy process at a time, from the repository root):

```sh
P=/home/user/venv312/bin/python S=scripts/stack/studies/mc04_s13_node_cap_budget
$P $S/budget.py --census
$P $S/guard.py $S/checkpoints/guard-controls.json -- $P $S/budget.py --controls
$P $S/guard.py $S/checkpoints/guard-slice-01.json -- $P $S/budget.py --run
$P $S/guard.py $S/checkpoints/guard-slice-NN.json -- $P $S/budget.py --resume   # until "complete"
$P $S/budget.py --evaluate && $P $S/budget.py --check
$P -m unittest discover -s $S -p 'test_*.py'
```

Status 2026-11-27: stopped at Arm 0 P4b (STOP 2). The sweep, P5, P7, P8, P9 and the what-if arm are NOT RUN and no
budget exists. See `result.json` and the report.
