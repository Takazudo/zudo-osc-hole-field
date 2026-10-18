# OSC whole-structure review

Source revision: 02e83bb6955d97958248946bd11d2e3f14014ad3, draft PR287. This directory is an additive, non-canonical review deliverable on draft PR287. The revision above is the geometry source, not the subsequent artifact commit. No deployment or order.

## Open the views

Open [osc-structure-review.html](osc-structure-review.html) on GitHub, use **Download raw file** (or right-click **Raw** → Save link as), preserve the `.html` extension, then open it in a browser that permits local HTML JavaScript/WebGL. It is self-contained and makes no network requests. A managed browser may block file navigation; the actual checks used Playwright set_content with system Chromium and software WebGL. This is a downloadable HTML, not a promised in-chat interactive attachment. [Whole-view PNG](current-whole.png) and [exploded PNG](current-exploded.png) show the actual rendered views. GitHub does not execute HTML in its source viewer; download the file first.

The original R21 workbench is `project/osc-hole-field/workbench/index.html` (standalone) and published-copy `doc/public/assets/osc-hole-field/workbench.html`. Documented URL: https://zudo-osc-hole-field.zudolab.dev/assets/osc-hole-field/workbench.html . Live availability could not be verified: this environment's network proxy returned 403; web lookup also failed. The local copy rendered successfully with no JS errors. It offers panel-hide, explode, camera controls and PNG export.

## Coverage and staleness

Historical R21 shows one large jack board, multiple control strips, a large core at z=-24 and a power pocket at z=-32 (its own display sign convention). It has 47 illustrative package allocations, including historical TL074 choices; this is not the present electrical selection or routed placement. Panel/grid remains relevant; the internal structure predates Issue278 front/middle/rear design. Do not interpret it as the current build.

The review HTML uses the existing Three.js/OrbitControls offline embedding approach. Fixed hardware centres come from placements.lock.json: 180 jacks, 144 controls, 114 LEDs. Marker radii are display choices, not new hardware dimensions. Panel is a zero-thickness reference; no new panel thickness is selected.

A01 board outer envelopes and carrier spans are retained Stage10 source data. These are still study proposals; holes/notches, detailed supports, power straps and population are omitted. The front control rectangle extends to y307 beyond the 298mm panel, exactly as retained; candidate enclosure requirement is 320x319x105mm. No enclosing shell origin, wall thickness or manufactured enclosure is invented.

J-SIG/J-PWR middle headers use the retained R33 rear-face study positions; the rear-face/reservation study was subsequently owner-approved for study only. It is not hardware adoption. Their ideal installed paths use retained 133/149mm design lengths and R12. Lines are sampled centreline graphics, not qualified cable solids or raw cut lengths. Their polyline approximation is about0.003355mm shorter than the analytic bend path; rendering does not recompute acceptance. Mated GH blocks use the inherited7.3mm study allowance. DIN is a union-XY mating-stack envelope between z50 and69.2, without contact numbering or an exact maker solid.

Earlier revision-2 O1-O5 card boxes are optional wireframes and off by default. They are not an integrated current layout, populated-board promise or clearance proof. Other front/middle/rear function outlines and routes remain incomplete. Empty areas are UNKNOWN, not free. No C36 cassette, RG34 guide or shortened cable is depicted as adopted. Retention/service/cover conflicts remain open.

Layer controls and exploded view are display tools; explode hides connectors, cables, carriers, cover and old card context so they cannot imply connected/service-feasible geometry at artificial offsets. Hover shows source/status labels. Panel XY looks from +z and preserves the locked x-right/y-down projection; it is not a front-face photograph. The first review caught a mirrored Panel preset; its viewing direction was corrected and a screen-coordinate regression added.

## Checks and limits

Existing R21 and final new HTML rendered in Chromium/WebGL with no JavaScript errors. Checked whole view, A01 close-up, layer visibility, optional historical context and exploded separation. New HTML requested no external network resources. Actual render receipts are historical-render.json and render-checks.json. Screenshots are synthetic geometry only.

Source inputs and SHA256 bindings are in view-data.json. Circuit:check passed before work; canonical and historical files remain unchanged. No KiCad/native regeneration, ERC/DRC, simulation, collision acceptance, physical validation, manufacturing, release/deploy or ordering.

Next choice: use the historical viewer for panel/control familiarity, or this bounded A01 view for current architecture discussion. A complete current internal instrument model requires separately supplied/approved outlines for the remaining functions; they should not be inferred from unused space. The separate physical-validation parts plan does not turn this preview into an ordering release.

## Reproduce from this checkout

Python3 builds from retained JSON and the already vendored Three.js/OrbitControls. No KiCad, Docker, Node build, CDN or package installation is needed for generation. The existing THREE-LICENSE.txt accompanies the embedded engine. No vendor manuals or credentials are included.

From the repository root:

```sh
python3 design/architecture-278/implementation/stage36/structure-review/extract.py
python3 design/architecture-278/implementation/stage36/structure-review/build.py
python3 design/architecture-278/implementation/stage36/structure-review/extract.py --check
python3 design/architecture-278/implementation/stage36/structure-review/build.py --check
python3 design/architecture-278/implementation/stage36/structure-review/check_review.py
```

The last command needs existing Python Playwright and system Chromium at `/usr/bin/chromium`. It writes screenshots and its receipt to `/tmp/osc-review-render` by default (override OSC_REVIEW_OUTPUT). It does not overwrite committed screenshots. This is a bounded render smoke, not an e2e or hardware suite. Run deterministic checks with `python3 -O` too. If source data changes, update the declared geometry revision and review coverage rather than silently regenerating a stale-revision label.

## Delivery history

The earlier local-only preview was not delivered to the owner. Library upload failed before preparation with HTTP401 from the hosted-apps tools listing; no Library IDs were created. `delivery.json` preserves that failure. No credential retry or access workaround was attempted. This repository artifact is the separately owner-authorized delivery route.
