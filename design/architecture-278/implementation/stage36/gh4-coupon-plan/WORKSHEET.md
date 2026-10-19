# GH4 coupon handling worksheet — all results PENDING

No physical work was performed. Copy this worksheet per specimen/run; retain first failures and raw photographs. This is a low-load unpowered handling observation, not endurance, pull-force or OSC qualification.

## Identification and setup

| Field | Record |
| --- | --- |
| Date/operator, specimen A or B, board revision/hash | PENDING |
| Header full MPN/lot, housing full MPN/lot, drawing revisions | PENDING |
| Contact/precrimped lead MPN, source, gauge, strands, OD, length | PENDING |
| Clamp jaw x/y/z extents, overhang, support surface, board bow | PENDING |
| Grip method/tool and operator, broad-face contact regions | PENDING |
| Instruments, resolution, calibration, coordinate-registration uncertainty | PENDING |
| Photographs top/side with scale and pin1, latch side, axes | PENDING |

Coupon coordinates differ from installed coordinates: establish connector wire-exit origin, u along pitch, v across broad faces, w withdrawal. Mark latch side empirically, never infer its sign from a mirrored drawing. Record transform from coupon x/y/z to connector u/v/w. No OSC obstructions are represented by the bare coupon.

## Observations (mm and degrees; signed extents, not just total widths)

| Measurement | Raw range / uncertainty / evidence |
| --- | --- |
| Mated header/housing height and wire-exit origin | PENDING |
| Latch contact location(u,v,w), required depression vector/stroke | PENDING |
| Latch actuation finger/tool min/max u,v,w through full stroke | PENDING |
| Whole-row grip min/max u,v,w on each broad face, including fingers/tool | PENDING |
| Straight wire-exit length and observed curvature during grip | PENDING |
| Approach angle about each axis and resultant angle, worst observed | PENDING |
| Axial travel at latch release, electrical disengagement, full mechanical clearance | PENDING |
| Combined latch+grip swept envelope for full sequence, including rotations | PENDING |
| Clamp/board interference and minimum signed gap, with uncertainty | PENDING |
| Board displacement/bow, housing/joint motion, damage before/after | PENDING |

Plan a small recorded sequence of up to three normal handling cycles per specimen; stop at the first obstruction or damage. This count is not a durability requirement or pass rating. Insert with distributed housing pressure. Depress latch fully before withdrawing with full wire-row broad-face grip; do not pull a single wire, gather along pitch, twist or force resistance. Maintain measured angle plus its uncertainty ≤15°. Stop if inability to comply; do not increase angle to obtain a result.

For each extent report measured minimum/maximum plus instrument, alignment and repeatability uncertainty; retain worst-case outer bound rather than average. Sweep the complete grip/tool geometry through measured motion; tip travel alone is insufficient. Include combined latch actuation and grip where simultaneous. Record failed attempts separately. A positive clearance requires lower bound(gap)>0; missing obstacle geometry yields UNKNOWN, not zero thickness/free space.

Optional continuity is a later separately authorized meter-only check with meter test current recorded, no external supply or powered circuit. Probe TP pads with appropriate mating housing attached; never insert probes in socket contacts. Record pin-to-TP mapping, cross-net shorts and resistance including instrument/leads before and after. Remove probes for motion. No such check was run here; this plan authorizes no energization.

## Decision record

- Coupon access candidate: reject if full latch release, correct whole-row grip or ≤15° bound cannot be achieved, or clamps/board obstruct motion. Revise size/fixture proposal and repeat; do not alter OSC geometry. Accept only as observed coupon access for the recorded specimens, not manufacturing or installed qualification.
- Compare resulting connector-local envelope with [sequential gate](../sequential-gate/README.md). Optimistic outward bounds+v5.405mm,−v1.848mm and axial H+q≤9mm are coupled, zero-angle/reference assumptions; exceeding any applicable optimistic bound rejects installed feasibility. Fitting them **does not pass**. A15mm travel at15° alone adds4.019mm lateral sweep, before grip rotation and uncertainty.
- Installed feasibility requires joint3D latch/grip/approach/travel envelope, actual neighboring obstacles, board bow, carrier alignment and support/sleeve handoff. Unknown obstacle geometry stays occupied/unknown. The coupon supplies measurements only; no reassignment of cover, carrier or reservation is authorized.
- Record result separately: coupon observation PENDING; installed access UNKNOWN; retention/load UNKNOWN; wire/flex UNKNOWN; thermal process UNKNOWN. Attach exact remaining inputs and the next bounded source recomputation.
