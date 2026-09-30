# 08 — Sibling zudo-pd: the reused power assembly and its KiCad conventions

Explorer 08 of 9. Exploration only; nothing in `$HOME/repos/circuits/zudo-pd` or the handoff was modified.
All numbers below were parsed from files (python3 s-expression parser, JSON, git), not inferred from names.
Items that could not be verified are marked **UNVERIFIED**.

Evidence base:

- Local checkout: `$HOME/repos/circuits/zudo-pd` at `797a221` (2026-08-16).
- Remote `origin/main`: `f25194fa73ded724e82d4561307c106480fbd9ce` (2026-09-22), read from a throwaway
  partial clone in the explorer scratch dir. Paths below are repo-relative and refer to **origin/main**
  unless marked "local".

---

## The local checkout is 13 commits stale and does not contain the P/B the handoff means

- Local `HEAD` and local `origin/main` ref are both `797a221`; GitHub `main` is `f25194f`. `git rev-list --count 797a221..f25194f` = **13**; diffstat 728 files, +4,060,298 / −265,079.
- At `797a221` there is **no `boards/board-p/`, no `manufacturing/`, no `scripts/pcb/`, no Board B PCB, and zero occurrences of `SMAJ16A`**. Local `CLAUDE.md` still says "PCB layout ... not started yet — schematics only".
- Everything the handoff references (Board P, SMAJ16A, 15 V-only, 110 × 85 mm Board B, 11.1 mm stack) exists only in those 13 commits:

| Commit | Date (JST) | Subject |
| --- | --- | --- |
| `609c1bb` | 2026-09-21 | feat(pcb): renew split power boards and component contracts |
| `8157428` | 2026-09-21 | build(manufacturing): retain validated prototype order packages |
| `17d0fd9` | 2026-09-21 | feat(mechanical): add adhesive PCB legs with straight M3 grip posts |
| `9fb7333` | 2026-09-21 | docs: rebuild the component-first design and fabrication guide |
| `356f974` | 2026-09-21 | chore(storage): remove LFS and keep large assembly previews local |
| `209f287` | 2026-09-21 | chore: retain only the latest PCB and accessory outputs |
| `ec656b7` | 2026-09-21 | build: refresh the current prototype package after cleanup |
| `ef08fe5` | 2026-09-21 | feat(board-b): add back silkscreen artwork and tooling |
| `6407791` | 2026-09-21 | fix(board-p): replace out-of-stock D5 TVS with Littelfuse SMAJ16A (C74561) |
| `aeeff56` | 2026-09-21 | build: regenerate assembly preview, leg fit evidence and prototype package for D5 change |
| `cc159ed` | 2026-09-21 | fix(hooks): run the pre-push doc check from doc/ so its pinned pnpm is used |
| `f385f20` | 2026-09-22 | fix(board-b): replace out-of-stock LDOs, add U8 ADJ divider, correct LED2 polarity |
| `f25194f` | 2026-09-22 | build: regenerate assembly evidence and JLCPCB package for the ordered revision |

Consequence: any agent that reads the local checkout gets the wrong board set (A + B, JST XH cable, L78xx LDOs, Fastons). The plan must pull zudo-pd before anyone designs against it.

---

## "P/B" means Board P (USB-PD input) stacked on Board B (synth conversion)

| Board | Path | Role | State |
| --- | --- | --- | --- |
| **Board P** | `boards/board-p/` | Reusable USB-PD sink: USB-C J1, STUSB4500QTR U1, AO3401A load switch Q1, SMAJ16A D5, 6-pin header JOUT1, NVM/debug pogo pads J2/J3 | Schematic generated + routed PCB |
| **Board B** | `boards/board-b/` | 15 V → +12 / −12 / +5 V: AP63201 + 2× LM2596S-ADJ pre-regulators, 2× LT1963A + LT3015 LDOs, PTC + TVS, outputs | Schematic generated + routed PCB |
| Board A | `boards/board-a/` | Previous USB-PD input design (JST B6B-XH-A cable) | Schematic only, historical reference |
| Root combined board | `zudo-pd.kicad_pro/.kicad_sch/.kicad_pcb` + 4 sheet files | As-built v0.4.0 single board, 82 × 99 mm, 94 footprints | Historical; ordered 4×; all failed PD negotiation |

Board P lineage: `boards/board-p/mechanical.json` `adapted_from.schematic_sha256 = ed2c4836…a2600` equals the sha256 of
`$HOME/repos/circuits/zudo-led-lamp/boards/board-p/board-p.kicad_sch`. zudo-pd's Board P is the led-lamp Board P with D5 swapped.
**There are therefore two Board P variants**: led-lamp's (D5 = SMAJ20A C571370) and zudo-pd's (D5 = SMAJ16A C74561).

---

## Output rails are design targets, not measured ratings

| Rail | Target | Chain | PTC (hold / trip @25 °C) | Output TVS | Conditional output band |
| --- | --- | --- | --- | --- | --- |
| +12 V | 1.2 A | U2 AP63201WU-7 → +13.44 V → U6 LT1963AEQ#TRPBF (adj) | PTC1 SMD1210P150TF/16 C7529589: 1.5 A / 3.0 A, 16 V | TVS1 SMAJ15A | 11.526 – 12.477 V |
| −12 V | 0.8 A | U4 LM2596S-ADJ inverting → −14.145 V → U8 LT3015EQ#PBF (adj, R26/R27/R28) | PTC3 BSMD1206-150-16V C883133: 1.5 A / 3.0 A, 16 V | TVS3 SMAJ15A | 11.741 – 12.370 V magnitude (nominal −12.054 V) |
| +5 V | 0.5 A | U3 LM2596S-ADJ → +6.519 V → U7 LT1963AEQ#TRPBF (adj) | PTC2 mSMD110-33V C70119: 1.1 A / 2.2 A, 33 V | TVS2 SMAJ6.5A | 4.815 – 5.196 V |

