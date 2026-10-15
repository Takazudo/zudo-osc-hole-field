# Independent electrical review — actual-pad candidate source stage

Review date: 2026-10-15. Reviewer is separate from the assembly implementation. This receipt assesses the final source bytes listed below, not earlier model results or a manufactured circuit.

## Disposition and material result

**Source inventory and bounded calculation consistency reviewed; electrical/routing/Stage 1 acceptance remains OPEN.** The new actual-pad study materially overturns reliance on the earlier299.760 mm centre/allocation result. Actual front/header pads, explicit GH interfaces and toleranced wire terms expose overlength paths in every declared placement alternative. No native or physical success follows from source reproduction.

| Alternative | Maximum allocation mm | Overlength endpoint rows |
|---|---:|---:|
| `compact_centred_pair` | 367.138432 | 17 |
| `compact_original_origins` | 355.813586 | 20 |
| `five_card_two_rows` | 488.311094 | 100 |
| `retained_150_recomputed` | 370.460612 | 23 |

The independent3840-combination finite rear assignment/whole-card-turn search reaches488.311094 mm minimum worst-case allocation within its fixed family,101 failing rows and three direct XY endpoint separations above300 mm in its reported winner. Its pin assignment can differ from the assembly report among equal maximum optima; neither solver minimizes failing-row count as a secondary objective. This is a failure of the declared family/allocation model, not a proof that all possible architecture arrangements fail.

## Source and topology review

All806 original endpoint tuples are retained, including38 NC endpoints and the nonphysical power flag. All249 physical packages are represented; the package total including that flag is250. All171 non-NC local-net node sets remain inventoried. Complete units, supply pins and unused units stay in their packages. Front hardware pads come from committed footprints at fixed panel datums, including the distinct wiper/switch and jack sleeve/tip locations. Rear-face reflection and quarter-turn transformation are explicit; selector instances use their actual locked rotations/depths rather than a generic horizontal translation.

Crossing paths now distinguish the actual driver-side source endpoint from local feedback/receiver branches. Control link destinations are restricted to their actual panel UID. Every expected instance/link/pin/net crossing is checked, including duplicate reference branches; an empty source/destination fails rather than silently removing a route. Nine shared source output identities are explicitly checked, including REF5/REFN5/GATE_REF where generic source-crossing metadata was absent. Shared feedback pins are not treated as independent remote drivers.

The source retains17 front links/54 conductors, with actual front and middle header pad assignments. Candidate GH2/4 land geometry is supported by exact rows in the retained, hash-verified JST manufacturer PDF; procurement, crimping, mating and installed bend/strain-relief acceptance remain separate. All270 front/middle conductor checks retain minimum wire-cut tolerance and conditional per-instance depths; minimum residual slack is12.479541 mm under this source model. This is not a swept cable or installed slack measurement.

Front/shared bypass placement now targets the associated package, and41 associations are retained including explicit shared C160x mapping. However rear capacitor/package origin separation still reaches21.438 mm (C1149/U1115),18.619 mm (C1129/U1105) and17.849 mm (C1148/U1115). A cluster or origin-distance association does not establish a short supply-pad/via/ground loop. Actual loop routing, decoupling impedance, feedback geometry and stability remain required.

## Findings corrected during final review

The supply endpoint ledger initially inherited the last150 mm comparison placement through a reused variable while the primary inventory used the compact115 mm placement. The source now resets to compact rear placement before building that ledger. The reviewer independently compared every rear supply/return endpoint coordinate against the compact pads. Shared-reference path rows now also carry direct XY separation, preventing future shared geometric failures from being silently counted as zero. Imported generator/parser helpers and rear footprint inputs are directly hash-bound.

## Remaining unimplemented electrical work

Local-net node inventories are not connected copper paths. They retain completeness but do not implement the local driver-to-sink tree, feedback loop, unique shared segments or aggregate route capacitance. Return records enumerate candidate parallel branches and middle corridors with unknown impedance; they are not a solved return network. Power records retain source and endpoint placeholders, not a complete source/common-distribution/branch/contact/via/load/return circuit with component tolerances. No equal return sharing, low-resistance contact performance or source regulation is established.

Combined branch+K return<=0.5 mOhm, rail transfer<=1 mOhm, hot drop<=20 mV, whole source/rail/return<=0.20 V and GH<=0.5 A/contact remain requirements. All dynamic/fault maxima remain unknown; quiescent components cannot fill those gaps. Five-receiver octave loading, raw-wiper leakage/settling, aggregate1 nF direct parasitics, partial-power injection, remote ground error and protection remain open. Every reported crossing capacitance is null. The1.15 octilinear factor,5 mm per segment and1 mm per endpoint are declared engineering reservations, not proven upper bounds around obstacles.

The evidence map retains24 missing exact front/shared MPNs (eight front resistors, C1602 and fifteen shared resistors). No part number was inferred from value/family syntax. Existing WQP518MA exact manufacturer drawing and Dailywell primary-source gaps remain. The source does not qualify all passive/trim identities, panel seating, connector faces, or assembled thermal/fault behavior. #57/#59/#65/#247 obligations remain open.

No native KiCad10.0.6 admission or native run is provided by this work. ERC/DRC, physical fit, energization and bench checks are NOT RUN. KEEP_K1402_INCUMBENT, canonical boards and locked placements remain outside this candidate scope.

## Reviewer validation

18 assembly tests PASS, including endpoint/return/NC omission mutations, shared branch coverage, source constraints, per-instance selector transforms, mirrored pad transforms and supply-coordinate consistency. Three matcher tests PASS, including exhaustive comparison against all5123×3 bipartite graphs. `placement_search.py --check` and `front_evidence.py --check` PASS. Direct review of the corrected supply ledger confirms compact endpoint coordinates. Full local routing, source/return electrical simulation, native and physical checks were not performed.

## Reviewed hashes

- `scripts/architecture278/implementation/assembly.py`: `7d453aea98dabe67640c40c381011b0cd4327d5c28141f141bcf513c927c4c39`
- `scripts/architecture278/implementation/test_assembly.py`: `4f542491e037dcc679eed03e27798949b7d7a11ad730c5a5398fb1df05d8afc0`
- `design/architecture-278/implementation/assembly.json`: `a90f5c24ad06f302c2a95161ccb9706e6e5bbf7be4c77d364cb9657a0e74a325`
- `design/architecture-278/implementation/assembly-report.json`: `2d8f9cbb7316011c8885fe46c1e2a785a7afb07f8ec4efdb5630bde124c498b0`
- `design/architecture-278/implementation/compact-rear.json`: `54f3763d49e9712e9a51f553ff1e15b4c8e7814d6cd9c80f6f28e46b72299bb2`
- `design/architecture-278/implementation/front-evidence.json`: `6f04deb55555d3035fb1bbf6bef3f36a7f4ae003f397a0c606592fc83e73bf62`
- `design/architecture-278/implementation/placement-search-report.json`: `6bf2c7813f2ea3ef809412f9a2cefd8beacb46e77d6cf6ce94d2cbf04ebf29c5`
