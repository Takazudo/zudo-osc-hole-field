# Current panel remains a usable fixed-layout draft; stale explanations corrected

2026-10-18 audit baseline: `142da27810994bc01f99bc2e6e1a559cd8f9c884`, draft PR #287 / Issue #278. No panel hardware movement, circuit change, aesthetic redesign or manufacturing regeneration. Parent #286 remains `b58068fbaeb65886958a67a4f4978613414e31c5`.

[Clean current source preview](current-panel.html) · [SVG](current-panel.svg) · [browser image](current-panel.png) · [complete machine-readable audit](audit.json). HTML/SVG are source illustrations, not native KiCad output or machining data. Open the HTML locally or serve this directory. The retained native render in `boards/panel/reports/panel-top.png` is separate evidence. Both Stage36 layout viewers and all coupon files are preserved.

## Audit result and correction matrix

| Area | Result | Action / authority / limit |
| --- | --- | --- |
| 438 centres | VERIFIED SOURCE MATCH | Every UID, kind, XY, reference and aperture in retained native feature table matches `design/grid/placements.lock.json` plus panel window parameters. 324 NPTH apertures + 114 undrilled windows. This is retained-data comparison, not a new native readback. |
| 33 functions, 180 ports, 144 controls | VERIFIED SOURCE MATCH | Every field declared in block-contracts matches the imported grid. Expanding current `design/spec/instrument.py` then matches all 438 physical UIDs/references exactly once. Independent source-path review finds 98 inputs and 82 outputs with no reversals. Connectivity/performance is not established by UID matching. |
| Labels | SOURCE CORRESPONDENCE; TWO OPEN SEMANTICS | Port/control keys and labels map to current parts. G06 and G07 below remain owner questions; no silent renaming or behavior change. Two A/B controls use module headings instead of separate control labels, explaining 142 control labels for 144 controls. |
| Imported pot values | 48 STALE ELECTRICAL ANNOTATIONS | Current DC-control parts select PTV09A-4020F-B104, not inherited B103. `audit.json.electrical_overrides` records each UID, old annotation, current MPN, role and source. Other pots: 51 B103 and 2 B504 (H1/H2 SLEW). Lock/grid/contract bytes and current circuit BOM remain unchanged. |
| Perimeter jack claim | CORRECTED | Current outer x=14.5/303.5, not 6.5/311.5. Trial Ø8.3 nut gives 10.35 mm nearest edge and 7.35 mm beyond the inner border edge. No border intrusion for that trial. Exact nut fit is not qualified by this arithmetic. |
| Actual border exclusions | RETAINED | Owner 0.27 mm copper lines at x=2.2/315.8 and y=2.2/295.8 remain excluded from clip coverage. P collars reach x=1.9/316.1, retaining 1.1 mm projection into the 0–3 mm border. No clip profile/strength is selected by this correction. |
| R21 vs current artwork defaults | INTENTIONAL PROFILES, NOW EXPLICIT | Historical UI/proofs use 0.85 mm switch words and 0.5 mm separator clearance. Panel export uses 1.0/2.5 for native stroke-font clearance, documented in prior visual review. Current preview and export share `art_profile.cjs`; no new aesthetic choice. Historical HTML/proofs remain unchanged. |
| OCT preview cutout | CORRECTED CURRENT EXPORT | Current art-only call reads Ø7 mm from lock instead of the renderer's legacy Ø6.3 default. Only five unstroked dark background circles change; these are ignored by native artwork conversion. Convertible copper/mask/silk primitives remain equal. Current source preview overlays all 438 actual source aperture sizes, including Ø1.6 undrilled windows. |
| Native panel evidence | RETAINED RECEIPT MATCH | Existing KiCad 10.0.6 board, DRC, feature table and render hashes still match. No fresh DRC/render claimed. Installed cloud CLI is 9.0.2 and rejected; no installation/image pull. |
| Physical assembly | CUSTOM INTEGRATION QUESTIONS OPEN | Source dimensions and manufacturer lands/pins are the normal basis for standard parts. Actual custom collars/clips, selector carrier, optical stack, tool/latch/grip envelopes and service sequence need integrated geometry review and, where necessary, a representative mock-up. No blanket per-component coupon gate. |

