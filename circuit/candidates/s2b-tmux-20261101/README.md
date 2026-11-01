# S2b TMUX7412F + TMUX6112 candidate (UNADOPTED, isolated development record)

**Status: UNADOPTED isolated development candidate. Not canonical, not validated, not a
manufacturing or order input.** The canonical specification, schematics, board projects,
partition, BOM and placement lock are unchanged by this directory. Nothing here is a
fabrication file. No DRC, zone fill or #293 fill was run. Canonical adoption needs a
separate approval.

Revision: phase 18 created the record; phase 19 revised it (RB4413 slot pin, stage38
assertion, independent rebuild). `patches/phase19-delta.patch` holds only the phase-19 change.

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
| R-exact series roles (14 roles from `design/readiness/r-exact-candidates.json`) | one E-series resistor | first element keeps its key and slot; `*_SERn` added | +80 (oscillator 12 × 5, envelope 3 × 6, wavefolder 1 × 2) | `oscillator.py`, `envelope.py`, `wavefolder.py` |
| Input fault switch (`input_fault_switch`) | ADG5412FBRUZ (TSSOP-16) | TMUX7412FRRPR (WQFN-16 RRP, `fault_switch_tmux`, C2982617), one package per input (ADG-2). Channel 1: S1 pad 1 jack, D1 pad 16, SEL1 pad 15. Channels 2-4 AGND, FF NC, EP AGND | 98 | `cells/_builder.py`, standard |
| Envelope switch | ADG5412FBRUZ | TMUX6112PWR (TSSOP-16, `switch_tmux6112`, C2673384), pin 12 NC, logic 1 = on | 12 | `envelope.py` |
| SEL hold (new) | none | `R_<key>_SELH<n>`: RC0603FR-07100KL 100 kOhm, from the logic net to the SEL pin; `<key>_SELH<n>_D`: BAT54S,215 (pin 1 AGND, pin 2 +12V, pin 3 SEL) | 36 R + 36 D | `envelope.py` `flush_sel_holds()` |
| Rail budget rows (new) | none | `fault_switches_tmux7412f` planning 0.6 / 0.5 mA; `switches_tmux6112` 0.023 / 0.012 mA (125 C maxima) | 98 / 12 | `rail-budget-preliminary.json` |
| Supply-architecture input (+12V minimum continuous) | 1700 mA | 1600 mA (computed by the ledger) | | `supply-architecture-input.json` |
| PD-facing +12V contract | 1700 mA | **unchanged, 1700 mA** (coordinator, phase 19: the extra margin costs PD nothing) | | `design/architecture-278/` text untouched |
| JR placement of RB4413 | locality reflow | pinned at the issue189 recorded source slot | | `design/partition/candidate-slot-pins.json` |

New parts are numbered after every existing part. 8234/8234 earlier key-to-designator rows
are unchanged, and the designator lock takes +12, +80 and +72 (`audit_master.py`).

Owner bundles: `.claude/skills/component-ti-opa4197idr/`,
`.claude/skills/component-ti-tmux7412frrpr/` and `.claude/skills/component-ti-tmux6112pwr/`.
Each has its own inventory line, direct-routing case, publication selection, shortlist row,
pin map and CAD receipt. The two TI PDFs (`circuit/sources/ic-library/TMUX7412F.pdf`,
`TMUX6112.pdf`) are retained bytes. The WQFN land `TI_RRP0016A`, its WRL envelope and both
symbols come from `scripts/libgen/build_s2b_switch_assets.py`, using drawing 4224816/A:

- 16 pads of 0.6 x 0.3 mm at 0.65 mm pitch on a 3.8 mm span;
- a 2.6 mm thermal pad with 4 x 1.15 mm paste apertures;
- a 0.07 mm NSMD mask;
- a 4.1 x 4.1 x 0.8 mm envelope.

## Packing: ADG-2, one TMUX7412FRRPR per input

TI SCDS404B section 9.4.2 says only that the faulted input turns off. Section 9.4.3 gives each
switch its own SEL pin, and FF is shared across the four channels. TI does not say that the
other channels keep operating, so F9 is UNKNOWN and quad packing (ADG-3) is not used.

The dated JLC 2026-10-31 prices are:

| Basis | Per unit | Per lot |
|---|---:|---:|
| ADG-2 instead of ADG-3 | +$244.90 | +$1124.83 |
| S2b total (ADG-2 + SEL hold) | $1442.19 | $6540.89 |

TMUX7412FRRPR stock is 512 against 490 per lot.

## Fault-row table (E13, source `design/readiness/s2b-protection-map.json`)

