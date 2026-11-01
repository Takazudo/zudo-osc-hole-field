# S2b TMUX7412F + TMUX6112 record (ADOPTED 2026-11-01, E15)

**Status: ADOPTED into the canonical specification and schematics on 2026-11-01** (user
decision card 16:07Z, decision **E15** in `project/osc-hole-field/electrical-decisions.json`).
It is not validated and not a manufacturing or order input. Nothing here is a fabrication file.

- **How it was adopted.** Branch `osc-s2b-adoption-prep` applied `patches/source.patch` with a
  3-way merge onto `539ff382`, added the retained PDFs and regenerated the outputs; it was merged
  into the working branch without squash. 288 of the 290 receipt files matched. The two that differ,
  `scripts/checks/s2b_protection_map.py` and `design/readiness/s2b-protection-map.json`, carry the
  canonical `f8e048f3` TMUX6112 definition-1 rows, restated for the SEL hold (PASS at 25 C, UNKNOWN
  below 25 C). The receipt below therefore describes the record as built on `60c7c3ab`, not the
  adopted tree; `verify_record.py --tree` on the adopted tree reports those two files.
- **Count tests.** `test_partition35`, `test_family_reuse` and `test_mult_common_board` (with the
  stage38 `generate.py` counts) are re-baselined for the D_BOOT parts. The stage45/50/54 historical
  bindings stay as recorded FAILs pending the owner's policy review.
- **PCB steps (disposable copies; `adoption/pcb-gate.json`).** The committed osc-core,
  osc-jack-left and osc-jack-right PCBs are unchanged and now FAIL schematic parity against the
  adopted schematic (704 / 548 / 496 issues, capped counts). On synced disposable copies the #293
  zone fill completes (osc-core 649 s, 2277 MiB peak, 900 s budget) and parity is 0, but DRC FAILs
  with 1470 / 1400 / 1396 errors (capped) from swapped footprints under existing copper and new
  parts at their floorplan positions. RB4413 passes the native courtyard and clearance scan; the
  issue189 pilot is BLOCKED by its own netlist guard. Placement and routing of the three boards are
  required before any board gate can pass.

## Revisions

| Phase | Change | Delta |
|---|---|---|
| 18 | Record created | — |
| 19 | RB4413 slot pin; stage38 assertion; independent rebuild | `patches/phase19-delta.patch` |
| 20 | Review corrections: F1/F3/F6/F10 and the usable signal range; SEL hold redesigned; PWM_OFFSET made exact; 15 R-exact role rows; TMUX6112 S/D comment; WQFN pin-1 silk mark; cost section | `patches/phase20-delta.patch` |
| 22 | Pitch linear range `signals.pitch_linear_range_V` = −5…+8 V added as **PROPOSED** option A1, pending the user's answer; the 1V/OCT row is now computed (PASS); VDD − 3 V wording states the 7.8 guarantee at VSS = 0 V; new owner facts for OPA4197 common-mode range, BAT54S reverse current versus temperature and TMUX7412F 7.8 (phase 21 was a desk study with no record change) | `patches/phase22-delta.patch` |
| 24 | BAV199,215 owner bundle (JLCPCB-hosted mirror of BAV199 v.3; its facts are UNSOURCED until a manufacturer-hosted copy is compared). New `precision` variant of `high_impedance_input` fits it on the five 1V/OCT inputs, MULT IN and S&H IN (9 per unit). New `precision_input_clamp` section in the protection map: drift before and after, and the OPA4197 input absolute-maximum reading (phase 23 was a desk study) | `patches/phase24-delta.patch` |
| 25 | Bootstrap clamp `D_BOOT` (BAT54S,215, pins 1 and 2 SENSE, pin 3 BUFFERED) added to the `precision` variant on the same 9 inputs, so SENSE ≤ V+ + 0.27 V at 25 °C also beyond the declared fault range; designator lock +9; protection map gains the bootstrap error and the revised absolute-maximum verdict; pitch linear range −5…+8 V (option A1) is now the user's decision of 2026-11-01 13:41Z (`signals.pitch_linear_range_status`, decision **E14**), no longer PROPOSED | `patches/phase25-delta.patch` |

## Decision

