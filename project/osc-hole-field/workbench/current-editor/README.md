# Current panel appearance editor

Open **[index.html](index.html)** after downloading it with GitHub's **Download raw file** action. Keep the `.html` extension and open it in a desktop browser. This single file includes the current source data, audited renderer and owner graphic library. It needs no server, network, installation or adjacent files. GitHub's source page does not run the editor.

If serving the checkout locally is preferred, from the repository root:

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory project/osc-hole-field/workbench
```

Open `http://127.0.0.1:8765/current-editor/`. The original historical R21 workbench remains at `/index.html`; it is preserved and is not the current geometry-locked editor.

## Use

- Change module/control/jack/switch text sizes, font, separator clearance or line weight. Click printed text (or choose it in the label menu), then adjust that label's horizontal/vertical offset. Label meaning is not editable here.
- Scroll the left sidebar for white/gold visibility and colors, existing owner heading ornaments by module family, relationship lines and LED line/bracket ornaments. No new artwork replaces the owner's originals.
- **Full panel** fits the panel; **Selected detail** centers the chosen label at 300%. Drag the canvas to pan. Use +/−, Ctrl/⌘+wheel, or focus the canvas and use arrow keys/+ /− /0. This moves the view, never a component.
- **Save settings** downloads versioned appearance JSON. **Load settings** accepts only this schema and matching geometry revision. There is no silent browser storage. Save before closing. **Reset baseline** restores the audited current appearance and full view.
- **Export SVG** produces a deterministic full-panel preview with embedded appearance settings and source hashes, independent of zoom/pan/selection. **Export PNG** rasterizes that same artwork at 5 or 10 px/mm (1590×1490 or 3180×2980). Save JSON alongside PNG; PNG has no settings payload. Pixel output is reproducible within the same browser/font environment, not guaranteed across operating systems.

Settings schema: `zudo-current-panel-appearance-v1`. Geometry revision binds both the placements lock and panel parameters (including LED window diameter). Geometry, pitch, component IDs, positions, hole sizes, arbitrary text/SVG, unsupported fields and historical R21 presets are rejected. Invalid imports leave the current appearance intact.

All **438 features** stay fixed: 180 jacks, 144 controls and 114 LED windows. The five OCT cutouts retain the audited Ø7 mm diameter. Current switch text is 1.0 mm and separator clearance 2.5 mm at reset. The editor reuses `../src/render.js`, `../layout/grid.json`, `../reference/icons.json`, the current `scripts/panel/art_profile.cjs` and the canonical placements lock/panel parameters. Build-time checks reject renderer/lock drift. No historical source renderer, grid, original workbench page or proof was changed.

This is an **appearance preview, not manufacturing output**. Grey discs represent undrilled LED windows. Text size/offset trials can overlap other ink or apertures; inspect them visually. Font metrics and strokes differ from native KiCad artwork, including three long-label native offsets. Exports do not regenerate boards, Gerbers or any manufacturing files. No mechanical or circuit validation is implied.

## Rebuild and verify

```bash
node project/osc-hole-field/workbench/current-editor/build.cjs
node project/osc-hole-field/workbench/current-editor/build.cjs --check
python3 scripts/panel/audit_current.py --check
node scripts/panel/test_current_art.cjs
```

Browser tests use installed Chromium and Python Playwright. Run through the environment's heavy guard as documented in [VERIFICATION.md](VERIFICATION.md). They load the complete document without external requests, verify all locked features, reject malformed/imported geometry, exercise save/load and pan/detail, and compare exported SVG/PNG output. No new dependency installation is required in this Cloud environment.

[Full UI screenshot](editor-full.png) · [Detail and lower appearance controls](editor-detail.png) · [Verification and independent review](VERIFICATION.md).

## Assembled hardware preview (owner feedback)

Hardware is visible by default at every fixed feature:180 jacks,101 knobs,30 toggle switches,5 rotary selectors,8 pushbuttons and114 LED windows. Overall Hardware and Jacks/Knobs/Switches/LEDs toggles preserve a holes-only view. Preferences, including export mode, are saved in the same geometry-bound JSON; existing v1 presets without those fields load with defaults. No automatic local storage or network is used.

Choose **Clean artwork (no hardware)**, the default export mode, or **Assembled preview (visible hardware)** before SVG/PNG export. Clean artwork retains the existing fixed-aperture preview, so it is still not a manufacturing silk file. Assembled exports honor all visibility toggles and include explicit mode metadata and filenames. Neither mode modifies the artwork generator or canonical manufacturing output.

The existing locked component identities distinguish toggle (Dailywell2MS), rotary (ALPS SRBV), button (Omron B3F), pot (Bourns PTV) and jack (Qingpu) types. The existing workbench supplies the visual vocabulary and trial Ø8.3 jack-nut, Ø8 rotary cap, Ø8.08 toggle-nut and Ø5 button envelopes. New Ø12 knob caps are **illustrative**, replacing the old6mm shaft-like view. Exact selected caps, jack nuts and lever appearance are not established; these drawings are not component CAD or a fit claim. Pointer/lever poses are illustrative, not functional states or shaft-indexing instructions. LED illustrations use the locked window diameter, unlit colors and no electrical/brightness simulation. Hardware never changes centres, hole diameters or label semantics.

A conservative label-bounding-box overlap count appears below the canvas; hover it for affected label text. At baseline the illustrative12mm caps obscure portions of several control labels (111 text bounds intersect hardware overall). This is intentionally visible for judging cap size/label placement, not hidden by painting labels above knobs. Use Selected label or hide hardware to edit obscured ink. Window/LED clearance and accurate assembled hardware fit remain unresolved; the screen is not a mechanical collision test.

## Capless pot appearance correction

Continuous pots now default to the Ø6 mm F-type insulated shaft. Optional Ø8/10/12 mm caps are explicitly illustrative; no cap MPN is selected. OCT retains the existing Ø8 custom draft cap. The flat is 4.5 mm across the remaining shaft section; its displayed angle is illustrative. Electrical identities are resolved from current circuit bindings (51 B103 / 48 B104 / 2 B504), while all mechanical lock labels and 438 centres remain unchanged. Old v1 settings without potAppearance load with the capless default. Clean artwork exports still omit hardware. See ../component-preview/README.md for the independently sourced STEP preview and detailed source limits.
