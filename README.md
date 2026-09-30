# zudo-osc-hole-field

A standalone, cable-patched analog synthesizer on one flat 318 × 298 mm front panel, with 180 jacks above 144 controls and 33 module instances. Documentation domain: [zudo-osc-hole-field.zudolab.dev](https://zudo-osc-hole-field.zudolab.dev).

**Status:** pre-release design; no fabrication release exists.

The site is built with [zudo-circuit-doc](https://github.com/Takazudo/zudo-circuit-doc) on top of [zudo-doc](https://github.com/zudolab/zudo-doc). Authored project documentation lives under `doc/src/content/docs/`; exact-component evidence lives under `.claude/skills/`, and the component pages are generated from that evidence.

GitHub Actions runs the evidence validation, documentation checks, site build and built-site checks, plus Python unit tests under `scripts/` and `design/`, for pull requests and pushes to `main`. These checks need no secrets and do not deploy the site.

## Commands

| Command | What it does |
| --- | --- |
| `pnpm install` | Install dependencies |
| `pnpm dev` | Dev server, regenerating component pages as evidence changes |
| `pnpm build` | Publish selected models, generate component pages, build the site |
| `pnpm check` | Validate evidence, check generated output is current, type-check the site |
| `pnpm check:site` | Post-build checks: references, publication scope, links |
| `pnpm circuit:check` | Validate the component evidence (offline) |
| `pnpm circuit:generate` | Regenerate the component pages and the preflight report |
| `pnpm circuit:doctor` | Report required and optional tools |
| `pnpm previews:generate` | Render footprint previews (optional; needs Docker) |

Agent-facing commands (new component bundles, online source refresh) are listed in [circuit/WORKFLOW.md](circuit/WORKFLOW.md).

## Tool requirements

| Tool | Required | Used for |
| --- | --- | --- |
| Node.js ≥22.18 | Yes | Everything |
| pnpm 11 (via corepack) | Yes | Install and scripts |
| Python ≥3.10 | Yes | Evidence validation (standard library only) |
| git | Yes | History and review diffs |
| Docker with the pinned KiCad image | No | Footprint previews |
| Chrome | No | Browser smoke check |
| Network | No | Downloading sources and assets only; the build is offline |
| easyeda2kicad | No | Importing CAD assets for LCSC-listed parts |
