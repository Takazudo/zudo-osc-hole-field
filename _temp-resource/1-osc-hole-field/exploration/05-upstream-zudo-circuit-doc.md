# 05 — Upstream framework `zudo-circuit-doc` (explorer report)

Explorer 05 of 9 for the `zudo-osc-hole-field` plan. Exploration only; nothing was modified in any
repo or in the handoff directory. All empirical runs happened on throwaway copies inside the
explorer's own scratch directory.

Date of exploration: 2026-09-28 (JST).

## The task premise is inverted: the handoff reviewed the NEWEST commit, the local checkout is the stale one

| Ref | SHA | Commit date | Where |
| --- | --- | --- | --- |
| Local checkout `$HOME/repos/myoss/zudo-circuit-doc` HEAD | `491f151` | 2026-09-27 16:16 +0900 (07:16Z) | local `main`, equal to the local `origin/main` ref; last fetch 2026-09-27 16:16:42 +0900 |
| Handoff-reviewed commit | `5d0e2b630776489d394be341586b889dfe0d1cb8` | 2026-09-27 11:15:27Z (20:15 +0900) | **current `main` HEAD on GitHub** (verified with `gh api repos/Takazudo/zudo-circuit-doc/commits/main`) |

- `git -C $HOME/repos/myoss/zudo-circuit-doc log --oneline 5d0e2b6..HEAD` fails with
  `fatal: ambiguous argument '5d0e2b6..HEAD': unknown revision` because the object does not exist
  locally. `git cat-file -t 5d0e2b6...` also fails.
- GitHub compare `491f151...5d0e2b6`: status `ahead`, `ahead_by: 7`, `behind_by: 0`.
- So **nothing has changed upstream since the handoff's review**. The local checkout is 7 commits
  behind and needs `git pull` before anyone reads docs from it.
- To read the true state, the explorer cloned the remote into its scratch dir. Everything below is
  from remote HEAD `5d0e2b6` unless a line says "local checkout".

### The 7 commits the local checkout is missing (491f151..5d0e2b6)

| SHA | Date (UTC) | Subject |
| --- | --- | --- |
| `e216508` | 2026-09-27 07:54 | test(provider): compare validator cwd against the resolved project path |
| `f3c0aee` | 2026-09-27 07:54 | chore(release): @takazudo/zudo-circuit-doc v0.1.0 |
| `c5a813c` | 2026-09-27 11:00 | docs: note the runtime 0.1.0 is on npm while the initializer is not |
| `fb25dfb` | 2026-09-27 11:00 | ci(release): stage npm releases for maintainer approval |
| `081f5d3` | 2026-09-27 11:05 | test(release): expect npm stage publish in the publish workflows |
| `c9a2a2b` | 2026-09-27 11:05 | chore(release): create-zudo-circuit-doc v0.1.0 |
| `5d0e2b6` | 2026-09-27 11:15 | docs: create projects with pnpm create now that both packages are on npm |

Files touched (11 files, +180/-58): `.claude/skills/l-make-release/SKILL.md`, two publish workflows,
`dev-docs/publishing.md`, two changelog MDX pages, `doc/.../getting-started/create-a-project.mdx`,
both `CHANGELOG.md`, one test file, one script test.

**No change to `packages/create-zudo-circuit-doc/templates/default/**`, to `src/**` of either
package, or to the runtime.** Verified: `diff -r` of the published template against both the remote
HEAD template and the local checkout template reports IDENTICAL. The local checkout is therefore
safe for reading template/runtime source, and stale only for release docs.

## Both packages are published on npm at 0.1.0

| Package | npm name | Versions | `latest` | Published (UTC) | Unpacked |
| --- | --- | --- | --- | --- | --- |
| Runtime | `@takazudo/zudo-circuit-doc` | `["0.1.0"]` | `0.1.0` | 2026-09-27T10:53:51Z | 1,073,951 B |
| Initializer | `create-zudo-circuit-doc` | `["0.1.0"]` | `0.1.0` | 2026-09-27T11:14:31Z | 267,581 B |

Git tags on the remote: `v0.1.0`, `create-zudo-circuit-doc-v0.1.0`. Upstream open issues: 0. All 8
CI workflows on `5d0e2b6` concluded `success`.

Runtime manifest (`packages/circuit-doc/package.json`):

- `bin`: `zudo-circuit-doc` -> `./bin/zudo-circuit-doc.js`
- `exports`: `.`, `./config`, `./ui`, `./mdx-extras`, `./islands`, `./descriptors`, `./styles.css`, `./package.json`
- `dependencies`: `mdast-util-to-markdown 2.1.2`, `mdast-util-mdx 3.0.0`, `mdast-util-gfm-table 2.0.0`, `three 0.185.1`
- `peerDependencies`: `@takazudo/zfb ^2.20.2`, `@takazudo/zudo-doc ^5.27.0`, `preact ^10.29.1`
- `engines.node`: `>=22.18.0`
- `files`: `bin lib python templates contract styles.css README.md LICENSE CHANGELOG.md`

Initializer manifest: no runtime dependencies at all; `engines.node >=22.18.0`; ships `bin dist templates`.

Version family (ADR-003, exact-pinned across the repo and the template):

| Package | Version |
| --- | --- |
| `@takazudo/zudo-doc`, `@takazudo/zudo-doc-history-server` | 5.27.0 |
| `@takazudo/zfb`, `@takazudo/zfb-runtime`, `@takazudo/zfb-md-wasm` | 2.21.0 |
| pnpm (`packageManager`, corepack) | 11.5.2 |
| Node | >=22.18.0 |
| Python | >=3.10, stdlib only |

Fallback rule recorded upstream: if build or island hydration fails on zfb 2.21.0 but passes on
2.20.3, pin the whole zfb family to 2.20.3 and file `/dev-upstream-report`.

## The initializer refuses the target repo because it contains `.git`

The rule, quoted from `packages/create-zudo-circuit-doc/src/scaffold.ts` lines 50-69:

```ts
/** Throws a CliError, unchanged, if the destination exists and is not empty (spec #4). There is no force flag. */
export function checkDestinationCollision(destinationPath: string): void {
  let stat: fs.Stats;
  try {
    stat = fs.statSync(destinationPath);
  } catch {
    return; // Missing destination is fine.
  }
  if (!stat.isDirectory()) {
    throw new CliError(
      `Cannot create project: "${destinationPath}" already exists and is not a directory.`,
    );
  }
  const entries = fs.readdirSync(destinationPath);
  if (entries.length > 0) {
    throw new CliError(
      `Cannot create project: "${destinationPath}" already exists and is not empty.`,
    );
  }
}
```

