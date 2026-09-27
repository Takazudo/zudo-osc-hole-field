# 06 — Sibling model project: zudo-led-lamp

Explorer 06 of 9. Read-only survey of `$HOME/repos/circuits/zudo-led-lamp` (public, `Takazudo/zudo-led-lamp`), the project the owner named as the documentation model for `zudo-osc-hole-field`.

All facts below were read from files, `git log`, parsed KiCad/JSON, or read-only `gh` / `npm view` / Docker Hub queries on 2026-09-28. Items I could not prove are marked **UNVERIFIED**.

- Lamp HEAD: `194d8a297e3545588197342130c3111a66c10973` (local = `origin/main`, working tree clean)
- 267 commits, 2026-07-26 → 2026-09-25, single author; 70 commits carry a `Co-Authored-By: Claude …` trailer
- 748 tracked files: `doc/` 314, `.claude/` 155, `footprints/` 123, `manufacturing/` 115, `boards/` 15, `scripts/` 14, `enclosure/` 3, `.github/` 3, `symbols/` 1
- 49 PRs (47 merged), 92 issues (labels: `sub` 58, `agent-found` 16, `epic` 13, `needs-decision` 4)
- 83 merge commits vs 184 non-merge: regular merges, `base/**` + `topic/**` branch naming

---

## 1. The lamp is the ancestor of zudo-circuit-doc, not a second instance of it

This is the single most important finding for the plan.

- The lamp's component catalogue is produced by **project-local code at `doc/component-docs/`** (90 tracked files, ~23,300 lines, 29 test files, 470 tests). Its own `ARCHITECTURE.md` says: "Scope: project-local code under `doc/`. Not a framework feature, not an installable package."
- `Takazudo/zudo-circuit-doc` was **extracted from the lamp at exactly `194d8a2`**. `packages/circuit-doc/src/core/PROVENANCE.md` records every `core/**` file as byte-identical to `doc/component-docs/core/**` at that commit, with sha256 per file, enforced by `scripts/check-core-provenance.mjs`. The lamp corpus is kept in that repo as a hash-locked regression fixture (`fixtures/led/`).
- The handoff says the same thing twice:
  - `LOCAL_AGENT_PROMPT.md:3` — "Use the official `Takazudo/zudo-circuit-doc` initializer/runtime, not a handmade imitation and not the lamp's old project-local generator."
  - `payload/doc/src/content/docs/research/osc-documentation-integration.mdx:10` — "do not copy `doc/component-docs` from the lamp and maintain a second incompatible generator."
- The lamp's `doc/SCAFFOLD.md` itself says "The reusable circuit documentation foundation is a separate future task." That task is now zudo-circuit-doc.

**Consequence:** "model doc = zudo-led-lamp" must be read as *model for content style, navigation, hosting and CI discipline*, not as *copy its generator*. The machinery comes from the published packages.

### What "the lamp's old project-local generator" is

| Piece | Lamp location | Role |
|---|---|---|
| Core | `doc/component-docs/core/` (20 files) | provider-neutral view model, publication policy, safe MDX, emit, pipeline, 5 renderers |
| Adapter | `doc/component-docs/adapters/circuit/` (11 files) | reads `.claude/skills/component-*` JSON; committed instance allowlist `selection.ts` (35 records / 91 sources); per-field publication `matrix.ts` |
| CLI | `doc/component-docs/cli/` (6 files) | `generate`, `check`, `watch`, `models`, `scan-artifacts` |
| Footprint previews | `doc/component-docs/footprint-previews/` (9 files) | SVG export through a digest-pinned KiCad **9.0.9** container, manifest with hashes |
| UI | `doc/component-docs/ui/` (7 `.tsx`) + `doc/src/component-preview/`, `doc/src/component-model-viewer/` | MDX components and two Preact islands (footprint preview, three.js WRL model viewer) |
| Scripts | `doc/component-docs/scripts/` (5) | built-reference check, mermaid check, zfb link-warning filter, browser smoke, doc-skill scan |
| Validator | `.claude/skills/component-spec-audit/scripts/validate.py` | Python, stdlib only; runs as a subprocess before any evidence is read |
| Output | `doc/src/content/docs/components/` (39 files), `doc/component-docs/preflight.json` | committed, generator-owned, never hand-edited |

Executed with `node --experimental-strip-types` (no bundler); relative imports carry `.ts`.

### How the official runtime differs

