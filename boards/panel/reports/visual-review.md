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

The regeneration preserved all eight unowned drawings and reported zero edited generated-art items. The panel board file was byte-identical before and after the merged-base regeneration. The historical review described a fresh top render and zero-violation DRC, but the retained PNG and DRC files still came from the earlier 6.3 mm octave-aperture board. The current-source refresh below replaces those stale retained artifacts.

The enclosure source now proposes segmented clips in clear parts of the 0–3 mm perimeter border, with no continuous solid lip or selected profile. The owner copper border occupies that band: 0.27 mm exposed-copper lines run at y = 2.2 and 295.8 mm and x = 2.2 and 315.8 mm. A front clip cannot cover those line segments. P spans x = 1–317 mm; its Ø3.2 mm support collars at x = 3.5/314.5 reach x = 1.9/316.1, a 1.1 mm projection into the border. The outer jack columns at x = 6.5/311.5 have a 0.65 mm border intrusion under the imported Ø8.3 mm nut trial envelope; the exact nut OD is UNSOURCED. These are plan-view exclusions only. Clip section geometry, exact nut fit, strength and tool access remain NOT RUN #65.

The selector M9 bores remain in the separate carrier; the panel retains only five Ø7.0 mm shaft apertures. Installed selector and optical fit remain NOT RUN #55/#64. The conditional EXT reservation adds no panel-face opening. The panel remains an unvalidated draft; no fabrication files were generated.

## Current-source native evidence refresh

The refreshed DRC and both retained/published PNG copies were exported directly from the unchanged current panel board with KiCad 10.0.6. Native readback confirms 438 fixed features, including five 7 mm octave openings, 324 NPTH holes and 114 undrilled windows. DRC includes all severities and reports zero violations and zero unconnected items, with copper-edge/hole rule floors of 0.5/0.25 mm (above the required 0.2 mm); no exclusion was added. Electronic schematic parity is not applicable to this board-only panel.

The previous and current top renders were opened and compared. The title, 18-column jack/control layout, gold/white labels and brackets, divider and border remain present and aligned; the five OCT openings now show the current larger apertures. No support drill or owner-art change was introduced. The native high-quality opaque render includes renderer shading; it is not a photograph or finish/optical qualification. KiCad exported 2352 × 2216 pixels for the requested 2384 × 2240 canvas; these are preview pixels, not panel dimensions.

`native-review.json` records the exact commands, pinned image/version, input/output hashes and actual canvas size. Board, project, parameters, lock, oracle pin, wrapper and feature-check producer bytes were checked unchanged across native exports; the panel custom-rule file was absent before and after. `scripts/panel/check_review_receipt.py` fails if source or retained/published output bytes drift; it never rewrites hashes. A source change therefore requires fresh native DRC and rendering plus another visual review before replacing this receipt. Physical #55/#64/#65 qualifications remain NOT RUN. No fabrication output was produced.