- Total 26.5 W. Input contract USB-PD 15 V / 3 A (45 W), permitted source range 15 V ±5 % = 14.25 – 15.75 V.
- Ripple: "< 1 mV peak-to-peak **target** — Unmeasured" (`doc/src/content/docs/getting-started/project-brief.md`).
- Every rail figure is flagged "targets, not measured capabilities" in `readme.md`, `CLAUDE.md`, `manufacturing/README.md`.
- PTC hot derating: PTC3 hold drops to 0.77 A at 85 °C (datasheet). PTC1 has no retained 85 °C row; the repo's own estimate is ~0.74 A, crossing the 1.2 A budget near ~48 °C ambient (UNSOURCED estimate in `component-ptc-smd1210p200tf-c20808/facts.json`).
- LDO dissipation screens at full target load: 4.23 W (+12), 1.95 W (+5), 3.54 W (−12) — `manufacturing/power-budget.json`.
- Rail indicator LEDs on Board B: LED2 green (+12), LED3 blue (+5), LED4 red (−12), each via 1 kΩ.
- Sources: `scripts/schgen/board_b_spec.py`, `manufacturing/power-budget.json`, `manufacturing/power-budget.md`.

---

## Board B exposes the rails on two connector types with a verified pin map

Parsed from `boards/board-b/board-b.kicad_pcb` pad nets (not from docs):

### J10 / J11 — 16-pin shrouded right-angle IDC header

- MPN **DEALON DW254P-2X8-L0**, LCSC **C4749189**, footprint `zudo-pd:IDC-TH_16P-P2.54_321016RG0ABK00A01`, through-hole, wave-solder route (not SMT).
- J10 at (41.4, 72.77), J11 at (81.5, 72.77), both F.Cu, 0°.
- Per-contact 3 A (UNSOURCED mirror drawing).

| Pins | Net |
| --- | --- |
| 1–2 | `-12V rail` (red stripe end) |
| 3–8 | `GND` |
| 9–10 | `+12V rail` |
| 11–12 | `+5V rail` |
| 13–14 | `CV rail` |
| 15–16 | `GATE rail` |

`CV rail` and `GATE rail` connect only J10 ↔ J11 (4 pins each); nothing on Board B drives them.

### J6 / J7 — 2-pole screw terminals

- MPN **Kangnex WJ500V-5.08-2P**, LCSC **C8465**, 5.08 mm pitch, footprint `zudo-pd:WJ500V-5.08-2P_C8465`, F.Cu, rotated 90°, wire entry facing the x = 0 edge.
- J6 at (7, 48): pin 1 = `GND` (7, 50.54), pin 2 = `-12V rail` (7, 45.46).
- J7 at (7, 61): pin 1 = `+5V rail` (7, 63.54), pin 2 = `+12V rail` (7, 58.46).
- Wire 14–30 AWG, strip 6–7 mm, M2.5 screw 0.4 N·m (all UNSOURCED mirror table).
- **Only one GND terminal exists for three rails.**

Both connector families share the same board-level budget; they are not additional capacity.

### Status signals are not on the output connectors

`ATT` and `PDOK` (open-drain, active-low, no on-board pull-up on either board) reach only Board B edge pogo pads P1.1 / P1.2.
The synth gets no power-good signal unless it is wired from those pads.

Seven top-edge contacts, 2.54 mm pitch, y = 1.8 mm: P1.1 ATT 56.19, P1.2 PDOK 58.73, P1.3 GND 61.27, P1.4 NC 63.81, TP3 +13.44 V PRE 66.35, TP4 +6.519 V PRE 68.89, TP5 −14.145 V PRE 71.43.

---

## Outlines and holes parsed from the PCBs match the mechanical records

| Item | Board P | Board B |
| --- | --- | --- |
| Edge.Cuts | 1 `gr_rect`, (0,0)–(27,40) | 4 `gr_line`, (0,0)–(110,85) |
| Size | **27 × 40 mm** | **110 × 85 mm** |
| Thickness / layers | 1.6 mm, 2 layers | 1.6 mm, 2 layers |
| Copper | 0.035 mm (1 oz) | 0.07 mm (2 oz) |
| Footprints | 28 (19 fitted) | 89 (75 fitted) |
| Fiducials | — | FID1 (9.5, 6), FID2 (107, 27), FID3 (18, 80) |

Mounting holes (coordinates relative to outline minimum, KiCad Y-down):

| Board | Ref | X | Y | Drill | Footprint |
| --- | --- | --- | --- | --- | --- |
| P | MH1 | 4.0 | 4.0 | Ø3.2 NPTH | `MountingHole:MountingHole_3.2mm_M3` |
| P | MH2 | 23.0 | 4.0 | Ø3.2 NPTH | same |
| P | MH3 | 12.8 | 32.6 | Ø3.2 NPTH | same |
| B | H1 | 3.5 | 16.0 | Ø3.2 NPTH | `zudo-pd:MountingHole_M3` (mates P MH1) |
| B | H2 | 3.5 | 35.0 | Ø3.2 NPTH | same (mates P MH2) |
| B | H3 | 32.1 | 24.8 | Ø3.2 NPTH | same (mates P MH3) |
| B | H4 | 106 | 4 | Ø3.0 NPTH | `zudo-pd:MountingHole_HC11_3mm` |
| B | H5 | 4 | 81 | Ø3.0 NPTH | same |
| B | H6 | 106 | 81 | Ø3.0 NPTH | same |
| B | H7 | 4 | 4 | Ø3.0 NPTH | same |

