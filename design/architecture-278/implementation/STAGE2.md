# Populated source study: current arrangement fails the electrical path gate

The second candidate source stage places all249 physical packages (65 front,30 shared-middle,154 rear), retains the nonphysical supply declaration, and accounts all806 endpoint tuples/38 NCs/171 nets. It adds17 actual GH header land patterns on each front/middle interface, exact locked panel datums, proposed opposite-face transforms, and per-instance selector rotations/depths. No native schematic, PCB or routed copper is produced. These are source placement declarations and dimensional reservations.

The 299.760mm result in the original candidate worksheet is superseded for assembly feasibility by this actual-pad study. That worksheet remains reproducible as historical evidence; it omitted actual front placement, GH developed contacts, full shared paths and routing/tolerance allowances.

## Actual placement and source evidence

`assembly.json`, `compact-rear.json` and `assembly.py` generate `assembly-report.json` and `assembly-placement.svg`. Whole front packages remain intact: U1116 serves FM/PWM/SYNC inputs and SIN output; U1117 serves TRI/SAW/PUL plus spare; U1118 serves1V plus spares. Protection and output feedback stay on the front jack board; controls/selectors remain separate from the rear core. Small front components use both proposed PCB faces, with through-hole pad keepouts on both. Source-side X reflection and locked rotations are explicit. Each oscillator's selector is transformed using its own locked rotation and16/29mm conditional plane, not copied blindly from O1.

The eight rear functional clusters fit a103×115mm envelope after translation and fixture relocation, retaining six rear tool axes. All five original card origins pass the bounded courtyard/fixture screen. This supersedes the need for150mm-tall cards, without changing the original150mm source comparison. Association alone is not local loop qualification: rear bypass origin distances still reach21.438mm, and pad/via/return-loop placement requires refinement.

All30 shared-middle packages are placed on a proposed island at x50..95/y135..172mm. Eight explicit supply-bypass associations supplement source keys that lack a Decouples attribute; components are placed near their whole IC package. The single shared source is retained, including ladder, feedback and spare units. Nine shared nets are now included in remote-path calculations, using explicit source pins rather than treating feedback pins as additional drivers.

The retained JST manufacturer PDF contains exact2/4-way header/housing rows and land dimensions. `front-evidence.json` binds those bytes and nominal dimensions; no family-only guessed replacement is used. It maps95 front/shared packages to16 retained identities;24 still lack exactMPNs (106 across the original full source set). WQP exact manufacturer identity/fit, Dailywell primary availability, TC33 retrieval and exact installed connector/support evidence remain open. No procurement qualification is implied.

## Recalculated path allocations

Each crossing branch uses its assigned front hardware or declared driver, actual footprint pads, both GH header pads, the chosen DIN contact and actual destination pads. Local net node sets are inventoried separately; local receiver branches are not falsely routed through remote headers. Every signal crossing and all nine shared nets are checked. The source graph retains every power/return endpoint; unknown common distribution, contact/joint resistance and parallel-return behavior remain null.

The reservation uses45-degree geometry plus15% routing allowance,5mm per copper segment,1mm per endpoint,63mm maximum wire (60nominal±3),15mm GH-pair developed contact allocation and25mm DIN allocation. Minimum wire57mm is separately tested against actual proposed header XY/depth and at least10mm service slack. These are explicit engineering reservations, not obstacle-routed upper bounds or manufacturer-certified tolerances. Capacitance remains unknown. No300mm/1nF/electrical limit was weakened.

| Source arrangement | Maximum allocation | Endpoint paths >300mm | Geometry scope |
|---|---:|---:|---|
| Retained150mm pair, recalculated |370.461mm|23|Prior large-card comparison|
| Compact103×115 pair, original origins |355.814mm|20|Bounded five-origin envelope remains possible|
| Compact pair centred at y88 |367.138mm|17|Isolated pair only; overlaps retained upper neighbors by32mm|
| Five compact cards, original origins/common pin map |488.311mm|100|All-five courtyard fit; electrical failure|

`placement_search.py` evaluates all120 oscillator-to-slot permutations and32 full-card0/180° combinations, with a common injective DIN signal assignment and adjacent return column. It independently round-trips all195 moving baseline endpoint rows, then uses exact per-net relaxed bounds and bipartite matching. All3840 configurations are considered;3839 cannot strictly improve the incumbent maximum. Original origins/all0° remain a minimizer at488.311mm. Its selected equal-maximum pin assignment has101 overlength rows, because the objective does not minimize failure count secondarily. This is a finite-family result, not a universal impossibility claim.

Three original O5 endpoint pairs have XY pad separation alone greater than300mm: PWM wiper307.68mm, PWM remote300.79mm and PW wiper313.04mm. At those proposed package locations, no pin assignment or copper routing can meet300mm. This is stronger than a pessimistic routing-reservation failure and requires different physical placement.

## Independent review and remaining boundary

The independent all438 locked-hardware screen reports no same-plane/face courtyard, through-pad, panel-transform or DIN/shared collision finding in the selected source. It retains350 unresolved hardware XY projections and one opposite-face middle header/R1616 projection for installed-depth/solid review. Those projections are not called physical collisions. The centred-pair alternative has two known retained-neighbor overlaps and is not an all-five solution.

Electrical, mechanical and code review receipts bind actual sources and outputs. Focused mutation tests cover endpoint/return/NC omission, source-coordinate consistency, nonfinite or weakened reservations, header transforms, all crossing branches, wire slack, package/cluster protection and matching correctness. The stricter source guard runs all stage1 and stage2 deterministic generators without native execution.

Stage1 remains OPEN. Complete local copper/return networks, capacitance/trace/via extraction, exact component identities, current/fault/state maxima, regulation, physical mating/solids, supported straps, stiffness, tool/service swept volumes and actual qualification remain incomplete. The source→common distribution→branch→load→return graph is not a qualified impedance implementation. All inherited electrical limits and #57/#59/#65/#247 obligations remain. NativeKiCad10.0.6/ERC/DRC/routing and physical checks are NOT RUN; no genuine admission or required tool capability was obtained.

## Recommended next bounded work

Continue with a path-first rear/backplane placement specification outside the now-exhausted fixed five-slot family. Keep the populated front/shared source, complete functional clusters, fixed panel centres and all limits. Evaluate new rear outlines/origins and connector locations jointly against every endpoint and neighboring occupied volume before committing to another CAD arrangement. Rear bypass/feedback loops must be refined within those clusters as part of that layout.

Two concrete comparisons are useful: (1) different rear card outlines/origins/orientations with the same supported direct-mate interface, and (2) a split supported rear signal interface with explicitly counted additional contacts, return paths, supports and service operations. Neither is selected or adopted here. Core-only front-copper reuse remains the retained comparison. Simply swapping the five existing slots, half-turning cards, shortening paper allowances or requesting native routing cannot resolve the demonstrated three direct-separation failures. A new arrangement needs source evidence of complete paths and positive tolerance/service margin before native admission is useful.
