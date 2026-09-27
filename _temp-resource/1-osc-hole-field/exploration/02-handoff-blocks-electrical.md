# 02 - Handoff block contracts and electrical definition depth

Explorer 02 of 9 for the `zudo-osc-hole-field` plan (design-conversation name: `zudo-osc-playground`). Exploration only; nothing in the handoff or any repo was modified. Date: 2026-09-28.

Path aliases used below:

- `<H>` = `$DROPBOX_CCLOGS_DIR/zudo-osc-hole-field/handoff-r21/zudo-osc-playground-r21-handoff`
- `<P>` = `<H>/payload/project/osc-playground`
- `<D>` = `<H>/payload/doc/src/content/docs`
- `<R>` = `<H>/payload/research/osc-playground`
- Sibling repos: `$HOME/repos/circuits/zudo-pd`, `$HOME/repos/circuits/zudo-led-lamp`, `$HOME/repos/circuits/zudo-case`

Two kinds of statement appear in this report and are kept apart:

- **HANDOFF** = verified by parsing or reading a handoff file.
- **PROPOSAL** = this explorer's engineering default. It is NOT handoff content and has no owner approval.

## The handoff fixes every jack and control, and almost no circuit

- 33 block instances, 180 jacks, 144 controls parse cleanly and match `current-spec.json` exactly.
- Only S&H+SLEW carries component values (one RC lag, one hold cap, one quad buffer). The other ten module types carry one sentence of behaviour plus a list of unresolved decisions.
- `kicad-sheet-plan.json` describes itself as "Sheet responsibilities, not an electrical netlist". `current-spec.json` phase is "Feature/layout handoff; pre-schematic and pre-layout".
- Consequence for the plan: "author the KiCad schematic" is circuit DESIGN work for ten of eleven module types, not transcription.

## All 13 source groups parsed without error

| File | What it gave |
| --- | --- |
| `<P>/block-contracts.json` (78,769 bytes, list of 33 blocks) | ports, controls, `behavior`, `engineering_to_finish` per instance |
| `<P>/kicad-sheet-plan.json` | 18 sheet names and responsibilities; library name `zudo_osc_playground`; 5 `required_before_layout` rules |
| `<P>/board-contracts.json` | 8 board domains, datum, 10 `interface_fields_to_complete` |
| `<P>/current-spec.json` | counts, hard constraints, `not_claimed` list |
| `<P>/decisions.json` | D01..D12, 9 USER + 3 PROPOSAL (D07, D08, D11) |
| `<P>/open-issues.json` | G01..G14, all `OPEN` |
| `<P>/workbench/layout/grid.json` | switch `positions` arrays (absent from block-contracts.json), pitch presets |
| `<P>/workbench/reference/switch-functions.json` | switch defaults and state explanations |
| `<P>/workbench/reference/panel.json` | historic R17 model; AO ranges, LED semantics, stage-LED behaviour |
| `<P>/workbench/mechanical/core-allocations.json`, `board-planes.json` | 47 preview IC rectangles; 13 board planes |
| `<P>/workbench/src/ar-engine.js`, `sh-slew-engine.js`, `app.js`, `three.js` | ideal UI behaviour; control-to-board mapping |
| `<D>/architecture/*.mdx` (15), `decisions/osc-scope-freeze.mdx`, `project/*.mdx` (2), `verification/*.mdx` (2) | narrative contracts and gates |
| `<R>/slew-circuit-proposal.json`, `slew-calculations.json`, `slew-ideal.cir`, `component-candidates.json`, `pin-map-intake.json` | the only numeric circuit content |

## Counts match current-spec exactly: 33 blocks, 180 jacks, 144 controls

| Family (handoff id) | Instances | Instance ids | Jacks/inst (in+out) | Controls/inst | Magnitude LEDs/inst | Clip LEDs/inst | Stage LEDs/inst |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OSC (`OSC`) | 5 | O1, O2, O3, O4, O5 | 8 (4+4) | 8 (1 octave, 2 switch, 5 pot) | 0 | 0 | 0 |
| FILTER/VCA (`VCF`) | 3 | F1, F2, F3 | 8 (4+4) | 6 (6 pot) | 4 | 0 | 0 |
| MIX5 (`MIX5`) | 2 | M5A, M5B | 6 (5+1) | 6 (6 pot) | 6 | 1 | 0 |
| MIX4+VCA (`MIX4`) | 2 | M4A, M4B | 6 (5+1) | 6 (6 pot) | 6 | 1 | 0 |
| AR (ENV) (`AR`) | 6 | E1, E2, E3, E4, E5, E6 | 7 (3+4) | 6 (3 switch, 1 button, 2 pot) | 3 | 0 | 2 |
| FOLD (`FOLD`) | 2 | W2, W1 | 4 (3+1) | 4 (4 pot) | 3 | 0 | 0 |
| OFFSET (AO) (`AO`) | 6 | A01, A02, A03, A04, A05, A06 | 3 (2+1) | 2 (2 pot) | 3 | 1 | 0 |
| MULT 1:3 (`MULT`) | 2 | B1, B2 | 4 (1+3) | 0 (none) | 1 | 0 | 0 |
| S&H+SLEW (`SH`) | 2 | H1, H2 | 3 (2+1) | 2 (1 button, 1 pot) | 3 | 0 | 0 |
| MANUAL A/B (SWITCH) (`SWITCH`) | 2 | X1, X2 | 3 (2+1) | 1 (1 switch) | 3 | 0 | 0 |
| NOISE (`NOISE`) | 1 | N1 | 4 (0+4) | 0 (none) | 0 | 0 | 0 |
| **Total** | **33** | | **180** | **144** | **92** | **10** | **12** |

Control parts by candidate record: 99 x `bourns-ptv09a-4020f-b103`, 2 x `bourns-ptv09a-4020f-b504`, 19 x `dailywell-2ms1`, 11 x `dailywell-2ms3`, 8 x `omron-b3f1020`, 5 x `alps-srbv160803`. Jack directions: 98 in, 82 out. Within each family every instance has an identical port/control signature and identical behaviour text (checked programmatically), so one hierarchical sheet per family is valid.

## Signal standards: the handoff states almost none

| Standard | HANDOFF statement | Status |
| --- | --- | --- |
| Audio level | None. OSC "pulse and sine amplitudes" listed as unresolved. | UNDEFINED |
| CV range | None. Preview uses AO manual offset -5..+5 V and a +/-10 V clip demo, both flagged "illustrative, not a specification". ENV preview peak is 5 V (`app.js`: `snap.level*5`). Bench plan steps are +/-1 V and +/-5 V. Slew hazard arithmetic assumes a 16 V jump. | UNDEFINED |
| V/oct | Jack label "1V/OCT" only. "V/oct scale/offset" unresolved; "calibrated V/oct tracking" is in `not_claimed`. Only numeric fact: 1 mV = 1.2 cents at 1 V/oct. | LABEL ONLY |
| Gate/trigger threshold | None. LM393 "with designed hysteresis and a 5 V pull-up domain"; acquisition one-shot 50-100 us is "a test starting point". | UNDEFINED |
| Input impedance | None numeric. MULT is "high-impedance input". `osc-blocks.mdx` lists input impedance as something to document per block. | UNDEFINED |
| Output impedance / load | None numeric. `slew-ideal.cir` uses `Rload 100k`. MULT note: output resistor outside feedback gives load error. | UNDEFINED |
| Power rails | `slew-circuit-proposal.json` `rails_proposed_V: [-12, 12]`; LM393 caveat mentions +/-12 V and a 5 V logic domain. Supply = reused zudo-pd. | PROPOSED +/-12 V and +5 V |
| Protection | G08 requirement only: inputs survive negative/high signal and power-off backfeed; outputs survive short and output-to-output patch; precision outputs keep a load-error budget. No circuit. | REQUIREMENT ONLY |
| Inter-module normals | None allowed (D03, `no_interblock_normals: true`). Jack switch contacts are unused. | DEFINED |
| LED semantics | Magnitude LED = "Absolute magnitude / audio envelope; not polarity or plug detection". Stage LED follows ENV only during its own stage, off in sustain and idle. Clip LED = near-saturation, threshold unqualified. No OSC LEDs. | BEHAVIOUR DEFINED, CIRCUIT UNDEFINED |
| Sensitive nodes | LF398 hold cap, oscillator timing cap, envelope integrator node, SLEW storage node must never cross a connector. | DEFINED (layout rule) |

### PROPOSAL: adopt one instrument-wide electrical standard before any sheet

Explorer default, not handoff content. Without it no sheet can be completed (this is what G08 asks for).

| Item | Default |
| --- | --- |
| Rails | +12 V, -12 V analogue; +5 V logic, all from zudo-pd |
| Audio | 10 Vpp (+/-5 V) nominal |
| Bipolar CV | +/-5 V nominal; every input tolerates +/-12 V continuously |
| Envelope | ENV 0..+8 V; BIP -5..+5 V (alternative: 0..+5 V to match the preview) |
| Pitch | 1.000 V/oct, 0.1 % resistors on pitch paths |
| Gate/trigger out | 0 V / +5 V |
| Gate/trigger in | rising threshold about +1.5 V, falling about +1.0 V (comparator with hysteresis) |
| Input impedance | 100 k nominal (50 k acceptable at attenuverter inputs) |
| Output, general | op-amp + 1 k series |
| Output, precision (MULT, S&H OUT, AO OUT) | 100-470 ohm inside the feedback loop with a small compensation cap |
| Input protection | summing-node inputs: the 100 k input resistor is the protection; high-Z inputs: series R + dual Schottky clamp to the rails + pulldown |
| Magnitude LED full scale | 5 V = about 1 mA |
| Clip threshold | +/-10 V at the monitored internal node |

## "15V-only" means the USB-PD sink must be unable to request 20 V

- HANDOFF (`<D>/architecture/osc-power.mdx`, G10): "The new Board P documentation identifies SMAJ16A and a required verified 15 V-only PD configuration." First power/program from a current-limited 5 V-only source with the downstream board disconnected, retain NVM readback, verify that no 20 V request is enabled.
- Verified in `$HOME/repos/circuits/zudo-pd/doc/src/content/docs/inbox/nvm-programming.md`: the PD sink is an STUSB4500. Factory NVM advertises PDO3 = 20 V / 1 A at highest priority, so a 20 V-capable charger negotiates 20 V on first plug-in. The required programmed state is `SNK_PDO_NUMB = 2` (PDO1 5 V + PDO2 15 V / 3 A only), `POWER_ONLY_ABOVE_5V` enabled.
- So "programmed 15V-only state" is a property of one chip's non-volatile memory on the supply board, not a property of this synth's circuits. A TVS with 16 V standoff on the 15 V bus would conduct at a 20 V contract, which is why the state must be proven before energizing.

### Handoff naming does not match the local zudo-pd checkout

| Handoff says | Local `zudo-pd` at `797a221` (VERSION 0.4.0) says |
| --- | --- |
| "Board P + Board B" | `boards/board-a` (USB-PD sink core) + `boards/board-b` (synth power). "Board P" is the zudo-led-lamp name for its PD board. |
| SMAJ16A | Not present in zudo-pd, zudo-led-lamp or zudo-case (grep, 0 hits). zudo-pd uses D5 SMAJ20A on `VBUS_IN` and SMAJ15A on the +/-12 V outputs. |

The SMAJ16A / Board P claim is UNVERIFIED locally. The plan must resolve which exact board revision is reused before writing sheet `01_power_interfaces`.

Rated outputs, zudo-pd Board B design doc: +12 V / 1.2 A, -12 V / 0.8 A, +5 V / 0.5 A. The zudo-pd `readme.md` says -12 V / 1.0 A and +5 V / 1.2 A. The two disagree; the lower figures are used for budgeting here.

## Every module maps to a sheet; only the SLEW sheet names its board

Sheet names are HANDOFF (`kicad-sheet-plan.json`). Board domains are HANDOFF (`board-contracts.json`); the per-control board assignment is the preview mapping in `<P>/workbench/src/three.js` and is provisional. The sheet plan itself never states which board a sheet belongs to, except `63_post_hold_slew` ("on local pot-board island").

| Module | Qty | Module sheet(s) | Shared sheets it also uses | Circuit board | Panel-hardware boards |
| --- | --- | --- | --- | --- | --- |
| OSC | 5 | `10_osc_channel` (instantiate five), `11_octave_reference` | `80_connectors` | K | J (8 jacks), O (OCT), OS (RANGE, SYNC), OP (5 pots) |
| FILTER/VCA | 3 | `20_filter_vca` (instantiate three) | `70_indicators`, `80_connectors` | K | J (8 jacks), MP (6 pots) |
| MIX5 | 2 | `30_mix5` (instantiate two) | `70_indicators`, `80_connectors` | K | J (6), MP (6 pots) |
| MIX4+VCA | 2 | `31_mix4_vca` (instantiate two) | `70_indicators`, `80_connectors` | K | J (6), MP (6 pots) |
| AR | 6 | `40_envelope` (instantiate six), `41_env_stage_led` | `70_indicators`, `80_connectors` | K | J (7), ES (3 toggles), ET (button), EP (2 pots + 2 stage LEDs) |
| FOLD | 2 | `50_folder` (instantiate two) | `70_indicators`, `80_connectors` | K | J (4), MP (4 pots) |
| OFFSET | 6 | `60_offset` (instantiate six) | `70_indicators`, `80_connectors` | K | J (3), EP (2 pots) |
| MULT 1:3 | 2 | `61_mult` (instantiate two) | `70_indicators`, `80_connectors` | K | J (4) |
| S&H+SLEW | 2 | `62_sample_hold`, `63_post_hold_slew` | `70_indicators`, `80_connectors` | K (LF398, hold cap, one-shot, comparator) and UP (pot, RC lag, pre/post buffers) | J (3), UT (SAMPLE button), UP (SLEW pot) |
| MANUAL A/B | 2 | `64_manual_ab` | `70_indicators`, `80_connectors` | K | J (3), US (toggle) |
| NOISE | 1 | `65_noise` | `80_connectors` | K | J (4) |
| Power | 1 | `01_power_interfaces` | `00_top` | P/B (reused zudo-pd) feeding K | - |