| Row | ADG5412F | TMUX7412F | Basis (SCDS404B) | S2b disposition |
|---|---|---|---|---|
| F1 powered, ±12 V on the jack | PASS | PASS | overvoltage only beyond the supplies by VT (index 32, 9.3.2.4) | Unchanged |
| F2 powered, jack beyond a rail | PASS | PASS | turns off regardless of logic; ±60 V source, 85 V source-to-supply/drain (index 31-32) | Unchanged |
| F3 unpowered, rails 0 V, GND present | PASS | PASS | sources Hi-Z; IS(FA) ±125 uA, ID(FA) ±50 nA max at 85 C (7.6) | Unchanged |
| F4 unpowered, rails floating, GND present | PASS | PASS | Hi-Z with 0 V or floating rails; floating leakage typical only | Unchanged |
| F5 GND absent | FAIL | FAIL | same requirement (9.3.2.2) | Unchanged outside the protected envelope |
| F6 one analog rail missing | PASS | PASS | single supply 8-44 V, same rule; conditional | Unchanged |
| F7 +5 V enable before analog rails | PASS | PASS | fail-safe logic, switch OFF (9.3.2.3) | Unchanged |
| F8 rail lift by a patched input | PASS | PASS | powered-off protection prevents back-powering (9.3.2.2, 9.3.2.5) | Unchanged |
| F9 several inputs faulted in one quad | PASS | UNKNOWN | no statement on undisturbed channels; FF shared | Avoided by ADG-2; UNKNOWN for any quad packing |
| F10 drain leakage and RON | PASS | PASS | RON 14 ohm, ID(ON) ±2 nA max at 85 C, ±15 V table; ±12 V not guaranteed | Unchanged |
| F11 land and pin map | PASS | FAIL | orderable only as WQFN-16 RRP; TSSOP PW is Preview | Resolved by the RRP0016A land and WQFN pin map |

## RB4413 slot pin (phase 19)

**The problem.** The SOIC-14 and WQFN-16 reflows of JR packed D4515 and R4507 into the slot
(285.34, 42.31, B.Cu) that the issue189 `jr-rb4413-edge-bridge` pending translation binds to
RB4413. That made the translation source stale.

**Rejected alternatives.**

- The phase-17 RB4413/RB4515 swap no longer restored that slot, and no other same-footprint
  swap does.
- A TSSOP-sized courtyard reservation broke 216 bypass proximity checks.
- Re-recording issue189 would need a new native pilot, which is a CI run outside this
  record's authority.

**The fix.** `candidate-slot-pins.json` makes `partition35_floorplan.py` place RB4413 at the
recorded slot before the JR locality pass. It also reserves the union of the slot and its
pending 0.2 mm translation, and adds RB4413's signal-net position as a locality anchor. The
earlier swap file and its code are removed.

**The result.**

- The floorplan is PASS with 0 errors, and bypass maximum stays at 2.535 mm.
- 153 JR packages move relative to phase 18; nothing moves on other boards.
- JR goes from B.Cu 568 / F.Cu 463 to 567 / 464.
- The pilot's native clearance result does not transfer to the moved neighbours, so native
  verification remains required at adoption.

## Contents

- `patches/source.patch` is the cumulative text diff of the 99 source files from 60c7c3ab.
- `patches/phase19-delta.patch` is the phase-18 record's source changed into this revision.
- `receipts/application-receipt.json` lists all 264 changed files with their before and after
  sha256 and kind: source, generated, or retained-source (the 2 TI PDFs).
- `receipts/checks.json` holds the step results, costs basis and open items.
- `tools/reproduce.sh` gives the generation order.
- `tools/verify_record.py` checks file identity only.

## Reproduce

```sh
git worktree add --detach <wt> 60c7c3ab78cba5e2fcd81973024894510e090cfb
ln -s <main-repo>/node_modules <wt>/node_modules   # remove before any export
bash circuit/candidates/s2b-tmux-20261101/tools/reproduce.sh <wt> circuit/candidates/s2b-tmux-20261101 <main-repo>
python3 circuit/candidates/s2b-tmux-20261101/tools/verify_record.py --tree <wt>
```

`reproduce.sh` reads the main repository's ignored `.circuit-cache/sources` and checks the
sha256 of both TI PDFs. It never writes to the main repository. Run the heavy steps through
the heavy guard and serialize native KiCad with `flock /tmp/kicad-native.lock`.

## Known FAILs and NOT RUN

| Check | Result | Cause |
|---|---|---|
| `design/spec` wavefolder `test_model_and_plot_receipts_current` | FAIL | The R-exact spice report changed and the plot receipt cannot be regenerated without matplotlib (not installed). Same on the predecessor record. |
| `scripts/checks/test_assembly_specification.py` (stage50) | FAIL (canonical PASS) | Historical binding to the canonical `inventory.json` hash. |
| `scripts/checks/test_connectivity_inventory.py` (stage45) | FAIL (canonical PASS) | Historical pad/netlist binding to the canonical part set. |
| `scripts/checks/test_power_cleanup.py` (stage54) | 6 F + 3 E (canonical 1 F) | Historical "exact fitted identity U116" binding to OPA4197IPWR. |
| `test_family_reuse`, `test_mult_copper_plan`, `test_mult_substrate_comparison`, `test_mult_common_board` | 1 FAIL each, the same test as canonical | Historical determinism / source-hash bindings. In the candidate, stage38 layout also differs in `current_report`. |
| `scripts/checks/test_architecture_history.py` | PASS with `PYTHONPATH=scripts/checks` | Errors only when run without that path; the same is true canonically. |
| `scripts/checks/test_ground_escape.py` | PASS with shapely 2.2.0 (scratch venv); 1 skipped | `test_local_export_replay`: large ignored native inputs unavailable. |
| DRC, zone fill, #293 fill | NOT RUN | Not authorized. |
| Physical fit, WQFN solder/thermal pad, SEL-hold timing | NOT RUN | NEEDS BENCH. |
