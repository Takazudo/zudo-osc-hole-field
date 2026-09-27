# 03 — Handoff parts research: 22 candidates, zero retained evidence, every panel-hardware footprint needs an audit

Explorer 03 of 9. Exploration only; nothing was modified in any repo or in the handoff.
Date of all checks: 2026-09-28.

Path aliases used below:

- `<HANDOFF>` = `$DROPBOX_CCLOGS_DIR/zudo-osc-hole-field/handoff-r21/zudo-osc-playground-r21-handoff`
- `<SCRATCH>` = `<scratch>/03-handoff-parts-research` (throwaway; will not survive the session)

Verification marks:

| Mark | Meaning |
| --- | --- |
| `[V-file]` | Verified by parsing a handoff or sibling-repo file with python3/grep |
| `[V-e2k]` | Verified by running the project's documented importer `easyeda2kicad 1.0.1` for that LCSC id into `<SCRATCH>/e2k/` |
| `[V-gitlab]` | Verified against the KiCad official library `master` branch on gitlab.com (read-only listing / raw file) |
| `[V-remote]` | Verified against GitHub remote `main` via `gh api` (read-only) |
| `UNVERIFIED` | From memory or inference; must be checked against a retained primary source |

---

## 1. The handoff parts data is one 22-row register in two copies, plus 3 interconnect rows that live only in the R17 file

- `<HANDOFF>/payload/project/osc-playground/workbench/parts/components.json` and `<HANDOFF>/payload/research/osc-playground/component-candidates.json` are JSON-identical (22 rows each) `[V-file]`.
- The 22 `part-*.mdx` pages under `<HANDOFF>/payload/doc/src/content/docs/research/` are a 1:1 rendering of those rows (sidebar positions 30–51). They add no fact that is not in the JSON `[V-file]`.
- `workbench/reference/r17-component-decisions.json` has 8 rows. Five repeat register parts with a machine-readable status; three are interconnect candidates that appear nowhere else: `PZ254V-11-10P` (C492409), `PM254V-11-10-H85` (C46595975), and the Samtec TSW/SSW family `[V-file]`.
- `pin-map-intake.json` holds exactly two pin maps: `LF398M/NOPB_SOIC14` and `OPA4197IPWR_TSSOP14` `[V-file]`.
- Referenced but absent from the archive: `workbench/parts/source-downloads.json` (named by `datasheets/README.md`) and `workbench/docs/MECHANICAL.md` (named by `mechanical/README.md`) `[V-file]`.

### Panel counts reproduce exactly from `layout/grid.json`

| Item | Count | Breakdown `[V-file]` |
| --- | --- | --- |
| Jacks | 180 | 98 IN + 82 OUT; all `component: qingpu-wqp518ma`; 18 x 10 cells fully occupied |
| Pots | 101 | OSC 25, VCF 18, MIX5 12, MIX4 12, AR 12, AO 12, FOLD 8 (= 99 x B103) + SH 2 (B504) |
| Octave selectors | 5 | O1–O5, control row 0, columns 0–4 (adjacent) |
| 2-position toggles | 19 | 5 RANGE + 6 SHAPE + 6 STAGE + 2 A/B |
| 3-position toggles | 11 | 5 SYNC (SOFT/OFF/HARD) + 6 MODE (ASR/AR/LOOP) |
| Buttons | 8 | 6 TRIG + 2 SAMPLE |
| Magnitude LEDs | 92 | ports with `led: true`; 78 on inputs, 14 on outputs |
| Stage LEDs | 12 | 6 RISE + 6 FALL pots carry a `stage` key (hard-coded `12` in `prepare_data.py`) |
| Clip LEDs | 10 | M5A/M5B/M4A/M4B `.SUM` + A01–A06 `.OUT` |

Grid position formula (compact preset `px=17, py=14`) `[V-file: src/render.js]`:
`x = 6 + (col + 0.5) * 17`; `y = (22 for jacks | 178 for controls) + (row + 0.5) * 14`; panel 318 x 298 mm.

---

## 2. Master table A — identity, quantity, status, source, supply note

Status vocabulary: **user-selected** (owner decision recorded in `decisions.json` or `r17-component-decisions.json`), **candidate**, **unresolved**.
"Est. qty" uses grid counts where the part is panel hardware. For ICs it gives the handoff figure first, then this explorer's estimate (see section 9), clearly labelled.

