# Moving the three blocked trims to the rear would put them 25 to 43 mm from their partners, and an IC sits behind each one

Task D step 3, 2026-11-20. Tests option 1 of `design/stack/trimmers/access-options.md` (local access with the
same part) on the retained cumulative MC04-R1 scene, and records what a through-board adjustment axis
(options 2 and 3) would have to clear.

```sh
python3 -B scripts/stack/studies/task_d3_blocked_trims/local_rear.py --output scripts/stack/studies/task_d3_blocked_trims/result.json
```

`result.json` sha256 `996375fec5a3799e5661077ca972dbde597ce00b731ac18d689d18895c990478`. The run takes a few minutes.

## The nearest free rear room is far from each circuit partner

Every raster fit on K's rear face is ranked by distance from the circuit-partner centroid, and the nearest
passes the exact predicate. Distances are footprint-origin locators:

| Trim | Partners (anchor) | Now, front: to anchor | Nearest free rear spot: to anchor | Shift from now |
| --- | --- | ---: | ---: | ---: |
| `RV8308` (M4A TIA_CAL) | R8380, U8313 | 12.78 | **43.23** (U8313 58.43) | 30.99 |
| `RV8408` (M4B TIA_CAL) | R8480, U8413 | 4.39 | **25.40** (U8413 23.57) | 29.56 |
| `RV4508` (E5 FALL_OFFSET) | R4581 (470 kΩ feed) | 13.11 | **38.76** | 31.02 |

Option 1 as a plain move would lengthen the TIA feedback paths several times over. The ST-07 screen found
no spot within 30 mm; RV8408's 29.56 mm spot here appears because this screen does not first place ST-07's
44 other rear candidates.

## The rear face under each trim is occupied, including by its own TIA partners

| Trim | Rear parts under its courtyard |
| --- | --- |
| `RV8308` | R8344, R8371, **R8380** (its TIA_FIXED partner), U8312 |
| `RV8408` | R4497, R7213, R8309, **U8413** (its TIA amplifier) |
| `RV4508` | C4558, U4539 |

So a rear-adjust part or an aperture on the current axis (options 2 and 3) must first move an IC from behind
each trim. For the TIA trims, those are the parts that make the current front position local today.

## Recommendation

Option 1 fails on room near the partners. Compare options 2 and 3 with the TIA cluster rearranged as a
unit: trim, fixed resistor and amplifier together, with the adjustment axis clear on the rear. That needs
the PVG3K drawing and pad mapping, a tool corridor and a routed feedback review. No position is selected.

## Scope

Courtyard room on the cumulative scene only, with the other unresolved bodies frozen at their old positions.
No tool access, height, routing or electrical claim.