P → B coordinate transform: `pd_to_board_b(x, y) = (y − 0.5, x + 12)`, owned by `scripts/pcb/board_b_layout.py`.
P projects onto B at x = −0.5 … 39.5, y = 12 … 39, i.e. **P overhangs B's left edge by 0.5 mm**.

P ↔ B interface (both parsed and cross-checked by `boards/board-b/assembly-preview/mechanical-check.json`, `pd_mating_xy: PASS`):

| Pin | P JOUT1 (PZ254V-11-06P, C492405, male) | B J5 (PM254V-11-06-H85, C2832269, female, 8.5 mm body) | Net |
| --- | --- | --- | --- |
| 1 | (6.55, 37.7) | (37.2, 18.55) | VBUS_OUT / `+15V INPUT` |
| 2 | (9.09, 37.7) | (37.2, 21.09) | VBUS_OUT / `+15V INPUT` |
| 3 | (11.63, 37.7) | (37.2, 23.63) | ATT |
| 4 | (14.17, 37.7) | (37.2, 26.17) | PDOK |
| 5 | (16.71, 37.7) | (37.2, 28.71) | GND |
| 6 | (19.25, 37.7) | (37.2, 31.25) | GND |

The header pair is **unkeyed**.

---

## The installed assembly needs about 116 × 91 × 25 mm plus cable exits on two edges

Documented (repo):

- Board B installs **front/component face DOWN** on four printed adhesive legs, seat height **18 mm** (`3dp-files/adhesive-leg/spec.json`).
- Leg base 14 × 14 × 2 mm, pole Ø7 mm; bases extend 3 mm past the board → adhesive footprint **116 × 91 mm**.
- Board P hangs below B, component face toward B, nominal plane separation **11.1 mm**; P back substrate plane 12.7 mm from B's front.
- Tallest B part: J6/J7 terminal body 14.0 mm nominal / 14.2 mm drawing max; electrolytics 10.3 mm.
- Terminal solder-tail maximum 4.7 mm; J5 tail 3.2 mm; J10/J11 tail 3.0 mm.
- M3 × 5 mm screws through Ø3.0 mm corner holes (zero nominal clearance; fit unmeasured).
- HC-11 11 mm standoffs do **not** clear the stack.

Derived by this explorer (arithmetic on the above; **UNVERIFIED physically**):

| Plane | Height above leg adhesive face |
| --- | --- |
| Terminal block lowest point | 18 − 14.2 = 3.8 mm |
| P back substrate | 18 − 12.7 = 5.3 mm |
| P JOUT1 solder tails (3.0 mm) | ≈ 2.3 mm |
| P component plane (USB-C sits here, body 3.16 mm toward B) | 6.9 mm → USB-C centre ≈ 8.5 mm |
| B component plane | 18.0 mm |
| B back plane | 19.6 mm |
| Top of tallest solder tail | 19.6 + 4.7 = **24.3 mm** |
| + M3 screw heads, adhesive tape | not specified in repo |

Access requirements:

- USB-C opening is at B's **left edge** (B x = −0.5), centre at B y ≈ 25.5 (P (13.506, 5) through the transform).
- Screw-terminal wire entries also face the left edge.
- J10/J11 mate toward the **bottom edge** (body spans y ≈ 76 … 85).

The handoff's 3D preview (`workbench/src/three.js` line 59) reserves `boardRect('P/B · power pocket reservation', 25, 31, 110, 85, -32, 12)` plus a 27 × 40 × 1.6 board at 11.1 — it uses the correct current board sizes but is labelled "ENVELOPE ONLY"; it does not model legs, the 116 × 91 footprint, the ≈ 25 mm height, or the two cable-exit edges.

---

## Factory-default STUSB4500 requests 20 V, and the SMAJ16A cannot survive that

Mechanism, from zudo-pd sources:

1. **Factory NVM** (`doc/src/content/docs/inbox/nvm-programming.md`): PDO1 5 V / 1.5 A, PDO2 15 V / 1.5 A, PDO3 **20 V / 1 A at highest priority**; `POWER_ONLY_ABOVE_5V` disabled.
2. **Required image** ("programmed 15 V-only state"): `SNK_PDO_NUMB = 2` (PDO3 never advertised), PDO2 = 15 V / 3 A, `POWER_ONLY_ABOVE_5V = 1` (VBUS_EN_SNK asserts only after the 15 V contract).
3. **D5 changed** in commit `6407791` from SMAJ20A (out of stock) to **Littelfuse SMAJ16A, C74561**: standoff 16 V, breakdown 17.8 – 19.7 V @ 1 mA, clamp 26 V max @ 15.4 A, 10/1000 µs, 25 °C.
4. D5 sits on `VBUS_IN` (J1.2/J1.5 side), **upstream of Q1**. A 20 V contract exceeds the 19.7 V maximum breakdown → sustained TVS conduction. Turning the load switch off does not protect it.
5. Margin at normal high line: 16.0 − 15.75 = **0.25 V**.

Mandatory procedure (`doc/src/content/docs/architecture/board-p.md`, `how-to/renewal-bring-up.md`):

1. First power from a **current-limited 5 V-only source**, Board B disconnected.
2. Resolve the open VREG_2V7 pull-up loading / jig-voltage question first (R15/R16 4.7 kΩ to VREG_2V7).
3. Program via J2 pogo pads: J2.1 SCL, J2.2 SDA, J2.3 GND, J2.4 RESET. Tooling documented: NUCLEO-F072RB + STSW-STUSB002 (UART firmware variant) or SparkFun STUSB4500 Arduino library; 4P 2.54 mm pogo clip.
4. Retain: received image, 40-byte programmed image, byte-for-byte readback, reset reload, full power-cycle readback.
5. Only then connect a 15 V / 20 V-capable PD source.

