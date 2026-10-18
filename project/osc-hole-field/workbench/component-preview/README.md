# Current panel component preview

Open `index.html` in a browser with WebGL2. It is self-contained and makes no runtime network requests. Front, Back, Orbit and Pot detail are camera presets; drag to orbit, wheel to zoom, right-drag to pan. Click a component for the current electrical identity, retained mechanical label and model limitations. Panel, components and component categories have independent visibility controls. The diameter comparison remains visible with capless pots selected.

This is a source-only appearance study, not native KiCad rendering, collision analysis or hardware qualification. All 438 centres come from `design/grid/placements.lock.json`; no lock, carrier, reservation, circuit or manufacturing geometry is changed. Artwork comes from the retained current-panel SVG. The 2 mm panel thickness is the existing project choice, not a measured panel. Wiring, rear boards, carriers, tools and service envelopes are omitted/unknown, **not free space**.

## Pot identity and appearance

Current circuit bindings select 101 Bourns pots: PTV09A-4020F-B103 (10 kΩ linear) ×51, PTV09A-4020F-B104 (100 kΩ linear) ×48, PTV09A-4020F-B504 (500 kΩ linear) ×2. The mechanical lock's 99 B103 / 2 B504 labels are retained mechanical references; both viewers obtain electrical identities directly from `scripts.panel.audit_current.circuit_bindings()`. No resistance redesign occurs.

Bourns PTV09 revision 01/25, physical PDF page 1, PTV09A-4 and F-Type drawings: Ø6 +0/−0.1 mm flat insulated shaft; L20 ±0.5 mm is measured from the drawing's mounting datum, not panel protrusion. Flat dimension 4.5 mm and flat length F7 mm apply to L20. The datasheet bytes inspected SHA256 `411cdb6a62e61f9c5bc2df76ed64ee21d7bcfbee035c1ba36beff08c43f28558` match retained B103 source evidence. Source: https://www.bourns.com/docs/product-datasheets/ptv09.pdf?sfvrsn=5e1089f1_14 . Bourns lists the shaft as plastic at https://bourns.com/products/trimpot-trimming-potentiometers/details/commercial-panel-controls/ptv09 ; polymer grade is unestablished here. Colors and pointer poses are illustrative.

Continuous pots default to capless shafts. Optional Ø8/10/12 mm cylinders illustrate diameter only; no cap MPN, bore fit, material, retention or supplier is selected. The five OCT controls are **SRBV160803 rotary selectors**, with the already documented custom draft OSC-KNOB-8-R1 Ø8 cap. They are not sliders and not the continuous pots. Existing O2/O4 13 mm extensions remain unqualified drafts.

## Provenance and transforms

Original STEP files are retained unmodified in `models/`, with their derived triangulations in `models/meshes.json`. See `models/receipt.json` for hashes, acquisition URLs, versions and checks. No supplier account or access restriction was bypassed.

- **Pot:** Devrin Talen's drawing-derived PTV09A-4F L20 model, KiCad library commit `cef48f63464c8ba65c189c679e9e02198b186372`; contributor MR1330, not manufacturer CAD and not an assertion that the MR is merged. Common exterior package is reused for B103/B104/B504; resistance internals are not modeled. Original model bounds (mm) x −0.153940…12.496060, y −3.2…8.105791, z −3.81…19.99. Cylindrical shaft radius 3 mm, axis x=6.9960603727775, y=2.5, z directed outward. Transform to local viewer mm: `(x−6.9960603727775, y−2.5, z−9.89)`, determinant +1; local +Y is panel-up. Shaft base z=7.89 becomes panel rear z=−2; tip z=19.99 becomes +10.10. **This seating assumption is not established by an actual carrier or PCB.** Original model's approximately 0.01 mm datum offset is retained. Brown body / green shaft shading divides original triangles at z=7.89; it does not claim exact material boundaries or native source colors.
- **Jack:** Jolin WQP518MA Thonkiconn STEP, third-party CAD under CC BY 4.0. Five solids; bounds x −5.25…6.987161, y −3.403102…14.4, z −4.5…4.5 mm. Main body measures 10.5×10×9 mm in source axes. Transform `(x−0.8, −z, y−12)` is a proper rotation and translation; socket axis x=0.8,z=0 aligns with the locked centre. Body front y=10 becomes z=−2 and nose y=14.4 becomes +2.4. Seating and actual nut engagement remain unknown; no nut is included. We measured the imported model, not a physical jack; complete drawing/pin matching is not claimed.
- **Selectors:** `design/mechanical/selector-assembly.json` supplies body 16.2×18.5×7.5, bushing Ø9, shaft Ø6 and existing PCB z=−16/−29. Body is an envelope, shaft rendered round (flat omitted). Custom cap and extension are display envelopes, not exact manufacturable solids. Existing rotations 0/180 are retained. Terminal tails, detailed retention and adapter PCB are omitted.
- **Toggle:** clearly marked visual substitute: illustrative 7×13×9 body, Ø2.4 lever; no exact vendor CAD or fit claim.
- **Button:** visual substitute for Omron B3F-1020, nominal 6×6 body; actuator and seating are illustrative.
- **LEDs:** locked window diameter with illustrative unlit lens; package and leads omitted.

World coordinates are mm: `X=locked x−159`, `Y=149−locked y`, panel front Z=0, positive Z toward user. Component local frames use proper rotations; locked `rot_deg` is applied with negative angle about world Z. Pot/jack seating poses and drawing envelopes must not be copied into canonical CAD as verified mounting geometry.

## Reproduce

From repository root:

```
python project/osc-hole-field/workbench/component-preview/build.py --check
node project/osc-hole-field/workbench/current-editor/build.cjs --check
python -m unittest scripts.panel.test_component_preview
```

Normal build consumes retained meshes and needs Python stdlib only. Optional derivative regeneration uses CadQuery 2.7.0 / OCP 7.8.1.1: `python project/osc-hole-field/workbench/component-preview/tessellate.py`, tolerance 0.08 mm / angular tolerance 0.15 radians. This is STEP import/tessellation, not native KiCad regeneration. Never overwrite receipts to conceal an unexpected derivative change.

Run each browser suite through the repository heavy guard, in normal and optimized Python:
`python [or python -O] project/osc-hole-field/workbench/component-preview/test_browser.py` and `python [or python -O] project/osc-hole-field/workbench/current-editor/test_browser.py`.
These files are outside the default scripts/design Python discovery, so must be invoked explicitly. Screenshots are regenerated by the browser suites. See `VERIFICATION.md` for actual commands/results and first failures.

## Remaining physical inputs

Measure actual panel thickness, pot mounting datum-to-panel and tip protrusion, jack body-face-to-panel/nut engagement, shaft flat orientation and carrier constraints. Confirm exact bought part markings, especially the 48 B104 controls. For cap options, an owner selection plus actual bore/flat/retention and neighboring-finger clearance measurements are required. No visual overlap result here qualifies assembly, service removal, flex radius or retention stiffness. Keep the earlier Stage35/36 measurements and unresolved decisions separate from this appearance study.
