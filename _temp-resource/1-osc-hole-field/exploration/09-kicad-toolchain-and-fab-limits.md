# 09 — KiCad toolchain feasibility and fabrication limits

Explorer 09 of 9 for `zudo-osc-hole-field`. Probed 2026-09-28 on WSL2 Ubuntu 24.04.4 (kernel 6.18.33.2), node v24.13.1, python 3.12.3, 12 cores, 11 GB RAM.
Nothing was installed, pulled, committed or modified. All experiments ran on copies inside the scratch dir. `git status --porcelain` is empty for zudo-led-lamp, zudo-pd, zudo-case, zudo-osc-hole-field and zudo-circuit-doc after the run.

Legend: **VERIFIED** = I ran it or parsed the file. **UNVERIFIED** = not checkable from here.

---

## 1. Headless KiCad already works on this machine — but only KiCad 9.0.9, which cannot open the siblings' KiCad 10 files

| Probe | Result |
| --- | --- |
| `kicad-cli`, `kicad`, `ngspice`, `java`, `podman`, `flatpak`, `pipx` on PATH | not found |
| `python3 -c "import pcbnew"` (host) | `ModuleNotFoundError` |
| Windows-side KiCad (`/mnt/c/Program Files/KiCad`, `Program Files (x86)`, `AppData/Local/Programs`, `D:`), `where.exe kicad-cli` | not installed. WSL interop itself works (`where.exe` ran) |
| `docker` | 29.3.0, daemon running, buildx 0.31.1, compose 5.1.0, 386 GB free on `/var/lib/docker` |
| Local KiCad image | **`kicad/kicad@sha256:e638b79b0321f29395a5b783e94bb9f3c73303e8da15da27b8f5cb4b67a37729`** = Docker Hub tags `9.0.9` / `9.0`, created 2026-05-03, linux/amd64, 476 MB content. Untagged locally (pulled by digest) |
| Inside that image | `kicad-cli` 9.0.9, `python3` 3.11.2 with `pcbnew` 9.0.9 importable, `/usr/bin/ngspice` (ngspice-39), 224 stock symbol libs, 155 stock footprint libs, no 3D models, user `kicad` uid 1000, `KICAD_IPC_API=ON`, Debian 12 |
| `snap` | binary present, `snap list` prints nothing |
| `apt-cache policy kicad` | candidate `7.0.11+dfsg-1build4` (noble/universe) — two majors too old |
| KiCad PPA | `ppa:kicad/kicad-10.0-releases` serves `kicad 10.0.6~ubuntu24.04.1` for noble (HTTP 200) |
| `uv` | 0.10.2 (tools: whisper-ctranslate2, yt-dlp) |
| pip packages matching `kiutils\|skidl\|kicad\|sexp\|kinet` | only `easyeda2kicad 1.0.1`. Also present: `pillow 12.2.0`, `PyYAML 6.0.1`, `Jinja2 3.1.2`. Absent: kiutils, skidl, kinet2pcb, sexpdata, kicad-skip, atopile, kipy, numpy, shapely, gerbonara |
| `xvfb-run`, `gh` 2.87.3, `git-lfs` | present |
| `$HOME/.claude/skills` matching `kicad\|circuit\|pcb\|schematic\|jlc\|bom\|gerber` | **none** (91 skills, zero matches) |

### The local 9.0.9 image rejects KiCad 10 files (VERIFIED)

Copy of `zudo-led-lamp/boards/swd-adapter/*.kicad_sch|.kicad_pcb` run in the container:

```
kicad-cli sch export netlist ...  -> "Failed to load schematic"  exit=3
kicad-cli pcb drc ...             -> "Failed to load board"      exit=3
```

Rewriting only the header to `(version 20250114)` / `"9.0"` still fails. After also stripping the two KiCad-10-only tokens `in_pos_files` and `duplicate_pin_numbers_are_jumpers` the **schematic** loads in 9.0.9 (netlist exit 0, ERC runs). The **PCB** still fails after removing `duplicate_pad_numbers_are_jumpers` — the v10 board format differs further.

---

## 2. Siblings generate schematics from Python specs and verify with KiCad 10 on the Mac; CI never runs KiCad

### File-format versions in sibling headers (VERIFIED by parsing)

| File | version | generator |
| --- | --- | --- |
| `zudo-led-lamp/boards/{board-l,board-p,swd-adapter}/*.kicad_sch` | `20260306` | eeschema `10.0` |
| `zudo-led-lamp/boards/*/*.kicad_pcb` | `20260206` | pcbnew `10.0` |
| `zudo-led-lamp/symbols/zudo-led-lamp.kicad_sym` | `20251024` | kicad_symbol_editor `10.0` |
| `zudo-pd/boards/{board-a,board-b}/*.kicad_sch`, root `*.kicad_sch` | `20260306` | eeschema `10.0` |
| `zudo-pd/zudo-pd.kicad_pcb` (1.7 MB) | `20260206` | pcbnew `10.0` |
| `zudo-pd/symbols/zudo-pd.kicad_sym` | `20231120` | kicad_symbol_editor `8.0` |
| `zudo-pd/_old_usb-pd-input.kicad_sch` | `20250114` | eeschema `9.0` |
| `zudo-pd/experiments/.../circuit-synth-spike/*.kicad_sch` | `20250114` | circuit_synth `0.8.36` |
| `zudo-case/engineering/r6-body/source-data/panels/zb-side-frame-{3u,7u}/*.kicad_pcb` | `20260206` | pcbnew `10.0` |
| `zudo-case/.../zb-side-frame-pad-{1u,3u}/*.kicad_pcb` | `20240108` | pcbnew `8.0` |
| Footprints: led-lamp 62 `.kicad_mod` (60 headerless easyeda2kicad style, 2 at `20240108`); zudo-pd 118 (114 headerless, 4 at `20240108`) | | |

