# Combined OSC + zudo-pd power contract: ledger and decision record

**Unvalidated draft. Arithmetic only.** No measured, guaranteed or simulated
whole-instrument demand or source capacity exists; every such field is `null`, and
no converter efficiency is booked. Canonical OSC schematic, PCB, BOM, placement,
`decision.json` and `KEEP_K1402_INCUMBENT` are unchanged. No zudo-pd file is edited.

- OSC base: `e1969027e63dfc22da1dbca07bf64e8778b122dd` (Stage54, PR #287 / Issue #278)
- zudo-pd read at `65031f98f02677998efada217f64e731d39437f7`; quoted values and source
  hashes are in `supply-input.json`
- Rebuild: `python3 design/architecture-278/integration/power-contract/ledger.py`, then `decompose.py` (`--check` verifies each)
- PD quotation check: `python3 design/architecture-278/integration/power-contract/verify_pd_pin.py <zudo-pd checkout>`
  (read-only `git show` at the pinned commit; prints NOT RUN without a checkout)
- PD capability screen: zudo-pd draft PR #219 `6071e1757c7678a4b5ed0af069a9eae202c6ee2d`,
  `manufacturing/supply-capability.json` (sha256 `e5864272…2b8d`), quoted under
  `pd_capability_screen`; `verify_pd_pin.py` checks it when that commit is fetched
- Ownership: OSC holds this combined record; zudo-pd #218 holds supply findings.

## Demand states (mA, +12 / −12 / +5 V)

| State | Classification | +12 V | −12 V | +5 V |
| --- | --- | --- | --- | --- |
| Reported typical subtotal | TYPICAL, partial | 857.198 | 790.698 | 80.273 |
| Normal planning (canonical) | PLANNING | 1534.819 | 1435.569 | 224.286 |
| Normal planning with Stage54 cleanup | CONDITIONAL, unadopted | 1492.819 | 1393.569 | 224.286 |
| Startup envelope, 10 ms soft start | Conservative envelope | 1759.459 | 1658.229 | 286.686 |
| Normal plus one bounded fault | PLANNING | 1559.819 | 1460.569 | 224.286 |
| Continuous requirement | CONTRACT | 1700 | 1600 | 300 |
| Transient requirement, 20 ms | CONTRACT envelope | 2000 | 1900 | 400 |
| Interface maximum (current-limit ceiling) | CONTRACT limit | 2100 | 2000 | 500 |

Every row reproduces committed evidence (`rail-budget.json`,
`supply-architecture(-input).json`, Stage54 `accounting.json`). The builder re-checks
the brief's numbers and the continuous rule (normal × 1.1, rounded up to 100 mA).
With Stage54 the rule still gives 1700 / 1600 / 300 mA: **the cleanup does not change
the source requirement.** The startup row and the transient requirement stack reserve,
capacitance ramp (150 / 150 / 100 µF nominal + 20 %) and fault allowances; they are
contract envelopes, not simultaneous operating points. The OTA/mirror overlap (26 IABC
feeds) stays unallocated, with no rebate against the 233 mA/rail reserve.

## Power against the input boundary

Input budgets from PD `power-budget.json`: 45 W nominal (15 V × 3 A), 42.75 W at
−5 % source, and 42 W at PD's own 14 V Board B screen. Cable, J1, Board P Q1 and the
VBUS header losses sit ahead of Board B and are not booked.

*Any architecture* uses OSC source-band voltages. *Current PD chain* is a lower bound
valid while U2/U3/U4 regulate: each LDO draws at least its output current from a
pre-rail no lower than PD's screened minimum (13.220 / 13.484 / 6.055 V), with
lossless converters and no ground, divider or LED current.

| State | OSC inlet W | Any architecture, efficiency needed at 45 / 42 W | Current chain pre-rail W (lower bound) | Current chain, converter efficiency needed at 45 / 42 W |
| --- | --- | --- | --- | --- |
| Normal planning | 36.78–37.54 | 81.7 % / 87.6 % | ≥ 41.00 | 91.1 % / 97.6 % |
| Stage54 conditional | 35.77–36.51 | 79.5 % / 85.2 % | ≥ 39.88 | 88.6 % / 95.0 % |
| Continuous requirement | 41.12–41.96 | 91.4 % / 97.9 % | ≥ 45.86 | **> 100 % (FAIL)** |
| Transient requirement | 48.82–49.82 | **> 100 % (FAIL)** | ≥ 54.48 | **> 100 % (FAIL)** |

Using PD's own U4 model (≤ 82.1 %, conduction losses only, so optimistic), the positive
converters would need 101.1 % at 45 W for normal planning (95.4 % with Stage54) and
over 100 % at 42 W. That model is a PD screen, not a guarantee.

## Ratings screen (guaranteed-class rows; LDO rows are UNSOURCED under PD policy)

| Rail | Continuous req. | Output PTC hold, 25 °C | PTC trip | LDO table rows end | Result |
| --- | --- | --- | --- | --- | --- |
| +12 V | 1.7 A | 1.5 A (PTC1) | 3.0 A | 1.5 A | Exceeds hold and LDO rows |
| −12 V | 1.6 A | 1.5 A (PTC3; 0.77 A at 85 °C) | 3.0 A | 1.5 A | Exceeds hold and LDO rows |
| +5 V | 0.3 A | 1.1 A (PTC2) | 2.2 A | 1.5 A | Within |

No PTC trip current enforces the 2.1 / 2.0 / 0.5 A interface maximum. PTC3 R1max
(0.13 Ω) alone drops 0.208 V at 1.6 A, as wide as the whole OSC −12 V source band.

## Cross-check with the PD capability screen (#219)

- U4's guaranteed-minimum switch current limits −12 V to **1.217 A** (1.222 A even at a
  lossless 42 W input). Every OSC planning, conditional and requirement state exceeds it.
