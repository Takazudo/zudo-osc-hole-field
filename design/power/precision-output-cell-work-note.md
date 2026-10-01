# Precision output protection candidate — issue 59

This batch captures one **candidate analog cell**, exact component evidence and reproducible bounds. It does not select a protection implementation, change the installed 110 switches, close issue 59, authorize energization, or change any board/source epoch. The original 33 modules, 438 fixed centres, signal limits and supply envelopes remain unchanged.

The useful result is a ground-independent contact topology with quantified remaining obstacles. Ordinary grounded CMOS switch protection cannot establish safety after its required ground disappears. Panasonic PhotoMOS output contacts have no analog ground pin. That removes this particular dependency; it does not create a ground-fault detector or guarantee immediate disconnection during a rail collapse.

## Captured connectivity and exact identities

The authored source is [precision-output-cell.json](precision-output-cell.json); the generated pin list is [precision-output-cell-connectivity.txt](precision-output-cell-connectivity.txt). It preserves the issue-58 feedback topology, increases the jack sense resistor from 2.74 kΩ to 4.99 kΩ, and adds two isolated contacts plus local rail bleeders.

```text
OPA4197 DRIVE -- K_DRIVE -- 499Ω -- 499Ω -- JACK
JACK -- 4.99kΩ -- K_SENSE -- FB
DRIVE -- (10MΩ || 10nF) -- FB

Independent PERMIT_I_PLUS -- LED(K_DRIVE) -- LED(K_SENSE) -- PERMIT_I_MINUS
VP -- 100kΩ -- local GND -- 100kΩ -- VN
```

The permanent resistor/capacitor feedback path remains local to the amplifier when contacts open; the jack is outside both contacts. The passive current-limiting resistors are on the jack side of each contact. Contact capacitance belongs between contact pins, not between a contact pin and analog ground. The unused three OPA4197 cores are grounded followers, as in the existing cell; their quiescent current is included.

| Role | Exact candidate / retained part | Evidence |
| --- | --- | --- |
| Amplifier | Texas Instruments OPA4197IPWR, PW TSSOP-14 | Existing SBOS737C, printed pp. 4–8 |
| Drive/sense contacts | Panasonic AQY232G3HSX, SOP4 reel X | ASCTB149E 202610, printed pp. 2–7 |
| Two output resistors | Yageo RC1210FR-07499RL, 499 Ω, 1210 | Existing exact-part sheet, 0.5 W at 70°C |
| Sense resistor | Yageo RC1210FR-074K99L, 4.99 kΩ, 1210 | Acquired exact-part sheet, 0.5 W at 70°C |
| Permanent feedback | Yageo RC0805FR-0710ML, 10 MΩ, 0805 | Acquired exact-part sheet |
| Compensation | KEMET C0805C103J5GACTU, 10 nF ±5%, 50 V C0G, 0805 | Acquired exact-part sheet |
| Rail bleeders | Yageo RC0805FR-07100KL, 100 kΩ, 0805 | Acquired exact-part sheet |

[The source receipts](precision-output-cell-sources.json) contain actual SHA-256 values, primary URLs, physical and printed page locators, and minimal normalized extracts. Newly downloaded complete PDFs remain in the ignored cache with all notices; they are not published or committed. Supplier-order routing for the new candidates remains UNSOURCED. No order code was invented. The live Panasonic catalog acquired under an old-looking URL contains **AQY232G3HSX**, not the older AQY232SX; its characteristics cannot be transferred to that old identity.

The permit interface is deliberately explicit: an independent source supplies the two series LEDs at the 5 mA characterization condition, with at least 3.4 V compliance at 25°C, and removes LED current on fault. It must not use local GND as its return. A current source, default-off circuit, all-rail/reference qualification and independently observable ground continuity are **not yet captured**. Neither a resistor-fed LED assumption nor the 1 mA operate-current threshold supplies the 5 mA timing/resistance guarantees. Supply decoupling, footprint and board integration are also open, so this batch does not issue a native KiCad schematic or electrical receipt.

## What the calculations establish

[The generated report](precision-output-cell-report.json) includes equations, conditions and source hashes. Calculations use the original 10 kΩ minimum load, ±5 V signal, 5 nF cable and up to 24.48 V opposing fault differential. Resistor bounds combine 1% tolerance with 100 ppm/°C over the complete −55…155°C component range, independently of ambient-temperature power derating.

