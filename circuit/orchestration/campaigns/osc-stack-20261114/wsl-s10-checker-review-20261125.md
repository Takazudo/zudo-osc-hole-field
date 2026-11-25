# WSL S10 rejection checker and source review

The owner returned engineering candidate `32580f77c9d0aa9c6067cbad965a6f701050ca5d`. The independent source reviewer accepted the corrected checker at `557b5a6e92e2600fcb4319bd8528c4f5812d3177` for the engineering baseline. S10 geometry remains rejected. [Design review](https://github.com/Takazudo/zudo-osc-hole-field/issues/367#issuecomment-7153304994)

The twelve diagnostic stop entries comprise six newly displaced sensitive passives, one strict feedback-distance violation and five locality-record discrepancies. The effective scene includes 16 face changes. C4554 switches to F and C5212 remains on F. R4238 moves 3.55 mm on B. The isolated combined-field check clears the three proposed block courtyards, while both placement consumers withhold those blocks. The 62 links, 124 latches and 531 signals describe a model; U1415, U5110 and U8409 still lack positions.

## Reproducible observations

| Check | Observed result |
| --- | --- |
| `overlay.py --check` and `python3 -m unittest test_s10` | Final replay and all 16 tests pass. Different Python hash seeds produce the same diagnostic bytes, SHA-256 `c0f18373b46ec9097024b057905a41403aebd41a638d02355219b92f4a11efab`. Run the overlay check independently because downstream consumers bind to this artifact. |
| `link_era_replacements.py --check`, `gate_a_open_items.py --check`, placement and Gate A tests | Ten retained S8 placements; all three returned blocks withheld. All 15 consumer tests pass. Missing evidence and mismatched placement rows are rejected. |
| `links_gate.py`, `c6_rebind.py --check` | The normal producer passed under the shared guard in 189 s. The separate replay passed in 188 s. Four held links, unchanged unheld live links, unchanged rider hosts and signal/position pins. No held-pose errors. The eight c6 outputs match the earlier positions and riders. |
| `link_electrical.py --check`, `c6_report.py --check`, trimmer checker | Current. The gate at `4c0ec4aa` has SHA-256 `793b7f1962a1c14855b11a36cba57f7544f20ac7c889b3d2e3135ab96be54c9d`. Only its evidence provenance and embedded placement record changed against the returned candidate. The c6 and trimmer projections change only their gate hash. |
| S8 member-face and board-conflict checkers; S9 and trimmer unit tests | Both S8 files current; four member-face tests, 17 S9 tests and 14 trimmer tests pass. The S9 search was not repeated. |
| Component and documentation checks | `pnpm circuit:check` passed. The validator performed the pin-asset check for 84 component lines; 445 declared placements are unverified. `pnpm check`, `pnpm build` and `pnpm check:site` passed. The build produced 335 pages. The link checker used one existing allowlist entry for the workbench template string. |

The recalculated figures are placement and run-length estimates. The checks provide no routed feedback-loop stability measurement, physical trimmer or latch-access measurement, or acceptance of the inherited board changes. No PCB DRC or zone fill was admitted. See [fixed-endpoint feasibility](mc04-s10-revision-2-feasibility.md), [matched stack failures](wsl-s10-stack-verification-20261125.md) and the [integration and trigger audit](wsl-s10-main-integration-audit-20261125.md).
