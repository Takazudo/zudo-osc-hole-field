# Finite rear assignment and whole-card orientation search

Independent source study; no native execution or canonical edits. The search preserves the compact 103×115 mm rear geometry and the five nonoverlapping slots (2,122), (107,122), (2,5), (107,5), (212,5) mm. It considers all120 oscillator-to-slot assignments and all32 combinations of0/180-degree whole-card turns, for3840 configurations. A180-degree turn maps every local rear endpoint and DIN pad as `(x,y) -> (103-x,115-y)`; functional clusters are not rearranged internally.

For each configuration, the solver minimizes the worst endpoint allocation using one common injective assignment of26 signal nets to32 c-row DIN positions, with matching b-row return positions. Precomputed per-instance/slot/turn/net/contact costs avoid regenerating the assembly. Each cost preserves the actual front endpoint/header terms,63 mm wire,15 mm GH pair,25 mm DIN and the inherited1.15×octile+7 mm segment allowance. Shared REF5/REFN5/GATE_REF paths run from their retained middle source output pads to DIN and rear receivers. All30 OCT0–5 rows remain unchanged and participate in the final maximum.

**Best maximum within this family:488.311094 mm; margin to300 mm:−188.311094 mm.** The original oscillator-to-slot assignment with all cards at0 degrees is a minimizer. Its selected common pin map is recorded in `placement-search-report.json`. There are101 overlength endpoint allocations. The unchanged octave maximum is182.324821 mm.

All3840 configurations were examined. After solving the first configuration, all3839 remaining configurations were excluded by a relaxed per-net lower bound: take each net's cheapest pin independently, then the worst net and fixed octave maximum. This ignores pin exclusivity and therefore cannot exceed the true common-assignment optimum. Every excluded configuration's bound was at least the incumbent; none could strictly improve it. The algorithm makes no claim to minimize the number of failing paths among equal worst-case optima.

Three endpoint pairs in this winning configuration have direct XY pad separations already above300 mm, independent of routing allowances:

| Instance/net | Endpoints | Direct XY mm |
|---|---|---:|
| O5 PWM wiper | RV108:2 → R1125:1 | 307.683242 |
| O5 PWM remote | RV108:3 → R1123:2 | 300.790729 |
| O5 PW wiper | RV107:2 → R1133:1 | 313.037464 |

These are geometric failures for the reported placement, not proof that every configuration has three direct-separation failures. The finite search proves failure to reach300 mm under the declared allocation model within its selected family; it does **not** prove universal architecture infeasibility. Other card dimensions, slots, connector placement, front/shared placement or complete-cluster arrangements were not searched. A next bounded source study should vary those geometry inputs while preserving locked panel centres, whole packages/feedback clusters and complete interface terms.

Validation: all195 DIN endpoint rows independently round-trip to the current assembly report within1e−9 mm before search. The full225-row winner preserves endpoint count. Deterministic `placement_search.py --check` passes. Three matcher tests pass, including all512 possible3×3 bipartite adjacency graphs checked against exhaustive permutations, a surplus-pin case and duplicate-preferred-pin rejection. `git diff --check` passes.

Rotated supports, power straps, guide/key engagement and extraction volumes still require rechecking. Capacitance, actual copper/plane return paths, source regulation, unknown dynamic/fault currents and physical qualification remain OPEN. Native/ERC/DRC and bench checks are NOT RUN. Source allocation margins are not measured worst-case routing bounds.

## Review hashes

- `scripts/architecture278/implementation/placement_search.py`: `e514016fbdfde05f070401fddbd8f2f7e10a746d27aba77920fcef7a0090a852`
- `scripts/architecture278/implementation/test_placement_search.py`: `9335d47442dd074da2bf6afe7389f5f6b7974d819fb1f384234188ed5ec37587`
- `design/architecture-278/implementation/placement-search-report.json`: `6bf2c7813f2ea3ef809412f9a2cefd8beacb46e77d6cf6ce94d2cbf04ebf29c5`
- `design/architecture-278/implementation/assembly-report.json`: `2d8f9cbb7316011c8885fe46c1e2a785a7afb07f8ec4efdb5630bde124c498b0`
