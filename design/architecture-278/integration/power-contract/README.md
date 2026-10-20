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
- Ownership: OSC holds this combined record; zudo-pd #218 holds supply findings. The PD
  owner's capability screening replaces `supply-input.json` when it lands.

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

## Gap list

| ID | Area | Gap | Owner | Status |
| --- | --- | --- | --- | --- |
| G1 | Input | Continuous, normal and transient demand against 42–45 W through the current chain | Product decision | OPEN, needs owner |
| G2 | Regulation | LDO rows end at 1.5 A; U2/U3/U4 current limits and efficiency at OSC currents | zudo-pd #218 | FAIL on rows; full screen pending |
| G3 | Protection | PTC1/PTC3 hold below continuous requirement; no device enforces the interface maximum | zudo-pd #218 | FAIL |
| G4 | Fault policy | OSC requires reverse blocking, coordinated all-rail shutdown and rail monitors; Board B ties LDO SHDN to IN and has no reverse blocking | Joint (OSC #52/#59, PD) | OPEN |
| G5 | Startup | 10 ms soft start and 150 / 150 / 100 µF (+20 %) ceilings against Board B start-up; PD notes U4 start may draw ~4.5 A for ≥ 2 ms against the 3 A contract; no cross-rail sequencing | Joint | NOT RUN |
| G6 | Voltage band | PD screens are wider than OSC source bands on all three rails, before PTC drop | Joint | OPEN |
| G7 | Ripple | 1 mVpp at load has no PD-side evidence | PD | NOT RUN |
| G8 | Distribution | 4.6 A worst return contact, 0.2 V rail+return loss, PTC R1max drop, J6/J7/J10/J11 contacts and the unselected OSC inlet connector | Joint | OPEN |
| G9 | Input path | Cable, J1, Board P Q1 AO3401A at 3 A and VBUS header losses ahead of Board B | PD | NOT RUN |
| G10 | Thermal | LDO dissipation at OSC currents; cooling plate is planned, not qualified | PD | NOT RUN |
| G11 | Demand | Complete typical, guaranteed maximum and OTA/mirror allocation remain unknown | OSC | OPEN |

## Decision record

| ID | Decision | Authority | Status |
| --- | --- | --- | --- |
| PWR-D1 | One shared ledger; OSC holds the combined record, PD holds supply findings and links here | Owner brief | ADOPTED |
| PWR-D2 | Requirements stay 1700 / 1600 / 300 and 2000 / 1900 / 400 mA; Stage54 is not booked | Routine (rule reproduces) | ADOPTED |
| PWR-D3 | Supply direction: the present 15 V Board B cannot carry the OSC contract; choose between a larger PD revision (higher input contract with Board P change, and/or no LDO post-regulation), a separate premium supply, or revisiting the OSC contract through demand closure | Owner | OPEN; quantified options follow PD #218 |

Checks for this record: `ledger.py --check` PASS; 6 focused tests PASS (normal and
`-O`); `verify_pd_pin.py` PASS against a local zudo-pd checkout at the pinned commit.
ERC, DRC, native KiCad export, simulation and any physical measurement: NOT RUN (no
schematic or PCB change).
