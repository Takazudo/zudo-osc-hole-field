# Combined OSC + zudo-pd power contract: ledger and decision record

**Unvalidated draft. Arithmetic only.** No measured, guaranteed or simulated
whole-instrument demand or source capacity exists; every such field is `null`, and
no converter efficiency is booked. Canonical OSC schematic, PCB, BOM, placement,
`decision.json` and `KEEP_K1402_INCUMBENT` are unchanged. No zudo-pd file is edited.

- OSC base: `e1969027e63dfc22da1dbca07bf64e8778b122dd` (Stage54, PR #287 / Issue #278)
- zudo-pd read at `65031f98f02677998efada217f64e731d39437f7`; quoted values and source
  hashes are in `supply-input.json`
- Rebuild: `python3 design/architecture-278/integration/power-contract/ledger.py` (`--check` verifies)
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
| L3 | The 20 ms transient cannot close on 20 V / 3 A: the 2.81 A continuous draw leaves a ±3.2 % limiter window, and the best retrieved limiter is ±3.7 %. The USB-PD Peak Current windows of at most 10 ms agree with the specification as I know it, but PD's citation is a secondary mirror (G-U) | Agree; record the citation class |
| L4 | Under the unchanged contract, 20 V / 5 A (100 W, 5 A e-marked cable) is the smallest PD contract that closes the transient at every assumed efficiency. 20 V / 3.25 A (65 W) also needs a 5 A cable and passes only at base efficiency | C2 is the minimum robust choice |
| L5 | The transient requirement is mostly the 10 ms full-capacitance ramp. The contract sets 10 ms as a minimum soft start; re-deriving the transient for a longer soft start (for example 50 ms gives about 1.8 / 1.7 / 0.4 A) would bring it to about 2.78–2.99 A at 20 V / 3 A, still marginal against 3 A. That is a change to an OSC contract value and is not adopted | Possible OSC-side question only, not a supply-side option |
| L6 | Source bands fail with the converters' internal references on every option; terminal sense plus a precision servo is a new circuit for C2 too. Ripple (1 mVpp) and the 2 mV / 1 mV precision gates remain NOT RUN and are not relaxed | Gates stay open |
| L7 | TVS2200 against STUSB4500: 0.00 / −0.35 V margin, plus the CC 22 V margin; the alternative controllers are out of stock or not in production stock. R7 (interface maximum, all-rail shutdown, reverse blocking) is unresolved for every option | Blocking before adoption |
| L8 | PD notes the final lineup edits were not re-reviewed | Re-review before the owner decision is recorded as adopted |

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
| PWR-D5 | Whether OSC gets an explicit degraded mode for lower-capability supplies (functional loss and new power domains) or full OSC requires a supply meeting the contract | Owner | OPEN; candidate only |

Checks for this record: `ledger.py --check` PASS; 8 focused tests PASS (normal and
`-O`); `verify_pd_pin.py` PASS against a local zudo-pd checkout at both pinned commits.
ERC, DRC, native KiCad export, simulation and any physical measurement: NOT RUN (no
schematic or PCB change).
