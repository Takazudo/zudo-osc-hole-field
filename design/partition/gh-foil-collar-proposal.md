# Proposed isolated foil collars for JL–K return 1, pin 2

**UNSELECTED engineering proposal.** The retained native local projection admits the finite geometry below without moving a header, panel item or existing pad. This is not a reconstructed board, qualified process, tested assembly, source/model admission or closure of issue #38. The proposal adds no canonical copper and changes no accepted electrical target.

The companion JSON is the source for `python3 -m scripts.pcbgen.foil_collar_geometry`. The command emits proposed copper polygons, named zone set differences, current-cut coordinates, conservative interval clearances and an open cost ledger. Its portable mode checks the retained projection and source hashes. It explicitly reports native revalidation **NOT RUN**. Add `--native-root /path/to/preserved/recovery/worktree` to verify the exact full board/export byte hashes and recompute the complete local item, hole and zone projections. Even that mode checks archived geometry only; new native reconstruction remains **NOT RUN**. Ignored native artifacts are not portable test dependencies.

## Actual source and native binding

The selected conductor is `JL-K-1`, AGND pin 2: BM08B-GHS-TBT(LF)(SN) headers, GHR-08V-S housings, SSHL-002T-P0.2 contacts and Alpha Wire 6821 BK005 wire. Other AGND pins are not merged with this test domain. Native coordinates below are millimetres, translated from the partition source by `(100, 50)`.

| Endpoint | Source connector / native reference | Face / native footprint pose | Native pad centre | Pad UUID |
| --- | --- | --- | --- | --- |
| JL | JL-K-1-JL / J900001 | B.Cu / (123, 86.05, 180°) | (119.875, 86.05) | 3f388439-96b8-5e20-aa1d-16ee31561d83 |
| K | JL-K-1-K / J900002 | F.Cu / (123, 89.95, 180°) | (119.875, 89.95) | 835eae24-7f0d-5918-8d54-859e5053df59 |

Both pads retain their full native 0.6 × 1.7 mm rectangle. Footprint UUIDs, native/export SHA-256 values, faces, rotations, board outlines, stackups and exact nearby item identities are retained in the JSON. The JL artifact is `osc-jack-left-white-current-v1.kicad_pcb`; K is `osc-core-ground-feasibility-v7.kicad_pcb`. They are historical unselected drafts, not replacements for current canonical geometry. The JSON separately hashes the source partition, locked placements and exact GH footprint; a changed source epoch fails rather than silently borrowing this projection.

## Finite geometry and actual conflicts

| Parameter | Nominal CAD | Prospective finished interval / bound |
| --- | --- | --- |
| Straight neck width | 0.200 mm | [0.180, 0.220] mm |
| Straight neck length | 0.760 mm | [0.740, 0.780] mm |
| Outer foil thickness | 0.070 mm | [0.063, 0.077] mm |
| Pad-side shoulder length | 0.330 mm | [0.310, 0.350] mm |
| PCB-side flare length | 0.480 mm | [0.460, 0.500] mm |
| Flare end width | 0.600 mm | [0.580, 0.620] mm |
| Neck centre displacement | −0.050 mm in x | Additional relative registration ±0.025 mm |
| Existing copper/pad edge uncertainty | — | ±0.025 mm |
| Copper isolation | — | At least 0.250 mm |

These are positive proposed acceptance intervals, not manufacturer guarantees. Nominal 0.200 mm meets the retained K native minimum-track rule; finished etch width is a separate requirement. A finite geometry/material pullback, full-section inner containment, outward envelope and dielectric/etch capability still need evidence. The connected copper pattern is one source union: joins are not independently displaced solids. No zero-tolerance fit is claimed.

The nominal neck centre is x=119.825. JL runs from y=84.870 to 84.110, outward in −y. K runs from y=91.130 to 91.890, outward in +y. The worst dry-collar boxes are JL `[119.690,84.045,119.960,84.915]` and K `[119.690,91.085,119.960,91.955]`. Complete nearby explicit copper is tested using conservative outer bounding boxes, including opposite-foil pads. Minimum axis separation is JL 0.270 mm and K 0.265 mm, leaving margins of 0.020 and 0.015 mm over 0.250 mm. No Euclidean diagonal clearance is invented from overlapping boxes. K's rear U4218/U4219 pads explain the −0.050 mm neck offset: the unshifted nominal gap can look adequate while its finite interval fails.

JL's existing AGND stitch overlaps the pad and bypasses the collar. The proposal explicitly retires only via `0e98d896-7f4b-529e-bb8d-5d0672d24f52` and its B.Cu segment `a93acaf3-1753-5d6e-b340-4ae1bc5472cc`. They remain untouched in the preserved board. Omitting either proposed retirement fails the screen. No existing component pad may be retired.

All native zones intersecting the bounded region receive explicit proposed local set differences. Own-face pours are removed around the full pad/shoulder/collar island; other-foil pours are removed around the full collar projection. The proposed pad, shoulder, neck and flare are retained as connected AGND copper. Every unretired barrel entering the island/collar is rejected. Cross-layer XY overlap by itself is not a DC short: this candidate deliberately uses the stronger clear-projection condition at the collar. Dielectric isolation and absence of other conductive coupling still need physical qualification.

The interval flare reaches 0.080 mm beyond its own-face pour exclusion in the worst case. This is geometric reach, not proof of filled-plane connectivity or a zero-resistance boundary. The exported target-plane identity only identifies the intended landing; filled-contour intersection and actual topology must be proved after reconstruction.

