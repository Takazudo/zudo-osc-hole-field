# 04 - Handoff docs, installer scripts, rename blast radius

Explorer 04 of 9. Exploration only. Nothing was written to the target repo, the handoff directory, or any sibling repo.
All executions ran on copies inside the session scratch dir.

- Handoff (read-only source): `$DROPBOX_CCLOGS_DIR/zudo-osc-hole-field/handoff-r21/zudo-osc-playground-r21-handoff`
- Target repo: `$HOME/repos/circuits/zudo-osc-hole-field` (contains only `.git/`)
- Framework checkout used for cross-checks: `$HOME/repos/myoss/zudo-circuit-doc`
- Date of probes: 2026-09-28

---

## 1. Handoff is intact: 161 files, 159 hashed, 0 mismatches

| Item | Value |
|---|---|
| Files on disk | 161 |
| Entries in `SHA256SUMS.json` | 159 (`files` map: path -> sha256) |
| Excluded from manifest (by its own `excluded` list) | `SHA256SUMS.json`, `reports/handoff-tests.json` |
| Hash mismatches | 0 |
| Payload files (`payload/**`) | 144, 21.52 MB |
| `payload/doc/public/assets/osc-playground/` | 15 files |
| `payload/doc/src/content/docs/` | 45 MDX |
| `payload/project/osc-playground/` | 75 files (10 top-level + 65 under `workbench/`) |
| `payload/research/osc-playground/` | 9 files |
| Root scripts | `install_resources.py`, `bootstrap_project.py`, `publish_workbench.py`, `verify_handoff.py`, `acquire_sources.py` |
| Root docs | `README.md`, `START_HERE.md`, `LOCAL_AGENT_PROMPT.md`, `UPSTREAM-INTEGRATION.md`, `VALIDATION.md` |
| `payload/project/osc-playground/VALIDATION-HANDOFF.md` | byte-identical to root `VALIDATION.md` |
| `publication-assets-to-add.json` | informational only; no script reads it (its `reason` text differs from what the installer writes) |

Largest files: `workbench/index.html` 2.86 MB and its byte-identical public copy `workbench.html` 2.86 MB,
`studies/screenshot-comparison.png` 1.77 MB, `vendor/three.core.js` 1.34 MB, `reference/user-jack-grid.png` 1.31 MB.

11 of the 15 public assets are byte-identical duplicates of workbench files (the `publish_workbench.py` pairs).

---

## 2. All five validation suites pass on this machine (run on a scratch copy)

Every one of these scripts WRITES a report file, so none is read-only. They must never be run inside the Dropbox handoff directory.

| Command (run in scratch copy) | Result here | Writes |
|---|---|---|
| `python3 verify_handoff.py` | **67 handoff checks passed** | `reports/handoff-tests.json` (check order differs from shipped file, same 67 check names) |
| `python3 -m unittest discover -s tests -v` | **10/10 OK** | `__pycache__/` dirs only |
| `python3 scripts/validate.py` | **45 structural checks passed** | `workbench/reports/structural-tests.json` (byte-identical to shipped) |
| `node scripts/test_logic.cjs` | **15 logic tests passed** | `workbench/reports/logic-tests.json` (byte-identical) |
| `node scripts/test_slew.cjs` | **18 SLEW model tests passed** | `workbench/reports/slew-tests.json` (byte-identical) |
| `xvfb-run -a python3 scripts/test_browser.py` | **NOT RUN** - python `playwright` module missing | would rewrite `panels/panel.svg`, 6 PNGs, 2 mechanical JSONs, 2 report JSONs |
| `python3 scripts/export_proofs.py` | **NOT RUN** - fails at `import cairosvg` (ModuleNotFoundError) | would rewrite panel PNG/PDF, 5 study SVG+PNG pairs, comparison PNG, PDF proof |
| Official `pnpm install` / `circuit:check` / `build` with the payload | **NOT RUN** (would install packages) | - |
| ngspice on `slew-ideal.cir` | **NOT RUN** - `ngspice` not installed | - |

After running the five suites, `diff -rq` between pristine and run copy showed only `reports/handoff-tests.json` and two `__pycache__` directories.

### Rebuild is byte-deterministic for the text pipeline

Running `prepare_data.py` -> `build.py` -> `render_static.cjs` on a pristine scratch copy reproduced **byte-identical**
`layout/grid.json`, `layout/changes.json`, `index.html` (2,995,815 bytes), `panels/panel.svg`, `panels/square-grid.svg`, `panels/grid-proof.svg`.
The five `studies/*.svg` crops are also reproducible with stdlib only (the `crop()` code path in `export_proofs.py` minus rasterization): all five matched the shipped files byte for byte.

---

## 3. `install_resources.py` is a create-only overlay: 144 creates + 3 edits, dry run by default

Usage: `python3 install_resources.py <target> [--apply]`. Payload root is fixed to `<script dir>/payload`.

### 3.1 Destination paths in the host project

Payload relative paths are preserved verbatim under the target root.

| Destination in host | Files | Notes |
|---|---|---|
| `doc/public/assets/osc-playground/` | 15 | workbench.html, panel.{svg,png}, panel-1to1.pdf, slew-controls.{svg,png}, slew-path.{svg,png}, slew-response.{svg,png}, control-grid.png, assembly.png, boards.png, exploded.png, THREE-LICENSE.txt |
| `doc/src/content/docs/architecture/` | 15 | `osc-*.mdx` |
| `doc/src/content/docs/decisions/` | 1 | `osc-scope-freeze.mdx` |
| `doc/src/content/docs/project/` | 2 | `osc-overview.mdx`, `osc-next-actions.mdx` |
| `doc/src/content/docs/research/` | 25 | 3 `osc-*.mdx` + 22 `part-*.mdx` |
| `doc/src/content/docs/verification/` | 2 | `osc-release-gates.mdx`, `osc-slew-test-plan.mdx` |
| `project/osc-playground/` | 75 | NEW top-level `project/` dir: specs, contracts, `kicad-sheet-plan.json`, full `workbench/` (src, scripts, vendor three.js, reports, studies) |
| `research/osc-playground/` | 9 | NEW top-level `research/` dir: candidates, sources queue, slew calc/traces, `slew-ideal.cir` |
| `project/osc-playground-import-log/<UTC stamp>/` | 4 | only on `--apply`: `receipt.json` + `before/` copies of the 3 edited host files |

