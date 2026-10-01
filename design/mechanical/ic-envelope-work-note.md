# Provisional IC display-envelope placement

Issue #85 corrects the generated display boxes without changing footprint pads,
board placement, copper, or any of the 438 fixed panel hardware centres. The
original package dimensions remain the same; nine boxes had assigned length and
width to the wrong footprint axes. SOD-123 was already oriented correctly.

| Footprint family | Correct footprint X / Y / Z, mm |
|---|---|
| SOIC-14 | 4 / 8.75 / 1.75 |
| TSSOP-14 and TSSOP-16 | 4.5 / 5.1 / 1.2 |
| SOIC-8 | 3.98 / 5 / 1.75 |
| SOIC-16 | 4 / 10 / 1.75 |
| DIP-8 | 6.35 / 10.16 / 0.1 |
| SOT-23-5 | 1.75 / 3.05 / 1.45 |
| SOT-23 | 1.4 / 3 / 1.1 |
| SOT-363 | 1.35 / 2.2 / 1.1 |

The DIP footprint origin is pad 1, whereas its retained Fab body is centred at
PCB coordinates (3.81, 3.81) mm. Its centred WRL therefore needs model offset
(3.81, −3.81, 0) mm. KiCad's model Y convention differs from PCB Y. The pinned
10.0.6 exporter confirms that convention, and the native tests exercise it on
both board sides and after rotation. Retained exporter source SHA-256:
`6faba000ceeb46ac63b111d39bbdb746e1e7d175454df5486d294ecba94a73f1`.
Source: https://gitlab.com/kicad/code/kicad/-/raw/10.0.6/pcbnew/exporters/exporter_vrml.cpp,
`ExportVrmlFootprint`, offset conversion at lines 1077–1095 in the retained copy.

The generator now rebuilds its owned model clause. The earlier marker-present
return left stale offsets or rotations untouched, including in check mode.
Only that model clause changes; the surrounding 2D footprint data is preserved.
All ten envelope receipts bind the revised generator. Nine WRL hashes, the DIP
footprint hash and dependent receipt hashes are refreshed while retaining the
original stock-footprint and manufacturer-PDF acquisition hashes.

## Native evidence

`ic-envelope-native-report.json` records 17 fresh native cases and four rejected
placement mutations. It covers all ten IC families, the existing four component
model-axis unit checks, and translated/rotated/bottom-side DIP cases. The new
VRML reader composes the actual enclosing scene transforms, including rotation,
translation, scale and scale orientation; closed sibling transforms do not leak
into the result. IC body centres and long axes are compared with independently
loaded native Fab outlines. The missing DIP offset, reversed DIP Y offset and
90-degree and 20-degree SOT rotations are each rejected.

Fab containment is deliberately not an acceptance rule: the generic SOD-123 Fab
outline and retained manufacturer body envelope have different widths. This
check does not establish exact lead geometry, solderability, seating, installed
clearance or fit. In particular, the DIP's 0.1 mm display plate is not a package
height, and the SOIC-16 family height estimate remains an estimate.

Eleven focused unit regressions and the fresh pinned native cases pass. Library
receipt checks pass, and selected models and footprint previews are regenerated.
The complete aggregate replay also runs in CI, with a generated diff retained on
failure. Its first run found the old DIP footprint hash still recorded for
NOISE2 in the partition report; that report was regenerated from the corrected
footprint. The fresh board projection reports zero ERC errors and 673 retained
warnings across ten boards. Documentation validation, build and built-site
checks passed, and the extended workflow passes actionlint 1.7.12. These are
source, display and draft connectivity checks; physical qualification is NOT RUN.
