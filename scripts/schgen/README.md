# Functional schematic generator

`bash scripts/schgen/regen.sh` writes the draft master project under `schematic/`. The source is `design/spec/instrument.py`. **Never hand-edit a generated `.kicad_sch`**; change the spec or generator and regenerate. The checked-in synthetic circuit is a generator fixture, not an electrical design.

## Spec API

`specification()` returns `(families, instances)`. A `Family(name, parts, global_nets, sensitive_nets)` owns one or more shared child sheets. Set `Part.page` to 2 or higher when the module is too large for one sheet; each instance receives the same page set. A local net cannot span pages; declare an intentional cross-page net in `global_nets` or redesign the split. An `Instance(family, name, index)` places that sheet in the master. The current example in `design/spec/modules/synthetic.py` has three instances of one family and a separate, single instance power flag sheet. Local labels acquire paths such as `/SYN1/AOUT`; names in `global_nets` stay global across instances. `sensitive_nets` is carried into each component's hidden `Sensitive` field for later partition checks.

Each `Part` has a stable `key`, library `symbol`, reference `prefix` and `ordinal`, explicit `unit`, position in mm, and a complete `pins` map. A pin value is a net name or `None` for an explicit no-connect flag. Set `rotation` to 0, 90, 180 or 270. `value`, `footprint`, `attributes`, `panel_ref`, `panel_refs` and `dnp` are optional. `panel_refs` maps sheet-instance names to exact locked references on a shared sheet; `dnp=True` emits a not-fitted schematic component. `attributes` accepts `MPN`, `Manufacturer`, `LCSC`, `Role`, `PanelUid`, `Island`; `Block` is `${SHEETNAME}`, expanded per instance by KiCad. `Family.paper` may choose a larger sheet such as `A1`. A package's units use keys `U1.1`, `U1.2`, etc., the same prefix and ordinal, and **every populated unit must appear exactly once**, including the power unit. Unused amplifier/comparator pins still need `None` entries.

Circuit designators use `<prefix><instance index × 100 + ordinal>`, so part ordinal 3 in instance 2 is `R203`. Reserve instance indexes 1–999 and ordinal 1–99. Panel hardware instead sets `panel_ref` to the exact designator from the placement lockfile; collisions are rejected. The package scheme makes each instance's local references stable even though the schematic file is shared.

`LibrarySymbol.from_fixture()` reads a complete stock symbol expression extracted with `scripts/kicad/extract-stock.sh`. The fixtures are solely for the synthetic example. The project's real symbol and footprint libraries are separate entries in the project-local tables, using `${KIPRJMOD}`-relative paths. Authors add real symbols through the library workflow; do not copy the fixture into the project library.

## Verification

```sh
python3 -m unittest discover -s scripts/schgen -p 'test_*.py'
bash scripts/schgen/smoke.sh
```

The verifier compares every exported component pin with the spec, including deliberate no-connect pins. KiCad excludes power symbols and flags from the exported component list, so ERC covers those. This proves connectivity parity and ERC rule cleanliness for the selected instrument spec; it says nothing about electrical suitability.

## How to write a module: H1/H2 sample-and-hold pilot

`design/spec/modules/sample_hold.py` is the first real family. Its `family()` composes the OSC-ES-1 functions from `design/spec/cells/` with explicit net mappings. `design/spec/instrument.py` instantiates that one family twice, as `H1` and `H2`; `scripts/schgen/generate.py` loads each project symbol fragment alongside the test-only power flags. `bash scripts/schgen/regen.sh` regenerates the root and shared `schematic/sheets/sample_hold.kicad_sch`. Do not edit either schematic by hand.

Start from `design/grid/placements.lock.json`. The pilot's `panel_bindings()` resolves three jacks, SAMPLE, SLEW and three magnitude LEDs for each instance, checks that all sixteen UIDs are unique, and provides exact per-instance designators. A `Part.panel_refs` map sets those exact references on the shared sheet: for example `J:H1.TRIGGER → J509`, `J:H2.TRIGGER → J510`. Panel parts carry `PanelUid` as a `${SHEETNAME}` template because KiCad shares their source file; the binding audit resolves the template for H1 and H2. Other components leave `PanelUid` empty. `Part.dnp=True` marks the parallel 100 nF hold-footprint option without fitting it.

Use `cell_parts(cell_id, panel_uid, nets, ordinal_start=..., instance_tag=...)` to allocate unique component ordinals and local keys. Map every port that joins another cell, such as LF398 `RAW_HELD` into the slew pre-buffer, by name. A cell's private nets are deterministically namespaced. Complete all physical units of each IC package, including power and explicit no-connect units. `Part.attributes` should carry source-backed MPN/manufacturer/LCSC where available, plus Role and any Island. When a passive value differs from the selected series representative, leave the instance MPN blank until an exact orderable part is captured.

Declare timing/storage nets in `Family.sensitive_nets`: this pilot marks `HOLD_CAP`, `SLEW_STORAGE`, `SLEW_POT_IN`, `TIMING_C` and `TIMING_RCX`. Its `C:${SHEETNAME}.SLEW` island groups the panel pot, 2.2 kΩ minimum resistor, five lag capacitors and both buffers on one board. Keep `RAW_HELD` local to each KiCad sheet instance. A global label used merely to span child pages joins H1 and H2; the pilot therefore keeps the handoff's capture and post-hold stages as separate circuit groups on one A1 family sheet. Rails alone are global until the real power interface replaces test flags.