**No NVM image, readback or bench result is retained anywhere in the repo** (`git ls-files | grep -i nvm` returns only two doc pages; `fact-stusb-artifact` verdict = NEEDS BENCH).

Conditioned stress margins at the 26 V clamp point (`manufacturing/power-budget.json`): STUSB4500 28 V abs max +2.0 V; Q1 30 V VDS +4.0 V; U4 45 V abs max +4.19 V; D3 60 V +19.19 V; U4 40 V **operating** limit −0.81 V (exceeded).

Note for the synth: programming is a factory/bench task on Board P; the synth project itself carries no PD circuitry. The handoff's "no home soldering" rule is compatible because J2 is pogo-contact, not soldered.

---

## No evidence exists that any P/B hardware has been built

| Signal | Value |
| --- | --- |
| `VERSION` | `0.4.0` (X = product release, **Y = lifetime JLCPCB order count**, Z = checkpoint) |
| Git tags | `v1.0` only |
| `jlcpcb-order-snapshots/` | `v0_1_0`, `v0_2_0`, `v0_3_0`, `v0_4_0` — all the legacy combined board |
| v0.4.0 snapshot | `used-for-order/` recovered from a gitignored plugin dir; `from-order-detail/` is an empty placeholder; the README itself says there is no local proof the order was placed |
| Renewal package | `manufacturing/releases/corner-support-review/` — "development review files, not a released product or a submitted order" |
| Docs | `readme.md`, `boards/README.md`, `manufacturing/README.md`, `release-readiness.md` all say "No renewal hardware has been released or ordered" |
| Contradiction | HEAD commit subject: "regenerate assembly evidence and JLCPCB package **for the ordered revision**" |

If an order had been placed, the repo's own rule requires `VERSION` → `0.5.0` and `jlcpcb-order-snapshots/v0_5_0-board-p/` + `v0_5_0-board-b/`. Neither exists. Whether an order happened is **UNVERIFIED** and only the owner can answer.

### What a consumer must source-lock

| Item | Value |
| --- | --- |
| zudo-pd commit | `f25194fa73ded724e82d4561307c106480fbd9ce` |
| Package `git_base` (HEAD at export time) | `cc159ed4317a8319c11dccf4c04505ba3b9a4250` |
| KiCad version of export | 10.0.0 |
| `boards/board-p/board-p.kicad_pcb` sha256 | `407f634942a641e8c91dfbd141e7ebe3eed2ac803b2d57c44871c6c44717d278` |
| `boards/board-p/board-p.kicad_sch` sha256 | `a68d98e5154e21c84dae3ca0be03abdd61df49240ff1f9db6a92e9feaba9611c` |
| `boards/board-b/board-b.kicad_pcb` sha256 | `c8f83fcdba4daa06bfcce6b998bc2c3ab0400a0c12d4b13e1ba391a72553fc2f` |
| `boards/board-b/board-b.kicad_sch` sha256 | `f435908edf76ddce37871717ddb3c0e497ead0d07b7aff62220b453dbcde61e3` |
| `scripts/schgen/board_p_spec.py` sha256 | `104f5c6abb8dc4ac555cccbe68981799b19ad3d1bdd6a006072ed60d0266ef94` |
| `scripts/schgen/board_b_spec.py` sha256 | `12814d07a8318bc16ab0259ff6baddfd67af3abe01b8824feb5b0885608cff49` |
| As-built evidence still missing | JLCPCB confirmed BOM, assembly photo, NVM image + readback, bench load/ripple/thermal results |

Manifest check run by this explorer: all 372 (P) and 494 of 495 (B) `source_hashes` in `manifest.json` match HEAD; the one missing file is the intentionally untracked `populated-stack.step` (152.9 MB, local-only by policy).

Package check state: Board P — ERC 0 errors / 29 warnings, DRC 0 errors / 46 warnings / 0 unconnected, 3 parity warnings (the mounting holes). Board B — ERC 0 / 54, DRC 0 / 40 / 0, parity 0.

Minor stale text inside zudo-pd (does not affect the contract): `boards/board-p/README.md` still discusses the SMAJ20A 32.4 V clamp and quotes 50 DRC warnings; the current report has 46.

---

## The power interface contract the synth should be designed against

| Field | Contract | Source |
| --- | --- | --- |
| Rails | +12 V, −12 V, +5 V, GND | `scripts/schgen/board_b_spec.py` NETS |
| Budget (targets) | +12 V 1.2 A, −12 V 0.8 A, +5 V 0.5 A, shared across J6/J7/J10/J11 | `CLAUDE.md`, `manufacturing/power-budget.json` `rated_targets` |
| Voltage band to tolerate | +12: 11.53 – 12.48 V; −12: −11.74 … −12.37 V; +5: 4.81 – 5.20 V (conditional screens) | `power-budget.json` `whole_chain_current_thermal_screen` |
| Ripple | Target < 1 mVp-p, unmeasured | `project-brief.md` |
| Primary connector | 2 × 8, 2.54 mm shrouded IDC, DW254P-2X8-L0 C4749189, Eurorack map, pins 1–2 = −12 V | parsed pads J10/J11 |
| Alternative connector | 2 × WJ500V-5.08-2P C8465 screw terminals (single GND pole) | parsed pads J6/J7 |
| Pins 13–16 | CV / GATE bus pass-through, undriven | NETS `CV rail`, `GATE rail` |
| Power-good | None on the output connectors; ATT/PDOK only on P1 pogo pads | NETS `ATT`, `PDOK` |
| Over-current | PPTC per rail: 1.5 / 1.5 / 1.1 A hold, slow (0.3 – 1.0 s at 8 A) | component skills `component-ptc-*` |
| Over-voltage | SMAJ15A on ±12 V, SMAJ6.5A on +5 V | `board_b_spec.py` |
| Startup | LM2596 inverting stage may demand ≈ 4.5 A for ≥ 2 ms against a 3 A PD contract; source may trip and retry | `power-budget.json` `open_qualification` |
| Sequencing | Three independent converter chains; no tracking or sequencing circuit exists; rail order unmeasured | absence in `board_b_spec.py` |
| Input gating | Q1 load switch closes only after the 15 V contract when `POWER_ONLY_ABOVE_5V = 1` | `board_p_spec.py`, `nvm-programming.md` |
| Thermal | U4 and U8 tabs sit on the −14.145 V rail; never bond to ground or a shared heatsink | `manufacturing/README.md` |