| Topic | Lamp (project-local) | zudo-circuit-doc 0.1.0 (official) |
|---|---|---|
| Delivery | source files inside the repo | npm packages `@takazudo/zudo-circuit-doc@0.1.0` + `create-zudo-circuit-doc@0.1.0` (both verified present on npm, `latest` = 0.1.0) |
| Entry | ~15 `pnpm` scripts calling `component-docs/cli/*.ts` | one CLI `zudo-circuit-doc` (`generate`, `check`, `validate`, `doctor`, `models`, `scan`, `check-built`, `footprints generate`) |
| Config | hard-coded paths in `adapters/circuit/paths.ts` | `circuit.config.ts` at repo root (`satisfies CircuitConfig`) |
| Selection | TypeScript `selection.ts` with exact count locks | `circuit/publication/selection.json` + `assets.json` |
| Preflight | `doc/component-docs/preflight.json` | `circuit/generated/preflight.json` |
| Validator | `validate.py` copied in the repo, LED board specs hard-coded as fallback | Python package shipped inside the npm tarball (`python3 -B circuit_validate.py --config <json>`) |
| Inventory | LCSC C-number is the identity key; derived from schgen specs | two profiles: `generic-v1` (`inventoryProvider.kind: "manual"`, `lcsc: ""` allowed, identity = manufacturer + MPN) and `led-generator-v1` |
| Empty catalogue | impossible (count locks fail) | valid; expected package count may be 0 |
| CSS prefix | `.zld-*` in `doc/src/styles/global.css` (535 lines) | `.zcd-*` in package `styles.css` |
| Islands | statically imported in `doc/pages/docs/[[...slug]].tsx` | `doc/pages/lib/_circuit-doc-islands.ts` seam |
| Agent entry | root `CLAUDE.md` owner map | `circuit/WORKFLOW.md` canonical; `CLAUDE.md` / `AGENTS.md` are thin pointers |
| Root manifest | none — only `doc/package.json` | root `package.json` + `pnpm-workspace.yaml` (`packages: ["doc"]`) |
| Doc sections | getting-started, architecture, power, research, how-to | project, architecture, research, decisions, verification |
| Hosting files | `doc/wrangler.toml` + Cloudflare adapter | **none in the template** |
| Known defects | 8 pre-existing findings listed in circuit-doc `dev-docs/extraction-baseline.md` | fixed under separate issues |

### Version drift between the three

| Package | Lamp `doc/package.json` | circuit-doc template | npm `latest` today |
|---|---|---|---|
| `@takazudo/zudo-doc` | `^5.27.0` (locked 5.27.0) | `5.27.0` exact | 5.28.1 |
| `@takazudo/zfb` family | `2.20.2` exact | `2.21.0` exact | 2.22.0 |
| `@takazudo/zfb-adapter-cloudflare` | `2.20.2` | not used | 2.22.0 |
| pnpm | `10.34.1` | `11.5.2` | — |
| Node | `>=22` | `>=22.18.0` | local: v24.13.1 |
| Python | 3.12 (CI pin) | `>=3.10` stdlib | local: 3.12.3 |
| wrangler | `4.114.0` exact | none | 4.142.0 |

The local clone `$HOME/repos/myoss/zudo-circuit-doc` is at `491f151`, **7 commits behind** remote `main` = `5d0e2b6` (the commit the handoff reviewed). Do not read the template from the local clone without noting that.

---

## 2. Doc site: zudo-doc 5.27.0 on zfb 2.20.2, English only, everything under `doc/`

### Layout

```
doc/
  zfb.config.ts              the one config file — zudoDoc({...})
  wrangler.toml              Cloudflare Workers static assets + custom domain
  package.json               packageManager pnpm@10.34.1, engines node >=22
  pnpm-workspace.yaml        minimumReleaseAge: 0; allowBuilds esbuild, workerd
  .npmrc                     one trust-policy exclusion (no secrets)
  tsconfig.json              extends @takazudo/zudo-doc/tsconfig.base.json; includes component-docs
  CLAUDE.md, SCAFFOLD.md     site guide + scaffold baseline/refresh procedure
  pages/index.tsx            1-line re-export of the package home route
  pages/docs/[[...slug]].tsx host-owned doc route stub (76 lines) with two island imports
  src/chrome-bindings.tsx    registers 6 MDX components for generated pages
  src/styles/global.css      @import chain + .zld-* block
  src/content/docs/          MDX content
  component-docs/            the project-local generator (section 1)
  enclosure-viewer/          esbuild-bundled three.js enclosure viewer
  scripts/check-links.js     copied from create-zudo-doc 5.27.0 (pinned in ZUDO_DEPS_PINS.md)
  scripts/setup-doc-skill.sh docs-to-agent skill generator
  public/assets/             component-previews/{footprints,models}, enclosure/, pcb/
  public/_redirects          12 301 rules for renamed component records
  .claude/skills/zudo-doc-navigation-design/SKILL.md   unpublished site-editing tooling
```

There is **no `package.json` at the repo root**. CI passes `package_json_file: doc/package.json` to `pnpm/action-setup` for that reason.

### Content sections

| Directory | Files | Hand-authored? | Purpose |
|---|---|---|---|
| `getting-started/` | 3 | yes | scaffold seed pages (still generic "What is Doc?" text) |
| `architecture/` | 11 | yes | locked design: overview, board-p, board-l, bom, decisions, next-steps, power-switch, rear-controls, enclosure, swd-adapter |
| `power/` | 5 | yes | USB-PD front end, ratings matrix, charger compatibility, lessons from zudo-pd |
| `research/` | 10 | yes | candidate studies (LEDs, driver ICs, MCU, knob, thermal, …) |
| `how-to/` | 3 | yes | Cloudflare/CI setup runbook, evidence-projection adoption guide |
| `components/` | 39 | **generated** | landing, catalog, integration, 35 records + records index |
| `claude/`, `claude-md/`, `claude-skills/` | 1 + 4 + 19 | **generated** by zudo-doc `claudeResources` | raw agent resources published from the repo-root `.claude/` |

