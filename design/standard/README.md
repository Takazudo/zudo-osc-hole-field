# OSC-ES-1 electrical proposal

Authority is **PROPOSAL (planning, owner-delegated)**. These are design inputs for issues #15 and #18, not captured circuits, accepted component evidence, or manufacturing data.

- `electrical-standard.json`: named role-to-part mapping, signal limits, 19 functional cell definitions, remote-control/island and calibration contracts, and explicit disposition of all fourteen planning defaults.
- `parts-shortlist.json`: 36 exact shared-family representatives. Blank supplier codes and `UNVERIFIED` availability are intentional. A listed identity does not establish factory stock.
- `rail-budget-preliminary.json`: planning module counts, conservative additions, package rounding, load assumptions and arithmetic. **The negative rail exceeds its design ceiling by 72.655 mA.**
- `source-receipts.json`: primary PDF byte receipts used for amplifier current choices, plus an honest unavailable-byte record for ADG5412F. These are planning receipts; #15/#21 own formal evidence promotion.
- `../../project/osc-hole-field/electrical-decisions.json`: E01–E09. Existing D01–D12 remain untouched.

Run `python3 design/standard/check_standard.py` from any directory. A consistency pass includes an explicit over-budget finding; it does not certify a passing rail budget. It checks IDs, exact-family references, cell parts/values, amplifier allocation arithmetic, ideal threshold/gain/RC/fault calculations and truthful budget flags.

Cell terminals are functional names. Only the retained manufacturer pin maps from #15 may turn them into numeric symbol/footprint pins. Cells request amplifier roles; do not embed amplifier MPNs in Python cell implementations.

Passive entries represent a series at one complete MPN. A 100 kohm series representative must never be instantiated as the orderable MPN for a 10 kohm resistor. Resolve each specified value/tolerance/power rating to its own full MPN during the exact-part library/evidence work. All circuit values are fixed here; unknown order codes remain unknown.

## Work note

Requested: decide the instrument-wide electrical standard and downstream contract. Initial `regen-all.sh` and `pnpm circuit:check` passed, with no tracked regeneration. Inventory and integration rules were empty; CAD checking was disabled. Read the imported R21 contracts and the planning size/current table, then recomputed a deliberately conservative package budget with every additional input, reference, remote-pot, wiper and indicator buffer charged explicitly.

The design adds source-facing power-off isolation, lowers bulk amplifier quiescent current, reduces the 48 DC pot loads, specifies factory calibration and keeps sensitive nodes local. No panel geometry, imported handoff, generated component page, or sibling-owned document was edited.

Remaining work: #15 exact pin/source/library and sourcing audit; #18 model/ERC validation; module capture; #24 power-off/rail sequencing and startup; #29 octave error and oscillator calibration; #33 actual netlist budget; #34 at least 72.655 mA negative-rail reduction before #35 partition. Simulation, hardware, cable-stability and thermal results are absent. Full site build belongs to the manager's merged-base guarded verification. Downstream issue edits and epic comment are staged separately for the manager and remain pending until applied.