Edited (not created) host files - exactly three:

1. `doc/src/content/docs/project/index.mdx` - append-links block
2. `doc/src/content/docs/project/next-actions.mdx` - append-links block
3. `circuit/publication/assets.json` - allowlist entries

### 3.2 Append-links behaviour

Appends `text.rstrip() + "\n\n" + block + "\n"` to the END of each of the two host pages. The block is:

```
<!-- osc-playground-r21-handoff:start -->

## zudo-osc-playground handoff

[Oscillator playground R21 project brief](./osc-overview.mdx). Read this project-specific handoff after the canonical circuit workflow.

<!-- osc-playground-r21-handoff:end -->
```

(second page: `[Oscillator playground local next actions](./osc-next-actions.mdx)`).

- If the BEGIN marker is absent: append.
- If the BEGIN marker is present and the exact block string is present: no-op.
- If the BEGIN marker is present but the exact block is not: abort `Managed link block changed; reconcile manually`.
- Everything above the block is preserved. On a fresh scaffold this leaves the template's placeholder brief (tables full of `Not entered`) in place with the link block under it.

### 3.3 Public-asset allowlist mutation

- Requires `schema_version == 1` and `assets` to be a list, else aborts `Unknown publication allowlist schema; not upgraded automatically`.
- For each of the 15 files under `payload/doc/public`, appends `{"path": "assets/osc-playground/<file>", "reason": "R21 authored oscillator-playground preview / diagram / print proof. Not approved component CAD or manufacturing evidence."}` when the path is not already listed.
- Existing entries are kept in order (template ships one: `favicon.svg`). Result on a fresh scaffold: 16 entries.
- The whole file is re-serialized with `json.dumps(indent=2, ensure_ascii=False)` + newline.
- Verified against runtime source (`packages/circuit-doc/src/scan/public-scope.ts`): only files with restricted extensions need an entry. Of the 15 assets, **5 are restricted** (`.pdf` x1, `.svg` x4); the 10 `.png`/`.html`/`.txt` entries are harmless surplus. Entry shape `{path, reason}` satisfies `readAssets()` in `config/map.ts` (path must be relative, no `..`; reason non-empty).

### 3.4 Preconditions and refusal conditions

| # | Condition | Message |
|---|---|---|
| 1 | Target path is itself a symlink | `Target itself must not be a symlink` |
| 2 | Any of 6 files missing: `circuit.config.ts`, `circuit/WORKFLOW.md`, `package.json`, `circuit/publication/assets.json`, `doc/src/content/docs/project/index.mdx`, `doc/src/content/docs/project/next-actions.mdx` | `Not a complete initialized circuit-doc host: missing <rel>` |
| 3 | `@takazudo/zudo-circuit-doc` not in root `package.json` dependencies or devDependencies | `Official runtime dependency absent; refusing to treat an arbitrary folder as a host` |
| 4 | `payload/` missing | `Missing payload ...` |
| 5 | Any symlink inside payload | `Symlink in payload ...` |
| 6 | Payload path under `doc/src/content/docs/components/`, `doc/public/assets/component-previews/`, `.claude/`, `node_modules/`, `circuit/generated/` | `Generator/evidence-owned path in overlay` |
| 7 | Destination exists and is not a byte-identical regular file | `Collision; existing file preserved: <rel>` |
| 8 | Any path component between target and destination is a symlink, or path escapes target | `Symlink not accepted` / `Path escapes project` |
| 9 | Managed link block edited (3.2) | `Managed link block changed; reconcile manually` |
| 10 | Allowlist schema unknown (3.3) | `Unknown publication allowlist schema` |
| 11 | On `--apply`: any observed file changed between plan and apply | `Concurrent change: <rel>` |

All refusals happen before the first write. Writes are atomic (temp file + fsync + `os.replace`). On an exception mid-apply, created files are unlinked and edited files restored; created directories and `before/` copies stay behind.

### 3.5 Observed behaviour against real paths (dry runs only)

| Run | Result |
|---|---|
| `install_resources.py $HOME/repos/circuits/zudo-osc-hole-field` (dry run, read-only) | **Refused**: `Not a complete initialized circuit-doc host: missing circuit.config.ts` (exit 1) |
| Dry run against a scratch host scaffolded by the published initializer 0.1.0 | `Identical files skipped: 0`, `Files to create/update: 147` (144 CREATE + 3 LINK/ALLOWLIST); host unchanged |
| `--apply` against a second scratch host | succeeded; import log written; `assets.json` 1 -> 16 entries |
| Second dry run after apply | `Identical files skipped: 144`, `Files to create/update: 0` |

This matches the shipped `reports/full-payload-import.json` (`write_count: 147`, `repeat_writes: 0`), now reproduced on a REAL scaffold rather than the synthetic host.

### 3.6 The installer is one-shot

Idempotence is byte equality. As soon as any imported file is edited in the repo (any MDX touch-up, any workbench rebuild), re-running the installer aborts on rule 7. After import the repo copy is the authority.

---

## 4. `bootstrap_project.py` cannot be used as shipped: wrong names, and it refuses the target repo

What it executes with `--run` (without `--run` it only prints the command):

```
npx --yes --package=create-zudo-circuit-doc@0.1.0 create-zudo-circuit-doc <ABS_DEST> \
  --name zudo-osc-playground --title zudo-osc-playground --library zudo_osc_playground \
  --agent both --yes --no-git --no-install
```

- `--initializer-script <path>` swaps the front for `node <resolved script>`.
- `--runtime-tarball <path>` appends `--runtime-spec file:<abs path>`.
- `--version` defaults to `0.1.0`.
- Node gate (only with `--run`): `node -p process.versions.node` must be `>= 22.18.0`.
- Destination gate: must be nonexistent or an EMPTY directory.

Observed (read-only dry run): `python3 bootstrap_project.py $HOME/repos/circuits/zudo-osc-hole-field` ->
`Destination must be nonexistent or empty. For an existing host use install_resources.py only.` (exit 1).
Cause: the repo contains `.git/`, and `any(dst.iterdir())` counts it.

The official initializer has the same rule. `packages/create-zudo-circuit-doc/src/scaffold.ts` `checkDestinationCollision()` uses `fs.readdirSync()` and throws
`Cannot create project: "<dest>" already exists and is not empty.` There is no force flag.

Consequences for the plan:

