# Stage56: close the Stage55 adoption findings on a disposable osc-core candidate

**Disposable candidate verification. Not adoption.** Canonical schematic, board
schematics, PCB, BOM, partition, placement lock and `decision.json` are unchanged;
KEEP_K1402_INCUMBENT stands. No zudo-pd edits, order, fabrication or energisation.
Base: Stage55 (`0f873098`, draft PR290), itself on `e1969027` (PR287, Issue278).

Stage55 verified the Stage54 idle-quad removal (12 quads, 24 bypasses) on a disposable
copy and left two findings before canonical adoption:

1. **U111 schematic parity.** 345 osc-core packages carry unit-dependent Role or
   LogicalCellKey (158 also Island). KiCad compares a footprint with one unit, so the
   choice of unit decides parity; the Stage55 candidate reported one U111 Role item.
2. **Bypass proximity.** For U101 REF5050AIDR, U107 and U207 LM393BIDR the nearest
   +12 V capacitor was a removed one (C144, C128, C240), closer than their own bypass.

This stage builds one candidate that closes both and reruns the full gate set. Like
Stage55 it is a demand-side cleanup gate only: the 1700/1600/300 mA continuous and
2000/1900/400 mA transient source requirements are unchanged and no supply gap is
closed (PR289 / #288). 42 mA/rail stays a maximum-Iq planning allowance; the typical
model is 27.36 mA/rail; neither is a measurement.

## Changes in the candidate

- **Retained bypasses.** C144, C128 and C240 stay. They are family parts that render
  once per H1/H2 instance, so their counterparts C244, C228 and C140 stay too (six
  100 nF GRM188R71H104KA93D on +12 V/AGND). Their `Decouples` attribute is re-owned
  from the removed IC to the survivor's package stem; value, MPN, footprint, position
  and nets are unchanged. Removal is now 12 quads + 18 bypasses = 30 parts; the same
  48 private board nets disappear.
- **Unit-field ambiguity.** For every osc-core package whose units disagree on Role,
  LogicalCellKey or Island, that field is dropped from all its units in the board
  render (824 package/field pairs on 333 surviving packages: Role 333, LogicalCellKey
  333, Island 158; Stage55's 345 included the 12 removed quads). This is
  a narrower form of the projector's JL/JR rule (which drops these fields
  unconditionally), done here as a render transform; `scripts/schgen` itself is unchanged. 30 board sheets change.
- **PCB field sync** (`pcb_fields.py`, host text edit of top-level footprint properties
  only). The renderer always emits Role and Island (as `""` once dropped), so the
  footprint fields are set to `""`; LogicalCellKey is not rendered, so it is deleted.
  The six retained caps get the new `Decouples`. 824/824 field syncs, 6 updates.
- **PCB cleanup** (`pcb_cleanup.py`, oracle) is the Stage55 rule on the 30-part roster,
  with the free-end test now using track half-width against removed pads, which
  closes the Stage55 C240.1 centreline-stub exception (C240 is retained anyway).
  30 footprints and 95 copper items removed (48 private-net, 47 free-end rail).

## Results (`native-audit.json`)

Baseline side is the retained Stage55 evidence of the same canonical board
(`fa60b4e1…`, bound by hash).

| Gate | Stage55 baseline copy | Stage56 candidate | Result |
| --- | --- | --- | --- |
| ERC errors / warnings | 0 / 218 off-grid | 0 / 218, identical signatures | PASS |
| DRC rule errors | 0 | 0 | PASS |
| Schematic parity | 0 (gated) | **0** (Stage55 candidate: 1) | PASS |
| Complete native ratsnest edges | 1402 | 1390 (only +12 V/−12 V 80→74) | PASS |
| Nets gaining edges / new open nets | – | none / none | PASS |
| Rail clusters (pad membership) | 81 / 81 / 214 / 1 | 75 / 75 / 214 / 1 = baseline minus removed pads | PASS |
| Uncapped warning types | track_dangling 12, silk_edge 6, text_height 4 | identical signatures | PASS |
| Capped types (199), whole board | hole_to_hole, silk_over_copper, silk_overlap | still 199 each | see below |

The six removed-only clusters per supply rail are the isolated OPA4197 supply pads of
U116–U118 and U216–U218, as in Stage55. No other net's edge count changed. The 325
distinct "new" signatures (397 removed) are all silk_over_copper (198) and
silk_overlap (127): truncation
reshuffling at the 199-marker cap.

**Capped types, bounded check** (`capped_diff.py`, `capped_tiles.py`, `capped-audit.json`).
KiCad 10.0.6 caps each type at 199 markers and kicad-cli cannot raise it; a full-board
X tiling was stopped because silk_overlap reached 199 in every 40 mm tile. Instead:

- The item-by-item source diff shows the candidate is the canonical board minus 30
  footprints, 77 segments and 18 vias, with nothing added. All other differences are
  hidden Role/LogicalCellKey/Island/Decouples fields (339 footprints) and zone
  whitespace (5 zones). No DRC item in any report names a hidden field.
- All three checks compare pairs of existing items, so removing items cannot create a
  violation, and outside the removed-item box (X 215.0–262.7 mm) every pair is
  geometrically identical. Non-regression therefore holds by construction.
- Confirmation, one DRC per side (2 of a hard cap of 8) on the tile X 214–264 mm, with
  `severity ignore` rules for pairs entirely outside it: hole_to_hole 58 → 58 and
  silk_over_copper 0 → 0, both complete, no new signature: **PASS**. silk_overlap
  reaches 199 in the tile on both sides, so its complete count is **NOT ESTABLISHED**;
  its non-regression rests on the construction argument above.

## Decoupling (`decoupling.json`, source level)

- No surviving osc-core IC now has a removed capacitor as its nearest same-rail
  capacitor (Stage55: U101, U107, U207).
- Nominal reduction: +12 V 0.6 µF (49.9→49.3 µF), −12 V 1.2 µF (42.2→41.0 µF).
  No DC-bias, tolerance, temperature or ESL derating.
- Ownership is preserved for every surviving IC. U1601–U1604 lack a complete owned
  bypass before and after; that existing gap is unchanged.
- **Nominal ownership of two caps.** C140 (14.19 mm from its new owner U107) and
  C244 (23.09 mm from U201) are kept only because the family model retains H1 and H2
  together. Their `Decouples` label is nominal; they act as general +12 V rail
  capacitance, not as local bypasses. Distances are floorplan origins, not copper.

## What this does not establish

No PDN impedance, analog, thermal, assembly or hardware result; no measured current.
Dropping the ambiguous unit fields removes metadata (Role, LogicalCellKey, Island)
from 333 osc-core packages in the board render; downstream consumers of those
fields on osc-core were not audited beyond `pnpm circuit:check`. Canonical adoption
needs explicit owner approval, then a generator change (osc-core unit-field rule and
retained family keys), BOM/worksheet updates and a fresh full CI on the adopted head.
