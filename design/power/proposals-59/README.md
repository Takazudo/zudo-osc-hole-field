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

## Not covered

- Return integrity (PRO item 2).
- The reference-receiver injection paths (30 receivers).
- The −6 V negative clamp part.
- Every temperature corner.

Physical qualification remains in #57. None of these proposals is adopted.
