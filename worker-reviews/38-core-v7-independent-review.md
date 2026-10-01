# K v7 native prerequisite — independent bounded review

## Conclusion

Native/source prerequisite review closes for the retained v7 nominal geometry. No physical/source identity defect found. This is not full-basis model or electrical acceptance.

Independently executed the read-only core_model_gate: PASS80 dependencies; actual DRC belongs to the v7 board, KiCad10.0.6, zero rule errors/parity issues,551 warnings. All source/artifact/copied-board/companion hashes matched. Parent guard571s result was not rerun. Unfinished non-ground signal/rail routing remains explicit:7354 named open edges, unchanged from v6, does not complete #43.

## Complete actual source inventory

Independent partition connector/pin and load-terminal reconciliation confirms1903 fitted own+376 GH+9 main=2288 unique connected source contacts,2287 balanced functions. Every GH and main is single-face F.Cu; main positions exactly match source+[100,50]. The raw board has2296 AGND pads: eight extras are exactly source-DNP C106:2,C146:2,C147:2,C148:2,C206:2,C246:2,C247:2,C248:2. Their copper remains in the conductor even though they supply no fitted load function.

1898 fitted own contacts are B-only. Five U6101 contacts(2,4,5,6,8) are PTH on all four foils. A B.Cu numerical probe convention does not reduce their actual source boundary to B.Cu or discharge inner-wall/F/B annular lifting requirements.

## v6/v7 deltas checked

- All13698 native items,499 holes and59 zones exactly equal by UUID; zone list order differs.
- All1509 connectivity member sets equal; new feed_classification labels account for cluster differences.
- Outline, stackup, native project rules and main member lists equal.
- All raw native top-level block multisets equal:3793 footprints,292 vias,59 zones,6 Edge.Cuts lines and setup/general/layers. Physical native blocks have not changed; byte hashes differ through serialization/order.
- Project JSON differs only by meta.filename v6→v7.
- All3594 source footprint-origin records, representative package fields/original units, main arrays,104 header stitches, native own-land rules and complete source-ground inventory equal.
- v7 export adds explicit enabled F/In1/In2/B layers, source/native depth1.6mm and foil bands[0,.07],[.13,.20],[1.40,1.47],[1.53,1.60]mm. This reports existing nominal stack, not fabrication/material qualification.
- Native receipt source epoch changes are exporter/native_stack helper/aggregate IO; no old receipt is rebound.

## Bindings

- v7 native receipt: `1e2f31fc78c54f5876dfdace07d5de1b9dfda143f2cf15420600fb682fc76058`
- v7 geometry: `a5b6ab06e376502a4516ce3632268c26a64f5705c168a778240809f60cea1ec6`
- v6 board: `589b3e0462657f74aac0e9cf96149a901f38bfbebf1a534737b4e5a1a5838ec0`
- v7 board: `98993d11e143da86ecc72190a1a4a0c6c9677b3b7bf431b78f6b3868615ae411`

The initial source-only full inventory helper296a97b9… and full-ground-basis-v1 receipt `0a7616fdc3a5b6a8a8df97f3ca0b8f6d372e33c8a39d6186f1947a089a063453` independently matched81 dependencies when reviewed; focused source/GH/connectivity/DNP test PASS1/5.060s. Root then changed the helper to implement full admission, so the final check correctly observed v1's helper digest becoming stale. Retain v1 historically and generate a fresh receipt. New full admission is reviewed separately; this note does not present stale v1 as current.

No source edits, native or full solver runs. An initial assertion that ALL native pads total2288 was resolved by the eight valid DNP pads above. Current/contact/material/process/3D/primal/common+positiveK and joined electrical acceptance remain OPEN.