| Quantity | Conditional result | Practical limit |
| --- | --- | --- |
| Ideal DC loading error | 0.267 mV | Permanent 10 MΩ path included; not calibrated total error |
| PW input-bias contribution | ≤0.077 mV | Combined subtotal 0.343 mV; amplifier offset/gain/thermal accuracy still open |
| Sustained main/sense fault current | ≤25.103 / 5.021 mA | Intact rail reference, no credit for a trip; input absolute current is not a recommended operating target |
| Each existing 499 Ω resistor | ≤0.3073 W | 0.5 W part; derating permits this only below about 102.8°C ambient under the manufacturer's mounting assumptions |
| Amplifier screening dissipation | 0.303 W whole quad with one contended active core | Includes all four cores' quiescent current; actual installed thermal path and abnormal clamp currents unknown |
| Two off contacts into one rail | ≤0.2047 V differential with 100 kΩ bleed | Only at sourced 25°C/IF=0 leakage conditions, no other energizing path; no absolute floating common-mode bound |
| Each bleeder at maximum supply | ≤0.128 mA, ≤1.594 mW | Must be included in an eventual aggregate ledger |

The bleeder result is a useful passive backstop after isolation. It does not establish whole-board non-backpower: a modeled 10 µF rail takes about 4.97 s to decay from 12.48 V to the illustrative 0.3 V guard under worst leakage. That guard is a diagnostic choice, not a relaxed replacement for an original requirement. Other powered ports, shared-rail injections and actual capacitor locations must be included before a safety claim.

The resistor-only alternative fails more fundamentally. With a conductive/unqualified switch, +12 V through approximately 975 Ω charges a floating, unloaded 10 µF rail to about 1.17 V in 1 ms and eventually toward 12 V. Holding the same illustrative 0.3 V with a passive bleed would require about 25 Ω and 0.480 A at 12 V. This is a counterexample to a **resistor-only proof**, not a statement that all ground-independent topologies are impossible.

## Cold collapse and local ground loss remain decisive

After an abrupt rail collapse, the two contacts can remain closed during detection and release. Even using the catalog's 0.5 ms maximum release condition at 25°C and assuming zero detection delay, the cold +12 V jack can inject approximately 12.31 mA through DRIVE and 2.46 mA through SENSE. The sense path is below the amplifier's 10 mA absolute input-current rating in this simplified calculation; the amplifier has no established powered-off **output injection** guarantee here. The input rating must not be copied to the output.

With the explicitly assumed 10 µF local reservoir and 100 kΩ bleed, a conductive-clamp counterexample reaches about **0.716 V before contact release**. The simple charge bound requires at least 24.6 µF for the cold-current case, or 50.2 µF for the conservative 24.48 V differential, to stay within an illustrative 0.3 V excursion. Detection delay, capacitance derating, ESR and accessible wiring all worsen the requirement. The actual local reservoir remains unknown.

The original supply contract caps nominal analog-rail capacitance at 150 µF. If all 16 precision jacks are held at +12 V during the same collapse, the constant-current screen asks for about 394 µF even at the 0.5 ms catalog release time. Assigning the whole 150 µF ceiling to this purpose and taking its −20% tolerance gives an optimistic detection-plus-release allowance of about **152 µs**. Actual fault concurrency and whether shared capacitance remains connected must be established. Bulk capacitance cannot simply be added beyond the existing contract.

A voltage-only monitor also cannot identify a particular opened ground conductor when an equally low-impedance alternate return leaves all observed voltages unchanged. A new monitor must specify the actual observed conductor, independent reference, test stimulus and alternate-return coverage. Two isolated output contacts alone do not solve this observability problem, and firmware cannot infer an unobservable physical break.

## Bias current prevents blanket replication

The original ledger is read directly by the calculator. It currently contains normal loads including allowances of 1534.819 mA / 1435.569 mA / 224.286 mA on +12 V / −12 V / +5 V, with 20 mA protection/supervision allowance on each rail. The continuous requirements remain 1700 / 1600 / 300 mA; maximum delivered currents remain 2100 / 2000 / 500 mA. No saving from the existing 110 switches is booked.

The 82 drive, 16 sense and 30 reference contacts total 128 LEDs. Independent 5 mA strings consume 640 mA. Pairing only the 16 precision drive/sense LEDs leaves 112 strings, **560 mA**, above the whole +5 V maximum before other loads. Even pairing every contact gives 320 mA; adding the existing normal +5 V load while replacing the entire 20 mA auxiliary allowance gives **524.286 mA**, still above the 500 mA limit. Real driver overhead and remaining supervision demand are additional.

Six LEDs per +12 V string would require 22 strings / 110 mA. Even assigning the entire existing auxiliary allowance to them gives 1624.819 mA normal, which becomes **1800 mA** using the original 10% reserve and 100 mA rounding. This is a prospective **minimum delivery requirement**, not a maximum-capacity violation by itself. The current declared 1700 mA requirement remains unchanged until a complete implementation justifies a ledger update. Cold/hot LED voltage, current-source compliance, grouping and failure behavior also remain unproved. The 2 mA recommended LED current cannot inherit G3HS resistance and timing maxima measured at 5 mA.

Two more useful sensitivities retain all original auxiliary allowance, the original reserve/ramp/fault terms, and add this candidate's 16 precision-cell bleeders:

- **No input-IC substitution:** 10–12 strings of at most 13 LEDs across ±12 V need 50–60 mA on each analog rail. The derived continuous requirements become 1800/1700 mA, with transient requirements 2100/2000 mA. Those equal the original maximum-delivered limits and preserve the 4.6 A return ceiling. They leave **zero positive limiter window**, so the existing strict source acceptance is not met. The 40 mV protection drop now implies at most 22.22/23.53 mΩ at those prospective continuous currents; it is not increased. This is a smaller physical-change candidate than replacing 110 ICs, but no string map or regulator is captured.
- **Conditional exact 110-quad TMUX substitution:** seven 13-LED bipolar strings plus seven strings of up to six LEDs from +12 V cover 128 contacts at +70/−35 mA. Replacing only the 110 existing ADG5412FBRUZ packages with TMUX7412FRRPR would change conditioned planning current by −77/−22 mA. Including the 16 precision bleeders then retains derived continuous 1700/1600/300 mA and transient 2000/1900/400 mA, with 100 mA windows. This is not a booked saving: the TMUX maxima used are at ±16.5 V, not the actual ±12 V project condition, and no existing package is replaced.

Thirteen LEDs at the 25°C 1.7 V maximum leave only 1.17 V of minimum bipolar-rail compliance; six leave 1.33 V on +12 V. Hot/cold Vf, actual current regulators, regulator overhead, other required bleeders and reference loads, control fault behavior and physical locality/grouping remain unknown. Neither sensitivity establishes the complete protection design or permits a source-contract change.

For the no-substitution cases, the transient arithmetic **before the final 100 mA rounding** is 2049.64/1947.66 mA. The original physical ceilings exceed those sums by 50.36/52.34 mA, respectively; the final rounding allowance consumes that arithmetic difference. This distinguishes a possible future tolerance/peak proof from actually exceeding a physical current ceiling. The existing rounded-requirement/strict-window gate is still not admitted, and neither its rounding nor the original contract is changed here.

An exact lower-current alternative in the same retained primary catalog is **AQY234SX**: maximum 35 Ω on resistance and 2 ms release at IF=2 mA, 25°C, specified load conditions; 320 V recommended contact voltage. Its resistance could be accommodated inside the feedback loop, and longer strings across the analog rails could lower bias current. Its four-times-longer release worsens collapse injection. This is an identified tradeoff, not a selected fix. Its forward-voltage maximum is specified at 50 mA; hot string compliance and a real regulated permit source still need evidence.

## Verification and next bounded implementation

`python3 scripts/checks/precision_output_cell.py` regenerates the bounds and pin list; `--check` detects drift and validates any present cached bytes. `python3 -m unittest scripts.checks.test_precision_output_cell -v` exercises independent KCL, fault counterexamples, budget failures and identity/topology mutations; its `test_*.py` name also includes it in ordinary portable test discovery. Importing the model's deck builder does not run the oracle. The model script uses the existing digest-pinned TI OPAx197 core in the pinned KiCad/ngspice oracle; decks and initialization remain inside a disposable ignored cache directory. Its PhotoMOS contacts are only static lumped R/C sensitivity elements.

Input validation binds the signal, load and fault envelope to OSC-ES-1, rail/ambient limits to the current supply contract, and channel populations to the issue-58 audit. Sourced device values and their test conditions are fixed receipt transcriptions, not sensitivity knobs. Only contact capacitance, assumed rail capacitance, the diagnostic voltage guard and resistor ambient screens may vary within their validated physical domains. A guard at/below the worst leakage equilibrium cannot yield a finite discharge time and is rejected. Nonfinite values, negative electrical magnitudes, zero capacitance, booleans, unclassified fields and overflowing results fail before a report is emitted; valid subzero Celsius screens remain permitted. Direct calculation calls use the same checks. These checks do not qualify the hardware.

The initial 400 µs sweep met the stricter inherited diagnostic in only 12/24 cases, with worst error approximately 2.46 mV. The final model report measures the original 1 ms deadline directly with longer plateaus: **24/24 meet the original target**, maximum deadline error 0.272 mV, maximum overshoot 5.486%, and at most 0.001 mV ripple after the deadline. The retained 400 µs diagnostics still meet only 12/24. Neither sweep proves switching, fault, temperature or hardware behavior. See [precision-output-cell-model.json](precision-output-cell-model.json) for actual results. Bench work and native candidate schematic/ERC/PCB checks are **NOT RUN** because no complete control/decoupling/physical candidate exists.

The next implementation should settle the **cold-collapse boundary first**: define actual local reachable capacitance and permitted pin/rail excursion, derive a detector-plus-release requirement, and capture a source-backed fast disconnect or independently current-limited/shunted boundary that meets it. A faster isolated contact must also meet the full-population bias budget; AQY234SX is a concrete lower-current comparison, not a reason to accept slower release. Only then capture the independent permit/ground-observation circuit and run switch-skew, partial-power and aggregate fault tests. Do not replicate this cell or replace the installed switches before those obligations close.
