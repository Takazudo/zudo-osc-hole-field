# Issue #20 top-render review

Reference: R21 318 × 298 mm rendered proof attached to issue #20, inspected at full resolution. Target: `panel-top.png`, KiCad 10 top-side render with proposed black mask, white silk and exposed ENIG gold. Whole-board, oscillator jack group and envelope control columns were opened at close range.

| Contract item | Inspection |
| --- | --- |
| Flat rectangle, 18 × 10 jacks above 18 × 8 controls, divider y = 166 mm | Present; fixed outline and all 438 features read back from the lockfile. |
| New project title at upper left | `ZUDO / OSC HOLE FIELD` visible. |
| Labels, toggle words, headings and icons | 180 jack labels, 142 control labels, 71 toggle words and 65 headings sourced from the art-only renderer; legible in both close-ups. |
| Gold and white brackets | 155 accent and 131 plain features match the lockfile flags; toggles/buttons have no brackets. |
| Module separators and mixer relation marks | Visible. Separator clipping is wider for the KiCad stroke font, leaving 147 segments versus 151 in the proof; this clears the DRC. |
| Indicator windows | 114 mask-only Ø1.6 mm proposal features at locked centres; no drills. Optical performance is untested. |
| Old title, review header/footer, hardware pictures | Absent from the KiCad board. Holes appear open in the top render; hardware is intentionally not drawn on fabrication layers. |
| Artwork overlap and manufacturing-rule floor | KiCad panel DRC has zero violations; switch words ≥1.0 mm, silk strokes ≥0.15 mm, copper strokes ≥0.2 mm. Three long jack labels are lowered 0.4 mm for exposed-bracket clearance. |

The proof is a look reference, not a mechanical qualification. Actual nut/shaft fit, selector auxiliary-hole conflict, black-mask and ENIG appearance, indicator readability, and mounting/stack decisions remain open. No fabrication files were generated.
