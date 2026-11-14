# Issue #59 plan: full on-board protection

**Status: plan only. Unvalidated draft.** This file selects no part and changes no
specification, schematic, ledger, inventory or gate. Issue #59 stays OPEN and every
board stays NON-ORDERABLE / NOT-ENERGIZABLE. Prepared 2026-11-14 against `origin/main`
`9cc7f465`.

The owner decision (2026-11-14, #59 comment 6869690807) is the scope:

- Every existing #59 target stays unchanged.
- The synth boards own all protection. Nothing moves to the EXT source contract.
- Powered-off patching stays in scope.

Gate state at planning time:

- `python3 scripts/checks/protection58.py --check` prints `PASS: protection audit consistency ONLY` and
  `BLOCKED: exact protection implementation gate; no topology selected`.
  The TMUX7412FRRPR and LM74800MDRRR cache byte checks print `NOT RUN` because the cache is absent.
- `--require-closed` stays red.
- The pre-ramp predicate `default_off_partial_power_protection_valid` is FALSE. It exists only in the
  untracked recovered sequence model
  (`positive-path-100nf-capture/scripts/checks/positive_sequence.py`). No tracked check carries it yet.
- `pnpm circuit:check`: NOT RUN for this plan. The fresh worktree has no `node_modules`,
  and no evidence file changed.

## Already done vs. reusable

| Area | Done (tracked) | Reusable as-is | Superseded by the owner decision |
| --- | --- | --- | --- |
| Obligation inventory | `protection58-audit.json`: 82 output UIDs, 16 sense paths, 30 reference receivers, 8-row rail state table, 6 arrival orders, return counterexample, 7 open gates | All of it. It is the closure checklist | — |
| Loss screen | 40 mV drop budgets; PSMN1R0-40YLD 2.45 mΩ hot (VGS 4.5 V, 150 °C) resistance-only screen | Arithmetic and FET conditions | — |
| Signal isolation | ADG5412FBRUZ owner (`component-adi-adg5412fbruz`): pinout, 1.3 mA/package IDD max at ±16.5 V, 16.5 Ω Ron max at ±13.5 V, 100 nA grounded-off leakage max, 10 µA floating leakage **typical only**, power-off isolation **requires GND**. #58 TI-amplifier diagnostic: 12/12 cases with lumped switch R/C and 2.74 k/10 M/10 nF. `precision-output-cell*`: AQY232G3 PhotoMOS cell with no analog ground pin, 24 powered-on cases. `integrated-output-candidate*`: ADG5401F, which also requires GND. `fast-disconnect-candidate*`: resistor-biased PNP form rejected. `proposals-59/` P59-A/B/C patches, unadopted | ADG owner facts; cell topologies and feedback values; rejection records | — |
| Monitor/permit | `monitor-permit-draft*`: TPS37044 + TLV9022 + REF3433 + LVC1G17 ×2 + LVC1G74, isolated native capture with 0 ERC errors/warnings, a dummy load only. `rail-monitor-candidate*` static margins. `negative-monitor-network*`. `negative-inverter-candidate*` (OPA388). `monitor-fault-retiming*`. `monitor-permit-current-report.json` | Captured candidate circuit and calculators | Its assumption that the latch shares the original 20 mA allowance |
| Rail switching | Recovered and untracked: `positive-path-100nf-capture`, LM74800MDRRR + 2× PSMN1R0-40YLDX + 100 nF C0G ramp, with a conditional 100 ms SOA screen. `negative-hotswap-v2`: LM5067 published window rejected at fixed Rs, LTC4253 programmed-SS accuracy open. `negative-precision-limiter-v2`/`return-v3`: an INA293A3/TLV3601/REF5020/TPS709 frontend with a 10 mΩ shunt | Topologies, rejection scopes and frontend graph | The `return-v3` "external/current-rise handoff" options. Under the owner decision these become synth-side obligations or an owner input (see below) |
| Return integrity | Recovered `return-interface-observability`: a 16-state proof that aggregate AGND voltage cannot detect a failed inlet return replaced by a patch sleeve | Counterexample and acceptance wording | The packet's source/harness-side implementation alternative |
| Sequencing | Recovered `positive_sequence.py`: OFF→RAMP→READY→LATCHED, with admission requiring the predicate | Requirement model | — |

## Sub-issues, in dependency order

### SI-1: Revised protection current requirement and contract reconciliation

**Goal.** Replace the 20 mA per-rail `protection-supervision-discharge` allocation with an explicit
requirement calculation for full on-board protection. Then regenerate the continuous, transient and
drop checks. The maximum delivered current stays 2100/2000/500 mA.

**Builds on:**

- `supply-architecture-input.json` (`load_envelope.auxiliary_allowance_mA`, `minimum_continuous_current_mA`).
- The `selected_requirement` derivation in `supply-architecture.json`.
- The `protection58.py` sensitivity rows: `ceil(98/4)×1.3 = 32.5 mA` global, `35×1.3 = 45.5 mA` module-local,
  plus 10 receiver-local packages in the historical row.
- `monitor-permit-current-report.json`.
- `positive-path-100nf-capture`: a ≤1.557 A non-capacitive bound to keep the 1.7 A ramp.

**Open questions:**

- The continuous contract is 1700/1600/300 mA. `osc-pd-current-handoff.json` records the owner
  decision of 2026-11-04 that keeps +12 V at 1700 mA as margin, with the check
  `canonical <= contract`. The post-S2b canonical rule result (commit `2e490ca8`) is
  1600/1600/300 mA. On +12 V that is 1450.9 mA × 1.1 = 1596 mA, only about 4 mA under the next
  100 mA step. Added protection current therefore consumes the +12 V margin almost immediately.
  The revised calculation must show the canonical result stays at or below the 1700 mA contract,
  or present an explicit contract change.
- The per-rail sum must cover:
  - ADG/receiver quads on ±12 V;
  - monitor, reference and latch on +5 V or a dedicated control rail;
  - gate-driver and charge-pump currents;
  - return-sensor excitation;
  - bleed and discharge networks.

  No unused-channel savings may be counted.
- The transient (1900/1900/400 mA) must still leave a positive window below the maximum delivered current.
- The 40 mV drop must be rechecked at the new continuous value.

**Evidence that closes it:**

- A generator-owned, per-function allocation table, then the final values once SI-2…SI-5 pick parts.
- The `build_supply_architecture.py` ledger-equality check must pass.
- The `protection58` audit must read the revised allowance instead of the constant 20.

**Gates affected:** the supply-architecture generator equality check, `existing_aux_allowance_mA`,
and the `normal_positive_Iq_*` rows in `protection58-audit.json`.

**New sources:** none for the method. Each final per-part maximum comes from the SI-2…SI-5 owner bundles.

### SI-2: On-board return-integrity and local GND-loss detection

**Goal.** Make return continuity observable on board, independent of any patch-sleeve return.
This covers:

- each inlet AGND contact (pins 5–8), across all 16 states, at zero load;
- local device-GND loss across the #35 nine-board stack (12 load-side wires, 195 GH harnesses);
- an output named `return_integrity_valid` that feeds SI-3.

This comes before the switch choice because ADG5412F and ADG5401F power-off isolation is
specified only with GND present.

**Builds on:**

- The `return-interface-observability` counterexample.
- `protection58-audit.json` `return_counterexample`.
- The inlet pin map: pin 4 NC, pins 5–8 AGND.
- The 4.6 A worst single-return rule and the 0.2 V rail-plus-return loss budget.

**Open questions:**

- Branch-sensitive observation must happen before the parallel join while AGND keeps conducting.
  Options are current, flux or bounded excitation. The pin map must not change.
- What excitation detects a branch at zero load?
- What latency and error bound, and what burden inside the return-loss budget?
- How is GND loss defined per board and per harness?
- Which partition is protected: a whole board, or each switch island?
- If ADG stays, what keeps the switch GND reference valid during a detected loss?

**Evidence that closes it:**

- Exact sensor identities with retained primary sources.
- A per-branch, 16-state truth table with guaranteed thresholds.
- A local-GND-loss fault matrix per board.
- An executable check that rejects aggregate-voltage-only sensing.

**Gates affected:** `open_gates` items 5 and 6, and the `return_integrity_valid` admission term.

**New sources:** any sensing part is **NOT RETAINED**. The earlier DC/magnetic screens are limited
negative evidence only.

### SI-3: Autonomous all-rail monitor with a default-OFF latch and finite fault deadline

**Goal.** Build monitoring at the load without relying on any upstream power-good. It needs:

- guaranteed windows, tolerance and hysteresis for +12, −12 and +5 V;
- control power that survives a fault;
- a default-OFF driver and latch that hold OFF with every rail absent or partial;
- all 6 arrival orders and all 6 failure orders, including brownout and hiccup;
- signal disable before rail discharge;
- a finite fault deadline derived from the SI-4 SOA and let-through and the SI-5 clamp stress;
- permit distribution to every board island.

**Builds on:**

- `monitor-permit-draft.json` and its native capture.
- `rail-monitor-candidate-report.json`, with recovery margins of 17.7/11.0/122.8 mV upper and
  conditional static values only.
- `negative-monitor-network*` and `negative-inverter-candidate*`.
- `monitor-fault-retiming*`.
- The `component-monitor-permit-candidates` owner.
- The recovered `positive_sequence.py`. Port it into a tracked check.

**Open questions:**

- The draft powers the monitor from the monitored +5 V. A surviving control supply is not designed yet.
- Negative-domain level shifting into the RAW_N12/NEG_SENSE frontend is unbounded in a fault
  (`return-v3`).
- TLV6700 timing is nominal only. TPS37044 has a 10 µs max under conditions, but its startup is nominal.
- ISO7710 default-low needs a powered receiver.
- The REF3433 output capacitance is unestablished because its Murata source is unavailable.
- What is the deadline value, and is it guaranteed rather than typical?
- What is the reset and recovery behaviour? See the owner inputs.

**Evidence that closes it:**

- A captured monitor, latch and driver with guaranteed-column timing.
- A 27-state input/receiver/signal matrix plus 6 + 6 order runs through the pinned ngspice.
  These are diagnostic, not qualification.
- The tracked sequence check, with the predicate wired to real SI-2/SI-5 evidence and not a status string.

**Gates affected:** `open_gates` item 2 and the pre-ramp predicate.

**New sources:** the control-supply and level-shift parts are **NOT RETAINED**.
The TPS37044, TLV9022, REF3433, LVC1G17/74 and OPA388 sources are retained.

### SI-4: Rail switching paths for +12, −12 and +5 V

**Goal.** Capture exact switch, driver and reverse-blocking paths for each rail. Each must meet:

- a ≤40 mV protection drop at the SI-1 continuous current, checked at 2.1/2.0/0.5 A;
- guaranteed hot on-resistance;
- reverse current blocking, including in the enabled state;
- every MOSFET body-diode orientation;
- dissipation and linear SOA during the ramp and during fault let-through;
- control by the SI-3 latch only (`RAMP_ENABLE`), never by the signal permit.

**Builds on:**

- `loss_calculations` / `fet_conditions` in `protection58-audit.json`.
- LM7480 SNOSDD8 extracts in `protection59-sources.json`. The cache bytes are absent, so the byte
  check is NOT RUN.
- The recovered +12 V capture (LM74800MDRRR + 2× PSMN1R0-40YLDX, 100 nF ramp, 15.5–33.2 ms ideal ramp).
- `negative-hotswap-v2`: LTC4253 34-page PDF hash recorded in the packet README; the PDF is not in
  the tracked repo.
- `negative-precision-limiter-v2` / `return-v3`.

**Open questions:**

- −12 V controller: LM5067's fixed-Rs window is rejected. LTC4253 programmed-SS transfer has only
  typical rows (needs a 0.805 mV window). LTC4371IMS#PBF is SOURCE UNAVAILABLE.
- +5 V has no candidate at all.
- A 10 mΩ shunt takes about 16 mV of the 40 mV budget.
- Unsensed bias-branch currents.
- Whether on-board current limiting is required. See the owner inputs.
- The mounting-base temperature behind the SOA screen.
- Downstream capacitor discharge in local fault loops.

**Evidence that closes it:**

- Exact identities with primary bytes and locators for all three paths.
- Guaranteed-column Ron/SOA arithmetic.
- A reverse-current state table.
- Let-through ≤ the trip plus unsensed current integrated over the SI-3 deadline.

**Gates affected:** `open_gates` item 1 and `loss_calculations`.

**New sources:** the +5 V path and any −12 V controller replacing LTC4253 are **NOT RETAINED**.
LTC4371 needs a fresh official byte acquisition; do not invent a hash.

### SI-5: Fault-protected signal isolation for 82 outputs, 16 sense branches and 30 receivers

**Goal.** Make every path default-OFF and safe under:

- powered-off and partial-power external ±12 V;
- floating or discharging rails;
- GND loss, through SI-2;
- enabled output contention (about 0.303 W per 499 Ω).

Local feedback must hold when the path is disabled. References stay within EXT, and the
sensitive storage, summing and timing nodes stay local. The ≤1 mV load error, ≤2 mV calibrated
error, 1 ms settling and 10% overshoot targets must be preserved.

**Builds on:**

- The ADG5412FBRUZ owner and its paired-channel arithmetic: 98 channels, 25 global or 35
  module-local quads.
- The 30 receivers. They are SW101-type selector inputs and are not in the 98. The historical row
  adds 10 receiver-local packages, so the module-local count is 45.
- The #58 diagnostic and the 4.99 kΩ precision cell.
- The AQY232G3 PhotoMOS cell, which is ground-independent and an option where SI-2 cannot keep GND.
- The `p59b`/`p59c` patches.
- The installed TMUX7412FRRPR (98) input switches. They are not part of this population.

**Open questions:**

- ADG5412F tables are specified at ±15/±20 V. Do they apply at ±12 V?
- Floating-rail leakage is typical only and needs a guaranteed bound or an added clamp.
- Do Dx clamp currents (30 mA abs max) stay within OPA4197 input and output limits?
- How do the switches behave between supply minimum and logic threshold? (P59-C)
- Package and island allocation against fixed placements.
- Charge injection and switch transients.
- Re-run stability, calibration, noise and current with a vendor switch model.

**Evidence that closes it:**

- Per-path captured cells with exact parts.
- An injection matrix covering every path and every rail state.
- An ngspice re-run with conditioned switch models. This is diagnostic only.
- Thermal and contention bounds per package.

**Gates affected:** `open_gates` items 3, 4 and 7, and the predicate.

**New sources:** the ADG5412F SPICE model and any guaranteed floating-supply leakage are **NOT RETAINED**.

### SI-6: Integration capture, ledger finalization and gate closure

**Goal.**

- Capture SI-2…SI-5 into the board specs and generators.
- Regenerate netlists, BOM and board reservations with `bash scripts/checks/regen-all.sh`.
- Run KiCad 10.0.6 ERC through `scripts/kicad/run.sh`.
- Finalize the SI-1 numbers from the real part counts.
- Replace each `protection58` open claim with an evidence-backed check, so that
  `--require-closed` can pass only on real evidence.

**Builds on:** everything above, `design/grid/placements.lock.json`, and the #35 board partition.

**Open questions:**

- Fit against fixed placements, reported with dimensions. Jacks and controls do not move.
- Domain-separation checks.
- Cross-board permit and GND routing.

**Evidence that closes it:**

- Regenerated outputs with no drift.
- ERC results recorded.
- Every new check passes.
- Physical transient, fault and thermal tests stay NOT RUN in #57.
- The result remains an unvalidated draft.

**Gates affected:** `protection58.py --require-closed`, the draft-contract gate (it must stay passing),
and the next-actions docs.

**New sources:** none beyond SI-2…SI-5.

## Owner inputs still needed

1. **Fault let-through premise.** The on-board fault deadline needs a current or energy bound during
   detection. Two choices:
   - Rely on the *existing* EXT requirement (≤2.1/2.0/0.5 A maximum including let-through).
     This adds nothing to the contract.
   - Add on-board current limiting. A 10 mΩ shunt costs about 16 mV of the 40 mV budget on ±12 V.

   This decides the SI-4 topology.
2. **Fault recovery behaviour.** After a latched fault, choose between:
   - recovery only by a full power cycle, with supervised discharge;
   - a reset input;
   - bounded automatic retry.

   No new panel control or indicator position is available under the fixed-placement rule.
3. **Conditional:** owner input is needed only if SI-1 shows a transient above the
   2100/2000/500 mA maximum delivered current, or SI-6 shows the quads and rail switches do not fit
   the fixed placements. Both would change an existing target.
