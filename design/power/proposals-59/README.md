# Issue #59 OSC-side protection proposals (UNADOPTED)

**UNADOPTED PROPOSAL. Unvalidated draft.** This file selects no part and changes no
schematic, specification, BOM or ledger. Every number is classed as follows:

- **FACT:** an owner-bundle fact, cited by fact id.
- **CALCULATED:** arithmetic on facts.
- **PROPOSED:** a value with no source. It is a starting point, not a pass criterion.

Nothing is measured, simulated or physically checked. Prepared 2026-10-31.

The proposals close three items that the 20 V PD interface contract cannot close from
the supply side ([`pd-interface-20v.md`](../../architecture-278/integration/power-contract/pd-interface-20v.md) §3, §5, §7):

| ID | Problem | Interface rule |
| --- | --- | --- |
| P59-A | VEE5 is not bounded inside the AS3340 VEE limits during the driver interval | R-VEE, R-DRV |
| P59-B | External patch injection into output and sense paths while OSC is off | R-INJ |
| P59-C | ADG5412F IN is high while its supplies are below the specified range | R-ADG |

## P59-A: bound VEE5 during the driver interval

**Problem.** AS3340D VEE–GND must stay within −6 V and +0.5 V
(`fact-vco-absolute-maximum-vee-to-ground`).

- VEE5 comes from one OPA4197 through `VEE_ISO` 100 Ω (`design/spec/modules/oscillator.py`).
- That driver is only in specified operation once its span is at least 4.5 V
  (`fact-op-precision-supply-recommended`) and REF5050 has VIN of at least 5.2 V
  (`fact-reference-input-recommended`).
- Before then, on every common ramp and discharge, the record bounds VEE5 only by A1
  (the driver output stays between its own rails).
- That window is 0.41–4.23 ms of a 10 ms ramp (CALCULATED).

**Sketch.** This is per oscillator, five instances.

```text
 OPA4197 VEE_DRIVER ──R_ISO──┬── VEE5 ── AS3340 pin 3
       ▲                     │
       └──── VEE_FB 10 kΩ ───┤
                             ├──|>|── AGND      D+  (anode VEE5, cathode AGND)
                             └──[CLAMP−]── AGND  negative clamp, ≥ −6 V
```

| Element | Proposal | Evidence status |
| --- | --- | --- |
| D+ positive clamp | One half of BAT54S,215 (already in inventory), anode at VEE5, cathode at AGND | FACT: VF ≤ 400 mV at 10 mA and ≤ 500 mV at 30 mA, 25 °C only (`fact-clamp-diode-forward-voltage`); VR 30 V (`fact-clamp-diode-reverse-voltage`). Reverse leakage of at most 2 µA at 25 V is in the retained PDF (Table 7) but **not promoted**. No temperature coverage |
| R_ISO | Raise from 100 Ω to ≥ 1.21 kΩ, so the clamp current is ≤ 10 mA at the worst +12 V | CALCULATED: (12.48 − 0.40) V / 10 mA = 1.208 kΩ. At 1.21 kΩ the current is ≤ 10.3 mA, inside the ±40 mA AS3340 pin limit (`fact-vco-absolute-maximum-pins`) |
| R_ISO side effect | The loop corrects the DC drop only while the driver has headroom. With swing ignored, the AS3340 VEE load must stay ≤ (12 − 5) V / 1.21 kΩ = 5.79 mA | CALCULATED. The AS3340 VEE pin current is a **missing fact**, so this is a gate |
| CLAMP− | A shunt element that conducts between about −5.3 V and −6 V and never conducts at the −5 V operating point | **UNSOURCED.** No inventory part fits. It needs Workflow B selection with guaranteed tolerance over temperature. The −5 V to −6 V window is narrow |
| Alternative to CLAMP− | Make −12 V alone impossible. That needs a second, OSC-side, supply-independent negative bound; the PD side cannot provide it | Open design question |

**Verification plan.**

1. Run KiCad 10.0.6 ngspice through `scripts/kicad/run.sh`, using the retained TI OPAx197
   PSpice model (`src-op-precision-vendor-model`, library SHA-256 fc5b020e…). The model
   notes do not claim validity below the minimum supply. A low-supply result is
   therefore diagnostic only, and the case is marked NOT RUN as qualification.
2. The BAT54S SPICE model is not retained. Acquire it through Workflow C first; until
   then the clamp result is NOT RUN.