The user chose S2b on the decision card of 2026-11-01 04:59Z. That choice accepts a change of
the protected-switch identity in the electrical standard. It is recorded as decision **E13** in
`project/osc-hole-field/electrical-decisions.json` and as `cells[0].protection_identity_change`
in `design/standard/electrical-standard.json`.

On the decision card of 2026-11-01 13:41Z the user set the 1V/OCT pitch linear range to
−5…+8 V (option A1 of the phase-21 study). It is decision **E14** and
`signals.pitch_linear_range_status` in the standard. It is the linear passing range only;
calibrated accuracy stays limited to `calibration.pitch_tracking_scope`.

## Every changed role

The record is one cumulative change set against predecessor commit
`60c7c3ab78cba5e2fcd81973024894510e090cfb`. It contains all of
`circuit/candidates/opa4197idr-rexact-20261031`.

| Role | Canonical | Candidate | Per unit | Where |
|---|---|---|---:|---|
| Precision op-amp (`precision`) outside the `control` region, and the octave reference | OPA4197IPWR (TSSOP-14) | OPA4197IDR (SOIC-14, `op_precision_d`, C2058532); U102, U202, U3303 and U3403 keep IPWR | 85 IDR + 4 IPWR | `io_partition.py` `precision_package()` |
| R-exact series and rescale roles (15 role rows in `design/readiness/r-exact-candidates.json`; R_REF4_TOP adds no placement) | one E-series resistor | first element keeps its key and slot; `*_SERn` added. Every row is exact except where `nominal_shift_percent` says otherwise; R_PWM_OFFSET is now exact: 1 M + 470 k + 330 k = 1.8 M | +85 (oscillator 13 × 5, envelope 3 × 6, wavefolder 1 × 2) | `oscillator.py`, `envelope.py`, `wavefolder.py`, `scripts/checks/r_exact_candidates.py` |
| Input fault switch (`input_fault_switch`) | ADG5412FBRUZ (TSSOP-16) | TMUX7412FRRPR (WQFN-16 RRP, `fault_switch_tmux`, C2982617), one package per input (ADG-2). Channel 1: S1 pad 1 jack, D1 pad 16, SEL1 pad 15. Channels 2-4 AGND, FF NC, EP AGND | 98 | `cells/_builder.py`, standard |
| Envelope switch | ADG5412FBRUZ | TMUX6112PWR (TSSOP-16, `switch_tmux6112`, C2673384), pin 12 NC, logic 1 = on. Channel tuples land on S1/D1 and on D/S for channels 2-4, as the ADG mapping did (bidirectional, equal off-leakage limits) | 12 | `envelope.py` |
| SEL hold (new, redesigned phase 20) | none | `R_<key>_SELH<n>`: RC0603FR-07100KL 100 kOhm, +5V to SEL. `<key>_SELH<n>_D`: BAT54S,215 clamp, pins 1 and 3 SEL, pin 2 +12V. `<key>_SELH<n>_PD`: BAT54S,215 pull-down, pins 1 and 3 SEL, pin 2 logic output. Diode 1 of each package is shorted | 36 R + 72 D | `envelope.py` `flush_sel_holds()` |
| Rail budget rows (new) | none | `fault_switches_tmux7412f` planning 0.6 / 0.5 mA; `switches_tmux6112` 0.023 / 0.012 mA (125 C maxima) | 98 / 12 | `rail-budget-preliminary.json` |
| Supply-architecture input (+12V minimum continuous) | 1700 mA | 1600 mA (computed by the ledger) | | `supply-architecture-input.json` |
| PD-facing +12V contract | 1700 mA | **unchanged, 1700 mA** (coordinator, phase 19) | | `design/architecture-278/` text untouched |
| JR placement of RB4413 | locality reflow | pinned at the issue189 recorded source slot | | `design/partition/candidate-slot-pins.json` |
| WQFN land | none | `TI_RRP0016A`, plus an F.SilkS pin-1 corner mark (project addition; the courtyard is unchanged) | | `scripts/libgen/build_s2b_switch_assets.py` |
| Input clamp `D` of `high_impedance_input`, variant `precision` (phase 24) | BAT54S,215 | BAV199,215 (SOT-23, `clamp_diode_ll`, C40919), same pin order (1 A1, 2 K2, 3 K1/A2) and same SOT-23 land. Part keys, nets, ordinals and Role attributes are unchanged; only the identity changes. The other 89 inputs keep BAT54S,215 | 9 (oscillator 1V × 5, MULT IN × 2, S&H IN × 2) | standard `cells[high_impedance_input].variants.precision`, `cells/_builder.py`, `oscillator.py`, `mult.py`, `sample_hold.py` |
| Bootstrap clamp `D_BOOT`, variant `precision` (phase 25) | none | BAT54S,215 across the unity follower: pins 1 and 2 on SENSE, pin 3 on BUFFERED (antiparallel pair). Added parts are moved after every existing part (`late_last()`), so all 8427 earlier key-to-designator rows are unchanged; new refs DO1106…DO1506, D3107/D3207, DH117/DH217 | 9 | standard `variants.precision.added_parts`, `cells/_builder.py`, `oscillator.py`, `mult.py`, `sample_hold.py`, `audit_master.py` |

