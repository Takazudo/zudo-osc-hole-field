# Planning verification and work record

Baseline e8e537b5f40649fa46e8f143df4a9228a28620cd; initial interrupted research008af347 is preserved. Current editor is deliberately unchanged. This directory alone changes; parent PR286 and all earlier stages remain unchanged. Draft planning deliverable, not adopted hardware.

Obtained/checked: six exact PDF receipts in sources.json (three Tayda socket listings share FH411.pdf); two newly obtained16-position ordinary-header drawings visually inspected on page1 and electrical tables page2. Local source bytes are ignored under .circuit-cache/sources/ordinary-headers; no raw supplier PDFs committed. Existing IDC drawings/CAD receipts are reused with hashes bound in analysis.json. No stock or quote verified, no supplier contact/purchase.

Corrected first research failure: interrupted008af347 conflated the seven-wire J-SIG front link with the middle/core interface. Stage10 source audit corrected this to eight DIN signals and eight separate AGND contacts, plus K-PWR +12/−12/AGND (no+5). Final proposal preserves all logical links and14 permanent tails, without silently adopting any map. This is a recorded design correction, not a suppressed test failure.

Actual focused commands (repository root), all PASS:

- `python3 design/architecture-278/implementation/stage36/ordinary-header-comparison/generate.py`
- Same command with `--check`: deterministic analysis.json and comparison.svg, using existing Stage36 SVG primitives; no historical generation or native CAD invoked.
- `python3 design/architecture-278/implementation/stage36/ordinary-header-comparison/check.py`:5tests, including geometric intervals/negative19.2mm control, source pin maps and retained14tails, six PDF byte hashes, input bindings and deterministic outputs.
- Same check with `python3 -O`:5tests PASS. Uses unittest checks, not optimized-away assertions.
- Single Chromium render of generated SVG using Python Playwright `set_content`, viewport1200×760, saved comparison.png. This is diagram inspection, not a browser suite or physical simulation. First preview's removal arrow crossed a caption; moved arrow and re-rendered before final review.
- `COREPACK_HOME=/workspace/shared/corepack corepack pnpm circuit:check` before edits/after: PASS,68-line manual inventory, no schematic/placement binding; pin-asset check performed.

The current check remains bounded to this source-only change. No long Stage28–36 recursive replay rerun: historical artifacts and generators are unchanged except their read-only import as drawing helpers; analysis binds the exact consumed inputs. No native regeneration/ERC/DRC, simulation, energization, physical fit/removal, load/stiffness, repeated-flex, manufacturing outputs, orders, release or deployment. No CI pass claimed. No build/site publication needed for a standalone planning SVG/PNG and Markdown change.

Source conclusions: the short-pin ordinary pair fails19.2mm; the12mm alternative passes only a necessary axial screen. Exact long pin, spacer, contact working travel, full alignment/board-bow tolerance, populated obstacles, accessible screws and complete removal sweep remain OPEN.32mm IDC depth and36mm access are engineering proposals, not maker requirements; closed socket height and installed cable cuts remain unresolved. No fixture is demanded by these unknowns. They define next layout inputs rather than a blanket component requalification gate.

`COREPACK_HOME=/workspace/shared/corepack corepack pnpm check` PASS: generated evidence pages/preflight,31 selected models,31 footprint previews and TypeScript unchanged/current. `git diff --check` PASS. Source-only tests are not physical verification.

## Independent final review

`/root/stage36_review`: **PASS_SOURCE_REVIEW_ONLY**, no remaining blocking findings. Independently verified six drawing receipts, corrected Stage10 mapping, axial/spacing arithmetic, retained overlaps, current-budget qualifications and final sketch; reproduced deterministic outputs and5tests normal/-O. Editor unchanged against e8e537b5. Review does not establish contact working travel, populated fit, support/alignment or complete extraction. Broad repository checks above are author-run.

Reviewed hashes: README `c73dd0cce29faf9b987e465582c8069b8d0d6f7dd99539d176d77a059c012f7d`; sources `2e6826a0759de253379afa39d40c35d330a1d3db0726d7d60b81ec4f6c0f0b0e`; check.py `564543b6510686b5045a428a5266de46b273895ccccaef942e587bc1d338bbfb`; generate.py `68b988c9d0051252dd2919bb73187f732dbae393e1670ef3d469e0d944a27e7e`; analysis `8aa57b68bf3c4885709df71b59b317f18ef99dfe708e7f0c1ca0bec4b0c8b4ca`; SVG `44c0c84537e76f5409da918fab3eee44859a8bbec02290b8b235088fa7b59f4f`; PNG `311f9080b99d6ca2ac5d15658e29296f933fed548ee648b854ad8d1c35c390d0`. This receipt append records the verdict; no substantive change after final review.
