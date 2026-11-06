# GH4 native coupon — REVIEW ONLY

Isolated unpowered evaluation coupon, authored on x0x on 2026-10-18 from
`23b0652fdc981b374c7d5c6b053e509372b008b0`. This directory alone is new.
Canonical A01 boards, historical stages, both viewers and parent PR #286 are unchanged.
No manufacturing release, upload, supplier contact, order or physical success is claimed.

## Native result

- KiCad CLI and pcbnew: **10.0.6**, existing Ubuntu WSL Docker image
  `kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`.
- `erc.rpt`: zero errors and warnings.
- `drc.rpt`: zero DRC violations, zero unconnected pads, zero schematic parity issues.
- `review-only/audit.json`: exported netlist, pin correspondence, placement, drill and
  Gerber checks. `review-only/gerber-review.png` renders actual exported Gerber
  linear strokes and flashed apertures. This limited parser rejects arcs/regions;
  it is not a substitute for a fabricator CAM review.
- `review-only/board-top.pdf`, `.png` and `.svg`: native KiCad board renderings.
- `REVIEW.md`: independent review and source/native bindings.

Native hashes are recorded in `review-only/audit.json`; `SHA256SUMS.txt` binds the
retained deliverables. KiCad creates new object UUIDs on regeneration; later
regeneration requires fresh native checks, exports, hashes and review.

## Exact identity and construction

J1 is JST **BM04B-GHS-TBT(LF)(SN)**, top-entry GH4, supplier identity **C161692**.
One populated header per board. The pinned maintained footprint is a library
asset, not a vendor-certified footprint. Source and SHA256 are in the unchanged
`../gh4-coupon-plan/design.json`; attribution/license are retained in
`FOOTPRINT-LICENSE.md`. The upstream footprint is byte-identical to pinned revision
`f8a45b4665c28a6280e46eefe9fd4df81d2cd17b`.

Manufacturer basis: JST eGH catalog, printed pages 2–3, retained in
`design/connectors/sources/jst-gh.pdf`, SHA256
`b1dcb317b6b9a4fbbedd2dbf42c64c95306a252d23de8933b85fcf161240b722`.
The mounting-surface view rotates 180 degrees without mirroring into this top
component view: signal pin 1 left, signal row below the body, mechanical lands
above. Exact six land centers/sizes match the reviewed design. No 3D body or
physical fit verification is inferred.

Overall 80×100 mm, functional 80×80 mm, two 10 mm rails. Four F.Cu-only independent
0.25 mm nets GH1–GH4 connect J1.n to TPn. No supply or planes. MP lands have no
signal net. Both-face clamp reservations and 1 mm V-cut bands are native rule
areas; 1 mm outer copper clearance and 0.25 mm spacing/track width are enforced.
Three Ø1 copper/Ø2 mask fiducials; three Ø2 NPTH tooling holes; four Ø2 testpads.
Only J1 has paste: four signal and two MP apertures. Testpads/fiducials/tooling
are excluded from assembly BOM/CPL. Bare lands have no component courtyard;
`missing_courtyard` is explicitly ignored, and all other ignored native defaults
are enumerated in the DRC report. J1 retains its pinned courtyard.

## Export conventions and unreleased status