32 hand-authored pages total. Header nav has exactly 6 items; the sixth is a dropdown (`Components` → `Catalog & Records` / `Raw Agent Resources`) because `categoryMatch` is a prefix test and dropping the `claude` entry empties those sidebars.

### Language

Single locale, English. `zfb.config.ts` sets no `locales` and no `defaultLocale`; `doc/CLAUDE.md` states "This is a single-locale site, so the header has no language switcher." `cjkFriendly: true` is on regardless. `defaultLocaleOnlyPrefixes` lists the six generated trees so a future locale cannot advertise translations of them. There is **no `ja` tree** anywhere.

### Page conventions (verified across the 32 hand-authored pages)

- Frontmatter keys in use: `title` (32/32), `sidebar_position` (32/32), `description` (24/32). No `category`, no tags.
- `sidebar_position` spaced by 10 within a section (10, 20, 30 …) with later insertions at 35, 36, 37.
- No `#` h1 in content; body starts at `##`. Two pages break this (`architecture/enclosure.mdx`, `architecture/swd-adapter.mdx`).
- Every section has an `index.mdx` of ~8 lines ending in `<CategoryNav category="…" />`.
- Admonitions use directive syntax with bracketed titles: `:::note` 15, `:::caution` 7, `:::warning` 5, `:::danger` 4, `:::tip` 3. `{title="…"}` is not supported.
- Net tables are Markdown tables with backticked `Ref.Pin` lists; mermaid appears in 3 pages and is gated by `check:mermaid`.
- Cross-links use relative `.mdx` paths inside a section and root-absolute `/docs/...` across sections.
- Navigation rule (from the `doc/.claude` skill): the directory tree *is* the navigation; 3 levels only; header 3–6 items.

### `package.json` scripts

| Group | Scripts |
|---|---|
| Dev | `dev`, `dev:network`, `dev:zfb`, `dev:zfb:network`, `dev:history` (port 4322), `dev:components` (watch) |
| Build | `build` = `generate:enclosure-viewer` → `generate:models` → `generate:components` → `zfb build`; `preview` |
| Generate | `generate:components`, `generate:models`, `generate:footprint-previews` (Docker), `generate:enclosure-viewer` |
| Check | `check` (`zfb check`), `check:components`, `check:models`, `check:footprint-previews`, `check:mermaid`, `check:images`, `check:anchors`, `check:links`, `check:built-component-references` |
| Scan | `scan:artifacts`, `scan:doc-skill` |
| Test | `test:components` (node:test), `test:model-viewer:browser` |
| Skill | `setup:doc-skill` and four variants |
| Gate | `b4push` |

### Quality gate `pnpm b4push` (12 steps, all credential-free)

`check` → `test:components` → `check:footprint-previews` → `check:models` → `check:mermaid` → `build` → `check:images` → `check:anchors` → `check:built-component-references` → `check:components` → `scan:artifacts` → `scan:doc-skill`

It is a plain script chain and does **not** wrap itself in `heavy-guard.sh`.

---

## 3. CI: three workflows, every gate credential-free, deploy is secret-gated and skips green

| Workflow | Trigger | What it does |
|---|---|---|
| `component-spec-skills.yml` | PR + push on paths: `.claude/skills/**`, `scripts/schgen/**`, `boards/**/*.kicad_{sch,pcb}`, `symbols/**`, `footprints/**/*.kicad_mod`, doc MDX, `firmware/**` | Python 3.12: `validate.py`; `unittest discover`; `check_forward_tests.py`; **schematic regen-idempotency** (`gen_schematic.py` ×3 then `git diff --exit-code boards/`); `verify_power_switch.py`; `verify_swd_adapter.py`. No KiCad, no network, 10-minute timeout |
| `pr-checks.yml` | PR to `main` or `base/**` on `doc/**`, `enclosure/**`, `boards/**/*.kicad_pcb`, `.claude/skills/**`, footprints, any `CLAUDE.md` | pnpm + Node 22 + Python 3.12 → the b4push gates → `check-zfb-link-warnings.sh` on the captured build log → **generated-output drift** (`git add --intent-to-add` + `git diff --exit-code`) → determinism re-run → two denied-value scans → preview deploy → route smoke test → sticky PR comment |
| `main-deploy.yml` | push to `main`, same paths | same gates minus the link-warning check and doc-skill scan → `wrangler deploy` |

Shared patterns worth copying:

- All actions are **SHA-pinned** with the tag in a trailing comment.
- `concurrency` groups; `cancel-in-progress` is false on `main` and for production deploy.
- `permissions: contents: read` (plus `pull-requests: write` only in `pr-checks.yml`).
- A **readiness step** maps the two secrets to env and emits `ready=true|false`; deploy steps are `if: steps.readiness.outputs.ready == 'true'`. A missing credential never skips a gate and never turns the job red.
- wrangler's version is read from `doc/package.json` `devDependencies.wrangler` so CI cannot drift from the pin.
- The build log is written to `$RUNNER_TEMP` (≈2,500 false zfb link warnings would otherwise bury a real one).

### Deploy target and hostname pattern

