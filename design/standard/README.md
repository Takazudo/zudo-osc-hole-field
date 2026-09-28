# OSC-ES-1 electrical proposal

Authority is **PROPOSAL (planning, owner-delegated)**. These remain design inputs, not captured circuits, accepted system behavior, or manufacturing data. Issues #15, #18 and #21 retained source bytes, audited selected pin maps, ran draft cell checks, and promoted exact component evidence into the generated catalogue.

- `electrical-standard.json`: named role-to-part mapping, signal limits, 19 functional cell definitions, remote-control/island and calibration contracts, and explicit disposition of all fourteen planning defaults.
- `parts-shortlist.json`: 36 exact shared-family representatives. Blank supplier codes and `UNVERIFIED` availability are intentional. A listed identity does not establish factory stock.
- `rail-budget-preliminary.json`: planning module counts, conservative additions, package rounding, load assumptions and arithmetic. **The negative rail exceeds its design ceiling by 72.655 mA.**
- `source-receipts.json`: primary PDF byte receipts used for amplifier current choices and the retained Analog Devices Rev. C ADG5412F source. The exact selected identities and source facts are promoted in #21's component owner bundles.
- `../../project/osc-hole-field/electrical-decisions.json`: E01–E09. Existing D01–D12 remain untouched.

Run `python3 design/standard/check_standard.py` from any directory. A consistency pass includes an explicit over-budget finding; it does not certify a passing rail budget. It checks IDs, exact-family references, cell parts/values, amplifier allocation arithmetic, ideal threshold/gain/RC/fault calculations and truthful budget flags.

Cell terminals are functional names. The #21 component owner records map numeric symbol/footprint pins to #15 and #29's retained manufacturer evidence. ALFA RPAR's retained 2020 v.7 PDF confirms AS3340D SOIC-16 identity and pin functions; schematic nets, supply suitability, oscillator behavior, calibration, physical fit, and procurement remain open. Cells request amplifier roles; do not embed amplifier MPNs in Python cell implementations.

Passive entries are exact shortlist series representatives in one shared owner bundle. The generated catalogue publishes the real `RC0603FR-07100KL` record as that bundle's landing page; the other ten exact representative MPNs remain separate inventory/owner records. A 100 kohm representative is not the orderable MPN for a 10 kohm resistor. No pseudo family MPN or per-value expansion is introduced; unknown order codes remain open.

## Work note

Requested: decide the instrument-wide electrical standard and downstream contract. Initial `regen-all.sh` and `pnpm circuit:check` passed, with no tracked regeneration. Inventory and integration rules were empty; CAD checking was disabled. Read the imported R21 contracts and the planning size/current table, then recomputed a deliberately conservative package budget with every additional input, reference, remote-pot, wiper and indicator buffer charged explicitly.

The design adds source-facing power-off isolation, lowers bulk amplifier quiescent current, reduces the 48 DC pot loads, specifies factory calibration and keeps sensitive nodes local. No panel geometry, imported handoff, generated component page, or sibling-owned document was edited.

Remaining work includes AS3340D commercial orderability, full electrical/supply suitability and physical fit, exact Murata lifecycle/evidence gaps, the Fenghua exact-MPN gap, manufacturer/model and bench checks for precision-output stability, module capture, #24 power-off/rail sequencing and startup, #29 octave error and oscillator calibration, #33 a netlist-derived budget, and #34 resolving the 72.655 mA preliminary negative-rail deficit before #35 partition. The ADG5412F project-supply fault response/current budget, physical fit, cable stability, thermal behavior and procurement remain open. Full site build belongs to the manager's merged-base guarded verification.