`zudo-led-lamp/manufacturing/jlcpcb/2026-09-19/manifest.json` records `kicad_version: 10.0.0`. Every command in `checks/commands.log` uses `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`.

### How the siblings run checks

- **Generator**: `scripts/schgen/` in both repos. `schgen_core.py` (led-lamp 239 lines, zudo-pd 298), `sexp.py` (48 / 73 lines, dependency-free tokenizer), per-board `*_spec.py` with `COMPONENTS`, `NETS`, `NO_CONNECT`. Emits header `version 20260306`, `generator "eeschema"`, `generator_version "10.0"`. Deterministic `uuid5` UUIDs.
- **Style**: flat single sheet, **0 wires**, one `global_label` per connected pin, `no_connect` markers. Measured: `zudo-pd/boards/board-b` 66 symbols / 177 global labels / paper A2; `zudo-led-lamp/boards/board-l` 69 symbols / 165 labels / A2.
- **Limits of the existing generator**: `(unit 1)` only — both symbol libraries contain zero multi-unit symbols; no hierarchical sheets; one symbol per exact MPN.
- **Local verify**: `scripts/schgen/verify.sh <board>` → `kicad-cli sch export netlist --format kicadsexpr` → `verify_netlist.py` diff against the spec. Prints `SKIPPED` and exits 0 when `kicad-cli` is absent.
- **zudo-pd extras**: `verify_geometry.py` (pure Python: labels sit on pin endpoints, no cross-net coordinate collisions), `check_baseline.py`, `check_decisions.py`, `run_smoke_test.sh`.
- **CI** (`.github/workflows/component-spec-skills.yml`, `ubuntu-latest`, python 3.12, SHA-pinned actions): regen-idempotency (`gen_schematic.py` then `git diff --exit-code boards/`) plus pure-Python verifiers. README states "CI cannot run kicad-cli".
- **Fab export**: `zudo-led-lamp/scripts/pcb/export-jlcpcb.py` runs `pcb drc --refill-zones --save-board --schematic-parity --format json`, `sch erc --format json`, netlist, gerbers, drill, pos, SVG. `verify-jlcpcb.py` re-parses Gerbers with `gerbonara` and rasterises with `resvg_py`.
- **Docker is used in exactly one place**: doc footprint previews. `doc/component-docs/footprint-previews/config.ts` pins the same 9.0.9 digest, runs `docker run --rm --platform linux/amd64 --network none --mount type=bind,...` and `kicad-cli fp export svg`. `zudo-circuit-doc/packages/circuit-doc/src/config/define.ts:30` ships that digest as the framework default `previewRenderer.image`.
- **PCBs are not generated**: no PCB generator script exists in any sibling. Largest sibling boards: zudo-pd 94 footprints / 992 segments / 216 vias; led-lamp board-l 74 / 664 / 75. How they were routed is UNVERIFIED (no autorouter, DSN or SES reference anywhere in the repos).
- **Sibling ERC/DRC baseline with the label-only style** (KiCad 10.0.0): board-l ERC 6 × `pin_to_pin` warnings, DRC 59 warnings (silk), 0 parity; board-p 27 DRC warnings, 3 `extra_footprint` parity warnings; swd-adapter ERC 0.

### export-jlcpcb.py depends on a skill that is missing on this machine

`export-jlcpcb.py:269` defaults `--converter` to `$HOME/.claude/skills/jlcpcb-bom-generate-from-kicad/scripts/convert_to_jlcpcb.py`. That directory does not exist on WSL.

### Prior owner research already rejected third-party schematic generators

`zudo-pd/experiments/ai-circuit-design/circuit-synth-spike/FINDINGS.md` (2026-06-17): circuit-synth 0.12.1 installed and ran, output parsed by kicad-cli 10, but zero wires, generic symbols, v9 format token, and root-sheet netlist export returned an empty component list. Verdict there: not adopted. `doc/src/content/docs/learning/ai-circuit-design-research.md` concludes the LLM should emit coordinate-free connectivity and a deterministic engine should do geometry.

---

## 3. The full generate → ERC → netlist → PCB → DRC → render loop ran headless here (PoC, KiCad 9.0.9)

All in the scratch dir, inside the local container with `--network none`. Code is in the appendix.

| Step | Command | Result |
| --- | --- | --- |
| Generate hierarchical schematic | `python3 gen_sch.py` (stdlib only) | root `poc.kicad_sch` + ONE child `osc_channel.kicad_sch` instantiated **5 times**; 25 components |
| Netlist | `kicad-cli sch export netlist --format kicadsexpr` | exit 0; 25 components with per-instance refs `R101…R503`; 17 nets |
| Spec diff | `verify_netlist.py` | **PASS** — all 17 nets match, per-instance local nets named `/OSC1/MID` … `/OSC5/MID` |
| ERC | `kicad-cli sch erc --format json --severity-all` | 0 violations on `/` and `/OSC1/`…`/OSC5/` |
| Schematic render | `kicad-cli sch export svg` | 6 SVGs (root + one per instance) |
| PCB from netlist | `python3 gen_pcb.py` using container `pcbnew` | 25 footprints, 18 nets, 75 KB, **0.05 s** |
| DRC + parity | `kicad-cli pcb drc --schematic-parity --format json --severity-all` | 0 violations, **0 schematic parity issues**, 33 unconnected (nothing routed) |
| PCB render | `kicad-cli pcb export svg`, `kicad-cli pcb render` | exit 0; PNG readable by the agent's image reader |
| Scale probe | 180 × `Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles` on a 318 × 298 mm outline | saved 1.33 MB board; DRC 2.2 s; SVG 0.46 s; 3D render 1.6 s |
| Flip to back side | `fp.Flip(pos, False)` + `SetOrientationDegrees(90)` | saved pads on `B.Cu B.Mask B.Paste` |
| Autorouter hand-off | `pcbnew.ExportSpecctraDSN(board, "poc.dsn")` | `True`, 4.9 KB; `ImportSpecctraSES` and `ZONE_FILLER` exist |
| SPICE | `ngspice -b slew-ideal.cir` on a copy of the handoff deck | exit 0, 26064 data rows |
| Container start | `docker run ... kicad-cli version` | 0.42 s wall |