1. The three names are hard-coded to the OLD project name. Do not run this script with `--run` as shipped.
2. The scaffold must be produced in an empty temp directory and then moved into the repo working tree (or scaffolded into a new empty directory that then receives the existing `.git/`).

### Published packages exist and match the reviewed commit

| Probe | Result |
|---|---|
| `npm view create-zudo-circuit-doc` | versions `["0.1.0"]`, `latest: 0.1.0` |
| `npm view @takazudo/zudo-circuit-doc` | versions `["0.1.0"]`, `latest: 0.1.0` |
| Reviewed commit `5d0e2b630776489d394be341586b889dfe0d1cb8` | exists on GitHub; it IS current `main` HEAD (compare: identical, ahead 0 / behind 0), committed 2026-09-27T11:15:27Z |
| Local checkout `$HOME/repos/myoss/zudo-circuit-doc` | HEAD `491f151e...` on `main`; does NOT contain the reviewed commit (checkout is behind remote) |
| Published initializer tarball vs local checkout `templates/default` | `diff -rq` empty: identical template |
| Initializer run in scratch with NEW names (`--name zudo-osc-hole-field --title zudo-osc-hole-field --library zudo_osc_hole_field --agent both --yes --no-git --no-install`) | exit 0, 60 files created |

The handoff's claim that the registry path was unverified is now resolved: both packages are on npm at 0.1.0.

### Scaffold facts that the payload depends on

From the scratch scaffold (`doc/zfb.config.ts`, root `package.json`, `circuit.config.ts`):

- `base: "/"` - required by the payload's root-absolute `/assets/...` links.
- `defaultLocale: "en"`, no other locales.
- `siteName` = the `--name` value. No `siteUrl`, no `wrangler.toml`, no Cloudflare adapter dependency in the template. The domain `zudo-osc-hole-field.zudolab.dev` has to be added by the plan.
- `packageManager: pnpm@11.5.2`, `engines.node >= 22.18.0`.
- `cad: { enabled: false, libraryName: "<--library value>" }`.
- Host doc sections: `project`, `architecture`, `research`, `decisions`, `verification`, `components` (generated). Same five authored sections the payload targets.
- Host `.gitignore` ignores `*.log` and `doc/dist`, not `project/` or `research/`.

---

## 5. Other root scripts

### `publish_workbench.py [project] [--apply]`

Copies 11 named files from `<project>/project/osc-playground/workbench/` to `<project>/doc/public/assets/osc-playground/` using `shutil.copyfile` (overwrites, no collision guard). Default `project` = the handoff's own `payload/`. Dry run by default.

| Source (under `workbench/`) | Public name |
|---|---|
| `index.html` | `workbench.html` |
| `panels/panel.svg`, `panels/panel.png`, `panels/panel-1to1.pdf` | same names |
| `studies/utility-controls.svg` / `.png` | `slew-controls.svg` / `.png` |
| `studies/control-grid.png`, `studies/assembly.png`, `studies/boards.png`, `studies/exploded.png` | same names |
| `vendor/THREE-LICENSE.txt` | same name |

Not covered: `slew-path.svg`, `slew-path.png`, `slew-response.svg`, `slew-response.png`. **No script in the handoff generates these four files.** They are one-off authored diagrams with no source.

### `verify_handoff.py`

67 checks: grid invariants (180 ports equal to R20, 142 prior controls equal, exactly `C:H1.SLEW`/`C:H2.SLEW` added at (7,6)/(7,7), 144 cells occupied, kinds `pot 101 / octave 5 / switch 30 / button 8`), payload hygiene (no `components/`, no `.claude/`, no `circuit.config.ts`, no `package.json`), public workbench == workbench index, all JSON parses, all public SVG parses, exactly 45 MDX, frontmatter per page, all MDX links resolve, four workbench reports pass, no invented source hashes, no fonts/`.pyc`, manifest hashes match.
Hard-codes `osc-playground` in 5 places. Writes `reports/handoff-tests.json`.

### `acquire_sources.py --output <dir> [--ids ...] [--run]`

Reads `payload/research/osc-playground/sources.json` (11 records, 10 with URLs; authority split: MANUFACTURER_PRIMARY 4, REFERENCE-DESIGN 4, DISTRIBUTOR_IDENTITY 2, PROJECT-CHOICE 1). Without `--run` prints id + URL and creates nothing (verified). With `--run` downloads each URL (30 s timeout, 25 MB cap, `User-Agent: zudo-osc-playground-source-acquisition/1.0`), requires `%PDF-` magic for ids `LF398`, `OPA4197`, `PTV09`, writes content-addressed files and `receipts-<stamp>.json`. Status is `DOWNLOADED_NOT_AUDITED` or `SOURCE_UNAVAILABLE`.

### `tests/test_installer.py`

10 tests on temp hosts: dry run read-only, authored text + allowlist preserved, idempotent, collision aborts, unknown host rejected, generated path rejected, symlink escape rejected, concurrent change rejected, modified managed block rejected, WORKFLOW/package.json never changed. Hard-codes `osc-playground` in 4 places and `Oscillator playground R21` in 1.

---

## 6. The 45 MDX pages are plain English Markdown with zero component usage

| Property | Finding |
|---|---|
| Language | English only. 0 CJK characters in all 45 files. Non-ASCII limited to typographic symbols (dash, multiply, plus-minus, micro, ohm, degree). |
| Total words | 7,677 |
| Frontmatter keys used | `title`, `sidebar_position` only. No `description`, no `sidebar_label`, no tags. |
| `import` statements | 0 |
| JSX components | 0 |
| Raw HTML tags | 0 |
| Unescaped `{`, `}`, or `<` outside code | 0 (scanned; the only `<suffix>` is inside an inline code span) |
| Body `# H1` | 0 pages; page title comes from frontmatter |
| Markdown features | `##` headings, paragraphs, GFM tables (2 pages), fenced code `sh` / `text` (3 pages), 1 image, ordered list (1 page) |
| Internal `.mdx` links | 3, all in `project/osc-overview.mdx` |
| Root-absolute asset links | 3 (`workbench.html` x2, `slew-path.svg` image x1) |
| External links | 48 across 12 hosts (jlcpcb.com 19, ti.com 9, github.com 5, thonk.co.uk 3, bourns.com 3, lcsc.com 2, electricdruid.net 2, st.com, samtec.com, alldatasheet.com, addacsystem.com, tech.alpsalpine.com 1 each) |
| Titles using a `—` escape inside a double-quoted YAML string | 36 of 45 |
| Sidebar position collisions with host template pages | none (host uses 1, 2, 3, 10; payload uses 18-51) |