New parts are numbered after every existing part. 8234/8234 canonical key-to-designator rows
are unchanged (and 8427/8427 across phase 25), and the designator lock takes +12, +85, +108 and (phase 25) +9 (`audit_master.py`).

Owner bundles: `.claude/skills/component-ti-opa4197idr/`,
`.claude/skills/component-ti-tmux7412frrpr/`, `.claude/skills/component-ti-tmux6112pwr/` and
(phase 24) `.claude/skills/component-nexperia-bav199-215/`.
Each has its own inventory line, direct-routing case, publication selection, shortlist row,
pin map and CAD receipt. The two TI PDFs (`circuit/sources/ic-library/TMUX7412F.pdf`,
`TMUX6112.pdf`) and the BAV199 mirror copy (`BAV199.pdf`) are retained bytes. Phase 22 adds facts only (no identity change) to the
canonical `.claude/skills/component-ti-opa4197ipwr/` and `.claude/skills/component-nexperia-bat54s-215/`
bundles, from their already retained datasheets.

## Packing: ADG-2, one TMUX7412FRRPR per input

TI SCDS404B section 9.4.2 says only that the faulted input turns off. Section 9.4.3 gives each
switch its own SEL pin, and FF is shared across the four channels. TI does not say that the
other channels keep operating, so F9 is UNKNOWN and quad packing (ADG-3) is not used. ADG-2
costs +$244.90 per unit and +$1124.83 per lot more than ADG-3.

## Cost: priced-line subtotal $1484.33 per unit, $6734.27 per lot

This is a subtotal of priced lines only, not a unit cost. The full breakdown is under `cost` in
`receipts/checks.json`. Prices are the retained JLC 2026-10-31 tiers, and a lot is 5 units.

| Line | Per unit | Per lot |
|---|---:|---:|
| Start: cost-study scenario S2b (ADG-3, TMUX6112 envelope, 89 OPA4197IDR, R-exact) | $1196.19 | $5410.57 |
| TMUX7412FRRPR 98 instead of 36 (ADG-2) | +$244.90 | +$1124.83 |
| Op-amps as fitted: 85 IDR + 4 IPWR instead of 89 IDR | +$40.59 | +$188.05 |
| SEL hold: 36 RC0603FR-07100KL + 72 BAT54S,215 | +$2.12 | +$8.14 |
| PWM_OFFSET exact (820K 17 → 12, plus 470K × 5 and 330K × 5) | +$0.19 | +$0.96 |
| Precision clamp (phase 24): 9 BAV199,215 ($0.0383, 1–99 tier at 9 and 45) replace 9 BAT54S,215 (input clamp line 98 → 89) | +$0.09 | +$0.76 |
| Bootstrap clamp (phase 25): 9 BAT54S,215 (input clamp line 89 → 98) | +$0.25 | +$0.96 |
| **Priced-line subtotal** | **$1484.33** | **$6734.27** |

