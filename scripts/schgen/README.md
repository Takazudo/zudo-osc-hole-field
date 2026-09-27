# Functional schematic generator

`bash scripts/schgen/regen.sh` writes the draft master project under `schematic/`. The source is `design/spec/instrument.py`. **Never hand-edit a generated `.kicad_sch`**; change the spec or generator and regenerate. The checked-in synthetic circuit is a generator fixture, not an electrical design.

## Spec API

`specification()` returns `(families, instances)`. A `Family(name, parts, global_nets, sensitive_nets)` owns one or more shared child sheets. Set `Part.page` to 2 or higher when the module is too large for one sheet; each instance receives the same page set. A local net cannot span pages; declare an intentional cross-page net in `global_nets` or redesign the split. An `Instance(family, name, index)` places that sheet in the master. The current example in `design/spec/modules/synthetic.py` has three instances of one family and a separate, single instance power flag sheet. Local labels acquire paths such as `/SYN1/AOUT`; names in `global_nets` stay global across instances. `sensitive_nets` is carried into each component's hidden `Sensitive` field for later partition checks.

Each `Part` has a stable `key`, library `symbol`, reference `prefix` and `ordinal`, explicit `unit`, position in mm, and a complete `pins` map. A pin value is a net name or `None` for an explicit no-connect flag. Set `rotation` to 0, 90, 180 or 270. `value`, `footprint`, `attributes` and `panel_ref` are optional. `attributes` accepts `MPN`, `Manufacturer`, `LCSC`, `Role`, `PanelUid`, `Island`; `Block` is `${SHEETNAME}`, expanded per instance by KiCad. A package's units use keys `U1.1`, `U1.2`, etc., the same prefix and ordinal, and **every populated unit must appear exactly once**, including the power unit. Unused amplifier/comparator pins still need `None` entries.

Circuit designators use `<prefix><instance index × 100 + ordinal>`, so part ordinal 3 in instance 2 is `R203`. Reserve instance indexes 1–999 and ordinal 1–99. Panel hardware instead sets `panel_ref` to the exact designator from the placement lockfile; collisions are rejected. The package scheme makes each instance's local references stable even though the schematic file is shared.

`LibrarySymbol.from_fixture()` reads a complete stock symbol expression extracted with `scripts/kicad/extract-stock.sh`. The fixtures are solely for the synthetic example. The project's real symbol and footprint libraries are separate entries in the project-local tables, using `${KIPRJMOD}`-relative paths. Authors add real symbols through the library workflow; do not copy the fixture into the project library.

## Verification

```sh
python3 -m unittest discover -s scripts/schgen -p 'test_*.py'
bash scripts/schgen/smoke.sh
```

The verifier compares every exported component pin with the spec, including deliberate no-connect pins. KiCad excludes power symbols and flags from the exported component list, so ERC covers those. This proves connectivity parity and ERC cleanliness of the synthetic fixture only; it says nothing about electrical suitability.