`fs.readdirSync` returns dot-entries, so `['.git']` has length 1. There is no `.git` exemption
anywhere in `src/` or in the tests (grep confirmed). There is no force flag.

Empirical confirmation (published 0.1.0, scratch dir containing only a fresh `.git`):

```
Error: Cannot create project: ".../runs/gitonly" already exists and is not empty.
exit=1
```

The directory was left unchanged. A truly empty existing directory is accepted (exit 0) and filled
in place.

State of the target repo `$HOME/repos/circuits/zudo-osc-hole-field`: contains only `.git`; one commit
`1590775 init` (an empty commit, no tracked files); remote `origin` is
`https://github.com/Takazudo/zudo-osc-hole-field.git`, visibility **public**, default branch `main`,
no Actions secrets configured.

The handoff's own wrapper `bootstrap_project.py` applies the same rule
(`dst.exists() and (not dst.is_dir() or any(dst.iterdir()))`) and would refuse the repo as well.

### Every initializer flag (from `src/args.ts`, `src/help.ts`, `src/validate.ts`)

```
Usage: create-zudo-circuit-doc [destination] [--name <npm-name>] [--title <site title>]
       [--library <kicad-lib-name>] [--agent claude|codex|both|none] [--yes]
       [--install|--no-install] [--git|--no-git] [--runtime-spec <spec>] [--help] [--version]
```

| Flag | Default | Validation / behaviour |
| --- | --- | --- |
| `[destination]` | prompted on a TTY | At most one positional. Missing + (`--yes` or non-TTY) is a usage error (exit 2). Must not exist, or be empty. |
| `--name <npm-name>` | basename of destination | 1-214 chars; must not contain `node_modules`; `^[a-z0-9][a-z0-9._-]*$` or scoped equivalent |
| `--title <site title>` | title-cased name (`zudo-osc-hole-field` -> `Zudo Osc Hole Field`) | 1-80 chars; no control chars; none of `" ' \` \ $ < > { }` (it is substituted verbatim into TS literals and MDX frontmatter) |
| `--library <kicad-lib-name>` | name with scope stripped and illegal chars replaced by `-`, cut at 64 | `^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$` |
| `--agent claude\|codex\|both\|none` | `both` | `claude` removes `AGENTS.md`; `codex` removes `CLAUDE.md`; `none` removes both. `.claude/skills/**` always stays |
| `--yes`, `-y` | off | Never prompt |
| `--install` / `--no-install` | install | Last spelling on the command line wins. Runs `pnpm install` (stdio inherited). Failure -> exit 1, files left in place |
| `--git` / `--no-git` | git | Last spelling wins. Runs `git init -b main`, `git add -A`, commit `Initial commit from create-zudo-circuit-doc`. **Skipped with a note if the destination is already inside a git work tree.** Uses a neutral identity if none is configured |
| `--runtime-spec <spec>` | template's `^0.1.0` | 1-1024 chars; semver range/dist-tag (`^[0-9A-Za-z.\-+^~*<>=|\s]+$`) or `file:` with an **absolute** path. Rewrites the dependency in both `package.json` and `doc/package.json` |
| `--help`, `-h` / `--version`, `-v` | | Print and exit 0 |

Exit codes: `0` ok, `1` collision / install or git failure, `2` usage error.

Placeholders substituted in every non-binary template file: `__PROJECT_NAME__`, `__SITE_TITLE__`,
`__LIBRARY_NAME__`. `_gitignore` is renamed to `.gitignore`. Composition happens in a staging
directory `.create-zudo-circuit-doc-staging-<hex>` and is renamed into place atomically.

After substitution the project name appears in exactly 5 files: `README.md`, `circuit.config.ts`,
`doc/package.json`, `doc/zfb.config.ts`, `package.json`.

### Generated tree (60 files, `--agent both`)

```
.claude/skills/circuit-spec-integration/SKILL.md
.claude/skills/circuit-spec-integration/references/rules.json
.claude/skills/component-spec-audit/SKILL.md
.claude/skills/component-spec-audit/references/contract.md
.claude/skills/component-spec-audit/references/direct-routing.json
.claude/skills/component-spec-audit/references/external-vendor-qualifiers.json
.claude/skills/component-spec-audit/references/inventory.json
.claude/skills/component-spec-audit/references/new-component-workflow.md
.gitignore
AGENTS.md
CLAUDE.md
README.md
ZUDO_DEPS_PINS.md
circuit.config.ts
circuit/WORKFLOW.md
circuit/agent-task-examples.md
circuit/checks/README.md
circuit/generated/preflight.json
circuit/publication/assets.json
circuit/publication/selection.json
circuit/templates/README.md
circuit/templates/cad-asset-receipt.json
circuit/templates/cad-asset-receipt.md
circuit/templates/project-docs/architecture/interfaces.mdx
circuit/templates/project-docs/architecture/overview.mdx
circuit/templates/project-docs/decisions/decision.mdx
circuit/templates/project-docs/decisions/sourcing.mdx
circuit/templates/project-docs/project/change-impact.mdx
circuit/templates/project-docs/project/index.mdx
circuit/templates/project-docs/project/next-actions.mdx
circuit/templates/project-docs/project/task-request.mdx
circuit/templates/project-docs/research/component-candidate.mdx
circuit/templates/project-docs/verification/bring-up.mdx
doc/package.json
doc/pages/docs/[[...slug]].tsx
doc/pages/index.tsx
doc/pages/lib/_circuit-doc-islands.ts
doc/public/favicon-16x16.png
doc/public/favicon-32x32.png
doc/public/favicon.ico
doc/public/favicon.svg
doc/scripts/check-links.js
doc/src/chrome-bindings.tsx
doc/src/content/docs/architecture/index.mdx
doc/src/content/docs/architecture/overview.mdx
doc/src/content/docs/components/catalog/index.mdx
doc/src/content/docs/components/index.mdx
doc/src/content/docs/components/integration/index.mdx
doc/src/content/docs/components/records/index.mdx
doc/src/content/docs/decisions/index.mdx
doc/src/content/docs/project/how-we-work.mdx
doc/src/content/docs/project/index.mdx
doc/src/content/docs/project/next-actions.mdx
doc/src/content/docs/research/index.mdx
doc/src/content/docs/verification/index.mdx
doc/src/styles/global.css
doc/tsconfig.json
doc/zfb.config.ts
package.json
pnpm-workspace.yaml
```