| # | id | Manufacturer | Full MPN | Role | Package | Est. qty | Status | Primary source URL in handoff | Supply note in handoff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `bourns-ptv09a-4020f-b103` | Bourns | PTV09A-4020F-B103 | All original continuous controls (10 k linear start value) | PTV09A-4, vertical, bushingless, 6 mm F shaft, L=20 | 99 positions (value/taper per circuit still open) | **user-selected** mechanical family (D06; r17 `MECHANICAL_FAMILY_SELECTED_VALUE_PER_CIRCUIT`); electrical value unresolved | https://www.bourns.com/docs/product-datasheets/PTV09.pdf | JLC C5848782; no stock statement |
| 2 | `bourns-ptv09a-4020f-b504` | Bourns | PTV09A-4020F-B504 | H1.SLEW, H2.SLEW rheostats (500 k linear) | same mechanics as #1 | 2 | **candidate** (D08 is an engineering proposal, not owner-approved) | same PDF | JLC C5154140; "zero stock / minimum 10" at snapshot; pre-order or external route |
| 3 | `alps-srbv160803` | Alps Alpine | SRBV160803 | 5 octave selectors, 6 positions | Vertical rotary, body 16.2 x 18.5 x 7.5 mm | 5 | **user-selected** (r17 `USER_SELECTED`) | https://tech.alpsalpine.com/e/products/detail/SRBV160803/ | JLC C470374; no stock statement |
| 4 | `dailywell-2ms1` | Dailywell | 2MS1T1B1M2QES-5 | 2-position ON-ON selectors | Sub-mini SPDT, PC pins | 19 | **user-selected** (r17 `USER_SELECTED`) | https://www.lcsc.com/product-detail/C908280.html | JLC/LCSC C908280, "identity rechecked" |
| 5 | `dailywell-2ms3` | Dailywell (sold by Thonk as DW2) | 2MS3T1B1M2QES | 3-position ON-OFF-ON | Sub-mini SPDT center-off | 11 | **user-selected** design intent; sourcing **unresolved** (r17 `DESIGN_SELECTED_EXTERNAL_SOURCING`) | https://www.thonk.co.uk/wp-content/uploads/2017/05/DW2-SPDT-ON-OFF-ON-2MS3T1B1M2QES.pdf | No JLC/LCSC code; consignment needed |
| 6 | `omron-b3f1020` | Omron | B3F-1020 | 6 TRIG + 2 SAMPLE buttons | THT tactile 6 x 6, 5 mm height | 8 | **candidate** | https://jlcpcb.com/partdetail/OmronElectronics-B3F1020/C722171 | JLC C722171 "verified"; no manufacturer link at all |
| 7 | `qingpu-wqp518ma` | Qingpu (WQP) | WQP518MA ("Thonkiconn") | All patch points | THT threaded 3.5 mm mono jack | 180 (+98 black and 82 red dress nuts, no MPN) | **candidate** (r17 `CANDIDATE_EXACT_NUT_MATING_OPEN`) | https://www.thonk.co.uk/shop/thonkiconn/ | JLC C9900052034 "earlier sourcing record"; "does not prove normal-stock availability" |
| 8 | `kento-white` | KENTO | KT-0603W | Magnitude + stage indicators | 0603 top emitter | 104 | **candidate** (carry-forward sample) | https://jlcpcb.com/partdetail/C2290 | JLC C2290 |
| 9 | `kento-red` | KENTO | KT-0603R | Clip indicators | 0603 top emitter | 10 | **candidate** (carry-forward sample) | https://jlcpcb.com/partdetail/C2286 | JLC C2286 |
| 10 | `alfa-as3340d` | ALFA RPAR | AS3340D | 5 oscillator cores | SOIC-16 | 5 | **candidate**, external; "not requalified" | https://www.alldatasheet.com/html-pdf/1159050/ALFA/AS3340/110/1/AS3340.html (a mirror, not the manufacturer) | No JLC/LCSC code |
| 11 | `electric-druid-noise2` | Electric Druid | NOISE2 | Shared noise source for 4 outputs | Programmed PDIP (8-pin, UNVERIFIED) | 1 | **candidate**, external programmed part | https://electricdruid.net/noise2-white-pink-noise-source/ | No JLC/LCSC code; bought programmed from the creator |
| 12 | `st-tl074` | STMicroelectronics | TL074CDT | General mixers / filters / folders / A-B buffers | SOIC-14 | Handoff: "circuit-dependent". Preview: 26 SOIC-14 rectangles. Explorer estimate: 66–89 | **candidate** (carry-forward) | https://www.st.com/resource/en/datasheet/tl074.pdf | JLC C6963 |
| 13 | `ti-lm13700` | Texas Instruments | LM13700M/NOPB | MIX4 gain cells, 3 filter/VCA blocks | SOIC-16 | Handoff: "circuit-dependent". Preview: 3. Explorer estimate: 7–8 | **candidate** (carry-forward) | https://www.ti.com/product/LM13700 | JLC C1346265 |
| 14 | `ti-lf398m` | Texas Instruments | LF398M/NOPB | 2 S&H cells | SOIC-14 | 2 | **candidate** | https://www.ti.com/product/LF398-N (queue: `https://www.ti.com/lit/gpn/lf398-n`, SNOSBI3C) | LCSC C1346172 verified; "JLC assembly listing not verified" |
| 15 | `ti-hc221` | Texas Instruments | CD74HC221M96 | Dual one-shot for both S&H triggers | SOIC-16 | 1 | **candidate** | https://www.ti.com/product/CD74HC221 | JLC C133954; "order review pending" |
| 16 | `ti-lm393` | Texas Instruments | LM393DR | Trigger conditioning, optional clip detectors | SOIC-8 | Handoff: 1 + "more". Preview: 7 SOIC-8. Explorer estimate: up to 17 | **candidate** | https://www.ti.com/lit/gpn/lm393 | JLC C67470 "verified" |
| 17 | `kemet-hold-10n` | KEMET | C0805C103J5GACTU | LF398 hold capacitor, 10 nF C0G 50 V 5 % | 0805 | 2 | **candidate** | https://jlcpcb.com/partdetail/KEMET-C0805C103J5GACTU/C2167597 | JLC C2167597 "verified" |
| 18 | `fh-c0g-100n-slew` | FH (Fenghua) | 1206CG104J500NT | SLEW lag bank, 5 x 100 nF per channel | 1206 | 10 | **candidate** | https://jlcpcb.com/partdetail/47351-1206CG104J500NT/C46348 | JLC C46348; primary capacitor spec not retained |
| 19 | `ti-opa4197` | Texas Instruments | OPA4197IPWR | 6 MULT buffers + 4 SLEW buffers | TSSOP-14 | 3 | **candidate** | https://www.ti.com/lit/ds/symlink/opa4197.pdf (SBOS737C) | JLC C2057327; "pre-order / no allocated stock" |
| 20 | `ti-tmux6111` | Texas Instruments | TMUX6111PWR | Alternative discrete S&H switch | TSSOP-16 | 0 (alternative, not fitted) | **candidate**, not fitted | https://www.ti.com/product/TMUX6111 | No JLC code assigned |
| 21 | `interconnects` | not selected | "Exact keyed header + socket / terminated harness set" | Interface-to-core interconnect | to select | derived from circuit boundary | **unresolved** ("Not selected") | https://www.samtec.com/products/ssw | none |
| 22 | `zudo-pd` | owner project | zudo-pd Board P + Board B | Power supply | separate assembly | 1 assembly | **user-selected** reuse (D10) | https://github.com/Takazudo/zudo-pd | n/a |
| R17-a | `header` | XFCN | PZ254V-11-10P | 1 x 10 male header, 2.54 mm | THT | unassigned | **candidate**, not assigned (r17 `CONNECTOR_CANDIDATE_NOT_ASSIGNED`) | https://jlcpcb.com/partdetail/PZ254V-11-10P/C492409 | JLC C492409 |
| R17-b | `socket` | XFCN | PM254V-11-10-H85 | 1 x 10 female socket, 8.5 mm insulator | THT | unassigned | **candidate**, not assigned | https://jlcpcb.com/partdetail/XFCN-PM254V_11_10H85/C46595975 | JLC C46595975 |
| R17-c | `connector-pair-family` | Samtec | TSW / SSW (no suffix) | Documented mating-family alternative | THT | unassigned | **unresolved** | https://www.samtec.com/products/ssw | none |

Register-wide facts `[V-file]`: 38 source links, 37 distinct URLs; hosts: jlcpcb.com 17, ti.com 7, thonk.co.uk 3, bourns.com 2, lcsc.com 2, electricdruid.net 2, one each for alpsalpine, st.com, alldatasheet, samtec, github. Only 3 URLs are direct PDFs. Nine rows have no manufacturer-origin link at all: `fh-c0g-100n-slew`, `dailywell-2ms1`, `dailywell-2ms3`, `omron-b3f1020`, `qingpu-wqp518ma`, `kento-white`, `kento-red`, `alfa-as3340d`, `zudo-pd`. Six rows have `code: null`. `research_checked_in_this_pass` is true for 10 rows, false for 10, missing for 2.

---

## 3. Master table B — CAD assets: ICs and chips are covered; all seven panel-hardware parts need an audited or custom footprint