Board population from the preview mapping (verified by replaying the `three.js` rule over `grid.json`): OP 25 pots, MP 50 pots, EP 24 pots, UP 2 pots, O 5 rotary, OS 10 toggles, ES 18 toggles, US 2 toggles, ET 6 buttons, UT 2 buttons, J 180 jacks. `board-planes.json` lists 13 planes: J, O, OS, OP, MP, ES, ET, EP, UT, UP, US, K, P/B.

Structural consequence: KiCad holds one PCB per project. The 18-sheet plan reads like one hierarchy, but the hardware is 12 new boards plus the reused supply. The plan needs one KiCad project per physical board (the zudo-pd `boards/board-a`, `boards/board-b` pattern) with the module sheets living in the K project.

## Per module: 3 capturable now, 3 after a level standard, 1 partly, 4 need design

Each section gives the HANDOFF contract, then what is undefined, then the PROPOSAL default. `<inst>` stands for the instance id.

### OSC x5: not capturable now, the largest open design

Instances: `O1` (OSC 1), `O2` (OSC 2), `O3` (OSC 3), `O4` (OSC 4), `O5` (OSC 5).

| Jack key | Panel label | Dir | Signal role | Magnitude LED | Clip LED |
| --- | --- | --- | --- | --- | --- |
| `<inst>.1V` | 1V/OCT | in | pitch CV; panel label 1V/OCT, scale/offset unresolved | no | no |
| `<inst>.FM` | FM | in | frequency-modulation input; depth via FM+/- pot; exp vs linear undefined | no | no |
| `<inst>.PWM` | PWM | in | pulse-width modulation CV; depth via PWM+/- pot | no | no |
| `<inst>.SYNC` | SYNC CV | in | sync source; routed by SYNC toggle SOFT/OFF/HARD (OFF ignores jack) | no | no |
| `<inst>.SIN` | SIN | out | raw sine output (needs separate shaper; amplitude undefined) | no | no |
| `<inst>.TRI` | TRI | out | raw triangle output (amplitude undefined) | no | no |
| `<inst>.SAW` | SAW | out | raw sawtooth output (amplitude undefined) | no | no |
| `<inst>.PUL` | PUL | out | raw pulse output (amplitude undefined) | no | no |

| Control key | Panel label | Kind | Candidate part | Positions (grid.json) | Function | Interface board (preview mapping) |
| --- | --- | --- | --- | --- | --- | --- |
| `<inst>.OCT` | OCT | octave | alps-srbv160803 | -2/-1/0/1/2/3 | octave select, 6 indexed positions | O |
| `<inst>.VCO/LFO` | RANGE | switch | dailywell-2ms1 | LFO/VCO | range select (panel label RANGE) | OS |
| `<inst>.SYNC` | SYNC | switch | dailywell-2ms3 | SOFT/OFF/HARD | sync mode select | OS |
| `<inst>.TUNE` | TUNE | pot | bourns-ptv09a-4020f-b103 | continuous | coarse tune (span undefined) | OP |
| `<inst>.FINE` | FINE | pot | bourns-ptv09a-4020f-b103 | continuous | fine tune (span undefined) | OP |
| `<inst>.FM±` | FM ± | pot | bourns-ptv09a-4020f-b103 | continuous | FM depth, bipolar attenuverter | OP |
| `<inst>.PW` | PW | pot | bourns-ptv09a-4020f-b103 | continuous | manual pulse width | OP |
| `<inst>.PWM±` | PWM ± | pot | bourns-ptv09a-4020f-b103 | continuous | PWM depth, bipolar attenuverter | OP |

Handoff `behavior`: "Independent ADDAC701-inspired oscillator. Six-position octave control; continuous TUNE/FINE; LFO/VCO range, FM/PWM and soft/off/hard sync targets. Four raw waveforms."

Handoff `engineering_to_finish`: "AS3340D plus required sine shaping is a candidate, not a complete core. Resolve V/oct scale/offset, octave ladder, switch bounce, FM topology, hard/soft sync, pulse and sine amplitudes, LFO limits, startup and factory calibration. No through-zero assumption."

- LEDs: none. Candidate note for the white LED says "No OSC lamps".
- Candidate core ICs (HANDOFF): AS3340D SOIC-16 x5, no JLC/LCSC code, "Carry-forward external candidate; not requalified". TL074 for shaping. Preview allocates 1 x AS3340D + 1 x TL074 per oscillator as an area rectangle only.
- Switch defaults (HANDOFF `switch-functions.json`): RANGE default VCO; SYNC default OFF.
- HANDOFF specifies: function list, control set, octave positions -2..+3, no through-zero FM.
- HANDOFF leaves undefined: every component value; V/oct scale and offset; octave ladder; switch bounce handling; FM topology; hard and soft sync implementation; all four output amplitudes; LFO limits; startup; calibration method; negative-supply arrangement; temperature compensation.

PROPOSAL default: AS3340 datasheet VCO.

1. Core per the AS3340/CEM3340 datasheet application circuit: C0G timing cap local to the IC, negative supply through the datasheet series resistor, scale and high-frequency-tracking trims.
2. Pitch summing at the IC's frequency-control summing node: 1V/OCT through 100 k 0.1 %, TUNE and FINE through scaled resistors, octave voltage through 100 k 0.1 %.
3. Octave reference (sheet 11): one precision reference, a 0.1 % ladder with 1.000 V steps, the 6-position switch selects a tap, a buffer on K receives it. Only a low-impedance DC voltage crosses the O-to-K connector.
4. RANGE = a switched DC offset into the pitch summer (about -7 octaves), NOT a switched timing capacitor. Reason: the RANGE toggle sits on board OS and the timing node may not cross a connector.
5. FM = exponential FM through the FM+/- attenuverter into the pitch summer. Alternative: AC-coupled linear FM into the IC's linear-FM input.
6. SYNC = comparator-conditioned edge routed by the toggle to the IC's hard-sync input, soft-sync input, or nowhere.
7. PW + PWM+/- summed by one op-amp into the PWM control input.
8. TRI, SAW, PUL each level-shifted and scaled to +/-5 V by one op-amp section.
9. SIN = triangle-to-sine shaper using a matched differential pair plus one op-amp section, two trims.

Size: about 9 op-amp sections (3 quads with spares), 1 AS3340D, half an LM393, 1 matched pair, about 75 R, 22 C, 4 trimmers.

Decisions still required: exp vs linear FM; RANGE mechanism; TUNE and FINE spans; frequency range; output levels; who turns the trimmers (factory or owner); shared vs per-oscillator octave reference.

### FILTER/VCA x3: not capturable until G06 is decided

Instances: `F1` (FILTER 1), `F2` (FILTER 2), `F3` (FILTER 3).

| Jack key | Panel label | Dir | Signal role | Magnitude LED | Clip LED |
| --- | --- | --- | --- | --- | --- |
| `<inst>.IN` | IN | in | signal input feeding filter core and dry VCA | yes | no |
| `<inst>.FREQ` | FREQ CV | in | cutoff CV; depth via FREQ+/- pot | yes | no |
| `<inst>.RES` | RES CV | in | resonance CV; depth via RES+/- pot | yes | no |
| `<inst>.GAIN` | GAIN CV | in | VCA gain CV; depth via GAIN+/- pot | yes | no |
| `<inst>.LP` | LP | out | low-pass output (GAIN dependence = open issue G06) | no | no |
| `<inst>.BP` | BP | out | band-pass output (GAIN dependence = open issue G06) | no | no |
| `<inst>.HP` | HP | out | high-pass output (GAIN dependence = open issue G06) | no | no |
| `<inst>.OUT` | OUT | out | unfiltered (dry) VCA output, parallel to LP/BP/HP | no | no |

| Control key | Panel label | Kind | Candidate part | Positions (grid.json) | Function | Interface board (preview mapping) |
| --- | --- | --- | --- | --- | --- | --- |
| `<inst>.FREQ` | FREQ | pot | bourns-ptv09a-4020f-b103 | continuous | manual cutoff | MP |
| `<inst>.RES` | RES | pot | bourns-ptv09a-4020f-b103 | continuous | manual resonance | MP |
| `<inst>.FREQ±` | FREQ± | pot | bourns-ptv09a-4020f-b103 | continuous | FREQ CV depth, bipolar | MP |
| `<inst>.RES±` | RES± | pot | bourns-ptv09a-4020f-b103 | continuous | RES CV depth, bipolar | MP |
| `<inst>.GAIN` | GAIN | pot | bourns-ptv09a-4020f-b103 | continuous | manual VCA gain | MP |
| `<inst>.GAIN±` | GAIN± | pot | bourns-ptv09a-4020f-b103 | continuous | GAIN CV depth, bipolar | MP |

Handoff `behavior`: "Parallel dry VCA OUT plus LP/BP/HP outputs. Frequency/resonance/gain controls and corresponding CV depth. No selector required."

Handoff `engineering_to_finish`: "Write a signal diagram deciding whether GAIN also scales LP/BP/HP. R21 baseline proposal: LP/BP/HP upstream of dry OUT VCA; do not silently change this. Qualify resonance/self-oscillation/stability and overload."

- LEDs: 4 magnitude LEDs, one per input jack.
- Candidate core ICs (HANDOFF): LM13700M/NOPB SOIC-16 (C1346265) and TL074CDT SOIC-14 (C6963), "Quantity: Circuit-dependent". Preview allocates 1 x LM13700 + 1 x TL074 per filter.
- HANDOFF specifies: four outputs; "R21 baseline proposal: LP/BP/HP upstream of dry OUT VCA; do not silently change this"; R17 reference text for OUT: "Unfiltered VCA output, parallel to LP/BP/HP: proposed circuit contract"; no selector.
- HANDOFF leaves undefined: filter topology and order; whether GAIN scales LP/BP/HP (G06); whether RES responds on all paths; self-oscillation; CV laws; all values.

PROPOSAL default: LM13700 state-variable filter plus a separate OTA VCA.

1. Two-integrator state-variable loop from the LM13700 datasheet, giving HP, BP, LP simultaneously (12 dB/oct).
2. Exponential converter (matched pair + op-amp) driving both integrator bias currents from FREQ + attenuverted FREQ CV.
3. Voltage-controlled resonance = a third OTA in the damping feedback path.
4. Dry VCA = a fourth OTA from the buffered input to OUT, linear gain law, GAIN + attenuverted GAIN CV.
5. GAIN acts on OUT only. LP/BP/HP are taken from the filter, unaffected by GAIN. This is the reading of the R21 baseline; it must be confirmed by the owner.

This needs 4 OTAs = 2 x LM13700 per filter. The preview's single LM13700 per filter is not enough for this topology.

Size: about 12 op-amp sections (3 quads), 2 LM13700, 1 matched pair, about 85 R, 22 C, 3 trimmers.

### MIX5 x2: capturable after the level standard is fixed

Instances: `M5A` (MIX5 A), `M5B` (MIX5 B).

| Jack key | Panel label | Dir | Signal role | Magnitude LED | Clip LED |
| --- | --- | --- | --- | --- | --- |
| `<inst>.1` | 1 | in | signal input 1 into its own bipolar attenuverter | yes | no |
| `<inst>.2` | 2 | in | signal input 2 into its own bipolar attenuverter | yes | no |
| `<inst>.3` | 3 | in | signal input 3 into its own bipolar attenuverter | yes | no |
| `<inst>.4` | 4 | in | signal input 4 into its own bipolar attenuverter | yes | no |
| `<inst>.5` | 5 | in | signal input 5 into its own bipolar attenuverter | yes | no |
| `<inst>.SUM` | SUM | out | mono sum after manual LEVEL | yes | yes |

| Control key | Panel label | Kind | Candidate part | Positions (grid.json) | Function | Interface board (preview mapping) |
| --- | --- | --- | --- | --- | --- | --- |
| `<inst>.1±` | 1 ± | pot | bourns-ptv09a-4020f-b103 | continuous | input 1 gain, bipolar attenuverter | MP |
| `<inst>.2±` | 2 ± | pot | bourns-ptv09a-4020f-b103 | continuous | input 2 gain, bipolar attenuverter | MP |
| `<inst>.3±` | 3 ± | pot | bourns-ptv09a-4020f-b103 | continuous | input 3 gain, bipolar attenuverter | MP |
| `<inst>.4±` | 4 ± | pot | bourns-ptv09a-4020f-b103 | continuous | input 4 gain, bipolar attenuverter | MP |
| `<inst>.5±` | 5 ± | pot | bourns-ptv09a-4020f-b103 | continuous | input 5 gain, bipolar attenuverter | MP |
| `<inst>.LEVEL` | LEVEL | pot | bourns-ptv09a-4020f-b103 | continuous | manual output level after sum | MP |