- PTC1 holds 1.5 A at 25 °C. Canonical normal planning (1.535 A external) exceeds it;
  the Stage54 conditional row (1.493 A) does not. Indicator LEDs sit before the PTC.
- PTC3 holds 0.77 A at 85 °C, below even the PD 0.8 A target (PD FAIL).
- **Efficiency discrepancy, recorded rather than averaged:** PD reports 88.6 % (15 V) /
  95.0 % (14 V) for "planning normal"; this ledger reports 91.1 % / 97.6 %. The cause is
  the demand basis. The brief quoted 1.493 / 1.394 / 0.224 A as planning normal, but
  those are the unadopted Stage54 conditional loads; PD probed them. This ledger's
  Stage54 row gives 88.6 % / 95.0 %, matching PD. Canonical planning normal is
  1.535 / 1.436 / 0.224 A and governs. The residual difference is small and comes
  from PD's indicator/feedback current and floor terms.

## Findings

1. **The present Board B fails the continuous requirement two independent ways**:
   output PTC holds and LDO rating rows end below 1.7 / 1.6 A, and LDO post-regulation
   alone needs ≥ 45.86 W against a 42–45 W input.
2. **Normal planning very likely fails too.** It needs ≥ 91.1 % aggregate converter
   efficiency at 45 W (97.6 % at 42 W); PD's optimistic U4 model already rules that out.
3. **No converter at 15 V / 3 A meets the 20 ms transient contract from the input
   alone.** It requires 48.82 W at source-band voltage. USB-PD peak-current overload
   windows are shorter than 20 ms (spec knowledge, not repository evidence), and stored
   energy would need sequencing that Board B does not have.
4. The canonical planning demand exceeds the unmeasured PD targets 1200 / 800 mA by
   334.8 / 635.6 mA (292.8 / 593.6 mA with Stage54).

## Voltage bands (screens, not measurements)

| Rail | OSC source band | OSC load band | PD conditional output | Inside source band |
| --- | --- | --- | --- | --- |
| +12 V | 12.00–12.30 V | 11.53–12.48 V | 11.526–12.477 V | Not demonstrated; minimum already below load band |
| −12 V | 12.00–12.20 V | 11.74–12.37 V | 11.741–12.370 V | Not demonstrated; maximum 0.1 mV above load band |
| +5 V | 5.05–5.10 V | 4.81–5.20 V | 4.815–5.196 V | Not demonstrated |

PD intervals are its whole-chain conditional screens before PTC and cable drop. The OSC
bands and the 1 mVpp ripple-at-load criterion are OSC contract values; neither side is
relaxed here.

## Review of PD-002 supply alternatives

Reviewed zudo-pd#218 PD-002 / PR #219 `8cb38bbbaf90609fa2f516cb558cf91acfb69cf5`
(`manufacturing/supply-alternatives.md`) against this ledger. Integration review only;
the option choice remains PWR-D3.

| ID | Finding | Effect |
| --- | --- | --- |
| R1 | Load basis is canonical; Stage54 is labelled conditional | OK |
| R2 | External power uses 12 / 12 / 5 V; the OSC source bands reach 12.3 / 12.2 / 5.1 V (continuous 41.96 W, not 41.10 W) | B1 continuous input current rises about 2 %, to about 2.61–2.82 A |
| R3 | Transient path (b) needs a sink input limit whose minimum stays above the continuous input current (about 2.82 A) and whose maximum stays at or below 3 A, a window of about ±3 %; the hold-up must also be charged before the outputs ramp, which needs sequencing | Path (b) is not demonstrated; the hold-up arithmetic itself reproduces (about 0.9 mF at 18.67 to 17.67 V) |
| R4 | The 2 mV / 1 mV precision criteria are kept as gates (no relaxation), but the OSC supply contract's 1 mVpp ripple at load, the 12.00–12.30 / 12.00–12.20 / 5.05–5.10 V source bands and the 0.2 V rail plus return loss are not screened; PTC drop outside the loop is 0.17–0.20 V | Add as gates for every no-LDO option |
| R5 | "Keep 15 V" requires lowering the OSC continuous requirement below canonical planning normal | Inadmissible as a supply-side choice; only demand closure can change the requirement |
| R6 | B1 replaces the preserved 15 V / 3 A / 45 W boundary and needs a 60 W or larger 20 V-capable charger | Product decision for the owner; the TVS clamp versus the STUSB4500 28 V absolute maximum must close before adoption |
| R7 | No proposed device enforces the OSC 2.1 / 2.0 / 0.5 A interface maximum (PTC trip 5 A, switch limit 6.3 A); the OSC requirement for coordinated all-rail shutdown and reverse blocking is not addressed | G3 / G4 stay open under every option |

