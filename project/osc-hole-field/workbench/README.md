# R21 workbench

This is the updated R20 grid, not a new panel. Open index.html locally. Both SLEW pots occupy the formerly empty cells; every old port/control record is unchanged. All 2D/3D dimensions remain proposals pending mechanical qualification.

Rebuild: `python3 scripts/prepare_data.py`, `python3 scripts/build.py`, `node scripts/render_static.cjs`, `python3 scripts/export_proofs.py`. Check: `python3 scripts/validate.py`, `node scripts/test_logic.cjs`, `node scripts/test_slew.cjs`. Browser: `xvfb-run -a python3 scripts/test_browser.py` with Playwright and Chromium installed. CairoSVG/Pillow/PyMuPDF are needed for raster/PDF proofs; no documentation runtime is needed for the standalone preview.

The SLEW simulation is an ideal RC lag, not a LF398 model, circuit simulator or firmware. Paper drawings are ergonomic references, never machining drawings. Doc-system integration and the current engineering queues are in the parent project handoff.

Authority cautions: `layout/placements-review.csv` is a stale 322-row review with no SLEW pots, and `reference/panel.json` is R17 geometry. Neither file is an authority.

The strict site link check allowlists the literal JavaScript template href `${esc(x.url)}` in `assets/osc-hole-field/workbench.html` (currently line 245) through `scripts/checks/check-site-links-allowlist.txt`. After regenerating the workbench, rerun the link check and update the allowlist key if the generated file or line changes.