Handoff `behavior`: "Five independent bipolar attenuverters feeding a mono sum, then manual LEVEL."

Handoff `engineering_to_finish`: "Resolve gain normalization/headroom; not automatically divide by five. Indicator at each input and SUM; clip must reflect internal overload, not only attenuated output."

- LEDs: 6 magnitude (five inputs + SUM) and 1 red clip LED at SUM.
- Candidate core ICs (HANDOFF): TL074 ("General mixers"). Preview shows 4 "MIX analogue allocation" quads for all four mixers.
- HANDOFF specifies: five bipolar attenuverters, mono sum, manual LEVEL; "not automatically divide by five"; clip must reflect internal overload, not only the attenuated output.
- HANDOFF leaves undefined: summing gain and headroom; AC or DC coupling; pot value and taper; clip threshold.

PROPOSAL default: five single-op-amp attenuverters (gain 2k-1), inverting unity summer, LEVEL pot as a passive attenuator, output buffer restoring polarity. Clip window comparator senses the summer output BEFORE the LEVEL pot. DC-coupled, unity sum.

Size: 7 op-amp sections (2 quads), about 36 R, 10 C.

### MIX4+VCA x2: capturable after the VCA law is chosen

Instances: `M4A` (MIX4 A), `M4B` (MIX4 B).

| Jack key | Panel label | Dir | Signal role | Magnitude LED | Clip LED |
| --- | --- | --- | --- | --- | --- |
| `<inst>.1` | 1 | in | signal input 1 into its own bipolar attenuverter | yes | no |
| `<inst>.2` | 2 | in | signal input 2 into its own bipolar attenuverter | yes | no |
| `<inst>.3` | 3 | in | signal input 3 into its own bipolar attenuverter | yes | no |
| `<inst>.4` | 4 | in | signal input 4 into its own bipolar attenuverter | yes | no |
| `<inst>.ATTEN` | ATTEN | in | VCA control CV (NOT a fifth audio input); depth via CV+/- pot | yes | no |
| `<inst>.SUM` | SUM | out | post-sum VCA output | yes | yes |

| Control key | Panel label | Kind | Candidate part | Positions (grid.json) | Function | Interface board (preview mapping) |
| --- | --- | --- | --- | --- | --- | --- |
| `<inst>.1±` | 1 ± | pot | bourns-ptv09a-4020f-b103 | continuous | input 1 gain, bipolar attenuverter | MP |
| `<inst>.2±` | 2 ± | pot | bourns-ptv09a-4020f-b103 | continuous | input 2 gain, bipolar attenuverter | MP |
| `<inst>.3±` | 3 ± | pot | bourns-ptv09a-4020f-b103 | continuous | input 3 gain, bipolar attenuverter | MP |
| `<inst>.4±` | 4 ± | pot | bourns-ptv09a-4020f-b103 | continuous | input 4 gain, bipolar attenuverter | MP |
| `<inst>.CV±` | CV ± | pot | bourns-ptv09a-4020f-b103 | continuous | ATTEN CV depth, bipolar | MP |
| `<inst>.LEVEL` | SUM GAIN | pot | bourns-ptv09a-4020f-b103 | continuous | manual VCA gain (panel label SUM GAIN) | MP |

Handoff `behavior`: "Four attenuverters feed summing stage then VCA. ATTEN CV through CV± combines with manual SUM GAIN."

Handoff `engineering_to_finish`: "ATTEN is control, not a fifth audio input. Preserve pre-VCA overload detection when final output is attenuated. Define VCA gain law and allowed input/CV ranges."

- LEDs: 6 magnitude (four inputs + ATTEN CV + SUM) and 1 red clip LED at SUM.
- Candidate core ICs (HANDOFF): LM13700 ("MIX4 gain cells"), TL074.
- HANDOFF specifies: four attenuverters, sum, then VCA; ATTEN CV through CV+/- combines with manual SUM GAIN; pre-VCA overload detection must be preserved.
- HANDOFF leaves undefined: VCA gain law; allowed input and CV ranges; maximum gain; all values.

PROPOSAL default: four attenuverters, inverting summer, one LM13700 OTA as a linear VCA with current-to-voltage output stage, control current from an op-amp + PNP voltage-to-current converter fed by SUM GAIN + attenuverted ATTEN CV. Unity gain at +5 V control. Clip comparator on the summer output before the VCA.

Size: 8 op-amp sections (2 quads), 1 LM13700, about 46 R, 12 C, 1 trimmer.

### AR x6: not capturable now, second-largest open design

Instances: `E1` (ENV 1), `E2` (ENV 2), `E3` (ENV 3), `E4` (ENV 4), `E5` (ENV 5), `E6` (ENV 6).

| Jack key | Panel label | Dir | Signal role | Magnitude LED | Clip LED |
| --- | --- | --- | --- | --- | --- |
| `<inst>.SIG` | SIG | in | trigger/gate input (edge vs gate vs follower scope undecided, G07) | yes | no |
| `<inst>.RISE` | RISE | in | rise-time CV (law undefined) | yes | no |
| `<inst>.FALL` | FALL | in | fall-time CV (law undefined) | yes | no |
| `<inst>.ENV` | ENV | out | unipolar envelope output | no | no |
| `<inst>.BIP` | BIP | out | bipolar version of envelope (scale undefined) | no | no |
| `<inst>.EOC` | EOC | out | end-of-cycle output (pulse duration undefined) | no | no |
| `<inst>.STG` | STG | out | stage gate, high during stage chosen by STAGE toggle | no | no |

| Control key | Panel label | Kind | Candidate part | Positions (grid.json) | Function | Interface board (preview mapping) |
| --- | --- | --- | --- | --- | --- | --- |
| `<inst>.MODE` | MODE | switch | dailywell-2ms3 | ASR/AR/LOOP | operating mode | ES |
| `<inst>.SHAPE` | SHAPE | switch | dailywell-2ms1 | LINEAR/CURVED | segment curve | ES |
| `<inst>.STAGE` | STAGE | switch | dailywell-2ms1 | RISE/FALL | which stage drives STG output | ES |
| `<inst>.TRIG` | TRIG | button | omron-b3f1020 | continuous | manual trigger | ET |
| `<inst>.RISE` | RISE | pot | bourns-ptv09a-4020f-b103 | continuous | rise time (proposed as control-voltage pot, not rheostat) | EP |
| `<inst>.FALL` | FALL | pot | bourns-ptv09a-4020f-b103 | continuous | fall time (proposed as control-voltage pot, not rheostat) | EP |

Handoff `behavior`: "ASR/AR/LOOP; linear/curved; stage gate selection rise/fall; manual trigger. RISE/FALL pots with stage-gated ENV-strength lamps; ENV/BIP/EOC/STG outputs."

Handoff `engineering_to_finish`: "Freeze SIG semantics and retrigger behavior in a truth table. The UI is ideal behavior only. Define trigger thresholds, EOC pulse duration, bipolar output scale and CV law. Never load timing capacitor with indicator."

- LEDs: 3 magnitude (SIG, RISE, FALL input jacks) and 2 white stage LEDs (rise, fall) beside the pots.
- Switch defaults (HANDOFF): MODE default AR; SHAPE default LINEAR; STAGE default RISE.
- Candidate core ICs (HANDOFF): none named. Preview allocates one "analogue allocation" quad and one "comparator" per envelope.
- HANDOFF specifies (ideal behaviour, `ar-engine.js` and state explanations): ASR = rise, sustain while gate high, then release; AR = one contour per accepted trigger; LOOP = repeat, starts without a trigger; gate release during an ASR rise falls from the present level; CURVED = "Logarithmic rise and exponential fall target"; STG gate active during the selected stage; stage LEDs dark in sustain and idle; RISE/FALL pots are "PROPOSED_CONTROL_VOLTAGE_POT", "not a direct rheostat substitution".
- Preview-only numbers, explicitly not circuit values: time 0.25 + 2.5 x pot seconds; minimum 5 ms; curve = cubic ease; peak 5 V.
- HANDOFF leaves undefined (G07): SIG threshold and whether SIG is edge, gate or follower; timing range; CV law; EOC pulse or gate and its duration; retrigger rule; curve circuit; ENV and BIP levels; timing capacitor.

PROPOSAL default: comparator + latch + voltage-controlled integrator.

1. SIG is gate/trigger only, no follower mode. Comparator with hysteresis; TRIG button ORed in after debounce.
2. Two voltage-controlled current sources (one LM13700, or two expo converters) charge and discharge one C0G/film integrator capacitor local to K.
3. Top comparator at +8 V ends the rise; bottom comparator near 0 V ends the fall.
4. A flip-flop holds rise/fall state; MODE selects gate-sustain, one-shot, or EOC-retriggers-itself.
5. SHAPE CURVED = feed a fraction of ENV back into both rate summers.
6. EOC = fixed positive pulse of a few ms at end of fall; STG = gate for the selected stage; both 0/+5 V.
7. Stage LEDs (sheet 41) driven from a buffered ENV copy, gated by the rise/fall state. The integrator node is never loaded.

Size: about 8 op-amp sections (2 quads), 1 LM13700, 2 LM393, 2 logic ICs, 2 matched pairs, about 80 R, 20 C, 2 trimmers.

### FOLD x2: not capturable now, no topology and no candidate core

Instances: `W2` (FOLD 2), `W1` (FOLD 1).

| Jack key | Panel label | Dir | Signal role | Magnitude LED | Clip LED |
| --- | --- | --- | --- | --- | --- |
| `<inst>.IN` | IN | in | signal input | yes | no |
| `<inst>.FOLD` | FOLD CV | in | fold-amount CV; depth via FOLD+/- pot | yes | no |
| `<inst>.BIAS` | BIAS CV | in | bias/symmetry CV; fixed amount, no attenuator | yes | no |
| `<inst>.OUT` | OUT | out | folded output after LEVEL | no | no |

| Control key | Panel label | Kind | Candidate part | Positions (grid.json) | Function | Interface board (preview mapping) |
| --- | --- | --- | --- | --- | --- | --- |
| `<inst>.FOLD` | FOLD | pot | bourns-ptv09a-4020f-b103 | continuous | manual fold amount | MP |
| `<inst>.FOLD±` | FOLD ± | pot | bourns-ptv09a-4020f-b103 | continuous | FOLD CV depth, bipolar | MP |
| `<inst>.BIAS` | BIAS | pot | bourns-ptv09a-4020f-b103 | continuous | manual bias | MP |
| `<inst>.LEVEL` | LEVEL | pot | bourns-ptv09a-4020f-b103 | continuous | output level | MP |

Handoff `behavior`: "IN -> fold/bias shaping -> level -> OUT. FOLD CV and BIAS CV as drawn."

Handoff `engineering_to_finish`: "FOLD± affects FOLD CV. BIAS CV amount fixed unless a user-approved control is added; no undocumented knob. Define transfer curve, amplitude/offset limit and non-oscillatory behavior."

- LEDs: 3 magnitude (IN, FOLD CV, BIAS CV).
- Candidate core ICs (HANDOFF): TL074 only, by the generic note "General mixers / filters / folders".
- HANDOFF specifies: signal order IN, fold/bias shaping, level, OUT; FOLD+/- acts on FOLD CV; BIAS CV has a fixed amount.
- HANDOFF leaves undefined: transfer curve; number of folds; how fold amount is voltage controlled; amplitude and offset limits; stability.

PROPOSAL default: Serge-lineage series folder behind a pre-gain VCA.

1. One LM13700 OTA as the pre-gain VCA, controlled by FOLD + attenuverted FOLD CV.
2. BIAS + BIAS CV (unity, fixed) summed into the folder input.
3. Four series diode-clamped op-amp folding cells.
4. Output summer, LEVEL pot, output buffer.

Size: about 11 op-amp sections (3 quads), 1 LM13700, about 10 diodes, 65 R, 15 C, 1 trimmer.

### OFFSET x6: capturable after the range decision

Instances: `A01` (OFFSET 1), `A02` (OFFSET 2), `A03` (OFFSET 3), `A04` (OFFSET 4), `A05` (OFFSET 5), `A06` (OFFSET 6).

| Jack key | Panel label | Dir | Signal role | Magnitude LED | Clip LED |
| --- | --- | --- | --- | --- | --- |
| `<inst>.IN` | IN | in | signal to attenuate/invert (DC-coupled) | yes | no |
| `<inst>.OFFSET` | OFFSET | in | additive offset CV input (unity summing per R17 reference) | yes | no |
| `<inst>.OUT` | OUT | out | OUT = gain*IN + manual offset + OFFSET CV | yes | yes |

| Control key | Panel label | Kind | Candidate part | Positions (grid.json) | Function | Interface board (preview mapping) |
| --- | --- | --- | --- | --- | --- | --- |
| `<inst>.ATTEN` | ATTEN ± | pot | bourns-ptv09a-4020f-b103 | continuous | gain -1..+1 (intent) | EP |
| `<inst>.OFFSET` | OFFSET | pot | bourns-ptv09a-4020f-b103 | continuous | manual offset (preview +/-5 V, not final) | EP |

