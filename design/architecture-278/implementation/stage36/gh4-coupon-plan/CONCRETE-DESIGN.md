# GH4 unpowered coupon — concrete source design

2026-10-18; baseline5e39d5a265a27d8cbdb3385a10d32a27f37d5f10. **This is our design for later isolated CAD execution.** It supersedes the30mm/array alternatives and supplier-decision gates in earlier plan sections. JLC is the fabricator, not the project architect. No supplier enquiries, new licenses, native files, exports or orders. Whole-layout viewer unchanged.

## Chosen construction

One GH4 header per identical board; target two assembled endpoints. Two-layer FR4,1.6mm,1oz copper, green solder mask, lead-free HASL; Standard normal-paste assembly evaluation. Finished functional board80×80mm, top/bottom10mm process rails, overall80×100mm. One coupon per assembly unit; no tiny array. Provisional fabrication quantity5, assemble2 and retain3bare units, checked later against the actual quote rather than a custom supplier-design enquiry. Rails initially retained, avoiding manual snapping of an assembled sample. If later removed, locally support the board and inspect joints afterward; do not react rail removal through the header.

All coordinates are **top component view, upper-left of overall panel, x right/y down**, inmm. [design.json](design.json) is the machine-readable source, not fabrication data.

| Feature | Chosen value |
| --- | --- |
| Functional area | x0…80, y10…90 |
| Process rails / V-cut | y0…10 and90…100; full-width straight V-cut lines y10/y90, not internal Edge.Cuts slots |
| J1 | Exact JST BM04B-GHS-TBT(LF)(SN), JLC C161692, footprint origin(40,50), zero rotation; sole populated component |
| Fiducials | (5,5),(75,5),(5,95); copperØ1, mask openingØ2; no drill/paste; unconnected |
| Tooling holes | (15,5),(65,5),(15,95);Ø2 NPTH, no copper annulus |
| TP1–4 | (34,72),(38,72),(42,72),(46,72);Ø2 exposed copper, no paste; no BOM component |
| Electrical topology | Four isolated nets GH1…GH4, J1 pin n→TPn;0.25mm traces and chosen0.25mm net clearance; no planes, supply or inter-pin connection |
| Mechanical lands | Two MP lands soldered, no signal net; no electrical role or service-load rating assigned |
| Clamp zones | x2…10 and70…78, y30…70, both faces; copper/component-free; support underside near header with nonconductive bench support avoiding joints |
| Other copper / labels | At least1mm from outline/V-cuts; mark pin1, TP1–4, UNPOWERED SAMPLE, axes and revision; keep silk off mask openings |

Keep +/−y approaches and space above the header empty. Actual grip/latch dimensions are measured after receiving the generous coupon; they do not block this drafting step. Do not transfer measurements to the OSC enclosure without its separate obstacle/fixture analysis. No proof-load fixture or extra mechanism is designed here.

## Header geometry and orientation