All manufacturing-style files live in **review-only/** and are not order files.
The perimeter is four Edge.Cuts segments. Full-width V-cuts at y10/y90 are
annotations on `Dwgs.User`, named `V-CUT-REVIEW`; they are not slots. That Gerber
also carries explanatory text; eventual fabrication interpretation must explicitly
identify the two score lines. There is no automatic V-score machining instruction.

`placement-native.csv` contains only J1, mm, top, 0 degrees, X40 Y−50. KiCad's
absolute placement export uses Y up; design/PCB coordinates use Y down from the
upper-left overall origin. Therefore Y−50 corresponds to design y50. This is a
native review CPL, not a supplier-normalized upload. Do not reinterpret it without
an explicit transform and placement preview. `bom-review-only.csv` contains one
exact header per board, not a five-board order quantity.

## Commands and evidence

Run from repository root with the existing pinned image; do not run regen-all:

```sh
n=design/architecture-278/implementation/stage36/gh4-coupon-native
bash scripts/kicad/run.sh kicad-cli version
bash scripts/kicad/run.sh python3 "$n/generate.py"
bash scripts/kicad/run.sh kicad-cli sch erc --exit-code-violations --output "$n/erc.rpt" "$n/gh4-coupon.kicad_sch"
bash scripts/kicad/run.sh kicad-cli pcb drc --schematic-parity --exit-code-violations --output "$n/drc.rpt" "$n/gh4-coupon.kicad_pcb"
bash "$n/export-review.sh"
python3 "$n/audit_review.py"  # needs already-installed Pillow
```

`export-review.sh` records the exact native netlist/SVG/Gerber/drill/placement
commands. Native PDF command used:
`bash scripts/kicad/run.sh kicad-cli pcb export pdf --layers F.Cu,F.Silkscreen,Edge.Cuts,Dwgs.User --output "$n/review-only/board-top.pdf" "$n/gh4-coupon.kicad_pcb"`.
PDF rasterization used existing Windows Python 3.12.14, pypdfium2 5.14.0 at scale5,
cropped to (0,0,1150,1450); Gerber rendering used Pillow 12.3.0.

Before and after native authoring, the existing Node 22.22.2 installation ran
`node node_modules/@takazudo/zudo-circuit-doc/bin/zudo-circuit-doc.js validate`:
PASS. SCOPE: manual inventory, 68 lines, zero declared placements unverified,
no schematic/placement binding; pin-asset check performed. The final direct CLI
`check` passed generated-page/preflight/model checks and all 31 committed footprint
previews. Three `gh4-coupon-plan/test_design.py` source tests passed. Full pnpm
workspace TypeScript/site checks and whole OSC regeneration were NOT RUN; unrelated
site/native inputs were not edited. No browser-viewer test was rerun.

## Failures retained and corrected

1. Sandboxed WSL enumeration returned E_ACCESSDENIED; approved read-only host
   execution succeeded. Windows PATH/standard installation registry contained no
   KiCad; WSL had no standalone KiCad package/binary. Existing pinned Docker image
   returned exact 10.0.6. No KiCad install, image pull, default or daemon change.
2. First direct validation command guessed `bin/cli.mjs` and failed MODULE_NOT_FOUND.
   The actual entrypoint is `bin/zudo-circuit-doc.js`.
3. `pnpm circuit:check` attempted automatic dependency reconciliation and aborted
   with ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY before replacing modules. Its log
   referenced pnpm 11.5.2 temporary tool cache. No install was intentionally run;
   switched to the existing direct CLI to avoid automatic package-manager work.
4. Windows footprint download hit sandbox WinError10013; WSL public download
   succeeded, required SHA256 matched. No credentials were needed.
5. Initial pcbnew API calls failed for LSET constructors/union and the obsolete
   SetDoNotAllowCopperPour method. Replaced with AddLayer and SetDoNotAllowZoneFills.
   Initial board DRC attempt could not open the not-yet-generated board.
6. First schematic load failed with a literal multiline string; escaped it.
   `erc-02.rpt` retains 23 warnings (off-grid schematic coordinates and absent
   project/library discovery during incomplete generation). Corrected schematic
   grid coordinates and completed local project/library files; final ERC zero.
7. Independent review found local /GHn vs PCB GHn naming. Changed to global GHn
   labels. `drc-parity-first.rpt` then retained 11 metadata parity warnings:
   datasheet field, TP values, and six board-only features. Corrected fields and
   explicit board-only attributes; final parity zero. `drc-first.rpt` retains the
   earlier clean geometry-only check, not final parity evidence.
8. The auxiliary audit initially assumed the old numeric/net-name PCB syntax;
   KiCad 10 stores direct net names. Corrected the reader; final audit passed.
9. Staged whitespace checking identified raw KiCad SVG trailing spaces and
   Windows receipt CRLF. Narrow local attributes preserve reviewed SVG bytes and
   accept CRLF only for audit.json/BOM; authored files remain checked. The hash
   manifest uses LF. The initial pathspec staging matched no files; an explicit
   file list was used, excluding `.kicad_prl` and Python caches.

## Handoff boundary

Remote PR #287 branch `agent/278-stage28-din-harness-20261017` was read at pinned
`23b0652fdc981b374c7d5c6b053e509372b008b0` before any coupon write. Work used an
independent no-hardlinks clone under this task workspace, never another session's
worktree. Before pushing, the parent must re-confirm current remote head and the
push route. The clone's origin still points to the read-only source checkout;
do not push to that local origin. No push was made.

Physical soldering, continuity/isolation measurements, grip/latch/access, board
bow, flex/durability and assembly-process qualification are NOT RUN. Supplier
placement preview, V-score interpretation and release approval remain later
manufacturing gates. Native rule checks do not establish those physical results.