Sibling convention `[V-file]`: neither sibling uses the stock KiCad libraries for parts. Each keeps ONE project symbol file and ONE project footprint library, populated with `easyeda2kicad --lcsc_id <C> --footprint --symbol --3d`, and hand-drawn only for pads/test points. The single stock exception is `MountingHole:MountingHole_3.2mm_M3` (8 instances in the lamp PCBs). KiCad itself is NOT installed in this WSL (`kicad-cli` not found); stock names below were therefore verified on GitLab, not locally.

| id | LCSC id | Importer result `[V-e2k]` | Stock KiCad symbol `[V-gitlab]` | Stock KiCad footprint `[V-gitlab]` | Verdict | Drawing dimensions still needed | In handoff? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `bourns-ptv09a-4020f-b103` | C5848782 | Symbol `PTV09A-4020F-B103` (5 pins named 1–5, no functions). Footprint is a FAMILY file `SW-TH_PTV09A-4015F-B502` + 3D of the 15 mm-shaft variant | `Device:R_Potentiometer_MountingPin` | `Potentiometer_THT:Potentiometer_Bourns_PTV09A-1_Single_Vertical` (named -1, not -4) | **IMPORT + AUDIT** | Pin 1/2/3 to CCW/wiper/CW; lug spacing and slot size; shaft centre to pin row; body outline; shaft datum for L=20; seated height | NO — only envelope `10 x 10 x 6.8`, shaft Ø6, panel hole Ø6.3 |
| `bourns-ptv09a-4020f-b504` | C5154140 | **FAILED** twice: "Failed to fetch data from EasyEDA API" | same | same | **REUSE #1 footprint**, new symbol value | same as above | NO |
| `alps-srbv160803` | C470374 | Symbol `SRBV160803` (12 pins named 1–12, no functions). Footprint is a FAMILY file `SW-TH_SRBV141404` + matching 3D | `Switch:SW_Rotary_1x6_MP` (generic) | none | **CUSTOM symbol pin map + AUDITED footprint** | Common and position terminals 1–6; lug position/width and whether lugs are mandatory; shaft/bushing datum; actuator L=15 datum; panel hole | PARTLY — body 16.2 x 18.5 x 7.5 only |
| `dailywell-2ms1` | C908280 | Symbol + exact-name footprint `SW-TH_2MS1T1B1M2QES-5` + 3D | `Switch:SW_SPDT` | none | **IMPORT + AUDIT** | Terminal to throw direction; bushing thread and length; nut AF; lever sweep; seated height | NO — envelope `8.13 x 5.08 x 8.64`, bushing Ø5, hole Ø5.2 |
| `dailywell-2ms3` | none | not probed (no id) | `Switch:SW_SPDT_MSM` | none | **REUSE #4 footprint (UNVERIFIED same body) + new symbol** | Same as 2MS1, from the Thonk DW2 PDF | NO |
| `omron-b3f1020` | C722171 | Symbol `B3F-1020` (4 separate pins). Footprint `SW-TH_4P-L6.2-W6.5-P4.50-S7.30` + 3D | `Switch:SW_Push` | `Button_Switch_THT:SW_PUSH_6mm_H5mm` | **IMPORT + AUDIT** (see conflict 4.3) | Hole pattern; internal pairing of terminals; plunger height/stroke; cap/plunger part | NO — envelope `6 x 6 x 5`, plunger Ø5 |
| `qingpu-wqp518ma` | C9900052034 | **FAILED** twice | `Connector_Audio:AudioJack2_SwitchT` | `Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles` | **CUSTOM footprint derived from stock** (re-anchored at barrel centre, tightened courtyard) | Proof that WQP518MA equals PJ398SM; pin positions and slot/hole sizes; shoulder height above PCB; bushing thread and length; nut OD/thickness; panel hole | NO — trial values only: nut Ø8.3, plug Ø9.6, hole Ø6.2, body `9.5 x 10 x 8` |
| `kento-white` | C2290 | Symbol `0603Whitelight_C2290`, footprint `LED0603-R-RD_WHITE` + 3D | `Device:LED` | `LED_SMD:LED_0603_1608Metric` (UNVERIFIED name) | **REUSE from zudo-pd** (identical names) | Emitter height; viewing angle; optical path to a 1.32 mm aperture | NO |
| `kento-red` | C2286 | Symbol `KT-0603R`, footprint `LED-SMD_L1.6-W0.8-R-RD` + 3D | `Device:LED` | same | **REUSE from zudo-pd** (its copy uses footprint `LED0603-RD`; importer now returns a different footprint name) | same | NO |
| `alfa-as3340d` | none | not probed | `Audio:AS3340` | `Package_SO:SOIC-16_3.9x9.9mm_P1.27mm` (UNVERIFIED name) | **STOCK symbol copied into project lib + generic SOIC-16** | Pinout from a genuine ALFA datasheet | NO |
| `electric-druid-noise2` | none | not probed | none | `Package_DIP:DIP-8_W7.62mm` (UNVERIFIED name) | **CUSTOM symbol**, generic DIP-8 footprint | 8-pin function map from the Electric Druid datasheet | NO |
| `st-tl074` | C6963 | Symbol `TL074CDT` (single block, 14 pins), footprint `SOIC-14_L8.7-W3.9-P1.27-LS6.0-BL` | `Amplifier_Operational:TL074` (multi-unit) | generic SOIC-14 | **STOCK multi-unit symbol preferred**; importer footprint | none beyond package drawing | n/a |
| `ti-lm13700` | C1346265 | Symbol `LM13700M/NOPB`, footprint `SOIC-16_L9.9-W3.9-P1.27-LS6.0-BL` + 3D | `Amplifier_Operational:LM13700` | generic SOIC-16 | same | none | n/a |
| `ti-lf398m` | C1346172 | Symbol `LF398M/NOPB` (14 pins), footprint SOIC-14 + 3D | `Analog:LF398_SOIC14` | generic SOIC-14 | same | none | Pin map present in `pin-map-intake.json` |
| `ti-hc221` | C133954 | Symbol `CD74HC221M96`, footprint SOIC-16 + 3D | only `74xx:74LS221` (no HC221) | generic SOIC-16 | **IMPORT** | none | NO pin map |
| `ti-lm393` | C67470 | Symbol `LM393DR`, footprint `SOIC-8_L5.0-W4.0-P1.27-LS6.0-BL` + 3D | `Comparator:LM393` | generic SOIC-8 | STOCK or IMPORT | none | NO pin map |
| `kemet-hold-10n` | C2167597 | **FAILED** twice | `Device:C` | sibling `C0805` | **REUSE sibling `C0805`** | none | n/a |
| `fh-c0g-100n-slew` | C46348 | Symbol `1206CG104J500NT`, footprint `C1206` + 3D | `Device:C` | sibling `C1206` | **REUSE sibling `C1206`** | none | n/a |
| `ti-opa4197` | C2057327 | Symbol `OPA4197IPWR`, footprint `TSSOP-14_L5.0-W4.4-P0.65-LS6.4-BL` + 3D | `Amplifier_Operational:OPA4197xPW` | generic TSSOP-14 | STOCK multi-unit symbol preferred | none | Pin map present |
| `ti-tmux6111` | none | not probed | none found (searched `TMUX6*`) | generic TSSOP-16 | CUSTOM symbol only if the alternative is adopted | pinout | NO |
| `header` PZ254V-11-10P | C492409 | Symbol + `HDR-TH_10P-P2.54-V-M` + 3D; drill 1.10 | `Connector_Generic:Conn_01x10` (UNVERIFIED name) | `Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical` | IMPORT (same family as sibling 6-pin) | mating pin length, insulator height | Partly: "2.54 mm, 10-position" |
| `socket` PM254V-11-10-H85 | C46595975 | Symbol + `HDR-TH_10P-P2.54-V-F-5` + 3D; drill 1.10 | same | `Connector_PinSocket_2.54mm:PinSocket_1x10_P2.54mm_Vertical` | IMPORT | body height, insertion depth | Partly: "8.5 mm insulator height" |

