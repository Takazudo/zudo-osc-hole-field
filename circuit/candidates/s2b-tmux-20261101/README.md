# S2b TMUX7412F + TMUX6112 candidate (UNADOPTED, isolated development record)

**Status: UNADOPTED isolated development candidate. Not canonical, not validated, not a
manufacturing or order input.** The canonical specification, schematics, board projects,
partition, BOM and placement lock are unchanged by this directory. Nothing here is a
fabrication file. No DRC, zone fill or #293 fill was run. Canonical adoption needs a
separate approval.

## Revisions

| Phase | Change | Delta |
|---|---|---|
| 18 | Record created | — |
| 19 | RB4413 slot pin; stage38 assertion; independent rebuild | `patches/phase19-delta.patch` |
| 20 | Review corrections: F1/F3/F6/F10 and the usable signal range; SEL hold redesigned; PWM_OFFSET made exact; 15 R-exact role rows; TMUX6112 S/D comment; WQFN pin-1 silk mark; cost section | `patches/phase20-delta.patch` |

## Decision

The user chose S2b on the decision card of 2026-11-01 04:59Z. That choice accepts a change of
the protected-switch identity in the electrical standard. It is recorded as decision **E13** in
`project/osc-hole-field/electrical-decisions.json` and as `cells[0].protection_identity_change`
in `design/standard/electrical-standard.json`.

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

New parts are numbered after every existing part. 8234/8234 earlier key-to-designator rows
are unchanged, and the designator lock takes +12, +85 and +108 (`audit_master.py`).

Owner bundles: `.claude/skills/component-ti-opa4197idr/`,
`.claude/skills/component-ti-tmux7412frrpr/` and `.claude/skills/component-ti-tmux6112pwr/`.
Each has its own inventory line, direct-routing case, publication selection, shortlist row,
pin map and CAD receipt. The two TI PDFs (`circuit/sources/ic-library/TMUX7412F.pdf`,
`TMUX6112.pdf`) are retained bytes.

## Packing: ADG-2, one TMUX7412FRRPR per input

TI SCDS404B section 9.4.2 says only that the faulted input turns off. Section 9.4.3 gives each
switch its own SEL pin, and FF is shared across the four channels. TI does not say that the
other channels keep operating, so F9 is UNKNOWN and quad packing (ADG-3) is not used. ADG-2
costs +$244.90 per unit and +$1124.83 per lot more than ADG-3.

## Cost: priced-line subtotal $1483.99 per unit, $6732.55 per lot

This is a subtotal of priced lines only, not a unit cost. The full breakdown is under `cost` in
`receipts/checks.json`. Prices are the retained JLC 2026-10-31 tiers, and a lot is 5 units.

| Line | Per unit | Per lot |
|---|---:|---:|
| Start: cost-study scenario S2b (ADG-3, TMUX6112 envelope, 89 OPA4197IDR, R-exact) | $1196.19 | $5410.57 |
| TMUX7412FRRPR 98 instead of 36 (ADG-2) | +$244.90 | +$1124.83 |
| Op-amps as fitted: 85 IDR + 4 IPWR instead of 89 IDR | +$40.59 | +$188.05 |
| SEL hold: 36 RC0603FR-07100KL + 72 BAT54S,215 | +$2.12 | +$8.14 |
| PWM_OFFSET exact (820K 17 → 12, plus 470K × 5 and 330K × 5) | +$0.19 | +$0.96 |
| **Priced-line subtotal** | **$1483.99** | **$6732.55** |

- Unpriced lines are excluded and remain UNKNOWN: BAS16GW-QX, the jacks, LEDs, switches, AS3340D, NOISE2 and the remaining capacitor groups.
- The review's corrected figure before this phase, $1482.78 per unit and $6728.94 per lot, is reproduced by the first three adjustments plus the phase-18 hold of $1.10 per unit.
- Stock: TMUX7412FRRPR 512 against 490 per lot.

## Fault-row table (E13; generated by `scripts/checks/s2b_protection_map.py`)

