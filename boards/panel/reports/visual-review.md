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

The proof is a look reference, not a mechanical qualification. Actual nut/shaft fit, black-mask and ENIG appearance, indicator readability, and mounting/stack decisions remain open. No fabrication files were generated.

## Issue #37 regeneration and perimeter review

The current parameter set regenerates a 318 × 298 × 2.0 mm panel with 324 drilled apertures and 114 undrilled Ø1.6 mm mask windows. KiCad readback matches all 438 lockfile UID/x/y centres. Apertures are 180 × Ø6.2 mm jacks, 101 × Ø6.3 mm pots, 30 × Ø5.2 mm toggles, 8 × Ø5.0 mm buttons and five Ø7.0 mm octave shaft openings. No support hole is present in the panel. The 35 EL support holes and 30 P clearances, plus J/P/K edge supports and K service apertures, remain internal PCB features.

The regeneration preserved all eight unowned drawings and reported zero edited generated-art items. The panel board file was byte-identical before and after the merged-base regeneration. A fresh KiCad 10 top render was opened and compared with the prior layout; the geometry and owner artwork are unchanged, so the committed preview remains the canonical raster. The post-merge KiCad 10.0.6 panel DRC reported zero violations and zero unconnected items.

The enclosure source now proposes segmented clips in clear parts of the 0–3 mm perimeter border, with no continuous solid lip or selected profile. The owner copper border occupies that band: 0.27 mm exposed-copper lines run at y = 2.2 and 295.8 mm and x = 2.2 and 315.8 mm. A front clip cannot cover those line segments. P spans x = 1–317 mm; its Ø3.2 mm support collars at x = 3.5/314.5 reach x = 1.9/316.1, a 1.1 mm projection into the border. The outer jack columns at x = 6.5/311.5 have a 0.65 mm border intrusion under the imported Ø8.3 mm nut trial envelope; the exact nut OD is UNSOURCED. These are plan-view exclusions only. Clip section geometry, exact nut fit, strength and tool access remain NOT RUN #65.

The selector M9 bores remain in the separate carrier; the panel retains only five Ø7.0 mm shaft apertures. Installed selector and optical fit remain NOT RUN #55/#64. The conditional EXT reservation adds no panel-face opening. The panel remains an unvalidated draft; no fabrication files were generated.
