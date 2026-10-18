# Whole-instrument layered layout proposal

Owner-requested extension of the preserved [historical A01 viewer](../structure-review/README.md). Source baseline `367f0b12b17c720e2aa9f40b23659d551abeceb8`; the independent [GH4 coupon plan](../gh4-coupon-plan/README.md) remains separate. PR287 remains draft. Nothing here modifies canonical CAD, fixed hardware, parent PR286 or earlier studies.

## Open the viewer

Download [osc-structure-review.html](osc-structure-review.html) using GitHub **Download raw file**, retain the `.html` extension, and open it locally. GitHub's source page cannot run it. All Three.js modules/data are embedded; no server/CDN/network needed. Browser WebGL must be available. Corporate browser policies can block local files; use an approved browser/environment, not policy workarounds.

[Whole assembly](whole.png) · [Exploded](exploded.png) · [Side stack](side-stack.png) · [Panel](panel.png) · [A01 focus](a01-context.png).

Use Whole assembly, Side stack, Exploded, Panel only and individual layer toggles. Pick a block from the selector or coverage table. Front-facing/rear-facing buttons inspect opposite geometric faces, not KiCad copper side assignments. PanelXY and rear views keep x-right/y-down; opposite front view mirrors x. Drag to orbit, wheel to zoom; hover for exact identity/status. Save PNG exports the canvas. Focus shows that block's geometry but cannot prove isolation from hidden neighbors: always restore All33 for context. Labels show panel/rear in whole view to reduce clutter; focusing shows other-layer labels too.

## Coverage and geometry provenance

All **33 functional blocks** from `project/osc-hole-field/block-contracts.json` have coverage-table rows and board allocation envelopes: O1–O5, F1–F3, M5A/B, M4A/B, W1/W2, E1–E6, A01–A06, B1/B2, H1/H2, X1/X2 and N1. These are function IDs, not a newly adopted board count. All438 complete locked placement records are retained unchanged:180jacks,144controls,114LEDs. Marker diameters remain illustrative; this is not a drill drawing. `view-data.json` binds every input with SHA256.

| Representation | Meaning |
| --- | --- |
| White/colored panel markers | Fixed source XY coordinates; no hardware movement |
| Green solid A01 envelopes | Exact retained outer-envelope XY/z from previous viewer / Stage10, including LED substrate; still unadopted source study, not exact populated solids |
| Amber wireframe, layer-color tint | **New conceptual** envelopes for32 other blocks; no source-qualified outline, component fit or routed capacity |
| Red crosses | Centres of197 nominal same-layer box-overlap pairs; unresolved proposed conflicts, not a complete collision analysis |
| Optional grey10outlines | Actual incumbent partition polygons, sign-converted from negative-front depth convention; historical context, not adopted replacements |
| Coverage/shared-service text | Explicit unknowns without invented physical hosting |

Concept rule: each block's jack/control/LED/selector group gets its fixed-point bounding rectangle plus6mm in every XY direction. Middle/rear use the entire block's fixed panel projection plus6mm. This deliberately exposes overlap; **it is not a packing solution or a claim that narrow function strips can contain their circuits**. Width, clearance, pad allowance, thermal capacity, stiffness and routing have not been established. No A01 circuit replication into A02–A06 occurs. The161envelopes are review objects, not161approved PCBs. Existing A01 envelopes override the concept rule and remain visibly larger; A01 control retains its out-of-panel extension.

New conceptual depth/thickness allocations: LED4.2, control10, jack35, middle48.4, rear69.2mm, thickness1.6mm. Selector16/29mm retains the earlier3+2depth idea, but the new rectangular selector proxies do not establish exact adapters. Depths are review proposals borrowed from current/earlier studies, not newly qualified seated datums or permission to alter hardware. The z105 cover is a plane, not an enclosure solid. Exploded offsets are presentation only; cover and historical outlines are hidden while exploded. No length/service conclusion may be drawn from those display offsets.

Shared +12V/−12V/+5V/AGND and oscillator reference/octave services remain explicitly listed from the source ledger. Source/inlet/protection, shared physical hosting, all package population, inter-board connections, access notches, supports and complete service corridors are unknown. The old viewer retains R33 paths/carrier context; this whole instrument view intentionally does not invent their replication. J-SIG cover conflict, registration, independent support handoff and removal remain unresolved. Unmarked or transparent space is unknown/occupied for feasibility decisions; this visualization never clears it.

## Verification and next decision

Source tests check exact fixed records, all33function coverage, each block's middle/rear allocation, unchanged A01 envelopes, complete incumbent polygon/sign conversion, input hashes and overlap block identity. Browser tests check offline rendering, orientation, focus, all layer controls, explode, historical toggle and PNG download; their output defaults to `/tmp/osc-whole-layout-render` for read-only reruns. See REVIEW.md and render-checks.json for results/first failures.

Next review: select a family or grouping to replace its projection envelopes with a dimensioned allocation based on package/connector/access requirements, while preserving panel positions. The197overlaps make this a layout discussion, not a recommendation to fabricate. Native KiCad, ERC/DRC, copper, fabrication outputs, physical fit, electrical testing, supplier upload, deployment and ordering are NOT RUN / not authorized by this viewer task.