- Unpriced lines are excluded and remain UNKNOWN: BAS16GW-QX, the jacks, LEDs, switches, AS3340D, NOISE2 and the remaining capacitor groups.
- The review's corrected figure before this phase, $1482.78 per unit and $6728.94 per lot, is reproduced by the first three adjustments plus the phase-18 hold of $1.10 per unit.
- Stock: TMUX7412FRRPR 512 against 490 per lot. BAV199,215 86 068 (2026-11-01) against 45 per lot.

## Fault-row table (E13; generated by `scripts/checks/s2b_protection_map.py`)

| Row | ADG5412F | TMUX7412F | Basis (SCDS404B) | S2b disposition |
|---|---|---|---|---|
| F1 powered, ±12 V on the jack | PASS | PASS | Survival: the device turns off only beyond the supplies by VT (9.3.2.4). Signal passing is a separate condition: VT is 0.7 V typical at 25 C only, RON rises exponentially within 3 V of VDD (9.3.4). VDD − 3 V is guaranteed only at VSS = 0 V (7.8); there is no RON maximum at ±12 V dual supply | Survival unchanged. Signal passing is conditional on the usable range below |
| F2 powered, jack beyond a rail | PASS | PASS | Turns off regardless of logic; ±60 V source, 85 V source-to-supply/drain | Unchanged |
| F3 unpowered, rails 0 V, GND present | PASS | PASS | Sources Hi-Z, ±60 V blocked (9.3.2.2). IS(FA) ±125 uA is **typical only** (no maximum). ID(FA) ±50 nA is a maximum at 85 C | Blocking unchanged. Source-side fault leakage has no guaranteed bound, as for ADG5412F |
| F4 unpowered, rails floating, GND present | PASS | PASS | Hi-Z with 0 V or floating rails; floating leakage typical only | Unchanged |
| F5 GND absent | FAIL | FAIL | A GND reference must always be present (9.3.2.2) | Unchanged; outside the protected envelope |
| F6 one analog rail missing | PASS | **UNKNOWN** | −12 V missing: PASS, VSS = 0 is a specified single supply (7.4, 9.1). +12 V missing: UNKNOWN, VDD = 0 is below the 5 V minimum while UVLO is defined on VDD − VSS = 12 V | Changed to UNKNOWN until bench evidence or a sequencing rule covers it |
| F7 +5 V enable before analog rails | PASS | PASS | Fail-safe logic, switch OFF (9.3.2.3) | Unchanged |
| F8 rail lift by a patched input | PASS | PASS | Powered-off protection prevents back-powering (9.3.2.2, 9.3.2.5) | Unchanged |
| F9 several inputs faulted in one quad | PASS | UNKNOWN | No statement on undisturbed channels; FF shared | Avoided by ADG-2; UNKNOWN for any quad packing |
| F10 drain leakage and RON | PASS | PASS (conditional) | Inside VSS … VDD − 3 V into the 100 k R_PD load. RON 14 ohm / ID(ON) ±2 nA maxima exist in the ±15 V ±10 % table for VS −10…+10 V (7.6); RON 15 ohm / RFLAT 0.5 ohm maxima in the 12 V single-supply table for VS 0…7.8 V (7.8). Neither is a ±12 V dual-supply table | Conditional PASS inside the usable range; UNKNOWN above VDD − 3 V. 1V/OCT checked against the declared pitch range |
| F11 land and pin map | PASS | FAIL | Orderable only as WQFN-16 RRP; TSSOP PW is Preview | Resolved by the RRP0016A land and WQFN pin map |

### Usable signal range and input roles

The usable signal range is VSS … VDD − 3 V, which is **−12 … +9 V at nominal rails**. It comes
from the description in 9.3.4. The VDD − 3 V limit is **guaranteed only with VSS = 0 V**: table 7.8
gives RON ≤ 15 ohm (−40…85 °C) for VS 0…7.8 V at VDD = 12 V ±10 % (10.8…13.2 V). At ±12 V dual
supply it is an extrapolation, not a table condition (owner fact `fact-fault-switch-t-ron-12v-single`).

