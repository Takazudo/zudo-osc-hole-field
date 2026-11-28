# MC04-S14: feedback capacitor what-if, class G specification cell, re-score of classes A, C and D

MODEL EVIDENCE ONLY, STUDY, NOT ADOPTED, UNVALIDATED DRAFT.

Brief: `circuit/orchestration/campaigns/osc-stack-20261114/mc04-s14-feedback-capacitor-brief-20261128.md`
(Revision 3, SHA-256 `c6904428…0ae9ec2`, admitted under DS-182). Report:
`circuit/orchestration/campaigns/osc-stack-20261114/mc04-s14-report-20261128.md`.

No capacitor is adopted. No board, schematic, specification, BOM, owner bundle or S13 file is changed.

## Files

| File | Role |
| --- | --- |
| `cells.py`, `runner.py`, `budget.py`, `guard.py` | byte copies of the S13 files, changed as listed in the report (`guard.py` unchanged) |
| `s13_pinned.py` | the pinned S13 modules, imported read-only in a separate interpreter (replays, P4, P10, cache binding) |
| `s14.py` | the S14 driver: Arm 0, arm R, arm W, arm G, pairs, tables, `--check` |
| `test_s14.py` | M1 to M8, M12 (in-memory) to M21 and N1 to N17 (replaces the copied `test_s13.py`) |
| `results.jsonl` | one line per seed, group, deck, rescaled second deck and arm R re-score record |
| `whatif.json` | one row per what-if set and per class G corner (arm G) |
| `rescore.json` | one row per net of classes A, C and D, and the per-IC table (S7) |
| `result.json` | pins, fingerprint, slices, guards, invocation counts by kind, arm times |
| `checkpoints/` | Arm 0 record, invocation ledger, slice records, guard summaries, discarded attempts |

## Commands

```sh
P=/home/user/venv312/bin/python; S=scripts/stack/studies/mc04_s14_feedback_capacitor
$P $S/guard.py $S/checkpoints/guard-arm0.json -- $P $S/s14.py --arm0 <fetched SBOMAF9E.ZIP>
$P $S/guard.py $S/checkpoints/guard-slice-01.json -- $P $S/s14.py --run slice-01
$P $S/s14.py --evaluate
$P $S/s14.py --check
$P -m unittest discover -s $S -p 'test_s14.py'
```

Every deck runs as `bash scripts/kicad/run.sh ngspice -b <deck>` (KiCad 10.0.6, ngspice 44.2, pinned image).
Working files go to the ignored `.circuit-cache/sources/mc04-s14/`; the S13 cache is read, never written.
