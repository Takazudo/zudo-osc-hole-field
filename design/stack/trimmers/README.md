# ST-07 FFC trimmer and test pad access candidate

Status: **courtyard-level candidate for independent electrical and mechanical review**. No K board, panel hardware, schematic, or fixing source was changed. Generate with `python3 scripts/stack/trimmers/generate.py`; check with `python3 scripts/stack/trimmers/check.py` and `python3 scripts/checks/frozen_studies.py discover scripts/stack/trimmers`.

## Source and reconciliation

The projection is pinned to main `690366aa69450b642f7daee2cb809eb5ded38d63`. The exact file hashes are in `relocation-plan.json`; key inputs are `link-gate.json` SHA-256 `6e3141c94d8aff6d3552916fd37caf11e710607cf9add46c315107d41aa093b1`, `link-gate-options.json` `a2703fbcbf344b1bc9b06ecd4dde97605857a62c32eb1e3ca0a26400e6cd20bb`, and `fixing-sites.json` `8402ce558d2de13512ff325a5550ef21f303d64b5e5cb86c1aa20ffe2924225b`. The checker binds the board's extracted placement and courtyard geometry through `canonical_geometry_digest`, and its `Block`, `Role`, and pad-net properties through `board_metadata_digest`. A routing-only board edit leaves both projections current. The checker also compares each row's recorded module, role and nets to the live board. The raw board file hash remains in the record for audit, but is not the staleness gate.

The retained link gate places 61 FFC links and defines K rear connector, tail, slot, latch and 22 fixing keepouts. Its 438 displaced footprint records are applied cumulatively before adjustment inventory or search. It leaves 26 other displaced footprints with no position, so later placement can invalidate this proposal. The stack candidate puts K's rear face at **−32.2 mm**, rear parts to −37.2 mm, and the enclosure inner rear at −40 mm; the 2.8 mm nominal remainder is not a screwdriver or tolerance clearance.

The canonical K board has 44 front and 56 rear trimmers plus two front and two rear D1.5 test pads. The FFC projection moves `RVO1408` from rear `(41.6, 218.7)` to front `(35.1048, 222.45)`, yielding **45 front and 55 rear trimmers**. All 104 adjustments have one record. The board's `Block`, `Role`, and pad-net properties supply the inventory's module, role and net names; they are project metadata, not a verified node-sensitivity or loop-length calculation.

## Placement screen

The search considers the 45 projected front trimmers and two front pads, in ascending courtyard area then reference. It tests a 0.5 mm grid within a 30 mm circle from each projected position, shortest shift first. A candidate keeps the same orientation and uses K's rear face. The checker independently checks the K outline and edge margin, existing transformed rear courtyards and holes, every placed link's rear connector, tail, slot and latch margin, the 22 fixing keepouts, and overlap against earlier candidate placements. The grid and 30 mm radius are **assumed planning parameters**, not electrical limits. Neither a courtyard pass nor nominal rear depth proves physical tool access.

| Outcome | Count | Meaning |
| --- | ---: | --- |
| Front trimmers with a rear geometric candidate | 42 | Requires circuit loop/guard, rear tool, silkscreen and layout review |
| Front trimmers without a courtyard position in this search | 3 | `RV4508`, `RV8308`, `RV8408`; needs design decision |
| Front test pads with a rear geometric candidate | 2 | `TP301`, `TP302`; needs electrical and probe-fixture review |
| Already rear trimmers and pads | 57 | Kept as projected; rear service access unmeasured |

The 44 proposed positions have median shift **9.1856 mm** and maximum **29.3641 mm** from the *projected* positions. These values are not comparable to the old plan's 42-of-44, 9.1 mm and 31.0 mm values: that plan did not include the cumulative FFC/fixing projection or the new front `RVO1408`. `RVO1408` is proposed at rear `(56.6048, 242.45)` after a 29.3641 mm shift from its projected front position; its `SCALE_TRIM` role makes an electrical review especially necessary. No move has been selected for a board edit.

## Circuit, access and next design decisions

The output intentionally records node sensitivity, current loop length, added vias and guard status as unresolved for every row. A role or net label does not establish the adjusted component, route topology, impedance, guard need or allowable added loop length. A reviewer must derive these per role from the schematic and actual proposed K routing, set justified limits, and reject or revise any geometric candidate that exceeds them. In particular, evaluate oscillator scale and high-frequency trims, filter expo trims, summing or transimpedance adjustments, and the two rail probe pads before placement. Do not silently widen a loop limit to keep a geometric pass.

For each rear candidate, confirm a screwdriver shaft and hand approach through the assembled enclosure against real nearby heights, the −37.2 mm rear-parts limit and the 2.8 mm nominal enclosure remainder. Verify exact trimmer adjust orientation, silkscreen readability, probe fixture contact, and tolerances. For `RV4508`, `RV8308` and `RV8408`, a rear-adjust exact part or a facing-board access aperture are alternatives that need separate source, drill and facing-board clearance evidence; neither is selected. Calibration planning must specify rear approach with the front instrument assembled, stable power/reference access, a fixture for `TP301`/`TP302` if moved, and a way to read each setting. The release-gate procedure itself remains unchanged here.

This candidate is ready to hand to ST-10/ST-25 for **review**, not adoption. It requires independent review, changed-source regeneration, applicable current-head repository gates and explicit integration by the sole manager. Held board DRC/zone fill, hardware qualification and Gate A remain held.

MC-01's independently reviewed checkpoint `e4b300b31fccf53acfeafc8fbba286278c32ecfb` changed link-electrical `inputs.json` (SHA-256 `3a2b15e54e43dbbba5adb97c3451de7d948ecf78d58e14fc62313ff8765c9bd3`) after this candidate's main baseline. Direct byte comparison of the checkpoint and this worktree confirmed the link gate, link options, fixing list, and canonical K board hashes above are identical, so this candidate's **geometry and board metadata projections remain bound** to those exact inputs. At integration, compare the changed-source regeneration and all source hashes to this record, then rerun this generator and checker before using any proposed position. A matching link count alone is not proof of matching geometry.
