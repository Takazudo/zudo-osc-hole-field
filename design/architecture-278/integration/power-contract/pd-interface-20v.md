# OSC–PD interface contract for the 20 V / 5 A revision

**UNVALIDATED DRAFT interface record.** It is derived from OSC records only. It
selects no part and changes no OSC requirement, schematic, PCB, BOM or zudo-pd file.
Nothing here is measured. It applies the owner decision of 2026-10-31 11:11Z (decision
card `cmsg_01Pv35emdXEU6gCRF3teSpo23Q1CUhqDN2ebZaArfgF1Ru`): PWR-D3 = D3-A (20 V / 5 A PD revision, 5 A e-marked cable) and PWR-D5 = D5-1
(no degraded mode; accept or refuse). Those are electrical decisions E11/E12 in
`project/osc-hole-field/electrical-decisions.json`. Prepared 2026-10-31.

Each value has one class:

- **CONTRACT**: an existing OSC requirement, quoted with its source.
- **CALCULATED**: arithmetic on CONTRACT values or on owner-bundle facts
  (`.claude/skills/component-*/facts.json`, cited by fact id). It is not a measurement.
  A CALCULATED value marked **(A1)** also depends on assumption A1 in §7. Phase 7
  promoted the absolute-maximum rows of the retained IC datasheets into the owner
  bundles; their fact ids are cited in §7.
- **PROPOSED**: no OSC source exists. It is a starting value for joint agreement, not a
  pass criterion. A PROPOSED value becomes a requirement only when both owners accept
  it, and only after the abs-max and injection facts listed in README Q-A item 1 are
  captured.

The boundary is the OSC inlet `OSC-EXT-PWR-8-R1`. Logical pins 1 / 2 / 3 carry
+12V_IN / −12V_IN / +5V_IN, pin 4 is unpopulated and pins 5–8 are AGND. The connector is
NOT SELECTED. There is no power-good or control pin, so every enable decision on the
source side is made without OSC signalling. Under
`design/power/protection58-draft-contract.json`, the external source or interface owns:

- the maximum-current envelope, including fault let-through;
- reverse blocking on all three rails;
- autonomous load-rail window monitoring;
- coordinated all-rail shutdown and discharge;
- observable inlet-return integrity.

Sources in brief:

- **SAI** — `design/power/supply-architecture-input.json`
- **PCR** — this directory's [README.md](README.md)
- **SUP** — `doc/src/content/docs/decisions/osc-supply-architecture.mdx`
- **PRO** — `doc/src/content/docs/decisions/osc-protection-architecture.mdx`
- **WN52** — `design/power/WORK-NOTE-52.md`

## 0. Delivery envelope (reference for every item below)

| Item | +12 V | −12 V | +5 V | Class / source |
| --- | --- | --- | --- | --- |
| Continuous minimum | 1700 mA | 1600 mA | 300 mA | CONTRACT, SAI `minimum_continuous_current_mA` |
| Transient minimum, held ≥ 20 ms | 2000 mA | 1900 mA | 400 mA | CONTRACT, SUP table; SAI `transient_requirement_duration_ms` |
| Maximum delivered, including tolerance and let-through | 2100 mA | 2000 mA | 500 mA | CONTRACT, SAI `maximum_delivered_current_mA`; protection58 responsibility 1 |
| Source band, ripple included | 12.00–12.30 V | 12.00–12.20 V | 5.05–5.10 V | CONTRACT, SAI |
| Load band | 11.53–12.48 V | 11.74–12.37 V | 4.81–5.20 V | CONTRACT, SAI |
| Ripple at load | < 1 mVp-p | < 1 mVp-p | < 1 mVp-p | CONTRACT, SAI |
| Rail plus return loss | ≤ 0.20 V | ≤ 0.20 V | ≤ 0.20 V | CONTRACT, SAI |
| Load capacitance the source must start | ≤ 180 µF (150 +20 %) | ≤ 180 µF | ≤ 120 µF (100 +20 %) | CONTRACT, SAI |
| Inlet power, continuous / 20 ms transient | 41.12–41.96 W / 48.82–49.82 W (all rails) | | | CALCULATED, PCR budget table |

The worst return contact carries 4.6 A, the sum of the maxima (PCR G8). Assume that
whole sum can flow in any one AGND conductor (SAI `return_current_rule`).

## 1. Limiter trip time against the 20 ms transient