## All 33 blocks remain present

Counts below are deterministic from `audit.json`; “mapped” means UID/reference correspondence, not circuit qualification. Every row retains unverified integrated physical fit.

<!-- block-matrix:start -->
| Block | Family | In / out | Controls | LEDs | Electrical overrides | Semantic status |
| --- | --- | --- | --- | --- | --- | --- |
| O1 | OSC | 4 / 4 | 8 | 0 | 3 | NO NEW QUESTION IDENTIFIED |
| O2 | OSC | 4 / 4 | 8 | 0 | 3 | NO NEW QUESTION IDENTIFIED |
| O3 | OSC | 4 / 4 | 8 | 0 | 3 | NO NEW QUESTION IDENTIFIED |
| O4 | OSC | 4 / 4 | 8 | 0 | 3 | NO NEW QUESTION IDENTIFIED |
| O5 | OSC | 4 / 4 | 8 | 0 | 3 | NO NEW QUESTION IDENTIFIED |
| F1 | VCF | 4 / 4 | 6 | 4 | 3 | G06 OPEN |
| F2 | VCF | 4 / 4 | 6 | 4 | 3 | G06 OPEN |
| F3 | VCF | 4 / 4 | 6 | 4 | 3 | G06 OPEN |
| M5A | MIX5 | 5 / 1 | 6 | 7 | 0 | NO NEW QUESTION IDENTIFIED |
| M5B | MIX5 | 5 / 1 | 6 | 7 | 0 | NO NEW QUESTION IDENTIFIED |
| M4A | MIX4 | 5 / 1 | 6 | 7 | 1 | NO NEW QUESTION IDENTIFIED |
| M4B | MIX4 | 5 / 1 | 6 | 7 | 1 | NO NEW QUESTION IDENTIFIED |
| W2 | FOLD | 3 / 1 | 4 | 3 | 2 | NO NEW QUESTION IDENTIFIED |
| W1 | FOLD | 3 / 1 | 4 | 3 | 2 | NO NEW QUESTION IDENTIFIED |
| E1 | AR | 3 / 4 | 6 | 5 | 2 | G07 OPEN |
| A01 | AO | 2 / 1 | 2 | 4 | 1 | NO NEW QUESTION IDENTIFIED |
| E2 | AR | 3 / 4 | 6 | 5 | 2 | G07 OPEN |
| A02 | AO | 2 / 1 | 2 | 4 | 1 | NO NEW QUESTION IDENTIFIED |
| E3 | AR | 3 / 4 | 6 | 5 | 2 | G07 OPEN |
| A03 | AO | 2 / 1 | 2 | 4 | 1 | NO NEW QUESTION IDENTIFIED |
| E4 | AR | 3 / 4 | 6 | 5 | 2 | G07 OPEN |
| A04 | AO | 2 / 1 | 2 | 4 | 1 | NO NEW QUESTION IDENTIFIED |
| E5 | AR | 3 / 4 | 6 | 5 | 2 | G07 OPEN |
| A05 | AO | 2 / 1 | 2 | 4 | 1 | NO NEW QUESTION IDENTIFIED |
| E6 | AR | 3 / 4 | 6 | 5 | 2 | G07 OPEN |
| A06 | AO | 2 / 1 | 2 | 4 | 1 | NO NEW QUESTION IDENTIFIED |
| B1 | MULT | 1 / 3 | 0 | 1 | 0 | NO NEW QUESTION IDENTIFIED |
| B2 | MULT | 1 / 3 | 0 | 1 | 0 | NO NEW QUESTION IDENTIFIED |
| H1 | SH | 2 / 1 | 2 | 3 | 0 | NO NEW QUESTION IDENTIFIED |
| X1 | SWITCH | 2 / 1 | 1 | 3 | 0 | NO NEW QUESTION IDENTIFIED |
| H2 | SH | 2 / 1 | 2 | 3 | 0 | NO NEW QUESTION IDENTIFIED |
| X2 | SWITCH | 2 / 1 | 1 | 3 | 0 | NO NEW QUESTION IDENTIFIED |
| N1 | NOISE | 0 / 4 | 0 | 0 | 0 | NO NEW QUESTION IDENTIFIED |
<!-- block-matrix:end -->

