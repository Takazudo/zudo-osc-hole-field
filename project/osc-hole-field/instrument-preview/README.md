# OSC instrument preview

`index.html` is a self-contained, offline 3D preview of the current OSC instrument: the panel and all ten native board drafts at their true depths. It is published unchanged as `doc/public/assets/osc-hole-field/instrument-3d.html`. It makes no network request; Three.js r180 and OrbitControls are inlined from `../workbench/vendor/` (MIT, `THREE-LICENSE.txt`).

**Status.** Every board is an unvalidated draft. Routing is incomplete on K, JL and JR. Component body heights are illustrative display values. This is **not a native KiCad render: KiCad render NOT RUN**, because the pinned KiCad 10.0.6 oracle needs Docker, which is unavailable in the cloud container where this preview was built. Nothing in the page is fit, clearance, electrical or manufacturing evidence. No board, grid, partition, schematic, symbol or footprint file is written by these scripts.

## Sources

`extract.py` records the SHA-256 and size of every input in `view-data.json`. `build.py` refuses to build, and `--check` fails, when any of those files has changed since extraction.

| Input | Use |
| --- | --- |
| `boards/osc-stage-optical`, `osc-jack-left`, `osc-jack-right`, `osc-core`, `osc-octave-1`…`5` `.kicad_pcb` | Edge.Cuts outline, NPTH apertures, footprints, tracks, vias, pads and zone fills |
| `boards/osc-control/osc-control-routed-draft.kicad_pcb` | P (see below) |
| `boards/panel/panel.kicad_pcb` | 438 panel features, checked against the lock |
| `design/grid/placements.lock.json` | 438 fixed centres, panel holes, mesh positions |
| `design/partition/partition.json` | F.Cu plane z, thickness, board keys, roles, enclosure proposal |
| `circuit/routing/osc-pcb-current-checkpoint.json` | K/JL/JR labels, open-edge breakdown and epoch trail, successor hashes |
| `design/reports/instrument-readiness.json` | board selection, adoption state, open edges for EL, P and O1–O5 |
| `design/panel/current-audit/current-panel.svg`, `design/panel/panel-params.json`, `design/mechanical/selector-assembly.json` | panel artwork texture, LED window diameter, selector instances |
| `../workbench/component-preview/models/meshes.json` | pot and jack meshes (attribution in `../workbench/component-preview/models/ATTRIBUTION.md`) |

**Which P file.** `osc-control-routed-draft.kicad_pcb` is the current P record. `design/reports/instrument-readiness.json` binds it as unit P (adoption: "candidate; RV601 edge tab not adopted into canonical partition", 0 complete native open edges) and lists `osc-control-layout.kicad_pcb` under `excluded_board_files`. The verification page `doc/src/content/docs/verification/osc-pcb-control.mdx` describes the routed draft (4,140 segments, 527 vias). The layout file has no copper and is the placement input. PR #339 changed only the oracle binding of the P checks and touched no board file. The UI labels P "routed draft".

Excluded: `boards/osc-jack/` (historical single jack board), `boards/fixture-jacks/` (fixture) and the P layout file.

## Coordinates

Every footprint in the ten boards carries `FootprintOriginMm`. The difference between the footprint position and this property is the same for every footprint on every board: **(100, 50) mm**. The panel board has no such property; its Edge.Cuts origin is at (100, 50) as well.

- Panel frame: `x = x_kicad − 100`, `y = y_kicad − 50` (mm, y down). This is a pure translation. There is no mirror: F.Cu faces the panel, and the viewer looks at the panel front from +Z, which is the side KiCad shows by default.
- World: `X = x − 159`, `Y = 149 − y`, `Z = 0` at the panel front with +Z toward the viewer. This matches the component preview.
- Board planes: F.Cu at the partition's `face_z_mm` (EL −4.2, JL/JR −10, P −11.8, O1/O3/O5 −16, O2/O4 −29, K −100), B.Cu at `face_z_mm − thickness`, inner layers spaced evenly between them. F-side bodies extend toward the panel (+Z), B-side bodies toward the rear.
- Footprint rotation: KiCad's counter-clockwise angle (y down) becomes a positive rotation about world +Z.