`pnpm install` additionally creates `pnpm-lock.yaml` at the root (must be committed; CI uses
`--frozen-lockfile`).

**Not generated:** `boards/`, `symbols/`, `footprints/`, `manufacturing/`, `.github/`, any
`wrangler.*`, any deploy configuration.

### Generated root `package.json` scripts (exact)

| Script | Command |
| --- | --- |
| `dev` | `pnpm --dir doc dev` |
| `build` | `zudo-circuit-doc models && zudo-circuit-doc generate && pnpm --dir doc build` |
| `check` | `zudo-circuit-doc check && pnpm --dir doc check` |
| `circuit:check` | `zudo-circuit-doc validate` |
| `circuit:generate` | `zudo-circuit-doc generate` |
| `circuit:doctor` | `zudo-circuit-doc doctor` |
| `check:site` | `zudo-circuit-doc check-built && zudo-circuit-doc scan && pnpm --dir doc check:links -- --strict-anchors --strict-broken` |
| `previews:generate` | `zudo-circuit-doc footprints generate` |

Root: `private: true`, `type: module`, `packageManager: pnpm@11.5.2`, `engines.node >=22.18.0`,
one devDependency `@takazudo/zudo-circuit-doc: ^0.1.0`.

`doc/package.json` scripts: `dev` (generate, then `run-parallel dev:zfb dev:history dev:circuit`),
`build` (`zfb build`), `preview`, `check` (`zfb check`), `check:links`, `dev:zfb`, `dev:zfb:network`,
`dev:network`, `dev:history` (port 4322), `dev:circuit` (generate `--watch`).

`pnpm-workspace.yaml`: `packages: ["doc"]`, `minimumReleaseAge: 0`, `allowBuilds.esbuild: true`.

### Runtime CLI surface (`zudo-circuit-doc 0.1.0`)

| Command | Flags |
| --- | --- |
| `generate` | `--watch` |
| `check` | — |
| `validate` | `--online`, `--refresh-source <id>…`, `--json` |
| `models` | `--check` |
| `footprints generate\|check` | `--pull` |
| `scan` | `--agent-skill <dir>` |
| `check-built` | — |
| `check-browser` | `--dist <dir>`, `--representatives <json>`, `--chrome <bin>`, `--shell-assertions`, `--search-assertions` |
| `doctor` | — |
| `new-component <suffix>` | `--dry-run` |

Global: `--config <path>` (default `./circuit.config.ts`), `--help`, `--version`.
Exit codes: `0` pass, `1` check failed, `2` usage/config error, `4` not run (optional tool missing).

### Tool requirements, and what this machine has

| Tool | Requirement | This machine |
| --- | --- | --- |
| Node | >=22.18.0 (required) | v24.13.1 |
| pnpm | 11.5.2 via `packageManager` (required) | shim reports 10.30.3 outside a project, **11.5.2 inside** the generated project |
| Python | >=3.10 stdlib (required; override with `CIRCUIT_DOC_PYTHON`) | 3.12.3 |
| git | required for history/initial commit | 2.43.0 |
| Docker + pinned KiCad image | optional, `footprints generate` only | Docker 29.3.0 present; image not needed while CAD is disabled |
| Chrome / `CHROME_BIN` | optional, `check-browser` only | `/usr/bin/google-chrome` |
| easyeda2kicad | optional | present |
| `kicad-cli` / KiCad (host) | not used by the framework | **not installed on this host** |
| wrangler | not used by the framework | 4.72.0 on PATH (upstream pins 4.85.0 via npx) |

## WORKFLOW.md is a 361-line agent contract with seven workflows and six verdicts

Source: `circuit/WORKFLOW.md` in the generated project. `CLAUDE.md` and `AGENTS.md` are thin pointers
to it (3 bullets each).

**Shared entry (every task):** read `project/index.mdx` and `project/next-actions.mdx`; read the
inventory and relevant owner bundles; run `pnpm circuit:check` **before** editing and note what
already fails; route by exact manufacturer + complete MPN + supplier order code + project role;
keep a work note for multi-step tasks.

**Evidence bundles (v1 contract).** One owner bundle per exact component or group at
`.claude/skills/component-<suffix>/`, created with `pnpm exec zudo-circuit-doc new-component <suffix>`.
Eight files:

| File | Role |
| --- | --- |
| `manifest.json` | record identity, parentage, assigned source/fact/interaction IDs |
| `sources.json` | authority, availability, revision, URL, hash, locator, retained extract |
| `facts.json` | typed claims: value, unit, conditions, provenance, verdict, calculation deps |
| `coverage.json` | declared domain coverage, reasons, `blocking_fact_ids` |
| `routing.json` | positive/negative routing cases |
| `interactions.json` | component-level interaction knowledge |
| `pin-map.json` | source-backed pin identity and project mapping (symbol pin, footprint pad, net) |
| `SKILL.md` | bundle entry instructions |

The template ships deliberate placeholder values; the validator fails on any left behind.

**Inventory.** `.claude/skills/component-spec-audit/references/inventory.json`, manual profile: one
line per orderable identity; unique `line_id` plus unique (manufacturer, complete MPN); `lcsc`
required but may be `""` and must never be fabricated; `suppliers` optional and display-only;
`placements` may be `[]` and are **declared, not verified**. `pnpm circuit:check` prints a `SCOPE:`
line that must be repeated in reports. Observed on the empty scaffold:

```
SCOPE: inventory provider=manual; schematic/placement binding not performed (0 lines, 0 declared placements unverified); pin-asset check not performed: cad disabled
SKIP: pin-asset check not performed: cad disabled
PASS: component-spec contract; 0 lines; offline=True; refreshed=none
```

**Generator-owned tree (never hand-edit):**

- `doc/src/content/docs/components/**` — catalog, record and integration pages
- `circuit/generated/preflight.json`
- `doc/public/assets/component-previews/**` — footprint SVGs and published WRL models
- `node_modules/@takazudo/zudo-circuit-doc/` (package-owned)

A hand-edited generated file is reported as drift by `pnpm check`; one with its marker removed is an
ownership conflict and the emitter refuses to overwrite it.

