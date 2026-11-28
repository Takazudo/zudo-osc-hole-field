# MC04-S13: node capacitance budgets (study, model evidence only)

MODEL EVIDENCE ONLY, STUDY, NOT ADOPTED, UNVALIDATED DRAFT. Brief:
`circuit/orchestration/campaigns/osc-stack-20261114/mc04-s13-node-capacitance-budget-brief-20261127.md` (Revision 8,
with Addenda A, B and C), decision rows DS-161 to DS-174. Report: `mc04-s13-report-20261127.md` in the same campaign directory.

| File | Role |
| --- | --- |
| `cells.py` | netlist from `design.spec.instrument.specification()` (checked pin for pin against `io-partition.json`), census (P6), cell extraction rule, deck builders |
| `runner.py` | multi-analysis runner (one deck is one `bash scripts/kicad/run.sh ngspice -b` invocation), the seed decks of Addenda B and C, the lone-input-pin check (C1), the per-deck slice deadline and the criterion measurements |
| `p4b.py` | Arm 0 P4b per Addendum A: the pinned input-buffer module in batches of 5 cases, `paper_point` stubbed in memory, journal `checkpoints/p4b.jsonl` |
| `budget.py` | driver: `--census`, `--pins` (P1 to P3), `--controls` (P5, P6b, P7, P8, M3), `--m12`, `--run` / `--resume` (slices: no deck starts unless its 600 s timeout fits inside 28 min), `--evaluate`, `--check` |
| `guard.py` | copy of the S12 guard: 4 GiB on tree RSS plus `docker stats`, MemAvailable floor 8 GiB, `docker kill` of the pinned image on abort |
| `test_s13.py` | P6 and mutations M1, M2, M4 to M21 (offline), the noise-plot selection on every complete closed deck, the slice deadline, discarded-work accounting and the sweep order; M3 and M12 read recorded runs |
| `census.json`, `results.jsonl`, `budget.json`, `result.json`, `checkpoints/` | outputs; `checkpoints/discarded-*.json(l)` hold work whose lines were discarded and still count against the caps |

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

Status 2026-11-28, fourth run (Revision 8), with the result review's corrections: Arm 0 passed (P1 to P8, P4b reused
under B6; M12 NOT EVALUATED as required). The sweep stopped at the 5 h sweep ceiling (STOP 3), with 1 480 deck records.
62 class G sweep points and the whole what-if arm are NOT RUN. Every class G deck run was NOT EVALUATED. `budget.json`
labels 64 rows: 38 FAILS AT ZERO STRAY, 9 NO HEADROOM AT PAPER, 6 BLOCKED (classes F and I) and 11 NOT EVALUATED.
The 11 are 10 class C rows, whose K5 at wiper 1.0 is withdrawn (review finding 1), and the class G row. No row is
BUDGETED. Model evidence only, an unvalidated draft. See `result.json` and the report.