Importer summary `[V-e2k]`: 18 ids tried, **15 resolved** to a symbol + footprint whose MPN matches the handoff claim, **3 failed** on two attempts each (C5154140, C9900052034, C2167597). A failure means EasyEDA has no CAD record for that id; it does not by itself prove the id is wrong. All three still need an independent identity check.

Two pin maps agree between two independent non-primary sources `[V-file + V-e2k]`: LF398M/NOPB SOIC-14 (1 INPUT, 3 V−, 7 OUTPUT, 8 hold cap, 10 LOGIC REF, 11 LOGIC, 12 V+, 14 OFFSET ADJ) and OPA4197IPWR (standard quad, 4 V+, 11 V−). Neither source is a retained manufacturer document.

Format note `[V-file + V-e2k]`: the importer writes symbol file `version 20211014` and legacy `(module ...)` footprints. Siblings store footprints in that legacy form inside KiCad 10 projects (`board-p.kicad_pcb` is `version 20260206`, `generator_version "10.0"`; `zudo-led-lamp.kicad_sym` is `version 20251024`). The same pipeline therefore works unchanged.

---

## 4. The imports expose five geometry conflicts with the fixed grid

All five are derived from imported or stock footprints, not from manufacturer drawings. Each is UNVERIFIED until the drawing is retained, but each is large enough to decide before any layout work.

### 4.1 OCT row: adjacent SRBV160803 mounting lugs collide at the 17 mm column pitch

- Imported footprint `SW-TH_SRBV141404`: 10 signal pads in two rows of five (2.54 mm pitch, rows at y = ±9.15), plus 2 lug pads at x = ±8.0, y = −1.1 with Ø2.0 drill and Ø3.0 pad `[V-e2k]`. Its silk outline is exactly 16.2 x 18.5 mm, matching the handoff body envelope.
- O1–O5 sit at x = 14.5, 31.5, 48.5, 65.5, 82.5 (17 mm pitch) `[V-file]`.
- Right lug of OCT n is at +8.0; left lug of OCT n+1 is at 17 − 8.0 = +9.0. Centre distance **1.0 mm** with Ø2.0 drills: the holes merge. Pads (Ø3.0) overlap by 2.0 mm. Footprint courtyard is 19.0 mm wide against a 17 mm pitch.
- The handoff statement "17 mm column grid leaves 0.8 mm body gap" is correct for the bodies and silent on the lugs.
- The preview's O strip spans x = 7 to 90 mm `[V-file: src/three.js]`. OCT1's left lug centre is x = 6.5 and OCT5's right lug centre is x = 90.5. Both fall outside that board outline.

### 4.2 Jack column: stock footprint courtyard is 14.40 mm against a 14 mm row pitch

- Stock `Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles`: pads S (0, 0), TN (0, 3.1), T (0, 11.4); barrel centre at (0, 6.48); F.Fab 9.0 x 12.48; courtyard 10.0 x 14.40 `[V-gitlab]`.
- 180 jacks at 14 mm row pitch give a 0.40 mm courtyard overlap on every vertical neighbour pair. Body-to-body gap is 1.52 mm. Copper gap between one jack's T pad and the next jack's S pad is about 0.62 mm.
- The grid gives the barrel centre, while the stock origin is the sleeve pad. Scripted placement needs a 6.48 mm offset or a re-anchored project copy.

### 4.3 B3F-1020: importer hole pattern is 7.3 x 4.5 mm, stock 6 mm tact pattern is 6.5 x 4.5 mm

`SW-TH_4P-L6.2-W6.5-P4.50-S7.30` pads at (±3.65, ±2.25) `[V-e2k]`; `SW_PUSH_6mm_H5mm` pads at 6.5 x 4.5 `[V-gitlab]`. Both use 1.1 mm drills. The importer symbol has four independent pins; the stock footprint pairs them 1-1 / 2-2. The Omron drawing must decide both points.

### 4.4 PTV09A: lug spacing is 8.6 mm in the import and 8.8 mm in the stock footprint

Import: pins at 2.5 mm pitch, lugs at (±4.3, −3.5), oval drill 2.0 x 2.2, shaft centre 7.0 mm from the pin row `[V-e2k]`. Stock: pins at 2.5 mm pitch, lugs 8.8 mm apart, round drill 2.2, shaft centre 7.0 mm from the pin row `[V-gitlab]`. The shaft-to-pin distance agrees; the lug geometry does not.

### 4.5 Two imports are family files drawn for a different variant

`PTV09A-4020F-B103` arrives with the footprint and 3D model of `PTV09A-4015F-B502` (15 mm shaft, so the 3D shaft is 5 mm short). `SRBV160803` arrives with the footprint and 3D of `SRBV141404`. The sibling lamp project hit the same class of defect: EasyEDA supplied a dual-unit footprint for the single-unit ALPS RK10J11E0034 and the pad identities had to be rewritten from the drawing (`$HOME/repos/circuits/zudo-led-lamp/footprints/vendor/C470643/README.md`) `[V-file]`.

### Preview envelopes are the only mechanical numbers in the handoff

From `workbench/src/three.js` `[V-file]`. None is a pad, drill or datum dimension.

| Part | Body box (mm) | Other preview geometry | Panel hole in preview |
| --- | --- | --- | --- |
| Jack | 9.5 x 10 x 8 | bushing Ø5.8 x 5.2; nut Ø8.3 x 1.35 | Ø6.2 |
| Pot | 10 x 10 x 6.8 | shaft Ø6 x 12.5 | Ø6.3 |
| Octave | 16.2 x 18.5 x 7.5 | shaft Ø6 x 12.5; cap Ø8 x 5 | Ø6.3 |
| Toggle | 8.13 x 5.08 x 8.64 | bushing Ø5 x 5.5; hex nut; lever 9 mm | Ø5.2 |
| Button | 6 x 6 x 5 | plunger Ø5 x 4 | Ø5.0 |
| LED | none | aperture drawn Ø1.32, 6.15 mm right of jack centre | — |
| PCB / panel | 1.6 thick each | — | — |

