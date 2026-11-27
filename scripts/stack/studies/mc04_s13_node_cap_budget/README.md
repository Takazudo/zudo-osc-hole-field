# MC04-S13: node capacitance budgets (study, model evidence only)

MODEL EVIDENCE ONLY, STUDY, NOT ADOPTED, UNVALIDATED DRAFT. Brief:
`circuit/orchestration/campaigns/osc-stack-20261114/mc04-s13-node-capacitance-budget-brief-20261127.md` (Revision 6,
with Addenda A and B), decision rows DS-161 to DS-173. Report: `mc04-s13-report-20261127.md` in the same campaign directory.

| File | Role |
| --- | --- |
| `cells.py` | netlist from `design.spec.instrument.specification()` (checked pin for pin against `io-partition.json`), census (P6), cell extraction rule, deck builders |
| `runner.py` | multi-analysis runner (one deck is one `bash scripts/kicad/run.sh ngspice -b` invocation), the seed decks of Addendum B and the criterion measurements |
| `p4b.py` | Arm 0 P4b per Addendum A: the pinned input-buffer module in batches of 5 cases, `paper_point` stubbed in memory, journal `checkpoints/p4b.jsonl` |
| `budget.py` | driver: `--census`, `--pins` (P1 to P3), `--controls` (P5, P6b, P7, P8, M3), `--m12`, `--run` / `--resume` (25 min slices), `--evaluate`, `--check` |
| `guard.py` | copy of the S12 guard: 4 GiB on tree RSS plus `docker stats`, MemAvailable floor 8 GiB, `docker kill` of the pinned image on abort |
| `test_s13.py` | P6 and mutations M1, M2, M4 to M16 (offline); M3 and M12 read recorded runs |
| `census.json`, `results.jsonl`, `budget.json`, `result.json`, `checkpoints/` | outputs |

Decks and data stay in the ignored `.circuit-cache/sources/mc04-s13/`. The OPAx196 and OPAx197 libraries stay in their
ignored caches and are pinned by hash; no model file is committed.

Run (one heavy process at a time, from the repository root):

```sh
P=/home/user/venv312/bin/python S=scripts/stack/studies/mc04_s13_node_cap_budget
$P $S/budget.py --census
$P $S/guard.py $S/checkpoints/guard-p1-p3.json -- $P $S/budget.py --pins <OPAx196 ZIP fetched read-only>
$P $S/guard.py $S/checkpoints/guard-p4b-slice-01.json -- $P $S/p4b.py --run   # then --resume per slice
$P $S/guard.py $S/checkpoints/guard-controls.json -- $P $S/budget.py --controls
$P $S/guard.py $S/checkpoints/guard-slice-01.json -- $P $S/budget.py --run
$P $S/guard.py $S/checkpoints/guard-slice-NN.json -- $P $S/budget.py --resume   # until "complete"
$P $S/budget.py --evaluate && $P $S/budget.py --check
$P -m unittest discover -s $S -p 'test_*.py'
```

Status 2026-11-27, third run (Revision 6): P1 to P6 pass, with P4b reused under Addendum B6. The run stopped at Arm 0
P6b (STOP 2) on the H-REF9 corner with TMUX 100 pF and the bracket to AGND. The sweep is NOT RUN and no budget
exists. See `result.json` and the report.