| Input role | Inputs per unit | Normal swing | Verdict |
|---|---:|---|---|
| Audio: filter IN, MIX4 1-4, MIX5 1-5, FOLD IN, A/B, MULT IN, S&H IN, OFFSET IN | 37 | ±5 V (`audio_nominal_V`) | PASS, 4 V margin |
| Bipolar CV: envelope RISE/FALL, filter FREQ/RES/GAIN, MIX4 ATTEN, OFFSET, oscillator FM/PWM, FOLD/BIAS | 43 | ±5 V (`bipolar_cv_nominal_V`) | PASS, 4 V margin |
| Gate and trigger: envelope SIG, oscillator SYNC, S&H TRIGGER | 13 | 0…5 V project gate level | PASS. External gates above +9 V are UNKNOWN (high-impedance comparator path) |
| Pitch: oscillator 1V/OCT | 5 | −5…+8 V, `signals.pitch_linear_range_V`, **USER DECISION** 2026-11-01 13:41Z (option A1; decision E14) | **PASS** for signal passing, 0.53 V margin: the top is compared with VDD − 3 V = 8.53 V at the required +12 V minimum of 11.53 V (`supply-architecture-input.json`; extrapolated from 7.8). Accuracy is a separate gate; see the clamp-leakage finding below |

## Pitch range and owner facts (phase 22)

The pitch row is computed by `s2b_protection_map.py` from the standard. With no
`pitch_linear_range_V` it returns FLAG; a range whose top exceeds VDD − 3 V at the required +12 V
minimum returns FAIL. If the user picks another option, edit the two `signals` fields and rerun.

| Owner fact (new) | Value | Source |
|---|---|---|
| `fact-op-precision-input-common-mode-range` (IPWR and IDR `-d-` twin) | VCM (V−) − 0.1 V … (V+) + 0.1 V, table header VS ±4…±18 V, 25 °C | SBOS737C 6.7, printed 7 |
| `fact-op-precision-input-stage-transition` (both) | CMRR ≥ 110 dB for VCM < (V+) − 3 V and ≥ 80 dB for VCM > (V+) − 1.5 V (−40…125 °C, VS ±18 V); **no limit** in the transition (V+) − 3 … (V+) − 1.5 V | SBOS737C 6.7 |
| `fact-clamp-diode-reverse-current-temperature` | Fig. 2, typical only: 25 °C about 0.3 µA (1 V) to 1.5–2 µA (30 V); 85 °C about 15–20 µA to about 60 µA; 125 °C about 200–500 µA. The only maximum is 2 µA at 25 V, 25 °C | BAT54S Fig. 2, printed 3/9 |
| `fact-fault-switch-t-ron-12v-single` | RON ≤ 11 / 15 / 18 ohm (25 / 85 / 125 °C), RFLAT ≤ 0.5 ohm, ΔRON ≤ 0.6 ohm (85 °C) for VS 0…7.8 V, VDD 10.8…13.2 V, VSS 0 V | SCDS404B 7.8, printed 13 |

**Finding (phase 22; resolved for the precision inputs in phase 24).** The BAT54S clamp at `SENSE`
has no reverse-current maximum away from 25 °C. Phase 24 below replaces it on the precision inputs.

## Precision input clamp (phase 24; generated by `s2b_protection_map.py`, section `precision_input_clamp`)

The 5 pitch inputs, MULT IN and S&H IN use the `precision` variant of `high_impedance_input`.
In this variant, D is BAV199,215 in place of BAT54S,215. Leakage flows through
R_eff = R_LIMIT + R_PD ∥ (998 Ω source + 14 Ω RON) = 11.0 kΩ. Drift is the maximum of |e(V,T) − e(V,25 °C)|
over the role range and 0…40 °C; cents are at 1 V/oct.

| Role | Per unit | Range | Before: BAT54S, typical only | After: BAV199 bound | After: BAV199 typical |
|---|---:|---|---|---|---|
| Pitch (1V/OCT) | 5 | −5…+8 V (user decision A1, E14) | 13.4 mV = 16.1 c; no guaranteed bound (UNKNOWN) | ≤ 0.128 mV = 0.15 c | 0.0001 mV |
| MULT IN | 2 | ±5 V | 8.3 mV = 9.9 c; UNKNOWN | ≤ 0.128 mV = 0.15 c | 0.0001 mV |
| S&H IN | 2 | ±5 V | 8.3 mV = 9.9 c; UNKNOWN | ≤ 0.128 mV = 0.15 c | 0.0001 mV |