## Lower-capability supplies: demand-side conditions (PD-003)

This separates what full OSC requires from what a lower-capability supply could do
safely. It changes no requirement.

1. **Full OSC needs the canonical contract.** A supply whose guaranteed continuous or
   20 ms transient capability is below 1.7 / 1.6 / 0.3 A or 2.0 / 1.9 / 0.4 A is not an
   OSC-compatible supply, whatever the adapter's wattage. A low-output model can still
   be a valid PD supply for lighter products.
2. **OSC demand cannot be throttled by the supply.** It is dominated by quiescent and
   rail-to-rail resistor current in one EXT domain with no switchable sections. Limiting
   current at the source therefore produces brownout, which the OSC fault policy forbids
   (monitors at load, coordinated all-rail shutdown, no partial supply). "Adaptive
   current" at the source can only choose between enabling OSC fully or not at all.
3. **Safe behaviour on an insufficient contract:** detect the negotiated PDO before
   enabling any OSC rail; enable only when it covers both the continuous and the
   transient requirement; on renegotiation, a lower contract, charger removal or
   brownout, shut all rails down together; treat a charger change as a power cycle.
4. **A degraded OSC mode would be a new product decision.** It needs switchable power
   domains with their own all-rail sequencing, backfeed protection between powered and
   unpowered sections (the existing missing-rail and unplugged-board fault cases apply),
   and panel indication. The planning demand that would have to be switched off, using
   PD-002's maximum continuous outputs (efficiencies assumed):

| PD-002 capability (+12 / −12 V, +5 V at 0.3 A) | Planning reduction needed (+12 / −12 V) | Equivalent functions |
| --- | --- | --- |
| 15 V floor, low: 1400 / 1320 mA | 262.1 / 235.6 mA | about 4.2 oscillators or 4.5 envelopes |
| 15 V floor, high: 1490 / 1400 mA | 180.3 / 162.8 mA | about 2.9 oscillators or 3.1 envelopes |
| 15 V ideal, high: 1600 / 1510 mA | 80.3 / 62.8 mA | about 1.3 oscillators or 1.4 envelopes |

Per-module planning values are in `ledger.json` `low_power_supply_screen`. The 20 ms
transient requirement still applies in any degraded mode unless it is re-derived from
the reduced demand.

## Review of PD-003 product lineup

Reviewed zudo-pd#218 PD-003 / PR #219 `2bd418e` (`manufacturing/b1-gates.md`,
`manufacturing/product-lineup.md`). Integration review only.

| ID | Finding | Effect |
| --- | --- | --- |
| L1 | Canonical loads and source-band voltages are used; PWR-D4 holds. Independent re-computation with PD-002's assumed efficiencies gives 2.60–2.79 A continuous and 3.09–3.32 A transient at an 18.4–18.67 V board input, matching PD's 2.61–2.81 / 3.10–3.35 A | Reproduced |
| L2 | Accept-or-refuse is the only adaptive behaviour admitted for OSC; the low SKU is not an OSC supply; a degraded mode stays OSC decision PWR-D5 and never a supply feature | Consistent with the lower-capability conditions above |
| L3 | The 20 ms transient cannot close on 20 V / 3 A: the 2.81 A continuous draw leaves a ±3.2 % limiter window, and the best retrieved limiter is ±3.7 %. The USB-PD Peak Current windows of at most 10 ms agree with the specification as I know it, but PD's evidence is secondary (TI E2E quote and a Linux patch mirror; specification text not retrieved) | Agree; record the citation class |
| L4 | Corrected after PD `99ea307` / `2eacc68`: the transient needs a 20 V contract of at least about 3.38 A (about 68 W) with a 5 A e-marked cable; 100 W is a consequence of choosing PDO2 = 20 V / 5 A, not a demand floor. 20 V / 3.5 A (70 W) leaves about 0.15 A at the −5 pt assumed efficiencies (worst transient about 3.35 A at an 18.22 V board input); that path has no sink limiter, so the ±3.7 % limiter tolerance does not stack, but the margin is only about 4 % against unvalidated efficiencies, and STUSB4500 NVM encoding of 3.5 / 4 A is unconfirmed. 20 V / 3.25 A (65 W) passes only at base efficiency | 20 V / 5 A remains the most robust; 3.5 / 4 A are viable only after efficiency evidence and NVM confirmation |
| L5 | The transient requirement is mostly the 10 ms full-capacitance ramp. The contract sets 10 ms as a minimum soft start; re-deriving the transient for a longer soft start (for example 50 ms gives about 1.8 / 1.7 / 0.4 A) would bring it to about 2.78–2.99 A at 20 V / 3 A, still marginal against 3 A. That is a change to an OSC contract value and is not adopted | Possible OSC-side question only, not a supply-side option |
| L6 | Source bands fail with the converters' internal references on every option; terminal sense plus a precision servo is a new circuit for C2 too. Ripple (1 mVpp) and the 2 mV / 1 mV precision gates remain NOT RUN and are not relaxed | Gates stay open |
| L7 | TVS2200 against STUSB4500: 0.00 / −0.35 V margin, plus the CC 22 V margin; the alternative controllers are out of stock or not in production stock. R7 (interface maximum, all-rail shutdown, reverse blocking) is unresolved for every option | Blocking before adoption |
| L8 | PD notes the final lineup edits were not re-reviewed | Re-review before the owner decision is recorded as adopted |

