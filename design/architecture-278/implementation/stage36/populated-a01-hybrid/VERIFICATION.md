# Source verification

Baseline:28b301520861cfe2e925fffff5f849d5681250fe; draft287 base remains b58068fbaeb65886958a67a4f4978613414e31c5.

Executed from repository root:

- `python3 design/architecture-278/implementation/stage36/populated-a01-hybrid/check.py` —6 tests pass.
- `python3 -O design/architecture-278/implementation/stage36/populated-a01-hybrid/check.py` —same6 tests pass; no reliance on removable assertions.
- `python3 design/architecture-278/implementation/stage36/populated-a01-hybrid/generate.py --check` —exact layout JSON/SVG deterministic match.
- `COREPACK_HOME=/workspace/shared/corepack corepack pnpm check` —component contract, generated documentation/preflight/models/footprints, documentation type check pass.
- `COREPACK_HOME=/workspace/shared/corepack corepack pnpm circuit:check` —component-spec contract pass; tool explicitly reports schematic/placement binding not performed.
- `git diff --check` —pass.
- First screenshot attempt failed because the default Playwright browser cache was absent; retried with existing `/usr/bin/chromium`, without installation. File navigation was blocked by browser policy; rendered the SVG string with `setContent` successfully.
- Single Playwright local SVG screenshot rendered for visual inspection; not a browser test suite. Manufacturer source PDFs inspected/extracted; SHA256 bindings in sources.json. Cache files are ignored and not shipped.

Tests cover118-reference reconciliation, negative former collision locations, current source package projections, same-board connector intersections, engagement intervals including failing25 mm alternative,24 mirrored ordinary contacts, power order, source hashes, unknown occupancy flags and preserved editor. They do not establish IDC mappings, body heights, cable qualification, manufacturing or physical fit. No long historical suite rerun, KiCad regeneration, ERC/DRC, heavy test suite, energization or physical/native/manufacturing verification was run. First geometric failures are recorded in README.

Independent final review is recorded separately in REVIEW.md, bound to the final substantive files. Verification notes do not convert proposed geometry to adopted hardware.