- **How the bound is formed.** The bound is (IR at 40 °C + IR at 25 °C) × R_eff. It uses the
  BAV199 Fig. 4 maximum curve at VR = 75 V: 6.6 nA at 40 °C, a project reading, and 5 nA at 25 °C
  from Table 7.
- **Assumptions behind the bound.** IR does not rise at lower VR, and it does not rise below
  25 °C.
- **Source status.** The source is the JLCPCB-hosted mirror. nexperia.com returned Access Denied,
  and that block was not worked around. The validator therefore keeps every BAV199 fact
  UNSOURCED until a manufacturer-hosted copy is compared.
- **0…70 °C.** The JSON gives these too: before, 134.8 c pitch and 82.0 c MULT/S&H (typical);
  after, ≤ 0.24 c.

**OPA4197 input absolute maximum (SBOS737C 6.1, index 4).** The table has two separate rows:

- common-mode voltage, (V−) − 0.5 V … (V+) + 0.5 V;
- input current, ±10 mA.

No footnote lets the voltage row be exceeded when the current is limited. Section 7.3.7 says the
ESD diodes are intended to stay inactive in normal operation. The VDD…VDD + VT window therefore
cannot pass on the current row alone.

- **Inside the declared contract: PASS for both clamps.** `input_continuous_fault_V` is ±12 V
  and the required load-rail minima are 11.53 V and −11.74 V. The jack can then exceed the local
  rail by at most 0.47 V or 0.26 V. That is within 0.5 V, with 0.03 V margin.
- **Beyond the contract.** Take a source at the supply maximum (12.3 V at the source) against a
  load rail of 11.53 V: the overdrive is 0.77 V. SENSE − V+ is then at most min(VT, VF):
  - BAT54S: ≤ 0.24 V at 0.1 mA, but only at 25 °C.
  - BAV199: no VF maximum below 1 mA, so the result is **UNKNOWN**.
- **Current row: PASS.** The current is ≤ about 70 µA.
- **Built in phase 25: the bootstrap clamp `D_BOOT`.** See the next section.

## Bootstrap clamp D_BOOT (phase 25; same generated section)

D_BOOT is a BAT54S,215 across the unity follower, with pins 1 and 2 on SENSE and pin 3 on
BUFFERED. It is fitted on the same 9 inputs, beside the BAV199 rail clamp.

**Absolute maximum beyond the declared contract: PASS at 25 °C.**

- SENSE − V+ ≤ VF(D_BOOT) + I × ZO ≤ 0.24 + 0.026 = **0.27 V**, a margin of 0.23 V to the
  (V+) + 0.5 V row. The negative side is symmetric.
- **Why the follower output limits at the rail.** Both op-amps state no phase reversal: OPA4197
  SBOS737C 7.3.3 and OPA4196 SBOS869 7.3.3.
- **The current I.** I ≤ 70 µA when the TMUX7412F drain is inside its own Dx ≤ VDD + 0.7 V
  absolute maximum. At that current the BAT54S VF is ≤ 0.24 V (0.1 mA row, 25 °C).
- **ZO.** 375 Ω is a typical figure only.
- **Below 25 °C: UNKNOWN as a guarantee.** The BAT54S has no VF curve or maximum there. A
  general Schottky temperature coefficient of about 1–2 mV/K would use about 0.05 V of the
  margin at 0 °C.

**Added error.** The follower holds the D_BOOT diode voltage at its offset VOS. The diode current
is therefore 2 Is sinh(VOS / Vt), and the error at SENSE is that current × R_eff.

- **This term needs Is.** The phase 24 note that "leakage needs no hot maximum" overstated it:
  the bootstrap reduces the voltage across the diode, not the need for an Is maximum.
- **At 25 °C: bounded.** With Is ≤ 2 µA (Table 7 at 25 V) and |VOS| ≤ 100 µV, the error is
  ≤ 0.171 mV = 0.21 c, a fixed offset that the 25 °C trim removes.
- **Drift 0…40 °C: typical only.** This uses Is = the typical IR at 1 V and |VOS| = 100 µV
  plus the drift maximum (OPA4197 4.5 µV/°C) or the drift typical (OPA4196 0.8 µV/°C). There is
  no hot IR maximum, so the guaranteed drift is UNKNOWN.