## Budget decomposition (owner request, zudo-pd #218)

Requested in [zudo-pd#218 comment 6284861864](https://github.com/Takazudo/zudo-pd/issues/218#issuecomment-6284861864).
`decompose.py` writes `decomposition.json` by classifying every one of the 347 rows of
`design/power/rail-ledger.json`. The basis text of each row is kept in that file, and
the input sha256 values are recorded under `inputs_sha256` (OSC base `e1969027`).

Status of the numbers:
- Everything here is **CALCULATED** and **UNVERIFIED**.
- Nothing is **MEASURED**: there is no whole-instrument or module current measurement.
- No requirement changes. A lower level is at most a candidate operating range for PWR-D5.

### Parts of the canonical planning budget

All values are mA, given as +12 V / −12 V / +5 V.

| Part | Planning | Typical | Varies with |
| --- | --- | --- | --- |
| IC quiescent (OPA4197/4196 at full-temperature max Iq, ADG5412, LM13700, LM393, AS3340D, LF398, NOISE2) | 1035.5 / 963.0 / 10.0 | 676.8 / 623.4 / 5.0 | Nothing the user does (LM13700 IABC partly control-dependent, see Q3) |
| HC logic packages | 0 / 0 / 87.0 | 0 / 0 / 34.8 | Clock and trigger rate (Q5) |
| Static resistive and reference paths (REF5050, trims, enable feeds, dividers) | 23.6 / 4.9 / 7.2 | 16.5 / 3.4 / 3.7 | Nothing |
| Coarse reserves (233 mA per analog rail, plus the 5 V conditioning reserve) | 233 / 233 / 30 | 122 / 122 / 15 | Fixed or unallocated. It contains 26 mA per rail of verified nominal trim current; the rest also covers feedback, signal pots and clamp transients (Q4) |
| Inlet, protection, reference and logic allowances | 34.7 / 26.7 / 49.4 | 30.7 / 26.7 / 31.4 | Nothing |
| Internal signal paths (clamp feeds, fold feedback, command, summing and local resistor paths) | 27.8 / 27.8 / 0 | 4.7 / 4.7 / 0 | Signal level; no user notice bounds them |
| Patch and indicators (output and jack loads, magnitude and clip LEDs) | 174.2 / 174.2 / 0 | 30.3 / 30.3 / 0 | Patching and signal level |
| Operation and state (FOLD/LEVEL drive, stage LEDs, pull-ups, contacts) | 6.0 / 6.0 / 40.7 | 1.3 / 1.3 / 19.5 | Knobs, buttons and logic state |
| **Canonical planning** | **1534.8 / 1435.6 / 224.3** | | |
| Rule (×1.1, rounded up to 100 mA) → continuous requirement | +165.2 / +164.4 / +75.7 | | |
| Startup ramp and one fault → 20 ms transient | +300 / +300 / +100 | | Startup only (soft start and capacitance) |

**What the decomposition shows:**
- **Most of the budget does not depend on what the user does.** 86 / 86 / 82 % of canonical planning is fixed or unallocated reserve: quiescent current, static paths, reserves and allowances. Without the reserves the fixed share is still about 71 % on the analog rails.
- **"All knobs at maximum" does not give maximum consumption.** All operation-dependent rows together are 6 / 6 / 41 mA. Patch and indicator rows are 174 / 174 / 0 mA, and internal signal paths 28 / 28 / 0 mA.
- **Double counting found in the rows:**
  - The rows themselves state only 3.3 mA on +5 V as impossible: one-hot stage LEDs charged for both states.
  - Some LM393 rows say their −12 V charge is never drawn, but Stage54 `clip_comparator_accounting` confirms pin 4 on −12 V for every row that charges it (A01–A06, M4A/B, M5A/B). That charge stays, and their typical −12 V rises by 10 mA. The H, O and E comparator rows book 0 mA on −12 V, which may under-book (Q2).
- **Jack loads and magnitude LEDs draw from one rail at a time.** Clip LEDs, feedback, summing, clamp and differential drive paths load both rails at once.
  - This lowers total power by up to 1.96 W at nominal.
  - It does not lower per-rail current, because every output can hold a positive control voltage at once. Stage54 `simultaneity` likewise says there is no blanket halving.
- **The largest unverified margin is the spread between maximum and typical Iq:** 358.7 / 339.6 / 57.2 mA.
  - It mixes guaranteed full-temperature maxima (OPA419x) with unverified planning allowances (ADG5412 extrapolated to ±12 V, HC logic, NOISE2, LM13700), some of which could be exceeded. It is not double counting.
  - It cannot be credited without a measured distribution.
  - The reserves are second (233 → 122 typical), pending operating-point measurement.

### Demand levels

| Level | mA (+12 / −12 / +5) | Rail output W, nominal / source-band max | ×1.1 rule | Class |
| --- | --- | --- | --- | --- |
| Normal typical | 882.5 / 821.9 / 109.4 | 21.0 / 21.4 | — | CALCULATED, UNVERIFIED (typical rows are partly assumptions) |
| Heavy realistic patch | 1534.8 / 1435.6 / 221.0 | 36.7 / 37.5 (34.8 nominal with one rail at a time) | 1700 / 1600 / 300 | CALCULATED, UNVERIFIED |
| Canonical planning | 1534.8 / 1435.6 / 224.3 | 36.8 / 37.5 | 1700 / 1600 / 300 | PLANNING (governs) |
| Explicit usage limit (candidate) | 1386.2 / 1287.0 / 203.0 | 33.1 / 33.8 | 1600 / 1500 / 300 | CANDIDATE, CALCULATED, UNVERIFIED |
| Startup worst envelope (capacitance ceiling) | 1759.5 / 1658.2 / 286.7 | 42.4 / 43.3 | — | CONSERVATIVE ENVELOPE |
| Startup with fitted capacitance | 1609.5 / 1498.2 / 239.6 | 38.5 / 39.3 | — | CALCULATED, UNVERIFIED; not a contract value |
| Continuous requirement | 1700 / 1600 / 300 | 41.1 / 42.0 | — | CONTRACT, unchanged |
| 20 ms transient requirement | 2000 / 1900 / 400 | 48.8 / 49.8 | — | CONTRACT, unchanged |

**Explicit usage limit:** fixed parts and internal signal paths stay at planning, and the patch, indicator and operation rows are held to typical (indicators near typical brightness, outputs into roughly 100 kΩ loads).
- This is the most any patch-based usage notice can remove: about 149 / 149 / 21 mA.
- If adopted, the continuous rule would give 1600 / 1500 / 300 mA, only one 100 mA step below the requirement. That is a **candidate re-basing for PWR-D5**, not a requirement.
- The user enforces it, and the supply cannot detect a violation.
- Reaching the limit must still be met by an all-rail refusal or shutdown. A low probability of occurrence is not a PASS.

### 60 W-class input

- **Rail output power is not charger input power.** Input = rail output ÷ end-to-end efficiency, which covers the converters, LDO headroom, cable and PDO. No efficiency is booked here.
- **Any architecture:**
  - 60 W covers the continuous requirement only at ≥ 69.9 % end-to-end efficiency (≥ 73.6 % at 57 W, source −5 %).
  - It covers the 20 ms transient only at ≥ 83.0 % (≥ 87.4 %).
- **Current LDO chain (Board B pre-rails at their PD-screened minima, from `ledger.json`):**
  - The continuous requirement needs ≥ 45.86 W of pre-rail power, so the converters must reach ≥ 76.4 % efficiency (80.5 % at 57 W).
  - The 20 ms transient needs ≥ 54.48 W, so the converters must reach ≥ 90.8 % (95.6 % at 57 W).
  - PD screened about 85 % at its own lighter targets.
  - Inference: at that efficiency the transient corresponds to roughly 64 W at the charger. This matches the owner's 64 W example, but it is not a measured or adopted figure.
- **The excess over 60 W is startup, not patching.** The transient adds 300 / 300 / 100 mA above continuous, and that is mostly the 10 ms full-capacitance ramp. A usage notice cannot reduce it. Only OSC hardware can: slower soft start, sequencing or less capacitance (PD-003 L5). Any of those changes an OSC contract value and needs the owner.

**Startup with fitted capacitance:** the ceiling row charges 150 / 150 / 100 µF (+20 %) at the 10 ms minimum soft start, adding 224.6 / 222.7 / 62.4 mA. The OSC owner reports 49.9 / 42.2 / 24.5 µF fitted (all MLCC, +5 V including NOISE_VDD 4.7 µF; Q6), which adds 74.7 / 62.6 / 15.3 mA. The contract keeps the ceiling, so capacitance may still be added up to it, and the transient requirement is unchanged.

### Circuit facts from the OSC owner (Q1–Q6, relayed by the coordinator, source at `e1969027`)

| ID | Answer | Effect here |
| --- | --- | --- |
| Q1 | 92 magnitude paths sit in BAS16GW-QX bridges: the positive half draws +12 V → 5.6 kΩ → AGND, the negative half sinks into the −12 V-side op-amp. 10 clip LEDs run +12 V → 22.1 kΩ → LED → LM393 open collector | Confirms the one-rail-at-a-time set; clip LEDs stay on both rails |
| Q2 | 44 LM393s, pin 8 on +12 V. Pin 4 on AGND for 24 (U107/U207, O1–O5, E1–E6) and on −12 V for 20 (A01–A06, M4A/B, M5A/B) | The 0 mA −12 V booking of the H/O/E rows is correct; no change |
| Q3 | LM13700 IABC values are nominal (filter 0.49–506 µA derived, RES 0–100 µA, DRY 0–403 µA, envelope 0.49–500 µA, MIX4 0–500 µA, wavefolder 0–403 µA in its own row) | Overlap with reserves stays unallocated; no credit |
| Q4 | Only the 26 mA per rail of trim is stated as fixed; no source splits the rest | Reserves stay as booked |
| Q5 | 87 mA is a fixed 6 × 29 × 0.5 mA allowance; NOISE2 10 mA is an example value; no maximum trigger rate is stated | No change |
| Q6 | Fitted 49.9 / 42.2 / 19.6 µF (24.5 µF on +5 V with NOISE_VDD), far below the ceiling; no soft start, inrush limiting, sequencing or power-good is implemented | New fitted-capacitance startup row |

## Review of the PD 60 W-class screen

Reviewed zudo-pd PR #219 `7bb2e0a85069d4acca95a4b214c77d6494cad55d` (`manufacturing/power-limit-60w.md`). Integration review only.

| ID | Finding | Effect |
| --- | --- | --- |
| W1 | PD quotes the decomposition rows from `17fd746` unchanged and keeps the OSC record values as the verification record | Agree |
| W2 | R60 caps (1.60 / 1.50 / 0.28 A) carry the OSC usage-limit candidate demand (1.386 / 1.287 / 0.203 A), but not its ×1.1 rule result (1.6 / 1.5 / 0.3 A): +5 V 0.3 > 0.28 A, and the total is EDGE on the LTC4282 basis. Above the heavy realistic patch, R60 leaves about 4 % on ±12 V where the OSC rule asks for 10 % | Using R60 for OSC means dropping or refining the OSC reserve and rounding rule. That is an OSC contract change for PWR-D5, not a supply-side choice |
| W3 | Startup envelope 42.4 W (12 / 12 / 5 V) / 43.3 W (source-band maximum) matches this record; PD's non-fit against every safe trip holds for the ceiling row. With fitted capacitance (1.610 / 1.498 / 0.240 A), +12 V exceeds the R60 LTC4282 cap by about 10 mA and −12 V is about 2 mA inside; the INA301 reference caps (1.66 / 1.56 / 0.29 A) carry it on paper | Fitted row is EDGE, not PASS; full OSC still needs the ceiling |
| W4 | The OSC contract sets a 10 ms **minimum** soft start (`supply-architecture-input.json` `soft_start_min_ms`) and no maximum (confirmed by the OSC owner; see PWR-C1). PD reads it as a ceiling ("reach their bands within the OSC 10 ms"). A slower common source ramp is inside the contract as written and scales the ramp term down (20 ms halves it). What OSC must still answer for W60-D3: all-rails-together tolerance of a longer ramp, since no staged enable or power-good exists | Correct L6 wording; W60-D3 narrows to OSC tolerance |
| W5 | The 90.8 % converter efficiency in this record applies to the current LDO chain; PD's screen uses the switcher-direct candidate with assumed efficiencies (transient 3.11–3.35 A against 3.0 A). Both conclude the 20 ms transient does not fit 60 W | Consistent |
| W6 | M1 accepts on a 20 ms moving average. Peaks shorter than 20 ms are what a trip sees; accepting on the average alone would hide them | Add a peak criterion over the trip's own blanking window |
| W7 | Latching all-rail off, re-plug reset, no auto-retry, no hold-up first, and sequenced start flagged against the all-rails-together rule match the PD-003 conditions | Agree |

The lineup recommendation (C2 as the full-OSC basis; C1-L only for a light SKU until the startup fits and M1–M3 data exist) relaxes no OSC limit.

## Slower common startup ramp: OSC answers to the PD questions (Q-A to Q-C)

Asked by the PD owner after the owner's [zudo-pd#218 comment 6285348769](https://github.com/Takazudo/zudo-pd/issues/218#issuecomment-6285348769). Candidate only (PWR-C1). Calculated, unverified, no requirement changed.

**Q-C Scaling model.** The PD model is acceptable as a screen. The steady part is the heavy realistic patch, and capacitor charging scales as 10 ms ÷ ramp time. Three conditions apply:
- **The ramp is linear and monotonic, and judged by its maximum slew.** The model takes the maximum dV/dt as V/T. A soft start that is faster at first (RC-shaped or stepped) must be judged by its steepest part. An interrupted ramp is a separate case.
- **The fitted row assumes no capacitance is added.** It holds only while the fitted capacitance stays at or below 49.9 / 42.2 / 24.5 µF. The 150 / 150 / 100 µF contract ceiling still governs any full-OSC source.
- **Taking the full steady load during the ramp is conservative.** Loads draw less at reduced voltage.

Startup rows, mA (`decomposition.json` `startup_ramp_candidate`):

| Ramp | Ceiling capacitance | Fitted capacitance |
| --- | --- | --- |
| 10 ms | 1759.5 / 1658.2 / 283.4 | 1609.5 / 1498.2 / 236.3 |
| 20 ms | 1647.1 / 1546.9 / 252.2 | 1572.2 / 1466.9 / 228.6 |
| 50 ms | 1579.7 / 1480.1 / 233.5 | 1549.8 / 1448.1 / 224.0 |

On the fitted basis, keeping +12 V at or below 1.60 A needs a ramp of at least 11.47 ms. This reproduces the PD figures (≥ 11.5 ms; 1.573 A at 20 ms).

**Q-B Separation.** A slower ramp only changes the startup inrush row. The following stay unchanged and are judged separately even if startup fits on paper:
- the 20 ms transient requirement (2.0 / 1.9 / 0.4 A, built from the ceiling ramp plus one fault and rounding);
- the continuous requirement and its ×1.1 reserve with 100 mA rounding (PWR-D5);
- the source bands, 1 mVpp ripple, 2 mV / 1 mV precision, and the interface maximum.

Re-deriving the transient from a slower ramp or from fitted capacitance would be an OSC contract change for the owner.

**Q-A Longest acceptable ramp: there is no circuit-derived ceiling and tolerance is unverified, so the campaign must be extended.**

The contract sets no upper bound; it requires a monotonic ramp no faster than 10 ms (`osc-electrical-standard.mdx` L113). The OSC owner's circuit-side answer is from `a4d7cca` on `e1969027`.

The AR reset is the only timing element found:
- **Circuit:** +5 V feeds 100 kΩ and 1 µF to AGND, with a discharge diode, two HC14 stages and two HC74 synchronous-release stages (`design/spec/modules/envelope.py` L157–162). The 1 µF has no MPN, so the 100 ms time constant has unknown tolerance.
- **Thresholds:** HC14 thresholds are held only at VCC = 4.5 V. Below 4.5 V, behaviour is unknown during any ramp, whatever its length.
- **Arithmetic estimate (not in source):** release is about 37–98 ms after a +5 V step. On a slow ramp the RC lags the rail, so reset releases after +5 V settles.
- **Unaddressed:** ±12 V entering its band late.
- **Not proven:** the source says this circuit is not brownout supervision (`osc-block-ar.mdx` L264–265), and real RC/reset behaviour is NOT RUN (L307–309). REF5050 startup and LM393 undervoltage output state are not in the repo.

The PD campaign (6 rail orders × 10 / 20 / 50 ms: VEE5, injection, reset timing, latch-up) is incomplete. These items must be added; each is required by an OSC source:
1. **Facts to capture first:** abs-max, injection and latch-up for LM13700, OPA4197/4196, LM393, LF398, ADG5412F, REF5050 and HC00/HC14/HC74/HC221. ADG5412F leakage is stated not to apply to floating or ramping rails, and AS3340 has only VEE −6 V recorded.
2. **Failure cases:** the 6 failure orders, brownout and hiccup, all-rail disconnect, and the post-discharge off state with AGND never opened (`osc-protection-architecture.mdx` L73).
3. **Missing rail and ground:** a single rail permanently missing, and ground loss (`osc-supply-architecture.mdx` L103, `osc-standard-cells.mdx` L42, `osc-block-osc.mdx` L35).
4. **Wiring faults and restart:** miswiring and offset wiring, open ground, startup retry, thermal hold and trip, discharge and restart (`osc-supply-architecture.mdx` L107).
5. **Back-feed while off:** from external patching (including through output resistors and sense paths), a partial supply, and a removed receiving board (`osc-supply-architecture.mdx` L105, `osc-reference-fanout.mdx` L29, `osc-standard-cells.mdx` L575, `verification/osc-slew-test-plan.mdx` L23).
6. **Output-short recovery** without latch-up (`osc-electrical-standard.mdx` L59).
7. **Supply side:** synth-side ripple, cable drop, current and thermal rise (`osc-power.mdx` L89).
8. **Power-on states:**
   - LF398 (`osc-sample-hold-slew.mdx` L98);
   - AR single trigger when the gate is high at reset release (`osc-block-ar.mdx` L261–262, L276);
   - MIX4 sequencing (`osc-block-mix4.mdx` L53);
   - LM393 output and LED states.
9. **Ramp-specific checks:**
   - AR release at 20 / 50 ms ramps, with ±12 V early and late;
   - AS3340 VEE and the OPA4197 VEE driver in every order;
   - −5 V reference fanout injection into its 30 inputs;
   - input-switch enable and sync validity while +5 V is absent.
10. **Model check:** supply current during the ramp, to validate the Q-C model.

There is no staged-enable circuit yet, so every test runs on the current three-converter supply.

## Gap list

| ID | Area | Gap | Owner | Status |
| --- | --- | --- | --- | --- |
| G1 | Input | Continuous, normal and transient demand against 42–45 W through the current chain | Product decision | OPEN, needs owner |
| G2 | Regulation | LDO rows end at 1.5 A; U4 switch-current ceiling 1.217 A on −12 V; efficiency at OSC currents has no evidence | zudo-pd #218/#219 | FAIL |
| G3 | Protection | PTC1 hold below canonical normal and continuous; PTC3 below continuous at 25 °C and 0.77 A at 85 °C; no device enforces the interface maximum | zudo-pd #218/#219 | FAIL |
| G4 | Fault policy | OSC requires reverse blocking, coordinated all-rail shutdown and rail monitors; Board B ties LDO SHDN to IN and has no reverse blocking | Joint (OSC #52/#59, PD) | OPEN |
| G5 | Startup | 10 ms soft start and 150 / 150 / 100 µF (+20 %) ceilings against Board B start-up; PD notes U4 start may draw ~4.5 A for ≥ 2 ms against the 3 A contract; no cross-rail sequencing | Joint | NOT RUN |
| G6 | Voltage band | PD screens are wider than OSC source bands on all three rails, before PTC drop | Joint | OPEN |
| G7 | Ripple | 1 mVpp at load has no PD-side evidence | PD | NOT RUN |
| G8 | Distribution | 4.6 A worst return contact, 0.2 V rail+return loss, PTC R1max drop, J6/J7/J10/J11 contacts and the unselected OSC inlet connector | Joint | OPEN |
| G9 | Input path | Cable, J1, Board P Q1 AO3401A at 3 A and VBUS header losses ahead of Board B | PD | NOT RUN |
| G10 | Thermal | LDO dissipation at OSC currents; cooling plate is planned, not qualified | PD | NOT RUN |
| G11 | Demand | Complete typical, guaranteed maximum and OTA/mirror allocation remain unknown | OSC | OPEN |
| G12 | Low-capability supply | Contract detection before enable, renegotiation/removal/brownout all-rail shutdown, and any degraded-mode domain switching | Joint (PD-003) | OPEN |

## Decision record

| ID | Decision | Authority | Status |
| --- | --- | --- | --- |
| PWR-D1 | One shared ledger; OSC holds the combined record, PD holds supply findings and links here | Owner brief | ADOPTED |
| PWR-D2 | Requirements stay 1700 / 1600 / 300 and 2000 / 1900 / 400 mA; Stage54 is not booked | Routine (rule reproduces) | ADOPTED |
| PWR-D3 | Supply direction: the present 15 V Board B cannot carry the OSC contract; choose between a small in-product revision, a larger PD revision (for example 20 V input with Board P change), or a separate supply | Owner | OPEN; PD-002 requests it; integration review R1–R7 above |
| PWR-D4 | The brief's 1.493 / 1.394 / 0.224 A "planning normal" is the Stage54 conditional row; canonical 1.535 / 1.436 / 0.224 A governs comparisons | Routine (evidence) | ADOPTED |
| PWR-D5 | Whether OSC gets an explicit degraded mode for lower-capability supplies (functional loss and new power domains) or full OSC requires a supply meeting the contract | Owner | OPEN; candidate only. The usage-limit candidate (1600 / 1500 / 300 mA by the same rule) is in "Budget decomposition" |
| PWR-C1 | **Candidate, not a decision:** a slower common source ramp (20–50 ms). It is contract-compatible: the contract requires a monotonic ramp no faster than 10 ms and sets no upper bound (`osc-electrical-standard.mdx` L113, `decisions/osc-supply-architecture.mdx` L65; OSC owner answer from `31311c6`). The ramp term scales as CΔV/Δt: at 20 / 50 ms the ceiling ramp is 112.3 / 44.9 mA on +12 V (10 ms: 224.6) and the fitted ramp 37.4 / 14.9 mA (10 ms: 74.7). Correct OSC behaviour on a slow ramp is **unverified**: the AR reset RC (100 ms) is not brownout supervision and is untested on slow rails (`osc-block-ar.mdx` L258–265), the oscillators need each-rail-first/last, slow-ramp and brownout tests (`osc-block-osc.mdx` L35), and the all-orders staged enable has no circuit (`osc-protection-architecture.mdx` L72–73). Named risks: AS3340 VEE–GND −6 V abs max, the OPA4197 VEE driver, −5 V reference fanout and +5 V-absent logic. Abs-max and latch-up facts for LM13700, OPA4197/4196, LM393, LF398 and HC are not retained. Needs measurement (6 orders × 10 / 20 / 50 ms, VEE5, injection, reset release, latch-up), after the abs-max facts are captured | OSC owner, then product owner | CANDIDATE; UNVERIFIED; transient requirement unchanged |

Checks for this record: `ledger.py --check` and `decompose.py --check` PASS; 15 focused
tests PASS (normal and `-O`); `verify_pd_pin.py` PASS against a local zudo-pd checkout at both pinned commits.
ERC, DRC, native KiCad export, simulation and any physical measurement: NOT RUN (no
schematic or PCB change).
