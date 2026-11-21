# MC04 stage 5 native brief: swap the six front-board input-buffer packages to OPA4197IPWR

- Campaign / task ID / attempt ID: osc-stack-20261114 / MC04-S5-OPA4197-SWAP / 20261121-1
- State: **PLANNED (not admitted)**. The WSL session fills the environment and admission fields before any run.
- Top-level manager: Claude Project lead, thread "Resume OSC instrument order-readiness campaign", branch
  `claude/project-thread-iw3gai`. Sole dispatcher on the device: the WSL Claude Code session the owner starts.
- Parent decision: owner, 2026-11-21 10:18Z, "Accept, fix the rail in #34"
  (`mc04-remedy-decision-packet-20261120.md`). Evidence: MC04-S4 report `design/reports/spice/input-buffer-vendor.json`
  sha256 `445df865…c2ae`, revision 1 independently reviewed.
- Independent reviewer: a separate reviewer session or subagent that did not write the change.

## Goal and non-goals

Goal: in the specification and generators, change these six packages to OPA4197IPWR (TSSOP-14), keep them on
their front boards, regenerate every tracked output, and report where the TSSOP bodies land.

| Board | Ref (current) | Instance | Current MPN | Co-packed units that change with it |
| --- | --- | --- | --- | --- |
| JL | U1216 | O2 | OPA4196IDR | unit 4 general_output |
| JL | U1416 | O4 | OPA4196IDR | unit 4 general_output |
| JL | U1518 | O5 | OPA4197IDR | none (same die; package only) |
| JR | U4346 | E3 | OPA4196IDR | unit 4 general_output |
| JR | U8314 | M4A | OPA4196IDR | none |
| JR | U8417 | M4B | OPA4196IDR | unit 2 general_output, units 3–4 magnitude_indicator |

Non-goals: no K-board block moves (a later stage through `scripts/stack/geometry/links_gate.py`), no panel
hardware movement (all 438 locked centres stay), no change to the stock-FFC links, no routing/DRC/fill, no
fabrication files, no order, no hardware.

## Required change (specification first)

1. **U1518** uses the existing mechanism: add an instance-scoped entry to
   `design/partition/precision-tssop-retention.json` (family, package key, board region `jack`, board JL,
   instance O5) with this decision as the reason.
2. **The five OPA4196IDR packages** have no mechanism yet; `split_tssop_instances` in
   `design/spec/modules/io_partition.py` only maps OPA4197IDR to OPA4197IPWR. Extend it minimally so that an
   instance-scoped retention entry may name `from_mpn: "OPA4196IDR"` and maps that package to the
   `op_precision` shortlist record (OPA4197IPWR). Raise if an entry matches nothing, as today. Do not change any
   other OPA4196 package. Add a unit test for the new path next to the existing io_partition tests.
3. Regenerate through the normal generators: `bash scripts/checks/regen-all.sh`, then `pnpm circuit:generate`
   if the component catalog changes. Do not hand-edit generated schematics, netlists, reports or
   `doc/src/content/docs/components/`.
4. Component evidence: OPA4197IPWR is already owned by `.claude/skills/component-ti-opa4197ipwr/`. Update its
   declared placements/roles as `circuit/WORKFLOW.md` requires, so `pnpm circuit:check` stays PASS.
5. Rail budget: let `design/power/rail-budget.json` regenerate. Report the new −12 V and +12 V totals against the
   ceilings; expected about +17.2 mA typical, +25.0 mA maximum per analog rail. Do not edit the ceiling; #34 owns
   the overshoot.

## Additional simulation before acceptance

U8417 units 3–4 (magnitude indicators) become OPA4197; MC04-S4 case 5 simulated the indicator loop with OPA4196
only. Rerun case 5a/5b of `design/spec/cells/sweep_input_buffer_vendor.py` with OPA4197 at 0 pF and 7.2 pF added
(U8417 stays on its front board, so 0 pF is the as-built case), and add the rows to the same report with
`--check` drift detection. If the 0 pF margin is below the ASSUMED 45° criterion, stop after the simulation and
report; do not commit the swap for U8417.