| Role | Follower | BAV199 term (bound, unchanged) | D_BOOT drift (typical) | Total |
|---|---|---|---|---|
| Pitch | OPA4197 | ≤ 0.15 c | 0.096 c | 0.25 c |
| MULT IN | OPA4197 | ≤ 0.15 c | 0.096 c | 0.25 c |
| S&H IN | OPA4196 | ≤ 0.15 c | 0.055 c | 0.21 c |

- **The BAV199 term is not degraded.** The D_BOOT current is set by VOS alone and does not
  divert the BAV199 leakage, which still flows through R_eff. The two terms simply add.
- **0…70 °C (typical):** D_BOOT drift is 1.7 c on the OPA4197 inputs and 0.76 c on the OPA4196
  input.
- **NOT RUN:** the fault rows with one rail missing or the follower unpowered, and transient
  conduction while the follower slews.

## SEL hold (phase 20 redesign)

**Why it changed.** In the logic-low state, the old design (a 100 k series feed from the
logic net) let the reverse leakage of the +12V clamp lift SEL. The review found SEL at about
1.1 V at 85 C on typical curves, which is above VIL 0.8 V. The new design takes the series
resistor out of the logic-low path. A BAT54S pull-down sinks SEL into the logic output, and the
100 k pull-up to +5V sets the clamp current when +12V is absent.

**Figures used.**

| Figure | Value | Source |
|---|---|---|
| HC VOL max | 0.1 V at 20 uA; 0.33 V at 4 mA over −40…85 C | SN74HC00/14/74 7.5 |
| BAT54S VF max at 25 C | 240 mV at 0.1 mA; 320 mV at 1 mA | Table 7 |
| BAT54S IR max at 25 C | 2 uA (VR 25 V) | Table 7 |
| Leakage bound for 25…70 C | **50 uA, a project conservative bound, not a manufacturer maximum** | Fig. 2 typical at 85 C (about 35–40 uA at 12–13 V) × the 25 C max/typical ratio of 1.25 |
| TMUX6112 thresholds | VIL 0.8 V, VIH 2.0 V; RPD(IN) 6 MOhm typical | SCDS383F 6.5 |

**Results.**

| Row | Previous (phase 18) | Phase 20 |
|---|---|---|
| Logic low, 25 C | ≤ 0.30 V: PASS | ≤ 0.57 V (0.33 + 0.24 at ≤ 54.5 uA): PASS, 0.23 V margin |
| Logic low, 25…70 C | ≤ 5.1 V with the 50 uA bound (typical 85 C about 1.1 V): **FAIL** | ≤ 0.65 V (0.33 + ≤ 0.32 at ≤ 102.5 uA): PASS, 0.15 V margin. The 25 C VF maximum is used as the bound; typical Fig. 1 shows VF falling with temperature |
| Logic low, 0…25 C | ≤ 0.30 V: PASS | Leakage ≤ 2 uA. The VF rise below 25 C is UNKNOWN (no curve); the 0.23 V margin covers about 9 mV/K |
| Logic high | ≥ 4.2 V at 25 C | ≥ 2 V for RPD(IN) ≥ 84 kOhm; about 4.3 V at 6 MOhm typical |
| +12V absent: SEL ≤ VDD + 0.3 V | ≤ 0.24 V at 25 C: PASS; below 25 C UNKNOWN | ≤ 0.24 V at 25 C (≤ 54.5 uA): PASS; below 25 C UNKNOWN |
| +5V current | none | ≤ 52.5 uA per hold in logic low, ≤ 1.89 mA per unit. This is a passive load and is not in the rail worksheets |

## RB4413 slot pin (phase 19)

- `candidate-slot-pins.json` holds RB4413 at the slot recorded by issue189
  `jr-rb4413-edge-bridge`, (285.34, 42.31, B.Cu), and reserves its pending 0.2 mm translation.
- The JR reflow packs every other part around it.
- Re-recording issue189 would have needed a new native pilot.
- Neighbouring parts moved, so the pilot's clearance result does not transfer. Native
  verification remains required at adoption.