Handoff `behavior`: "OUT = gain * IN + manual offset + OFFSET CV, gain -1..+1 as intent."

Handoff `engineering_to_finish`: "Final offset range and headroom are not guaranteed by preview +/-5 V controls or +/-10 V clip demo. Buffer all outputs and detect overload."

- LEDs: 3 magnitude (IN, OFFSET, OUT) and 1 red clip LED at OUT.
- Candidate core ICs (HANDOFF): none specific; preview allocates one quad per cell.
- HANDOFF specifies: transfer `OUT = g*IN + manual_offset + OFFSET_CV`; gain -1..+1 "as intent"; DC-coupled; OFFSET jack is an input with unity summing (R17 reference); outputs buffered with overload detection.
- HANDOFF leaves undefined: final offset range and headroom ("not guaranteed by preview +/-5 V controls or +/-10 V clip demo"); precision class.

PROPOSAL default: attenuverter, inverting summer (attenuverter output + offset pot + OFFSET CV), inverter. Manual offset +/-5 V. 0.1 % resistors on unity paths so the cell can carry pitch CV.

Size: 3 op-amp sections (1 quad, one spare), about 18 R, 6 C.

### MULT 1:3 x2: capturable now

Instances: `B1` (MULT 1), `B2` (MULT 2).

| Jack key | Panel label | Dir | Signal role | Magnitude LED | Clip LED |
| --- | --- | --- | --- | --- | --- |
| `<inst>.IN` | IN | in | single high-impedance input | yes | no |
| `<inst>.1` | 1 | out | buffered copy 1 | no | no |
| `<inst>.2` | 2 | out | buffered copy 2 | no | no |
| `<inst>.3` | 3 | out | buffered copy 3 | no | no |

Controls: none.

Handoff `behavior`: "One high-impedance input, three individually buffered outputs."

Handoff `engineering_to_finish`: "Two copies of this function only, not four 1:4 MULTs. Precision error/stability/output isolation must be budgeted; output resistor outside feedback gives load error."

- LEDs: 1 magnitude at IN.
- Candidate core ICs (HANDOFF): OPA4197IPWR TSSOP-14 (C2057327); "Two quads reserve the six MULT buffers". Pin map intake exists in `<R>/pin-map-intake.json`.
- HANDOFF specifies: one high-impedance input, three individually buffered outputs, precision error budget, isolation resistor placement matters.
- HANDOFF leaves undefined: input resistance value; isolation resistor value; protection.

PROPOSAL default: one OPA4197 per MULT. Section 1 = input buffer (1 M to ground, series R, clamp). Sections 2-4 = unity followers with the isolation resistor inside the feedback loop.

Size: 4 op-amp sections, about 12 R, 8 C.

### S&H+SLEW x2: capturable now, the only block with values

Instances: `H1` (S&H 1), `H2` (S&H 2).

| Jack key | Panel label | Dir | Signal role | Magnitude LED | Clip LED |
| --- | --- | --- | --- | --- | --- |
| `<inst>.TRIGGER` | TRIGGER | in | positive-edge sample trigger (conditioned into finite acquisition pulse) | yes | no |
| `<inst>.IN` | IN | in | signal to be sampled | yes | no |
| `<inst>.OUT` | OUT | out | held value after post-hold slew (only output; no raw-held jack) | yes | no |

| Control key | Panel label | Kind | Candidate part | Positions (grid.json) | Function | Interface board (preview mapping) |
| --- | --- | --- | --- | --- | --- | --- |
| `<inst>.SAMPLE` | SAMPLE | button | omron-b3f1020 | continuous | manual sample | UT |
| `<inst>.SLEW` | SLEW | pot | bourns-ptv09a-4020f-b504 | continuous | post-hold lag amount, both directions | UP |

Handoff `behavior`: "Condition positive trigger edge into a finite sample pulse; captured target -> separate post-hold lag -> OUT. One SAMPLE button and one SLEW pot per channel."

Handoff `engineering_to_finish`: "No through gate tracking as default, no hidden clock/noise, no slew CV. Hold cap and lag cap different nodes. LF398 leakage/offset and acquisition must be qualified; final OUT LED sees glide."

- LEDs: 3 magnitude (TRIGGER, IN, OUT). The OUT LED sees the slewed output.
- Candidate core ICs (HANDOFF): LF398M/NOPB SOIC-14 x2 (LCSC C1346172); CD74HC221M96 SOIC-16 x1 (C133954); LM393DR SOIC-8 x1 (C67470); OPA4197IPWR x1 for four buffers. Alternative, not fitted: TMUX6111PWR.

HANDOFF values (all status PROPOSED):

| Item | Value | Source |
| --- | --- | --- |
| Hold capacitor | 10 nF C0G 0805, KEMET C0805C103J5GACTU (C2167597); test alternative 100 nF | `slew-circuit-proposal.json`, candidates |
| Rmin | 2.2 k, 1 % | `slew-calculations.json` |
| SLEW pot | 500 k linear, PTV09A-4020F-B504 (C5154140), +/-20 %, wired as rheostat with wiper shorted to the far end | proposal, D08 |
| C_SLEW | 0.5 uF = 5 x 100 nF C0G 1206, FH 1206CG104J500NT (C46348), +/-5 % | proposal |
| Buffers | unity pre-buffer and post-buffer, OPA4197 | proposal |
| Rails | -12 V, +12 V | proposal |
| tau | 1.1 ms to 251.1 ms nominal; corner at maximum 191 ms to 316 ms | calculations |
| 10-90 % time | 2.42 ms to 552 ms | calculations |
| 5 V step to 10 mV | 6.8 ms to 1.56 s | calculations |
| Acquisition pulse | 50-100 us, test range only | `osc-sample-hold-slew.mdx` |
| Hold droop at 10 nF | 3 mV/s typical, 20 mV/s at the 25 C maximum | calculations |
| Peak current into RC | 7.27 mA for a 16 V step | calculations |

Signal chain (HANDOFF): `IN -> LF398 + C_HOLD -> RAW_HELD -> pre-buffer -> Rmin + rheostat -> C_SLEW -> post-buffer -> OUT`; `TRIGGER -> conditioner -> bounded acquisition pulse -> LF398 logic`.

- HANDOFF leaves undefined: trigger threshold and hysteresis values; one-shot R and C; SAMPLE button debounce and ORing; LF398 logic-reference wiring and offset trim; IN buffer; output isolation; which knob direction is slower.

PROPOSAL default: capture exactly as proposed. Add an IN buffer, the standard trigger comparator, a button debounce RC into the second one-shot trigger input, a footprint for the alternative 100 nF hold cap, and a guard ring around both storage nodes.

Size per channel: 3 op-amp sections, 1 LF398M, half a CD74HC221, half an LM393, about 25 R, 15 C.

### MANUAL A/B x2: capturable now

Instances: `X1` (SWITCH 1), `X2` (SWITCH 2).

| Jack key | Panel label | Dir | Signal role | Magnitude LED | Clip LED |
| --- | --- | --- | --- | --- | --- |
| `<inst>.IN-A` | IN-A | in | selector input A | yes | no |
| `<inst>.IN-B` | IN-B | in | selector input B | yes | no |
| `<inst>.OUT` | OUT | out | selected signal | yes | no |

| Control key | Panel label | Kind | Candidate part | Positions (grid.json) | Function | Interface board (preview mapping) |
| --- | --- | --- | --- | --- | --- | --- |
| `<inst>.SELECT` | A / B | switch | dailywell-2ms1 | A/B | maintained A/B select | US |

Handoff `behavior`: "Manual maintained A/B selector with IN-A, IN-B, OUT."

Handoff `engineering_to_finish`: "Not a crossfader, sequential switch or clocked switch. Prevent output-output shorts during possible contact overlap; buffer/protect. Clicks are possible."

- LEDs: 3 magnitude (IN-A, IN-B, OUT).
- Switch default (HANDOFF test): A.
- Candidate core ICs (HANDOFF): TL074; "A/B planning uses two input buffers and an output buffer per cell". Preview allocates one quad per cell.
- HANDOFF specifies: manual maintained selector; buffer and protect; no source-to-source short during contact overlap; clicks are accepted.
- HANDOFF leaves undefined: values only.

PROPOSAL default: each input buffered, 1 k series to the toggle contacts, toggle common to an output buffer with a 1 M bias resistor so the node never floats mid-throw.

Size: 3 op-amp sections (1 quad), about 12 R, 5 C.

### NOISE x1: partly capturable, shaping filters undefined

Instances: `N1` (Noise).

| Jack key | Panel label | Dir | Signal role | Magnitude LED | Clip LED |
| --- | --- | --- | --- | --- | --- |
| `<inst>.WHITE` | WHITE | out | white noise | no | no |
| `<inst>.PINK` | PINK | out | pink noise | no | no |
| `<inst>.BLUE` | BLUE | out | blue noise (finite-band shaping) | no | no |
| `<inst>.BROWN` | BROWN | out | brown noise (finite-band shaping) | no | no |

Controls: none.

Handoff `behavior`: "White, pink, blue, brown, separately buffered outputs from shared source basis."

Handoff `engineering_to_finish`: "NOISE2 is a programmed digital pseudo-random source candidate. Four colors are not independent random generators. Blue/brown shaping is finite-band; no stability/DC/runaway claims."

- LEDs: none.
- Candidate core IC (HANDOFF): Electric Druid NOISE2, "Programmed PDIP device", no JLC code, quantity 1.
- HANDOFF specifies: white and pink from the programmed source; blue and brown by "proposed band-limited analogue shaping"; each output buffered; the four colours are not independent sources.
- HANDOFF leaves undefined: every filter value; output levels; supply for the 5 V device; through-hole vs socket assembly.

PROPOSAL default: NOISE2 application circuit on a filtered +5 V, reconstruction filter and gain to +/-5 V for white and pink, brown = leaky integrator from white, blue = band-limited differentiator from pink, four output buffers.

Size: about 6 op-amp sections (2 quads), 1 NOISE2, about 30 R, 20 C.

## Capture readiness: 3 yes, 3 after the level standard, 1 partly, 4 no

| Module | Capturable now? | Blocking decisions |
| --- | --- | --- |
| OSC | No | FM type, RANGE mechanism, tune spans, output levels, calibration owner, reference sharing (G03) |
| FILTER/VCA | No | GAIN/RES path freeze (G06), filter order, CV laws |
| MIX5 | After the level standard | summing gain, clip threshold |
| MIX4+VCA | After the level standard | VCA law and maximum gain |
| AR | No | SIG semantics, timing range, CV law, EOC form, levels (G07) |
| FOLD | No | topology, fold count, control law |
| OFFSET | After the level standard | offset range, precision class |
| MULT 1:3 | Yes | input and isolation resistor values |
| S&H+SLEW | Yes | trigger threshold, one-shot RC, debounce |
| MANUAL A/B | Yes | values only |
| NOISE | Partly | shaping filter values, output level |
| Indicators (sheet 70) | After the level standard | detector topology, LED current, where the drivers live |

## Cross-cutting circuits the module list hides

### Indicators are about 30 % of all op-amp sections

- 92 magnitude LEDs + 12 stage + 10 clip = 114 LEDs (HANDOFF). The power page says "104 white ... ten clip".
- PROPOSAL default per magnitude LED: one op-amp section with the LED inside a diode bridge in its feedback path, so LED current = |Vin| / R. High-impedance tap, no loading of the monitored node.
- That is 92 op-amp sections = 23 quad packages for LEDs alone.
- The LEDs sit beside the jacks. If their drivers live on K, about 92 extra lines cross the J-to-K connector. PROPOSAL: put magnitude drivers on the rear of board J; `board-contracts.json` allows J to carry "input/output circuitry as appropriate".

### 99 B103 pots need individual value decisions

HANDOFF: "Circuit capture must assign every original value/taper rather than buying 101 x B103."

| Electrical role of pot | Count | Members |
| --- | --- | --- |
| Bipolar attenuverter (signal/CV path) | 47 | OSC FM+/-, PWM+/-; VCF FREQ+/-, RES+/-, GAIN+/-; MIX5 1-5+/-; MIX4 1-4+/-, CV+/-; FOLD FOLD+/-; AO ATTEN+/- |
| DC control-voltage source | 48 | OSC TUNE, FINE, PW; VCF FREQ, RES, GAIN; MIX4 SUM GAIN; FOLD FOLD, BIAS; AR RISE, FALL; AO OFFSET |
| Signal level attenuator | 4 | MIX5 LEVEL; FOLD LEVEL |
| Rheostat in RC lag (B504) | 2 | S&H SLEW |
| **Total continuous pots** | **101** | matches handoff count 101 |

A 10 k attenuverter pot wired directly to a jack gives about 10 k input impedance. PROPOSAL: use the 100 k member of the same PTV09A-4020F family for the 47 attenuverters (availability UNVERIFIED), keep 10 k for the 48 DC-source pots fed from buffered +/-5 V references.

### Board-crossing signal count is large

Rough count if K holds all circuits: 180 jack signals + 101 pot wipers + about 40 toggle lines + 8 buttons + octave taps + LED lines + power. That is over 350 contacts, before returns. G09 is therefore a first-order design problem, not a detail.