| Load current per rail | Required source behaviour | Class / source |
| --- | --- | --- |
| ≤ continuous minimum | Deliver indefinitely, inside the source band; never trip or fold back | CONTRACT |
| ≤ transient minimum | Deliver for at least 20 ms with no trip, foldback or band exit. Judge it by the peak over the trip's own blanking window, not by a 20 ms average | CONTRACT (20 ms); peak criterion from PCR W6 |
| Between continuous minimum and maximum, beyond 20 ms | A timed trip is permitted, and only as an all-rail shutdown | PROPOSED; the contract sets no duration beyond 20 ms |
| > maximum (2100 / 2000 / 500 mA) | Never delivered. The maximum already includes tolerance and transient let-through, so a fast-trip overshoot above it does not comply (WN52: a fast trip near 2× the active limit cannot establish the cap) | CONTRACT |
| Limiter tolerance window | 100 mA between transient minimum and maximum on each rail. It is a planning proposal, not a proven realizable tolerance | CONTRACT value, labelled proposal in SAI `current_limit_contract` |
| Any trip on any rail | Coordinated all-rail shutdown. Latch off, no auto-retry; reset only by re-plug (a power cycle) | CONTRACT (SAI `fault_policy`, PCR PD-003 condition 3); latch / re-plug / no-retry agreed in PCR W7 |

A device must enforce the maximum (PCR R7), and no current PD candidate does. Both the
ramp ceiling (§5) and the 20 ms transient must fit inside that cap. The PD side owns
limiter dissipation and the time to trip on a sustained over-limit. OSC has no number
for that time beyond "not before 20 ms below the transient minimum".

## 2. Maximum reverse current into the source

| Item | Value | Class / source |
| --- | --- | --- |
| Reverse blocking | Required on all three source outputs | CONTRACT (SAI `fault_policy`; protection58 responsibility 2) |
| Reverse current into each source output, with the source off or shut down and the inlet rail held at up to its load-band maximum (12.48 / 12.37 / 5.20 V) | ≤ 1 mA per rail | PROPOSED. Matched to the 1 mA per-rail inlet leakage allowance (SAI `leakage_allowance_mA`); no OSC reverse-current figure exists |
| Polarity of the withstand | +12V_IN and +5V_IN positive, −12V_IN negative, relative to AGND | CONTRACT (pin map) |
| Back-feed that may be available | 82 outputs × 24.05 mA = 1.97 A per polarity, through the 998 Ω pairs alone | CALCULATED from SAI `fault_basis` and `design/power/downstream-handoff-52.md`. This is **not** a bound: the 100 Ω sense paths (PCR R1) and the reference paths are unbounded |

Source blocking alone does not protect OSC powered-off outputs (SAI `fault_cases[0]`).
That remains OSC #59 work.

## 3. Rail discharge at shutdown: level, time and skew

The record says the exact thresholds and timing are **UNSOURCED** (PRO item 4). The
component-limit rules in §7 are applied where owner bundles carry a fact. Everything
else stays PROPOSED.