## Circuit meanings checked beyond the imported contract

| Family | Current source paths / panel meaning |
| --- | --- |
| OSC O1–O5 | `oscillator.py`: 1V/OCT, FM, PWM, SYNC inputs; SIN/TRI/SAW/PUL outputs; OCT/RANGE/SYNC/TUNE/FINE/FM±/PW/PWM± remain. No panel lamps added. Six calibration trimmers remain internal. |
| VCF F1–F3 | `filter.py`: IN plus FREQ/RES/GAIN CV inputs, LP/BP/HP and parallel dry OUT. **G06:** manual GAIN and GAIN CV/depth control dry OUT only, not LP/BP/HP. Existing implementation proposal; owner confirmation remains open in `filter-work-note.md`. |
| MIX5 M5A/B | `mix5.py`, `mixer_common.py`: five attenuverting inputs, summed output and LEVEL. |
| MIX4 M4A/B | `mix4_vca.py`, `mixer_common.py`: four attenuverting inputs, ATTEN CV/depth plus manual LEVEL command VCA; SUM output. |
| FOLD W2/W1 | `wavefolder.py`: IN, FOLD/BIAS CV and OUT; FOLD/BIAS manual, FOLD CV depth and LEVEL remain. W2 stays left of W1. |
| ENV E1–E6 | `envelope.py`, `envelope_logic.py`: **G07:** SIG is conditioned gate/trigger, ORed with manual TRIG; rising edges retrigger from present level. ASR sustains while high, AR completes, LOOP restarts after EOC. ENV/BIP/EOC/STG outputs; RISE/FALL, MODE/SHAPE/STAGE controls. Not an envelope follower; owner confirmation remains open. |
| AO A01–A06 | `offset.py`: IN attenuation/inversion plus manual OFFSET and OFFSET CV sum to OUT. |
| MULT B1/B2 | `mult.py`: one input, three buffered outputs. |
| SH H1/H2 | `sample_hold.py`: TRIGGER and IN; manual SAMPLE, B504 SLEW and OUT. No hidden noise normal. |
| SWITCH X1/X2 | `manual_ab.py`: IN-A/IN-B selected manually to OUT; no clock, CV or crossfade added. |
| NOISE N1 | `noise.py`: WHITE/PINK/BLUE/BROWN outputs; no inputs or controls. |

Sources above are under `design/spec/modules/`. `audit.json.bindings` records actual selected MPN, role and terminal nets for every panel UID. This confirms capture and traceability, not analogue performance, installed wire routing, final protection or manufacturing readiness.

### Indicator legend must follow the monitored node

There are 92 magnitude, 12 stage and 10 clip windows; current exact emitter selections remain source records, not measured optical results.

- Magnitude indicates signal strength, not polarity, cable presence or calibrated volts. Current input magnitude paths are recorded in each module.
- MIX input magnitude follows the post-attenuverter signal. SUM magnitude follows LEVEL/VCA, while red SUM clip monitors **SUM_PRELEVEL**. Red can remain on when LEVEL is reduced. MIX4 ATTEN magnitude monitors buffered CV, not VCA command (`mixer_common.py`, `mix4_vca.py`).
- AO OUT magnitude/clip monitors `OUT_INTERNAL` before output protection (`offset.py`).
- ENV RISE/FALL stage lamps show stage-gated envelope magnitude; they are distinct from SIG/RISE/FALL input lamps (`envelope.py`).
- Nominal clip threshold remains ±10 V (`design/standard/electrical-standard.json`); no hold/hysteresis is promised. Historical UI's same-port magnitude/clip value does not represent mixer node separation. Its arbitrary brightness and ideal polynomial AR/ASR curves are educational; immediate LOOP restart omits current EOC dead time. The new preview has no simulation.

