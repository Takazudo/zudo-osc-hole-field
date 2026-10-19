# GH4 JLCPCB submission candidate

Local candidate prepared 2026-10-18 from published native commit
`537ab6a60272437458f1bfe923ca361c8a2ed09e`. No upload or manufacturing release.
The original `../gh4-coupon-native/review-only/` is unchanged.

## Files and intended use

- `GH4-fabrication-candidate.zip`: nine original copper/mask/paste/silk/profile
  Gerbers, two original metric Excellon drill files, one new score-only GM2,
  fabrication PDF and fabrication notes. This is the fabrication upload candidate.
- `BOM.csv` and `CPL.csv`: assembly inputs, one J1 per board, supplier column names.
- `fabrication-drawing.pdf`: dimensioned construction and placement verification.
- `ORDER-SETTINGS.md`: proposed quote settings and upload-time gates.
- `evidence/`: native reports, original Gerber render, placement/netlist, package
  verification receipt, and PDF inspection images. Not fabrication layers.
- `SHA256SUMS.txt`: all deliverables except itself. The outer delivery ZIP has a
  separate SHA256 sidecar. `build_package.py` reproduces the initial geometry and
  drawing from the sibling native directory; `finalize_package.py` builds archives
  and manifests after review. Both use the already-installed Python dependencies.

## Coordinate and layer decisions

All original manufacturing artwork and drill bytes are retained. Native export
was KiCad CLI/pcbnew **10.0.6** using existing image
`kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`.
Native ERC: 0 errors/warnings; DRC: 0 violations/unconnected/parity issues.
These reports are carried forward, not newly rerun for CSV packaging.

Gerber/drill/CPL share absolute metric coordinates: outline X0..80, Y-100..0.
The drawing's top-view y increases downward, so manufacturing Y=-y. CPL values
are copied unchanged from KiCad: J1 X40, Y-50, rotation 0, top. Only CSV columns
change. Negative Y is not a defect to fix independently. The four signal pads
are X38.125/39.375/40.625/41.875 at Y-51.95, pin 1 left. MP lands are X36.275 and
43.725 at Y-48.6. The footprint datum is not the plastic body's geometric center
(X40, Y-49.625), nor a manufacturer-qualified nozzle pickup point. No speculative
centroid offset or supplier-library rotation correction is applied.

GM1 retains the four-segment closed outer contour. GM2 has exactly two straight
full-width score centerlines at Y-10 and Y-90; it is NOT copper, routing or slots.
The original text-bearing review V-cut Gerber is excluded from the fabrication
ZIP. GM2 recognition is an upload/CAM confirmation gate, not proven vendor behavior.
The empty bottom copper/paste/silk and empty PTH drill are intentional. There are
three diameter-2 NPTH holes; only J1's six lands have paste. Bare TP/fiducial/tooling
features are absent from BOM/CPL. No copper zones require refilling.

The original `.gbrjob` is deliberately excluded: it reports stroke-inclusive
80.1 x 100.1 dimensions and finish `None`, which do not define this order.
Profile centerlines define 80 x 100 and order settings specify lead-free HASL.

## Official requirements checked on 2026-10-18

- [JLC KiCad 10 BOM/CPL guide](https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad),
  updated 2026-09-09: use supplier CSV headers, mm, native placement column mapping.
- [JLC KiCad Gerber/drill guide](https://jlcpcb.com/help/article/how-to-generate-gerber-and-drill-files-in-kicad-9),
  updated 2026-09-24: closed profile; copper/mask/silk plus paste for assembly;
  metric absolute Excellon; Protel filenames and ZIP packaging.
- [JLC panelization guide](https://jlcpcb.com/help/article/pcb-panelization):
  straight full-span scores, minimum 70 x 70 panel and Standard Assembly for V-cuts.

Those requirements support these file choices; they do not certify automatic
GM2 recognition or the C161692 library datum. Exact part availability, current
quote restrictions and supplier interpretation remain upload-time checks.
The [older KiCad 7 guide](https://jlcpcb.com/help/article/how-to-generate-gerber-and-drill-files-in-kicad-7)
asks users to check V-cut lines in GM1. Separate GM2 is this project's explicit
choice to distinguish scores from the closed routed perimeter, not a documented
JLC-prescribed filename convention. Supplier CAM must resolve that interpretation.

## Checks, commands and limitations

Before writing, WSL `git status --short` was clean; `git rev-parse HEAD` and
`git ls-remote https://github.com/Takazudo/zudo-osc-hole-field.git refs/heads/agent/278-stage28-din-harness-20261017`
both returned `537ab6a60272437458f1bfe923ca361c8a2ed09e`.
Source repository validation passed via existing Node 22.22.2:
`node node_modules/@takazudo/zudo-circuit-doc/bin/zudo-circuit-doc.js validate`.

Packaging command: bundled Windows Python 3.12.14 `build_package.py`, followed by
`finalize_package.py`; reportlab creates the PDF, pypdfium2 5.14.0 renders both
pages for inspection. The PDF marker completed successfully once before authoring.
The receipt checks actual exported geometry, CSV, drill coordinates and hashes
every original native file before/after. The strict inherited Gerber parser only
supports this coupon's linear strokes and flashed apertures; it is not a complete
CAM engine. The source renderer is retained with an explicit original-review label.

Windows Git initially refused the WSL-owned clone as dubious ownership; used
WSL Git without changing global safe-directory settings. The first drawing render
showed the functional-size label overlapping J1; moved the label and re-rendered.
No toolchain installation, image pull, whole-project regeneration or new native
board edit occurred. No new commit/push is made by this packaging task.

Physical fit, soldering, continuity, isolation, grip/latch, bow and durability are
untested. No supplier approval, placed order or assembled hardware is claimed.