### Host-framework dependencies (all implicit, none via components)

1. Relative `.mdx` link resolution (`../project/osc-next-actions.mdx` style). The host template uses the same style.
2. `base: "/"` for `/assets/osc-playground/...`.
3. GFM tables.
4. Content schema: `description` is `z.string().optional()` in `@takazudo/zudo-doc` 5.27.0 (`dist/docs-schema/index.js:15`), so pages without it validate. Every host template page and 85 of 95 lamp pages do carry `description`.
5. YAML escape handling for `—` in titles. zudo-doc depends on the `yaml` package; how zfb parses frontmatter is UNVERIFIED. No precedent for `\u` escapes exists in the lamp docs or the template.

### Only 2 of 15 public assets are referenced by any page

| Asset | Referenced from |
|---|---|
| `workbench.html` | `project/osc-overview.mdx`, `research/osc-components.mdx` |
| `slew-path.svg` | `architecture/osc-sample-hold-slew.mdx` (image) |
| other 13 (panel.svg/png/pdf, slew-controls, slew-response, slew-path.png, control-grid, assembly, boards, exploded, THREE-LICENSE) | no page |

### Page list

#### project (2)

| File | pos | Title | Purpose |
|---|---|---|---|
| `osc-overview.mdx` | 20 | zudo-osc-playground - project handoff | Baseline, scope (module counts, 180 jacks / 144 controls), mechanical intent, pointers to next work |
| `osc-next-actions.mdx` | 21 | Next actions - local agent | First-session steps, documentation pass rules, 6-step engineering sequence |

#### architecture (15)

| File | pos | Title | Purpose |
|---|---|---|---|
| `osc-sample-hold-slew.mdx` | 20 | S&H + SLEW - implementation proposal | LF398 + separate buffered RC lag; B504 500k, Rmin 2.2k, C 0.5 uF; tau 1.1-251.1 ms |
| `osc-board-stack.mdx` | 21 | Board partition and panel stack | Panel-first datum, interface boards + rear core, what is not locked, sensitive nodes |
| `osc-grid-authority.mdx` | 22 | Grid and artifact authority | `grid.json` is the single source; regeneration command list; SLEW centres (133.5,269)/(133.5,283) mm |
| `osc-blocks.mdx` | 23 | Module contracts and circuit capture plan | Points to `block-contracts.json` and `kicad-sheet-plan.json`; what to freeze before values |
| `osc-power.mdx` | 24 | Power reuse and startup boundary | Reuse zudo-pd Board P + B; 15 V-only PD state; budget from captured circuit |
| `osc-block-osc.mdx` | 40 | OSC - circuit task | AS3340D candidate oscillator, 6-position octave, 4 waveforms; instantiate 5 |
| `osc-block-vcf.mdx` | 41 | VCF - circuit task | Dry VCA OUT + LP/BP/HP; instantiate 3 |
| `osc-block-mix5.mdx` | 42 | MIX5 - circuit task | Five bipolar attenuverters to mono sum + LEVEL |
| `osc-block-mix4.mdx` | 43 | MIX4 - circuit task | Four attenuverters, sum, post-sum VCA |
| `osc-block-ar.mdx` | 44 | AR - circuit task | ASR/AR/LOOP envelope, ENV/BIP/EOC/STG outs; instantiate 6 |
| `osc-block-fold.mdx` | 45 | FOLD - circuit task | Wavefolder with FOLD CV and BIAS CV |
| `osc-block-ao.mdx` | 46 | AO - circuit task | Attenuverter + offset, gain -1..+1 |
| `osc-block-mult.mdx` | 47 | MULT - circuit task | 1 input, 3 buffered outputs |
| `osc-block-switch.mdx` | 49 | SWITCH - circuit task | Manual maintained A/B selector |
| `osc-block-noise.mdx` | 50 | NOISE - circuit task | White/pink/blue/brown buffered outputs |

All ten `osc-block-*` pages share one template: `Functional contract` / `Work before schematic lock` / `Deliverable`.

#### decisions (1)

| File | pos | Title | Purpose |
|---|---|---|---|
| `osc-scope-freeze.mdx` | 20 | R21 scope freeze and retained decisions | Layout frozen; what must not be revived; accepted vs proposed |

#### verification (2)

| File | pos | Title | Purpose |
|---|---|---|---|
| `osc-release-gates.mdx` | 20 | Readiness gates - no premature manufacturing release | 7-row gate table; no Gerber/BOM/CPL authorized |
| `osc-slew-test-plan.mdx` | 21 | S&H and slew bench plan | Coupon definition and 10-row test matrix |

#### research (25)

| File | pos | Title | Purpose |
|---|---|---|---|
| `osc-documentation-integration.mdx` | 18 | Integrating the official circuit documentation runtime | Upstream commit, file ownership, evidence promotion, command list |
| `osc-components.mdx` | 19 | Component research intake | 22-row register rules; 99 + 2 pots; toggle counts 19 / 11 |
| `osc-slew-evidence.mdx` | 20 | SLEW evidence and limitations | Candidate identities, LF398 leakage numbers, source receipt boundary |
| `part-bourns-ptv09a-4020f-b504.mdx` | 30 | PTV09A-4020F-B504 | C5154140; 2 SLEW pots |
| `part-fh-c0g-100n-slew.mdx` | 31 | 1206CG104J500NT | C46348; lag capacitor bank, 10 pcs |
| `part-ti-lf398m.mdx` | 32 | LF398M/NOPB | LCSC C1346172; 2 S&H cells |
| `part-ti-hc221.mdx` | 33 | CD74HC221M96 | C133954; one-shot for both triggers |
| `part-ti-lm393.mdx` | 34 | LM393DR | C67470; trigger conditioning |
| `part-kemet-hold-10n.mdx` | 35 | C0805C103J5GACTU | C2167597; hold capacitor candidate, 2 pcs |
| `part-ti-opa4197.mdx` | 36 | OPA4197IPWR | C2057327; MULT + SLEW buffers, 3 quads proposed |
| `part-ti-tmux6111.mdx` | 37 | TMUX6111PWR | alternative S&H topology, not fitted |
| `part-dailywell-2ms1.mdx` | 38 | 2MS1T1B1M2QES-5 | C908280; 2-position toggles, 19 pcs |
| `part-dailywell-2ms3.mdx` | 39 | 2MS3T1B1M2QES / Thonk DW2 | 3-position toggles, 11 pcs; no JLC number |
| `part-omron-b3f1020.mdx` | 40 | B3F-1020 | C722171; 8 buttons |
| `part-bourns-ptv09a-4020f-b103.mdx` | 41 | PTV09A-4020F-B103 | C5848782; 99 continuous positions, values pending |
| `part-alps-srbv160803.mdx` | 42 | SRBV160803 | C470374; 5 octave selectors |
| `part-qingpu-wqp518ma.mdx` | 43 | WQP518MA / Thonkiconn | C9900052034; 180 jacks |
| `part-kento-white.mdx` | 44 | KT-0603W | C2290; 104 indicator sites |
| `part-kento-red.mdx` | 45 | KT-0603R | C2286; 10 clip indicators |
| `part-st-tl074.mdx` | 46 | TL074CDT | C6963; general op-amp, qty circuit-dependent |
| `part-ti-lm13700.mdx` | 47 | LM13700M/NOPB | C1346265; MIX4 gain cells + filter/VCA |
| `part-alfa-as3340d.mdx` | 48 | AS3340D | 5 oscillator cores; no JLC number |
| `part-electric-druid-noise2.mdx` | 49 | NOISE2 | programmed noise source, 1 pc |
| `part-interconnects.mdx` | 50 | Exact keyed header + socket / harness set | board interconnect, unresolved |
| `part-zudo-pd.mdx` | 51 | Existing zudo-pd Board P + Board B | power supply assembly |