---

## 5. Sibling libraries cover LEDs, passives, headers, test pads and power-inlet parts; they contain none of the panel hardware or analog ICs

### The local zudo-pd checkout is five weeks behind its remote

| Repo | Local HEAD | Remote `main` `[V-remote]` |
| --- | --- | --- |
| `$HOME/repos/circuits/zudo-led-lamp` | `194d8a2` (2026-09-25 JST) | same commit |
| `$HOME/repos/circuits/zudo-pd` | `797a221` (2026-08-16) | `f25194f` (2026-09-21) |
| `$HOME/repos/myoss/zudo-circuit-doc` | `491f151` (2026-09-27 07:16Z) | `5d0e2b6` (2026-09-27 11:15Z) = the commit the handoff reviewed |

Consequence: the local zudo-pd has only Board A + Board B schematics and no `SMAJ16A`. The handoff's "Board P + Board B" and "SMAJ16A" wording matches remote `main`, which has `boards/board-p/`, `boards/board-b/board-b.kicad_pcb`, and 126 symbols against 99 locally. Nothing was pulled (exploration only).

### `$HOME/repos/circuits/zudo-led-lamp` `[V-file]`

- `symbols/zudo-led-lamp.kicad_sym`: 42 symbols.
  Resistors `0603WAF0000T5E`, `…1000…`, `…1003…`, `…1503…`, `…3302…`, `…4700…`, `…4701…`, `…5101…`, `…5602…`, `0805W8F1002T5E`, `FRC1206F33R0TS`, `FRC2512F33R0TS`, `RLP25FEER200`, `NCP18XH103F03RB`.
  Capacitors `CC0603KRX7R9BB104`, `CL10A105KB8NNNC`, `CL21A226MAQNNNE`, `CL21B104KBCNNNC`, `CL31A106KBHNNNE`.
  ICs `AL8860MP-13`, `AP63203WU-7`, `STM32G031F8P6`, `STUSB4500QTR`, `AO3401A_C347476`.
  Connectors `B6B-XH-A`, `DS254P-2X10-L0`, `PZ254V-11-05P`, `PZ254V-11-06P`, `PM254V-11-06-H85`, `TYPE-C-31-M-17`, `Conn_1x02/03/04/08`.
  Other `BSMD1206-075-30V`, `FNR4030S4R7MT`, `FXL0630-330-M`, `HL-AM-2835H421W-S1-08-HR3`, `PESD24VS1UB,115`, `SMAJ20A_C571370`, `SS26_C7420363`, `RK10J11E0034`, `SS-12D01-G020`, `TestPad`.
- `footprints/kicad/` (31 footprints, each duplicated in `zudo-led-lamp.pretty/`, 3D in `zudo-led-lamp.3dshapes/`):
  `C0603`, `C0805`, `C1206`, `R0603`, `R0805`, `R1206`, `R2512`, `F1206`, `CONN-TH_6P-P2.50_B6B-XH-A-LF-SN`, `HDR-TH_5P-P2.54-V-M`, `HDR-TH_6P-P2.54-V-F`, `HDR-TH_6P-P2.54-V-M`, `IDC-TH_20P-P2.54-V-R2-C10-S2.54`, `IND-SMD_L4.0-W4.0_FNR40XXS`, `IND-SMD_L7.0-W6.6_FXL0630`, `LED-SMD_L3.3-W2.8-RD`, `MSOP-8_…`, `POT-TH_RK10J11E0034`, `PogoPad_1x03/1x04/1x08_P2.54mm`, `QFN-24_…`, `SMA_L4.2-…`, `SMA_L4.3-…`, `SOD-523_…`, `SOT-23_…`, `SW-TH_SS-12D01-G020`, `TSOT-26_…`, `TSSOP-20_…`, `TestPad_D1.5mm`, `USB-C-SMD_10P-…`.
- `footprints/vendor/C470643/` and `C5446803/`: audit READMEs, derived STEP/WRL, `derive-model.py`, `model-audit.json`.
- `.claude/skills/component-*`: 14 owner bundles (plus the central `component-spec-audit` skill), each with the 8-file v1 layout.

### `$HOME/repos/circuits/zudo-pd` local `[V-file]`, with remote additions `[V-remote]`

- `symbols/zudo-pd.kicad_sym`: 99 symbol entries locally (two names appear twice: `KT-0603R`, `2541WR-2X08P`).
- `footprints/kicad/` + `zudo-power.pretty/`: 59 footprints locally (21 owner bundles under `.claude/skills/component-*`), including `LED0603-RD`, `LED0603-R-RD_WHITE`, `LED0603-FD_BLUE`, `LED0805-R-RD`, `HDR-TH_16P-P2.54-H-M-R2-C8-S2.54`, `HDR-TH_3P-P2.54-V-M`, `DIP-14_…`, `SOT-89-3_…`, `TO-252/263 …`, `F1206/F1210/F1812`, `TestPad_D1.5mm`, `PogoPad_1x04/1x08`.
- `footprints/scripts/gen_courtyards.py`: generates every courtyard as pads-plus-body bounding box + 0.25 mm.
- Remote-only additions relevant here: symbols `DW254P-2X8-L0` (C4749189), `WJ500V-5.08-2P` (C8465), `PZ254V-11-06P`, `PM254V-11-06-H85`, `SMAJ16A`, `PWR_FLAG`, nine `RT0603BRD07…` 0.1 % resistors, `GRM32ER71H106KA12L`; footprints `IDC-TH_16P-P2.54_321016RG0ABK00A01`, `WJ500V-5.08-2P_C8465`, `MountingHole_M3`, `MountingHole_HC11_3mm`, `Fiducial_1mm_Mask2mm`, `C1210`.

### Match against this part list

