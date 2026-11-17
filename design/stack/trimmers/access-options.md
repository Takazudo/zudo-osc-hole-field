# ST-07 access options for three unresolved front trimmers

Status: **source-grounded option study, NEEDS_DESIGN**. This note selects no part, position, aperture, routing or assembly change. It is rebound to the clean local MC-01/c6 + MC-03 composition `2c53715d49a4a7639723595590d1fd4eeb3a3c1f` and its 104-row [relocation plan](relocation-plan.json) (SHA-256 `56ce0dac92688e2a1d7a2844a8a56b1c122c04e92bd03a3db4463600d20075dd`; the plan's `source_commit` is MC-01/c6 `bf6c67718f2fe157bd58966d0c3555ea8f37b596`). Compared with the earlier MC-03 plan at `32939a6`, all 104 `records`, positions, metadata/geometry digests, source counts and unplaced replacement refs are identical; only `source_commit` and the link-gate entry of `source_sha256` differ. The plan's 30 mm, 0.5 mm-grid search is a courtyard screen, not a circuit length limit or proof that no placement exists.

## Bound evidence

| Source | SHA-256 / fact used |
| --- | --- |
| `boards/osc-core/osc-core.kicad_pcb` | `7311cd8e7aabb609c0a6d1a7f2ef42324c585d0c7b51f77c6bd3fc0338c54f22`; retained K footprint, face and pad properties |
| `design/stack/geometry/links/link-gate.json` | `1c091c1d6d4b9c000f770a0e604cb986d5c55e44cb77ea22083249afbf5cdb0d`; reviewed local c6 record with 61 links, connector/tail/slot/latch obstacles, 438 replacement footprints |
| `design/stack/fixings/fixing-sites.json` | `8402ce558d2de13512ff325a5550ef21f303d64b5e5cb86c1aa20ffe2924225b`; 22 fixing keepouts |
| `circuit/sources/ic-library/TC33X.pdf` | `b13258ee9f777b70198554ad4ed43cab2167b2bdf31bdcbe52c4956bfff1adbf`; Bourns TC33 drawing and 1.7 mm cross-slot adjustment-tool recommendation. It supplies no assembled-tool access proof. |
| [Bourns PVG3 datasheet, Rev. 09/25](https://www.bourns.com/docs/product-datasheets/pvg3.pdf) | `a4ac229ddbe03597ffee0c23073905e41f293e4e4ce3a0ad619b8af11e548838` (official PDF fetched for this study); manufacturer-only rear-adjust research candidate below, not a project source selection |
| `.claude/skills/component-passives-family/facts.json` | `9357be5ca35fbbcbaa3453ba5680ce54fd1de32b1611f3cf0fc4e3c6d8d9042b`; exact shortlisted `TC33X-2-103E` and `TC33X-2-102E` identities. Supplier allocation remains **UNVERIFIED**; that older facts file does not identify a rear-adjust substitute. |
| `design/reports/board-net-tokens.json` | `7ef8a93c0ced61f602448f53e1276d7164d6e5567096bc806685fcd3ea880c1c`; retained board pad-net names |
| `design/reports/board-side-map.json` | `e8a297a37089b23edfe6fe2fdae8840f7770cc325a848c743835c39a20479d57`; retained K footprint origins and copper faces for the TIA parts below |
| `design/reports/io-partition.json` | `37a773282d723d7f689d1e6cf009e4edd1947827a5ee45f0051e42cd4e907a0b`; retained role/pin mapping of the fixed TIA resistor, OTA and CURRENT_TO_VOLTAGE amp |
| `scripts/stack/geometry/kicad_extract.py` and `design/grid/placements.lock.json` | `23093e93bf8a5c9072310531d771f9592783673c13f9a23dd70eb9272505ecdd` and `297300b067fd646624b9e501791163fa2d60702862b61568753bf92e5b88dbe8`; source-only pad-centre extraction and K's `(100, 50)` mm KiCad-to-panel translation |
| `design/spec/modules/envelope.py` | `015b02c5d84550e19bf92b9ec838a43b255a728e02de1e562e855ba632fc2ee5`; E5 FALL_OFFSET topology |
| `design/spec/modules/mix4_vca.py` | `46d1efae983c32e763da7d3934d7fa01a7e0473c5b0c0bd586b28c9c85cf80e2`; M4A/M4B TIA_CAL topology |
| `design/spec/modules/oscillator.py` | `18393b0a9f580a91d7394a69a90cf89e2853f882fc55f37eeaa97f306c7c4377`; O4 SCALE_TRIM topology |
| `circuit/routing/osc-pcb-current-checkpoint.json` | `8bdc9552e0e001308d8fbace51b7ba815578b862eeda8eda0aa7bea66acca23d`; K has 2,226 aggregate open edges, without a retained per-net open map for these trims. |

The K rear face is at −32.2 mm, rear parts can reach −37.2 mm, and the enclosure inner rear is at −40 mm. The nominal 2.8 mm remainder is **not** a shaft, handle or tolerance clearance. Twenty-six other displaced footprints remain unplaced and can invalidate any apparent access corridor. The current board is an unvalidated routing draft.

| Trimmer | Retained connection and role | Current access finding |
| --- | --- | --- |
| `RV4508`, E5 | `TC33X-2-103E`, 10 kΩ FALL_OFFSET divider: pad 1 `REFN5`, pad 2 `FALL_OFFSET_TRIM`, pad 3 `REF5`; the wiper feeds `FALL_OFFSET` through 470 kΩ, with 1 kΩ return to AGND and LM13700 pin 14. See `design/spec/modules/envelope.py` and `design/reports/board-net-tokens.json`. | Front face, no rear courtyard candidate within the assumed 30 mm search; node sensitivity and tool access unmeasured. |
| `RV8308`, M4A; `RV8408`, M4B | `TC33X-2-103E`, 10 kΩ TIA_CAL rheostat: pad 1 `TIA_TRIM`, pads 2–3 `OTA_CURRENT`. Together with 100 kΩ `TIA_FIXED`, this is the CURRENT_TO_VOLTAGE feedback/summing-node path (`design/spec/modules/mix4_vca.py`). | Both front face, no rear courtyard candidate in that search. Treat feedback locality, parasitics and guard/routing as unresolved, not as a generic calibration lead. |

The named pad nets come from the retained board net-token map and do not show whether each connection is routed. The routing checkpoint supplies aggregate open edges only. Proposed routes, added copper length/vias, stability/noise bounds and tool approach are **UNKNOWN**.

### Existing TIA footprint locality, before any move

The retained `io-partition.json` maps `R8380`/`R8480` to the 100 kΩ
`TIA_FIXED` element, `U8313`/`U8413` to the `CURRENT_TO_VOLTAGE` amp unit,
and `U8307`/`U8407` to the OTA. The board-side map gives these **footprint
origins**, not the connected pad coordinates or routed copper. Straight-line
XY separation from the corresponding trimmer origin is only a geometric
locator; it is neither a loop-length estimate nor an electrical verdict.

| Path | Trimmer origin | Fixed TIA resistor origin (XY separation) | CURRENT_TO_VOLTAGE package origin (XY separation) | OTA package origin (XY separation) |
| --- | --- | --- | --- | --- |
| M4A | `RV8308` F `(227.60, 144.05)` | `R8380` B `(228.39, 141.41)` (2.756 mm) | `U8313` B `(228.20, 172.22)` (28.176 mm) | `U8307` B `(219.97, 148.84)` (9.009 mm) |
| M4B | `RV8408` F `(235.60, 184.60)` | `R8480` B `(240.41, 188.14)` (5.972 mm) | `U8413` B `(231.18, 189.83)` (6.848 mm) | `U8407` F `(217.22, 181.84)` (18.586 mm) |

M4A's amplifier package is already 28.176 mm away in XY from its trimmer
origin in the retained draft. This flags the *existing* path for pad-level
route and stability review before choosing option 1; moving the trimmer is
not a remedy by itself. Both TIA_FIXED resistors and both amplifier packages
are on K's back while the two blocked trimmers are on its front, so layer
transitions and the actual pad/copper route must be inspected rather than
inferred from these origins. This observation selects no new position.

The repository's source-only `kicad_extract.parse_board` reads pad centres
from the same retained K file after that translation. Combined with the
`io-partition.json` pin map, it gives these **straight-line XY lower bounds**
between pads on the named nets (mm):

| Path | `OTA_CURRENT`: trimmer pad 2 → CURRENT_TO_VOLTAGE input pin 6 | `OTA_CURRENT`: OTA output pin 5 → input pin 6 | `SUM_POSTVCA`: fixed resistor pad 1 → amp output pin 7 | `TIA_TRIM`: fixed resistor pad 2 → trimmer pad 1 |
| --- | ---: | ---: | ---: | ---: |
| M4A (`RV8308`, `U8307`, `U8313`, `R8380`) | 25.751 | 21.902 | 28.480 | 2.465 |
| M4B (`RV8408`, `U8407`, `U8413`, `R8480`) | 9.358 | 17.021 | 13.480 | 5.965 |

The OTA/amp and fixed-resistor/amp separations in both paths, especially
M4A, need the actual copper topology and stability evidence regardless of
which service-access option is chosen. The board parser reports pad geometry,
not trace connectivity, layer changes, impedance, parasitics or any stability
margin. These values do not license a trimmer move or assert a circuit defect.

## Options to investigate, in priority order

| Option | What the present evidence supports | Required falsifiable check before selection |
| --- | --- | --- |
| **1. Local access with the same part.** First look for a close courtyard rearrangement or a service approach to the current front part while retaining the TIA feedback network near its amplifier. | Existing exact-part identity and net mapping remain valid. The 30 mm greedy rear search found no position for three refs; it did not search every local rearrangement or establish an access aperture. This option avoids assuming a distant TIA feedback route. | On an isolated candidate, show the exact trimmer/100 kΩ/amp pad coordinates, baseline and proposed routed topology, added length/vias, return/guard treatment, and a sourced stability/noise/error limit. Screen all 438 replacements, 22 fixings, FFC tails/slots, both board faces and 26 unplaced parts. Independently show screwdriver axis, shaft/hand corridor, nearby part heights, reading and adjustment while assembled. Reject if any rule or access check fails. |
| **2. Exact rear-adjust replacement.** Retain the electrical position only if a specified compatible part and rear adjustment orientation can be sourced. | The current TC33 source establishes its own dimensions and tool recommendation. The separate PVG3K manufacturer lead below has an order-code construction and rear-adjust drawing, but **compatibility, supplier allocation and project suitability are UNKNOWN**. | Compare the PVG3K drawing, land/terminal mapping and 10 kΩ behavior with the retained TC33X, then model its mounted rear axis and actual tool dimensions through the enclosure with tolerance. Check changed body/courtyard against links, fixings, facing parts and enclosure. Recheck TIA circuit and native board constraints. |
| **3. Facing-board service aperture.** Keep the sensitive TIA trim local and approach its existing front adjustment axis through an explicitly designed opening. | It could avoid moving a feedback element, but no aperture or assembled tool corridor is retained. The link fields, fixing keepouts and 26 unplaced parts make a presumed clear hole unsafe. | Source the TC33 adjustment-axis and tool envelope; model the exact axis through the facing board and installed stack, including FFC fields, copper, holes, parts, fixings, supports, tolerance and access with the enclosure assembled. Independently review board strength, electrical clearance, drilling/manufacturing and native checks. No aperture is approved here. |

**Recommendation:** investigate option 1 first, specifically a local service path that preserves the M4A/M4B TIA feedback topology. If it fails with measured evidence, compare options 2 and 3 using exact drawings and tool corridors. The owner/design reviewer must decide among evidence-backed candidates; there is no justified numeric added-loop/via allowance or selected hardware change today.

**Manufacturer-only option-2 lead, not a substitute selection.** Bourns' official PVG3 Rev. 09/25 lists `PVG3K103C01` as a 10 kΩ *rear-adjust* reverse-gull-wing SMD trim. Its ordering key adds `R00` for 1,000-piece tape/reel, yielding research MPN `PVG3K103C01R00`; no supplier allocation is verified. The PVG3K drawing gives a 3.6 × 3.4 mm body, 5.8 mm terminal span and 2.2 mm adjustment-slot diameter. Its recommended PVG3K pad layout differs from the retained TC33X land pattern, so it cannot be treated as a footprint swap. The schematic marks terminals 1 and 3 as the resistive ends and 2 as the wiper. These manufacturer facts establish a part to **evaluate**, not K-board fit, assembled tool access, calibration equivalence or M4 TIA feedback stability. An isolated CAD/tool/route study must compare exact pad mapping, courtyard and height, mounted adjustment axis, tool corridor, routed feedback parasitics and sourcing before any substitution decision.

`RVO1408` is separate: O4 `TC33X-2-102E` SCALE_TRIM has pad 1 `SCALE_ADJ`, pads 2–3 `AGND`; `design/spec/modules/oscillator.py` puts a 1.5 kΩ fixed resistor between SCALE_PIN and SCALE_ADJ. The FFC projection moves it rear→front, then proposes rear `(56.6048, 242.45)` at 29.3641 mm from its projected front position. That is a geometric candidate only; oscillator scale sensitivity, routing and assembled tool access remain **NEEDS_DESIGN**.

No canonical K board, facing board, fixing, enclosure or circuit source is changed by this note. Native KiCad, DRC, fill, CI, hardware checks, changed-source regeneration, current-head integration gates and Gate A are **NOT RUN** here.