**Authored doc sections (five defaults):** `project`, `architecture`, `research`, `decisions`,
`verification` under `doc/src/content/docs/`. Only `project/` (with `index.mdx` and
`next-actions.mdx`) is load-bearing; the other four may be renamed or dropped. A new section needs a
content directory with `index.mdx`, a `headerNav` entry whose `categoryMatch` equals the directory
name, and a slot under the **6-item top-level header-nav cap** (all 6 are already used: Project,
Architecture, Research, Decisions, Verification, Components), so a new section must nest as a
`children` entry or replace one.

**Public-asset allowlist.** `circuit/publication/assets.json`
(`{ schema_version: 1, assets: [{ path, reason, source_id? }] }`, path relative to `doc/public`). The
scaffold lists only `favicon.svg`. The public-scope check fails on any file under `doc/public/` with
a restricted extension that is neither under `assets/component-previews/` nor allowlisted.
Restricted extensions (from `src/scan/public-scope.ts`):

```
.pdf .step .stp .kicad_mod .kicad_sym .kicad_pcb .kicad_sch .kicad_pro .kicad_prl
.zip .7z .json .wrl .svg .stl .3mf .obj .glb .gltf
.gbr .gtl .gbl .gto .gbo .gts .gbs .gtp .gbp .gko .gm1 .drl .xln .csv
```

Not restricted: `.png`, `.jpg`, `.html`, `.txt`, `.webp`. Symlinks under `doc/public` are always a
violation.

**Publication selection lock.** `circuit/publication/selection.json` lists `recordIds`, `sourceIds`,
`linkableSourceIds`, `documentSelections` and `expect` counts (`records`, `sources`,
`integrationRules`, `packages`), all zero at scaffold time. Adding evidence does not publish it.
Selection and allowlist edits happen in the same task as the evidence change.

**Six verdicts, spelled exactly:**

| Verdict |
| --- |
| `PASS - primary-source confirmed` |
| `CONFIRMED - distributor identity only` |
| `BLOCKER - deterministic spec violation` |
| `NEEDS BENCH` |
| `UNSOURCED` |
| `NOT APPLICABLE` |

Provenance values (separate field): `PRIMARY-SPEC`, `DISTRIBUTOR-IDENTITY`, `REFERENCE-DESIGN`,
`CALCULATED`, `PROJECT-CHOICE`, `BENCH-OBSERVED`, `UNVERIFIED`. An unavailable source carries
availability `SOURCE UNAVAILABLE` and the zero-hash sentinel (64 zeros). Source locators record both
a 0-based `physical_pdf_page_index` and a `printed_page_label`.

**Workflows:** A start a circuit; B add or replace an exact component; C find/download a source;
D obtain symbol, footprint and 3D model; E verify a specification; F record a bench result;
G handle a source or design change. Every task ends with a four-part completion report: obtained or
checked / exact identity / changed / remaining.

## The doc site lives in `doc/`, not at the repo root

The repo root is a pnpm workspace root whose only member is `doc`. `circuit.config.ts` sets
`docs.root: "doc"`, `docs.generatedContent: "doc/src/content/docs/components"`,
`docs.publicRoot: "doc/public"`, `docs.dist: "doc/dist"`.

| Path | Owner |
| --- | --- |
| `doc/src/content/docs/{project,architecture,research,decisions,verification}/` | Project |
| `circuit/WORKFLOW.md`, `circuit/agent-task-examples.md`, `circuit/templates/` | Project |
| `.claude/skills/component-*/` and the `references/*.json` files | Project (following the contract) |
| `circuit/publication/selection.json`, `assets.json` | Project (reviewed diff) |
| `circuit/cad-receipts/` | Project (created with the first asset) |
| `circuit.config.ts`, `doc/zfb.config.ts` | Project |
| `doc/src/**` outside `content/docs/components/` | Project |
| `doc/public/**` except `assets/component-previews/` | Project (subject to the allowlist) |
| Root `package.json` scripts | Project (the seam for pre-build steps and deploy hooks) |
| `doc/src/content/docs/components/**` | **Generator** |
| `circuit/generated/preflight.json` | **Generator** |
| `doc/public/assets/component-previews/**` | **Generator** |
| `node_modules/@takazudo/zudo-circuit-doc/` | **Package** |

Git-ignored by the scaffold: `node_modules`, `doc/dist`, `doc/.zfb`, `doc/.zfb-build/`,
`.zudo-doc/`, `.circuit-cache/`, and zudo-doc's generated
`doc/src/content/docs/{claude,claude-md,claude-commands,claude-skills,claude-agents}/`.

There is no `update` command. The runtime upgrades through `pnpm update`; the vendored zudo-doc host
glue is refreshed by hand following `ZUDO_DEPS_PINS.md` (pinned `create-zudo-doc` commit
`50cbd5c6c9e5a795d72a74a855e105e4939d4eab`, v5.27.0).

## The framework has no schematic, PCB, netlist or BOM support

What the framework knows about KiCad, exhaustively:

| Capability | Exists? | Where |
| --- | --- | --- |
| Read `.kicad_sym` symbol pins | Yes, text regex | `python/circuit_evidence/cad.py` (`\(number\s+"..."`) |
| Read `.kicad_mod` footprint pads | Yes, text regex | same file (`\(pad\s+...`) |
| Pin-map vs symbol vs footprint parity check | Yes, only when `cad.enabled: true` | `validate_pin_assets`; requires symbol pin == footprint pad number |
| Footprint SVG preview | Yes, via Docker `kicad-cli fp export svg` | `src/footprint-previews/generate.ts`; image `kicad/kicad@sha256:e638b79b…` KiCad 9.0.9, `linux/amd64` |
| 3D model web viewer | Yes, **WRL only** | `src/islands/package-model-viewer-island.tsx` (three 0.185.1) |
| Master footprint dir and `.pretty` dir byte-identity | Yes | checked with the config's two roots |
| Size limits | Yes | footprint 512 KiB, model 2 MiB, aggregate models 8 MiB |
| `.kicad_sch` rendering or parsing | **No** | the extension appears only in the restricted-extensions list |
| `.kicad_pcb` rendering or parsing | **No** | same |
| `.kicad_pro` handling | **No** | same |
| Netlist binding / ERC / DRC | **No** | `SCOPE:` line says "schematic/placement binding not performed" |
| BOM / CPL / Gerber export | **No** | "No manufacturing export profile" (limitations page) |
| STEP viewer or STEP->WRL conversion | **No** | limitations page |
| Host `kicad-cli` invocation | **No** | the only `kicad-cli` call runs inside the Docker container |