- Cloudflare **Workers static assets**, worker name = repo name (`zudo-led-lamp`).
- `doc/wrangler.toml`: `main = "./dist/_worker.js"`, `compatibility_flags = ["nodejs_compat"]`, `workers_dev = true`, `preview_urls = true`, `[assets] directory = "./dist"`, `not_found_handling = "404-page"`, `run_worker_first = false`, and
  `[[routes]] pattern = "zudo-led-lamp.takazudomodular.com"`, `custom_domain = true`.
- `zfb.config.ts` sets `siteUrl` to the same host and `adapter: "@takazudo/zfb-adapter-cloudflare"`.
- Production hostname pattern: **`<repo-name>.takazudomodular.com`**.
- PR preview pattern: `https://pr-<N>-<worker-name>.<subdomain>.workers.dev` via `wrangler versions upload --preview-alias pr-<N>`.
- Secrets used (names only): `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`. Values: REDACTED / not read.
- No account id appears in `wrangler.toml`.

**The new project's domain is in a different zone.** `zudo-osc-hole-field.zudolab.dev` follows the pattern of zudo-circuit-doc's own site (`zudo-circuit-doc.zudolab.dev`), whose `wrangler.toml` is the *static-only* form: no `main`, no `nodejs_compat`, no adapter, `workers_dev = false`, `compatibility_date = "2026-09-27"`, wrangler pinned `4.85.0`. Its deploy notes require the API token to cover the `zudolab.dev` zone with Workers Scripts: Edit, Workers Routes: Write and DNS: Edit.

---

## 4. KiCad: three flat single-sheet projects in KiCad 10 format, one shared library

### Projects

| Project | Files | Sheets | Paper | Components | Nets | Board | Layers |
|---|---|---|---|---|---|---|---|
| `boards/board-p/` | `.kicad_pro`, `.kicad_sch` (110 KB), `.kicad_pcb` (233 KB), `sym-lib-table`, `fp-lib-table` | 1 (no hierarchy) | A3 | 25 | 18 | 27 × 40 mm | 2, 1.6 mm FR4 |
| `boards/board-l/` | same set (`.kicad_sch` 194 KB, `.kicad_pcb` 516 KB) | 1 | A2 | 69 | 46 | 60 × 60 mm | 2 |
| `boards/swd-adapter/` | same set | 1 | A4 | 2 | 5 | 36 × 18.1 mm | 2 |

96 components in total across the whole lamp.

### File-format versions (read from headers)

| File type | `version` | `generator` | `generator_version` |
|---|---|---|---|
| `.kicad_sch` | `20260306` | `"eeschema"` (written by the Python generator) | `"10.0"` |
| `.kicad_pcb` | `20260206` | `"pcbnew"` | `"10.0"` |
| `.kicad_sym` | `20251024` | `"kicad_symbol_editor"` | `"10.0"` |
| `.kicad_pro` | `meta.version` 3 | — | — |
| lib tables | `version 7` | — | — |
| `.kicad_mod` (30 of 31) | legacy `(module easyeda2kicad:… (tedit …))` | easyeda2kicad | KiCad 5-era syntax |

Manufacturing reports record `kicad_version: 10.0.0`.

### Libraries

- Symbol library: **`zudo-led-lamp`** → `symbols/zudo-led-lamp.kicad_sym`, one file, 44 symbols, **zero multi-unit symbols**.
- Footprint library: **`zudo-led-lamp`** → `footprints/kicad/zudo-led-lamp.pretty/`, 31 footprints.
- 3D models: `footprints/kicad/zudo-led-lamp.3dshapes/`, 27 `.step` + 27 `.wrl`.
- **Dual-location rule:** every `.kicad_mod` exists byte-identical in `footprints/kicad/` (master) and in the `.pretty/` dir; verified 31 = 31.
- Lib tables are identical in all three projects and use `${KIPRJMOD}/../../symbols/…` and `${KIPRJMOD}/../../footprints/kicad/….pretty`. All projects must therefore sit at the same depth `boards/<name>/`.
- Hand-drawn footprints: `PogoPad_1x03/1x04/1x08_P2.54mm`, `TestPad_D1.5mm`.
- `footprints/vendor/<LCSC>/` holds vendor model derivation notes and scripts.
- Parts are imported with `easyeda2kicad --lcsc_id <id> --footprint --symbol --3d`; the EasyEDA API returns 403 after ~20 rapid requests.
- Design rules in `.kicad_pro`: one `Default` net class (track 0.2, clearance 0.2, via 0.6/0.3), no net-class patterns; `min_clearance` 0.127, `min_copper_edge_clearance` 0.5.

### How the schematics were authored: generated by pure-Python scripts, never drawn

Evidence:

- `scripts/schgen/README.md`: "The … schematics are not hand-drawn. … The spec is the source of truth; the `.kicad_sch` file is a build artifact of it."
- Every UUID in all three `.kicad_sch` files is **version 5** (430 / 214 / 53), matching `schgen_core.new_uuid()` = `uuid.uuid5(fixed namespace, seed)`.
- CI regenerates all three and fails on any diff under `boards/`.

Generator facts (`scripts/schgen/`, 11 files, Python **stdlib only**, no KiCad needed):