**Proof.** `test_extract.py` asserts that all 438 footprints with a `PanelUid` (JL 143, JR 139, P 139, EL 12, O1–O5 one each) land on their locked centres within 0.01 mm with matching rotation, and that each locked centre is claimed exactly once. The measured maximum deviation is 0.000 mm. It also asserts that each board's Edge.Cuts bounding box equals its partition outline bounding box, and that the panel board's 438 features equal the lock.

## Rendering

- **Copper.** Each copper layer is rasterized into a 1-bit PNG from its tracks, vias (over their layer span), pads (rect, round-rect drawn as rect, circle, oval, custom primitive polygons) and zone `filled_polygon`s, with drill holes cleared: K 12 px/mm, JL/JR 14, P 12, EL 16, O1–O5 24. The viewer uploads each one as a single-channel texture. Zone fills are present in every board file and are drawn. Silkscreen, solder mask and thermal-relief detail beyond the stored fills are omitted.
- **Bodies.** One instanced box per footprint, sized from the courtyard bounding box (fallback fab, then pads), on the footprint's real side. Heights come from a package-family table in `extract.py`; they are **illustrative**. NPTH-only support and service footprints are cut from the board instead of drawn.
- **Panel hardware.** Pots and jacks use the retained third-party meshes at their locked centres, with the component preview's transforms and its **panel-referenced seating assumption** (pot shaft base at the panel rear, jack body face at z −2). That seating comes from no carrier or PCB datum; jack seating is UNSOURCED in the partition. Any visual overlap or gap between a mesh and a board plane is not a fit or clearance result. Toggle levers, button plungers and selector shafts and caps are simple cylinders.
- **Enclosure.** Drawn as a dashed ghost from `partition.json` `enclosure` (inner 322 × 302 mm, inner rear −120 mm), labelled as a proposal with no case selected.
- **Routing meter.** The checkpoint records open edges per epoch, not a total, so the board card shows the recorded counts (K 3,409 → 3,363 → 2,518 → 2,226; JL 268 → 184; JR 312 → 192) and no percentage. The K1402/JL117/JR130 epoch belongs to a different design and is left out.

## UI

Assembled, Exploded (continuous slider), X-ray and Focus modes; per-board layer peel and layer toggles in the board card; search by reference, value, MPN or panel UID; click or tap a body for its identity; a six-step guided tour; a Sources drawer with input hashes and licences. `window.__preview` exposes `ready`, `setMode`, `focusBoard`, `select`, `find`, `setExplode`, `setPeel`, `view`, `startTour`, `stopTour`, `idle`, `state`, `screenOf` and `partWorld` for tests.

## Reproduce

From the repository root (Python 3 with Pillow; Node 22+ with Playwright for the browser test):

```
python3 project/osc-hole-field/instrument-preview/extract.py          # about 2.5 min; writes view-data.json and data/*.png
python3 project/osc-hole-field/instrument-preview/build.py            # writes index.html and the published copy
python3 project/osc-hole-field/instrument-preview/extract.py --check  # fails if the view data is stale
python3 project/osc-hole-field/instrument-preview/build.py --check    # fails if inputs or either HTML file are stale
python3 -m unittest project/osc-hole-field/instrument-preview/test_extract.py
node project/osc-hole-field/instrument-preview/test_browser.mjs [--publish]
```

`extract.py --base-commit <sha>` sets the commit shown in the status banner (default: `git rev-parse HEAD`). The browser test loads `index.html` from disk, requires zero console errors and no request other than the file itself (in-memory `blob:` and `data:` URLs excepted), drives every mode, checks picking, and saves screenshots to the system temp directory; `--publish` copies the four documentation screenshots to `doc/public/assets/osc-hole-field/instrument-3d-*.png`. Run it through the machine's heavy-run guard where one exists.

The page budget is 12,000,000 bytes; `build.py` fails above it.