Counts from grep over runtime source: `kicad_sch` 1 file, `kicad_pcb` 1 file, `kicad-cli` 1 file,
`sch export` 0, `pcb export` 0, `gerber` 0.

The second inventory profile, `led-generator-v1`, binds inventory lines to zudo-led-lamp's `schgen`
Python generator specs (`COMPONENTS`, `EXTERNAL_COMPONENTS`, `NETS`, `PROJECT_NAME` parsed by a
restricted AST interpreter, never executed). It is LED-specific; it requires an LCSC C-number for
every PCB line and is only usable if this project adopts the same spec-file format.

### Where KiCad sources are expected to live

**Nothing is defined for schematics or boards.** The generated-project reference says verbatim:
"Not generated: `boards/`, `symbols/`, `footprints/`, `manufacturing/`, any LED-specific value, or
deploy configuration of any kind."

The only convention is for **libraries**, by example (`examples/minimal/circuit.config.ts`):

```ts
cad: {
  enabled: true,
  libraryName: "<lib>",
  symbolLibraries: ["symbols/<lib>.kicad_sym"],
  footprintMasterRoot: "footprints/kicad",
  footprintLibraryRoot: "footprints/kicad/<lib>.pretty",
  modelRoot: "footprints/kicad/<lib>.3dshapes",
  modelLocatorPrefix: "${KIPRJMOD}/../../footprints/kicad/<lib>.3dshapes/",
  previewRenderer: DEFAULT_PREVIEW_RENDERER,
}
```

The `${KIPRJMOD}/../../` prefix implies KiCad project directories sit two levels below the repo
root, which matches the siblings: `zudo-led-lamp/boards/board-l/board-l.kicad_{pro,sch,pcb}` and
`zudo-pd/boards/board-a/`. So `boards/<board>/<board>.kicad_{pro,sch,pcb}` is the de facto layout,
inherited from zudo-led-lamp, not enforced by the framework.

Constraint that matters for reusing zudo-pd parts: every config path must be relative to
`circuit.config.ts`, must not be absolute, must not contain `..`, and a project-escaping or
symlinked footprint/model root is rejected. **Libraries from zudo-pd cannot be referenced in place;
they have to be copied into this repo** with a CAD asset receipt.

## The template ships no deploy configuration; the domain is set in two project-owned files

Grep of the template for `wrangler|cloudflare|siteUrl|workers.dev|pages.dev` returns nothing.
The template's `doc/zfb.config.ts` sets `base: "/"` (required: the package's asset URLs are
root-absolute) and **no `siteUrl`**. Upstream states: "The initializer and runtime do not configure
deployment."

The domain is set in two places, which must agree:

1. `doc/zfb.config.ts` -> `zudoDoc({ siteUrl: "https://zudo-osc-hole-field.zudolab.dev" })`
   (zudo-doc 5.27.0 `siteUrl?: string`, "Canonical site origin").
2. `doc/wrangler.toml` -> `[[routes]] pattern = "zudo-osc-hole-field.zudolab.dev"`, `custom_domain = true`.

Reference implementations:

| | upstream monorepo `doc/wrangler.toml` | zudo-led-lamp `doc/wrangler.toml` |
| --- | --- | --- |
| Kind | pure static assets | worker + assets |
| `main` | omitted | `./dist/_worker.js` |
| `compatibility_flags` | omitted | `["nodejs_compat"]` |
| zfb adapter | none | `@takazudo/zfb-adapter-cloudflare` |
| `workers_dev` | `false` | `true` (needed for PR preview aliases) |
| `preview_urls` | not set | `true` |
| `[assets]` | `directory = "./dist"`, `not_found_handling = "404-page"` | same plus `binding = "ASSETS"`, `run_worker_first = false` |
| Domain | `zudo-circuit-doc.zudolab.dev` | `zudo-led-lamp.takazudomodular.com` |
| Wrangler | 4.85.0 pinned in the workflow | read from `doc/package.json` devDependencies |

The generated project's build output is fully static: `doc/dist/` has **no `_worker.js`** (verified),
so the upstream monorepo's static-assets config is the matching model. `zudo-circuit-doc.zudolab.dev`
answers HTTP 200 today, which proves the `zudolab.dev` zone works with this pattern.
`zudo-osc-hole-field.zudolab.dev` does not resolve yet.

Upstream's deploy workflow (`.github/workflows/main-deploy.yml`): checkout with `fetch-depth: 0`
(doc history needs full git history), setup pnpm + Node 24, build, upload `doc/dist` as an artifact,
`npx wrangler@4.85.0 deploy --config doc/wrangler.toml` with secrets `CLOUDFLARE_API_TOKEN` and
`CLOUDFLARE_ACCOUNT_ID`, then three smoke gates with retry through the first-deploy DNS/cert
window (`scripts/smoke-url.sh`, 10 attempts x 15 s). Token scopes stated upstream: Workers Scripts
Edit, Workers Routes Write and DNS Edit for the `zudolab.dev` zone.

## No sibling project consumes zudo-circuit-doc

| Sibling | Manifest | `@takazudo/zudo-circuit-doc` | `@takazudo/zudo-doc` | `@takazudo/zfb` | pnpm |
| --- | --- | --- | --- | --- | --- |
| `zudo-led-lamp` (HEAD 194d8a2, 2026-09-25) | `doc/package.json` only, no root manifest | **none** | `^5.27.0` | `2.20.2` | 10.34.1 |
| `zudo-case` (HEAD 69d56e4, 2026-09-27) | root `package.json` | **none** | `^5.27.0` | `2.20.2` | not pinned |
| `zudo-pd` (HEAD 797a221, 2026-08-16) | `doc/package.json` only | **none** | `^5.5.1` | `^2.5.1` | 11.5.2 |

`git grep -l zudo-circuit-doc` returns nothing in any of the three. No `circuit.config.ts` and no
`circuit/WORKFLOW.md` exist in any sibling.