## Report (completion and hand-back)

Push to `claude/project-thread-iw3gai`, then report:

- the commits (spec change separate from regeneration), and sha256 of `design/reports/io-partition.json`,
  `design/power/rail-budget.json` and the simulation report;
- for each of the six packages: new ref (if renumbered), footprint, board, and the placement result the
  regenerated floorplan gives (distance from the pre-adoption slot; stage 3 predicted 13.4–32.1 mm, four beyond
  25 mm). Report a fit conflict with dimensions; do not move hardware to resolve it;
- the U8417 OPA4197 indicator-loop margins;
- every check with PASS / FAIL / NOT RUN and the reason: `pnpm circuit:check` before and after,
  `regen-all.sh` and `--check`, `python3 scripts/checks/instrument_readiness.py --check`, the new unit test,
  and the existing io_partition tests.

## Environment and budget (WSL session fills these)

- Model / effort / session ID: record from the client, not self-description.
- KiCad 10.0.6 only through `scripts/kicad/run.sh` with the pinned image; a missing oracle is a failure.
- Use the machine-wide heavy guard for regeneration and simulation; one native job at a time.

Native result: **NOT RUN** at this brief. Every schematic and PCB remains an unvalidated draft.

## Revision 1 after independent review (2026-11-21)

The run (`d25dd9f`, `b610521`, `bd76809`, `102d9c1`) made the spec swap correctly and minimally: exactly the six
packages changed MPN, refs unchanged, rail deltas exactly +17.2 mA typical / +25.0 mA maximum per analog rail,
panel hardware unchanged. The manager regenerated the power-contract decomposition and ledger (`decompose.py`,
`ledger.py`; the canonical +12 V requirement is now 1700 mA, equal to the contract, so the +12 V contract margin is
0 mA). That goes to the owner; the four `test_decompose.py`/`test_ledger.py` tripwires stay failing until the
owner rules. Do not edit them. Fix these and push:

1. **Simulation seeding.** The seed gate at `design/spec/cells/sweep_input_buffer_vendor.py:254` changed the
   reviewed OPA4196 S4 rows (0 pF / 1 µA 110.4° → 107.3°; 0 pF / 10 µA 92.72° → 85.9°), and the OPA4197
   7.2 pF / 1 mA point mixes a seeded voltage-injection run with an unseeded current-injection run. Record and
   assert the same DC operating point in both injection runs, apply it to both models, rerun, and report the
   change from the reviewed S4 values.
2. **Wavefolder plots.** `test_wavefolder` fails because `design/spec/modules/wavefolder-plots.json` pins a stale
   report hash after the io_partition digest changed. Regenerate the oracle traces and run
   `design/spec/modules/plot_wavefolder.py` with matplotlib 3.9.2 in a disposable venv.
3. **Placement record.** The hand-back misread D2232 (it moved back onto its slot). Report the real new
   displacements from pinned slots: D4309 44.8 mm (JR, face B→F; an E3 input diode now 37 mm from U4346),
   RB2116 30.9 mm (F1), RB1405 20.3, RB1504 15.8, D8333 10.9, R8325 10.9 mm, and C1341 25.7 → 30.7 mm. Correct
   the comment at `design/partition/partition35_floorplan.py:42-43` ("JR evicts nothing"). If the floorplan
   generator can keep D4309 within the protection-diode locality of U4346 without moving panel hardware, do
   that and report; otherwise report it as a fit conflict with dimensions.
4. **Commit hygiene.** Keep regenerated SVG deletions in the regeneration commit, not the simulation commit.
5. **Hand-back.** List as open, not passed: `test_rail_options` (count tripwire, deferred to #34),
   `test_instrument_readiness` (24 PCB mismatches until the layout stage), and any environment-only failure with
   its reason.
