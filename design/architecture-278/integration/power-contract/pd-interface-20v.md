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
| End state | Both analog rails grounded (discharged) with AGND present; this is the isolated state the ADG5412F source requires | CALCULATED, R-ADG (`fact-fault-switch-power-off-ground`); level not given by the source |
| Discharge time | All three rails at or below that level ≤ 100 ms after the shutdown decision, at ceiling capacitance and zero load | PROPOSED |
| Disconnect skew | All three rail paths open within ≤ 1 ms of each other | PROPOSED |
| Discharge skew, analog rails | No state with +12 V > 0.5 V while −12 V is absent, and none with −12 V magnitude > 6 V while +12 V is absent. Both rails therefore fall together, and neither may lead the other out | CALCULATED (A1), R-VEE |
| Discharge skew, +5 V | No state with +5 V above 0.8 V, one analog rail absent and the other at ≥ 8 V magnitude. +5 V must therefore fall to ≤ 0.8 V no later than the first analog rail leaves | CALCULATED, R-ADG; the 0.8 V VINL maximum is from the ±15 V table, so it is conditional at ±12 V |
| Driver interval: both rails present but VEE5 regulation not within specified operation | Exists on every common ramp and discharge, for +12 V between 0.5 V and 5.2 V (REF5050 minimum input). That is 0.41–4.23 ms of a 10 ms ramp, 0.81–8.46 ms of 20 ms and 2.03–21.1 ms of 50 ms. No supply-side ramp, skew or discharge order removes it | CALCULATED (A1), R-DRV. OPEN on the OSC side (#59): it needs an OSC-side bound on VEE5, not a PD number |
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
| Reverse-polarity excursion, ±12 V | ≤ 0.3 V of reverse polarity on either analog rail (ADG5412FBRUZ VDD–GND −0.3 V and VSS–GND +0.3 V; also REF5050AIDR VIN and LM393BIDR VCC −0.3 V) | CALCULATED, R-REV |
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
| One-rail-present tolerance with +5 V present | The single analog rail stays below 8 V magnitude (≤ 6.50 ms of +12 V lead, ≤ 6.56 ms of −12 V lead at the fastest slopes). Bringing +5 V up last avoids the case | CALCULATED, R-ADG; below 8 V isolation is not established by the source either |
| ADG5412F enable on a common ramp | On a common ramp +5 V passes the 0.8 V VINL maximum at 15.7 % of the ramp, and the analog rails reach the ±5 V minimum supply at 40.7–41.0 %. IN is therefore not guaranteed low while the switch supplies are below their specified range. This is covered by the existing OSC requirement for load-side inhibited input enables (#59), not by a PD sequencing change, which the all-rails-together rule forbids | CALCULATED, R-ADG (`fact-fault-switch-logic-thresholds`, `fact-fault-switch-supply-range`); OSC #59 |
| Rail-to-rail ramp skew | Ramps start within ≤ 0.41 ms of each other, set by the +12 V-leading case above, and all rails enter their source bands within ≤ 2 ms of each other | Start skew CALCULATED (A1); band-entry skew PROPOSED |
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

| Rule | Bundle fact | Project connection | Derived constraint |
| --- | --- | --- | --- |
| R-VEE | AS3340D `fact-vco-absolute-maximum-vee-to-ground` (VEE–GND −6 V / +0.5 V), `fact-vco-absolute-maximum-supply` (VCC–GND +18 / −0.5 V, VCC–VEE +24 / −0.5 V), `fact-vco-absolute-maximum-pins` (±40 mA any pin) | Pin 3 = VEE5, driven by an OPA4197 (precision role, ±12 V) through `VEE_ISO` 100 Ω and referenced to LOCAL_REFN5; pin 16 = +12V | With A1, an unregulated driver puts VEE5 anywhere between its rails. Hence +12 V alone ≤ 0.5 V and −12 V alone ≤ 6 V magnitude. At +12 V = 12 V a VEE5 short to the positive rail would push up to 115 mA through 100 Ω, above the ±40 mA pin limit, so the one-rail rule matters for current as well as voltage |
| R-DRV | OPA4197IPWR `fact-op-precision-supply-recommended` (≥ 4.5 V span, ±2.25 V); REF5050AIDR `fact-reference-input-recommended` (VIN ≥ VOUT + 0.2 V = 5.2 V) | The VEE driver needs both its supplies in range and the LOCAL_REFN5 reference, which REF5050 on +12 V generates | VEE5 regulation is within specified operation only once +12 V ≥ 5.2 V and the span is ≥ 4.5 V. Below that, R-VEE with A1 applies, and on a common ramp +12 V exceeds 0.5 V first. The interval is unavoidable from the supply side (§3) |
| R-ADG | ADG5412FBRUZ `fact-fault-switch-power-off-ground`, `fact-fault-switch-logic-thresholds` (VINH ≥ 2.0 V, VINL ≤ 0.8 V at ±15 V), `fact-fault-switch-supply-range` (±5 V to ±22 V), `fact-fault-switch-supply-absolute`, `fact-fault-switch-pin-absolute` | VDD/VSS (pins 13/4) on ±12 V; IN from +5 V through 1 kΩ with 100 kΩ pull-down (PCR R2) | Forbid +5 V above 0.8 V with one analog rail absent and the other at ≥ 8 V. The discharged end state is both rails grounded with AGND present. On a common ramp IN is not guaranteed low while the supplies are below ±5 V; OSC inhibited enables (#59) must cover this |
| R-CLAMP | BAT54S,215 `fact-clamp-diode-reverse-voltage` (30 V), `fact-clamp-diode-forward-current-absolute` (IF 200 mA, IFSM 600 mA < 10 ms), `fact-clamp-diode-forward-voltage` (VF ≤ 240 mV at 0.1 mA … ≤ 800 mV at 100 mA, 25 °C) | Rail clamp pair, A = −12V, K = +12V (`electrical-standard.json` cells `high_impedance_input`, `summing_node_input`) | Rail-to-rail span < 30 V. A reversed span forward-biases every pair in series. The VF rows are maximum-only, so they bound voltage at a given current and cannot cap the current at a given reversal |
| R-SUP | `fact-vco-absolute-maximum-supply` (VCC–GND 18 V), `fact-reference-absolute-maximum` (VIN 18 V), `fact-sample-hold-absolute-maximum` (±18 V), `fact-ota-absolute-maximum` (36 V or ±18 V), `fact-comparator-absolute-maximum` (38 V), `fact-op-precision-supply-absolute` / `fact-op-audio-supply-absolute` (±20 V, 40 V), `fact-fault-switch-supply-absolute` (48 V); HC logic `fact-nand-`, `fact-schmitt-`, `fact-flipflop-`, `fact-one-shot-absolute-maximum` (VCC 7 V) | Rail placement as above; REF5050 input on +12 V; HC logic on +5 V | Ceilings: +12 V < 18 V, −12 V < 18 V magnitude, span < 30 V (R-CLAMP binds), +5 V < 7 V |
| R-REV | `fact-fault-switch-supply-absolute` (VDD–GND −0.3 V, VSS–GND +0.3 V), `fact-reference-absolute-maximum` (VIN −0.3 V), `fact-comparator-absolute-maximum` (VCC −0.3 V), `fact-vco-absolute-maximum-supply` (VCC–GND −0.5 V); HC `…-absolute-maximum` (VCC −0.5 V) | Same | Reverse excursion ≤ 0.3 V on ±12 V and ≤ 0.5 V on +5 V |
| R-INJ | OPA4197/4196 `…-input-absolute` (inputs (V−) − 0.5 V to (V+) + 0.5 V, ±10 mA); LM393B IIK −50 mA; HC IIK/IOK ±20 mA, ±50 mA per VCC/GND pin; ADG5412F Dx/IN 30 mA; AS3340 ±40 mA any pin; LM13700 inputs within the supplies | Back-feed paths while OSC is off | This is an OSC-side constraint, outside the PD interface. Example: an external 12 V on a precision output jack reaches OPA4197 IN− through the 100 Ω sense resistor (PCR R1). With the rails at 0 V, IN− may sit at most 0.5 V above V+, so the path would need (12 − 0.5) / 100 Ω = 115 mA against a 10 mA limit. Open in #59. The PD reverse-current proposal (§2) is unchanged |
| — | ADG5412FBRUZ `fact-fault-switch-source-pin-overvoltage-protection` ±55 V; `fact-fault-switch-floating-off-leakage` 10 µA typical (no maximum) | Source pins | Source-pin feature only; not a rail or system rating |
| — | Bulk GRM21BR61E475KA12L `fact-c-bulk-rated-voltage` 25 Vdc; bypass GRM188R71H104KA93D `fact-c-bypass-rated-voltage` 50 Vdc (Murata catalogue) | Every rail | Both are above the 18 V per-rail ceiling. The catalogue gives no polarity or reverse-voltage statement, so capacitor reverse tolerance does not constrain R-REV either way |
| — | Discretes: BAS16GW-QX 100 V repetitive peak reverse; 2N7002,215 VDS 60 V; MMBT3904/3906 VCEO ±40 V; C0G 50 V (C0805C103, C0603C101, C0603C102) | Signal and control paths | All above the 30 V clamp ceiling; they do not tighten it |
| — | Kingbright APG1005SEC/E-T 25 mA, APHHS1005QWF/D 30 mA DC forward current abs max | LEDs driven from op-amp outputs through resistors | No supply-voltage limit follows |

Facts still missing. The ICs below have retained PDFs, but none of them states these facts:

| Part (rail) | Missing fact | Status |
| --- | --- | --- |
| OPA4197IPWR, OPA4196IDR candidate | Output behaviour below the 4.5 V minimum supply, and the ESD diode clamp voltage. This is what retires A1 | Not stated in the retained datasheets; needs a vendor answer or a bench test |
| OPA4197IPWR | Output swing to the rails | In the retained datasheet, not promoted (it would tighten R-DRV) |
| AS3340D | VEE pin current and the Zener characteristics while the driver is unregulated | The supply-guidance text only; no table |
| NOISE2 (+5 V via 22 Ω) | Any supply abs max or reverse limit | The retained source gives only the 5 V pin function |
| GRM21BR61E475KA12L, GRM188R71H104KA93D | Polarity, reverse-voltage tolerance, DC-bias | Not in the Murata catalogue responses; PDF datasheet downloads returned HTML or 404 (2026-10-31), so it stays SOURCE UNAVAILABLE |
| ADG5412FBRUZ | VINL/VINH at ±12 V (only the ±15 V, ±20 V, 12 V and 36 V tables exist) and maximum floating leakage | The datasheet has typical floating leakage only |
| Kingbright APG1005SEC/E-T, APHHS1005QWF/D | Reverse-voltage rating | Not promoted |

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