zudo-led-lamp is the **origin** of the framework, not a consumer: it still runs its own in-repo
generator under `doc/component-docs/` (scripts such as `generate:components`,
`generate:footprint-previews`, `scan:artifacts`). zudo-circuit-doc was extracted from it, and
`fixtures/led/` in the monorepo is a hash-locked copy of 329 led-lamp files. **zudo-osc-hole-field
will be the first real consumer of the published packages.**

Consequence for "model on zudo-led-lamp": copy its content structure, deploy workflow shape and
KiCad directory layout; do not copy its `doc/component-docs/` generator, its script graph, or its
zfb 2.20.2 pins.

## The published 0.1.0 scaffold installs, builds and passes every check on this machine

All runs used the published npm packages in the explorer's scratch directory.

| Step | Result |
| --- | --- |
| `node <tarball>/bin/create-zudo-circuit-doc.js <new dir> --no-git --no-install` | exit 0, 60 files |
| `pnpm create zudo-circuit-doc@0.1.0 <new dir> ...` | exit 0, tree byte-identical |
| `npx --yes --package=create-zudo-circuit-doc@0.1.0 create-zudo-circuit-doc <new dir> ...` | exit 0, tree byte-identical |
| Same against a directory containing only `.git` | **exit 1, refused** |
| Copy scaffold into a simulated repo (git init + empty `init` commit), `pnpm install` | 120 packages, 2.6 s, pnpm 11.5.2 |
| `pnpm circuit:doctor` | every required item ok; kicad image `n/a` (cad disabled) |
| `pnpm circuit:check` | PASS, 0 lines |
| `pnpm circuit:generate` | 4 generated pages, 0 written / 4 unchanged |
| `pnpm check` | passed, `zfb check` no errors |
| `pnpm build` (through `heavy-guard.sh`) | 21 pages in 3.07 s, `verdict=PASS` |
| `pnpm check:site` | passed; 534 internal links, 70 ids |
| `doc/dist` | 4.9 MB, 39 files, no `_worker.js`, no `sitemap.xml` |
| Add `siteUrl` only, rebuild, `pnpm check:site` | build ok, check:site **passed** |
| Add `siteUrl` + `sitemap: true` | build ok, `pnpm check:site` **FAILED** (see below) |
| `wrangler deploy --dry-run --config doc/wrangler.toml` (static-assets config, wrangler 4.72.0) | exit 0, "No bindings found", `--dry-run: exiting now.` |

## The handoff overlay breaks the build in two places and enabling a sitemap breaks the scan

Tested by applying the handoff's `install_resources.py --apply` to a scratch copy of the scaffold.
The handoff directory itself was only read.

Overlay size: 147 writes = 144 new files + 3 edits (`project/index.mdx`,
`project/next-actions.mdx`, `circuit/publication/assets.json`). New files: 45 MDX pages, 15 files
under `doc/public/assets/osc-playground/`, the rest under root-level `project/osc-playground/` and
`research/osc-playground/`. No collision with any scaffold file. After import the five authored
sections hold: project 5, architecture 17, research 26, decisions 2, verification 3 MDX files.
All 45 payload MDX files use only `title` and `sidebar_position` frontmatter, no imports and no
JSX components.

### Failure 1 — HTML comment markers are invalid MDX

The installer appends this to `project/index.mdx` and `project/next-actions.mdx`:

```
<!-- osc-playground-r21-handoff:start -->
```

`pnpm circuit:check` and `pnpm check` still pass, but `pnpm build` fails:

```
MDX compile error in .../doc/src/content/docs/project/index.mdx: markdown parse error:
57:2: Unexpected character `!` (U+0021) before name ... (note: to create a comment in MDX, use `{/* text */}`)
✗ error: bundler step failed
```

Replacing the two markers with `{/* ... */}` fixed it: build then produced 81 pages in 5.61 s,
search index 61 entries, `doc/dist` 22 MB / 114 files.

### Failure 2 — `workbench.html` trips the strict link check

```
=== Broken Links in Built HTML ===
  dist/assets/osc-playground/workbench.html:245  ${esc(x.url)}
❌ STRICT FAIL: 1 broken link (after allowlist).
```

`workbench.html` (2,995,815 bytes) is a self-contained app under `doc/public`; line 245 holds a JS
template literal that the scanner reads as an href. `zudo-circuit-doc check-built` and
`zudo-circuit-doc scan` both pass on the same build. The vendored `doc/scripts/check-links.js`
supports `--allowlist=PATH` with entries of the form `<file>:<line>:<href>`. Verified: an allowlist
file containing `dist/assets/osc-playground/workbench.html:245:${esc(x.url)}` makes the check exit 0.
The line number is part of the key, so regenerating the workbench invalidates the entry.

### Failure 3 — a populated sitemap is a hard scan failure in runtime 0.1.0

With `sitemap: true` in `doc/zfb.config.ts`:

```
[PUBLICATION_POLICY] sitemap has entries; enabling it is a separate publication decision
  offenders:
    dist/sitemap.xml
```

Source: `assertSitemapUnchanged` in `packages/circuit-doc/src/scan/artifacts.ts`. `ScanPolicyConfig`
has no field to permit it. The upstream monorepo's own site sets `sitemap: true`, but that site does
not run `zudo-circuit-doc scan`. For a generated project, `sitemap` must stay off.

## Stale or wrong handoff integration instructions