## Size estimate: about 320 op-amp sections, 150 ICs, 3,700 SMD placements

All numbers in this section are PROPOSAL-based planning estimates, accuracy about +/-30 %. HANDOFF explicitly says the 47 preview rectangles are "an area estimate" and must not be used for counts.

| Module | Qty | Op-amp sections / inst | Quad packages / inst | Other ICs / inst | R / inst | C / inst (signal, excl. decoupling) | Diodes / inst | Transistors / inst | Trimmers / inst |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OSC | 5 | 9 | 3 (TL074) | 1 x AS3340D, 0.5 x LM393 | 75 | 22 | 6 | 4 | 4 |
| FILTER/VCA | 3 | 12 | 3 (TL074) | 2 x LM13700 | 85 | 22 | 6 | 5 | 3 |
| MIX5 | 2 | 7 | 2 (TL074) | - | 36 | 10 | 0 | 0 | 0 |
| MIX4+VCA | 2 | 8 | 2 (TL074) | 1 x LM13700 | 46 | 12 | 2 | 1 | 1 |
| AR (ENV) | 6 | 8 | 2 (TL074) | 1 x LM13700, 2 x LM393, 2 x logic (4013/4011 class) | 80 | 20 | 8 | 8 | 2 |
| FOLD | 2 | 11 | 3 (TL074) | 1 x LM13700 | 65 | 15 | 10 | 1 | 1 |
| OFFSET (AO) | 6 | 3 | 1 (TL074) | - | 18 | 6 | 0 | 0 | 0 |
| MULT 1:3 | 2 | 4 | 1 (OPA4197) | - | 12 | 8 | 2 | 0 | 0 |
| S&H+SLEW | 2 | 3 | 1 (OPA4197 x0.5 + TL072-class x0.5) | 1 x LF398M, 0.5 x CD74HC221, 0.5 x LM393 | 25 | 15 | 4 | 0 | 1 |
| MANUAL A/B (SWITCH) | 2 | 3 | 1 (TL074) | - | 12 | 5 | 0 | 0 | 0 |
| NOISE | 1 | 6 | 2 (TL074) | 1 x NOISE2 (programmed) | 30 | 20 | 0 | 0 | 0 |
| **Signal-path subtotal** | 33 | **225** | **64** | see totals | **1640** | **482** | **132** | **87** | **47** |
| Magnitude LED driver | 92 | 1 | 0.25 | - | 2 | 0 | 2 | 0 | 0 |
| Clip LED detector | 10 | 0 | 0 | 1 x LM393 | 6 | 1 | 0 | 1 | 0 |
| Stage LED driver | 12 | 0.5 | 0.125 | - | 3 | 0 | 0 | 2 | 0 |
| **Instrument total** | | **323** | **89** | see totals | **1920** | **492** | **316** | **121** | **47** |

| Item | Planning number | Basis |
| --- | --- | --- |
| Op-amp sections | 323 | 225 signal path + 98 indicators |
| Quad op-amp packages | 89 | 64 signal path + 24.5 indicator |
| AS3340D | 5 | summed from per-module table, rounded up |
| LM393 | 26 | summed from per-module table, rounded up |
| LM13700 | 16 | summed from per-module table, rounded up |
| logic (4013/4011 class) | 12 | summed from per-module table, rounded up |
| LF398M | 2 | summed from per-module table, rounded up |
| CD74HC221 | 1 | summed from per-module table, rounded up |
| NOISE2 (programmed) | 1 | summed from per-module table, rounded up |
| All ICs | about 152 | quads + other ICs; references/regulators add 3-6 more |
| Resistors | about 2110 | 1920 in table + roughly 10 % for references, ladders, pull-ups |
| Capacitors | about 860 | 492 signal + 370 decoupling/bulk (2 per IC + 2 bulk per block) |
| Diodes (dual/single packages) | about 366 | 316 in table + about 50 input clamp pairs |
| Transistors | about 121 | per-module table |
| Trimmers | about 47 | per-module table |
| LEDs | 114 | 92 magnitude + 12 stage + 10 clip (handoff count) |
| SMD placements, all boards | about 3700 | sum of the rows above |
| THT/panel parts | 324 + connectors | 180 jacks, 101 pots, 30 toggles, 5 rotary, 8 buttons |

Comparison with the preview: `core-allocations.json` has 47 package rectangles. The estimate above is about 150 ICs. The preview under-represents the real circuit by roughly a factor of three.

Board area: about 3,700 SMD placements need roughly 450-600 cm2 of single-side placement area at moderate density. The panel is 31.8 x 29.8 cm = 948 cm2. It fits only with double-sided assembly and with circuitry distributed across K and the rear of J.

### Rail current: the -12 V rail is the tight one

| Load | Count | mA each, +12 V | mA each, -12 V | +12 V total mA | -12 V total mA | Note |
| --- | --- | --- | --- | --- | --- | --- |
| TL074-class signal quads | 60 | 5.6 | 5.6 | 336 | 336 | 1.4 mA/amp typical; 2.5 mA/amp max gives 600 mA |
| OPA4197 quads | 3 | 4 | 4 | 12 | 12 | about 1 mA/amp typical |
| Indicator quads (low-power TL064-class proposed) | 25 | 0.8 | 0.8 | 20 | 20 | would be 140 mA if TL074 were used |
| LM13700 | 16 | 4 | 4 | 64 | 64 | supply plus bias currents, estimate |
| AS3340D | 5 | 6 | 8 | 30 | 40 | negative rail through series resistor; verify against retained datasheet |
| LM393 | 26 | 0.6 | 0.1 | 16 | 3 | mostly positive rail / 5 V domain |
| LF398M | 2 | 4.5 | 4.5 | 9 | 9 | typical |
| DC-source pots (48 x 10 k across +/-5 V refs) | 48 | 1 | 1 | 48 | 48 | 2.4 mA each if placed directly across +/-12 V |
| Expo converters, references, ladders | 1 | 25 | 25 | 25 | 25 | lump estimate |
| Magnitude LEDs at 25 % average of 1 mA full scale | 92 | 0.25 | 0.25 | 23 | 23 | worst case 92 mA on one rail |
| Stage + clip LEDs | 1 | 10 | 2 | 10 | 2 | 12 x 0.5 mA average + 10 x 2 mA peak, positive rail |
| **Typical total** | | | | **593** | **582** | excludes output load and shorted-output current |

- Against zudo-pd Board B ratings (+12 V / 1.2 A, -12 V / 0.8 A, +5 V / 0.5 A): +12 V is at about 50 %, -12 V at about 73 % typical.
- With TL074 maximum supply current the -12 V rail reaches about 850 mA, above the 0.8 A rating.
- +5 V load is small: one-shot, comparator pull-ups, NOISE2, AR logic, under 50 mA.
- PROPOSAL: choose a lower-current quad for non-audio CV paths and for all indicators, and budget from the captured circuit as HANDOFF requires.

## G03, G06, G07, G08 block capture; G01, G02, G12 add layout blocks; four block release only

"Blocks capture" means a sheet cannot be completed without the decision. Drafting can still start.

| Issue | Domain | Blocks schematic capture | Blocks PCB layout | Blocks manufacturing release | Note |
| --- | --- | --- | --- | --- | --- |
| G01 Jack / nut / panel stack | MECHANICAL | No | Yes (board J plane, jack footprint) | Yes | needs a physical fit coupon |
| G02 OCT / pots / toggle / buttons | MECHANICAL | No | Yes (all interface boards) | Yes | needs real part measurements |
| G03 Complete one oscillator | ELECTRICAL | Yes (sheets 10, 11) | Yes (K) | Yes | design decisions, then bench |
| G04 S&H capture and hold accuracy | ELECTRICAL | No | No (use dual cap footprint) | Yes | bench characterization |
| G05 SLEW range and hot leakage | ELECTRICAL | No | No | Yes | bench characterization |
| G06 VCF dry path / gain topology | ELECTRICAL | Yes (sheet 20) | Yes (K) | Yes | one owner decision closes the capture part |
| G07 AR electrical semantics | ELECTRICAL | Yes (sheets 40, 41) | Yes (K) | Yes | truth table needed first |
| G08 Protection / loading / output shorting | ELECTRICAL | Yes (every sheet with a jack) | Yes | Yes | closed for capture by adopting one I/O standard cell |
| G09 Connectors and local circuits | MECH/ELEC | Partly (sheet 80, board partition) | Yes | Yes | defines which sheet lives on which board |
| G10 Exact zudo-pd integration | POWER | Partly (sheet 01 only) | Partly (power pocket, connector) | Yes | also blocks first energization |
| G11 Factory assembly and final integration | MANUFACTURING | No | No | Yes | influences part choice (THT NOISE2, trimmers) |
| G12 Native KiCad authority | CAD/RELEASE | No (it is the work itself) | Yes (pin-to-pad maps come first) | Yes | closed by doing the capture and layout |
| G13 Promote real evidence | DOCUMENTATION | No | Partly (pin maps need retained datasheets) | Yes | zudo-circuit-doc evidence workflow |
| G14 Output monitoring connection | PRODUCT | No | No | No (blocks bench test planning only) | no new module is added |

Summary: capture blockers are G03, G06, G07, G08 and part of G09/G10. Layout blockers add G01, G02, G12 and part of G13. G04, G05, G11, G14 block only release or test.

## Ten handoff defects or gaps found; coordinate formula verified

| Finding | Evidence | Effect on the plan |
| --- | --- | --- |
| `placements-review.csv` is stale | 322 rows; `C:H1.SLEW` and `C:H2.SLEW` missing | use `grid.json` + formula, never the CSV |
| Coordinate formula verified | x = 14.5 + 17 x col; jack y = 29 + 14 x row; control y = 185 + 14 x row; 0 mismatches over 322 rows | safe to generate footprints from cells |
| Switch positions absent from `block-contracts.json` | present only in `grid.json` `positions` | schematic generator must read both files |
| Library name is the old project name | `kicad-sheet-plan.json` `library: zudo_osc_playground` | rename to the new project name |
| Power board naming and TVS part unverifiable | see the zudo-pd section above | resolve before sheet 01 |
| Preview IC allocation is about one third of the real count | 47 rectangles vs about 150 ICs | do not size boards from the preview |
| One LM13700 per filter cannot do VC resonance + VCA + two integrators | topology arithmetic | plan 2 per filter |
| RANGE toggle is on a different board from the timing capacitor | `three.js` mapping + sensitive-node rule | RANGE must switch a control voltage |
| No S&H block page | `<D>/architecture` has 10 `osc-block-*.mdx`; S&H is covered by `osc-sample-hold-slew.mdx` | none, noted for doc migration |
| Three parts have no JLC/LCSC code | AS3340D, NOISE2, 2MS3T1B1M2QES | external procurement or consignment |
| `ngspice` and `kicad-cli` not on PATH in this WSL session | `which` returned nothing | simulation and native ERC/DRC need a tool decision; UNVERIFIED beyond PATH |

## Appendix A: 180 jacks, 98 in and 82 out

Centre coordinates use the verified compact-preset formula. They are pre-CAD review positions, not qualified footprints.

