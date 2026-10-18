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