Exit codes observed: 0 clean, 3 load failure. Docs: 5 when `--exit-code-violations` finds violations.

### Findings that change the design of the generators

1. **Schematic generation is byte-deterministic.** Two runs give identical sha256 for both files.
2. **pcbnew output is not.** Two runs differ on 608 lines, all UUIDs; the diff is empty after masking UUIDs. SWIG exposes `m_Uuid` read-only, there is no `SetUuid`. A regen-idempotency gate needs a UUID-rewrite pass.
3. **`FootprintLoad` re-parses the library on every call.** 180 loads took 30.5 s; load once and clone with `pcbnew.FOOTPRINT(src)`.
4. **ERC output depends on the container user's library tables.** Same schematic: default user `kicad` → 0 violations; `--user 1001:1001 -e HOME=/tmp` → 13 × `lib_symbol_issues` ("configuration does not include the symbol library 'Device'"). With `--user 1001:1001` and no HOME, kicad-cli logs "Directory '/.config/kicad/9.0' couldn't be created" but still exits 0.
5. **Multi-instance hierarchy works with plain S-expressions.** Each child symbol carries one `(path "/<root-uuid>/<sheet-uuid>" (reference "R101") (unit 1))` per instance; footprint `path` = sheet tstamps + symbol uuid gives zero parity issues.

---

## 4. Approach evaluation at this scale

Scale from the handoff (VERIFIED by parsing `current-spec.json` and `workbench/layout/grid.json`): 180 jacks, 144 controls (101 pots, 30 toggles, 8 buttons, 5 octave selectors), 92 magnitude + 12 stage + 10 clip LEDs = 114. Modules: OSC ×5, FILTER_VCA ×3, MIX5 ×2, MIX4_VCA ×2, AR ×6, FOLD ×2, OFFSET ×6, MULT ×2, SH_SLEW ×2, MANUAL_AB ×2, NOISE ×1. `kicad-sheet-plan.json` lists 18 sheets and states "Sheet responsibilities, not an electrical netlist". Board domains: J, OP/MP/EP, O, OS/ES/US, ET/UT, UP, K, P/B plus the panel. Total component count is UNVERIFIED — no netlist exists yet.

### (a) Purpose-built S-expression generators — adopt for schematics

- Proven in two sibling repos; stdlib only; deterministic; CI-checkable without KiCad.
- PoC proves the one missing capability (hierarchical multi-instance sheets).
- Needs extending: hierarchical sheets, multi-unit symbols (TL074, LM13700, OPA4197 are multi-unit in stock libs), per-board projection.
- Weak for PCBs: footprint embedding, rotation and back-side mirroring would have to be re-implemented by hand.

### (b) Libraries — none fits as the primary tool

| Library | Latest (PyPI) | Repo last push | Verdict |
| --- | --- | --- | --- |
| kiutils | 1.4.8, 2024-02-02 | 2024-07-10 | Stale; targets KiCad 6/7 tokens; GPL-3.0 |
| kicad-skip | 0.2.5, 2024-02-16 (single release) | 2024-05-26 | Stale; edits existing schematics |
| SKiDL | 2.3.0, 2026-07-28 | 2026-09-24 | Active, KiCad 10 support added in 2.3. Netlist-first; schematic output is auto-placed. Useful only as a second-opinion ERC |
| atopile | 0.15.9, 2026-09-12, requires Python `>=3.14,<3.15` | 2026-06-13 | Emits `.kicad_pcb`, no `.kicad_sch` — fails goal 2 |
| circuit-synth | 0.12.1, 2026-01-09 | 2026-03-08 | Already trialled and rejected by the owner |
| kicad-sch-api | 0.5.6, 2025-11-19 | — | Scripted edits only |
| kicad-tools | 0.21.1, 2026-09-21, "4 - Beta" | 2026-09-27 | Pure-Python DRC and A* router; documents KiCad 8+ formats only |
| kinet2pcb | 1.1.4, 2025-11-04 | — | Thin wrapper over pcbnew; PoC `gen_pcb.py` does the same in 50 lines |
| KiKit | 1.8.1, 2026-08-05 | 2026-09-25 | Keep in reserve for panelising small boards |
| KiBot | 1.9.1, 2026-07-28, AGPL-3.0 | 2026-09-25 | Redundant with `export-jlcpcb.py` |

None of them models **multi-board** designs. KiCad itself has no native multi-board project support.

### (c) pcbnew Python API inside the KiCad container — adopt for PCBs

- VERIFIED headless: load footprints, place, flip, assign nets and hierarchical paths, save, export DSN.
- KiCad's own code does footprint geometry, so rotation/mirroring errors cannot come from our generator.
- SWIG bindings are deprecated since 9.0, present in 9 and 10, planned for removal in KiCad 11. A digest-pinned image removes that risk for this project's lifetime.
- `import pcbnew` inside `kicad/kicad:10.0.6` is UNVERIFIED (image not present locally).