| Jack id | Family | Label | Dir | Cell (col,row) 0-based | Centre mm (x,y) compact 17x14 | Mag LED | Clip LED |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `O1.1V` | OSC | 1V/OCT | in | 0,0 | 14.5, 29.0 | - | - |
| `O1.FM` | OSC | FM | in | 0,1 | 14.5, 43.0 | - | - |
| `O1.PWM` | OSC | PWM | in | 0,2 | 14.5, 57.0 | - | - |
| `O1.SYNC` | OSC | SYNC CV | in | 0,3 | 14.5, 71.0 | - | - |
| `O1.SIN` | OSC | SIN | out | 0,4 | 14.5, 85.0 | - | - |
| `O1.TRI` | OSC | TRI | out | 0,5 | 14.5, 99.0 | - | - |
| `O1.SAW` | OSC | SAW | out | 0,6 | 14.5, 113.0 | - | - |
| `O1.PUL` | OSC | PUL | out | 0,7 | 14.5, 127.0 | - | - |
| `O2.1V` | OSC | 1V/OCT | in | 1,0 | 31.5, 29.0 | - | - |
| `O2.FM` | OSC | FM | in | 1,1 | 31.5, 43.0 | - | - |
| `O2.PWM` | OSC | PWM | in | 1,2 | 31.5, 57.0 | - | - |
| `O2.SYNC` | OSC | SYNC CV | in | 1,3 | 31.5, 71.0 | - | - |
| `O2.SIN` | OSC | SIN | out | 1,4 | 31.5, 85.0 | - | - |
| `O2.TRI` | OSC | TRI | out | 1,5 | 31.5, 99.0 | - | - |
| `O2.SAW` | OSC | SAW | out | 1,6 | 31.5, 113.0 | - | - |
| `O2.PUL` | OSC | PUL | out | 1,7 | 31.5, 127.0 | - | - |
| `O3.1V` | OSC | 1V/OCT | in | 2,0 | 48.5, 29.0 | - | - |
| `O3.FM` | OSC | FM | in | 2,1 | 48.5, 43.0 | - | - |
| `O3.PWM` | OSC | PWM | in | 2,2 | 48.5, 57.0 | - | - |
| `O3.SYNC` | OSC | SYNC CV | in | 2,3 | 48.5, 71.0 | - | - |
| `O3.SIN` | OSC | SIN | out | 2,4 | 48.5, 85.0 | - | - |
| `O3.TRI` | OSC | TRI | out | 2,5 | 48.5, 99.0 | - | - |
| `O3.SAW` | OSC | SAW | out | 2,6 | 48.5, 113.0 | - | - |
| `O3.PUL` | OSC | PUL | out | 2,7 | 48.5, 127.0 | - | - |
| `O4.1V` | OSC | 1V/OCT | in | 3,0 | 65.5, 29.0 | - | - |
| `O4.FM` | OSC | FM | in | 3,1 | 65.5, 43.0 | - | - |
| `O4.PWM` | OSC | PWM | in | 3,2 | 65.5, 57.0 | - | - |
| `O4.SYNC` | OSC | SYNC CV | in | 3,3 | 65.5, 71.0 | - | - |
| `O4.SIN` | OSC | SIN | out | 3,4 | 65.5, 85.0 | - | - |
| `O4.TRI` | OSC | TRI | out | 3,5 | 65.5, 99.0 | - | - |
| `O4.SAW` | OSC | SAW | out | 3,6 | 65.5, 113.0 | - | - |
| `O4.PUL` | OSC | PUL | out | 3,7 | 65.5, 127.0 | - | - |
| `O5.1V` | OSC | 1V/OCT | in | 4,0 | 82.5, 29.0 | - | - |
| `O5.FM` | OSC | FM | in | 4,1 | 82.5, 43.0 | - | - |
| `O5.PWM` | OSC | PWM | in | 4,2 | 82.5, 57.0 | - | - |
| `O5.SYNC` | OSC | SYNC CV | in | 4,3 | 82.5, 71.0 | - | - |
| `O5.SIN` | OSC | SIN | out | 4,4 | 82.5, 85.0 | - | - |
| `O5.TRI` | OSC | TRI | out | 4,5 | 82.5, 99.0 | - | - |
| `O5.SAW` | OSC | SAW | out | 4,6 | 82.5, 113.0 | - | - |
| `O5.PUL` | OSC | PUL | out | 4,7 | 82.5, 127.0 | - | - |
| `F1.IN` | VCF | IN | in | 5,0 | 99.5, 29.0 | Y | - |
| `F1.FREQ` | VCF | FREQ CV | in | 5,1 | 99.5, 43.0 | Y | - |
| `F1.RES` | VCF | RES CV | in | 5,2 | 99.5, 57.0 | Y | - |
| `F1.GAIN` | VCF | GAIN CV | in | 5,3 | 99.5, 71.0 | Y | - |
| `F1.LP` | VCF | LP | out | 5,4 | 99.5, 85.0 | - | - |
| `F1.BP` | VCF | BP | out | 5,5 | 99.5, 99.0 | - | - |
| `F1.HP` | VCF | HP | out | 5,6 | 99.5, 113.0 | - | - |
| `F1.OUT` | VCF | OUT | out | 5,7 | 99.5, 127.0 | - | - |
| `F2.IN` | VCF | IN | in | 6,0 | 116.5, 29.0 | Y | - |
| `F2.FREQ` | VCF | FREQ CV | in | 6,1 | 116.5, 43.0 | Y | - |
| `F2.RES` | VCF | RES CV | in | 6,2 | 116.5, 57.0 | Y | - |
| `F2.GAIN` | VCF | GAIN CV | in | 6,3 | 116.5, 71.0 | Y | - |
| `F2.LP` | VCF | LP | out | 6,4 | 116.5, 85.0 | - | - |
| `F2.BP` | VCF | BP | out | 6,5 | 116.5, 99.0 | - | - |
| `F2.HP` | VCF | HP | out | 6,6 | 116.5, 113.0 | - | - |
| `F2.OUT` | VCF | OUT | out | 6,7 | 116.5, 127.0 | - | - |
| `F3.IN` | VCF | IN | in | 7,0 | 133.5, 29.0 | Y | - |
| `F3.FREQ` | VCF | FREQ CV | in | 7,1 | 133.5, 43.0 | Y | - |
| `F3.RES` | VCF | RES CV | in | 7,2 | 133.5, 57.0 | Y | - |
| `F3.GAIN` | VCF | GAIN CV | in | 7,3 | 133.5, 71.0 | Y | - |
| `F3.LP` | VCF | LP | out | 7,4 | 133.5, 85.0 | - | - |
| `F3.BP` | VCF | BP | out | 7,5 | 133.5, 99.0 | - | - |
| `F3.HP` | VCF | HP | out | 7,6 | 133.5, 113.0 | - | - |
| `F3.OUT` | VCF | OUT | out | 7,7 | 133.5, 127.0 | - | - |
| `M5A.1` | MIX5 | 1 | in | 8,0 | 150.5, 29.0 | Y | - |
| `M5A.2` | MIX5 | 2 | in | 8,1 | 150.5, 43.0 | Y | - |
| `M5A.3` | MIX5 | 3 | in | 8,2 | 150.5, 57.0 | Y | - |
| `M5A.4` | MIX5 | 4 | in | 8,3 | 150.5, 71.0 | Y | - |
| `M5A.5` | MIX5 | 5 | in | 8,4 | 150.5, 85.0 | Y | - |
| `M5A.SUM` | MIX5 | SUM | out | 8,5 | 150.5, 99.0 | Y | Y |
| `M5B.1` | MIX5 | 1 | in | 9,0 | 167.5, 29.0 | Y | - |
| `M5B.2` | MIX5 | 2 | in | 9,1 | 167.5, 43.0 | Y | - |
| `M5B.3` | MIX5 | 3 | in | 9,2 | 167.5, 57.0 | Y | - |
| `M5B.4` | MIX5 | 4 | in | 9,3 | 167.5, 71.0 | Y | - |
| `M5B.5` | MIX5 | 5 | in | 9,4 | 167.5, 85.0 | Y | - |
| `M5B.SUM` | MIX5 | SUM | out | 9,5 | 167.5, 99.0 | Y | Y |
| `M4A.1` | MIX4 | 1 | in | 10,0 | 184.5, 29.0 | Y | - |
| `M4A.2` | MIX4 | 2 | in | 10,1 | 184.5, 43.0 | Y | - |
| `M4A.3` | MIX4 | 3 | in | 10,2 | 184.5, 57.0 | Y | - |
| `M4A.4` | MIX4 | 4 | in | 10,3 | 184.5, 71.0 | Y | - |
| `M4A.ATTEN` | MIX4 | ATTEN | in | 10,4 | 184.5, 85.0 | Y | - |
| `M4A.SUM` | MIX4 | SUM | out | 10,5 | 184.5, 99.0 | Y | Y |
| `M4B.1` | MIX4 | 1 | in | 11,0 | 201.5, 29.0 | Y | - |
| `M4B.2` | MIX4 | 2 | in | 11,1 | 201.5, 43.0 | Y | - |
| `M4B.3` | MIX4 | 3 | in | 11,2 | 201.5, 57.0 | Y | - |
| `M4B.4` | MIX4 | 4 | in | 11,3 | 201.5, 71.0 | Y | - |
| `M4B.ATTEN` | MIX4 | ATTEN | in | 11,4 | 201.5, 85.0 | Y | - |
| `M4B.SUM` | MIX4 | SUM | out | 11,5 | 201.5, 99.0 | Y | Y |
| `W2.IN` | FOLD | IN | in | 8,6 | 150.5, 113.0 | Y | - |
| `W2.FOLD` | FOLD | FOLD CV | in | 9,6 | 167.5, 113.0 | Y | - |
| `W2.BIAS` | FOLD | BIAS CV | in | 8,7 | 150.5, 127.0 | Y | - |
| `W2.OUT` | FOLD | OUT | out | 9,7 | 167.5, 127.0 | - | - |
| `W1.IN` | FOLD | IN | in | 10,6 | 184.5, 113.0 | Y | - |
| `W1.FOLD` | FOLD | FOLD CV | in | 11,6 | 201.5, 113.0 | Y | - |
| `W1.BIAS` | FOLD | BIAS CV | in | 10,7 | 184.5, 127.0 | Y | - |
| `W1.OUT` | FOLD | OUT | out | 11,7 | 201.5, 127.0 | - | - |
| `E1.SIG` | AR | SIG | in | 12,0 | 218.5, 29.0 | Y | - |
| `E1.RISE` | AR | RISE | in | 12,1 | 218.5, 43.0 | Y | - |
| `E1.FALL` | AR | FALL | in | 12,2 | 218.5, 57.0 | Y | - |
| `E1.ENV` | AR | ENV | out | 12,3 | 218.5, 71.0 | - | - |
| `E1.BIP` | AR | BIP | out | 12,4 | 218.5, 85.0 | - | - |
| `E1.EOC` | AR | EOC | out | 12,5 | 218.5, 99.0 | - | - |
| `E1.STG` | AR | STG | out | 12,6 | 218.5, 113.0 | - | - |
| `A01.IN` | AO | IN | in | 12,7 | 218.5, 127.0 | Y | - |
| `A01.OFFSET` | AO | OFFSET | in | 12,8 | 218.5, 141.0 | Y | - |
| `A01.OUT` | AO | OUT | out | 12,9 | 218.5, 155.0 | Y | Y |
| `E2.SIG` | AR | SIG | in | 13,0 | 235.5, 29.0 | Y | - |
| `E2.RISE` | AR | RISE | in | 13,1 | 235.5, 43.0 | Y | - |
| `E2.FALL` | AR | FALL | in | 13,2 | 235.5, 57.0 | Y | - |
| `E2.ENV` | AR | ENV | out | 13,3 | 235.5, 71.0 | - | - |
| `E2.BIP` | AR | BIP | out | 13,4 | 235.5, 85.0 | - | - |
| `E2.EOC` | AR | EOC | out | 13,5 | 235.5, 99.0 | - | - |
| `E2.STG` | AR | STG | out | 13,6 | 235.5, 113.0 | - | - |
| `A02.IN` | AO | IN | in | 13,7 | 235.5, 127.0 | Y | - |
| `A02.OFFSET` | AO | OFFSET | in | 13,8 | 235.5, 141.0 | Y | - |
| `A02.OUT` | AO | OUT | out | 13,9 | 235.5, 155.0 | Y | Y |
| `E3.SIG` | AR | SIG | in | 14,0 | 252.5, 29.0 | Y | - |
| `E3.RISE` | AR | RISE | in | 14,1 | 252.5, 43.0 | Y | - |
| `E3.FALL` | AR | FALL | in | 14,2 | 252.5, 57.0 | Y | - |
| `E3.ENV` | AR | ENV | out | 14,3 | 252.5, 71.0 | - | - |
| `E3.BIP` | AR | BIP | out | 14,4 | 252.5, 85.0 | - | - |
| `E3.EOC` | AR | EOC | out | 14,5 | 252.5, 99.0 | - | - |
| `E3.STG` | AR | STG | out | 14,6 | 252.5, 113.0 | - | - |
| `A03.IN` | AO | IN | in | 14,7 | 252.5, 127.0 | Y | - |
| `A03.OFFSET` | AO | OFFSET | in | 14,8 | 252.5, 141.0 | Y | - |
| `A03.OUT` | AO | OUT | out | 14,9 | 252.5, 155.0 | Y | Y |
| `E4.SIG` | AR | SIG | in | 15,0 | 269.5, 29.0 | Y | - |
| `E4.RISE` | AR | RISE | in | 15,1 | 269.5, 43.0 | Y | - |
| `E4.FALL` | AR | FALL | in | 15,2 | 269.5, 57.0 | Y | - |
| `E4.ENV` | AR | ENV | out | 15,3 | 269.5, 71.0 | - | - |
| `E4.BIP` | AR | BIP | out | 15,4 | 269.5, 85.0 | - | - |
| `E4.EOC` | AR | EOC | out | 15,5 | 269.5, 99.0 | - | - |
| `E4.STG` | AR | STG | out | 15,6 | 269.5, 113.0 | - | - |
| `A04.IN` | AO | IN | in | 15,7 | 269.5, 127.0 | Y | - |
| `A04.OFFSET` | AO | OFFSET | in | 15,8 | 269.5, 141.0 | Y | - |
| `A04.OUT` | AO | OUT | out | 15,9 | 269.5, 155.0 | Y | Y |
| `E5.SIG` | AR | SIG | in | 16,0 | 286.5, 29.0 | Y | - |
| `E5.RISE` | AR | RISE | in | 16,1 | 286.5, 43.0 | Y | - |
| `E5.FALL` | AR | FALL | in | 16,2 | 286.5, 57.0 | Y | - |
| `E5.ENV` | AR | ENV | out | 16,3 | 286.5, 71.0 | - | - |
| `E5.BIP` | AR | BIP | out | 16,4 | 286.5, 85.0 | - | - |
| `E5.EOC` | AR | EOC | out | 16,5 | 286.5, 99.0 | - | - |
| `E5.STG` | AR | STG | out | 16,6 | 286.5, 113.0 | - | - |
| `A05.IN` | AO | IN | in | 16,7 | 286.5, 127.0 | Y | - |
| `A05.OFFSET` | AO | OFFSET | in | 16,8 | 286.5, 141.0 | Y | - |
| `A05.OUT` | AO | OUT | out | 16,9 | 286.5, 155.0 | Y | Y |
| `E6.SIG` | AR | SIG | in | 17,0 | 303.5, 29.0 | Y | - |
| `E6.RISE` | AR | RISE | in | 17,1 | 303.5, 43.0 | Y | - |
| `E6.FALL` | AR | FALL | in | 17,2 | 303.5, 57.0 | Y | - |
| `E6.ENV` | AR | ENV | out | 17,3 | 303.5, 71.0 | - | - |
| `E6.BIP` | AR | BIP | out | 17,4 | 303.5, 85.0 | - | - |
| `E6.EOC` | AR | EOC | out | 17,5 | 303.5, 99.0 | - | - |
| `E6.STG` | AR | STG | out | 17,6 | 303.5, 113.0 | - | - |
| `A06.IN` | AO | IN | in | 17,7 | 303.5, 127.0 | Y | - |
| `A06.OFFSET` | AO | OFFSET | in | 17,8 | 303.5, 141.0 | Y | - |
| `A06.OUT` | AO | OUT | out | 17,9 | 303.5, 155.0 | Y | Y |
| `B1.IN` | MULT | IN | in | 0,8 | 14.5, 141.0 | Y | - |
| `B1.1` | MULT | 1 | out | 1,8 | 31.5, 141.0 | - | - |
| `B1.2` | MULT | 2 | out | 0,9 | 14.5, 155.0 | - | - |
| `B1.3` | MULT | 3 | out | 1,9 | 31.5, 155.0 | - | - |
| `B2.IN` | MULT | IN | in | 2,8 | 48.5, 141.0 | Y | - |
| `B2.1` | MULT | 1 | out | 3,8 | 65.5, 141.0 | - | - |
| `B2.2` | MULT | 2 | out | 2,9 | 48.5, 155.0 | - | - |
| `B2.3` | MULT | 3 | out | 3,9 | 65.5, 155.0 | - | - |
| `H1.TRIGGER` | SH | TRIGGER | in | 4,8 | 82.5, 141.0 | Y | - |
| `H1.IN` | SH | IN | in | 5,8 | 99.5, 141.0 | Y | - |
| `H1.OUT` | SH | OUT | out | 6,8 | 116.5, 141.0 | Y | - |
| `X1.IN-A` | SWITCH | IN-A | in | 7,8 | 133.5, 141.0 | Y | - |
| `X1.IN-B` | SWITCH | IN-B | in | 8,8 | 150.5, 141.0 | Y | - |
| `X1.OUT` | SWITCH | OUT | out | 9,8 | 167.5, 141.0 | Y | - |
| `H2.TRIGGER` | SH | TRIGGER | in | 4,9 | 82.5, 155.0 | Y | - |
| `H2.IN` | SH | IN | in | 5,9 | 99.5, 155.0 | Y | - |
| `H2.OUT` | SH | OUT | out | 6,9 | 116.5, 155.0 | Y | - |
| `X2.IN-A` | SWITCH | IN-A | in | 7,9 | 133.5, 155.0 | Y | - |
| `X2.IN-B` | SWITCH | IN-B | in | 8,9 | 150.5, 155.0 | Y | - |
| `X2.OUT` | SWITCH | OUT | out | 9,9 | 167.5, 155.0 | Y | - |
| `N1.WHITE` | NOISE | WHITE | out | 10,8 | 184.5, 141.0 | - | - |
| `N1.PINK` | NOISE | PINK | out | 11,8 | 201.5, 141.0 | - | - |
| `N1.BLUE` | NOISE | BLUE | out | 10,9 | 184.5, 155.0 | - | - |
| `N1.BROWN` | NOISE | BROWN | out | 11,9 | 201.5, 155.0 | - | - |