3. Model AS3340 VEE as a swept load of 0–6 mA, because the real pin current is unknown.
4. Cases:
   - tracking ramps at 10, 20 and 50 ms;
   - each one-rail-present case;
   - discharge in both orders.

   Pass criterion: VEE5 stays inside −6 V and +0.5 V at the 25 °C VF bound.
5. Bench: measure VEE5 at each case (#57).

**Phase 9 skew result (2026-10-31).** Two sources:

- **Guaranteed (CALCULATED).** These come from the BAT54S 25 °C VF maxima, A1 and A2 (VF
  monotonic in current). Each value carries conditions P1–P4 in
  `pd-interface-20v.md` §5.
  - +12 V lead: no R-VEE limit. VEE5 ≤ +0.50 V while the clamp current is ≤ 30 mA.
  - The +12 V lead is then limited only by R-ADG: ≤ 6.50 ms with +5 V present.
  - −12 V lead: ≤ 0.69 ms on 10 ms tracking ramps (0.069 × ramp time).
  - No P59-A figure covers temperature.
- **Diagnostic simulation.** `scripts/checks/p59a_skew_model.py` →
  [`p59a-skew-model.json`](p59a-skew-model.json). It ran 64 cases through the pinned
  ngspice and the TI OPAx197 model:
  - grid: skew −1.0 to +4.65 ms; AS3340 VEE load 0 or 6 mA (as a current from +12 V);
    two REF5050 surrogates.
  - The official BAT54S SPICE model is **NOT RETAINED**; Nexperia refused the download
    (HTTP 403). The clamp is therefore an envelope built from the promoted VF maxima. It
    conducts no more than a conforming diode at every voltage, so it can only overstate
    VEE5.

  | Variant | Inside −6 V / +0.5 V | Worst VEE5 |
  | --- | --- | --- |
  | Current 100 Ω, no clamp | 26 / 32 | +0.86 V at +12 V lead ≥ 2.26 ms with a 6 mA load. All 6 failures are +12 V leads ≥ 1 ms at 6 mA |
  | P59-A 1.21 kΩ + clamp envelope | 32 / 32 | max +0.452 V, min −5.14 V |

  What the simulation shows:
  - The model's driver did not itself drive VEE5 positive: the clamp carried 0 mA at a 0 mA
    load. The positive excursion comes from the assumed AS3340 load current.
  - **New conflict.** At a 6 mA load, P59-A settles VEE5 at −4.68 V instead of −5 V. The
    driver saturates through 1.21 kΩ, confirming gate P4 (≤ 5.79 mA). If the real AS3340 VEE
    current exceeds that, R_ISO must be chosen differently (a lower value with a higher
    clamp current rating, or a different clamp topology).

  The TI model makes no validity claim below 4.5 V span, so none of this is qualification.

### P59-A rev 2 (phase 10): the adoption candidate

Rev 1 raised R_ISO to 1.21 kΩ to limit how much the driver could push into the clamp. That
broke regulation at the AS3340 supply current: −4.68 V at 6 mA. Rev 2 instead blocks the
driver from sourcing at all and keeps R_ISO at 100 Ω.

```text
 OPA4197 VEE_DRIVE ──100 Ω──VEE_SINK──|<|── VEE5 ── AS3340 pin 3     D_SINK: BAT54S #1 D1
       ▲                      (K)  (A)  │                           (A = VEE5, K = VEE_SINK; D2 shorted)
       └──── VEE_FB 10 kΩ ──────────────┤
                                        ├──|>|── AGND               D_CLAMP: BAT54S #2 D2
                                        │                           (A = VEE5, K = AGND; D1 shorted)
                                        └──10 kΩ── AGND             R_BLEED keeps D_SINK forward biased
```

The patch is [`patches/p59a-oscillator-vee-clamp.patch`](patches/p59a-oscillator-vee-clamp.patch).
It applies to `design/spec/modules/oscillator.py` and is **not applied**. It adds, for
each of the five oscillators, two BAT54S,215 and one 10 kΩ resistor.

**Guaranteed figures (CALCULATED, 25 °C)**

All facts below were promoted in phase 10 from the retained PDFs, with hashes verified.

- **Driver cannot source into VEE5.** D_SINK is reverse biased by at most
  12.48 + 0.40 = 12.88 V. The leakage is ≤ 2 µA at 25 V (`fact-clamp-diode-reverse-current`).
  This removes the A1 worst case (driver at +12 V) from the positive bound entirely.
- **Positive bound.** The current into D_CLAMP is the AS3340 supply current plus at most
  2 µA, minus what the bleed draws.
  - AS3340 positive supply current: 6.5 mA maximum (`fact-vco-positive-supply-current`).
    This is a typical-table maximum at +15 V with the internal Zener at 20 °C, so it is not
    a guarantee at +12 V / −5 V.
  - At ≤ 10 mA, VEE5 ≤ +0.40 V; at ≤ 30 mA, ≤ +0.50 V (`fact-clamp-diode-forward-voltage`
    and A2). The +0.40 V figure therefore keeps a 3.5 mA margin over the table maximum.
- **Regulation.**
  - At a 7.0 mA sink current (6.5 mA AS3340 plus 0.5 mA bleed) the driver must reach
    −5 − 0.70 − 0.40 = −6.10 V.
  - The −12 V rail is ≥ 11.74 V in magnitude, and the output swing is ≤ 0.5 V from the rail
    at RLOAD = 2 kΩ (`fact-op-precision-output-swing`, 25 °C). The swing row is tested at
    about 5.6 mA, so 7.0 mA is outside its exact condition.
  - That leaves 5.14 V of headroom, so **P4 is retired**.
  - The AS3340 ±40 mA pin limit binds before regulation does.
- **Power.** Each figure is far below its rating:

  | Element | Dissipation | Rating |
  | --- | --- | --- |
  | R_ISO | ≤ 4.9 mW | RT0603BRD 0.1 W at 70 °C, `fact-r-precision-power` |
  | R_BLEED | 2.5 mW | same rating |
  | D_CLAMP | ≤ 4 mW | BAT54S Ptot 250 mW, `fact-clamp-diode-power-thermal` |

  **P3 is retired.**
- **Skew.** The figures are unchanged from phase 9:
  - +12 V lead: no R-VEE limit; R-ADG then limits it to ≤ 6.50 ms with +5 V present.
  - −12 V lead: ≤ 0.69 ms on a 10 ms tracking ramp. With A1 the driver can still sink
    VEE5 toward −12 V.
- **Cost.** The bleed adds 0.5 mA per oscillator, 2.5 mA in total, through the drivers.

**Diagnostic simulation (rev 2).** 47 of 48 cases ran:

- grid: skew −1.0 to +4.65 ms; AS3340 load 0, 6.5 or 10 mA; two REF5050 surrogates;
- result: every case that ran stayed inside −6 V / +0.5 V. Maximum +0.492 V at 10 mA with
  the conservative envelope;
- **settled VEE5 −5.000 V at both 6.5 and 10 mA**, so the conflict is resolved;
- one case (track, 0 mA, +2.26 ms) exceeded the 180 s ngspice limit and is **NOT RUN**.

**Still open**

- **Temperature.** No BAT54S VF maximum exists away from 25 °C. Fig. 1 gives typical curves
  at 25, 85 and 125 °C only, with nothing below 25 °C
  (`fact-clamp-diode-forward-voltage-temperature`). The cold case needs a bench measurement
  or a vendor statement.
- **AS3340 current.** It is known only from a typical table.
- **−12 V-lead limit.** It stays at 0.69 ms unless a negative clamp is added. No inventory
  part fits; a 5.6 V Zener class part would need Workflow B/C evidence.
- **BAT54S model.** The official SPICE model is not retained (HTTP 403).

## P59-B: output and sense injection while OSC is off

**Status.** An earlier proposal already exists and is not selected:
[`osc-protection-architecture.mdx`](../../../doc/src/content/docs/decisions/osc-protection-architecture.mdx)
"Missing rails" / output cell. It is a paired ADG5412F main and sense channel, a 2.74 kΩ
sense resistor on the jack side, and local 10 MΩ ∥ 10 nF feedback. This section re-checks
it against the facts promoted in phase 7.

| Check | Result | Class |
| --- | --- | --- |
| The original 100 Ω sense path, with 12 V external and rails at 0 V | (12 − 0.5) / 100 Ω = 115 mA against the OPA4197 ±10 mA input limit; IN− may sit at most 0.5 V above V+ (`fact-op-precision-input-absolute`) | CALCULATED; exceeds the limit |
| Revised 2.74 kΩ sense path at a 24.48 V differential | 9.02 mA, below 10 mA | CALCULATED (existing record), consistent with the promoted fact |
| Main path through 998 Ω into the D side | 24.78 mA screening. This is below the Dx abs-max limit of 30 mA and the continuous 29 mA at 125 °C (`fact-fault-switch-pin-absolute`, `fact-fault-switch-current-125c`) | CALCULATED; 1.2 mA margin to the abs max |
| Sx (jack side) unpowered | Isolated with the supplies grounded or floating and GND present; Sx is protected to ±55 V (`fact-fault-switch-power-off-ground`, `fact-fault-switch-pin-absolute`) | FACT; leakage while floating is typical only |
| Unmitigated back-feed into +12 V, all 82 outputs forced to 12 V while off | 82 × 12 V / 998 Ω = 0.99 A through the output ESD steering diodes (`fact-op-precision-esd-steering`) | CALCULATED bound on the resistor path; P59-B removes it |
| Bias error of the sense resistor | 15 nA × 2.74 kΩ = 41.1 µV (PW package, full temperature, `fact-op-precision-input-bias-current-full-temperature`) | CALCULATED; inside the 2 mV octave gate |
| Supply cost | At the 1.3 mA normal IDD maximum (`fact-fault-switch-normal-idd`, ±15 V table): 25 / 35 quads = 32.5 / 45.5 mA, above the 20 mA auxiliary allowance | CALCULATED (existing record); the ledger must carry it |

**Verification plan.**

- Reuse `scripts/checks/protection58_model.py`, which runs the TI OPAx197 model with 12
  load and cable cases. Rerun it with the 2.74 kΩ sense resistor and the local feedback.
- There is no ADI switch model, so leakage, enable and fault behaviour stay NOT RUN.
- Unpowered injection cannot be shown with the vendor model; it needs a bench test (#57).

## P59-C: inhibited enables for every ADG5412F

**Problem.**

- IN is tied to +5 V through 1 kΩ with a 100 kΩ pull-down (PCR R2).
- On a common ramp, +5 V crosses the 0.8 V VINL maximum at 15.7 % of the ramp
  (`fact-fault-switch-logic-thresholds`, ±15 V table). The analog rails reach the
  specified ±5 V minimum only at 40.7–41.0 % (`fact-fault-switch-supply-range`).
- An 8 V span can already permit turn-on (`fact-fault-switch-power-off-ground`).

**Proposal.** Replace the +5 V feed of every IN with a common permit, `ENABLE_OK`. Take it
from the existing monitor/permit candidate (`design/power/monitor-permit-draft.json`:
TPS37044 window supervisor, TLV9022 negative network, REF3433, SN74LVC1G17/74), which is
unselected and has native ERC passing with zero warnings. Requirements:

1. `ENABLE_OK` ≤ 0.8 V whenever any rail is outside its load band (11.53 V,
   11.74 V magnitude, 4.81 V). This guarantees IN is low until both analog rails exceed
   the ADG ±5 V minimum. Source: CALCULATED from the load bands and the ADG facts.
2. It defaults low, through a pull-down, when the monitor itself is unpowered. This is
   PROPOSED; the existing 100 kΩ pull-downs remain.
3. Driver load:
   - 110 fitted quads × 5 V / 100 kΩ = 5.5 mA of pull-down current (CALCULATED).
   - 440 IN pins × 0.7 µA typical = 0.31 mA. That figure is typical only and not
     promoted.
   - The SN74LVC1G17 output-current rating is not promoted, so a buffer per board is
     PROPOSED.
4. Distribution: one `ENABLE_OK` per board through the existing harness, with a local
   buffer on each board. Pin and harness allocation is open (#52/#54). This is PROPOSED.

**Verification plan.**

- Extend the existing `scripts/checks/monitor_permit_behavior.py`,
  `monitor_permit_rc.py` and `monitor_permit_native.py` with the IN threshold assertion
  and with 10, 20 and 50 ms tracking ramps, using the retained TPS37044, LVC and TLV
  facts.
- Models for these parts are not retained, so the dynamic results stay NOT RUN until
  they are acquired.
- Bench: confirm ADG channel state for every rail order (#57).

## Phase 10 adoption readiness

I applied each patch to a scratch worktree at 3c6e8ed0, ran the canonical regeneration and
recorded the first failure.

| Proposal | Patch (unapplied) | Regeneration result | Readiness |
| --- | --- | --- | --- |
| P59-A rev 2 | `patches/p59a-oscillator-vee-clamp.patch`: oscillator.py, plus a +15 designator-lock increment in `scripts/schgen/audit_master.py`, following the earlier #60/#61/#62 increments | **PASS** (detail below) | **Ready for a user decision**. Residual items are evidence: AS3340 current from a typical table, cold BAT54S VF, and the −12 V-lead limit |
| P59-B | `patches/p59b-precision-output-isolation.patch`: the `precision_output` cell gains U_MAIN and U_SENSE ADG5412F channels, R_FB 2.74 kΩ on the jack side, R_LOCAL 10 MΩ, C_FAST 10 nF, and R_EN/R_DRIVE | **FAIL** at `build_rail_ledger.py`: "package count mismatch B1 ADG5412FBRUZ: 7 != 1" | **Not ready** (blockers below) |
| P59-C | `patches/p59c-input-enable-permit.patch`: `input_fault_switch` R_DRIVE moved from +5V to ENABLE_OK | **FAIL** at the instrument ERC warning baseline: 259 against 228, with 31 new warnings on the root sheet | **Not ready** (blockers below) |

**P59-A regeneration detail.** Instrument ERC gave 0 errors, and the 228 baseline warning
identities match exactly. Native board ERC gave 0 errors on 10 boards. Cross-board
verification passes. The master audit shows 5921 components (+15) and 438 panel UIDs. The
rail ledger shows 650 IC packages. `regen-master-reports.sh --check` passes.

Adoption needs one extra ordering step, found during the trial. With new parts, `regen-all`
checks against the committed `master-audit.json` before the master-report step rewrites it.
So the order is:

1. Apply the patch.
2. `bash scripts/checks/regen-all.sh`, which stops at the audit drift.
3. Export the master netlist and run `scripts/schgen/audit_master.py <netlist>` to write the
   audit.
4. `bash scripts/schgen/regen-master-reports.sh`.
5. The same command with `--check`.

The new parts are appended last so that every existing designator stays stable. An earlier
mid-list insertion renumbered core parts and split island IO_JACK:O1.

**P59-B blockers.**

- Each new switch channel becomes its own package. Repacking into existing or new quads is
  open, and the module current worksheets and rail ledger need new package counts.
- The ADG supply cost of 32.5–45.5 mA must be charged to the ledger.
- C_FAST 10 nF and R_LOCAL 10 MΩ have no exact identity, because their values differ from
  the shortlist representatives.
- The ADG ±12 V behaviour and leakage while floating remain typical or unspecified.
- The patch also inherits P59-C's enable source problem.

**P59-C blockers.**

- `ENABLE_OK` is unmapped in every module. It becomes a local, undriven cell net, which is
  what produces the new warnings.
- The monitor/permit candidate is not instantiated in the master.
- Harness and pin allocation (#52/#54) is open.
- The SN74LVC1G17 output-current rating is not promoted.

## Phase 11 readiness (P59-B quad packing, P59-C permit block)

Both patches were applied to scratch worktrees at 99d9ff60 and regenerated with the
phase-10 procedure (regen-all, master netlist export, `audit_master.py`, every module
current worksheet, `regen-master-reports.sh`, `--check`).

| Proposal | Patch (unapplied) | First failing gate | Readiness |
| --- | --- | --- | --- |
| P59-B v2 | `patches/p59b-precision-output-isolation.patch` | `partition35_floorplan.py`: **jack locality overflow JR D4602** | **Not ready**: fit conflict plus a contract change |
| P59-C v2 | `patches/p59c-input-enable-permit.patch` | `connector_packing35.py`: jack-board header site list exhausted | **Not ready**: harness allocation needs a floorplan decision |

### P59-B v2

**What the patch does.**

- `precision_output` gets one ADG5412F package: channel 1 for the main path and channel 2
  for the sense path. It also gets R_FB 2.74 kΩ on the jack side, R_LOCAL 10 MΩ,
  C_FAST 10 nF and R_EN/R_DRIVE.
- `general_output` gets one channel.
- `io_partition.refine` packs output-isolation channels into quads per module and board
  region, and removes surplus packages with their bypasses.
- Input fault-switch packages are **not** shared with output channels. No retained fact
  covers how a fault on one channel interacts with the others.
- `protection58.py` accepts the P59-B sense path and counts only the non-output packages
  as existing.
- The patch includes the contract values that the ledger requires (below).

**Package count and supply cost (CALCULATED).**

| Item | Value |
| --- | --- |
| Physical ADG5412F quads | 110 → 147 (+37) |
| Ledger delta, from the module worksheets at the 1.3 / 0.7 mA quad planning unit (`fact-fault-switch-normal-idd`, ±15 V table) | +46.80 mA on +12 V, +25.20 mA on −12 V |
| Two manual_ab core quads | `general_output` is reused there as an internal selector buffer, so P59-B also isolates a non-jack path. That needs its own review |
| +5 V IN drive, not charged by the worksheets | 82 × 5.5 V / (101 kΩ × 0.99) = 4.5 mA. It fits inside the 20 mA auxiliary allowance |

**Against the PD contract (CALCULATED by `build_supply_architecture.py`).**

| Rail | HEAD normal → ×1.1, rounded | P59-B normal → ×1.1, rounded | Transient | PD maximum |
| --- | --- | --- | --- | --- |
| +12 V | 1534.82 → 1700 | 1581.62 → **1800** | 2000 → **2100** | 2100 |
| −12 V | 1435.57 → 1600 | 1460.77 → **1700** | 1900 → **2000** | 2000 |
| +5 V | 224.29 → 300 | 224.29 → 300 | 400 | 500 |

- Before P59-B the +12 V headroom to the 1700 mA step is 10.6 mA of normal load, and the
  −12 V headroom is 19 mA. Every packing of 82 isolated outputs crosses that step.
- P59-B therefore needs continuous 1800 / 1700 mA. Its transient (2100 / 2000) leaves no
  limiter window under the current maximum (2100 / 2000), so the gate
  "limiter has no window above required transient" fails.
- The trial variant sets maximum 2200 / 2100 mA as a PROPOSED value. The return sum is then
  4.8 A, which is still inside the 5 A contact rating check.
- This is a PD contract change, so it is a **user decision** and needs PD agreement.

**Trial results.**

- With that variant, the ledger, `build_supply_architecture.py` and protection58 pass.
  The audit passes with 6201 components and +295 signal designators.
- The trial then stops at `partition35_floorplan.py` with "jack locality overflow JR D4602".
  The added output parts do not fit the JR jack-board locality around the fixed jacks.
  Jacks stay fixed (project rule 1), so this is a **fit conflict**.
- Stale receipts on adoption: the SPICE receipts for envelope, wavefolder and manual_ab hash
  `io_partition.py`, and the panel current audit hashes `_builder.py`. They need model reruns.
  **NOT RUN** in the trial.

### P59-C v2

**What the patch does.**

- `ENABLE_OK` becomes a harness net. `input_fault_switch` R_DRIVE moves from +5V to it.
- `io_partition` renames it per family to `ENABLE_OK_<FAMILY>`.
- The power sheet instantiates the monitor/permit candidate:
  - U101–U106, R101–R121, R125, C101–C110, with VN connected to −12V;
  - the dummy sink Q101 and R122–R124 are removed;
  - ten SN74LVC1G17 branch buffers (A = PERMIT_Q), each with a 100 nF bypass.
- The rail-set unit tests ignore the branch nets.

**Load (CALCULATED).**

- 98 input channels × 5.5 V / (101 kΩ × 0.99) = 5.4 mA.
- The largest branch is the oscillator: 20 channels, 1.10 mA.
- Monitor block: +5 V 6.7 mA and +12 V 0.83 mA (`monitor-permit-current-report.json`
  conservative screen, without R124), −12 V 0.31 mA.
- Ten buffers at 10 µA quiescent each.
- The total is ≤ 12.2 mA on +5 V. It fits inside the existing 20 mA auxiliary allowance, so
  **no contract change** is needed.
- The envelope SLOPE_SELECT and STORAGE_CLAMP switches are functional, not inputs, and stay
  on their own drive.

**Trial results.**

- Module unit tests and the audit pass. The power parts lie outside the signal lock.
- `connector_packing35.py` then fails with IndexError on the jack-board site list. Every new
  conductor between a jack board and K needs a header contact. At HEAD, JL already uses
  25 of its 25 sites with 0 spare contacts, so even one `ENABLE_OK` net overflows.

**Options (user decision, #52/#54).**

1. Add a JL/JR header site. This is a floorplan change.
2. Generate the permit locally on each jack board. This needs a new evidenced circuit.
3. Route `ENABLE_OK` through the JL–P utility headers. Their capacity is unchecked.

**Evidence gaps.**

- No SN74LVC1G17 VOH/IOH row is promoted, so the high level of a branch under its
  ≤ 1.10 mA load is UNKNOWN.
- The LVC default-LOW behaviour at intermediate supply is not established.

## Not covered

- Return integrity (PRO item 2).
- The reference-receiver injection paths (30 receivers).
- The −6 V negative clamp part.
- Every temperature corner.

Physical qualification remains in #57. None of these proposals is adopted.
