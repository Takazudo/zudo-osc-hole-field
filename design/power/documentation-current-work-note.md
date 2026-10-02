# Keep the power handoff aligned with its current source

The authored power overview and supply decision retained older contract numbers:
1.6/1.5/0.3 A continuous, 4.4 A return, 634 IC packages and
48.3/41.1/24.5 µF master capacitance. The checked source already requires
1.7/1.6/0.3 A continuous, 4.6 A return, 650 IC packages and
49.9/42.7/24.5 µF. The old three-source table also hid domain A's negative margin.

`build_supply_documentation.py` now renders marked sections from the existing
`supply-architecture.json`: selected current and voltage requirements, current
historical-source comparisons, return/loss/power calculations and master
capacitance. Canonical schematic regeneration runs it immediately after the
report producer. `--check` rejects stale sections; missing or repeated section
markers fail. The surrounding narrative remains authored.

This does not change any source requirement, topology, identity, current bound,
board geometry or fixed hardware position. It preserves separate 40 mV protection
and 20 mV distribution allocations, and distinguishes minimum continuous power at
source-band maxima from a maximum fault-power limit. Capacitance is the captured
master inventory, not completed board/effective capacitance or the unfitted
protection candidate. The rejected P+B source remains historical; its programming
precondition applies if that architecture is revisited. Source and inlet remain
NOT SELECTED. #59 and physical #57 remain open.

Validation before edits: component contract PASS; guarded full regeneration PASS
in 242 seconds, no tracked drift. All six historical zudo-pd source-lock hashes
were freshly recomputed by `git show` at the pinned commit and matched; the sibling
checkout was untouched. A scratch changed-current probe updates rendered delivery;
missing markers are rejected. Independent review corrected the missing explicit
40/20 mV allocations and power terminology before application. Changed-source guarded aggregate regeneration, documentation check/build and
strict site checks passed in 237 seconds, with the existing one-link exception.
Combined-parent validation and CI are recorded in the PR. Physical and electrical qualification remain NOT RUN.