Design rules that follow for the synth side:

- Budget the synth at or below the targets with margin; the −12 V rail (0.8 A) is the tightest.
- Keep rail bulk capacitance on the synth modest and state it; large added capacitance worsens the unqualified start-up case.
- Assume rails can come up in any order and that a PD source may hiccup; protect inputs accordingly.
- Do not connect pins 13–16.
- Do not rely on ATT/PDOK.
- The handoff's `01_power_interfaces` sheet ("Frozen external zudo-pd output contract; connector/fuse/local bypass") maps directly onto this table.

---

## KiCad 10 file formats are used throughout, with a KiCad 8-format symbol library

| File kind | Header version | Generator |
| --- | --- | --- |
| `.kicad_pcb` (root, board-p, board-b, preview) | `20260206` | pcbnew 10.0 |
| `.kicad_sch` (root + 4 sheets, board-a/b/p) | `20260306` | eeschema 10.0 |
| `symbols/zudo-pd.kicad_sym` | `20231120` | kicad_symbol_editor 8.0 |
| `.kicad_pro` | `meta.version` 3 | — |
| `sym-lib-table` / `fp-lib-table` | `version 7` | — |
| `.kicad_mod` | mostly legacy `(module …)`; 4 files carry `version 20240108` | — |

zudo-led-lamp uses the same `20260206` / `20260306` versions, so both siblings are on KiCad 10.

### Library tables are project-local and relative

Root project:

```text
(lib (name "zudo-pd")(type "KiCad")(uri "${KIPRJMOD}/symbols/zudo-pd.kicad_sym") …)
(lib (name "zudo-pd")(type "KiCad")(uri "${KIPRJMOD}/footprints/kicad/zudo-power.pretty") …)
```

Each board two levels down (`boards/<name>/`) has its own tables using `${KIPRJMOD}/../../symbols/…` and `${KIPRJMOD}/../../footprints/kicad/zudo-power.pretty`.
3D models resolve through `${KIPRJMOD}/../../footprints/kicad/zudo-pd.3dshapes/`; no global KiCad path variable is used.

- One library nickname (`zudo-pd`) for both symbols and footprints. The validator rejects any other footprint nickname.
- Note the mismatch: the nickname is `zudo-pd` but the directory is `zudo-power.pretty`.
- **Dual-location rule**: every `.kicad_mod` exists byte-identically in `footprints/kicad/` and `footprints/kicad/zudo-power.pretty/`. Verified: 76 files each, identical name sets, zero content differences.
- 80 files in `zudo-pd.3dshapes/`.

### Symbols are named by exact MPN and carry the LCSC number

- 126 symbols. Property usage: `Reference` 126, `Value` 126, `Footprint` 126, `Datasheet` 103, **`LCSC Part` 120**, `Manufacturer` 34, `MPN` 34, `Description` 27.
- Symbol names are exact MPNs, sometimes suffixed with the LCSC code (`SMAJ15A_C571368`, `AO3401A_C347476`).
- Library symbols use the property name **`LCSC Part`**; generated schematic instances use **`LCSC`**; PCB footprints carry both (`LCSC` authoritative, `LCSC Part` / `LCSC Part #` / `JLCPCB Part #` checked as aliases by the exporter).
- Older symbols still point at `easyeda2kicad:<footprint>`; newer ones at `zudo-pd:<footprint>`. Both resolve because KiCad resolves by directory.
- Two symbols (`Conn_1x04`, `Conn_1x08`) still reference `zudo-led-lamp:PogoPad_…` in the library; the board spec overrides the footprint.

### Reusable for a synth, and what is missing

Reusable:

| Need | Symbol | Footprint | LCSC |
| --- | --- | --- | --- |
| Eurorack power header, shrouded RA | `DW254P-2X8-L0` | `IDC-TH_16P-P2.54_321016RG0ABK00A01` | C4749189 |
| Eurorack power header, older | `2541WR-2X08P` | `HDR-TH_16P-P2.54-H-M-R2-C8-S2.54` | C5383092 |
| 1 × 6 stacking header male / female | `PZ254V-11-06P` / `PM254V-11-06-H85` | `HDR-TH_6P-P2.54-V-M` / `-V-F` | C492405 / C2832269 |
| 1 × 3 header | `Header-Male-2.54_1x3`, `HB-PH3-25413PB2GOP` | `HDR-TH_3P-P2.54-V-M` | C49257, C6332196 |
| Screw terminal | `WJ500V-5.08-2P` | `WJ500V-5.08-2P_C8465` | C8465 |
| 0603 LEDs | `KT-0603R`, `KT-0603B`, `KT-0603YG`, `0603Whitelight_C2290` | `LED0603-RD`, `LED0603-FD_BLUE`, `LED0603-R-RD_WHITE` | C2286, C2288, C2289, C2290 |
| 0805 LED | `FC-2012HRK-620D` | `LED0805-R-RD` | C84256 |
| Passives | R0603 / R0805 lines incl. 0.1 % RT0603 series; C0603 / C0805 / C1206 / C1210; SMD electrolytics; 25SVPF47M polymer | `R0603`, `R0805`, `C0603`, `C0805`, `C1206`, `C1210`, `CAP-SMD_BD*` | various |
| Test / pogo pads | `TestPoint`, `PogoPad_1x04`, `PogoPad_1x08` | `TestPad_D1.5mm`, `PogoPad_1x04_P2.54mm`, `PogoPad_1x08_P2.54mm`, `PogoEdge_1x01_1.5x2.5mm`, `PogoEdge_BoardB_1x04_P2.54mm` | none (bare copper) |
| Mechanical | — | `MountingHole_M3` (Ø3.2), `MountingHole_HC11_3mm` (Ø3.0), `Fiducial_1mm_Mask2mm` | none |
| Protection | `SMAJ15A_C571368`, `SMAJ6.5A_C87267`, PTC lines | `D-FLAT_L4.3-W2.6-LS5.3-RD`, `F1206`, `F1210`, `F1812` | various |
| ERC | `PWR_FLAG` | — | — |
| Logic | `SN74HC14N` | `DIP-14_L19.2-W6.6-P2.54-LS10.9-BL` | C2907 |

