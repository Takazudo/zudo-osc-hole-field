# Fast discrete disconnect candidate — bounded issue-59 result

The common-source NMOS topology removes an analog-switch ground pin, but the concrete resistor-biased PNP version is **not an admissible protection cell**. Its coupled sense-driver DC countermodel requires unavailable amplifier swing; it also has excessive signal-dependent clamp current and no complete source-backed turnoff bound. A drive-only discrete / isolated-sense hybrid is a useful next topology, with quantified timing and current constraints below. Nothing is selected, fitted, energized or substituted; issue 59 remains open.

The authored [candidate](fast-disconnect-candidate.json), [retained evidence](fast-disconnect-candidate-sources.json), [calculator](../../scripts/checks/fast_disconnect_candidate.py) and [generated report](fast-disconnect-candidate-report.json) make this a reproducible circuit counterexample and design boundary. Original ±5 V, 10 kΩ, 1 ms precision targets, external ±12 V fault range, 33 modules, 438 centres, rail maxima, 4.6 A return, capacitance ceilings and 40 mV protection-drop limit remain unchanged.

## Concrete topology and exact parts

```text
LOCAL -- D Q_LOCAL S -- SOURCE_COMMON -- S Q_EXT D -- EXTERNAL_LIMITED
               G ----------- GATE ----------- G

VP -- E Q_UP C -- A D_BLOCK K -- (1kΩ || 1kΩ) -- GATE
      B                                    GATE -- 10kΩ -- SOURCE_COMMON
      +-- 100kΩ -- VP                       GATE -- K Z_GS A -- SOURCE_COMMON
      +-- 10kΩ -- PERMIT_SINK
```

`EXTERNAL_LIMITED` remains behind the original two 499 Ω drive resistors, or the candidate 4.99 kΩ sense resistor. The two NMOS body diodes both point from the common source toward their separate drains. The gate discharge resistor and clamp reference that common source. The PNP base returns to its emitter rail by default; an independent qualified sink enables it. A local-GND monitor, permit generator and physical pin/footprint mapping are not implied by this functional terminal diagram.

| Role | Exact candidate | Primary evidence retained |
| --- | --- | --- |
| Two NMOS | Infineon BSS138NH6327XTSA2, PG-SOT-23 | BSS138N Rev. 2.86, pp. 1–3; H6327 packaging; exact supplier identity and manufacturer package document |
| Default-off pull-up | Nexperia MMBT3906,215 | Existing 10-Apr-2025 owner PDF, pp. 1–3 |
| Reverse blocking | Nexperia BAS116,215 | 5-Aug-2020 PDF, pp. 1–3; manufacturer OPN/12NC identity |
| Gate-source clamp | Vishay BZT52C8V2-E3-08 | Document 86342 Rev. 1.1, pp. 1–2 |
| Two feed resistors | Yageo RC1210FR-071KL, 1 kΩ / 0.5 W | Actual exact-part sheet |
| Gate bleed and base resistor | Yageo RC0805FR-0710KL, 10 kΩ | Actual exact-part sheet |
| Base-emitter return | Yageo RC0805FR-07100KL, 100 kΩ | Prior exact-part sheet |

New primary PDFs remain unaltered with notices in ignored local cache. Only metadata, actual hashes and minimal extracts are committed. No supplier stock, assembly suitability, price or procurement is claimed.

## Both power-off polarities and a second backfeed path

With the internal terminal held at zero and the external terminal at −12 V, an assumed-off common-source node is pulled negative through a body diode. The illustrative 0.7 V diode model puts it near −11.3 V. A gate tied to zero then has approximately **+11.3 V VGS**: the assumed-off state is self-inconsistent. This is an onset counterexample, not a claim that both MOSFETs remain at their low-Ron state or that a particular steady fault current has been solved. A gate-source clamp at 8.2 V would still leave the channel enabled. Positive external voltage does not create this particular false-on condition when the internal node stays at zero.

An isolated pull-up plus a source-referenced bleed lets the ideal disabled gate follow the source for either polarity. It does not prove real off leakage or Miller immunity. **D_BLOCK is required:** a positive, still-charged common source/gate can otherwise forward-bias the PNP collector-base junction into an absent positive rail through the gate bleed/clamp. The diode adds charge, capacitance and reverse-recovery obligations of its own. Local ground loss still requires independently observable fault detection; this topology only removes a ground pin from the signal contact.

## The sense contact cannot carry gate-driver bias

