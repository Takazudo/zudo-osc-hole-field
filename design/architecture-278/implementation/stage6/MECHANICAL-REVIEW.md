# Independent Stage 6 mechanical review

All twelve Stage5 opposite-face projections are removed by nine explicit whole-header translations, using a stronger annular-pad envelope and the entire GH courtyard as an exclusion. No body cavity or opposite-face Z clearance is assumed. The source screen passes across480 contacts,10 female mounting holes,85 complete headers and30 shared-reference packages. Full mechanical acceptance remains **OPEN**; native/ERC/DRC, simulation and physical validation are **NOT RUN**.

## Signed drawing registration

The exact official drawing URLs, identities and SHA256 hashes remain in Stage5 din-evidence.json. Stage6 re-inspected both typesheets, including enlarged female flange and male axial-section views, plus the retained official JST eGH.pdf top-entry layout and header dimensions. Coordinates are drawing-derived source proposals, not an installed/native footprint proof.

Use drawing u right and v down, with origin halfway between contact positions16/17 on row b. In female A, position1 has u=+39.37 mm and rowa has v=−2.54 mm. In male B, position1 remains at positive u but rowa has v=+2.54 mm. The female transformation into current global XY is (−v,u), while male B uses (v,u). These opposite handedness transforms make all96 named mating contacts coincide, including the selected a/b/c rows. The checker compares all electrically used DIN pads against that registered grid; mutations of row orientation, mirror, angle or endpoint position fail closed.

The enlarged female A board-drilling view places the flange-hole axis0.3±0.1 mm above row b, toward rowa. Therefore current global flange centres are bank centre+(+0.3,±45) mm. The maximum hole radius1.45 mm is enlarged by hypot(0.1,0.05) for offset/half-span tolerance. The male has different flange spacing and an axial mounting datum; its flange is not copied onto the middle PCB. Fasteners and male support/load paths remain separate engineering work.

## Proposed copper and conservative body exclusion

Every contact, including all NC positions, gets a proposed1.8 mm circular copper land for this source screen. This is an engineering input, not a manufacturer pad recommendation or fabrication release. Against the official maximum1.1 mm drilling and0.025 mm true-position radius, the remaining annular ring is0.325 mm before fabrication tolerances. At2.54 mm pitch, nominal adjacent copper gap is0.74 mm, or0.69 mm after opposed positional allowances. Etch/plating, finished-hole process and circuit clearance rules remain unqualified.

The pad exclusion radius is0.925 mm. All such circles and the signed female flange-hole envelopes must miss all entire GH courtyards, covering body, solder lands and reference toe regions without depending on undocumented lower-body cavities. The previously retained GH courtyard is a conservative project reservation; it is not presented as a manufacturer tolerance solid. Solder-fillets and screwhead/washer/tool envelopes remain unknown.

JST top-entry source dimensions place the reference header outline approximately0.20..4.45 mm from the signal-land centre row:5.6 mm overall pad extent,0.3 mm reference end inset and4.25 mm body depth. The mounted body reference height is4.05 mm, with0.15 mm stand-off reference. The source uses a proposed1.6 mm middle PCB with female mating-side mount surfaceZ50 and opposite GH surfaceZ48.4. Female tail endpoints areZ46.95..47.15 from2.85..3.05 mm termination length. They overlap the GH reference body envelopeZ44.35..48.25; placing parts on opposite faces therefore cannot establish clearance. The full XY exclusion removes this dependency for the twelve listed cases without claiming complete physical solids.

## Complete-header changes and budgets

Deltas are cumulative from the original assembly middle-header coordinates, not incremental on Stage5:

| Instance | Whole headers | X translation mm |
| --- | --- | --- |
| O3 | SAW, PUL | +1.8 |
| O3 | K-O1-1, K-O1-2 | +5.0 |
| O4 | K-O1-1, K-O1-2 | +1.0 |
| O5 | K-O1-1, K-O1-2 | −3.0 |
| O3 | VCO/LFO | +1.0 |

All85 origins/courtyards/pad sets and pin links remain represented. Source checks report zero contact-pad/flange-envelope versus GH-courtyard intersections, zero same-face header-courtyard intersections and zero shared30 courtyard/hole-or-pad intersections. Reverting the headers to Stage5 restores exclusions under the stronger envelope.

The independent checker rebuilds and compares the complete parent rebudget report. It retains225 paths,240 returns and270 wire checks. Relative to Stage5,29 path rows and24 return records change. Minimum wire service slack is13.138613 mm against10 mm required; maximum path remains334.018298 mm, with38 paths above300 mm. Root rebudget preserves all non-middle path segments, endpoint identities, return ownership and shared capacitance obligations. All270 wire XYZ coordinates now use the registered GH opposite surfaceZ48.4, with the earlier conservativeZ50 result retained separately. No front/rear physical package movement or power repartition is implied by these header moves.

## Remaining boundaries and validation

This resolves the twelve recorded source exclusions, not full board or assembly acceptance. Exact native mirrored footprint registration, PCB face/thickness tolerances, male mounting flange support, fasteners, soldering processes, frame/guide strength, cable bends, all438 hardware Z solids and non-OSC occupied-volume disposition remain open. Existing service/withdrawal constraints and canonical artifacts are unchanged. The root's bounded X1 hosting increment is separate and must screen its own volumes against these coordinates.

Nine focused tests and deterministic --check pass, including signed-transform, flange-sign, angle, electrical-pin and annular-pad mutations, full-count checks and restored exclusions after reversion. The root rebudget's own tests are separately recorded. No native execution, fabrication or hardware energization occurred.

## Reviewed source hashes

| Source | SHA256 |
| --- | --- |
| `design/architecture-278/implementation/stage6/mechanical-input.json` | `8c2319da4c9d2dceb4fe41450dfef961cb533fc66e06f99722f8982a19d02300` |
| `design/architecture-278/implementation/stage6/header-repair-input.json` | `4ba94d09a5adea5b26ba5da17f25160fc241626fbc71fa324d13a7db23f79b37` |
| `design/architecture-278/implementation/stage6/candidate-report.json` | `2a7eb6d0c9095d864854209cf7280a6e1f8719b06ec5f1142ad2694c855431f7` |
| `design/architecture-278/implementation/stage6/mechanical-report.json` | `70824bb0cccedafc6287517e848a51ec32cf147b6171325ef6c6223bf4f26e71` |
| `scripts/architecture278/implementation/stage6_mechanical.py` | `93f66ec6fff506611096011e679b246d4143fe7e37886fb59d5d823ba2cb126d` |
| `scripts/architecture278/implementation/test_stage6_mechanical.py` | `af78ed0f7c289368125bbfeb5213196eb906aed6501724852b8f99fc79b50687` |
| `scripts/architecture278/implementation/stage6_rebudget.py` | `43e270c553fd089a8bb9f2b5f59c986bc3bdaf87e841b1f2af2085c3e161772a` |
| `scripts/architecture278/implementation/test_stage6_rebudget.py` | `b9cd5f948bb506ca65a9f490184d070e2932ec4fd5334eeb1280d70417c19786` |