| This project needs | zudo-led-lamp | zudo-pd | Verdict |
| --- | --- | --- | --- |
| KT-0603W, C2290 | — | symbol `0603Whitelight_C2290` + `LED0603-R-RD_WHITE` | **Reuse as is** |
| KT-0603R, C2286 | — | symbol `KT-0603R` + `LED0603-RD` | **Reuse as is** |
| PZ254V / PM254V headers | 5- and 6-pin, with a full evidence bundle `component-xfcn-board-headers` | 6-pin pair (remote only) | Same family; 10-pin footprints are new imports; bundle is a ready template |
| 0603 1 % resistors | 9 UNI-ROYAL values | 10 UNI-ROYAL values + 3 YAGEO | Reuse; add missing values |
| 0.1 % thin-film resistors | — | 9 values (remote only) | Reuse family for V/oct and ladder work |
| 100 nF 0603 X7R decoupling (C14663), 1 µF 0603 (C15849), 10 µF 1206 (C13585) | yes | yes | **Reuse as is** |
| `C0805`, `C1206` footprints for the hold and SLEW capacitors | yes | yes | **Reuse as is** |
| Test pads | `TestPad` + `TestPad_D1.5mm` | `TestPoint` + `TestPad_D1.5mm` | **Reuse as is** |
| Mounting holes, fiducials | stock `MountingHole_3.2mm_M3` | `MountingHole_M3`, `Fiducial_1mm_Mask2mm` (remote only) | Reuse |
| Power inlet from Board B | 2 x 10 IDC only | 2 x 8 shrouded IDC `DW254P-2X8-L0`, screw terminal `WJ500V-5.08-2P` (remote only) | **Reuse for the synth-side mate** |
| Rail protection (PTC, TVS, Schottky) | `BSMD1206-075-30V`, `SMAJ20A`, `SS26` | `SMD1210P200TF`, `mSMD110-33V`, `BSMD1206-150-16V`, `SMAJ15A`, `SS34` | Reuse where ratings fit |
| Local 5 V regulator | — | `L78L05ABUTR` (C42738, SOT-89) | Candidate for a logic domain |
| Jack, PTV09A pot, SRBV rotary, 2MS1/2MS3 toggles, B3F button | — | — | **Not present anywhere** |
| TL074, LM13700, AS3340, LF398, OPA4197, LM393, CD74HC221, TMUX6111, NOISE2 | — | — | **Not present anywhere** |
| SOIC-8, SOIC-14, SOIC-16, TSSOP-14, TSSOP-16, DIP-8 footprints | — | only `DIP-14` | **All must be imported** |

`$HOME/repos/circuits/zudo-case` is a documentation-only repo for metal cases. It has no `symbols/` or `footprints/` directory `[V-file]`.

---

## 6. Evidence: zero bytes are retained; capture needs datasheets and pin maps, release needs full owner bundles

### What the handoff actually delivers

| Artifact | Content `[V-file]` | Evidence value |
| --- | --- | --- |
| `research/osc-playground/sources.json` | 11 queue entries; **all** `original_file_retained: false`, **all** `sha256: null`. Authority: 4 manufacturer-primary, 4 reference-design, 2 distributor-identity, 1 project-choice | None. It is a reading list with locators |
| `research/osc-playground/promotion-queue.json` | 22 items, identical 5-step recipe. 19 are "candidate, do not silently promote"; 3 are "previously selected identity; evidence promotion needed" (`dailywell-2ms1`, `dailywell-2ms3`, `alps-srbv160803`) | A work queue |
| `research/osc-playground/pin-map-intake.json` | 2 pin maps, marked "research transcription" | Draft only |
| `workbench/datasheets/README.md` | States that no vendor PDF or 3D CAD was downloaded | — |
| `acquire_sources.py` | Dry-run by default; `--run` downloads the 10 URL-bearing queue entries into `<id>-<sha16>.pdf` or `.html` plus `receipts-<stamp>.json` with status `DOWNLOADED_NOT_AUDITED` or `SOURCE_UNAVAILABLE`; enforces a `%PDF-` header for `LF398`, `OPA4197`, `PTV09`; 25 MB cap | Queue holds 5 component sources, 1 behaviour reference and 4 framework pages. **33 of the 37 component URLs are outside its queue** (4 overlap) |

### What the runtime contract demands `[V-file: $HOME/repos/myoss/zudo-circuit-doc/packages/create-zudo-circuit-doc/templates/default/circuit/WORKFLOW.md]`

- One owner bundle per exact part under `.claude/skills/component-<suffix>/`, created by `pnpm exec zudo-circuit-doc new-component <suffix>`, with 8 files: `manifest.json`, `sources.json`, `facts.json`, `coverage.json`, `routing.json`, `interactions.json`, `pin-map.json`, `SKILL.md`.
- Six verdicts, spelled exactly: `PASS - primary-source confirmed`, `CONFIRMED - distributor identity only`, `BLOCKER - deterministic spec violation`, `NEEDS BENCH`, `UNSOURCED`, `NOT APPLICABLE`.
- A source without bytes is `SOURCE UNAVAILABLE` with the zero-hash sentinel (64 zeros). A guessed hash is forbidden.
- Every source lock records `physical_pdf_page_index` (0-based) and `printed_page_label`.
- CAD assets need a receipt in `circuit/cad-receipts/<ASSET_ID>.receipt.json` and a fidelity class: `exact-vendor`, `family`, `derived`, `unavailable`.
- `pnpm circuit:check` enforces symbol pins = footprint pads = pin map. It cannot tell whether they match the datasheet.
- Candidates stay out of `inventory.json` until selected. An empty generated catalogue is valid at the candidate stage (`<HANDOFF>/UPSTREAM-INTEGRATION.md`).

### Prerequisite split

| Stage | Needed per part | Not needed yet |
| --- | --- | --- |
| Doc site stand-up (goal 1) | Authored research pages only | Any bundle, inventory line or generated page |
| Schematic capture (goal 2) | Exact MPN + package; retained manufacturer datasheet with real SHA-256; symbol in the project library; draft `pin-map.json`. The handoff itself requires "every declared part obtains a complete MPN or explicit unresolved state" and "all used symbol pins mapped to exact footprint pad IDs" (`kicad-sheet-plan.json`) | facts, coverage, routing, interactions, selection, generated pages |
| PCB layout (goal 3) | Footprint audited against the mechanical drawing; CAD receipt + fidelity class; resolved stack heights and connector engagement | Publication selection |
| Release / publication | All 8 bundle files with no placeholders; inventory lines, placements, assertion counts; direct-routing cases; `selection.json` with `expect` count locks; `circuit:check`, `circuit:generate`, `check`, `build`, `check:site` all run | — |

---

## 7. GAP list: 18 part families the blocks need have no candidate at all

Confirmed by grep across every `.mdx`, `.md` and `.json` in the payload `[V-file]`: zero hits for trimmer, voltage-reference part numbers, regulator part numbers, clamp/TVS/Schottky diodes, transistor part numbers, tempco, LED driver ICs, or any standoff/spacer part.

