# Continue zudo-osc-hole-field locally

Read `START_HERE.md` in this handoff. Use the official `Takazudo/zudo-circuit-doc` initializer/runtime, not a handmade imitation and not the lamp's old project-local generator. Then read the generated `circuit/WORKFLOW.md` before making changes.

Initialize a NEW project or import safely into an existing initialized project. Review the dry run of `install_resources.py`. Never overwrite local work or generated component pages. The importer is a content overlay, not a schema upgrader. Read `doc/src/content/docs/project/osc-overview.mdx` and `osc-next-actions.mdx` after import.

The current user-approved feature/layout scope is R21. Canonical grid: `project/osc-hole-field/workbench/layout/grid.json`. Existing 180 jacks and 142 controls did not move. H1.SLEW occupies [7,6], H2.SLEW [7,7]. There are 180 jacks/144 controls, no unused lower cells, no faders, six AO cells, two 1:3 MULTs, two manual A/B selectors and four noise colors. Do not restart layout design or use generative concept art. Keep the flat editor and 3D tied to the same coordinates. The preview's code is not firmware or a native KiCad design.

Read the S&H/SLEW proposal and evidence caveats. The candidate is a separate buffered RC lag after the captured output, not a larger LF398 hold capacitor. One knob controls both directions. Do not invent bypass/CV/raw-output jacks or noise normalization. B504/500k and a 0.5uF bank are initial electrical proposals, not certified final values. Qualify LF398 offset, acquisition and droop; never inherit ADDAC215's accuracy or long time range.

Start with `pnpm circuit:check`; record baseline failures. Promote selected components with exact manufacturer/full MPN/supplier/package/role, retained sources and real hashes, native evidence bundles and pin maps. The supplied component intake has candidates and missing sources and is not an order BOM or native evidence inventory. Do not manufacture PASS facts to make the catalogue complete. Generate component pages with the native runtime; never hand-edit its `components/` tree.

Then resolve the mechanical section: panel/jack nut clamping, actual exposed shafts, OCT/toggle planes, button plunger, LED optical paths, selected mating connectors and supports. Design panel and boards together BEFORE routing. Coordinate the exact zudo-pd P/B source/as-built revision and mandatory programmed 15V-only state where relevant. No giant holes to hide recessed jacks; no arbitrary hanging THT leads or connector pins used as spacers.

Prepare a factory-assembled mechanical/control coupon and a factory-assembled S&H/slew/precision-buffer utility coupon. All soldering, connector fitting, firmware programming, calibration and rework are factory tasks. Screw/plug final assembly is acceptable; no home soldering. No purchase, supplier email, shipment or fabrication order without explicit owner authorization.

Capture one complete oscillator and remaining circuits with values, pin maps, protection, error/headroom/current budgets and tests before replication. Use `kicad-sheet-plan.json`, `board-contracts.json` and `open-issues.json` as work queues. Do not derive a final BOM or power budget from the rough 3D IC rectangles.

Deliver actual local native ERC/DRC, mechanical reports, documentation checks and bench evidence when available. Report NOT RUN honestly for unavailable tools. Stop before any manufacturing release until the recorded gates are closed. Preserve the engineering rationale in the five authored doc sections; update exact evidence, then regenerate.
