# Stage 7 mechanical source assessment

This assessment was written by the author of the mechanical generator and input. Independent review is performed separately by the root, electrical and interface/code reviewers.

The X1 source demonstrator retains56 complete packages,76 units,182 pins,10 bypass associations and7 fixed panel centres. Thirteen focused tests and deterministic --check pass. All12 bounded source exclusion screens report zero findings; this is **not physical acceptance**. Native/ERC/DRC, simulation, fabrication and physical validation were **NOT RUN**.

The25 earlier opposite-face package projections are individually resolved using complete courtyard exclusion, with no inferred body cavities or shortened tails. Actual fixed-hardware through-pad boxes from all438 centres are screened. Whole-package movements preserve pins and units. Every front package and transport header must fit its own board outline; separate package/header mutation tests verify rejection outside that outline. U3304 and its bypasses move rigidly; the U3305 output-feedback group is regrouped locally, including both bypasses, R3314/15/16 and C3301. Its corrected bypass rail-pad distances are2.2975 mm and2.351278 mm. All41 net spans and all10 bypass distances are recomputed from current XYZ. Some LED network spans worsen; this report makes no blanket locality or electrical-performance improvement claim. Electrical budgets and feedback constraints are separately reviewed.

The13 old generic perimeter-strip projections are superseded by seven discrete, noncollinear mount locations. Jack mounts are(107,125),(160,119),(107,160),(160,160); control mounts are(108,269),(93,289),(123,289). Proposed M2.5 hardware uses2.7 mm PCB holes,5 mm washer and driver envelopes and a4.5 mm screw-head envelope. The clamp is physically ordered: rear head/washerZ21.6..24.1 bears on PCB rear face21.6; PCB spans20..21.6; the opposite-side shoulder spacerZ10..20 bears on panel-facing surface20 and carrier bossZ8..10. Rear driver approach isZ24.1..43.9. Hole-to-board-edge annulus is explicitly checked. These dimensions are engineering proposals, not selected-part ratings. Carrier-to-enclosure attachment, fastener grade, load distribution, stiffness and proof-load remain **UNKNOWN**; no floating boss is credited as a qualified chassis load path.

The control board has a proposed bottom extension to host the transport headers and triangular mount pattern. Both substrates include42 explicit rectangular clearance apertures around exact foreign through-pad boxes with0.1 mm per-side proposed margin. These remove known pin-material obstruction only: they do **not** establish clearance to neighboring bodies or PCBs, adopt neighboring functions, or prove installation access. No unknown neighboring space is treated as free. Apertures and mount holes are screened against own packages, transport headers and mount contact/tool regions. Connectivity is computed on the exact rectangle arrangement with circular mount holes conservatively boxed; positive web widths are diagnostic, not manufacturing or stiffness criteria.

Final front transport header centres are J-SIG(127.7,159), J-PWR(142.8,159), C-SIG(101,291), C-PWR(115,291). The first two moved to clear foreign-pin substrate apertures. Front pads use rear PCB faceZ21.6; middle pads use panel-facing faceZ48.4. All eight header bodies, mating-reference heights and15 mm normal extraction sweeps are screened together in common XYZ, including simultaneous sweeps and rear mount-driver access. Strain-relief boxes use rotated offsets and proposedZ30..34 enclosure/carrier support; C-PWR offset(−8,−8) avoids the other middle-header sweep. None is treated as solder-supported or force-qualified. Wire/contact budgets and mis-mating constraints are in the independent interface/electrical reports.

The five old middle/rear fixture projections are bounded by explicit proposed rear-facing Z requirements: guide1 stays atZ64.2..105; probes1/2 and power1/3 stay atZ69.2..87.2. These requirements provide at least15.8 mm separation from the middle-side service sweep if selected hardware meets them. Exact guide, probe-tool, power-connector/loom and strain-relief bodies remain unselected; the report labels the result conditional rather than claiming verified clearance.

Remaining blockers are precise: carrier/chassis attachment and strength; actual neighbor body/PCB occupied volumes; production substrate webs and hole/annular tolerances; solder/tool/strain hardware; fulfillment of the rear-fixture Z requirements; and electrical/native/physical validation. Other functions and POWER are not silently hosted. The incumbent/canonical design and other OSC geometry remain unchanged.

## Substrate diagnostics

- X1-control: 1 connected component; minimum positive axis-aligned web 0.5400 mm. No structural acceptance is implied.
- X1-jack: 1 connected component; minimum positive axis-aligned web 0.4200 mm. No structural acceptance is implied.

## Source receipt

| File | SHA256 |
| --- | --- |
| `design/architecture-278/implementation/stage7/mechanical-input.json` | `c57e010ada43bd51757ed2d1f12005b4c42ad88d8646c79ba0333a3580d66a17` |
| `design/architecture-278/implementation/stage7/interface-input.json` | `4e665e4da5f8a72daee36c0660bd191423841d204f6726365341e091c3ad2b9e` |
| `design/architecture-278/implementation/stage7/mechanical-report.json` | `a3946ca5f41751a4ce01cc37a70a5657a79f8c3c751888c7e89f6ef32380741a` |
| `scripts/architecture278/implementation/stage7_mechanical.py` | `fe1450236382500668f525fcee19c68ed773c1d614fff6cada467a39bcb2a3c1` |
| `scripts/architecture278/implementation/test_stage7_mechanical.py` | `557a4e20dce6f87575580bc6630075aaae9de578bb9018678afb44fbce2038ff` |
| `scripts/architecture278/implementation/stage7_interfaces.py` | `bcda866923f4cef4c7b154fa45823a044e64b11ac03adfe1054c239241aee984` |