| # | Missing family | Why the blocks need it | Sibling asset that can seed it |
| --- | --- | --- | --- |
| G1 | General 1 % resistors, all values | Every block | UNI-ROYAL `0603WAF…` symbols + `R0603` |
| G2 | 0.1 % thin-film resistors | V/oct summing, octave ladder, MULT and AO gain | zudo-pd remote `RT0603BRD07…` |
| G3 | Decoupling and bulk capacitors | About 2 per IC plus per-board bulk | `CC0603KRX7R9BB104`, `CL10A105KB8NNNC`, `CL31A106KBHNNNE` |
| G4 | Timing and integrator capacitors (C0G or film) | AS3340 timing capacitor x 5, AR integrators x 6, VCF integrators | none |
| G5 | Trimmers | V/oct scale, initial frequency, HF tracking, sine shape, LF398 offset, VCA/VCF feedthrough. Factory-only calibration makes access a layout constraint | none (stock footprints exist: `Potentiometer_Bourns_3296W_Vertical` `[V-gitlab]`) |
| G6 | Voltage reference | `11_octave_reference` sheet, AO manual offset, clip thresholds | none (stock symbols exist: `REF5010`, `REF5050` family, `LM4040` `[V-gitlab]`) |
| G7 | Synth-side regulators and rail filters | 5 V logic domain for CD74HC221, LM393 pull-ups and NOISE2; AS3340 negative-supply arrangement; per-board RC/ferrite filtering | `L78L05ABUTR` |
| G8 | Input/output protection | Open issue G08: every input and output | `PESD24VS1UB`, PTC fuses |
| G9 | Small-signal diodes and transistors, matched pairs | Expo converters, folder stages, AR steering, LED drivers | `AO3401A` only |
| G10 | Logic and analog switches for AR and sync | ASR/AR/LOOP state, EOC/STG pulses, soft/hard sync | `SN74HC14N` (DIP-14, unsuitable) |
| G11 | Indicator detector/driver topology | 92 + 12 + 10 LEDs, each "buffered" by contract | none |
| G12 | LED optics | Light pipe or diffuser for a 0603 emitter about 10 mm behind a Ø1.32 aperture | none |
| G13 | Board-to-board connectors with pin budget and mates | Open issue G09; only one unassigned 1 x 10 pair exists | XFCN 6-pin bundle |
| G14 | Power inlet mate and harness | Board B outputs on `WJ500V-5.08-2P` screw terminals and `DW254P-2X8-L0` IDC headers | zudo-pd remote symbols and footprints |
| G15 | Standoffs, spacers, screws, supports | Bushingless pots are not panel-clamped; board contracts require supports | `MountingHole_M3` |
| G16 | Panel hardware without MPN | 98 black + 82 red dress nuts, 30 toggle nuts, 5 OCT caps, 8 button caps or plungers | none |
| G17 | Test points | SLEW test plan names six probe nets | `TestPad_D1.5mm` |
| G18 | NOISE2 support | DIP-8 socket or soldered; programmed-part supply chain to the assembler | none |

---

## 8. Interconnect: one unassigned 1 x 10 pair, a nominal 11.0 mm stack, and preview gaps from 9.4 to 17.9 mm

### Candidates

| Candidate | Facts | Status |
| --- | --- | --- |
| XFCN PZ254V-11-10P, C492409 | 1 x 10, 2.54 mm, THT; importer footprint drill 1.10 mm `[V-e2k]` | r17: not assigned; "this 10-pin example is not sufficient for the whole jack board" |
| XFCN PM254V-11-10-H85, C46595975 | 1 x 10, 2.54 mm, 8.5 mm insulator `[V-file]` | r17: not assigned; "8.5 mm is not the assembled PCB separation" |
| Samtec TSW / SSW | family only, no suffix | documented alternative |
| Factory-terminated harness | no part named | option only |

### What is actually known about stack height

- Sibling evidence, primary-source PASS, for the 6-pin members of the same family (`$HOME/repos/circuits/zudo-led-lamp/.claude/skills/component-xfcn-board-headers/`) `[V-file]`: male 6 mm mating pin, 2.5 mm insulator, 3 mm tail; female 8.5 mm body, 3.2 mm tail, 0.64 x 0.40 mm pin; 3 A and 250 V per contact; unkeyed, not latching.
- zudo-pd remote `boards/README.md` `[V-remote]`: Board P's front plane sits nominally at Z = +11.1 mm from Board B's front plane with that pair. `mechanical-check.json` records `physical_stack_and_cable_fit: "NOT MEASURED"`.
- Nominal mated spacing is therefore 2.5 + 8.5 = **11.0 mm**, unmeasured.

### The preview planes were not derived from any connector

`workbench/mechanical/board-planes.json` gives each board's top surface below the panel rear plane; boards are 1.6 mm thick `[V-file]`. Core top surface is at −24.

| Board | Top surface z | Bottom surface z | Gap to core top |
| --- | --- | --- | --- |
| ET, UT (buttons) | −4.5 | −6.1 | **17.9 mm** |
| J (jacks) | −10.0 | −11.6 | **12.4 mm** |
| O (octave) | −10.6 | −12.2 | **11.8 mm** |
| OS, ES, US (toggles) | −11.5 | −13.1 | **10.9 mm** |
| OP, MP, EP, UP (pots) | −13.0 | −14.6 | **9.4 mm** |
| K (core) | −24.0 | −25.6 | — |
| P/B pocket | −32.0 | — | 110 x 85 mm envelope, matching Board B's real 110 x 85 mm outline `[V-remote]` |

No gap equals 11.0 mm. One header/socket pair cannot serve all five interface planes. The handoff says so itself: all depths are "proposals" (`board-contracts.json`).

### Pin budget is undefined and potentially very large

If all active circuitry stays on the core, the crossing count approaches 180 jack signals + up to 303 pot terminals + 114 LED drives + switch lines. The handoff rule "only buffered/control signals cross board connections" plus local SLEW circuitry points the other way: put active circuits on the interface boards. No document fixes the partition. `board-contracts.json` lists 10 interface fields to complete per board pair; none is filled.

---

## 9. BOM scale (explorer estimate): 66–89 quad op-amps, which puts the −12 V rail at risk

This section is this explorer's arithmetic, not handoff data. The handoff forbids deriving a BOM from the preview rectangles; this estimate exists only to size the plan.

| Block | Count | Op-amp channels each | Quads |
| --- | --- | --- | --- |
| OSC | 5 | about 8 (4 output buffers, shaper, reference, PWM sum) | 10 |
| VCF | 3 | about 8 | 6 |
| MIX5 | 2 | about 7 (5 attenuverters, sum, level) | 4 |
| MIX4 | 2 | about 8 | 4 |
| FOLD | 2 | about 8 | 4 |
| AR | 6 | about 4, plus 1 dual comparator | 6 |
| AO | 6 | about 3 | 5 |
| A/B | 2 | 3 (handoff: two input buffers + one output buffer) | 2 |
| NOISE | 1 | about 6 | 2 |
| Signal path subtotal | | | **43** |
| Magnitude indicators | 92 | 1 to 2 per LED | **23–46** |
| Total TL074-class | | | **66–89** |

Separately: 3 x OPA4197, 2 x LF398, 7–8 x LM13700, up to 17 x LM393 (1 S&H + 6 AR + 10 clip window detectors).

Rail check: TL074 supply current is about 1.4 mA typical and 2.5 mA maximum per amplifier (UNVERIFIED, from memory). 66–89 quads draw roughly 370–500 mA typical and 660–890 mA maximum per rail. zudo-pd is specified for +12 V / 1.2 A, −12 V / 0.8 A, +5 V / 0.5 A `[V-file: $HOME/repos/circuits/zudo-pd/CLAUDE.md]`. The worst case alone reaches the whole −12 V budget before LM13700, AS3340 and 114 LEDs are added.