| File | Lines of interest |
|---|---|
| `sexp.py` | 40-line S-expression tokenizer/parser |
| `schgen_core.py` | 240 lines: reads symbols out of the `.kicad_sym` by text scan, embeds them in `lib_symbols`, places instances, emits labels |
| `board_*_spec.py` | `PROJECT_NAME`, `OUT`, `PAPER`, `COMPONENTS {ref: (symbol, value, lcsc, footprint, dnp, (x, y))}`, `NETS {name: ['REF.PIN', …]}`, `NO_CONNECT`, optional `LABEL_OVERRIDES`, `EXTERNAL_COMPONENTS` |
| `gen_schematic.py` | 10-line CLI |
| `verify_netlist.py` / `verify.sh` | diff a `kicad-cli sch export netlist` against the spec; `SKIPPED` exit 0 when `kicad-cli` is absent |
| `verify_power_switch.py`, `verify_swd_adapter.py` | pure-Python topology audits, run in CI |

Hard limits of the generator, all verified in `schgen_core.py`:

- **No wires.** Connectivity is 100% `global_label` at pin endpoints (165 labels on board-l, 0 `(wire`, 0 `(junction`).
- **One flat sheet.** No `(sheet` nodes, no hierarchical labels, single `sheet_instances` path `/`.
- **`(unit 1)` is hard-coded.** `pins_of()` gathers pins from *all* sub-symbols and places them on one instance, so a multi-unit part (dual/quad op-amp, OTA, CMOS gates) cannot be represented.
- **Rotation is always 0** (`(at X Y 0)`); no mirroring.
- No power symbols and no `PWR_FLAG`; this is the source of the 6 `pin_to_pin` ERC warnings per board.
- Library nickname and path are hard-coded to `zudo-led-lamp`.
- Coverage is enforced: every pin of every component must be in exactly one net or in `NO_CONNECT`.

### How the PCBs were authored: KiCad pcbnew, with agent edits through the pcbnew Python API

Evidence:

- Every UUID in all three `.kicad_pcb` files is **version 4** (2336 / 973 / 155): not the deterministic generator.
- No PCB generator exists under `scripts/`; `scripts/pcb/` contains only `export-jlcpcb.py`, `verify-jlcpcb.py`, `verify-controls.py`. History shows no deleted PCB generator either.
- `architecture/next-steps.mdx`: "layout, DRC and fab export are ordinary KiCad."
- The first full layouts arrived as large commits with subject `update`, no body, no agent trailer, with `.kicad_pro` rewritten in the same commit: board-p `9857ba7` (+10,374 lines, 2026-08-20), board-l `8b03e9c` (+24,285 lines, 2026-08-23). No session log exists for those dates. **UNVERIFIED** but consistent with the owner laying them out in the KiCad GUI on macOS.
- Later edits were made by agents with **throwaway Python scripts using `import pcbnew as k`**, kept in cclogs rather than in the repo:
  `$DROPBOX_CCLOGS_DIR/zudo-led-lamp/{rear-controls-pcb,stack-clear-controls,jlc-switch-replacement,low-profile-controls}/*.py` (12 scripts, 899 lines).
  They load the board, remove/move footprints, `FootprintLoad` from the `.pretty` dir, assign nets from a `kicad-cli` netlist, and route with a hand-written **A\* grid router** (0.25 mm step, 0.21 mm clearance, two layers, `heapq`), then refill zones and `SaveBoard`. Each run kept `baseline.kicad_pcb`, `attempt-drc.json`, `final-drc.json` and 3D renders beside the script.