| Row | ADG5412F | TMUX7412F | Basis (SCDS404B) | S2b disposition |
|---|---|---|---|---|
| F1 powered, ±12 V on the jack | PASS | PASS | Survival: the device turns off only beyond the supplies by VT (9.3.2.4). Signal passing is a separate condition: VT is 0.7 V typical at 25 C only, RON rises exponentially within 3 V of VDD (9.3.4), and there is no RON maximum at ±12 V | Survival unchanged. Signal passing is conditional on the usable range below |
| F2 powered, jack beyond a rail | PASS | PASS | Turns off regardless of logic; ±60 V source, 85 V source-to-supply/drain | Unchanged |
| F3 unpowered, rails 0 V, GND present | PASS | PASS | Sources Hi-Z, ±60 V blocked (9.3.2.2). IS(FA) ±125 uA is **typical only** (no maximum). ID(FA) ±50 nA is a maximum at 85 C | Blocking unchanged. Source-side fault leakage has no guaranteed bound, as for ADG5412F |
| F4 unpowered, rails floating, GND present | PASS | PASS | Hi-Z with 0 V or floating rails; floating leakage typical only | Unchanged |
| F5 GND absent | FAIL | FAIL | A GND reference must always be present (9.3.2.2) | Unchanged; outside the protected envelope |
| F6 one analog rail missing | PASS | **UNKNOWN** | −12 V missing: PASS, VSS = 0 is a specified single supply (7.4, 9.1). +12 V missing: UNKNOWN, VDD = 0 is below the 5 V minimum while UVLO is defined on VDD − VSS = 12 V | Changed to UNKNOWN until bench evidence or a sequencing rule covers it |
| F7 +5 V enable before analog rails | PASS | PASS | Fail-safe logic, switch OFF (9.3.2.3) | Unchanged |
| F8 rail lift by a patched input | PASS | PASS | Powered-off protection prevents back-powering (9.3.2.2, 9.3.2.5) | Unchanged |
| F9 several inputs faulted in one quad | PASS | UNKNOWN | No statement on undisturbed channels; FF shared | Avoided by ADG-2; UNKNOWN for any quad packing |
| F10 drain leakage and RON | PASS | PASS (conditional) | Inside VSS … VDD − 3 V into the 100 k buffer. RON 14 ohm / ID(ON) ±2 nA maxima exist only in the ±15 V ±10 % table for VS −10…+10 V | Conditional PASS inside the usable range; UNKNOWN above VDD − 3 V |
| F11 land and pin map | PASS | FAIL | Orderable only as WQFN-16 RRP; TSSOP PW is Preview | Resolved by the RRP0016A land and WQFN pin map |

### Usable signal range and input roles

The usable signal range is VSS … VDD − 3 V, which is **−12 … +9 V at nominal rails**. It comes
from the typical-curve description in 9.3.4 and is not guaranteed.

| Input role | Inputs per unit | Normal swing | Verdict |
|---|---:|---|---|
| Audio: filter IN, MIX4 1-4, MIX5 1-5, FOLD IN, A/B, MULT IN, S&H IN, OFFSET IN | 37 | ±5 V (`audio_nominal_V`) | PASS, 4 V margin |
| Bipolar CV: envelope RISE/FALL, filter FREQ/RES/GAIN, MIX4 ATTEN, OFFSET, oscillator FM/PWM, FOLD/BIAS | 43 | ±5 V (`bipolar_cv_nominal_V`) | PASS, 4 V margin |
| Gate and trigger: envelope SIG, oscillator SYNC, S&H TRIGGER | 13 | 0…5 V project gate level | PASS. External gates above +9 V are UNKNOWN (high-impedance comparator path) |
| Pitch: oscillator 1V/OCT | 5 | the standard gives 1 V/oct but **no range** | **FLAG**. Sources above +9 V leave the usable range, and above about +12.7 V (VDD + VT typical) the switch opens. A declared pitch range is needed |

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

## Contents

- `patches/source.patch` is the cumulative text diff of the 101 source files from 60c7c3ab.
- `patches/phase19-delta.patch` and `patches/phase20-delta.patch` each hold one revision.
  Applied in order on top of the previous source set, they reproduce the source files exactly.
- `receipts/application-receipt.json` lists all 268 changed files with before and after sha256
  and kind: source, generated, or retained-source (the 2 TI PDFs).
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
sha256 of both TI PDFs. It never writes to the main repository.

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
| `test_family_reuse`, `test_mult_copper_plan`, `test_mult_substrate_comparison`, `test_mult_common_board` | 1 FAIL each, the same test as canonical | Historical determinism and source-hash bindings |
| `scripts/checks/test_architecture_history.py` | PASS with `PYTHONPATH=scripts/checks` | Errors without that path, as canonically |
| `scripts/checks/test_ground_escape.py` | PASS with shapely 2.2.0 (scratch venv); 1 skipped | Large ignored native inputs unavailable |
| DRC, zone fill, #293 fill | NOT RUN | Not authorized |
| Physical fit, WQFN solder and thermal pad, SEL-hold timing and behaviour below 25 C | NOT RUN | NEEDS BENCH |
