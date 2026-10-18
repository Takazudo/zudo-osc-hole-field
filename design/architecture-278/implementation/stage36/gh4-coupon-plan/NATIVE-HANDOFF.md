# Isolated GH4 native handoff — NOT EXECUTED

The source design is [CONCRETE-DESIGN.md](CONCRETE-DESIGN.md), with exact coordinates in [design.json](design.json). This is a future task, not native or manufacturing output. Preserve both viewers and canonical OSC CAD. Do not order, upload or energize.

## Capability boundary

Cloud command `KICAD_CLI_BIN=/usr/bin/kicad-cli bash scripts/kicad/run.sh kicad-cli version` failed: installed KiCad **9.0.2**, repository requires **10.0.6** (wrapper accepts the broader 10.0.x pattern). Read-only `/home/agent` cache/config diagnostics also appeared. No installation, Docker changes, regeneration, ERC, DRC or exports ran. Version mismatch alone prevents use as this project's oracle.

Use an existing Mac KiCad 10.0.6 installation or an already available approved WSL Docker image. Do not replace the pinned oracle. In a clean checkout of this continuation's final commit, from repository root:

```bash
# Mac, if already installed:
export KICAD_CLI_BIN=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
bash scripts/kicad/run.sh kicad-cli version
# WSL alternative: leave KICAD_CLI_BIN unset; wrapper uses scripts/kicad/pin.env.
# Confirm exact output 10.0.6 before proceeding.
```

Pinned image: `kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`. If neither exact oracle is available, report unavailable and stop native execution; these instructions authorize no install.

## Source acquisition and authoring

After separately authorized native work, create an isolated project directory, e.g. `design/architecture-278/implementation/stage36/gh4-coupon-native/`. No such project is supplied by this source study. Fetch the footprint into a project-local library, preserving its license and attribution:

```bash
python3 - <<'PY'
import hashlib, json, pathlib, urllib.request
base = pathlib.Path('design/architecture-278/implementation/stage36')
design = json.loads((base/'gh4-coupon-plan/design.json').read_text())
src = design['footprint_source']
data = urllib.request.urlopen(src['url']).read()
if hashlib.sha256(data).hexdigest() != src['sha256']:
    raise SystemExit('Footprint hash mismatch; stop')
lib = base/'gh4-coupon-native/gh4.pretty'
lib.mkdir(parents=True, exist_ok=True)
target = lib/'JST_GH_BM04B-GHS-TBT_1x04-1MP_P1.25mm_Vertical.kicad_mod'
if target.exists() and target.read_bytes() != data:
    raise SystemExit('Existing footprint differs; stop')
target.write_bytes(data)
PY
```

In KiCad 10.0.6, author `gh4-coupon.kicad_pro`, `.kicad_sch`, and `.kicad_pcb` in that directory. Register the local footprint library. Use a four-pin passive header symbol and four testpoints: pin n to TPn, nets GH1–GH4 only. Assign the pinned footprint; MP lands remain without signal nets. Testpoints, fiducials and tooling are excluded from assembly BOM/CPL. No power flags or power source are needed. Inspect symbol-to-pad numbering explicitly.

Use overall origin (0,0), 80×100 rectangle on Edge.Cuts; full-width V-cut annotations y10/y90 on a clearly named fabrication drawing layer, **not slots**. Place every feature from design.json with no rotation/mirror change. Top copper only for signal routing; no planes. Route each signal straight downward initially, then monotonically fan to its corresponding TP without crossings; enforce 0.25 mm trace and clearance, 1 mm other-copper edge/V-cut clearance, and both-face clamp keepouts. Set TP/fiducial paste off and tooling NPTH. Review mask and paste apertures against the catalog/manual references. Do not treat a missing 3D model as evidence about body geometry; use the retained body envelope and inspect the 2D footprint.

After saving, use the wrapper for checks (these commands require the newly authored files):

```bash
native=design/architecture-278/implementation/stage36/gh4-coupon-native
bash scripts/kicad/run.sh kicad-cli sch erc --exit-code-violations --output "$native/erc.rpt" "$native/gh4-coupon.kicad_sch"
bash scripts/kicad/run.sh kicad-cli pcb drc --exit-code-violations --output "$native/drc.rpt" "$native/gh4-coupon.kicad_pcb"
```

Retain first failures, fix causes and rerun. Independently review all four pin-to-pad-to-TP paths, all six signal-net isolation pairs, MP separation, top-view pin1, mask/paste, tooling, rails/V-cuts, clamp reservations and full extents. Bind review to exact source/native hashes. ERC/DRC do not prove solderability, mechanical strength or physical access.

## Later outputs and receipt

Manufacturing export is a separate authorized task: check the pinned CLI's export help, generate into a new isolated output directory, then review copper/mask/paste/silk/outline/drill renders, V-cut interpretation and top placement against the same native hash. BOM has one exact header per board; CPL contains that header only with checked units, origin, top side and orientation. No export commands are executed or manufacturing files supplied here.

Only then check actual C161692 stock/price and quantity interpretation, obtain owner order authorization, and inspect received coupons using CONCRETE-DESIGN.md and the retained handling worksheet. Do not make supplier design enquiries. Grip dimensions, board bow, wire identity and repeat-flex behavior remain measurements, not prerequisites for authoring this generous coupon.
