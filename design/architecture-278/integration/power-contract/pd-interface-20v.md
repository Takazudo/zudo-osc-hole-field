# OSC–PD interface contract for the 20 V / 5 A revision

**UNVALIDATED DRAFT interface record.** It is derived from OSC records only. It
selects no part and changes no OSC requirement, schematic, PCB, BOM or zudo-pd file.
Nothing here is measured. It applies the owner decision of 2026-10-31 11:11Z (decision
card): PWR-D3 = D3-A (20 V / 5 A PD revision, 5 A e-marked cable) and PWR-D5 = D5-1
(no degraded mode; accept or refuse). Those are electrical decisions E11/E12 in
`project/osc-hole-field/electrical-decisions.json`. Prepared 2026-10-31.

Each value has one class:

- **CONTRACT**: an existing OSC requirement, quoted with its source.
- **CALCULATED**: arithmetic on CONTRACT values. It is not a measurement.
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

The record says the exact thresholds and timing are **UNSOURCED** (PRO item 4).
Everything numeric below is therefore PROPOSED unless marked otherwise.

| Item | Value | Class / source |
| --- | --- | --- |
| Shutdown action order | Disconnect all three rail paths, then actively discharge all three rails. AGND is never opened | CONTRACT (PRO items 3–4; SAI `fault_policy`) |
| Stored energy to remove at the ceiling | 13.62 / 13.40 / 1.56 mJ (180 / 180 / 120 µF at 12.30 / 12.20 / 5.10 V) | CALCULATED |
| Discharge level | Each rail magnitude ≤ 0.6 V | PROPOSED |
| Discharge time | All three rails at or below that level ≤ 100 ms after the shutdown decision, at ceiling capacitance and zero load | PROPOSED |
| Disconnect skew | All three rail paths open within ≤ 1 ms of each other | PROPOSED |
| Discharge skew | No rail stays above 50 % of its source-band minimum for more than 10 ms after any other rail falls below that level | PROPOSED; targets the AS3340 VEE −6 V and partial-rail risks (PCR PWR-C1, R1–R3) |
| Re-enable | Only from the discharged state (all rails at or below the discharge level) | PROPOSED |
| Detection-to-disconnect time, and injection charge per pin during it | Must be stated by the design; no OSC value | CONTRACT obligation (PRO item 4); value UNSOURCED |

## 4. Surge envelope at the OSC inlet

| Item | Value | Class / source |
| --- | --- | --- |
| Steady state while enabled | Inside the source band, ripple included | CONTRACT |
| Turn-on overshoot, load-step response and shutdown transients | Inside the source band. The record has no separate overshoot allowance; any allowance above the band is a contract change | PROPOSED reading of the CONTRACT band |
| Overvoltage shutdown | All-rail shutdown if any inlet rail magnitude exceeds 12.48 / 12.37 / 5.20 V (the load-band maxima) | PROPOSED; the record requires overvoltage protection (SAI `fault_cases[3]`) with no threshold |
| Reverse-polarity excursion on any rail | ≤ 0.3 V of reverse polarity, measured at the inlet | PROPOSED; OSC abs-max facts are not retained (PCR Q-A item 1) |
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
| Rail-to-rail ramp skew | Ramps start within ≤ 1 ms of each other, and all rails enter their source bands within ≤ 2 ms of each other | PROPOSED; the record has the rule, not a number |
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

## Open gates this file does not close

- L7: TVS2200 against the STUSB4500 28 V abs max, 0.00 / −0.35 V margin. **Blocking.**
- R7 / G3 / G4: the limiter that enforces the maximum, reverse blocking and all-rail
  shutdown.
- L6 / G6 / G7: source bands and ripple, NOT RUN.
- G9 / G10: input path and thermal, NOT RUN.
- G12: contract detection and the shutdown circuit, OPEN.

Physical qualification remains in OSC #57.
