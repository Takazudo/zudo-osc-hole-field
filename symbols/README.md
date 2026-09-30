# KiCad symbols

Each authored symbol has one fragment at `symbols/src/<SymbolName>.kicad_sym`.
The committed `symbols/zudo-osc-hole-field.kicad_sym` library is generated from
those fragments in sorted symbol-name order.

Do not hand-edit the assembled library. Update the affected fragment, then run
`bash scripts/libgen/regen.sh`. If a merge conflicts in the assembled library,
keep either version long enough to resolve the fragments and regenerate it.

Every symbol carries `MPN`, `Manufacturer`, and `LCSC` properties. A blank LCSC
value records that no supplier code was verified; do not fill it from a guess.
Non-orderable utility symbols may use blank MPN and manufacturer values. Any
non-empty footprint reference uses the `zudo-osc-hole-field` nickname and must
resolve inside the project's single `.pretty` library.

Seed fragments were extracted from the pinned zudo-pd commit recorded in their
CAD receipts. `python3 scripts/libgen/seed_assets.py --source-repo <path>` is an
explicit import operation; ordinary regeneration does not read the sibling
repository.
