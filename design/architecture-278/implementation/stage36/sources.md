# Source reconciliation and interface ownership

All coordinates are the existing study's millimetre frame. They are not measurements.

| Need | Authoritative retained source | What it establishes / remaining obligation |
|---|---|---|
| M35-01/02 datum/bow | Stage10 mechanical-input/report, stage10_mechanical.py; Stage31 common-input | Board/carrier outlines and toward-carrier bow amplitude only. Applying the same amplitude with both signs is a NEW conservative sensitivity/allocation. Positive B/C registration and local slope are NEW proposals. |
| M35-06 neighboring boards/components | placements.lock.json; Stage33 reservations; Stage35 occupied_obstacles | Locked XY/source boards remain; unknown depth and assumed 3 mm body heights remain occupied. Per-ref caps in analysis.json are unaccepted board/component-owner obligations. |
| M35-07 enclosure | Stage10 minimum candidate enclosure 320×319×105; Stage34 plan | Candidate envelope only; no detailed cover/rib/aperture drawing. C36 opening and rib exclusion are new enclosure obligations, not confirmation of an existing opening. |
| M35-08 roots/access | Stage10 frame and anchor geometry | Rear crossmember x237..318,y170..174,z51..62; rails x237..243 and305..311,y174..282; anchor/tool at315,172. New roots must preserve these and core envelope. |
| Core-first path | Stage31 core envelope used by Stage34 obstacle_prisms | x236..312,y174..282,z50..134 includes 40 mm extraction/handle reservation. Fixed roots remain during extraction. |
| Housing capture | design/connectors/sources/jst-gh.pdf, printed pp2–3 | GH GHR-04V-S/GHR-07V-S with BM04B/BM07B-GHS-TBT(LF)(SN); nominal housing A/B dimensions 3.75/6.25 and7.5/10; housing5.7 high×4.15 deep; header4.05 high×4.25 deep; 7.3 assembled reference. Does NOT establish keeper ledges, latch stroke, pull force or capture allowance. |

JST PDF SHA256: `b1dcb317b6b9a4fbbedd2dbf42c64c95306a252d23de8933b85fcf161240b722`.
The retained PDF pages were rendered and visually inspected. PCB pitch1.25±0.05
must not be accumulated and is not a connector mating-capture tolerance.
GH-specific handling manuals CHM-1-2149/2111 were not obtained. Generic handling
advice and nominal outlines cannot qualify the proposed keeper.

The inherited current-source correction remains conditional **A01** budgets,
not the wrong X1 module. No new wire data/current limit/stiffness is inferred.
Root material, integral joint strength, threads, fastener tolerances, stud
straightness, bore tolerance and latch access have no selected hardware evidence.
The 0.25 mm guide-path target is an explicitly proposed interface allocation,
not a manufacturer requirement or a relaxation of the existing K4 threshold.

Independent carrier translations, rotations and signed bow are not favorably
correlated. Audit rotation allowance sums three chord-displacement bounds using
the farthest prism corner from any housing exit; conservative overbounds are
intended, not a tolerance qualification. Source stack/margins are preserved.
New cap proposals never replace the unknown-occupied obstacle dataset.

Each-axis registration ±1 mm is converted to sqrt(3) mm for Euclidean
clearance subtraction against cross-carrier obstacles, replacing the inherited
scalar1 mm. Rear-carrier structural geometry shares its datum; all other
inherited stack contributors remain. This is a reservation screen, not a full
assembly tolerance qualification.