| Item | Value | Class / source |
| --- | --- | --- |
| Shutdown action order | Disconnect all three rail paths, then actively discharge all three rails. AGND is never opened | CONTRACT (PRO items 3–4; SAI `fault_policy`) |
| Stored energy to remove at the ceiling | 13.62 / 13.40 / 1.56 mJ (180 / 180 / 120 µF at 12.30 / 12.20 / 5.10 V) | CALCULATED |
| Discharge level, +12 V | ≤ 0.5 V | CALCULATED (A1), R-VEE: a residual +12 V with −12 V discharged can reach VEE5 |
| Discharge level, −12 V and +5 V | ≤ 0.6 V magnitude. The bundle-backed bound for −12 V alone is 6 V (R-VEE); 0.6 V is tighter | PROPOSED |
| End state | Both analog rails grounded (discharged) with AGND present; TMUX7412F powered-off protection requires a GND reference to be present (SCDS404B §9.3.2.2) | CALCULATED, R-SW (`fact-fault-switch-t-fault-grounded-source-leakage` conditions: VDD = VSS = 0 V, GND = 0 V); level not given by the source |
| Discharge time | All three rails at or below that level ≤ 100 ms after the shutdown decision, at ceiling capacitance and zero load | PROPOSED |
| Disconnect skew | All three rail paths open within ≤ 1 ms of each other | PROPOSED |
| Discharge skew, analog rails | No state with +12 V > 0.5 V while −12 V is absent, and none with −12 V magnitude > 6 V while +12 V is absent. Both rails therefore fall together, and neither may lead the other out | CALCULATED (A1), R-VEE |
| Discharge skew, +5 V | No state with +5 V above 0.8 V, one analog rail absent and the other at ≥ 8 V magnitude. +5 V must therefore fall to ≤ 0.8 V no later than the first analog rail leaves | CALCULATED, R-SW; the 0.8 V VINL maximum is from the ±15 V table, so it is conditional at ±12 V. Derived for ADG5412FBRUZ before E13/E15; retained unchanged as a conservative row until OSC re-derives it for TMUX7412FRRPR and TMUX6112PWR (§7 R-SW) |
| Driver interval: both rails present but VEE5 regulation not within specified operation | Exists on every common ramp and discharge, for +12 V between 0.5 V and 5.2 V (REF5050 minimum input). That is 0.41–4.23 ms of a 10 ms ramp, 0.81–8.46 ms of 20 ms and 2.03–21.1 ms of 50 ms. No supply-side ramp, skew or discharge order removes it | CALCULATED (A1), R-DRV. OPEN on the OSC side (#59): it needs an OSC-side bound on VEE5, not a PD number |
| *If P59-A adopted:* driver interval | VEE5 ≤ +0.40 V (clamp current ≤ 10 mA) or ≤ +0.50 V (≤ 30 mA), and VEE5 ≥ the −12 V rail, which is ≥ −6 V while −12 V magnitude ≤ 6 V. On tracking ramps the −12 V magnitude at +12 V = 5.2 V is 5.16 V, so the interval is inside −6 V / +0.5 V. Discharge: −12 V magnitude must reach ≤ 6 V no later than +12 V falls below 5.2 V | CALCULATED (A1, A2, P59-A conditions in §5), 25 °C only. UNADOPTED |
| Re-enable | Only from the discharged state (all rails at or below the discharge level) | PROPOSED |
| Detection-to-disconnect time, and injection charge per pin during it | Must be stated by the design; no OSC value | CONTRACT obligation (PRO item 4); value UNSOURCED |

## 4. Surge envelope at the OSC inlet

| Item | Value | Class / source |
| --- | --- | --- |
| Steady state while enabled | Inside the source band, ripple included | CONTRACT |
| Turn-on overshoot, load-step response and shutdown transients | Inside the source band. The record has no separate overshoot allowance; any allowance above the band is a contract change | PROPOSED reading of the CONTRACT band |
| Overvoltage shutdown | All-rail shutdown if any inlet rail magnitude exceeds 12.48 / 12.37 / 5.20 V (the load-band maxima) | PROPOSED trip; the record requires overvoltage protection (SAI `fault_cases[3]`) with no threshold |
| Overvoltage ceiling, +12 V | < 18 V (AS3340D VCC–GND, REF5050AIDR VIN, LF398M ±18 V and LM13700M ±18 V). The 12.48 V trip is 5.52 V below it | CALCULATED, R-SUP |
| Overvoltage ceiling, −12 V | < 18 V magnitude (LF398M and LM13700M ±18 V). The 12.37 V trip is 5.63 V below it | CALCULATED, R-SUP |
| Overvoltage ceiling, rail-to-rail | (+12 V) + \|−12 V\| < 30 V at every instant: +12 V < 17.63 V with −12 V at 12.37 V, and \|−12 V\| < 17.52 V with +12 V at 12.48 V. The proposed trips give 24.85 V, 5.15 V below the ceiling. BAT54S,215 (30 V) is the binding part; the IC span limits are 36–48 V | CALCULATED, R-CLAMP and R-SUP |
| Overvoltage ceiling, +5 V | < 7 V for the fitted HC logic (SN74HC00/14/74, CD74HC221). NOISE2 has no supply limit in its retained source. If the monitor-permit candidates are adopted the ceiling drops to 5.5 V (TLV9022DR recommended supply). The 5.20 V trip is 1.80 V below 7 V | CALCULATED, R-SUP; NOISE2 gap in §7 |
| Reverse-polarity excursion, ±12 V | ≤ 0.3 V of reverse polarity on either analog rail (TMUX7412FRRPR `fact-fault-switch-t-supply-absolute` and TMUX6112PWR `fact-env-switch-t-supply-absolute`: VDD–GND −0.3 V and VSS–GND +0.3 V; also REF5050AIDR VIN and LM393BIDR VCC −0.3 V) | CALCULATED, R-REV |
| Reverse-polarity excursion, +5 V | ≤ 0.5 V (HC logic VCC −0.5 V). The proposed interface value stays 0.3 V, inside it. NOISE2 has no retained limit | CALCULATED, R-REV; NOISE2 gap in §7 |
| Single-fault VBUS (20 V) reaching an OSC rail | Must not reach the inlet. The inlet contact voltage requirement is ≥ 30 V, but no OSC load is rated for it | CONTRACT (30 V contact rating, SAI `inlet`); load protection PROPOSED |
| Current surge | Never above the maximum in §0, including startup | CONTRACT |
| Hot plug | Prohibited. Ground is not first-mate or last-break | CONTRACT (SAI `inlet.hotplug`) |

## 5. Startup ramp bound

| Item | Value | Class / source |
| --- | --- | --- |
| Shape | One common monotonic ramp on all three rails | CONTRACT (SUP startup; PCR W7 all-rails-together rule) |
| Fastest | No faster than 10 ms, judged by its steepest slope: ≤ 1.23 / 1.22 / 0.51 V/ms (source-band maximum ÷ 10 ms). An interrupted ramp is a separate test case | CONTRACT 10 ms (SAI `soft_start_min_ms`); slopes CALCULATED (PCR Q-C) |
| Slowest | No upper bound in the contract. OSC tolerance of slower ramps is unverified; 20–50 ms is candidate PWR-C1 only | CONTRACT; PWR-C1 CANDIDATE |
| Startup current, ceiling capacitance | 1759.5 / 1658.2 / 283.4 mA at 10 ms; 1647.1 / 1546.9 / 252.2 at 20 ms; 1579.7 / 1480.1 / 233.5 at 50 ms | CALCULATED (`decomposition.json` `startup_ramp_candidate`) |
| Ramp increment at 10 ms | 224.64 / 222.66 / 62.40 mA | CALCULATED (SUP table) |
| One-rail-present tolerance, analog rails | +12 V alone ≤ 0.5 V; −12 V alone ≤ 6 V magnitude. At the fastest slopes this allows +12 V to lead by ≤ 0.41 ms and −12 V to lead by ≤ 4.92 ms | CALCULATED (A1), R-VEE |
| One-rail-present tolerance with +5 V present | The single analog rail stays below 8 V magnitude (≤ 6.50 ms of +12 V lead, ≤ 6.56 ms of −12 V lead at the fastest slopes). Bringing +5 V up last avoids the case | CALCULATED, R-SW; below 8 V isolation is not established by the source either. Derived for ADG5412FBRUZ before E13/E15; retained unchanged as a conservative row until OSC re-derives it for TMUX7412FRRPR and TMUX6112PWR (§7 R-SW) |
| "Both analog rails up" for the +5 V hold (PD B20 question, 2026-10-31) | **Definition 1 is sufficient for every PD-facing row:** +5 V ≤ 0.8 V until both analog rails exceed about 1.5 V magnitude, with the analog rails tracking. It satisfies three rows: one-rail-present with +5 V (the single rail stays below 8 V while +5 V is present), the P59-A conditional row, and the discharge rows. Definition 3 (source band) has **no OSC basis**: no OSC fact needs +5 V to wait for the analog source band. Definition 2 (±5 V) is the only supply-side way to hold ADG5412F IN low until its supplies reach the ±5 V specified minimum. OSC does **not** ask for it, because that gap belongs to OSC: it is #59 P59-C (`ENABLE_OK`). Until P59-C is adopted, the ADG5412F enable gap stays **OPEN on the OSC side** and is not a PD failure | CALCULATED, R-SW (`fact-fault-switch-supply-range` ±5 V minimum; `fact-fault-switch-logic-thresholds` VINL 0.8 V from the ±15 V table, conditional at ±12 V; `fact-fault-switch-power-off-ground` 8 V span). Derived for ADG5412FBRUZ before E13/E15; retained unchanged as a conservative row until OSC re-derives it for TMUX7412FRRPR and TMUX6112PWR (§7 R-SW). With TMUX7412F fail-safe logic (F7 PASS) the "ADG5412F enable gap" named here is closed for the jack inputs; the TMUX6112 SEL hold covers the envelope switches |
| *Only if the user chooses definition 2 before P59-C:* rows that would relax | (a) Shape: the common ramp then applies to ±12 V only, and +5 V starts once both analog magnitudes are ≥ 5 V, which is 4.10 ms into a 10 ms analog ramp. (b) Start skew: ≤ 0.41 ms applies to the ±12 V pair only. (c) Band-entry skew: about ≤ 3.9 ms instead of ≤ 2 ms. At 0.51 V/ms, +5 V reaches 4.81 V at 13.53 ms against −12 V band entry at 9.62 ms. (a) changes the CONTRACT W7 all-rails-together rule, so it is a **user decision**; (c) is a PROPOSED value | CALCULATED from the §5 slopes and load bands; CONTRACT change, not adopted |
| +5 V slope excursion (B20 SIM: 1.03 V/ms over a 0.01–0.4 V step) against the 0.51 V/ms limit | **No OSC part constrains it.** No promoted fact for a +5 V-rail part (HC logic, TLV75533P, NOISE2, TMUX7412F and TMUX6112 SEL) gives a supply-ramp limit. The 0.51 V/ms figure comes only from the CONTRACT ≥ 10 ms ramp rule. The OSC-side consequence is startup current: ≤ 120 µF × 1.03 V/ms = 124 mA capacitive during the step, against the 500 mA maximum and 400 mA transient minimum. The excursion still breaks the CONTRACT slope wording, so it needs a fix (PD) or an explicit owner exception. It is not a part hazard. For no-load starts the owner exception is now E21 (row below) | CALCULATED (§0 load capacitance and maximum); CONTRACT slope rule unchanged. The REF3433 slow-slew note in the unselected monitor candidates asks for faster, not slower, input slew, so it does not apply |
| No-load start-up step on −12 V and +5 V (owner decision E21, 2026-11-14; replaces the 2026-11-03 slope exceptions for B20 phase 10 §5d and the nominal +5 V no-load start) | **Recorded owner exception, stated as a current limit, not a slope.** No load only. **−12 V:** while \|−12 V\| ≤ 0.75 V, charging current ≤ 350 mA into any bank up to 180 µF. **+5 V:** while +5 V ≤ 0.45 V, charging current ≤ 180 mA into any bank up to 120 µF. No V/ms figure applies inside those regions. Conditions: (1) no load only; loaded starts keep 1.23 / 1.22 / 0.51 V/ms. (2) +12 V is on the common ramp during the step; the start-skew (≤ 0.41 ms) and one-rail rows are not relaxed. (3) Monotonic, with no reversal. After the step the rail may lead the ideal common tracking ramp by ≤ 0.25 V and may hold flat while the ramp catches up; it returns to the normal tracking difference within 15 ms of the ramp start. The band-entry skew row (≤ 2 ms) still applies. A 0.25 V lead is about 0.2 ms of ramp at 1.22 V/ms, inside the 0.41 ms start skew; a flat hold is slower, never faster. (4) Above the regions the base slope rows and every voltage-form skew row apply unchanged. Basis: no retained OSC datasheet gives a supply dV/dt, ramp-rate or charge limit (keyword review of the `circuit/sources/ic-library/` PDFs, 2026-11-14). Inside the regions every rail IC is below its recommended minimum: HC and LM393B 2 V, OPA4197 4.5 V span, LM13700 ±4.75 V, LF398 ±5 V, REF5050 5.2 V input, TMUX6112 10 V span, and TMUX7412F below UVLO (5.1 V minimum rising), where the datasheet treats it as powered off with Sx Hi-Z and logic ignored (SCDS404B §9.1, §9.3.2.2, §9.3.2.3); TMUX7412F is latch-up immune by construction (§9.3.2.6) and TMUX6112 meets 100 mA per JESD78. The step excursion is bounded by the region itself, so bypass current is C × dV/dt only (0.16 mA per 100 nF at 1.6 V/ms). 350 / 180 mA are 18 % / 45 % of the 1900 / 400 mA transient minimums and below the 2000 / 500 mA maxima. Not covered: injection from patched signals while the rails are low (R-INJ, #59) is independent of the step and stays open; the TMUX6112 SEL hold is bounded at 25 °C only. PD figures are simulation, not measurement | USER-CONFIRMED (E21 in `project/osc-hole-field/electrical-decisions.json`); bound values from §0; PD SIM figures from the zudo-pd D1 route note 2026-11-14 |
| OSC #59 P59-B (unadopted) load growth | If P59-B is adopted as patched (147 ADG5412F quads), the ledger requires a continuous minimum of **1800 / 1700 / 300 mA**, a transient of 2100 / 2000 / 400 mA, and a maximum above 2100 / 2000 mA (PROPOSED 2200 / 2100). The current §0 values hold only while P59-B is not adopted | CALCULATED by `build_supply_architecture.py` in a scratch trial; a CONTRACT change requires a user decision and PD agreement |
| Input-switch enable on a common ramp (TMUX7412FRRPR since E13/E15) | Below UVLO (VDD − VSS 5.1–6.4 V rising) the device is powered off: channels OFF, Sx Hi-Z and SEL ignored, with fail-safe logic up to +44 V (SCDS404B §9.1, §9.3.2.2, §9.3.2.3; s2b-protection-map F7 PASS). The former ADG5412F result, IN not guaranteed low while the supplies were below ±5 V, therefore no longer applies to the jack inputs. Between UVLO and the 8 V minimum span the state is not tabulated; load-side inhibited enables (#59) still cover it. Envelope TMUX6112 switches rely on the SEL hold (SEL ≤ VDD + 0.24 V at 25 °C) | CALCULATED, R-SW (`fact-fault-switch-t-logic-without-supply`, `fact-fault-switch-t-supply-range`, `fact-env-switch-t-sel-hold`); OSC #59 |
| Rail-to-rail ramp skew | Ramps start within ≤ 0.41 ms of each other, set by the +12 V-leading case above, and all rails enter their source bands within ≤ 2 ms of each other | Start skew CALCULATED (A1); band-entry skew PROPOSED |
| *If P59-A adopted:* one-rail-present tolerance and start skew | **+12 V lead:** no R-VEE limit for any duration. VEE5 ≤ +0.40 V while the clamp carries ≤ 10 mA, ≤ +0.50 V up to 30 mA. The next limit is R-SW: ≤ 6.50 ms of +12 V lead at the fastest slopes with +5 V present, and none from current OSC records if +5 V stays ≤ 0.8 V until both analog rails are present. **−12 V lead:** ≤ 0.69 ms on 10 ms tracking ramps (0.069 × ramp time: 1.38 ms at 20 ms, 3.45 ms at 50 ms). In voltage terms, −12 V magnitude ≤ 6 V until +12 V ≥ 5.2 V. This replaces the 4.92 ms one-rail figure, because the driver interval now governs. Unconditional values above are unchanged | CALCULATED (A1, A2), 25 °C only, UNADOPTED. Phase 10 candidate is P59-A rev 2 (`design/power/proposals-59/README.md`): a sink-only BAT54S series diode, a BAT54S clamp to AGND and a 10 kΩ bleed, with R_ISO kept at 100 Ω. The driver cannot source into VEE5 (≤ 2 µA reverse leakage, `fact-clamp-diode-reverse-current`). Remaining condition: the AS3340 supply current is ≤ 10 mA for the 0.40 V bound or ≤ 30 mA for the 0.50 V bound. The only source is `fact-vco-positive-supply-current`, a typical-table 6.5 mA maximum at +15 V, so this is not a guarantee. The rev 1 conditions on R_ISO power (P3) and VEE load (P4) are retired: the R_ISO, bleed and clamp dissipations are each ≤ 5 mW, and regulation keeps 5.14 V of headroom at a 7 mA sink current. Diagnostic simulation (TI OPAx197 model, conservative BAT54S VF envelope, official model NOT RETAINED): `design/power/proposals-59/p59a-skew-model.json`. Rev 2: 47/48 cases ran, all inside −6 V / +0.5 V, settling at −5.000 V at 6.5 and 10 mA; one case is NOT RUN (timeout). Rev 1, for comparison, settled at −4.68 V at a 6 mA load |
| Precondition | Any PD hold-up is charged before the outputs ramp | CONTRACT for a hold-up path (PCR R3) |
| Brownout during the ramp | All-rail shutdown (§3) | CONTRACT |

## 6. Contract detect before enable (D5-1 semantics)

1. With nothing attached, and through negotiation, all three OSC rails are disconnected
   and discharged (§3). AGND stays connected. (CONTRACT: PCR PD-003 condition 3, L2.)
2. **Accept** only a 20 V contract at the qualified current: 5 A with a 5 A e-marked
   cable recognized (E11). The paper floor is about 3.38 A at 20 V (PCR L4), but it rests
   on unvalidated efficiencies and is not an acceptance threshold. (CONTRACT decision;
   current threshold set by E11.)
3. **Refuse** any other result: a default 5 V attach, any other fixed PDO, 20 V below the
   qualified current, a cable that is not e-marked, or a failed negotiation. Refused
   means no OSC rail is enabled, with no reduced or partial mode. (CONTRACT, E12.)
   Refusal indication on the PD side is PROPOSED.
4. **Enable** all three rails together with the §5 ramp, only after acceptance and only
   once the PD internal rails are valid. OSC has no upstream power-good to wait for.
   (CONTRACT; inlet pin 4 is NC.)
5. **After enable**, any of these causes an all-rail shutdown treated as a power cycle,
   latched until re-plug, with no auto-retry: hard reset, renegotiation (including a
   request for the same PDO), a lower contract, charger or cable removal, VBUS brownout,
   any limiter trip, overvoltage, or a rail outside its band. (CONTRACT: PCR PD-003
   condition 3, W7. Including same-PDO renegotiation is a PROPOSED reading.)
6. Brownout timing: shut down before any rail leaves its source band, or within
   ≤ 1 ms of leaving it. (PROPOSED; the record has no number.)
7. OSC keeps its own load-side three-rail monitors and inhibited enables. These are
   independent of the PD decision and are open in OSC #59 (PCR G4, G12). Inlet-return
   integrity must be observable without relying on patch sleeves (PRO item 2). That is
   open, joint work.

## 7. Component-limit derivations from OSC owner bundles

The rail placement of each IC is taken from `design/spec/modules/io_partition.py`
(`rail_pins`), `oscillator.py` (VEE driver and AS3340 pins) and `noise.py`. Every fitted
package is still `placements: []` in the inventory. Bundle facts are cited by fact id
and are primary-source confirmed unless noted.

**Assumption A1** (narrowed, still not a bundle fact): an unregulated op-amp output stays
between its own supply pins. Phase 7 checked the retained OPA4197 datasheet. It describes
current-steering ESD diodes from the input and output pins to the internal supply lines
(`fact-op-precision-esd-steering`), but gives no clamp voltage and no output behaviour
below the 4.5 V (±2.25 V) recommended minimum (`fact-op-precision-supply-recommended`).
A1 therefore cannot be retired. The diode structure supports the direction of A1 for an
externally forced pin, but not its value.

**Assumption A2** (P59-A rows only): the BAT54S forward voltage rises monotonically with
current, so a current at or below a datasheet test point gives a VF at or below that
point's maximum (`fact-clamp-diode-forward-voltage`, 25 °C only). No VF maximum is
retained at any other temperature, so no P59-A figure covers temperature.

| Rule | Bundle fact | Project connection | Derived constraint |
| --- | --- | --- | --- |
| R-VEE | AS3340D `fact-vco-absolute-maximum-vee-to-ground` (VEE–GND −6 V / +0.5 V), `fact-vco-absolute-maximum-supply` (VCC–GND +18 / −0.5 V, VCC–VEE +24 / −0.5 V), `fact-vco-absolute-maximum-pins` (±40 mA any pin) | Pin 3 = VEE5, driven by an OPA4197 (precision role, ±12 V) through `VEE_ISO` 100 Ω and referenced to LOCAL_REFN5; pin 16 = +12V | With A1, an unregulated driver puts VEE5 anywhere between its rails. Hence +12 V alone ≤ 0.5 V and −12 V alone ≤ 6 V magnitude. At +12 V = 12 V a VEE5 short to the positive rail would push up to 115 mA through 100 Ω, above the ±40 mA pin limit, so the one-rail rule matters for current as well as voltage |
| R-DRV | OPA4197IPWR `fact-op-precision-supply-recommended` (≥ 4.5 V span, ±2.25 V); REF5050AIDR `fact-reference-input-recommended` (VIN ≥ VOUT + 0.2 V = 5.2 V) | The VEE driver needs both its supplies in range and the LOCAL_REFN5 reference, which REF5050 on +12 V generates | VEE5 regulation is within specified operation only once +12 V ≥ 5.2 V and the span is ≥ 4.5 V. Below that, R-VEE with A1 applies, and on a common ramp +12 V exceeds 0.5 V first. The interval is unavoidable from the supply side (§3) |
| R-SW (formerly R-ADG; this file previously cited ADG5412FBRUZ) | TMUX7412FRRPR `fact-fault-switch-t-supply-range` (VDD − VSS ≥ 8 V, VDD ≥ 5 V), `fact-fault-switch-t-logic-thresholds` (VIH ≥ 1.3 V, VIL ≤ 0.8 V), `fact-fault-switch-t-logic-without-supply`, `fact-fault-switch-t-supply-absolute`, `fact-fault-switch-t-pin-absolute`; TMUX6112PWR `fact-env-switch-t-supply-range` (span ≥ 10 V), `fact-env-switch-t-digital-input-absolute` (SEL ≤ VDD + 0.3 V), `fact-env-switch-t-sel-hold` | TMUX7412F: one package per jack input, VDD/VSS on ±12 V, pad 17 to AGND (E13/E15). TMUX6112: 12 envelope switches with a SEL hold on each SEL line | The discharged end state is both rails grounded with AGND present. Logic before supplies is supported (switch OFF). F6 (`design/readiness/s2b-protection-map.json`): +12 V missing with −12 V present is UNKNOWN, because VDD is below its 5 V minimum while the span can exceed UVLO; a −12 V-alone limit of 5 V magnitude (the falling UVLO minimum) is a candidate, not yet a PD requirement. The +5 V rows derived from ADG5412F (L104, L137, L138) are retained until this rule is re-derived |
| R-CLAMP | BAT54S,215 `fact-clamp-diode-reverse-voltage` (30 V), `fact-clamp-diode-forward-current-absolute` (IF 200 mA, IFSM 600 mA < 10 ms), `fact-clamp-diode-forward-voltage` (VF ≤ 240 mV at 0.1 mA … ≤ 800 mV at 100 mA, 25 °C) | Rail clamp pair, A = −12V, K = +12V (`electrical-standard.json` cells `high_impedance_input`, `summing_node_input`) | Rail-to-rail span < 30 V. A reversed span forward-biases every pair in series. The VF rows are maximum-only, so they bound voltage at a given current and cannot cap the current at a given reversal |
| R-SUP | `fact-vco-absolute-maximum-supply` (VCC–GND 18 V), `fact-reference-absolute-maximum` (VIN 18 V), `fact-sample-hold-absolute-maximum` (±18 V), `fact-ota-absolute-maximum` (36 V or ±18 V), `fact-comparator-absolute-maximum` (38 V), `fact-op-precision-supply-absolute` / `fact-op-audio-supply-absolute` (±20 V, 40 V), `fact-fault-switch-supply-absolute` (48 V); HC logic `fact-nand-`, `fact-schmitt-`, `fact-flipflop-`, `fact-one-shot-absolute-maximum` (VCC 7 V) | Rail placement as above; REF5050 input on +12 V; HC logic on +5 V | Ceilings: +12 V < 18 V, −12 V < 18 V magnitude, span < 30 V (R-CLAMP binds), +5 V < 7 V |
| R-REV | `fact-fault-switch-supply-absolute` (VDD–GND −0.3 V, VSS–GND +0.3 V), `fact-reference-absolute-maximum` (VIN −0.3 V), `fact-comparator-absolute-maximum` (VCC −0.3 V), `fact-vco-absolute-maximum-supply` (VCC–GND −0.5 V); HC `…-absolute-maximum` (VCC −0.5 V) | Same | Reverse excursion ≤ 0.3 V on ±12 V and ≤ 0.5 V on +5 V |
| R-INJ | OPA4197/4196 `…-input-absolute` (inputs (V−) − 0.5 V to (V+) + 0.5 V, ±10 mA); LM393B IIK −50 mA; HC IIK/IOK ±20 mA, ±50 mA per VCC/GND pin; ADG5412F Dx/IN 30 mA; AS3340 ±40 mA any pin; LM13700 inputs within the supplies | Back-feed paths while OSC is off | This is an OSC-side constraint, outside the PD interface. Example: an external 12 V on a precision output jack reaches OPA4197 IN− through the 100 Ω sense resistor (PCR R1). With the rails at 0 V, IN− may sit at most 0.5 V above V+, so the path would need (12 − 0.5) / 100 Ω = 115 mA against a 10 mA limit. Open in #59. The PD reverse-current proposal (§2) is unchanged |
| — | TMUX7412FRRPR `fact-fault-switch-t-source-overvoltage` (Sx fault ±60 V to GND, 85 V to supply or drain); `fact-fault-switch-t-fault-grounded-source-leakage` 125 µA typical at ±60 V with VDD = VSS = 0 V (no maximum) | Source pins | Source-pin feature only; not a rail or system rating |
| — | Bulk GRM21BR61E475KA12L `fact-c-bulk-rated-voltage` 25 Vdc; bypass GRM188R71H104KA93D `fact-c-bypass-rated-voltage` 50 Vdc (Murata catalogue) | Every rail | Both are above the 18 V per-rail ceiling. The catalogue gives no polarity or reverse-voltage statement, so capacitor reverse tolerance does not constrain R-REV either way |
| — | Discretes: BAS16GW-QX 100 V repetitive peak reverse; 2N7002,215 VDS 60 V; MMBT3904/3906 VCEO ±40 V; C0G 50 V (C0805C103, C0603C101, C0603C102) | Signal and control paths | All above the 30 V clamp ceiling; they do not tighten it |
| — | Kingbright APG1005SEC/E-T 25 mA, APHHS1005QWF/D 30 mA DC forward current abs max | LEDs driven from op-amp outputs through resistors | No supply-voltage limit follows |

Facts still missing. The ICs below have retained PDFs, but none of them states these facts:

| Part (rail) | Missing fact | Status |
| --- | --- | --- |
| OPA4197IPWR, OPA4196IDR candidate | Output behaviour below the 4.5 V minimum supply, and the ESD diode clamp voltage. This is what retires A1 | Not stated in the retained datasheets; needs a vendor answer or a bench test |
| OPA4197IPWR | Output swing to the rails | In the retained datasheet, not promoted (it would tighten R-DRV) |
| AS3340D | VEE pin current and the Zener characteristics while the driver is unregulated | Supply guidance promoted as text (`fact-vco-negative-supply-guidance`); no Zener tolerance or VEE pin current table |
| NOISE2 (+5 V via 22 Ω) | Any supply abs max or reverse limit | The retained source gives only the 5 V pin function |
| GRM21BR61E475KA12L, GRM188R71H104KA93D | Polarity, reverse-voltage tolerance, DC-bias | Not in the Murata catalogue responses; PDF datasheet downloads returned HTML or 404 (2026-10-31), so it stays SOURCE UNAVAILABLE |
| TMUX7412FRRPR | Guaranteed ±12 V tables (RON is tabulated at ±15 V and 12 V single supply only); the state with VDD = 0 V and VSS present (F6); behaviour of undisturbed channels while another input of the package is in fault | Not stated in the retained datasheet. Packing stays one package per input |
| Kingbright APG1005SEC/E-T, APHHS1005QWF/D | Reverse-voltage rating | Not promoted |
| BAT54S,215 (P59-A only) | VF maxima away from 25 °C; official SPICE model | The retained PDF has typical curves only, at 25, 85 and 125 °C (`fact-clamp-diode-forward-voltage-temperature`). The Nexperia model download was refused (HTTP 403, 2026-10-31), so the model is NOT RETAINED |
| AS3340D (P59-A) | Guaranteed supply and VEE pin current at +12 V / −5 V | Only a typical-table 6.5 mA maximum at +15 V with the internal Zener at 20 °C (`fact-vco-positive-supply-current`) |

## Open gates this file does not close

- L7: TVS2200 against the STUSB4500 28 V abs max, 0.00 / −0.35 V margin. **Blocking.**
- R7 / G3 / G4: the limiter that enforces the maximum, reverse blocking and all-rail
  shutdown.
- L6 / G6 / G7: source bands and ripple, NOT RUN.
- G9 / G10: input path and thermal, NOT RUN.
- G12: contract detection and the shutdown circuit, OPEN.
- The §7 missing facts. A1, the driver interval (an OSC-side #59 item) and the remaining
  PROPOSED trip, discharge and timing values still depend on them.

Physical qualification remains in OSC #57.