### Electrical annotations have explicit precedence

The placement lock owns XY/kind/apertures. Its imported `component` field and the R21 grid/block-contract annotations describe handoff provenance, not a current BOM. Current `design/spec/instrument.py` expansion owns this audit's electrical selection. The 48 B104 overrides are OSC TUNE/FINE/PW ×5 (15), VCF FREQ/RES/GAIN ×3 (9), MIX4 LEVEL ×2 (2), FOLD FOLD/BIAS ×2 (4), ENV RISE/FALL ×6 (12), AO OFFSET ×6 (6). B103/B104 share the PTV09A-4020F mechanical family; this reconciliation changes no body/shaft/hole. It does not invent interchangeability or change the circuit to match stale metadata.

## Remaining decisions and next work

1. Owner confirm or revise G06 dry OUT-only gain and G07 gate/trigger semantics before final panel wording. A different behavior requires an explicit circuit/label impact proposal; no circuit change is made here.
2. Retain fixed panel positions. Resolve custom support/clip exclusions, selector carrier/adapter, optics and actual tool/service envelopes with dimensions and an integrated mock-up where source geometry cannot establish access. Conceptual envelope overlaps in the Stage36 whole-layout viewer are not proof of physical interference.
3. Standalone GH4 coupon **not ordered**, purchase **deferred**, not a mandatory gate. Files remain optional historical work; cart untouched. Normal standard-part basis: manufacturer dimensions/recommended land/pin numbering, CAD and assembly-preview comparison. Custom latch/grip envelope belongs to integrated access design, not standard connector requalification or endurance testing. GH is not frozen: parent is comparing IDC/ribbon alternatives separately. No substitution is adopted; standard Eurorack power and bespoke signal pinouts must never become accidentally interchangeable.
4. After correctness/semantics, plan aesthetic variants separately. This audit does not choose new styling, move controls, enlarge holes or change front artwork intent.

## Reproduce the source audit

From repository root:

```sh
python3 scripts/panel/audit_current.py --check
node scripts/panel/render_current.cjs --check
node scripts/panel/test_current_art.cjs
python3 -m unittest scripts.panel.test_current_audit
python3 -O -m unittest scripts.panel.test_current_audit
python3 scripts/panel/check_review_receipt.py
```

Regenerate source audit/preview by omitting `--check` from the first two commands; review the resulting hashes and matrix. Tests are source tests. Do not repin native receipts as a substitute for native execution.

### Minimal local native handoff

No manufacturing export is needed for the two documentation fixes or five ignored dark SVG circles. Existing native geometry/artwork bytes remain untouched. If later native panel regeneration is authorized, use an existing **KiCad 10.0.6** installation/image through `scripts/kicad/run.sh`; do not use cloud 9.0.2. Mac can set `KICAD_CLI_BIN=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`; WSL uses the existing digest in `scripts/kicad/pin.env`. Verify exact version first, then `bash scripts/panel/regen.sh` in an isolated checkout. Compare board/art/feature bytes, run native DRC/render using the exact commands in `boards/panel/reports/native-review.json`, and independently review before refreshing that receipt. Stop on drift instead of rewriting expected hashes. No manufacturing output, supplier upload or order is authorized by this handoff.

Owner connector direction: use standard, readily sourced and replaceable connectors with flexible cable assembly. Flying-bus and `Takazudo/zudo-bus` are owner-supplied references for a separate comparison, not a selected interface here. This does not imply 16-pin power connectors on every signal interface.

Owner stack constraint update: minimum thinness is no longer mandatory. Additional board separation and enclosure depth may be proposed for standard connectors, cable bends and service access. The mentioned 5 mm is an example, neither a target nor a limit. This supersedes using the previous narrow cassette/depth as a fixed requirement for new proposals; canonical stack dimensions are unchanged here. Finish this panel audit first, then compare standard power/signal connector stacks using actual mating-envelope dimensions.