**Missing entirely**: 3.5 mm jacks, potentiometers (PTV09 or any), rotary switches (SRBV160803), toggle switches, tactile/push buttons, op-amps, OTAs, LF398, transistor arrays, precision references, trimmers, board-to-board signal connectors beyond the 1 × 6. zudo-pd contributes conventions and generic parts, not the synth's panel hardware.

---

## Schematics are generated from Python specs, flat, with no wires

- Source of truth: `scripts/schgen/board_{p,a,b}_spec.py`, each defining `PROJECT_NAME`, `OUT`, `PAPER`, `COMPONENTS`, `NETS`, `NO_CONNECT`, optional `ERC_POWER_FLAGS`, `LABEL_OVERRIDES`.
- `COMPONENTS[ref] = (lib_symbol, value, lcsc, footprint, dnp, (x, y))`.
- `NETS[name] = ['Ref.Pin', …]`.
- `schgen_core.py` (329 lines) embeds the used `lib_symbols`, places instances, and puts a **global label on every pin endpoint**. Parsed Board P output: 25 symbols, 89 global labels, 5 no-connects, **0 wires**, one root sheet (`sheet_instances path "/" page 1`).
- **No hierarchical sheet support** — the generator never emits a `sheet` node. Board B (76 components) is a single A1 sheet.
- Toolchain is pure Python with its own `sexp.py`; KiCad is not needed to generate. It was ported from zudo-led-lamp.

Commands:

```sh
python3 scripts/schgen/gen_schematic.py board_b_spec
python3 scripts/schgen/verify_geometry.py scripts/schgen/board_b_spec.py boards/board-b/board-b.kicad_sch
python3 scripts/schgen/check_baseline.py scripts/schgen/board_b_spec.py scripts/schgen/baselines/board-b.json --allow scripts/schgen/baselines/board-b-allow.json
python3 scripts/schgen/check_decisions.py
bash scripts/schgen/run_smoke_test.sh
scripts/schgen/verify.sh board-b        # needs kicad-cli; prints SKIPPED and exits 0 without it
```

---

## PCBs are scripted through pcbnew Python plus an external Specctra router

`scripts/pcb/` (24 scripts, 5,551 lines):

| Step | Script | Needs |
| --- | --- | --- |
| Placement table | `board_b_layout.py` (`WIDTH`, `HEIGHT`, `PLACEMENTS`, `MOUNTING_HOLES`, `FIDUCIALS`, `NEGATIVE_ZONES`, `GROUND_STITCHES`) | — |
| Generate unrouted placement | `place-board-b.py` — builds a `pcbnew.BOARD()`, loads footprints from `zudo-power.pretty`, assigns nets from the spec, sets aux origin to (0, HEIGHT) | KiCad Python with `pcbnew` + `wx` |
| Export DSN with net classes | `prepare-routing.py` (`ExportSpecctraDSN`) | KiCad Python |
| Route | external Specctra autorouter; tool name not recorded in the repo (**UNVERIFIED**, presumably Freerouting) | — |
| Import SES + pours | `finish-board-b.py` (`ImportSpecctraSES`, GND + negative-rail zones) | KiCad Python |
| Restore project rules | `configure-board-b.py` | — |
| Silkscreen artwork | `apply-back-silkscreen.py`, `place-assembly-labels.py` | — |
| Checks | `verify-board-b.py`, `verify-power-layout.py`, `verify-compact-mechanics.py`, `check-model-paths.py`, `check-model-bodies.py`, `verify-step-datums.py` | mixed |
| Export | `export-jlcpcb.py`, `verify-jlcpcb.py`, `export-assembly-preview.py` | `kicad-cli`, `uv` |

Safety habits built into every script: refuses to overwrite an existing output path; writes to a new path and promotes only after checks; copies the `.kicad_pro` beside a temporary PCB because a native pcbnew save can reset project defaults.

Board B net classes (`board-b.kicad_pro`): Default 0.25 mm track / 0.25 mm clearance / via 1.2 / 0.6; `Power` 1.0 mm; `PD feed` 1.5 mm. Design-rule minimums: clearance 0.2, track 0.2, via Ø0.8, annular 0.25, hole 0.3, copper-to-edge 0.3, text height 0.8.
Board P: Default 0.2 / 0.2 / via 0.6 / 0.3; minimums 0.127 mm clearance and track, copper-to-edge 0.5.

