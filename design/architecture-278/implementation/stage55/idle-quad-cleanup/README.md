# Stage55: native ERC/DRC and decoupling gate for the Stage54 idle-quad cleanup

**Disposable candidate verification. Not adoption.** Canonical schematic, board
schematics, PCB, BOM, partition, placement lock and `decision.json` are unchanged;
KEEP_K1402_INCUMBENT stands. No zudo-pd edits, routing experiment, order,
fabrication or energisation. Start head `e1969027e63dfc22da1dbca07bf64e8778b122dd`
(draft PR287, Issue278). `bash scripts/checks/regen-all.sh` at that head produced no
tracked change.

Stage54 proposed removing 12 idle powered quads (U112/U113/U116–U119 and
U212/U213/U216–U219) and their 24 owned 100 nF bypasses, and left canonical
adoption gated on cleanup ERC/DRC and a decoupling review. This stage runs those
gates on a disposable osc-core copy. It is a demand-side cleanup gate only: it does
not change the 1700/1600/300 mA continuous or 2000/1900/400 mA transient source
requirements and does not close any supply gap (see PR289 / #288 for the ledger).
The 42 mA/rail figure remains a maximum-Iq planning allowance; the typical model
is 27.36 mA/rail; neither is a measurement.

## Method

1. `candidate.py` reuses Stage54 `prepare()` unchanged and runs the canonical board
   projector (`scripts/schgen/project_boards.py`) in memory. The unfiltered run must
   reproduce every committed `boards/osc-core` schematic byte; the candidate run
   filters only the 36 removed references from the assignment and floorplan. Only
   `sample_hold_H1_K` and `sample_hold_H2_K` change; 48 board nets disappear.
2. `pcb_cleanup.py` (pinned oracle, pcbnew 10.0.6) copies the canonical PCB and
   deletes the 36 footprints, the 48 private-net tracks, and on rail nets only copper
   whose end met a removed pad or deleted copper and now meets nothing. Copper still
   joining other copper is kept, so no chain is cut. Zones are not edited. Result:
   48 private tracks plus 34 rail tracks and 23 rail vias; AGND copper untouched.
   The end test uses the track centreline, so one 0.5 mm +12 V B.Cu segment that only
   overlapped C240.1 by its width remains as a stub inside a via's reach; KiCad does
   not flag it and it is electrically harmless, but it is a known exception.
   A second independent run is byte-identical (SHA256 in `evidence/pcb-receipt.json`).
3. `native.py` runs the identical ERC and DRC (`--schematic-parity --refill-zones
   --severity-all`) on both sides. `ratsnest_refilled.py` refills all zones and takes
   the complete native ratsnest (`scripts/pcbgen/ratsnest.py`), because kicad-cli lists
   at most 499 unconnected items on this board. `rail_clusters.py` records the pad
   membership of every +12 V, −12 V, AGND and +5 V cluster on both refilled boards.
4. `decoupling.py` reviews ownership, rail capacitance and floorplan neighbourhood.

## Results

| Gate | Baseline copy | Candidate | Result |
| --- | --- | --- | --- |
| ERC errors / warnings | 0 / 218 off-grid | 0 / 218 off-grid, identical signatures | PASS |
| DRC rule errors | 0 | 0 | PASS |
| Schematic parity | 0 | 1 (U111 Role field, see below) | PASS, classified |
| Complete native ratsnest edges | 1402 (485 nets) | 1390 (485 nets) | PASS |
| Nets gaining edges / new open nets | – | none / none | PASS |
| Rail clusters (pad membership) | 81 / 81 / 214 / 1 | 75 / 75 / 214 / 1, equal to baseline minus removed pads | PASS |
| Uncapped warning types | track_dangling 12, silk_edge 6, text_height 4 | identical signatures | PASS |
| Capped types (199) | hole_to_hole, silk_over_copper, silk_overlap | still 199 each | **NOT ESTABLISHED** |

The 12 removed ratsnest edges are the six +12 V and six −12 V single-pad clusters of
the OPA4197 quads U116–U118 and U216–U218, whose supply pins were not yet joined to
their rails. The six OPA4196 quads' supply pins were already in the main rail
clusters; removing them drops pads from those clusters without splitting any. Every
candidate rail cluster equals a baseline cluster with removed pads dropped: no cut,
no merge. No other net's edge count changed.

**Capped warnings.** hole_to_hole, silk_over_copper and silk_overlap reach KiCad's
199-marker cap on both sides. silk_over_copper shows 198 signatures swapped in and
198 out, silk_overlap 127/130: truncation reshuffling. Nonregression of those types
is not established by this comparison, as in Stage53. An informational screen finds
no listed capped marker within 6 mm of a removed footprint on either side, which,
given truncation, proves nothing either way.

**U111 parity finding (pre-existing, must be resolved before adoption).** The
candidate reports `Field 'Role' differs (PCB: 'sample_hold:unused grounded
Schmitt', Schematic: 'switch_button_input:U')` for U111, which is not removed. The
canonical render already gives U111's units three different Role values, and 345
osc-core packages carry unit-dependent Role/LogicalCellKey (158 Island). KiCad
compares a footprint with one unit. All seven U111 symbols keep identical positions,
order and UUIDs in both renders; only the symbol count of `sample_hold_H1_K` changes
(91→49). Why KiCad then compares a different unit is a **hypothesis**, not shown.
The classifier accepts only this exact (U111, Role) item, and only when both the PCB
and schematic values are among U111's unit values in both renders.
Canonical adoption would hit the same parity item. A fix is a projector/board
decision (for example, stripping unit-specific fields on osc-core as already done
for JL/JR), out of scope here.

## Decoupling review (`decoupling.json`)

- Every removed bypass is owned (`Decouples`) by a removed IC; every surviving powered
  IC keeps its owned bypasses. Pre-existing U1601–U1604 have no complete owned
  bypass both before and after; this is an existing gap, unchanged here.
- Nominal ceramic capacitance falls 1.2 µF per analog rail: +12 V 49.9→48.7 µF
  (2.4%), −12 V 42.2→41.0 µF (2.8%) instrument-wide; osc-core +12 V 28.2→27.0 µF.
  No DC-bias, tolerance, temperature or ESL derating is applied.
- Removed ICs sit 4.4–15.5 mm from the nearest surviving powered IC (floorplan
  origins); each surviving IC's own bypasses are unchanged.
- Ownership does not cover physical proximity. For three surviving osc-core ICs the
  nearest same-rail capacitor is a removed one, closer than their own bypass:
  U101 REF5050AIDR (C144 at 1.39 mm, own C113 at 5.19 mm), U207 LM393BIDR (C240 at
  0.89 mm, own C216 at 6.00 mm), U107 LM393BIDR (C128 at 3.71 mm, own C116 at
  5.15 mm), all +12 V. They need PDN/layout review before adoption; the simplest
  conservative option is to keep the nearby capacitor as an unowned rail bypass.
  Distances are floorplan origins, not copper paths.
- The change reduces downstream ceramic capacitance seen by the zudo-pd regulators.
  Regulator/cable stability is a supply-side question for the PD owner, not assessed.

## Independent review

A fresh-context reviewer (`REVIEW.md`) found the disposable-gate claim supported
with qualifications. Its findings and their disposition are recorded there.

## What this does not establish

No PDN impedance, analog, thermal, assembly or hardware result. No measured current.
Canonical adoption still needs explicit owner approval, the U111 parity resolution,
the U101/U107/U207 bypass-proximity review,
canonical generator/BOM/worksheet updates and a fresh full CI on the adopted head.