The MOS gate oxide draws little DC current; the external gate-source resistor and Zener do not. Their complete current enters `SOURCE_COMMON`. In the sense branch, that current reaches the feedback/jack network. Independent nodal KCL gives an injection-to-jack transfer of **−4990.75 Ω** for the nominal network. A 50 µA injection shifts the jack about **−249.54 mV**.

This is a **DC transfer/offset shift**, not automatically the difference between unloaded and loaded output. Allocating an illustrative 1 mV of uncompensated static error to this effect permits only about **200.37 nA**; that allocation is diagnostic, not an inferred original absolute-accuracy requirement. To meet the MOSFET's 4.5 V on-resistance test condition, the fitted 10 kΩ bleed alone draws at least **439.8 µA**, including the resistor high bound. Its ideal linear shift exceeds **2.19 V** before clamp current is counted. A bleed exceeding roughly **22.46 MΩ** would be needed for that illustrative allocation. Calibration could remove a constant offset at one operating point.

The captured driver has a stronger problem than an unallocated offset. Solving the sense network and piecewise pull-up/clamp **together** at −5/0/+5 V requires amplifier drive of approximately **-111.162/-40.678/1.585 V**. The negative and zero cases lie outside even the maximum supply magnitudes. Those numbers are the conditional ideal circuit's required linear outputs, not predictions that the real amplifier generates impossible voltages. A real amplifier saturates; the nominal circuit cannot reproduce the requested transfer as drawn. The PNP/diode drops, ideal 8.2 V clamp and 4 Ω MOS contacts are declared countermodel assumptions, and no compensation redesign or complete device operating envelope is captured.

For a DRIVE contact, gate current lies inside remote output feedback, so the amplifier can compensate the voltage while carrying the additional current. A conditional 4 mA drive-current / isolated-sense DC model has about **0.259 mV** maximum ideal load error over −5/0/+5 V, with amplifier drive near −5.519…+5.487 V. This is not calibrated accuracy or a 1 ms transient result. The extra output sink dissipation screen reaches approximately 71.5 mW; installed package heat and fault operation remain unqualified.

The actual resistive pull-up is much more expensive: with the assumed 8.2 V clamp and PNP/diode drops, it draws approximately **17.29 mA** at negative full-scale, of which only 0.82 mA flows in the bleed. The rest flows through the clamp into the analog source node. A viable hybrid therefore needs a bounded current-source or a different gate-charge/active-discharge arrangement. Merely choosing a larger gate-source resistor does not solve every obligation.

## Manufacturer speed numbers do not close the release bound

Infineon supplies genuine maxima: Qg ≤1.4 nC per MOSFET at 0…10 V gate, 48 V drain, 230 mA and 25°C; Ciss ≤41 pF at zero gate / 25 V drain / 1 MHz; turnoff delay ≤10 ns plus fall ≤12.3 ns with a 6 Ω gate driver and the stated switching load. These are useful conditioned facts, not maximum charge or delay over the proposed network's cold-collapse trajectory and temperature range.

Even pretending the two-device Qg total alone covers the whole transition, discharging through the 10 kΩ high bound down to a **diagnostic** 0.1 V VGS gives a conservative charge-over-minimum-current screen of **286.5 µs**. That calculation excludes clamp/diode/driver charge and does not establish VGS=0 leakage at the endpoint. A threshold specified at 26 µA is not an off-current guarantee.

The PNP's 225 ns storage plus 75 ns fall maxima require **1 mA reverse base current**. Its 100 kΩ default-off resistor provides only an illustrative **8.5 µA** at the stated saturation voltage. The BAS116's 3 µs reverse-recovery maximum also has a specific 10 mA forward/reverse test. No complete release maximum is therefore recorded; both `whole_gate_network_charge_max_C` and `complete_disconnect_delay_max_s` remain null.

The exact current-neutral alternative **VOM1271T** drives GATE relative to SOURCE_COMMON photovoltaically. Its retained Rev. 1.9 datasheet gives **65 µs typical**, with the maximum column blank, at 20 mA LED current and 200 pF load. Its minimum output voltage/current are specified at 10 mA LED current. It fixes the DC isolation mechanism but does not supply the missing release bound or a free LED-current budget.

## Hybrid collapse and the other 66 outputs

Retain one AQY232G3HSX isolated SENSE contact per precision output and consider a fast discrete DRIVE contact. At cold +12 V external forcing, the original resistor bounds give approximately 12.305 mA drive injection and 2.461 mA sense injection per cell. The following screens spend an **illustrative 0.3 V excursion** and optimistically assume the entire 150 µF nominal analog-rail ceiling, minus 20% tolerance, is reachable: **120 µF**. Neither that excursion nor capacitor reachability is a newly accepted requirement.