DRC severities set to `ignore` in both projects: `footprint_filters_mismatch`, `footprint_type_mismatch`, `missing_courtyard`, `track_not_centered_on_via`, `tuning_profile_track_geometries` (Board P also `duplicate_footprints`).

---

## ERC, DRC and exports run through kicad-cli, which this WSL machine does not have

Exact commands from `scripts/pcb/export-jlcpcb.py`:

```sh
kicad-cli pcb drc --refill-zones --save-board --schematic-parity --format json -o checks/drc.json <board>.kicad_pcb
kicad-cli sch erc --format json -o checks/erc.json <board>.kicad_sch
kicad-cli sch export pdf -o schematic.pdf <board>.kicad_sch
kicad-cli sch export netlist --format kicadsexpr -o raw/<board>.net <board>.kicad_sch
kicad-cli pcb export gerbers -l F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts,F.Paste,B.Paste --use-drill-file-origin --subtract-soldermask -o gerbers <board>.kicad_pcb
kicad-cli pcb export drill --format excellon --drill-origin plot --excellon-units mm --excellon-separate-th --excellon-oval-format route -o gerbers <board>.kicad_pcb
kicad-cli pcb export pos --format csv --units mm --use-drill-file-origin --exclude-dnp -o raw/positions.csv <board>.kicad_pcb
kicad-cli pcb export svg --mode-single --fit-page-to-board --exclude-drawing-sheet --sketch-pads-on-fab-layers -l F.Cu,F.Fab,F.Silkscreen,Edge.Cuts -o assembly-top.svg <board>.kicad_pcb
kicad-cli pcb render --width 1800 --height 1400 --quality high --rotate 20,0,-15 --zoom 0.8 -o 3d-top.png <board>.kicad_pcb
```

Where they run:

- All recorded runs used macOS paths (`/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`, KiCad-bundled Python 3.9 for `pcbnew`). The exporter's `--kicad-python` default is macOS-only.
- **On this machine**: `kicad-cli` not on PATH, no Windows KiCad under `/mnt/c/Program Files/KiCad`. Docker 29.3.0 is installed.
- The only KiCad image present locally is `kicad/kicad@sha256:e638b79b…7729` = **KiCad 9.0.9**, used by zudo-pd solely to render `.kicad_mod` previews (`doc/component-docs/footprint-previews/config.ts`). It cannot open `20260206` / `20260306` board files (**UNVERIFIED by execution**; follows from the format version).
- Docker Hub lists `kicad/kicad:10.0.0` … `10.0.6` (amd64), so a containerised KiCad 10 `kicad-cli` is available but not yet pulled.
- CI (`.github/workflows/component-spec-skills.yml`) deliberately runs **no KiCad**: only pure-Python checks.

---

## lefthook guards documentation only, never KiCad files

`lefthook.yml` (origin/main):

| Hook | Command | Scope |
| --- | --- | --- |
| `skip_lfs: true` | — | Git LFS is prohibited repo policy |
| pre-commit `format-mdx` | `./scripts/mdx-format.sh --write {staged_files}`, `stage_fixed: true` | `doc/src/content/docs/**/*.{md,mdx}`, excluding generated `components/**` |
| pre-push `check-doc` | `(cd doc && pnpm run check)` | only when the branch is `main` |

Hardware integrity is enforced in CI and by the exporter, not by git hooks.

CI jobs: `component-spec-skills.yml` (validator strict, unit tests, forward tests, schgen smoke test, regen-idempotency for boards A/B/P via `git diff --exit-code -- boards/`, label geometry, baseline drift, decision lock, courtyard check, bare-copper attribute check, doc-engine tests); `pr-checks.yml` (doc build + preview deploy); `main-deploy.yml` (doc build + Cloudflare Workers deploy, gated on secrets being present).

---

## CLAUDE.md rules for agents editing KiCad files

From root `CLAUDE.md`, `footprints/CLAUDE.md`, `boards/README.md`, `scripts/schgen/README.md`:

1. **Never hand-edit a generated `.kicad_sch`.** Edit the spec module, regenerate, and commit spec + schematic together.
2. **Never regenerate the historical root project** from split-board specs.
3. **PCB has separate layout ownership.** Sync identities and nets with the schematic, then review routing, power loops, returns, copper capacity, thermal paths, connector orientation, clearances.
4. **Component work starts at the inventory.** Any part identity / rating / pin / footprint / substitution question routes through `.claude/skills/component-spec-audit/` (inventory.json: 60 lines, 11 exclusions) and the matching `component-*` owner skill (30 bundles). Never answer from memory.
5. **The generated component catalog under `doc/src/content/docs/components/` is never hand-edited.**
6. **Footprints**: write to both library locations byte-identically; courtyards are generated by `footprints/scripts/gen_courtyards.py` (IPC-style 0.25 mm excess, 0.05 mm stroke), never hand-drawn.
7. **Bare-copper footprints** (test pads, pogo pads, fiducials, mounting features) must carry `(attr smd exclude_from_pos_files exclude_from_bom)`; v0.4.0 shipped phantom CPL rows without it.
8. **Hand-created footprints** use the `zudo-pd:<Name>` tag and the legacy `(module …)` format.
9. **Never use Git LFS.** Large assembled STEP previews stay local; their hashes are recorded in `manufacturing/local-only-assembly-previews.json`, and checks must fail if a required local file is missing.
10. **No backup snapshot folders**; keep only the latest PCB and package, use git history.
11. **Document connectivity as net tables + Mermaid**, never ASCII-art schematics: `Net | Connected pins (Ref.Pin) | Value/Note`.
12. **English only** for docs, labels, comments, commit messages.
13. **A clean DRC / ERC / export is never described as qualification**; every package states its blockers.
14. **Versioning actions** only through `.claude/skills/l-bump-version-{x,y,z}` and only when requested.
15. `pd-schematic-review` skill is read-only against `*.kicad_sch` / `*.kicad_pcb` and confirms `git status --porcelain` is empty before finishing.