## Appendix B: 144 controls, 101 pots, 30 toggles, 5 rotary, 8 buttons

| Control id | Family | Label | Kind | Part | Positions | Cell (col,row) 0-based | Centre mm (x,y) | Board |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `O1.OCT` | OSC | OCT | octave | alps-srbv160803 | -2/-1/0/1/2/3 | 0,0 | 14.5, 185.0 | O |
| `O1.VCO/LFO` | OSC | RANGE | switch | dailywell-2ms1 | LFO/VCO | 0,1 | 14.5, 199.0 | OS |
| `O1.SYNC` | OSC | SYNC | switch | dailywell-2ms3 | SOFT/OFF/HARD | 0,2 | 14.5, 213.0 | OS |
| `O1.TUNE` | OSC | TUNE | pot | bourns-ptv09a-4020f-b103 | - | 0,3 | 14.5, 227.0 | OP |
| `O1.FINE` | OSC | FINE | pot | bourns-ptv09a-4020f-b103 | - | 0,4 | 14.5, 241.0 | OP |
| `O1.FM±` | OSC | FM ± | pot | bourns-ptv09a-4020f-b103 | - | 0,5 | 14.5, 255.0 | OP |
| `O1.PW` | OSC | PW | pot | bourns-ptv09a-4020f-b103 | - | 0,6 | 14.5, 269.0 | OP |
| `O1.PWM±` | OSC | PWM ± | pot | bourns-ptv09a-4020f-b103 | - | 0,7 | 14.5, 283.0 | OP |
| `O2.OCT` | OSC | OCT | octave | alps-srbv160803 | -2/-1/0/1/2/3 | 1,0 | 31.5, 185.0 | O |
| `O2.VCO/LFO` | OSC | RANGE | switch | dailywell-2ms1 | LFO/VCO | 1,1 | 31.5, 199.0 | OS |
| `O2.SYNC` | OSC | SYNC | switch | dailywell-2ms3 | SOFT/OFF/HARD | 1,2 | 31.5, 213.0 | OS |
| `O2.TUNE` | OSC | TUNE | pot | bourns-ptv09a-4020f-b103 | - | 1,3 | 31.5, 227.0 | OP |
| `O2.FINE` | OSC | FINE | pot | bourns-ptv09a-4020f-b103 | - | 1,4 | 31.5, 241.0 | OP |
| `O2.FM±` | OSC | FM ± | pot | bourns-ptv09a-4020f-b103 | - | 1,5 | 31.5, 255.0 | OP |
| `O2.PW` | OSC | PW | pot | bourns-ptv09a-4020f-b103 | - | 1,6 | 31.5, 269.0 | OP |
| `O2.PWM±` | OSC | PWM ± | pot | bourns-ptv09a-4020f-b103 | - | 1,7 | 31.5, 283.0 | OP |
| `O3.OCT` | OSC | OCT | octave | alps-srbv160803 | -2/-1/0/1/2/3 | 2,0 | 48.5, 185.0 | O |
| `O3.VCO/LFO` | OSC | RANGE | switch | dailywell-2ms1 | LFO/VCO | 2,1 | 48.5, 199.0 | OS |
| `O3.SYNC` | OSC | SYNC | switch | dailywell-2ms3 | SOFT/OFF/HARD | 2,2 | 48.5, 213.0 | OS |
| `O3.TUNE` | OSC | TUNE | pot | bourns-ptv09a-4020f-b103 | - | 2,3 | 48.5, 227.0 | OP |
| `O3.FINE` | OSC | FINE | pot | bourns-ptv09a-4020f-b103 | - | 2,4 | 48.5, 241.0 | OP |
| `O3.FM±` | OSC | FM ± | pot | bourns-ptv09a-4020f-b103 | - | 2,5 | 48.5, 255.0 | OP |
| `O3.PW` | OSC | PW | pot | bourns-ptv09a-4020f-b103 | - | 2,6 | 48.5, 269.0 | OP |
| `O3.PWM±` | OSC | PWM ± | pot | bourns-ptv09a-4020f-b103 | - | 2,7 | 48.5, 283.0 | OP |
| `O4.OCT` | OSC | OCT | octave | alps-srbv160803 | -2/-1/0/1/2/3 | 3,0 | 65.5, 185.0 | O |
| `O4.VCO/LFO` | OSC | RANGE | switch | dailywell-2ms1 | LFO/VCO | 3,1 | 65.5, 199.0 | OS |
| `O4.SYNC` | OSC | SYNC | switch | dailywell-2ms3 | SOFT/OFF/HARD | 3,2 | 65.5, 213.0 | OS |
| `O4.TUNE` | OSC | TUNE | pot | bourns-ptv09a-4020f-b103 | - | 3,3 | 65.5, 227.0 | OP |
| `O4.FINE` | OSC | FINE | pot | bourns-ptv09a-4020f-b103 | - | 3,4 | 65.5, 241.0 | OP |
| `O4.FM±` | OSC | FM ± | pot | bourns-ptv09a-4020f-b103 | - | 3,5 | 65.5, 255.0 | OP |
| `O4.PW` | OSC | PW | pot | bourns-ptv09a-4020f-b103 | - | 3,6 | 65.5, 269.0 | OP |
| `O4.PWM±` | OSC | PWM ± | pot | bourns-ptv09a-4020f-b103 | - | 3,7 | 65.5, 283.0 | OP |
| `O5.OCT` | OSC | OCT | octave | alps-srbv160803 | -2/-1/0/1/2/3 | 4,0 | 82.5, 185.0 | O |
| `O5.VCO/LFO` | OSC | RANGE | switch | dailywell-2ms1 | LFO/VCO | 4,1 | 82.5, 199.0 | OS |
| `O5.SYNC` | OSC | SYNC | switch | dailywell-2ms3 | SOFT/OFF/HARD | 4,2 | 82.5, 213.0 | OS |
| `O5.TUNE` | OSC | TUNE | pot | bourns-ptv09a-4020f-b103 | - | 4,3 | 82.5, 227.0 | OP |
| `O5.FINE` | OSC | FINE | pot | bourns-ptv09a-4020f-b103 | - | 4,4 | 82.5, 241.0 | OP |
| `O5.FM±` | OSC | FM ± | pot | bourns-ptv09a-4020f-b103 | - | 4,5 | 82.5, 255.0 | OP |
| `O5.PW` | OSC | PW | pot | bourns-ptv09a-4020f-b103 | - | 4,6 | 82.5, 269.0 | OP |
| `O5.PWM±` | OSC | PWM ± | pot | bourns-ptv09a-4020f-b103 | - | 4,7 | 82.5, 283.0 | OP |
| `F1.FREQ` | VCF | FREQ | pot | bourns-ptv09a-4020f-b103 | - | 5,0 | 99.5, 185.0 | MP |
| `F1.RES` | VCF | RES | pot | bourns-ptv09a-4020f-b103 | - | 5,1 | 99.5, 199.0 | MP |
| `F1.FREQ±` | VCF | FREQ± | pot | bourns-ptv09a-4020f-b103 | - | 5,2 | 99.5, 213.0 | MP |
| `F1.RES±` | VCF | RES± | pot | bourns-ptv09a-4020f-b103 | - | 5,3 | 99.5, 227.0 | MP |
| `F1.GAIN` | VCF | GAIN | pot | bourns-ptv09a-4020f-b103 | - | 5,4 | 99.5, 241.0 | MP |
| `F1.GAIN±` | VCF | GAIN± | pot | bourns-ptv09a-4020f-b103 | - | 5,5 | 99.5, 255.0 | MP |
| `F2.FREQ` | VCF | FREQ | pot | bourns-ptv09a-4020f-b103 | - | 6,0 | 116.5, 185.0 | MP |
| `F2.RES` | VCF | RES | pot | bourns-ptv09a-4020f-b103 | - | 6,1 | 116.5, 199.0 | MP |
| `F2.FREQ±` | VCF | FREQ± | pot | bourns-ptv09a-4020f-b103 | - | 6,2 | 116.5, 213.0 | MP |
| `F2.RES±` | VCF | RES± | pot | bourns-ptv09a-4020f-b103 | - | 6,3 | 116.5, 227.0 | MP |
| `F2.GAIN` | VCF | GAIN | pot | bourns-ptv09a-4020f-b103 | - | 6,4 | 116.5, 241.0 | MP |
| `F2.GAIN±` | VCF | GAIN± | pot | bourns-ptv09a-4020f-b103 | - | 6,5 | 116.5, 255.0 | MP |
| `F3.FREQ` | VCF | FREQ | pot | bourns-ptv09a-4020f-b103 | - | 7,0 | 133.5, 185.0 | MP |
| `F3.RES` | VCF | RES | pot | bourns-ptv09a-4020f-b103 | - | 7,1 | 133.5, 199.0 | MP |
| `F3.FREQ±` | VCF | FREQ± | pot | bourns-ptv09a-4020f-b103 | - | 7,2 | 133.5, 213.0 | MP |
| `F3.RES±` | VCF | RES± | pot | bourns-ptv09a-4020f-b103 | - | 7,3 | 133.5, 227.0 | MP |
| `F3.GAIN` | VCF | GAIN | pot | bourns-ptv09a-4020f-b103 | - | 7,4 | 133.5, 241.0 | MP |
| `F3.GAIN±` | VCF | GAIN± | pot | bourns-ptv09a-4020f-b103 | - | 7,5 | 133.5, 255.0 | MP |
| `M5A.1±` | MIX5 | 1 ± | pot | bourns-ptv09a-4020f-b103 | - | 8,0 | 150.5, 185.0 | MP |
| `M5A.2±` | MIX5 | 2 ± | pot | bourns-ptv09a-4020f-b103 | - | 8,1 | 150.5, 199.0 | MP |
| `M5A.3±` | MIX5 | 3 ± | pot | bourns-ptv09a-4020f-b103 | - | 8,2 | 150.5, 213.0 | MP |
| `M5A.4±` | MIX5 | 4 ± | pot | bourns-ptv09a-4020f-b103 | - | 8,3 | 150.5, 227.0 | MP |
| `M5A.5±` | MIX5 | 5 ± | pot | bourns-ptv09a-4020f-b103 | - | 8,4 | 150.5, 241.0 | MP |
| `M5A.LEVEL` | MIX5 | LEVEL | pot | bourns-ptv09a-4020f-b103 | - | 8,5 | 150.5, 255.0 | MP |
| `M5B.1±` | MIX5 | 1 ± | pot | bourns-ptv09a-4020f-b103 | - | 9,0 | 167.5, 185.0 | MP |
| `M5B.2±` | MIX5 | 2 ± | pot | bourns-ptv09a-4020f-b103 | - | 9,1 | 167.5, 199.0 | MP |
| `M5B.3±` | MIX5 | 3 ± | pot | bourns-ptv09a-4020f-b103 | - | 9,2 | 167.5, 213.0 | MP |
| `M5B.4±` | MIX5 | 4 ± | pot | bourns-ptv09a-4020f-b103 | - | 9,3 | 167.5, 227.0 | MP |
| `M5B.5±` | MIX5 | 5 ± | pot | bourns-ptv09a-4020f-b103 | - | 9,4 | 167.5, 241.0 | MP |
| `M5B.LEVEL` | MIX5 | LEVEL | pot | bourns-ptv09a-4020f-b103 | - | 9,5 | 167.5, 255.0 | MP |
| `M4A.1±` | MIX4 | 1 ± | pot | bourns-ptv09a-4020f-b103 | - | 10,0 | 184.5, 185.0 | MP |
| `M4A.2±` | MIX4 | 2 ± | pot | bourns-ptv09a-4020f-b103 | - | 10,1 | 184.5, 199.0 | MP |
| `M4A.3±` | MIX4 | 3 ± | pot | bourns-ptv09a-4020f-b103 | - | 10,2 | 184.5, 213.0 | MP |
| `M4A.4±` | MIX4 | 4 ± | pot | bourns-ptv09a-4020f-b103 | - | 10,3 | 184.5, 227.0 | MP |
| `M4A.CV±` | MIX4 | CV ± | pot | bourns-ptv09a-4020f-b103 | - | 10,4 | 184.5, 241.0 | MP |
| `M4A.LEVEL` | MIX4 | SUM GAIN | pot | bourns-ptv09a-4020f-b103 | - | 10,5 | 184.5, 255.0 | MP |
| `M4B.1±` | MIX4 | 1 ± | pot | bourns-ptv09a-4020f-b103 | - | 11,0 | 201.5, 185.0 | MP |
| `M4B.2±` | MIX4 | 2 ± | pot | bourns-ptv09a-4020f-b103 | - | 11,1 | 201.5, 199.0 | MP |
| `M4B.3±` | MIX4 | 3 ± | pot | bourns-ptv09a-4020f-b103 | - | 11,2 | 201.5, 213.0 | MP |
| `M4B.4±` | MIX4 | 4 ± | pot | bourns-ptv09a-4020f-b103 | - | 11,3 | 201.5, 227.0 | MP |
| `M4B.CV±` | MIX4 | CV ± | pot | bourns-ptv09a-4020f-b103 | - | 11,4 | 201.5, 241.0 | MP |
| `M4B.LEVEL` | MIX4 | SUM GAIN | pot | bourns-ptv09a-4020f-b103 | - | 11,5 | 201.5, 255.0 | MP |
| `W2.FOLD` | FOLD | FOLD | pot | bourns-ptv09a-4020f-b103 | - | 8,6 | 150.5, 269.0 | MP |
| `W2.FOLD±` | FOLD | FOLD ± | pot | bourns-ptv09a-4020f-b103 | - | 9,6 | 167.5, 269.0 | MP |
| `W2.BIAS` | FOLD | BIAS | pot | bourns-ptv09a-4020f-b103 | - | 8,7 | 150.5, 283.0 | MP |
| `W2.LEVEL` | FOLD | LEVEL | pot | bourns-ptv09a-4020f-b103 | - | 9,7 | 167.5, 283.0 | MP |
| `W1.FOLD` | FOLD | FOLD | pot | bourns-ptv09a-4020f-b103 | - | 10,6 | 184.5, 269.0 | MP |
| `W1.FOLD±` | FOLD | FOLD ± | pot | bourns-ptv09a-4020f-b103 | - | 11,6 | 201.5, 269.0 | MP |
| `W1.BIAS` | FOLD | BIAS | pot | bourns-ptv09a-4020f-b103 | - | 10,7 | 184.5, 283.0 | MP |
| `W1.LEVEL` | FOLD | LEVEL | pot | bourns-ptv09a-4020f-b103 | - | 11,7 | 201.5, 283.0 | MP |
| `E1.MODE` | AR | MODE | switch | dailywell-2ms3 | ASR/AR/LOOP | 12,0 | 218.5, 185.0 | ES |
| `E1.SHAPE` | AR | SHAPE | switch | dailywell-2ms1 | LINEAR/CURVED | 12,1 | 218.5, 199.0 | ES |
| `E1.STAGE` | AR | STAGE | switch | dailywell-2ms1 | RISE/FALL | 12,2 | 218.5, 213.0 | ES |
| `E1.TRIG` | AR | TRIG | button | omron-b3f1020 | - | 12,3 | 218.5, 227.0 | ET |
| `E1.RISE` | AR | RISE | pot | bourns-ptv09a-4020f-b103 | - | 12,4 | 218.5, 241.0 | EP |
| `E1.FALL` | AR | FALL | pot | bourns-ptv09a-4020f-b103 | - | 12,5 | 218.5, 255.0 | EP |
| `A01.ATTEN` | AO | ATTEN ± | pot | bourns-ptv09a-4020f-b103 | - | 12,6 | 218.5, 269.0 | EP |
| `A01.OFFSET` | AO | OFFSET | pot | bourns-ptv09a-4020f-b103 | - | 12,7 | 218.5, 283.0 | EP |
| `E2.MODE` | AR | MODE | switch | dailywell-2ms3 | ASR/AR/LOOP | 13,0 | 235.5, 185.0 | ES |
| `E2.SHAPE` | AR | SHAPE | switch | dailywell-2ms1 | LINEAR/CURVED | 13,1 | 235.5, 199.0 | ES |
| `E2.STAGE` | AR | STAGE | switch | dailywell-2ms1 | RISE/FALL | 13,2 | 235.5, 213.0 | ES |
| `E2.TRIG` | AR | TRIG | button | omron-b3f1020 | - | 13,3 | 235.5, 227.0 | ET |
| `E2.RISE` | AR | RISE | pot | bourns-ptv09a-4020f-b103 | - | 13,4 | 235.5, 241.0 | EP |
| `E2.FALL` | AR | FALL | pot | bourns-ptv09a-4020f-b103 | - | 13,5 | 235.5, 255.0 | EP |
| `A02.ATTEN` | AO | ATTEN ± | pot | bourns-ptv09a-4020f-b103 | - | 13,6 | 235.5, 269.0 | EP |
| `A02.OFFSET` | AO | OFFSET | pot | bourns-ptv09a-4020f-b103 | - | 13,7 | 235.5, 283.0 | EP |
| `E3.MODE` | AR | MODE | switch | dailywell-2ms3 | ASR/AR/LOOP | 14,0 | 252.5, 185.0 | ES |
| `E3.SHAPE` | AR | SHAPE | switch | dailywell-2ms1 | LINEAR/CURVED | 14,1 | 252.5, 199.0 | ES |
| `E3.STAGE` | AR | STAGE | switch | dailywell-2ms1 | RISE/FALL | 14,2 | 252.5, 213.0 | ES |
| `E3.TRIG` | AR | TRIG | button | omron-b3f1020 | - | 14,3 | 252.5, 227.0 | ET |
| `E3.RISE` | AR | RISE | pot | bourns-ptv09a-4020f-b103 | - | 14,4 | 252.5, 241.0 | EP |
| `E3.FALL` | AR | FALL | pot | bourns-ptv09a-4020f-b103 | - | 14,5 | 252.5, 255.0 | EP |
| `A03.ATTEN` | AO | ATTEN ± | pot | bourns-ptv09a-4020f-b103 | - | 14,6 | 252.5, 269.0 | EP |
| `A03.OFFSET` | AO | OFFSET | pot | bourns-ptv09a-4020f-b103 | - | 14,7 | 252.5, 283.0 | EP |
| `E4.MODE` | AR | MODE | switch | dailywell-2ms3 | ASR/AR/LOOP | 15,0 | 269.5, 185.0 | ES |
| `E4.SHAPE` | AR | SHAPE | switch | dailywell-2ms1 | LINEAR/CURVED | 15,1 | 269.5, 199.0 | ES |
| `E4.STAGE` | AR | STAGE | switch | dailywell-2ms1 | RISE/FALL | 15,2 | 269.5, 213.0 | ES |
| `E4.TRIG` | AR | TRIG | button | omron-b3f1020 | - | 15,3 | 269.5, 227.0 | ET |
| `E4.RISE` | AR | RISE | pot | bourns-ptv09a-4020f-b103 | - | 15,4 | 269.5, 241.0 | EP |
| `E4.FALL` | AR | FALL | pot | bourns-ptv09a-4020f-b103 | - | 15,5 | 269.5, 255.0 | EP |
| `A04.ATTEN` | AO | ATTEN ± | pot | bourns-ptv09a-4020f-b103 | - | 15,6 | 269.5, 269.0 | EP |
| `A04.OFFSET` | AO | OFFSET | pot | bourns-ptv09a-4020f-b103 | - | 15,7 | 269.5, 283.0 | EP |
| `E5.MODE` | AR | MODE | switch | dailywell-2ms3 | ASR/AR/LOOP | 16,0 | 286.5, 185.0 | ES |
| `E5.SHAPE` | AR | SHAPE | switch | dailywell-2ms1 | LINEAR/CURVED | 16,1 | 286.5, 199.0 | ES |
| `E5.STAGE` | AR | STAGE | switch | dailywell-2ms1 | RISE/FALL | 16,2 | 286.5, 213.0 | ES |
| `E5.TRIG` | AR | TRIG | button | omron-b3f1020 | - | 16,3 | 286.5, 227.0 | ET |
| `E5.RISE` | AR | RISE | pot | bourns-ptv09a-4020f-b103 | - | 16,4 | 286.5, 241.0 | EP |
| `E5.FALL` | AR | FALL | pot | bourns-ptv09a-4020f-b103 | - | 16,5 | 286.5, 255.0 | EP |
| `A05.ATTEN` | AO | ATTEN ± | pot | bourns-ptv09a-4020f-b103 | - | 16,6 | 286.5, 269.0 | EP |
| `A05.OFFSET` | AO | OFFSET | pot | bourns-ptv09a-4020f-b103 | - | 16,7 | 286.5, 283.0 | EP |
| `E6.MODE` | AR | MODE | switch | dailywell-2ms3 | ASR/AR/LOOP | 17,0 | 303.5, 185.0 | ES |
| `E6.SHAPE` | AR | SHAPE | switch | dailywell-2ms1 | LINEAR/CURVED | 17,1 | 303.5, 199.0 | ES |
| `E6.STAGE` | AR | STAGE | switch | dailywell-2ms1 | RISE/FALL | 17,2 | 303.5, 213.0 | ES |
| `E6.TRIG` | AR | TRIG | button | omron-b3f1020 | - | 17,3 | 303.5, 227.0 | ET |
| `E6.RISE` | AR | RISE | pot | bourns-ptv09a-4020f-b103 | - | 17,4 | 303.5, 241.0 | EP |
| `E6.FALL` | AR | FALL | pot | bourns-ptv09a-4020f-b103 | - | 17,5 | 303.5, 255.0 | EP |
| `A06.ATTEN` | AO | ATTEN ± | pot | bourns-ptv09a-4020f-b103 | - | 17,6 | 303.5, 269.0 | EP |
| `A06.OFFSET` | AO | OFFSET | pot | bourns-ptv09a-4020f-b103 | - | 17,7 | 303.5, 283.0 | EP |
| `H1.SAMPLE` | SH | SAMPLE | button | omron-b3f1020 | - | 5,6 | 99.5, 269.0 | UT |
| `H1.SLEW` | SH | SLEW | pot | bourns-ptv09a-4020f-b504 | - | 7,6 | 133.5, 269.0 | UP |
| `X1.SELECT` | SWITCH | A / B | switch | dailywell-2ms1 | A/B | 5,7 | 99.5, 283.0 | US |
| `H2.SAMPLE` | SH | SAMPLE | button | omron-b3f1020 | - | 6,6 | 116.5, 269.0 | UT |
| `H2.SLEW` | SH | SLEW | pot | bourns-ptv09a-4020f-b504 | - | 7,7 | 133.5, 283.0 | UP |
| `X2.SELECT` | SWITCH | A / B | switch | dailywell-2ms1 | A/B | 6,7 | 116.5, 283.0 | US |