For 16 precision outputs, with the sense contact still conducting for its conditional 0.5 ms table delay, equal drive release must be no later than **82.85 µs** at zero detection delay. A hypothetical 50 µs drive release needs about **98.44 µF** and leaves only **27.37 µs** for detection. These are requirements on a future circuit, not proven timings. Reference paths and disconnected local reservoirs cannot be omitted or assigned zero current.

The other **66 outputs are real general_output cells**, enumerated in the generated report. Their local feedback precedes the same 998 Ω output resistance. The standard explicitly specifies general ±5 V unloaded and accepts normal resistive loading; they have no separate precision SENSE branch. **One contact instead of two is a justified simplification.** They still require bipolar external-fault, powered-off, partial-rail and return-loss protection. No slower-release or backpower exemption was found. The lack of a precision-specific 1 mV target is not permission for arbitrary offset or distortion.

Six of those outputs, E1…E6.ENV, require **0…8 V**. The present positive-rail PNP pull-up provides only about **2.26 V VGS** at +8 V in the stated headroom screen, below the BSS138N 4.5 V Ron condition. A lower-gate-voltage guaranteed MOSFET or floating/boosted driver would be needed; an unbounded typical curve is insufficient.

If **all 82 drive contacts plus 16 senses** experience the same cold-collapse forcing, the optimistic 120 µF budget permits only approximately **16.16 µs** equal drive release before detection. The 16-cell result cannot be generalized. This is a declared concurrency sensitivity, not a new simultaneous-all-output-short source-capacity claim; the 30 reference paths still need their own complete accounting.

## Current budget and the unselected 15 ms ramp proposal

The calculator retains the original normal ledger and every auxiliary allowance. Drive gate/clamp current is charged to **both** analog rails because the amplifier can sink it to −12 V; base current additionally loads +12 V. Sixteen precision rail bleeders are included. Sixteen isolated sense LEDs grouped into eight 5 mA strings add 40 mA on +5 V, with real current-driver and grouping design still absent.

For **only 16 precision DRIVE contacts** limited by a hypothetical 4 mA source each, plus the above loads, derived continuous requirements are 1800/1700/300 mA. The current 10 ms ramp yields rounded transient requirements 2100/2000/400 mA and zero analog limiter windows. An unselected **15 ms minimum ramp** reduces capacitor ramp terms to 149.76/148.44/41.6 mA and yields rounded transients 2000/1900/400 mA, restoring 100 mA windows under the original 2100/2000/500 mA ceilings. The 4.6 A return ceiling and 40 mV drop remain; the prospective continuous loads require tighter protection-path resistance.

The actual original rule is “no faster than 10 ms.” No maximum startup deadline was found in the current OSC-ES-1, source contract or original electrical-decision records, so a 15 ms proposal is not forbidden by that rule. Actual sequencing/startup behavior must still be qualified. **Slower startup does not relax shutdown timing**, and no source file is changed here.

The full **82-drive** version of the same 4 mA/per-contact architecture still exceeds the original maxima, even at 15 ms: its rounded transient requirements become 2400/2200/400 mA. The concrete resistor/Zener pull-ups fail even for the 16-cell sensitivity. Remaining output and reference families cannot be made free to close the ledger.

## Verification and next circuit constraints

Portable tests exercise both power-off polarities, source-referenced gate/base topology, blocking-diode direction, independent sense and drive KCL, preserved timing gaps, invalid inputs, full 82-output coverage and unchanged rail ceilings. The checker verifies present source bytes and reports absent optional caches honestly. No native schematic/ERC/PCB, MOSFET transient model or bench timing was run: the static sense conflict and uncaptured full gate-charge/driver timing already prevent admission, and a typical-capacitance simulation would not cure those gaps.

The next concrete design must provide a **default-off, source-referenced fast discharge without persistent precision-sense bias**, bound total gate/clamp/driver charge and stored-charge removal over the actual rail/temperature trajectories, and establish detector plus release time against reachable capacitance for the complete fault concurrency. Keep the sense contact electrically current-neutral. For the other 66 outputs, retain their one-contact simplification while proving the +8 V headroom cases and both external fault polarities. Replace the wasteful resistor/clamp pull-up with a bounded low-bias driver and close the complete 82-drive/16-sense/30-reference ledger before any population change. No source-backed complete timing certificate was obtained in this batch.
