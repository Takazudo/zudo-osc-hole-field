# Population and historical supply status

Date: 2026-10-02. Unvalidated draft; no hardware qualification.

Original issue 17's evidence bundles and publication are present, including
all three pot values and the compact LED replacements. A fresh review found
the retained DEALON DW254P-2X8-L0 / LCSC C4749189 header still labelled Fitted.
The current EXT source and inlet remain NOT SELECTED. Mark that historical
candidate DNP and describe its role consistently, retaining its evidence,
CAD and unassigned pin map. Manual inventory now has 65 orderable lines,
47 fitted and 18 DNP or hand-fit lines. These are catalogue population flags,
not a change to the generated 5,896 fitted assembly components.

Issue 87's bounded catalogue-evidence work is complete: the exact retained
Murata JSON and request receipt, lifecycle status and missing detailed-source
boundary are published. Continuing global bypass source/substitution work
belongs under issue 21, with protection integration under issue 59. Correct
current status prose without changing the historical work notes or selecting
a global capacitor replacement.

Original issue 18's cell current worksheet still described its superseded
712.655 mA / 640 mA preliminary supply study as a present limit. Label those
numbers historical and point to the current EXT requirements and rail ledger.
Keep all cell values, partial current allocations and qualification limits.
CI now runs the existing native cell ERC/netlist gate so future green checks
include this capture acceptance.

Evidence before this change:

- Clean guarded baseline regeneration at 7dc03f1 PASS, 190 seconds. The
  independently checked library correction was then integrated from main
  0f80445; post-change regeneration also checks the combined source.
- Component contract PASS: manual inventory 65 lines, zero declared
  placements, no schematic/placement binding; pin-asset check performed.
- Isolated native cell audit at 7dc03f1 PASS: 19 cells, 268 symbol units,
  zero ERC errors, six documented LED pin-type warnings; all exported pin
  nets match. No cell topology changed in this publication correction.
- Original issue 17 merge b185391d and issue 18 merge 55b63909 are ancestors
  of current main; their implementations were audited, not replayed.

Post-change aggregate regeneration, native cell gate, documentation check/build,
publication scan and strict links all PASS under the guard in 320 seconds.
The native monitor report changes only the inventory input hash. Independent
review found no blocking issue; final-head CI outcomes are retained in the PR.
Exact inlet realization, source and assembly acceptance, component sourcing,
protection, startup and physical fit remain open. No schematic connection,
footprint, fixed panel centre or electrical limit is changed.