### (d) kicad-cli 9/10 — adopt as the oracle, not as an author

- Available in both: `sch erc`, `sch export {netlist,pdf,svg,bom,dxf,...}`, `pcb drc` (`--schematic-parity`, `--refill-zones`, `--save-board`, `--exit-code-violations`, `--severity-*`), `pcb export {gerbers,drill,pos,svg,pdf,step,glb,ipc2581,odb,...}`, `pcb render`, `fp export svg`, `jobset run`.
- New in the 10.0 CLI docs versus 9.0: `pcb import` (PADS/Allegro/etc.), `pcb upgrade`, `sch upgrade`, `pcb export stats`, 3D PDF, `--variant`.
- **No "update PCB from schematic" command exists** in 9 or 10.
- **IPC API is unusable headless**: KiCad dev docs state it "only supports communication with a running instance of the KiCad GUI" in 9 and 10, PCB editor only; headless via kicad-cli and schematic support arrive in KiCad 11.
- Jobsets are optional; sibling scripts already cover the same ground.

---

## 5. Recommended toolchain: spec-first generators with a digest-pinned KiCad 10.0.6 container as the only oracle

| Layer | Choice | Version |
| --- | --- | --- |
| Target file format | KiCad 10 | `.kicad_sch` `20260306`, `.kicad_pcb` `20260206` — identical to siblings |
| Oracle | `kicad/kicad:10.0.6` | digest `sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`, Docker Hub updated 2026-09-22, linux/amd64 only, 809 MB compressed. KiCad 10.0.6 released 2026-08-29 |
| Schematic author | `scripts/schgen/` forked from `$HOME/repos/circuits/zudo-pd/scripts/schgen` | Python 3.12 stdlib |
| PCB author | `scripts/pcbgen/` running on the container's `python3` + `pcbnew` | KiCad 10.0.6 bundled |
| Gerber cross-check | `gerbonara` 1.6.3 + `resvg-py` 0.5.0 via `uv run --with` | Python ≥ 3.12 |
| SPICE | `ngspice` inside the KiCad container | ngspice-39 in the 9.0.9 image; 10.0.6 UNVERIFIED |
| Part import | `easyeda2kicad` 1.0.1 | already installed |
| Optional router | Freerouting 2.4.1 (2026-09-03) | needs Java or its container; neither present |

### Verification loop

```
1  gen       python3 scripts/schgen/gen_schematic.py <board>        host, no KiCad
2  offline   coverage + verify_geometry + cross-board net check     host, no KiCad
3  ERC       kicad-cli sch erc --format json --severity-all         container
4  netlist   kicad-cli sch export netlist --format kicadsexpr       container
             python3 scripts/schgen/verify_netlist.py <spec> <net>  host
5  PCB sync  python3 scripts/pcbgen/sync.py <board>                 container (pcbnew)
             + deterministic UUID rewrite                           host
6  DRC       kicad-cli pcb drc --schematic-parity --refill-zones
             --save-board --format json --severity-all              container
7  render    kicad-cli sch export svg|pdf, pcb export svg,
             pcb render --side top|bottom                           container
8  fab       gerbers + drill + pos + BOM, gerbonara re-parse        container + host
```

### Rules the plan must encode

