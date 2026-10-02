# Courtyard containment and repeated placement faces

Difficulty: mid — geometric containment and repeated-source invariants.
Related issue: #19. Every board remains an unvalidated draft.

The former corner/midpoint outline check accepted the courtyard rectangle
[0, 0, 10, 10] at 0.25 mm clearance inside the outline
[[-20,-20],[20,-20],[20,20],[-20,20],[-20,6],[5,5],[-20,4]].
The notch excludes courtyard point [2,5], but both long edge midpoints are
outside the rectangle. The new check tests complete segment/rectangle
intersection and minimum perimeter distances, including a nearby concave tip.
It keeps the existing 1e-6 mm positive-clearance comparison tolerance and
conservatively rejects direct boundary contact, including at zero clearance.

A repeated component could request F.Cu and be flipped to that native face,
then reuse its base instance's B.Cu template region. Both face-specific obstacle
checks and the placement report could then describe the wrong face. Every
selected region now must agree with the actual native face and any explicit
BoardSide. A mismatch reports overflow and does not save the board.

Explicit FootprintOriginMm anchors retain their documented source precedence:
README says they are checked at that coordinate and never searched elsewhere.
This change does not require all explicit anchors to be exact translations.
An anchored base now records a template for unanchored repeats; previously
that combination could raise KeyError. No fixed centres, capacities, regions,
source anchors, circuit values or hardware geometry are changed.

Baseline circuit validation passed. Guarded baseline regeneration at 0f80445
passed in 278 seconds with no tracked drift. Main 81c3fc3 (PR #102 pose fix) was
integrated before the native placer suite started. The earlier queued native
attempt was canceled before execution and is NOT RUN, not a test failure.
Sixteen focused geometry/region/pose tests passed. The fresh guarded native
placer suite passed in 28 seconds: one/six/island fixtures have zero courtyard
and parity violations; repeated placement is byte-stable; expected overflow
and wrong native-face plans leave board bytes unchanged; the owner-locked
footprint stays fixed; an anchored base seeds unanchored repeated templates.
The native F.Cu/B.Cu mutation and B.Cu positive cases inspect actual footprint
layers. Final aggregate verification is pending. Physical routing, fit and
electrical qualification remain NOT RUN.