- `swd-adapter.kicad_pcb` arrived complete in one squash-merged agent PR (#105). How it was produced is **UNVERIFIED**; no script was retained.
- 663 of 664 board-l track segments are at 0/45/90/135°.

### ERC / DRC: run with KiCad 10 `kicad-cli` on the owner's Mac, never in CI

- Commands are logged in `manufacturing/jlcpcb/2026-09-19/<board>/checks/commands.log`, all invoking `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`:
  `pcb drc --refill-zones --save-board --schematic-parity --format json`, `sch erc --format json`, `sch export netlist --format kicadsexpr`.
- Results retained as JSON:

| Board | ERC | DRC | Unconnected | Parity |
|---|---|---|---|---|
| board-p | 6 warnings (`pin_to_pin`) | 27 warnings (19 `text_height`, silk, 1 `track_dangling`, 1 `holes_co_located`) | 0 | 3 (`extra_footprint`, mounting holes) |
| board-l | 6 warnings (`pin_to_pin`) | 59 warnings (39 `silk_overlap`, 19 `silk_over_copper`, 1 `lib_footprint_mismatch`) | 0 | 0 |
| swd-adapter | 0 | 1 warning | 0 | 0 |

  Zero errors on all three.
- CI has no KiCad. It enforces only regen-idempotency plus the two pure-Python audits.

### This WSL machine cannot run KiCad 10 checks today

| Tool | State on this machine |
|---|---|
| `kicad-cli` | **not installed** |
| Docker | 29.3.0 present |
| Cached KiCad image | `kicad/kicad@sha256:e638b79b…` = **9.0.9**, amd64 — cannot open `20260306` / `20260206` files |
| `easyeda2kicad`, `uv` | installed in `$HOME/.local/bin` |
| Official KiCad 10 image | `kicad/kicad:10.0.6` (also `10.0`, `-full` variants) published 2026-09-22 on Docker Hub, amd64 — **not pulled** |

The official image description says it contains "KiCad EDA, python and the stock symbol and footprint libraries for use in automation workflows", so `kicad-cli` and `pcbnew` Python would both be available in a container. **UNVERIFIED** until pulled and run.

---

## 5. Manufacturing: one dated, hash-locked JLCPCB release per order

`manufacturing/` holds 115 tracked files.

```
manufacturing/
  README.md                          order instructions, caveats, traceability
  ORDER-STATUS.md                    "Order placed — 2026-09-19"
  jlcpcb-rotation-corrections.json   part-number-locked CPL rotation overrides (1 entry: board-l RV1 +180°)
  jlcpcb/zudo-led-lamp-2026-09-19.zip
  jlcpcb/2026-09-19/
    README.md, ORDER-NOTES.md, SHA256SUMS, manifest.json, rotation-corrections.json
    checks/{board-*-drc.json, independent-validation.json}
    <board>/
      <board>-gerbers.zip
      gerbers/   9 Gerber layers + PTH.drl + NPTH.drl + .gbrjob
      bom.csv    columns: Comment, Designator, Footprint, JLCPCB Part #
      cpl.csv    columns: Designator, Mid X, Mid Y, Layer, Rotation
      excluded.csv
      assembly-{top,bottom}.svg, gerber-{top,bottom}.{svg,png}
      raw/       netlist, KiCad BOM, KiCad positions
      source/    snapshot of .kicad_pcb/.kicad_pro/.kicad_sch + lib tables
      checks/    commands.log, drc.json, erc.json, export-validation.json
```

- `scripts/pcb/export-jlcpcb.py` (Python stdlib + `kicad-cli`) snapshots the sources, normalises stale `LCSC Part` fields, applies release population overrides, runs DRC/ERC/netlist-verify, exports Gerbers/drill/pos, and **refuses to overwrite** an existing release directory.
- BOM conversion depends on a **personal skill script** outside the repo (`jlcpcb-bom-generate-from-kicad/scripts/convert_to_jlcpcb.py`, supplied with `--converter`).
- `scripts/pcb/verify-jlcpcb.py` re-renders the Gerber ZIPs independently with `gerbonara==1.6.3` and `resvg-py`.
- CPL uses native KiCad coordinates with the drill/place origin, no second Y inversion (KiCad 10 guide).
- BOM rows: board-p 14, board-l 24, swd-adapter 2.

---

## 6. Project skills: 16 at repo root, 1 under `doc/`

| Skill | Files | Relevance |
|---|---|---|
| `component-spec-audit` | 34 | **Core.** Owns the end-to-end "add or replace a BOM component" workflow (`references/new-component-workflow.md`): lock identity in the schgen spec → build evidence bundle → acquire symbol/footprint/STEP+WRL → choose what is public → regenerate and commit. Holds `inventory.json`, `contract.md`, `schema.json`, `validate.py` + tests, mutation/golden fixtures, the bundle template |
| `circuit-spec-integration` | 6 | Cross-component rules (`rules.json`, 7 rules), forward tests, observed runs |
| 14 × `component-<part>` | 8–9 each | Evidence owner bundles: `SKILL.md`, `manifest.json`, `sources.json`, `facts.json`, `coverage.json`, `routing.json`, `interactions.json`, `pin-map.json`, `agents/openai.yaml` |
| `doc/.claude/skills/zudo-doc-navigation-design` | 1 | Site navigation rules; deliberately **unpublished** because `claudeResources.claudeDir` points at the repo-root `.claude` |

Corpus size: 14 owner bundles, 35 records, 91 sources, 391 facts, 163 pins.

Root `CLAUDE.md` is a 17-line routing map from part to owner skill. `footprints/CLAUDE.md` defines the KiCad asset rules.

---

## 7. Enclosure: lamp-specific CadQuery generator

`enclosure/generate.py` (uv inline script, `cadquery==2.6.1`, `trimesh==4.8.3`) builds a 3D-printed starburst shell, reads the PCBs through `sexp.py`, and needs `kicad-cli` for PCB models. `doc/enclosure-viewer/` bundles a three.js viewer and verifies source/board/mesh hashes at build time, which is why `boards/**/*.kicad_pcb` is a trigger path for the doc workflows. Nothing here applies to a flat 318 × 298 mm panel.

---

## 8. Replicate from the model

### Structure

- `boards/<name>/` one KiCad project per PCB order, all at the same depth, each with its own `sym-lib-table` / `fp-lib-table`.
- One shared library named after the repo: `symbols/zudo-osc-hole-field.kicad_sym`, `footprints/kicad/zudo-osc-hole-field.pretty/`, `footprints/kicad/zudo-osc-hole-field.3dshapes/`, with `${KIPRJMOD}/../../…` paths.
- `scripts/schgen/` and `scripts/pcb/` for generators and verifiers; `manufacturing/jlcpcb/<date>/` for releases.
- `doc/` as the site root; repo-root `.claude/skills/` as the evidence store.
- `.gitignore` entries for KiCad transients: `*.kicad_prl`, `*-backups/`, `fp-info-cache`, `*.lck`, `_autosave-*`, `__pycache__/`.
- `ZUDO_DEPS_PINS.md` + `doc/SCAFFOLD.md` recording scaffold provenance and refresh procedure.
- `footprints/CLAUDE.md` and `doc/CLAUDE.md` scoped guides; short root `CLAUDE.md`.

### Conventions

- Spec module is the source of truth; the `.kicad_sch` is a committed build artifact; commit both together.
- Deterministic `uuid5` identifiers so regeneration is byte-stable.
- Every pin is either in a net or in `NO_CONNECT`; the generator asserts it.
- Exact MPN + manufacturer per BOM line; never infer evidence from a same-name part.
- Part identity in the schematic instance, not in shared footprints.
- STEP **and** WRL for every model.
- Doc page conventions from section 2; `sidebar_position` in tens; one `index.mdx` with `<CategoryNav>` per section; header nav capped at 6.
- Generated trees are committed and never hand-edited.
- Agent PCB edits keep baseline, attempt DRC and final DRC as evidence.

### Scripts and CI

- Regen-idempotency job for generated schematics.
- Generated-output drift check with `git add --intent-to-add`.
- Secret-readiness gating so deploy skips green.
- SHA-pinned actions, `concurrency`, minimal `permissions`.
- wrangler version read from `package.json`.
- A credential-free `b4push` chain mirrored step for step in CI.
- `manufacturing` export that refuses to overwrite and records `commands.log`.

## 9. Lamp-specific — do not copy

| Item | Why |
|---|---|
| `doc/component-docs/**` (90 files) | superseded by `@takazudo/zudo-circuit-doc`; the handoff forbids copying it |
| `doc/src/component-preview/`, `doc/src/component-model-viewer/`, `.zld-*` CSS, the island imports in the route stub | shipped by the package as `./islands`, `./ui`, `./styles.css` (`.zcd-*`) |
| `.claude/skills/component-spec-audit/scripts/validate.py` and its LED fixtures | validator ships inside the npm package |
| 14 `component-*` bundles, `inventory.json`, `rules.json`, `selection.ts` count locks | lamp parts and lamp counts |
| `doc/public/_redirects` | lamp record renames |
| Hostname `*.takazudomodular.com`, worker name, Cloudflare adapter + `_worker.js` + `nodejs_compat` | new site is `zudolab.dev`, static assets only |
| PR smoke routes `/docs/components/records/al8860mp-13` and the `AL8860MP-13` content probe | lamp record |
| `enclosure/`, `doc/enclosure-viewer/`, `_artwork-resources/enclosure.ai`, `generate:enclosure-viewer` in `build` | 3D-printed lamp shell |
| `power/` section, USB-PD/STUSB4500 pages, bring-up gates | lamp circuit (zudo-pd reuse is a different explorer's subject) |
| `getting-started/` seed pages | generic scaffold text; the official template uses `project/` instead |
| `schgen_core.py` **as-is** | hard-coded library name, single unit, single sheet, rotation 0 |
| KiCad 9.0.9 preview container pin | lamp byte-reproducibility choice; the package carries its own |
| LCSC-as-identity assumption | the synth uses many non-LCSC panel parts (jacks, pots, switches) |
| pnpm 10.34.1 / zfb 2.20.2 pins | official family is pnpm 11.5.2 / zfb 2.21.0 / zudo-doc 5.27.0 |
| Personal BOM converter dependency | external to the repo; not reproducible elsewhere |

---

## 10. Risks and blockers

1. **Model vs. official runtime conflict.** The owner says "model doc is zudo-led-lamp"; the handoff says use the official runtime and not the lamp generator. The handoff's doc payload (15 architecture, 25 research, 2 project, 2 verification, 1 decisions pages) already matches the **official template's** section names, not the lamp's.
2. **schgen does not scale to this design as written.** It was proven on 96 components with no multi-unit parts. An analog synth is dominated by dual/quad op-amps and OTAs; `(unit 1)` is hard-coded. A 1,000+ component design on one flat label-only sheet is also unreadable for the owner, who intends to tweak the design later.
3. **No KiCad 10 on this machine.** ERC, DRC, netlist verification and `pcbnew` scripting all ran on the owner's Mac for the lamp. Here only a KiCad 9.0.9 image is cached.
4. **PCB authoring has no reusable tooling.** The lamp's agent routing scripts are one-off, hard-code absolute macOS paths and a 60 mm board bound, and handled at most ~10 nets per run. Nothing in the model demonstrates agent-authored layout at the scale of 180 jacks + 144 controls across stacked boards.
5. **The hand-rolled A\* router is not a plan for full-board routing.** It was used for local repairs only.
6. **Hosting template gap.** The official template ships no `wrangler.toml`, no deploy workflow and no CI at all; the lamp's are tied to a worker adapter and another zone.
7. **Cloudflare token zone scope.** A token scoped for `takazudomodular.com` will fail to attach a `zudolab.dev` custom domain.
8. **Version family drift.** Three different pin sets exist (lamp, template, npm latest). Mixing them is explicitly warned against in the handoff.
9. **Local zudo-circuit-doc clone is 7 commits stale** relative to the reviewed commit.
10. **Legacy footprint syntax.** easyeda2kicad emits KiCad 5-era `(module …)` files; KiCad 10 reads them, but `lib_footprint_mismatch` warnings follow once KiCad re-saves the board copy.
11. **Stale `LCSC Part` fields in shared footprints** can override schematic identity in plugin-based BOM export.
12. **Panel size vs. fab limits.** The lamp's largest board is 60 × 60 mm; nothing in the model covers a 318 × 298 mm panel PCB. **UNVERIFIED** here; belongs to the panel/fab explorer.

---

## 11. Open decisions with recommended defaults

| # | Decision | Recommended default |
|---|---|---|
| 1 | Generator: lamp copy vs official runtime | Official `create-zudo-circuit-doc@0.1.0` + `@takazudo/zudo-circuit-doc@0.1.0`; take only style, nav discipline, CI and hosting patterns from the lamp |
| 2 | Doc section layout | Official template sections (`project`, `architecture`, `research`, `decisions`, `verification`, `components`) because the handoff payload already targets them; add a `how-to` section only when a runbook exists |
| 3 | Locale | English only, `defaultLocale: "en"`, `cjkFriendly: true`; no `ja` tree |
| 4 | Version family | The template's exact pins (zudo-doc 5.27.0, zfb 2.21.0, pnpm 11.5.2, Node ≥22.18.0); bump later as one family with `/dev-bump-zudo-deps` |
| 5 | Hosting form | Static assets only, modelled on zudo-circuit-doc's `wrangler.toml`; `siteUrl` = `https://zudo-osc-hole-field.zudolab.dev`; no adapter |
| 6 | When to deploy | Commit `wrangler.toml` and secret-gated workflows now; the deploy step skips green until the owner sets the two secrets |
| 7 | PR previews | Defer; they need `workers_dev = true` and `preview_urls = true`, which the static production config turns off |
| 8 | Schematic authoring | Keep the spec-as-source, deterministic, CI-idempotent approach, but write a new generator that supports multi-unit symbols, hierarchical sheets per functional block, rotation, and power symbols. Do not reuse `schgen_core.py` unchanged |
| 9 | KiCad version | KiCad 10 file formats, matching the lamp and the owner's installed KiCad |
| 10 | ERC/DRC execution | Pull `kicad/kicad:10.0.6` by digest and run `kicad-cli` in Docker locally through `heavy-guard.sh`; add it to CI as a separate job later |
| 11 | PCB authoring | Scripted placement from the fixed panel grid via `pcbnew` Python in the same container; routing left to the owner in the GUI unless a later decision says otherwise |
| 12 | Inventory profile | `inventoryProvider.kind: "manual"` (generic-v1), since most panel parts have no LCSC number |
| 13 | Library naming | `zudo-osc-hole-field` for symbol, footprint and 3D libraries |
| 14 | zudo-pd boards | Reference by pinned revision rather than copying KiCad files into this repo (confirm with the zudo-pd explorer) |
| 15 | Root `package.json` | Yes, as the official template does; the lamp's doc-only layout is the older shape |

---

## 12. Key paths

| What | Path |
|---|---|
| Lamp repo | `$HOME/repos/circuits/zudo-led-lamp` |
| Site config | `$HOME/repos/circuits/zudo-led-lamp/doc/zfb.config.ts` |
| Hosting config | `$HOME/repos/circuits/zudo-led-lamp/doc/wrangler.toml` |
| Workflows | `$HOME/repos/circuits/zudo-led-lamp/.github/workflows/{component-spec-skills,pr-checks,main-deploy}.yml` |
| Old generator contract | `$HOME/repos/circuits/zudo-led-lamp/doc/component-docs/ARCHITECTURE.md` |
| Schematic generator | `$HOME/repos/circuits/zudo-led-lamp/scripts/schgen/schgen_core.py` |
| Board spec example | `$HOME/repos/circuits/zudo-led-lamp/scripts/schgen/board_p_spec.py` |
| KiCad asset rules | `$HOME/repos/circuits/zudo-led-lamp/footprints/CLAUDE.md` |
| Onboarding workflow | `$HOME/repos/circuits/zudo-led-lamp/.claude/skills/component-spec-audit/references/new-component-workflow.md` |
| Manufacturing export | `$HOME/repos/circuits/zudo-led-lamp/scripts/pcb/export-jlcpcb.py` |
| Release example | `$HOME/repos/circuits/zudo-led-lamp/manufacturing/jlcpcb/2026-09-19/` |
| Agent PCB scripts | `$DROPBOX_CCLOGS_DIR/zudo-led-lamp/{rear-controls-pcb,stack-clear-controls,jlc-switch-replacement,low-profile-controls}/` |
| Official runtime clone (stale by 7) | `$HOME/repos/myoss/zudo-circuit-doc` |
| Official template | `$HOME/repos/myoss/zudo-circuit-doc/packages/create-zudo-circuit-doc/templates/default/` |
| Extraction record | `$HOME/repos/myoss/zudo-circuit-doc/dev-docs/extraction-baseline.md` |