Assembly scale: 324 panel THT parts (180 + 101 + 30 + 5 + 8) plus headers, and roughly 1,500–2,500 passives.

---

## 10. What the plan must do

1. Pull `$HOME/repos/circuits/zudo-pd` and `$HOME/repos/myoss/zudo-circuit-doc` before anyone copies a symbol or footprint from them.
2. Create the project library pair `symbols/zudo-osc-hole-field.kicad_sym` and `footprints/kicad/zudo-osc-hole-field.pretty/` (+ `.3dshapes/`), following the sibling dual-location rule. Replace the handoff library name `zudo_osc_playground` (`kicad-sheet-plan.json`).
3. Run a dedicated "panel hardware footprint" work item FIRST, for seven parts: jack, PTV09A, SRBV160803, 2MS1, 2MS3, B3F-1020, 0603 LED optics. For each: download the manufacturer drawing, hash it, audit the imported footprint, record a CAD receipt.
4. Resolve conflicts 4.1 and 4.2 before any board outline is drawn. Both interact with the fixed grid.
5. Seed the library from siblings: both LEDs, passives, `C0805`/`C1206`, test pads, mounting holes, fiducials, the 2 x 8 power header, the screw terminal.
6. Re-run the documented importer for the 15 resolvable ids into `.circuit-cache/cad/<part>` at about 12 s spacing. This session's imports live only in `<SCRATCH>` and are throwaway.
7. Decide the symbol style for multi-channel ICs before sheet work starts.
8. Extend source acquisition to all 37 component URLs; `acquire_sources.py` covers only 4 of them.
9. Add a "missing families" selection item for G1–G18, sequenced per block, with trimmers, reference and protection chosen while the first oscillator is captured.
10. Add a power-budget checkpoint after the first block of each family is captured.
11. Treat evidence in two tiers: capture-grade now, release-grade bundles later.

---

## 11. Risks and blockers

| # | Risk | Severity | Basis |
| --- | --- | --- | --- |
| R1 | OCT lug collision at 17 mm pitch may be incompatible with "positions are fixed" | **Blocker for the O board** until the ALPS drawing is read | 4.1 |
| R2 | Jack courtyard overlap on 180 parts; footprint origin is not the barrel centre | High | 4.2 |
| R3 | No mechanical drawing of any kind is in the handoff | High | section 4 table |
| R4 | WQP518MA identity: its JLC id does not resolve, and its equivalence to the stock PJ398SM footprint is unproven | High (180 parts) | table B |
| R5 | −12 V rail may be undersized for a TL074-based design with buffered indicators | High | section 9 |
| R6 | Four parts have no LCSC/JLC route (2MS3, AS3340D, NOISE2, TMUX6111) and the jack is a sourcing record; the owner requires factory-only soldering | High | table A |
| R7 | Interconnect has no pin budget, no selected mate and no matching stack height | High | section 8 |
| R8 | Family footprints and 3D models silently represent other variants | Medium | 4.5 |
| R9 | 18 part families are unselected; the BOM is dominated by parts the handoff never names | Medium | section 7 |
| R10 | Local sibling checkouts are stale, so copied assets may be outdated | Medium | section 5 |
| R11 | B504 showed zero stock with a minimum of 10; OPA4197 was pre-order | Medium | table A |
| R12 | KiCad is not installed in this WSL; no ERC/DRC or footprint render can run here. Footprint previews need Docker | Medium | `kicad-cli` not found |
| R13 | A hand-rolled request to the EasyEDA API returns HTTP 403; only the `easyeda2kicad` tool itself works | Low | this session |

---

## 12. Open decisions, with a recommended default for each

| # | Decision | Recommended default |
| --- | --- | --- |
| D1 | Stock KiCad libraries or project-local library | Project-local library, as both siblings do. Copy stock symbols into it where they are better |
| D2 | Symbol style for quad/dual ICs | Stock multi-unit symbols (`TL074`, `LM13700`, `OPA4197xPW`, `LM393`, `LF398_SOIC14`, `AS3340`) copied into the project library with MPN and LCSC fields; importer footprints |
| D3 | Jack footprint | Project copy of the stock PJ398SM footprint, re-anchored at the barrel centre (offset 6.48 mm), courtyard regenerated by the sibling `gen_courtyards.py` rule, accepted only after the WQP518MA drawing matches |
| D4 | OCT lugs | Read the ALPS drawing first. If lugs are required, use one shared slot between neighbours; if optional, omit lug holes and add a board support next to the row. Do not move the grid |
| D5 | Pot footprint source | Importer footprint for C5848782, corrected to the Bourns drawing; reuse for B504. Replace the 15 mm-shaft 3D model with a 20 mm one and classify it `derived` |
| D6 | B3F hole pattern | Omron drawing decides; default to the 6.5 x 4.5 mm stock pattern if the drawing is unavailable at capture time, marked `UNSOURCED` |
| D7 | 2MS3 footprint | Reuse the 2MS1 footprint with a separate `SW_SPDT_MSM`-style symbol, after comparing the Thonk DW2 PDF |
| D8 | Op-amp for general duty | Keep TL074CDT for capture; re-decide after the first power budget. Use transistor or comparator LED drivers instead of one op-amp per LED |
| D9 | Interconnect family | XFCN PZ254V / PM254V (evidence bundle already exists in the lamp). Choose the socket height per interface plane; move the core plane rather than the control planes |
| D10 | Circuit partition | Active circuitry on the interface boards near its controls; the core carries power distribution and the circuits that have no panel control. This minimises crossings |
| D11 | Power inlet | 2 x 8 shrouded IDC `DW254P-2X8-L0` on the core with a factory-made ribbon, matching Board B J10/J11 |
| D12 | Evidence depth before capture | Capture-grade only: retained datasheet + hash + pin map. Full bundles after a part survives its first block capture |
| D13 | NOISE2 mounting | DIP-8 socket, so the programmed part can be inserted at final assembly without soldering |
| D14 | Passive strategy | One `component-project-passives`-style bundle, as the lamp does, limited to JLC basic parts where possible |

---

## Appendix — how the checks were run

- Register, grid, counts, planes, preview envelopes: `python3` parsing of the handoff JSON and `src/*.js`.
- Sibling inventories: s-expression walk of both `.kicad_sym` files; `find` over `footprints/`.
- Importer: `easyeda2kicad --lcsc_id <id> --symbol --footprint --3d --output <SCRATCH>/e2k/<id>/lib`, 12 s apart, 18 ids; three failures retried once.
- Stock library names and three stock footprints: GitLab API tree listing and raw download of `kicad/libraries/kicad-symbols` and `kicad-footprints`, branch `master`.
- Remote state: `gh api repos/Takazudo/<repo>/commits/main`, tree listing and four raw files of zudo-pd at `f25194f`.
- Not done: no KiCad run, no PDF download of any manufacturer datasheet, no live stock check at JLCPCB or LCSC, no local JLCPCB parts database found.