Run `bash scripts/schgen/smoke.sh` after regeneration. It requires KiCad 10 ERC zero errors, exact identity parity for the 228 documented pin-type warnings in `design/reports/master-erc-warning-baseline.json`, full exported netlist parity, and rejection of a deliberate hold-node mutation in both instances. Warning identity compares the sheet path, severity, type, description, and sorted symbol/pin descriptions; it omits KiCad UUIDs and schematic coordinates. `python3 -m unittest scripts.schgen.test_core` covers the shared-sheet panel-reference and DNP generator features; `python3 -m unittest discover -s design/spec/modules -p 'test_*.py'` checks pilot binding and topology. These are connectivity checks, not bench validation. Canonical schematic regeneration also refreshes `design/reports/current/sample_hold.json` from the current family. `python3 -m design.spec.modules.build_sample_hold_current --check` and the pilot regression tests reject a stale package population. This report gives partial per-instance rail planning values and leaves complete maxima NOT ESTABLISHED; `design/reports/spice/sample_hold.json` records only ideal RC behavior.

## M5A/M5B and M4A/M4B mixer families

`design/spec/modules/mix5.py` and `mix4_vca.py` compose standard OSC-ES-1 cells through `mixer_common.py`. The two family sheets are each reused twice; instance indices 81–84 reserve collision-free internal component references while `panel_refs` binds the exact fixed M5A/M5B and M4A/M4B hardware. `panel_bindings()` asserts 19 unique UIDs per instance. Input and OTA current nodes are local; only instrument rails are global. Regenerate with `bash scripts/checks/regen-all.sh`, then export the KiCad 10 netlist and run `scripts/schgen/verify_netlist.py`. The module tests check panel identity, audio/CV isolation, protected input order, clip monitor, OTA termination and planned rail counts. `design/spec/modules/run_mixer_spice.py` generates bounded ideal and vendor OTA fixtures with one frozen in-range calibration across the command/input matrix. It exits nonzero on a model headroom, zero-bias shutoff or gain-law failure; the report retains feedthrough and real-hardware limitations.

## Whole-instrument integration audit

Run `bash scripts/schgen/regen-master-reports.sh` to regenerate the instrument, export its KiCad netlist, and write `design/reports/master-audit.json`, `design/reports/netlist-stats.json`, `design/power/rail-budget.json`, and `design/power/rail-ledger.json`. Run the same command with `--check` to fail on regeneration or report drift. `scripts/schgen/audit_master.py` gates the exact 35-instance roster, all 438 locked panel UIDs, designator and physical-unit uniqueness, KiCad pin-net parity, and sensitive panel-net island membership; its report lists every sensitive net and island member. It also rejects an all-NC active unit, a missing multi-unit package section, a blank island on a Sensitive pin, and a panel part outside its Sensitive island. `scripts/schgen/build_master_budget.py` sums the eleven authored module current reports and the power-inlet bleeders. It labels all sums as reported planning/assumed subtotals and leaves complete typical and guaranteed maxima unresolved where source reports do. `scripts/schgen/build_rail_ledger.py` checks the current fitted IC package supply-pin traces against exact worksheet package counts and audits all 347 per-load feed/rail assignments in `design/power/rail-allocation-input.json`; its separate conditional cases and extra inlet/SH assumptions never promote the original subtotals to guaranteed maxima.

Run `bash scripts/schgen/export-master.sh` for the 36-page hierarchy PDF, one root SVG, and one SVG for each of the thirteen distinct generated child-sheet sources under `schematic/exports/`. The child SVGs show the shared source sheet; the PDF shows every instance. KiCad exports are draft documentation, not fabrication files. `normalize_exports.py` replaces only PDF/SVG creation timestamps after the oracle export so repeated exports are byte-identical; SVGs otherwise retain KiCad's whitespace formatting.

## Source I/O allocation (#60)

The module family decorators in `design/spec/modules/io_partition.py` assign candidate jack/control/core regions and repack equivalent physical amplifier/Schmitt channels. Every source function is compared by canonical channel signature before and after packing. The A/B control driver uses local unity feedback plus two 499 ohm isolation resistors into its jack-region precision receiver. The native source now has 640 fitted IC packages. `design/reports/io-partition.json` is the source-level package/unit/island/area handoff to #35; it is not a selected PCB partition.

After aggregate and master-report regeneration, run `python3 scripts/checks/io_partition60.py --netlist .circuit-cache/master-audit/netlist.net --require-cut` and then the same command with `--check`. Run `python3 -m unittest scripts.checks.test_io_partition60` for missing/duplicate package assignments, swapped units, raw-TIP and sensitive-island crossing, and impossible-area mutations. `python3 -m design.spec.modules.run_manual_ab_spice` screens the fixed A/B path with the retained TI model. Exact protection stays OPEN in #59 and no physical fit is inferred.

## Current power documentation

`build_supply_documentation.py` renders marked current requirement, rejected-source
comparison, return/loss and master-capacitance sections from
`design/power/supply-architecture.json`. It runs after that report's producer in
`regen.sh`; use `--check` to reject documentation drift. Edit the authored contract
or producer, then regenerate those sections. The surrounding historical narrative
remains authored. These source-derived planning values do not establish source
capacity, complete load maxima or physical qualification.

`build_schematic_status.py` renders marked rail and family-current tables from
`design/power/rail-budget.json`. Canonical regeneration refreshes the mixer
worksheets and master budget before these tables. `--check` rejects publication
drift; unknown complete maxima and partial worksheet scopes remain explicit.