All 22 `part-*` pages share one template: `Identity and role` / `Current status` / `Qualification boundary` / `Sources to acquire`.

---

## 7. Rename blast radius: 206 text occurrences in 52 files, plus 3 directories and 8 rendered images

Counted by byte regex over all 161 files. `A + B + C + E + F = 206`, equal to the count of every case-insensitive `playground` match, so nothing else is hiding.

### 7.1 By pattern

| Code | Pattern | Count |
|---|---|---|
| A | `zudo-osc-playground` | 27 |
| B | `osc-playground` not preceded by `zudo-` | 159 |
| C | `zudo_osc_playground` | 2 |
| D | `osc_playground` not preceded by `zudo_` | 0 |
| E | `OSC PLAYGROUND` | 13 |
| F | `oscillator playground` / `oscillator-playground` (case-insensitive) | 5 |
| | **Total** | **206** |

### 7.2 By file class

| Class | Files | A | B | C | E | F | Total |
|---|---|---|---|---|---|---|---|
| MDX | 18 | 1 | 23 | 0 | 0 | 0 | 24 |
| JSON, excluding the SHA manifest | 7 | 3 | 16 | 1 | 0 | 1 | 21 |
| `SHA256SUMS.json` | 1 | 0 | 99 | 0 | 0 | 0 | 99 |
| Python | 7 | 5 | 15 | 1 | 0 | 4 | 25 |
| JS (`src/render.js`) | 1 | 0 | 0 | 0 | 1 | 0 | 1 |
| HTML (`src/shell.html`, `index.html`, `workbench.html`) | 3 | 8 | 0 | 0 | 2 | 0 | 10 |
| SVG | 10 | 0 | 0 | 0 | 10 | 0 | 10 |
| Markdown (`.md`) | 5 | 10 | 6 | 0 | 0 | 0 | 16 |
| **Total** | **52** | 27 | 159 | 2 | 13 | 5 | **206** |

### 7.3 By meaning (pattern B split, all 159)

| Meaning | Count | Where |
|---|---|---|
| Asset URL path `assets/osc-playground` | 39 | MDX 4, `publication-assets-to-add.json` 15, SHA manifest 15, Python 4, md 1 |
| Project dir `project/osc-playground` | 103 | MDX 17, SHA manifest 75, Python 6, md 4, `current-spec.json` 1 |
| Research dir `research/osc-playground` | 14 | MDX 2, SHA manifest 9, Python 2, md 1 |
| Import log dir `project/osc-playground-import-log` | 1 | `install_resources.py` |
| Managed-block marker `osc-playground-r21-handoff` | 2 | `install_resources.py` |

### 7.4 Directory and file paths

| Path | Files beneath |
|---|---|
| `payload/doc/public/assets/osc-playground/` | 15 |
| `payload/project/osc-playground/` | 75 |
| `payload/research/osc-playground/` | 9 |

99 of 161 file paths contain the old slug. No file BASENAME contains `playground`. Outside the archive, the extracted directory and zip are named `zudo-osc-playground-r21-handoff`.

### 7.5 MDX contents (24 occurrences in 18 of 45 files)

- 1 x title: `project/osc-overview.mdx` -> `title: "zudo-osc-playground — project handoff"`
- 3 x asset URL (2 links to `workbench.html`, 1 image `slew-path.svg`)
- 1 x inline code `doc/public/assets/osc-playground/` (`osc-grid-authority.mdx`)
- 17 x inline code `project/osc-playground/...` (11 of them are the `block-contracts.json` mention on block pages)
- 2 x inline code `research/osc-playground/...`

27 MDX files contain no old-name string at all (all 22 `part-*` pages among them).

### 7.6 JSON contents (excluding manifest)

| File | Occurrence | Rename? |
|---|---|---|
| `publication-assets-to-add.json` | 15 asset paths | yes |
| `payload/project/osc-playground/current-spec.json` | `layout_authority` path | yes |
| `payload/project/osc-playground/decisions.json` | D12 prose: "the oscillator playground" | yes |
| `payload/project/osc-playground/kicad-sheet-plan.json` | `"library": "zudo_osc_playground"` | yes |
| `workbench/layout/grid.json` | `"title": "zudo-osc-playground"` | yes, by regenerating |
| `workbench/reference/r20-grid.json` | `"title": "zudo-osc-playground"` | **NO** - retained R20 byte copy; its sha `d794483b...` is recorded in `handoff-provenance.json` |
| `payload/project/osc-playground/handoff-provenance.json` | `"name": "zudo-osc-playground-r20.zip"` | **NO** - historical archive name paired with a sha256 |

### 7.7 Python and JS scripts

