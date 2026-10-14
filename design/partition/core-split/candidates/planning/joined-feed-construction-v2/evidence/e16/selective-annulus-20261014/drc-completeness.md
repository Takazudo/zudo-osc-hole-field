# DRC completeness implementation and retained-evidence assessment

`native_validation.py::assess_native_reports` extends the existing E16 native worker. Its assessment is written into `execution.json` after the same filled-board phase chain is verified. It separates command execution, complete pad/feed/peer reconciliation, findings enumeration, native report acceptance, and candidate adoption. A successful command is not native acceptance. Candidate adoption remains `NOT ADOPTED` / `accepted: false`, even for a clean synthetic control.

The gate refuses completeness for absent result collections, incomplete severities, ignored checks, exclusions, missing per-track or schematic scope, explicit truncation, malformed categories, pinned per-category saturation, missing/corrupt same-board complete connectivity, and disagreement between DRC-listed open edges and the complete all-net open-edge census. It never compares unresolved pad counts to open edges. An incoming `PASS` or `accepted` field cannot override these checks. Native report PASS is limited to a complete clean report with reconciled connectivity; it does not imply electrical compliance, adoption or physical qualification.

## Pinned-toolchain limitation

The read-only upstream inspection used KiCad tag `10.0.6`. Hashes and sizes of the fetched source files are in `drc-upstream-sources.json`; those temporary research copies are recoverable from the exact URLs, subject to hash verification.

- [DRC engine source](https://gitlab.com/kicad/code/kicad/-/raw/10.0.6/pcbnew/drc/drc_engine.cpp): lines 61–62 define ordinary 199 and extended 499 limits; `RunTests` lines 929–937 resets them per error code (extended for clearance/unconnected), with ignored checks assigned zero. `ReportViolation` lines 2273–2286 atomically drops findings after the limit. Saturation establishes uncertainty, including when the actual total happens to equal the limit.
- [CLI DRC source](https://gitlab.com/kicad/code/kicad/-/raw/10.0.6/kicad/cli/command_pcb_drc.cpp): options include `--all-track-errors`, `--schematic-parity`, severity selection, refill and output format; no unlimited-category option is exposed. Per-track reporting does not disable the engine cap. The existing E16 command does not request all-track or schematic-parity checks; an empty parity array therefore does not prove that check ran.

No supported exhaustive enumeration mechanism has been established for the unchanged pinned CLI. Repeating it, requesting all severities, changing format or toggling per-track reporting cannot remove the per-category cap. A different collector would require separately reviewed implementation and admission; it must not silently replace the pinned oracle or reduce rules/severity. Existing commands and sidecars are unchanged by this task. Broader execution scope has not been authorized or run.

## Read-only results and verification

`drc-retained-assessment.json` binds all three historical execution/report/census inputs by SHA-256 and preserves their original records unchanged. Their receipt chains pass integrity checks. Command execution and source/native reconciliation remain PASS. All three findings inventories are INCOMPLETE, all three native acceptance statuses are `BLOCKED_INCOMPLETE`, and none is adopted. KA-t2 lists 479 of 479 open edges; KB-t2 lists 499 of 1,220; KB-p1 lists 499 of 1,219. Each hits four ordinary 199-item warning categories. All retain five ignored checks and the unrequested track/parity scopes. These are reclassifications of retained evidence, not new measurements.

Focused source-only command:

```sh
python3 -m unittest discover -s design/partition/core-split/candidates/planning/joined-feed-construction-v2 -p test_native_validation.py
```

Result: 33 tests PASS, including ten new completeness regressions. Synthetic tests and retained JSON inspection import no `pcbnew`, launch no Docker/native process and consume no numerical/native admission or campaign quota. Fresh native execution and exhaustive DRC remain NOT RUN. Independent review is recorded by the task owner separately.
