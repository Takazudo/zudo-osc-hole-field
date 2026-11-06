# Verification receipt

Baseline51aa218dc5eb17c22fd13531e04c115da87c8520; only this new candidate directory changes. Current editor, fixed placements, canonical outputs and all historical files preserved.

Commands from repository root:

- `python3 design/architecture-278/implementation/stage36/hybrid-service-layout/check.py` —7 tests PASS.
- `python3 -O design/architecture-278/implementation/stage36/hybrid-service-layout/check.py` —7 tests PASS.
- `python3 design/architecture-278/implementation/stage36/hybrid-service-layout/generate.py --check` —exact deterministic JSON/SVG match; zero modeled known-obstacle, fastener/package and pocketed crossbar/retained-support hits.
- `python3 design/architecture-278/implementation/stage36/hybrid-service-layout/inspect_cad.py --check` —exact CAD report match. CadQuery reports a nonfatal ezdxf home-cache warning; no runtime/home change or installation attempted.
- `COREPACK_HOME=/workspace/shared/corepack corepack pnpm circuit:check` before/after and `COREPACK_HOME=/workspace/shared/corepack corepack pnpm check` after —PASS. Manual68-line inventory, no schematic/placement binding; generated docs/preflight/models/footprints and documentation type check pass.
- `git diff --check` —PASS.
- Local SVG rendered via existing Playwright/system Chromium `setContent`, inspected and retained as PNG. Not a browser suite or mechanical verification.

Tests bind original maps at both ends, extrasNC, REF versus rail identities, opposite-face numbering and local90° rotation, known solids after pocket subtraction, volume conservation, preserved negative old-access/uncut-rail cases, unknown neighbor occupancy, rejected closure inference, source hashes and preserved editor/lock. Maker PDFs and exact STEP evidence retained as cache receipts;12 source files bound. No changes to historical checker scripts or broad historical replay; no native KiCad, ERC/DRC, physical test, manufacturing, energization or procurement. No heavy suite was needed for this additive source study.

First failures remain explicit: naive cap closure intersects body; raw drawing-frame rotation applied to native STEP interferes; uncut rails intersect crossbars; old control member intersects expanded access envelope. Final source review is separate and hash-bound in REVIEW.md. It must not be read as approval of unresolved neighbor fit, strain-relief geometry or strength.