| File | A | B | C | E | F | What |
|---|---|---|---|---|---|---|
| `install_resources.py` | 1 | 3 | | | 3 | markers x2, import-log dir, block heading, 2 link titles, allowlist reason |
| `bootstrap_project.py` | 2 | | 1 | | | `--name`, `--title`, `--library` values |
| `publish_workbench.py` | | 2 | | | | source dir, output dir |
| `verify_handoff.py` | | 5 | | | | payload paths |
| `acquire_sources.py` | 1 | 1 | | | | sources path, User-Agent |
| `tests/test_installer.py` | | 4 | | | 1 | fixture paths, asserted string |
| `workbench/scripts/prepare_data.py` | 1 | | | | | `title='zudo-osc-playground'` (line 67) |
| `workbench/src/render.js` | | | | 1 | | line 25: panel legend `'ZUDO / OSC PLAYGROUND'` |

### 7.8 Generated workbench HTML (3 MB, grep only)

`workbench/index.html` and its public copy `workbench.html` are byte-identical. Each holds 4 occurrences:

1. `<title>zudo-osc-playground · R21 grid workbench</title>`
2. `<h1>zudo-osc-playground</h1>`
3. `window.GRID_DATA={..."title":"zudo-osc-playground"...}`
4. `'ZUDO / OSC PLAYGROUND'` inside the inlined `render.js`

The base64-embedded three.js bundles and `src/three.js` contain none. `GRID_DATA.title` is never read by `app.js`, `render.js` or `three.js` - it is metadata only.

### 7.9 The panel artwork itself carries the old name

`render.js` line 25 draws a fixed legend at x = 8 mm, y = 9.2 mm, font-size 2.6 mm, weight 600: **`ZUDO / OSC PLAYGROUND`**.
This is a panel silk/copper text element, confirmed visually in `panel.png` and as extractable text in `panel-1to1.pdf`.

Text occurrences (10 SVG): `panels/panel.svg`, `panels/square-grid.svg`, `panels/grid-proof.svg`, `studies/{jack-grid,control-grid,utility-jacks,utility-controls,env-offset}.svg`, public `panel.svg`, public `slew-controls.svg`.

Rendered occurrences that grep cannot see:

| Image | Shows | Affected |
|---|---|---|
| `panels/panel.png` + public `panel.png` | legend, top-left | yes |
| `panels/panel-1to1.pdf` + public copy | legend as text (embedded font Arimo-Bold) | yes |
| `reports/pdf-proof.png` | rasterized PDF page | yes |
| `reports/desktop.png`, `mobile.png`, `split.png` | workbench header `zudo-osc-playground` | yes |
| `studies/assembly.png`, `exploded.png` + public copies | panel texture in 3D; legend present but illegible at that scale | technically yes |
| `studies/{jack-grid,control-grid,utility-*,env-offset}.png`, public `control-grid.png`, `slew-controls.png` | crops start at y >= 16 mm, below the legend | no |
| `reference/user-jack-grid.png` | owner's source screenshot, no project name | no |
| `slew-path.*`, `slew-response.*` | no name | no |

### 7.10 KiCad library name

`zudo_osc_playground` appears exactly twice: `bootstrap_project.py` (`--library`) and `kicad-sheet-plan.json` (`"library"`). It would also land in `circuit.config.ts` `cad.libraryName` via the initializer.

Sibling convention differs from the handoff's underscore form:

| Repo | Symbol library | Footprint library | lib-table nickname |
|---|---|---|---|
| `$HOME/repos/circuits/zudo-led-lamp` | `symbols/zudo-led-lamp.kicad_sym` | `footprints/kicad/zudo-led-lamp.pretty` | `zudo-led-lamp` |
| `$HOME/repos/circuits/zudo-pd` | `symbols/zudo-pd.kicad_sym` | `footprints/kicad/zudo-power.pretty` | `zudo-pd` |

The initializer accepts both (`^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$`) and defaults `--library` to `--name`.

### 7.11 SHA manifest

99 of the 159 keys in `SHA256SUMS.json` contain `osc-playground`. After a rename every one of those keys points at a path that no longer exists.

---

## 8. Recommended strategy: rename BEFORE import, in a working copy, rebuild generated files, issue a new manifest

### 8.1 Proof: the strategy was executed end to end in scratch

A scripted rename (Appendix A) on a copy of the handoff, followed by rebuild and a regenerated manifest:

| Step | Result |
|---|---|
| Directory renames | 3 |
| Text files edited | 36 files, 86 replacements |
| `prepare_data.py`, `build.py`, `render_static.cjs` | ran clean |
| Study SVG crops regenerated (stdlib) | 5 |
| `publish_workbench.py --apply` on the scratch payload | 11 copies refreshed |
| `validate.py` / `test_logic.cjs` / `test_slew.cjs` | 45 / 15 / 18 passed |
| `verify_handoff.py` with the OLD manifest | **fails** on the last check only: `AssertionError: All immutable delivery hashes match` |
| `verify_handoff.py` with a regenerated manifest | **67 passed** |
| `unittest` | 10/10 OK |
| Renamed installer `--apply` on a scratch scaffold | 147 writes, all under new paths |
| Residual old-name text after rename | 2, both intentional: `handoff-provenance.json` (archive name), `reference/r20-grid.json` (title) |
| `grid.json` keys that differ from the original | `title` only. `ports`, `controls`, `groups`, `blocks`, `presets` are value-identical |
| Byte deltas | `index.html` 36 bytes, each SVG 9 bytes, file lengths unchanged |
| Manifest comparison | 159 entries; 110 byte-identical content (79 of them path-only changes); 49 content changes |

Lengths are unchanged because the new strings are the same length as the old ones:
`zudo-osc-playground` and `zudo-osc-hole-field` are both 19 characters; `OSC PLAYGROUND` and `OSC HOLE FIELD` are both 14.
The panel legend therefore occupies the same width and the rename cannot disturb label spacing.

New `grid.json` sha256 after rename (scratch result): `b707f2fd04c23d08250026698cb3343254f04c1fd7a08c9f6bc36972c99df92a`
(original: `65230567c120b95389586e547d5364b798fb627d2762873b3de1eb42892fbca0`, which is also what `handoff-provenance.json` records as `current_grid_sha256`).

### 8.2 Why before, not after

1. Repo history never contains the old name or old paths. Renaming after import would mean `git mv` on 99 files, including about 21 MB of binaries.
2. Published URLs are correct from the first deploy (`/assets/osc-hole-field/...`).
3. The installer's safety net (collision check, allowlist, tests) keeps working because payload and scripts are renamed together.
4. The original installer and the renamed installer use different markers. If the ORIGINAL were ever applied to the real repo, a later renamed run would not recognise the old block and would append a second one, and old-named directories would sit beside new-named ones. The original installer must never touch the real repo.