- Phase 29 (decision E15 minimal-move reflow) replaced this file with
  `design/partition/adopted-placement-pins.json`. That file pins every unchanged-footprint
  JL/JR/K package at its pre-adoption (539ff382) slot and keeps the RB4413 reservation.
  Only swapped ICs, with their bypass capacitors, evicted small passives and added parts move.

## Contents

- `patches/source.patch` is the cumulative text diff of the 120 source files from 60c7c3ab.
- `patches/phase19-delta.patch`, `patches/phase20-delta.patch`, `patches/phase22-delta.patch`, `patches/phase24-delta.patch` and `patches/phase25-delta.patch` each hold one revision.
  Applied in order on top of the previous source set, they reproduce the source files exactly.
- `receipts/application-receipt.json` lists all 290 changed files with before and after sha256
  and kind: source, generated, or retained-source (the 2 TI PDFs and the BAV199 mirror copy).
- `receipts/checks.json` holds the step results, the cost section ("priced-line subtotal"),
  the SEL-hold figures and rows, and the open items.
- `tools/reproduce.sh` gives the generation order; it also regenerates the S2b protection map
  and the R-exact table.
- `tools/verify_record.py` checks file identity only.

## Reproduce

```sh
git worktree add --detach <wt> 60c7c3ab78cba5e2fcd81973024894510e090cfb
ln -s <main-repo>/node_modules <wt>/node_modules   # remove before any export
bash circuit/candidates/s2b-tmux-20261101/tools/reproduce.sh <wt> circuit/candidates/s2b-tmux-20261101 <main-repo>
python3 circuit/candidates/s2b-tmux-20261101/tools/verify_record.py --tree <wt>
```

`reproduce.sh` reads the main repository's ignored `.circuit-cache/sources` and checks the
sha256 of the three retained PDFs. It never writes to the main repository.

Run the heavy native steps with the guard outside and the KiCad lock inside:
`bash $HOME/.claude/scripts/heavy-guard.sh -- flock /tmp/kicad-native.lock <cmd>`. The
reverse order can deadlock.

## Known FAILs and NOT RUN

| Check | Result | Cause |
|---|---|---|
| `design/spec` wavefolder `test_model_and_plot_receipts_current` | FAIL | The R-exact spice report changed and the plot receipt cannot be regenerated without matplotlib (not installed) |
| `scripts/checks/test_assembly_specification.py` (stage50) | FAIL (canonical PASS) | Historical binding to the canonical `inventory.json` hash |
| `scripts/checks/test_connectivity_inventory.py` (stage45) | FAIL (canonical PASS) | Historical pad/netlist binding to the canonical part set |
| `scripts/checks/test_power_cleanup.py` (stage54) | 6 F + 3 E (canonical 1 F) | Historical "exact fitted identity U116" binding to OPA4197IPWR |
| `test_mult_copper_plan`, `test_mult_substrate_comparison` | 1 FAIL each, the same test as canonical | Historical determinism and source-hash bindings |
| `test_family_reuse` | 2 FAIL (canonical 1) | Phase 25: frozen MULT jack count 36 (now 37 with D_BOOT) and `proposal.json` determinism |
| `test_mult_common_board` | 3 FAIL (canonical 1) | Phase 25: frozen 36 B1 packages (now 37), `layout.json` determinism, and the hard-coded populated count 37 in stage38 `generate.py` (now 38) |
| `scripts/checks/test_partition35.py` | 1 FAIL (canonical PASS) | Phase 25: frozen JL part count 1060 (now 1069 with 9 D_BOOT). These historical baselines are not re-baselined in the record (policy review at adoption) |
| `scripts/checks/test_architecture_history.py` | PASS with `PYTHONPATH=scripts/checks` | Errors without that path, as canonically |
| `scripts/checks/test_ground_escape.py` | PASS with shapely 2.2.0 (scratch venv); 1 skipped | Large ignored native inputs unavailable |
| DRC, zone fill, #293 fill | NOT RUN | Not authorized |
| Physical fit, WQFN solder and thermal pad, SEL-hold timing and behaviour below 25 C | NOT RUN | NEEDS BENCH |