JL B.Cu is **+5V**, not AGND. Its paid return therefore needs a new 0.200 mm dogleg through `(119.825,83.750) → (120.750,83.750) → (120.750,84.500)` and a proposed 0.700/0.300 mm via at the last point to In1.Cu AGND. Finished drill [0.280,0.320] mm and barrel copper [0.025,0.035] mm are prospective. The compiler emits +5V clearance for the entire flare/dogleg and new-via antipads on F.Cu +12V, In2.Cu −12V and B.Cu +5V. It preserves the intended In1 AGND landing. New via and dogleg stay outside the isolated island and require native routing, mask, annular, plane-access and electrical proof. K's flare targets actual F.Cu AGND; spreading into that foil is also paid.

## Dry support and complete trace

Retain existing pad mask openings only. Add no opening on the shoulder, collar, flare, dogleg or new via. The full possible wet support is each same-face pad's entire copper box, expanded by 0.025 mm copper-edge uncertainty + 0.050 mm mask expansion + 0.050 mm mask registration + 0.050 mm over-mask solder extent. It remains at least 0.110 mm from the worst dry collar, above the required 0.100 mm separation. The live archived check verifies zero native baseline mask expansion and no nonzero local pad/footprint overrides. Actual mask seal, three-dimensional solder support, component-metal interference and process capability remain unqualified. The unknown header interior is not replaced by invented metal dimensions.

The output cut is the collar's complete actual width through its complete actual foil thickness. Nominal native depth is JL [1.530,1.600] mm and K [0,0.070] mm. The signed trace is `I / (actual width × actual thickness)` over the entire section, with normals JL `(0,−1,0)` and K `(0,+1,0)` and opposing endpoint net currents. It is not a trace on an ideal plane, pad centre or partial surface. A potential comparison must be constant on the complete possible cut support and extend through the adjoining real domain; this is a trial restriction, not a claim of physical equipotential. Geometry/material metric bounds and both matched field constructions are still open.

## Once-only cost and test boundary

The possible future tested assembly contains both isolated pads, both pad-side shoulders, both full collars, the actual contacts/crimps and the entire selected wire. Each collar is included in that assembled test domain once; its separate axial estimate must not be added again. The reference prism calculation at the proposed worst resistivity 0.000023 Ω·mm gives 1.582011 mΩ per neck. This is only a straight homogeneous reference diagnostic, not a manufactured-class upper bound or a whole-branch result.

JL's PCB-side flare, dogleg, new barrel, annular transfer and In1 spreading lie outside that tested domain and require separate finite current/potential energy bounds. K's flare and F.Cu spreading likewise remain paid. The other branch/K copper remains in the common network. The original combined 0.5 mΩ common requirement, GH 0.5 A/contact, rail 1 mΩ, distribution 20 mV and full-path 0.20 V requirements are unchanged. Parallel paths require a joined network proof; equal sharing cannot be assumed.

**No qualifying harness certificate exists.** Every excitation ampere must cross both selected collars, with no other electrical ports or unmodelled internal interface energy. Other GH AGND pins, other harnesses, board planes and main wires create bypasses in the installed system. A whole-board `V/I_total` cannot certify this conductor. The fixture must isolate the selected path or provide an independently valid local power certificate. A detached fixture test does not automatically certify later remated contacts: temperature/current/contact-state coverage, fixture power, instrument terminals and test-to-installed process applicability remain open. No catalogue contact maximum is promoted to this assembled-domain certificate.

The next constructive step is a bounded native reconstruction of these exact named retirements, zone clips and source copper/mask unions, followed by refill, local and whole-board connectivity/DRC, and full-section extraction under the pinned oracle. It must verify the PCB-side landing and preserve all fixed pads, obstacle copper and nets. Only then can this pair supply actual cut geometry to an isolated-assembly fixture/process design and a matched access-energy proof. This proposal supplies neither that reconstruction nor electrical/hardware acceptance.

## Source-owned K native priority correction

The first native realization is retained in `foil-collar-native-receipt.json` as a rejected historical experiment. Its K collar and F.Cu AGND landing both used priority 0, causing a real `zones_intersect` error. The source now specifies K collar priority **1**, with retained landing priority **0**. The compiler rejects equal priorities for a same-face landing, and the native constructor checks the actual target priority before applying the owned value. JL's explicit planned priority remains 0; its historical candidate is neither refilled nor rebound to this revised proposal hash.

K's declared native scope is `full_refill_draft_epoch`. A native rule/connectivity result may pass while the historical local-only criterion remains failed. This does not suppress any KiCad rule or admit a material class, electrical model or physical build. Every refilled copper change belongs to the new K artifact, and fresh whole-geometry electrical witnesses remain required. All dimensions, fixed hardware, source copper allowances and original electrical limits are unchanged by this priority correction.

## JL frozen-source replay

JL now also declares `full_refill_draft_epoch` before a new native run. The
historical local-only delta failure and failed in-flight source-stability check
remain in `foil-collar-native-receipt.json`; neither is relabelled as passing.
The new run must freeze its source inputs and check the entire refilled board,
including nonlocal copper changes, complete connectivity and the full untrimmed
dry section. This scope change makes no dimensional, net, clearance, priority
or electrical-limit change. The completed source-stable native result is
recorded separately in `foil-collar-jl-replay-receipt.json` and its Markdown
companion. Its rule/connectivity scope passes; its local-only, electrical and
physical admission do not.

The historical K receipt keeps its original global proposal hash. K-local
construction is unchanged, but no K replay or rebinding is implied by this
JL-only continuation. Fresh electrical witnesses remain required for each
candidate's complete geometry, and no physical or material admission follows
from a passing native rule/connectivity result.