| # | Handoff statement | Status | Correct value |
| --- | --- | --- | --- |
| 1 | Project name `zudo-osc-playground`; wrapper hardcodes `--name zudo-osc-playground --title zudo-osc-playground --library zudo_osc_playground` | **Stale** (owner renamed) | `zudo-osc-hole-field`; `bootstrap_project.py` cannot be used unmodified |
| 2 | "do not infer registry publication from a package.json version"; tarball fallback via `--initializer-script` + `--runtime-tarball` | **Obsolete** | Both packages are live on npm at 0.1.0; no local build/pack is needed |
| 3 | "The repository README still labels development status" | True but misleading | README and both package READMEs still say "under construction"; the generated project's own `README.md` still ends with a "Package status … not yet published on npm" section. Both are wrong as of 2026-09-27 |
| 4 | `python3 bootstrap_project.py /absolute/path/to/zudo-osc-playground --run` against the project directory | **Will fail** | The repo directory contains `.git`; both the wrapper and the initializer refuse it |
| 5 | `install_resources.py --apply` then `pnpm build` | **Breaks the build** | HTML comment markers are invalid MDX (Failure 1) |
| 6 | `pnpm check:site` after import | **Fails** | `workbench.html` false positive (Failure 2) |
| 7 | Payload paths `project/osc-playground/`, `research/osc-playground/`, `doc/public/assets/osc-playground/`, pages `osc-overview.mdx`, `osc-next-actions.mdx` | Stale naming | 40 of 144 payload text files mention "playground"; 24 occurrences inside the doc MDX. Rename is a plan decision |
| 8 | Requirements Node >=22.18.0, pnpm 11.5.2, Python >=3.10, zudo-doc 5.27.0, zfb 2.21.0 | **Correct** | matches `upstream-snapshot.json` and the published template |
| 9 | Flags `--no-git --no-install --agent both --yes`, `--runtime-spec file:<absolute>` | **Correct** | all exist with those semantics |
| 10 | "five authored doc sections" | **Correct** | project, architecture, research, decisions, verification |
| 11 | "An empty generated component catalogue is valid" | **Correct** | verified: 0 records passes every check |
| 12 | Reviewed commit `5d0e2b6…`, initializer 0.1.0 | **Correct and current** | it is `main` HEAD |
| 13 | Handoff uses `npx --yes --package=create-zudo-circuit-doc@0.1.0 create-zudo-circuit-doc` | Works | Upstream now documents `pnpm create zudo-circuit-doc <dir>`; both produce identical trees |
| 14 | Nothing in the handoff about deploy, `siteUrl`, wrangler or CI | Gap | the plan must add all of it |
| 15 | `publication-assets-to-add.json` lists 15 files | Consistent | the installer allowlists the same 15, including the non-restricted `.png`, `.html`, `.txt` (harmless) |

Doc section names and paths that the installer depends on all exist in the 0.1.0 scaffold:
`circuit.config.ts`, `circuit/WORKFLOW.md`, `package.json`, `circuit/publication/assets.json`,
`doc/src/content/docs/project/index.mdx`, `doc/src/content/docs/project/next-actions.mdx`.

## Recommended initialization procedure

Verified end to end on a simulated copy of the target repo, except steps marked UNVERIFIED.

```sh
# 0. Preconditions (all satisfied on this machine)
node -v            # >= 22.18.0
python3 --version  # >= 3.10

# 1. Work on a branch, not on main (global git rule)
cd "$HOME/repos/circuits/zudo-osc-hole-field"
git switch -c <topic-branch>

# 2. Scaffold into a fresh directory OUTSIDE the repo. The initializer refuses the repo itself
#    because it contains .git. The basename sets the default package name.
STAGE="$(mktemp -d)"
pnpm create zudo-circuit-doc@0.1.0 "$STAGE/zudo-osc-hole-field" \
  --name zudo-osc-hole-field \
  --title "zudo-osc-hole-field" \
  --library zudo-osc-hole-field \
  --agent both --yes --no-git --no-install

# 3. Copy the 60 scaffold files into the repo (dotfiles included, .git untouched)
cp -a "$STAGE/zudo-osc-hole-field/." "$HOME/repos/circuits/zudo-osc-hole-field/"

# 4. Install and record the baseline
cd "$HOME/repos/circuits/zudo-osc-hole-field"
pnpm install            # resolves pnpm 11.5.2 from packageManager; writes pnpm-lock.yaml
pnpm circuit:doctor
pnpm circuit:check
pnpm circuit:generate
pnpm check
bash "$HOME/.claude/scripts/heavy-guard.sh" -- pnpm build
pnpm check:site

# 5. Commit the untouched scaffold as its own commit before any edit,
#    so later diffs against upstream stay readable.
```

Then, as separate commits:

6. Edit `doc/zfb.config.ts`: add `siteUrl: "https://zudo-osc-hole-field.zudolab.dev"`. Do **not**
   add `sitemap: true`.
7. Delete the stale "Package status" section from the generated `README.md`.
8. Import handoff content **without** running `install_resources.py --apply` unmodified: copy the
   payload files, add the two links to `project/index.mdx` and `project/next-actions.mdx` by hand
   (no HTML comments), and add the restricted-extension assets to
   `circuit/publication/assets.json`.
9. Make `check:site` pass with the workbench: either add
   `--allowlist=<file>` to the root `check:site` script, or keep `workbench.html` out of
   `doc/public`.
10. Add `doc/wrangler.toml` (static-assets form) and the deploy workflow only when the owner is
    ready; the user said static-assets serving comes later.

UNVERIFIED: step 2's `--library zudo-osc-hole-field` choice against the siblings' KiCad library
naming (zudo-pd uses `symbols/zudo-pd.kicad_sym`, which suggests hyphenated names are the house
convention); the actual Cloudflare deploy; `pnpm dev`; `zudo-circuit-doc check-browser`;
`footprints generate` with the Docker image.

## Risks and blockers

| # | Risk | Severity | Mitigation |
| --- | --- | --- | --- |
| R1 | Initializer refuses the repo directory (`.git` present) | Blocker if unplanned | Scaffold into a temp dir and copy in (verified) |
| R2 | Handoff installer writes HTML comments into MDX; `pnpm build` fails | Blocker | Hand-apply the two links or use `{/* */}` |
| R3 | `workbench.html` fails strict link check | Blocker for `check:site` | `--allowlist` entry (fragile line number) or move the file |
| R4 | `sitemap: true` fails `zudo-circuit-doc scan` | Medium | Leave sitemap off; `siteUrl` alone is safe |
| R5 | Framework has no schematic/PCB/netlist/BOM features | High for scope | KiCad authoring, ERC/DRC, rendering and BOM are entirely project-built; the doc site can only show them as images or allowlisted files |
| R6 | No host KiCad / `kicad-cli` on this machine | High for goals 2 and 3 | Use the pinned Docker image `kicad/kicad` 9.0.9 (Docker 29.3.0 is present) or install KiCad; decide before planning ERC/DRC steps |
| R7 | Every KiCad export placed under `doc/public` needs an allowlist entry (`.svg`, `.pdf`, `.json`, `.csv`, `.kicad_*`, Gerbers, `.step`, `.wrl`) | Medium | One allowlist edit per asset in the same task; prefer `.png` for plain images |
| R8 | 6-item header-nav cap is already full | Low | Nest new sections (for example boards/panel) as `children` |
| R9 | `claudeResources` publishes the repo's `.claude/` tree and root `CLAUDE.md` on the public site (build log: "1 CLAUDE.md, 0 commands, 2 skills") | Medium, repo is public | Keep anything private out of `.claude/` and `CLAUDE.md`; project-specific agent notes added there become public pages |
| R10 | 180 jacks + 144 controls + ICs means a very large evidence inventory if every part is promoted | High for effort | Promote by exact part number, not by placement; one bundle covers all placements of the same MPN. Catalogue may legitimately stay empty at first |
| R11 | zudo-pd libraries cannot be referenced across repos | Medium | Copy into `symbols/` and `footprints/kicad/` with CAD receipts |
| R12 | 3D models must be WRL, each <= 2 MiB, aggregate <= 8 MiB | Medium | Budget early; many jack/pot models will hit the aggregate cap (override via `cad.limits`) |
| R13 | First real consumer of a one-day-old 0.1.0 release | Medium | Expect upstream defects; report with `/dev-upstream-report`. Already found: stale "Package status" README section in the published template |
| R14 | `minimumReleaseAge: 0` disables pnpm's supply-chain delay | Low | Known upstream trade-off; revisit later |
| R15 | Local upstream checkout is 7 commits behind | Low | `git pull` in `$HOME/repos/myoss/zudo-circuit-doc` before using it as a reference |
| R16 | CI must check out full history (`fetch-depth: 0`) for doc history, and needs Node >= 22.18 | Low | Copy the upstream setup action (Node 24) |
| R17 | Target repo has no Actions secrets | Blocks deploy only | Owner adds `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` when serving is set up |

