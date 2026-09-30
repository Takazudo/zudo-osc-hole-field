# Issue 48 work note

Requested result: choose a concrete conditional supply architecture while preserving 33 modules and 438 centres, and retain physical source qualification outside draft completion.

Inputs: merged #51 ledger and #47 selector assembly, original #24/#48 issue bodies, pinned zudo-pd source lock, OSC-ES-1. Baseline `pnpm circuit:check` passed (42 manual inventory lines, no schematic/placement binding); initial full regeneration changed no tracked files.

Decision: three independent pinned P+B assemblies are the minimum arithmetic candidate and fit three separately dimensioned proposed pockets, but voltage-loss and exact inlet/cable evidence do not establish the interface. Select one EXT external regulated-source requirement contract. Source and orderable inlet/mate remain NOT SELECTED. No source capacity, rating, supplier code, physical fit or measurement was invented.

Evidence: existing source lock and exact IC ledger retained. Molex candidate manufacturer text was inspected, but primary drawing/spec bytes timed out; source attempts use the zero-hash unavailable sentinel. Catalog contact maxima do not qualify simultaneous-contact capacity. No component candidate was promoted to the inventory.

Qualification: created https://github.com/Takazudo/zudo-osc-hole-field/issues/57 with original #24 and #48 requirements retained verbatim and explicit source realization, current, thermal, startup, programming, capacitor, grounding, connector, fault and physical-fit work. No hardware purchase/contact/energization is authorized. This issue remains OPEN after CAD tasks finish.

Review fixes: account for shared-return displacement raising a rail; tighten +5 V source upper requirement to 5.10 V. Separate minimum required source delivery from maximum permitted fault current (2.0/1.9/0.5 A), so connector sizing never treats a minimum rating as a current limiter. Rate every ground contact for the entire 4.4 A maximum sum. Reject negative/nonfinite allowances. Keep derived reports and authored requirements distinct from current schematic implementation.

Checks: architecture and adversarial allocation/interface tests, existing rail ledger/options tests, standard checker, evidence validation, regeneration/drift and documentation checks. Full site build/browser and physical checks remain manager-owned or NOT RUN as appropriate; see worker review log for final outcomes.

Downstream: #52 implements load-side supervision, limiter/backfeed/output-sense protection, full capacitor audit, and exact supported connector or visible requirement-only CAD. #35 consumes one EXT domain and selected inlet bracket reserve, retaining selector keepouts; rejected three source trays are not installed. Exact amendment text is in `downstream-amendments-48.md` for the manager to apply.