---

## JLCPCB ordering is a scripted, hash-locked export with BOM/CPL parity checks

Templates: `jlcpcb-templates/sample-bom.xlsx` (columns `Comment, Designator, Footprint, JLCPCB Part #`) and `sample-cpl.xlsx` (`Designator, Mid X, Mid Y, Layer, Rotation`).

Current practice (`scripts/pcb/export-jlcpcb.py`, `doc/src/content/docs/how-to/jlcpcb-package.md`):

```sh
python3 scripts/pcb/export-jlcpcb.py tmp/current-prototype-export --boards board-p board-b
uv run --with gerbonara --with resvg-py python scripts/pcb/verify-jlcpcb.py tmp/current-prototype-export
```

What the exporter enforces before writing anything:

- Output directory must not exist.
- `validate.py --strict` and `check_forward_tests.py --strict` pass (preflight.log).
- Power reports, assembly preview and STEP datum proofs are fresh against current PCB hashes.
- PCB reference set equals `spec.COMPONENTS` (extra footprints must be bare-copper with exclusion attrs).
- Per part: footprint name, `Value`, DNP flag, inventory LCSC, PCB `LCSC` property and every alias all agree.
- DRC: zero errors, zero unconnected, parity issues only `extra_footprint`. ERC: zero errors.
- Exported netlist equals the spec (`verify_netlist.py`).
- CPL rows equal BOM refs exactly; each CPL coordinate is cross-checked against the footprint position and the aux origin.
- Source files unchanged during export.

Outputs per board: `<board>-gerbers.zip`, `gerbers/`, `bom.csv`, `cpl.csv`, `excluded.csv`, `schematic.pdf`, `assembly-top.svg`, `assembly-bottom.svg`, `3d-top.png`, `gerber-*.png/svg`, `source/` snapshot, `raw/`, `checks/` (`commands.log`, `drc.json`, `erc.json`, `export-validation.json`, `model-paths.json`, `model-bodies.json`). Package level: `manifest.json`, `SHA256SUMS` (152 lines), `ORDER-NOTES.md`, `preflight.log`, `independent-validation.json`.

Conventions worth copying:

- BOM `Comment` = exact MPN; grouping key = (MPN, LCSC, footprint).
- CPL uses native KiCad coordinates with the drill/place origin at the board's bottom-left aux origin; Y is already Cartesian — **do not negate again**. Rotations are native KiCad angles and must still be checked in JLCPCB's placement preview.
- DNP parts and bare copper go to `excluded.csv` with a reason, never silently dropped.
- Through-hole connectors need an explicit assembly decision (wave / hand), not assumed SMT.
- After a real order: copy exactly the submitted files to `jlcpcb-order-snapshots/v0_Y_0-<board>/used-for-order/`, recover JLCPCB's confirmed BOM into `from-order-detail/`, bump Y.

Historical practice (legacy board): the `kicad-jlcpcb-tools` KiCad plugin (Bouni), valued for its rotation-correction database after v0.2.0 shipped a QFN-24 with a 180° vs 270° mismatch. Part libraries come from `easyeda2kicad --lcsc_id <id> --footprint --symbol`.

---

## The documentation stack here is the project-local generator the handoff tells the synth not to copy

- `doc/` uses `@takazudo/zudo-doc` 5.21.0, `@takazudo/zfb` 2.16.0, `@takazudo/zfb-adapter-cloudflare` 2.16.0, pnpm 11.5.2, Node 22.
- `doc/component-docs/` is a project-local TypeScript generator (ported from zudo-led-lamp) that projects `.claude/skills/component-*` evidence into `doc/src/content/docs/components/`.
- Deployed as a Cloudflare Workers static-assets site: `doc/wrangler.toml` `name = "zudo-pd"`, `[assets] directory = "./dist"`, production route `pd.takazudomodular.com` with `custom_domain = true`, deploy via `wrangler deploy --env production`, account id read from the environment.
- The handoff's `LOCAL_AGENT_PROMPT.md` (source material) says to use the official `Takazudo/zudo-circuit-doc` initializer, "not the lamp's old project-local generator". zudo-pd is an instance of that older pattern. Use it as a reference for deploy wiring and CI gating only.

---

## Other directories carry nothing the synth needs

| Path | Content |
| --- | --- |
| `design-resources/` | One file, `zudo-pd-ai-resources.ai` (2.76 MB Illustrator artwork) |
| `3dp-files/` | `adhesive-leg/` only (generator, verifier, STL/STEP, fit report) |
| `diagram-sources/` | 7 schemdraw scripts for the power stages |
| `experiments/ai-circuit-design/` | `schematic-review`, `spice-value-sizing`, `circuit-synth-spike` |
| `jlcpcb-templates/` | 2 sample xlsx files |
| `.env.example` | 2 keys, values REDACTED (legacy Netlify) |

---

## Paths

- Local repo: `$HOME/repos/circuits/zudo-pd`
- Handoff: `_temp-resource/1-osc-hole-field/handoff-r21/zudo-osc-playground-r21-handoff`
- Handoff power pages: `payload/doc/src/content/docs/architecture/osc-power.mdx`, `payload/doc/src/content/docs/research/part-zudo-pd.mdx`
- Handoff contracts: `payload/project/osc-playground/board-contracts.json` (domain `P/B`), `open-issues.json` (G10), `decisions.json` (D10), `kicad-sheet-plan.json` (`01_power_interfaces`)
- Explorer scratch clone (throwaway): `<scratch>/08-sibling-zudo-pd/zudo-pd-remote`