### 8.3 Rebuild, do not sed-edit

| Artefact | Rebuild with | Runnable here today |
|---|---|---|
| `workbench/layout/grid.json`, `layout/changes.json` | `python3 scripts/prepare_data.py` | yes |
| `workbench/index.html` | `python3 scripts/build.py` | yes |
| `panels/panel.svg`, `square-grid.svg`, `grid-proof.svg` | `node scripts/render_static.cjs` | yes |
| `studies/*.svg` (5) | `export_proofs.py` | SVG part reproducible with stdlib; script itself needs cairosvg |
| `panels/panel.png`, `panels/panel-1to1.pdf`, `studies/*.png` (5 crops), `studies/screenshot-comparison.png`, `reports/pdf-proof.png`, `reports/pdf-check.json` | `python3 scripts/export_proofs.py` | **no** - cairosvg missing |
| `reports/desktop.png`, `mobile.png`, `split.png`, `studies/assembly.png`, `boards.png`, `exploded.png`, `reports/browser-tests.json`, `reports/text-ink.json`, `mechanical/*.json` | `xvfb-run -a python3 scripts/test_browser.py` | **no** - python playwright missing |
| Public copies (11) | `python3 publish_workbench.py <root> --apply` | yes |
| `reports/structural-tests.json`, `logic-tests.json`, `slew-tests.json` | the three check scripts | yes |
| Root `reports/*` | `verify_handoff.py`, `unittest` | yes |
| `SHA256SUMS.json` | regenerate | yes |

Edit by text replacement (authored sources): the 18 MDX files, 5 root `.md`, `VALIDATION-HANDOFF.md`, the 6 Python scripts + test, `prepare_data.py`, `src/render.js`, `src/shell.html`, `current-spec.json`, `decisions.json`, `kicad-sheet-plan.json`, `publication-assets-to-add.json`.

Never edit: `reference/r20-grid.json`, the `source_archive.name` value in `handoff-provenance.json`.

Re-rendered PNG/PDF will not be byte-identical to the shipped ones. The SVG asks for `Arial,Helvetica,sans-serif`; the shipped PDF embedded Arimo; this machine resolves to Liberation Sans. All three are metric-compatible, so text widths match but bytes and glyph shapes differ.

### 8.4 What happens to `SHA256SUMS.json` and the identity checks

- The pristine handoff stays immutable in cclogs as provenance. Its manifest remains valid for it.
- The renamed derivative gets a NEW manifest. The handoff's own `VALIDATION.md` requires this: "Intentional local edits and regenerated screenshots/reports will require a new review snapshot; do not force old hashes or weaken validation to hide changes."
- Add a `rename-provenance.json` next to `handoff-provenance.json` recording: old name, new name, old and new `grid.json` sha256, the statement that only `title` differs, and the old -> new path map with counts (110 identical content, 49 changed).
- Installer identity strings that must change together: BEGIN/END markers, block heading, two link titles, allowlist reason text, import-log directory. `tests/test_installer.py` asserts on the link title string (`Oscillator playground R21`), so test and installer must be edited in the same pass.
- The installer's 6-file host check and the runtime-dependency check are name-independent and need no change.

### 8.5 Keep the `osc-` page-slug prefix

- 23 pages carry it (architecture 15, decisions 1, project 2, research 3, verification 2). The 22 `part-*` pages do not.
- `osc` is still part of the new name, so the prefix stays meaningful.
- It prevents collisions with host template pages (`project/next-actions.mdx`, `architecture/overview.mdx`, the five `index.mdx`).
- Dropping it would change 23 URLs, 3 internal links, 2 installer link targets and the test fixture for no gain.

### 8.6 Proposed names

| Thing | Old | New |
|---|---|---|
| Repo / npm `--name` / `siteName` | `zudo-osc-playground` | `zudo-osc-hole-field` |
| Display title (`--title`, workbench `<title>` and `<h1>`, `grid.json` title) | `zudo-osc-playground` | `zudo-osc-hole-field` |
| Overview page title | `zudo-osc-playground — project handoff` | `zudo-osc-hole-field — project handoff` |
| Prose name | `Oscillator playground` / `the oscillator playground` | `OSC hole field` / `zudo-osc-hole-field` |
| Panel legend | `ZUDO / OSC PLAYGROUND` | `ZUDO / OSC HOLE FIELD` |
| Short slug | `osc-playground` | `osc-hole-field` |
| Public asset path | `doc/public/assets/osc-playground/` -> URL `/assets/osc-playground/` | `doc/public/assets/osc-hole-field/` -> `/assets/osc-hole-field/` |
| Project inputs dir | `project/osc-playground/` | `project/osc-hole-field/` |
| Research inputs dir | `research/osc-playground/` | `research/osc-hole-field/` |
| Import log dir | `project/osc-playground-import-log/` | `project/osc-hole-field-import-log/` |
| Managed-block markers | `<!-- osc-playground-r21-handoff:start/end -->` | `<!-- osc-hole-field-r21-handoff:start/end -->` |
| Acquisition User-Agent | `zudo-osc-playground-source-acquisition/1.0` | `zudo-osc-hole-field-source-acquisition/1.0` |
| KiCad library | `zudo_osc_playground` | `zudo-osc-hole-field` (sibling convention; see open decision 1) |
| Domain | - | `zudo-osc-hole-field.zudolab.dev` |
| Page slug prefix | `osc-` | `osc-` (unchanged) |
| Historical strings | `zudo-osc-playground-r20.zip`, `r20-grid.json` title | unchanged |

---

## 9. Workbench rebuild dependencies: text pipeline ready, raster and browser pipelines blocked