## Open decisions with recommended defaults

| # | Decision | Recommended default |
| --- | --- | --- |
| D1 | How to scaffold into a repo that already has `.git` | Temp-dir scaffold + copy; `--no-git --no-install` |
| D2 | `--title` | `zudo-osc-hole-field` (matches the led-lamp site name style) rather than the auto title `Zudo Osc Hole Field` |
| D3 | `--library` (KiCad library name) | `zudo-osc-hole-field`, hyphenated like `zudo-pd` |
| D4 | `--agent` | `both` (the owner runs Claude Code and Codex; this run hands off with `-toco`) |
| D5 | Use the handoff's `bootstrap_project.py` / `install_resources.py` | No. Call the published initializer directly and import the payload by hand |
| D6 | Rename payload paths and slugs from `osc-playground` to `osc-hole-field` | Yes, in one dedicated commit right after import, before anything links to them |
| D7 | `siteUrl` now, deploy later | Set `siteUrl` in the scaffold phase; add `doc/wrangler.toml` and the workflow in a later, separate issue |
| D8 | Deploy shape | Static assets only (upstream monorepo form: no `main`, no adapter, `workers_dev = false`). Add the adapter and preview aliases only if PR previews are wanted |
| D9 | `sitemap` | Off until upstream adds a scan-policy switch |
| D10 | `cad.enabled` | Keep `false` for the scaffold; flip to `true` in the issue that adds the first symbol/footprint library |
| D11 | Inventory profile | `manual`. `led-generator-v1` only if the schematic is generated from schgen-style spec files with LCSC numbers for every part |
| D12 | KiCad source layout | `boards/<board>/<board>.kicad_{pro,sch,pcb}`, `symbols/<lib>.kicad_sym`, `footprints/kicad/<lib>.pretty`, `footprints/kicad/<lib>.3dshapes` (matches led-lamp and the `${KIPRJMOD}/../../` prefix) |
| D13 | Where schematic/PCB/panel pages go | Under `architecture/` (design) and `verification/` (ERC/DRC reports); add a nested `boards` section only if the volume demands it |
| D14 | How to show schematics and boards on the site | Exported PNG for inline display; SVG/PDF only with allowlist entries |
| D15 | KiCad toolchain for ERC/DRC and exports | The Docker image already pinned by the framework (KiCad 9.0.9), so host and CI agree |
| D16 | Workbench HTML under `doc/public` | Keep it, with a link-check allowlist file committed beside `doc/scripts/` |
| D17 | Report the stale README section upstream | Yes, via `/dev-upstream-report` during implementation |

## Files read

- `$HOME/repos/myoss/zudo-circuit-doc` (local, HEAD 491f151): `README.md`, `AGENTS.md`, `CLAUDE.md`, `package.json`, `pnpm-workspace.yaml`
- Remote clone at `5d0e2b6`: `dev-docs/{README,decisions,publishing,site-deploy}.md`; `doc/wrangler.toml`, `doc/zfb.config.ts`, `doc/package.json`; `.github/workflows/main-deploy.yml`, `.github/actions/setup/action.yml`; `scripts/smoke-url.sh`
- `packages/create-zudo-circuit-doc/`: `package.json`, `README.md`, `CHANGELOG.md`, `bin/`, `src/{args,cli,git,help,install,next-steps,plan,prompt,scaffold,validate}.ts`, `templates/default/**`
- `packages/circuit-doc/`: `package.json`, `CHANGELOG.md`, `src/config/define.ts`, `src/cli/{help.ts,commands/index.ts,commands/doctor.ts,commands/scan.ts}`, `src/scan/{public-scope,policy,artifacts}.ts`, `python/circuit_evidence/{cad.py,inventory/manual.py,inventory/led_generator_v1.py}`
- `doc/src/content/docs/`: `getting-started/{create-a-project,requirements,limitations,generated-project}.mdx`, `concepts/{publication,ownership-and-upgrades,inventory-profiles,cad-fidelity}.mdx`, `reference/{generated-project,capability-matrix,config}.mdx`, `workflows/migrate-existing-project.mdx`
- `examples/minimal/{circuit.config.ts,README.md}`
- Handoff (read only): `README.md`, `START_HERE.md`, `LOCAL_AGENT_PROMPT.md`, `UPSTREAM-INTEGRATION.md`, `VALIDATION.md`, `bootstrap_project.py`, `install_resources.py`, `publication-assets-to-add.json`, `payload/project/osc-playground/{upstream-snapshot,handoff-provenance}.json`
- Siblings: `zudo-led-lamp/doc/{package.json,wrangler.toml,zfb.config.ts}`, `.github/workflows/`; `zudo-case/package.json`; `zudo-pd/doc/package.json`

Skimmed only: `fixtures/led/**` (329 upstream files, hash-locked), `packages/circuit-doc/test*/**`,
`scripts/**` beyond `smoke-url.sh`, `dev-docs/{extraction-baseline,scenario-matrix}.md`.