[JST eGH](https://www.jst-mfg.com/product/pdf/eng/eGH.pdf), retained as `design/connectors/sources/jst-gh.pdf`, SHA256b1dcb317b6b9a4fbbedd2dbf42c64c95306a252d23de8933b85fcf161240b722, printed pages2/3, contains the top-entry land pattern and exact BM04 row. It supports this coupon without waiting for a separate toleranced product drawing. Body8.25×4.25×4.05; contact pitch1.25 and total contact span3.75mm. Catalog values remain reference dimensions, not measured parts.

[Maintained KiCad footprint pinned revision](https://gitlab.com/kicad/libraries/kicad-footprints/-/blob/f8a45b4665c28a6280e46eefe9fd4df81d2cd17b/Connector_JST.pretty/JST_GH_BM04B-GHS-TBT_1x04-1MP_P1.25mm_Vertical.kicad_mod), downloaded and inspected, SHA256c0e5c962366864b39ad3a295bb6419547e18f0f5ac49060d75ea51d0e7079732, cites eGH. Reuse only after byte/hash and native import checks. No file copied into canonical libraries. Existing repository3/7/8way assets and external mapping aids do not substitute for GH4.

| Land | Relative centre | Global centre | Size |
| --- | --- | --- | --- |
|1|−1.875,+1.95|38.125,51.95|0.60×1.70|
|2|−0.625,+1.95|39.375,51.95|0.60×1.70|
|3|+0.625,+1.95|40.625,51.95|0.60×1.70|
|4|+1.875,+1.95|41.875,51.95|0.60×1.70|
|MP left|−3.725,−1.40|36.275,48.60|1.00×2.80|
|MP right|+3.725,−1.40|43.725,48.60|1.00×2.80|

Footprint body x±4.125,y−2.50…+1.75 → global[35.875,47.50,44.125,51.75]. The footprint origin is near the body centre, not exactly its geometric centre (body centre y49.625). Pin1 is the leftmost signal pad in our component view. JST's illustrated mounting view has pin1 on the right with signal lands above: a180° planar rotation maps it to this orientation. Transform(x,y)→(−x,−y) has determinant+1; no mirror is introduced. Schematic pin mapping, top-side placement and this orientation must survive export/render review; supplier placement rotation must be verified in its preview rather than assumed from a zero-angle number.

## Requirements-to-design matrix

| Documented requirement / source | Our design | Verification | Remaining real gap |
| --- | --- | --- | --- |
| [Standard capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities):70×70minimum, rails/fiducials |80×80functional,80×100overall | Both dimensions exceed minimum even before rails | Actual quote/stock later, not missing board architecture |
| [Edge rails/fiducials](https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order):≥5mm rails,Ø1copper/Ø2mask,3–4marks,3.35mm edge clearance including mark area |10mmrails,3asymmetric marks;Ø2clear zone |5mm centre distance →4mm clear-zone-to-edge/V-cut, greater than3.35 | Native mask/clearance verification |
| [Process edges/tooling](https://jlcpcb.com/help/article/specifications-for-adding-process-edges-and-positioning-holes): recommendsØ2tooling,1mmmarks,3.85mmmark offset |Ø2NPTH;mark centres5mmfromouteredges | Tooling hole edge4mmfromrail edges; marks and holes separated by≥10mmcentres | Native drill/copper separation |
| [Panelization](https://jlcpcb.com/help/article/pcb-panelization): straight full-panel V-cuts,≥70mm overall | Two full-width cuts at10/90, no array |80mmcut span,80mmcut separation; no part/copper crossing | Later fabrication-layer interpretation/render |
| J1 catalog/pinned footprint | Exact6lands,4signal nets,2mechanical pads | Pitch/span/size/view transform independently checked; native DRC later | Native import and physical solder inspection |
| [Assembly terms](https://jlcpcb.com/help/article/terms-and-conditions-of-jlcpcb-assembly-service): component body≥2.5mmfromedge | Body nearest functional edge35.875mm | Source arithmetic plus later native rule | No generic IPC density qualification inferred from library import |
| Own conservative routing/support choice |0.25trace/clearance,1mmedge/V-cut,sideclampzones | Source land gap0.65mm; later native net/clearance and keepout tests | No completed routing or structural strength claim |
| Owner manuals J2/J3; see [inventory](SOURCE-INVENTORY.md) | Distributed insertion, fully released latch, full-row broad-face grip,≤15°study angle | Receipt observation worksheet | Actual grip, bow and durability remain unmeasured; not drafting blockers |

## Thermal decision

CHM-1-2149rev2p4 recommends a housing-surface curve peaking250+5/0°C,230°Cband30±10s and150–180°C for60–120s, depending on solder paste and evaluation. **250°C is not a mandatory minimum assembly temperature.** It also recommends0.12–0.15mm stencil with pad-sized apertures; thicker stencils require paste-volume adjustment. Preserve these conditions as process-reference evidence.

Choose published Standard normal240±5°C as the **reasonable evaluation process** for this unpowered coupon, not a completed production qualification. Published oven/process figures are not a measured housing profile, and we do not invent one. No bespoke per-job optimization/certification prerequisite: JLC's assembly terms state its line cannot be optimized for each order. Our tasks are correct lands, paste/mask export review, placement review and receipt inspection. If available assembly settings conflict with documented component constraints, stop/reconcile; never silently relax them. Economic255±5°C and medium/low paste remain unselected. Keep lower-temperature joint-strength warning as history, not an arbitrary substitute.

## Execution and acceptance

Source choices are complete enough for the next isolated native step. Separate product-drawing access, measured fingers or supplier architecture advice are not prerequisites. Use the [native handoff](NATIVE-HANDOFF.md), pinned footprint and design.json. Native ERC/DRC, pinmap, export and placement reviews remain necessary and NOT RUN here. Five fabricated/two assembled is a quote-stage quantity; C161692 stock/price is checked then, with separate housing/precrimped lead procurement. No order authority follows.

On receipt, record part/lot/orientation, inspect four contact joints and both hold-down joints, check TP mapping and all six pairwise net-isolation combinations with a low-energy meter before handling, then repeat after gentle handling. Meter settings/lead resistance are recorded; reject missing joints, bridges, unexpected open/short or visible damage. No power supply attached. Numeric resistance acceptance needs the actual meter/contact baseline; do not invent it. Mechanical-pad isolation from signal nets is checked, not assumed from no-net assignment. Keep receipt failures; no whole-instrument current, retention or service guarantee.