| Dependency | Needed by | Present | Detail |
|---|---|---|---|
| Python >= 3.10 | all `.py` | yes | 3.12.3 at `/usr/bin/python3` |
| Node | `render_static.cjs`, `test_logic.cjs`, `test_slew.cjs` | yes | v24.13.1 (nodenv); 22.22.0 and 22.22.2 also installed |
| Node >= 22.18.0 | official initializer / doc runtime | yes | same |
| pnpm 11.5.2 (template `packageManager`) | doc host | version differs | pnpm 10.30.3 on PATH; corepack 0.34.6 present |
| CairoSVG (python) | `export_proofs.py` | **no** | `ModuleNotFoundError`; system `libcairo.so.2` IS present |
| Pillow | `export_proofs.py` | yes | 12.2.0 |
| PyMuPDF (`fitz`) | `export_proofs.py` | yes | 1.27.2.3 |
| Playwright (python) | `test_browser.py` | **no** | `ModuleNotFoundError` |
| Chromium at `/usr/bin/chromium` (script default) | `test_browser.py` | **no** | override with env `CHROMIUM`; `/usr/bin/google-chrome` 146.0.7680.153 present; Playwright cache has `chromium-1208` ... `chromium-1243` |
| Xvfb / `xvfb-run` | `test_browser.py` (runs headed) | yes | `/usr/bin/xvfb-run` |
| Fonts for SVG raster | `export_proofs.py` | substitute | Liberation Sans, DejaVu Sans; no Arial, no Arimo |
| ngspice | `slew-ideal.cir` | **no** | not on PATH |
| `kicad-cli` / KiCad | goals 2 and 3 | **no** | not on PATH; no KiCad under `/mnt/c/Program Files`; python `pcbnew`, `kiutils`, `sexpdata` all missing |
| docker | possible KiCad container | yes | `/usr/bin/docker` |
| `uv`, `pip3` | installing python deps | yes | `$HOME/.local/bin` |

---

## 10. Defects and gaps found in the handoff

| # | Finding | Evidence |
|---|---|---|
| 1 | Four public diagrams have no generator | `slew-path.{svg,png}`, `slew-response.{svg,png}`: no script writes them; `publish_workbench.py` does not list them |
| 2 | 13 of 15 published assets are linked from no page | section 6 |
| 3 | Dangling reference | `workbench/mechanical/README.md` points to `../docs/MECHANICAL.md`; no `docs/` directory exists |
| 4 | Dangling reference | `workbench/datasheets/README.md` cites `parts/source-downloads.json` and "the retry script"; `parts/` holds only `components.json` |
| 5 | Validation scripts are not read-only | all five write report files; `test_browser.py` additionally overwrites `panels/panel.svg` |
| 6 | Host brief stays a placeholder after import | the installer only appends a link block under the template's `Not entered` tables |
| 7 | New top-level `project/` and `research/` directories | not part of the template or of any sibling repo layout |
| 8 | `publication-assets-to-add.json` is dead data | nothing reads it; its reason text differs from the installer's |
| 9 | No page has a `description` | all host template pages and 85 of 95 lamp pages do |

---

## Appendix A - scratch rename script (reference implementation, ran successfully)

Scratch location (session-scoped, may be gone): `<scratchpad>/04-handoff-docs-installer-rename/rename_sim.py`.

```python
#!/usr/bin/env python3
"""Rename a COPY of the handoff. argv[1] = copy root."""
import sys
from pathlib import Path
R=Path(sys.argv[1]).resolve()
OLD_DIR='osc-playground';NEW_DIR='osc-hole-field'
for d in ['payload/doc/public/assets','payload/project','payload/research']:
    (R/d/OLD_DIR).rename(R/d/NEW_DIR)
W=R/'payload/project'/NEW_DIR/'workbench'
PUB=R/'payload/doc/public/assets'/NEW_DIR
GENERATED={W/'index.html',W/'layout/grid.json',W/'layout/changes.json',
 W/'panels/panel.svg',W/'panels/square-grid.svg',W/'panels/grid-proof.svg',
 PUB/'workbench.html',PUB/'panel.svg',PUB/'slew-controls.svg',
 *(W/'studies').glob('*.svg')}
HISTORICAL={W/'reference/r20-grid.json',R/'SHA256SUMS.json'}
REPORTS=set((R/'reports').glob('*'))|set((W/'reports').glob('*'))
TEXT_EXT={'.mdx','.md','.py','.js','.cjs','.json','.html','.css','.csv','.cir','.txt'}
PROTECT='zudo-osc-playground-r20.zip'
SUBS=[('zudo_osc_playground','zudo_osc_hole_field'),   # or 'zudo-osc-hole-field', see open decision 1
      ('zudo-osc-playground','zudo-osc-hole-field'),
      ('oscillator-playground','osc-hole-field'),
      ('osc-playground','osc-hole-field'),
      ('OSC PLAYGROUND','OSC HOLE FIELD'),
      ('Oscillator playground','OSC hole field'),
      ('oscillator playground','OSC hole field')]
for p in sorted(R.rglob('*')):
    if not p.is_file() or p.suffix.lower() not in TEXT_EXT: continue
    if p in GENERATED or p in HISTORICAL or p in REPORTS or 'vendor' in p.parts: continue
    t=p.read_text();o=t
    t=t.replace(PROTECT,'\x00P\x00')
    for a,b in SUBS: t=t.replace(a,b)
    t=t.replace('\x00P\x00',PROTECT)
    if t!=o: p.write_text(t)
```

Follow-up sequence that was run after it, from `<copy>/payload/project/osc-hole-field/workbench`:

```sh
python3 scripts/prepare_data.py
python3 scripts/build.py
node scripts/render_static.cjs
python3 scripts/export_proofs.py          # needs cairosvg; NOT RUN here
xvfb-run -a python3 scripts/test_browser.py   # needs playwright; NOT RUN here
python3 scripts/validate.py
node scripts/test_logic.cjs
node scripts/test_slew.cjs
cd <copy>
python3 publish_workbench.py --apply
# regenerate SHA256SUMS.json (same schema: scope / excluded / files)
python3 verify_handoff.py
python3 -m unittest discover -s tests -v
```

## Appendix B - items not verified

- UNVERIFIED: that the official doc build (`pnpm install`, `circuit:check`, `build`, `check:site`) passes with the 45 pages and 15 assets. Nobody has run it, upstream or here.
- UNVERIFIED: how zfb parses the `—` escape in 36 titles.
- UNVERIFIED: effect of `strictContentBridge: true` on pages without `description`.
- UNVERIFIED: Cloudflare static-asset HTML handling for the raw `/assets/osc-hole-field/workbench.html` URL.
- UNVERIFIED: whether `boards.png` contains any legible legend (panel is hidden in that view; not inspected pixel by pixel).
- NOT RUN: `export_proofs.py`, `test_browser.py`, ngspice, any KiCad tool, `acquire_sources.py --run`, `bootstrap_project.py --run`.
