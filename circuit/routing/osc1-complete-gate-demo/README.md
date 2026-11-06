# OSC1 complete-warning gate: native demonstration on the core (R3)

Status: read-only demonstration on an isolated copy of an unvalidated draft. Nothing
was promoted, and no file under `boards/` changed. This is not routing progress.

## Result: the mandatory gate ran end to end on a capped core report and passed with complete evidence

- Input: the refilled current-state copy of `osc-core` (adopted board
  `dda33a25…c728c`, recorded in `boards/osc-core/reports/routing.json`).
- Candidate: one AGND stitch via (0.6/0.3 mm) at C2213.2 (B.Cu), which joins one
  stranded AGND island. Open edges 3409 → 3408, AGND islands 22 → 21, 0 native
  errors, 0 schematic parity findings.
- Both reports cap `silk_over_copper` and `silk_overlap`, so the gate required
  complete evidence without any command-line option. The source-bound native
  audit ran for 701 s, and its before/after hashes matched the two boards. It
  reported no new hole or silk identity, so the unchanged `promotion_gate`
  passed on the completed reports.
- Two earlier candidates are kept in `receipt.json` under `prior_runs`. Native
  DRC rejected both before the audit: J900259.2 (`items_not_allowed`, inside a rule
  area) and U4410.4 (`clearance`, `hole_clearance`, `solder_mask_bridge`).

The rejection paths (a hidden new 200th warning, and missing, failed, unbound or
unsupported evidence) are covered by the unit tests in
`scripts/pcbgen/test_route_jack_grid.py` and `test_route_shards.py`. They were not
repeated natively here.

Reproduce with `python3 scripts/pcbgen/demo_complete_gate.py`. It needs the
`.circuit-cache/osc-core-grid-current-state/` workspace written by
`scripts/pcbgen/current_state.py`.

## Not retrieved: `.circuit-cache/p29/k36-keep/` (R7)

The review cites `.circuit-cache/p29/k36-keep/`. That cache is untracked local
output and is not present in this checkout or in any pushed branch, so it was not
retrieved or inspected. Nothing in OSC1 depends on it.