- **One wrapper** `scripts/kicad/run.sh`: resolves the pinned digest, passes `--platform linux/amd64 --network none`, mounts the repo, and refuses to run if `kicad-cli version` is not `10.0.x`. Fallback order: `$KICAD_CLI` → docker → `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`.
- **Never `SKIPPED`-as-pass.** Siblings exit 0 when KiCad is missing; here Docker exists on both the dev machine and GitHub runners, so a missing oracle must fail.
- **Project-local `sym-lib-table` / `fp-lib-table` with `${KIPRJMOD}`-relative URIs** and one project library (`zudo-osc-hole-field`, replacing the handoff's `zudo_osc_playground`). Copy stock symbols into it. This removes the environment-dependent ERC result found in the PoC.
- **`pcbgen` is an update, not a rewrite.** It loads the existing board, adds/removes/re-nets footprints, and leaves tracks, vias, zones and owner-drawn graphics untouched. KiCad offers no CLI for this.
- **Multi-board is modelled in the spec, not in KiCad.** One functional netlist; every component carries a board id; the generator emits one KiCad project per board under `boards/<board>/` with connector pins at each boundary. A cross-board verifier joins per-board netlists through the connector mate map and diffs against the functional netlist.
- **Repetition is per board.** Within a board, one child sheet per module slice, instantiated N times as in the PoC.

### GitHub Actions

`ubuntu-latest` ships Docker, so CI can run the real oracle — an upgrade over the siblings. Two jobs: the existing pure-Python regen-idempotency job, and a `kicad-checks` job calling `scripts/kicad/run.sh`. Runner uid is not 1000; use `--user root -e HOME=/home/kicad` or write outputs to a world-writable directory (exact flag combination UNVERIFIED; both the uid mismatch symptom and the HOME dependency are VERIFIED).

### What the owner must install or do

1. **WSL**: `docker pull kicad/kicad:10.0.6` (then reference by digest). Mandatory.
2. **Mac**: Docker Desktop with amd64 emulation, or upgrade the KiCad app from 10.0.0 to 10.0.6 for GUI review.
3. **Sync or vendor** `jlcpcb-bom-generate-from-kicad` (missing on WSL).
4. **Optional, only if autorouting is chosen**: Java 21 + `freerouting-2.4.1.jar`, or the Freerouting container.
5. Nothing via apt, pip or snap.

---

## 6. Fabrication limits (JLCPCB pages fetched 2026-09-28)

### PCB fabrication — a 318 × 298 mm 2-layer black ENIG panel is inside limits

Source: https://jlcpcb.com/capabilities/pcb-capabilities and https://jlcpcb.com/help/article/pcb-dimensions (article shows "Last Updated: Sep 09, 2026").

| Item | Published value |
| --- | --- |
| Max size FR4 1-layer / 2-layer / 4-layer / 6+ | 606 × 510 / **670 × 600** / 663 × 593 / 656 × 586 mm |
| Extended 2-layer FR4 (1.0/1.2/1.6/2.0 mm, 1 oz or 2 oz) | up to 1020 × 600 mm |
| Min size | 3 × 3 mm |
| FR4 thickness | 0.4 / 0.6 / 0.8 / 1.0 / 1.2 / 1.6 / 2.0 mm; "2.5 mm and above are for 12+ layer PCBs only" |
| Thickness tolerance (≥ 1.0 mm) | ± 10 % → 1.6 mm = 1.44–1.76; 2.0 mm = 1.80–2.20 |
| Solder mask | Green, Purple, Red, Yellow, Blue, White, Black |
| Surface finish | HASL leaded / lead-free, ENIG, OSP |
| Drill diameter | 0.15 – 6.3 mm; "Holes with diameter ≥ 6.3 mm are CNC routed from a smaller drilled hole" |
| Hole tolerance | +0.13 / −0.08 mm; position ± 0.05 mm |
| **Min NPTH** | **0.50 mm** |
| **Min plated slot** | **0.5 mm** (2-layer), length ≥ 2 × width |
| **Min non-plated slot** | **1.0 mm**, tolerance ± 0.2 mm |
| Rectangular holes without rounded corners | not supported |
| Routed outline tolerance | ± 0.2 mm; ± 0.1 mm precision option needs ≥ 50 × 50 mm and 3 tooling holes ≥ 1.5 mm |
| Copper to routed edge / NPTH to track | ≥ 0.2 mm / 0.2 mm |
| NPTH pad annular ring | ≥ 0.45 mm |
| Solder-mask bridge, black or white, 1 oz | min pad spacing 0.13 mm |
| Silkscreen | line ≥ 0.15 mm, text height ≥ 1.0 mm, pad-to-silk 0.15 mm |
| Trace / space 1–2 layer 1 oz | 0.10 / 0.10 mm |

No size restriction is published for the black + ENIG combination. Price for 318 × 298 mm is UNVERIFIED (needs the quote tool).

**Panel thickness**: 1.6 mm or 2.0 mm are the realistic options. 2.0 mm is 1.95× stiffer in bending ((2.0/1.6)³). The panel is fabrication-only, so assembly thickness limits do not apply. Final choice depends on jack bushing engagement, which the handoff lists as open issue G01.

**Hole consequences for the panel**: handoff apertures are LED 1.2 / 1.44 mm, button 5.0 mm, pot shaft 6.0 mm, octave 8.0 mm, jack nut envelope 8.3 mm. Holes below 6.3 mm are drilled (+0.13/−0.08); holes at or above 6.3 mm are routed. Jack and toggle bushing holes sit right at that boundary, so the chosen diameter decides the process and tolerance.

### PCB assembly — limits from https://jlcpcb.com/capabilities/pcb-assembly-capabilities

| Feature | Economic PCBA | Standard PCBA |
| --- | --- | --- |
| **Single PCB size** | **10 × 10 – 470 × 500 mm** | **70 × 70 – 460 × 500 mm** |
| Panelised delivery size | 10 × 10 – 250 × 250 mm | 70 × 70 – 250 × 250 mm |
| Placement | Single-sided (SMT/THT) | Single and double-sided (SMT/THT) |
| Layers | 2, 4, 6 | 1 – 32 |
| Thickness | 0.8 – 1.6 mm | No limit |
| Order volume | 2 – 50 pcs | 2 – 80000 pcs |
| Colour / finish | restricted table | No limit |
| Edge rails, fiducials | Not necessary | Necessary |
| Min package | 0402 | 0201 |
| Build time | 1 – 3 days | ≥ 4 days |

Economic colour/finish table (layer column is not present in the page's static HTML; grouping inferred as 2-layer rows first): 0.8 Green HASL; 1.0 and 1.2 Green/Black HASL; 1.6 Green HASL or ENIG; **1.6 Black HASL only**; 1.6 Blue/Purple HASL; 1.6 Red/White leaded HASL.

THT: "JLCPCB supports Through-Hole Technology (THT) component assembly and mixed-technology (SMD + THT) PCB assembly … available under both the Economic and Standard PCBA." FAQ (https://jlcpcb.com/help/article/pcb-assembly-faqs): hand-soldered parts cost "$3.5 hand-soldering labor fee + $0.0173 manual assembly fee per joint".

A 2024-08-09 JLCPCB Q&A entry records the quote tool once warning at "570x470mm" while the capabilities page said 470 × 500 — the two have disagreed before.

PCBWay (https://www.pcbway.com/assembly-capabilities.html, fetched 2026-09-28): "Min Board Size: 10mm x 10mm … Max Board Size: 250mm x 500mm", SMT, THT and hybrid, single or double-sided.

---

## 7. A 318 mm wide jack board with 180 jacks CAN be factory assembled at JLCPCB

Jack centres span x 14.5 – 303.5 mm (289 mm) and y 29 – 155 mm (126 mm) on the 318 × 298 mm panel (VERIFIED from `workbench/layout/placements-review.csv`, 180 rows). A single jack board is therefore at most about 318 × 150 mm.

| Limit | 318 × 150 mm jack board | 318 × 298 mm full-panel-size board |
| --- | --- | --- |
| JLCPCB fab 670 × 600 | fits | fits |
| JLCPCB Economic PCBA 470 × 500 | fits by size | fits by size |
| JLCPCB Standard PCBA 460 × 500 | fits | fits |
| PCBWay assembly 250 × 500 | fits | does not fit (298 > 250) |

Conditions attached to that yes:

- **Standard PCBA is required**, not Economic, as soon as a board is double-sided, thicker than 1.6 mm, or black with ENIG. Black with HASL at 1.6 mm, single-sided, could stay Economic.
- **Small boards fall below the Standard minimum of 70 × 70 mm.** The octave strip (5 switches at 17 mm pitch) and the button boards need edge rails or panelisation. Panelised delivery is capped at 250 × 250 mm.
- **Every THT part must be orderable through JLCPCB** (library, global sourcing or consignment). Handoff records show WQP518MA as `C9900052034` and several parts with zero stock — availability is UNVERIFIED.
- **JLCPCB's DFM review has the last word.** Published limits are VERIFIED; acceptance of this specific board is UNVERIFIED until a quote is accepted.

Alternatives if the single board is refused or warps:

1. Split J at a module column boundary: 2 boards of 9 columns (about 153 × 140 mm) or 3 of 6 columns (about 102 × 140 mm). Both fit every limit above including 250 × 250.
2. Use another assembler for the large board only.
3. Keep fabrication at JLCPCB and consign THT soldering to a local assembler — still satisfies "no home soldering".

---

## 8. Risks and blockers

| # | Risk | Severity |
| --- | --- | --- |
| R1 | **No netlist exists.** The handoff is pre-schematic; `open-issues.json` G03–G08 are open electrical design items. The toolchain can only verify what the spec states | Blocker for goal 2 content, not for tooling |
| R2 | **Routing has no headless owner.** No sibling precedent, no autorouter installed, KiCad 10 has no headless API. Handoff gate: "No unrouted PCB is called release" | High |
| R3 | The only local KiCad is 9.0.9 and cannot read v10 files. Until the 10.0.6 image is pulled, zero KiCad checks can run on this machine for v10 output | High, 1 command to clear |
| R4 | `import pcbnew` in the 10.0.6 image is UNVERIFIED | Medium |
| R5 | KiCad has no multi-board model; functional hierarchy cuts across 13+ physical boards | High — drives generator architecture |
| R6 | Existing schgen lacks multi-unit symbols and hierarchy | Medium — PoC covers hierarchy only |
| R7 | Regenerating a PCB destroys manual work unless `pcbgen` is an in-place update. The owner intends to restyle panel silk/copper by hand | High |
| R8 | pcbnew UUIDs are random; idempotency CI needs a rewrite pass | Low |
| R9 | ERC results vary with container user/HOME when stock libraries are referenced | Low once libs are project-local |
| R10 | Doc framework pins KiCad 9.0.9 for footprint previews; footprints saved by a KiCad 10 GUI may not load there | Medium |
| R11 | `kicad/kicad` images are amd64-only; Apple Silicon runs them emulated | Low |
| R12 | Standard PCBA 70 × 70 mm minimum versus small strips; 250 × 250 mm panel cap | Medium |
| R13 | `jlcpcb-bom-generate-from-kicad` skill absent on WSL | Low |

---

## 9. Open decisions with recommended defaults

| # | Decision | Recommended default |
| --- | --- | --- |
| D1 | KiCad target version | **10.0.6**, files in v10 format. Do not emit v9 to suit the local image |
| D2 | Where KiCad runs | Digest-pinned Docker image on WSL, Mac and CI. Native Mac app only for GUI review |
| D3 | Schematic style | Label-at-pin, no wires, hierarchical sheets with repeated instances. Multi-unit symbols for op-amps |
| D4 | PCB authoring | pcbnew in the container, update-in-place, UUID normalisation |
| D5 | Multi-board model | One functional spec, one KiCad project per board, cross-board verifier |
| D6 | Routing | Route one module instance, replicate by pitch offset with pcbnew, fill ground with `--refill-zones`, Freerouting for leftovers, owner GUI pass as final review. Treat as its own epic phase |
| D7 | Panel ownership | Generator owns outline, holes and baseline labels by deterministic UUID; owner art lives in separate items that regen preserves |
| D8 | Panel thickness | 1.6 mm provisional; decide 1.6 vs 2.0 with issue G01 |
| D9 | Jack board partition | Single board, with the 2 × 9-column split documented as the fallback |
| D10 | PCBA tier | Standard PCBA for every assembled board |
| D11 | Assembled-board finish | Black + ENIG only on the visible panel; assembled boards may use HASL unless the owner wants them matching |
| D12 | Doc footprint preview image | Keep framework default 9.0.9 and keep `.kicad_mod` files in a format it reads; revisit if previews fail |
| D13 | CI | Add a real `kicad-checks` job; missing oracle fails the build |
| D14 | Third-party libraries | None in the core loop. SKiDL / kicad-tools only as optional second opinions |

---

## Appendix A — PoC code (scratch copies are temporary)

### gen_sch.py — hierarchical schematic, one child sheet × 5 instances

```python
import uuid, json
NS = uuid.UUID('a3f0c9d2-2f3e-4a9b-9b0f-3c1d7e8f4a10')
def U(s): return str(uuid.uuid5(NS, s))
PROJ = 'poc'; N = 5
SYMLIB = '/usr/share/kicad/symbols/Device.kicad_sym'

def extract_symbol(path, name):
    text = open(path, encoding='utf-8').read()
    i = text.find(f'(symbol "{name}"'); depth = 0; j = i; ins = False
    while j < len(text):
        c = text[j]
        if ins:
            if c == '\\': j += 1
            elif c == '"': ins = False
        elif c == '"': ins = True
        elif c == '(': depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0: return text[i:j+1]
        j += 1

R_RAW = extract_symbol(SYMLIB, 'R').replace('(symbol "R"', '(symbol "Device:R"', 1)
HEADER = lambda u, paper='A4': (f'(kicad_sch\n\t(version 20250114)\n\t(generator "zudo_schgen")\n'
    f'\t(generator_version "9.0")\n\t(uuid "{u}")\n\t(paper "{paper}")\n')
root_uuid = U('root')
sheet_uuid = [U(f'sheet:{n}') for n in range(1, N+1)]

def prop(name, val, x, y, hide=False):
    h = ' (hide yes)' if hide else ''
    return f'\t\t(property "{name}" "{val}" (at {x:g} {y:g} 0) (effects (font (size 1.27 1.27)){h}))'

def resistor(uid, x, y, value, fp, instances):
    out = [f'\t(symbol (lib_id "Device:R") (at {x:g} {y:g} 0) (unit 1)',
           '\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)',
           f'\t\t(uuid "{uid}")',
           prop('Reference', instances[0][1], x+2.54, y-1.27), prop('Value', value, x+2.54, y+1.27),
           prop('Footprint', fp, x, y, True), prop('Datasheet', '', x, y, True),
           f'\t\t(pin "1" (uuid "{U(uid+":1")}"))', f'\t\t(pin "2" (uuid "{U(uid+":2")}"))',
           f'\t\t(instances (project "{PROJ}"']
    for path, ref in instances:                      # one path per sheet instance
        out.append(f'\t\t\t(path "{path}" (reference "{ref}") (unit 1))')
    out.append('\t\t))\n\t)')
    return '\n'.join(out)

def glabel(net, x, y, ang, seed):
    j = 'left' if ang in (0, 90) else 'right'
    return (f'\t(global_label "{net}" (shape passive) (at {x:g} {y:g} {ang}) '
            f'(effects (font (size 1.27 1.27)) (justify {j})) (uuid "{U(seed)}"))')
def hlabel(net, shape, x, y, ang, seed):
    j = 'left' if ang in (0, 90) else 'right'
    return (f'\t(hierarchical_label "{net}" (shape {shape}) (at {x:g} {y:g} {ang}) '
            f'(effects (font (size 1.27 1.27)) (justify {j})) (uuid "{U(seed)}"))')
def llabel(net, x, y, ang, seed):
    return (f'\t(label "{net}" (at {x:g} {y:g} {ang}) '
            f'(effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{U(seed)}"))')

FP = 'Resistor_SMD:R_0603_1608Metric'
child = [HEADER(U('child:osc')), '\t(lib_symbols\n\t\t' + R_RAW.replace('\n', '\n\t\t') + '\n\t)']
parts = {'R1': (50.8, 50.8), 'R2': (76.2, 50.8), 'R3': (101.6, 50.8)}
nets_child = {'R1': ('IN', 'MID'), 'R2': ('MID', 'OUT'), 'R3': ('MID', 'GND')}
for k, (x, y) in parts.items():
    idx = int(k[1:])
    inst = [(f'/{root_uuid}/{sheet_uuid[n]}', f'R{(n+1)*100+idx}') for n in range(N)]
    child.append(resistor(U('child:'+k), x, y, '10k', FP, inst))
    for pin, (dy, ang) in (('1', (-3.81, 90)), ('2', (3.81, 270))):
        net = nets_child[k][0 if pin == '1' else 1]
        px, py = x, y + dy                           # sheet Y is inverted vs symbol Y
        if net in ('IN', 'OUT'):
            child.append(hlabel(net, 'input' if net == 'IN' else 'output', px, py, ang, f'child:h:{k}:{pin}'))
        elif net == 'GND':
            child.append(glabel(net, px, py, ang, f'child:g:{k}:{pin}'))
        else:
            child.append(llabel(net, px, py, ang, f'child:l:{k}:{pin}'))
child.append('\t(embedded_fonts no)\n)')
open('osc_channel.kicad_sch', 'w').write('\n'.join(child) + '\n')

root = [HEADER(root_uuid, 'A3'), '\t(lib_symbols\n\t\t' + R_RAW.replace('\n', '\n\t\t') + '\n\t)']
for n in range(N):
    sx, sy = 50.8 + n*50.8, 50.8
    su = sheet_uuid[n]
    root.append('\n'.join([
        f'\t(sheet (at {sx:g} {sy:g}) (size 25.4 12.7)',
        '\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)',
        '\t\t(stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0.0000))',
        f'\t\t(uuid "{su}")',
        f'\t\t(property "Sheetname" "OSC{n+1}" (at {sx:g} {sy-0.7:g} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))',
        f'\t\t(property "Sheetfile" "osc_channel.kicad_sch" (at {sx:g} {sy+13.3:g} 0) (effects (font (size 1.27 1.27)) (justify left top)))',
        f'\t\t(pin "IN" input (at {sx:g} {sy+5.08:g} 180) (uuid "{U(f"sheetpin:{n}:IN")}") (effects (font (size 1.27 1.27)) (justify left)))',
        f'\t\t(pin "OUT" output (at {sx+25.4:g} {sy+5.08:g} 0) (uuid "{U(f"sheetpin:{n}:OUT")}") (effects (font (size 1.27 1.27)) (justify right)))',
        f'\t\t(instances (project "{PROJ}" (path "/{root_uuid}" (page "{n+2}"))))',
        '\t)']))
    root.append(glabel(f'OSC{n+1}_IN', sx, sy+5.08, 180, f'root:g:{n}:IN'))      # label ON the sheet pin
    root.append(glabel(f'OSC{n+1}_OUT', sx+25.4, sy+5.08, 0, f'root:g:{n}:OUT'))
    for base, (na, nb), yy in ((600, (f'OSC{n+1}_OUT', 'GND'), 101.6), (700, ('VIN', f'OSC{n+1}_IN'), 127)):
        ref = f'R{base+n+1}'; x = 50.8 + n*50.8
        root.append(resistor(U('root:'+ref), x, yy, '1k', FP, [(f'/{root_uuid}', ref)]))
        root.append(glabel(na, x, yy-3.81, 90, f'root:g:{ref}:1'))
        root.append(glabel(nb, x, yy+3.81, 270, f'root:g:{ref}:2'))
root.append('\t(sheet_instances (path "/" (page "1")))')
root.append('\t(embedded_fonts no)\n)')
open('poc.kicad_sch', 'w').write('\n'.join(root) + '\n')
```

### gen_pcb.py — netlist → board with pcbnew (parity-clean)

```python
import pcbnew, re
mm = pcbnew.FromMM
net_text = open('poc.net', encoding='utf-8').read()
comps = []
for m in re.finditer(r'\(comp \(ref "([^"]+)"\)(.*?)(?=\n\s*\(comp \(ref|\n\s*\(libparts|\Z)', net_text, re.S):
    ref, body = m.group(1), m.group(2)
    sp = re.search(r'\(sheetpath \(names "([^"]*)"\) \(tstamps "([^"]*)"\)\)', body)
    comps.append(dict(ref=ref,
        value=re.search(r'\(value "([^"]*)"\)', body).group(1),
        fp=re.search(r'\(footprint "([^"]*)"\)', body).group(1),
        sheetname=sp.group(1), sheet_ts=sp.group(2),
        sym_ts=re.findall(r'\(tstamps "([^"]+)"\)', body)[-1]))
nets = {}
for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)(.*?)(?=\n\s*\(net \(code|\Z)', net_text, re.S):
    for r, p in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2)):
        nets[(r, p)] = m.group(1)

b = pcbnew.BOARD()
# ... Edge.Cuts rectangle omitted ...
netinfo = {}
for name in sorted(set(nets.values())):
    ni = pcbnew.NETINFO_ITEM(b, name); b.Add(ni); netinfo[name] = ni
cache = {}
for i, c in enumerate(sorted(comps, key=lambda c: c['ref'])):
    lib, name = c['fp'].split(':')
    src = cache.get(c['fp']) or cache.setdefault(
        c['fp'], pcbnew.FootprintLoad(f'/usr/share/kicad/footprints/{lib}.pretty', name))
    fp = pcbnew.FOOTPRINT(src)                                   # clone; do not re-load
    fp.SetParent(b)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    fp.SetReference(c['ref']); fp.SetValue(c['value'])
    fp.SetPath(pcbnew.KIID_PATH(c['sheet_ts'] + c['sym_ts']))    # this is what makes parity pass
    fp.SetSheetname(c['sheetname'])
    fp.SetSheetfile('osc_channel.kicad_sch' if c['sheetname'] != '/' else 'poc.kicad_sch')
    fp.SetPosition(pcbnew.VECTOR2I(mm(10 + (i % 5) * 22), mm(8 + (i // 5) * 10)))
    for pad in fp.Pads():
        n = nets.get((c['ref'], pad.GetNumber()))
        if n: pad.SetNet(netinfo[n])
    b.Add(fp)
pcbnew.SaveBoard('poc.kicad_pcb', b)
```

### Container invocation used for every check

```bash
docker run --rm --network none -v "$PWD:/work" -w /work \
  kicad/kicad@sha256:e638b79b0321f29395a5b783e94bb9f3c73303e8da15da27b8f5cb4b67a37729 \
  kicad-cli pcb drc --schematic-parity --format json --severity-all -o drc.json poc.kicad_pcb
```

## Appendix B — Sources

- https://jlcpcb.com/capabilities/pcb-assembly-capabilities (fetched 2026-09-28)
- https://jlcpcb.com/capabilities/pcb-capabilities (fetched 2026-09-28)
- https://jlcpcb.com/help/article/pcb-dimensions (Last Updated Sep 09, 2026)
- https://jlcpcb.com/help/article/pcb-assembly-faqs (fetched 2026-09-28)
- https://jlcpcb.com/help/answers/detail/455-Maximum-dimensions (question dated 2024-08-09)
- https://www.pcbway.com/assembly-capabilities.html (fetched 2026-09-28)
- https://hub.docker.com/r/kicad/kicad — tags API queried 2026-09-28
- https://www.kicad.org/blog/2026/08/KiCad-10.0.6-Release/ (2026-08-29)
- https://www.kicad.org/blog/2026/03/Version-10.0.0-Released/
- https://docs.kicad.org/10.0/en/cli/cli.html and https://docs.kicad.org/9.0/en/cli/cli.html
- https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/index.html
- https://dev-docs.kicad.org/en/apis-and-binding/pcbnew/
- https://github.com/freerouting/freerouting/releases (v2.4.1, 2026-09-03)
- PyPI JSON API for kiutils, kicad-skip, skidl, atopile, circuit-synth, kicad-sch-api, kicad-python, kikit, kibot, kinet2pcb, gerbonara, resvg-py, easyeda2kicad, kicad-tools (queried 2026-09-28)
- https://ppa.launchpadcontent.net/kicad/kicad-10.0-releases/ubuntu/dists/noble/ (queried 2026-09-28)
- EEVblog thread "Warning : JLCPCB new nonsensical PCBA size limits" — HTTP 403, content UNVERIFIED
