# Independent code and source consistency review — stage 2

Reviewed final engineering source after the parent declared it ready, 2026-10-15. This review accepts reproducible source accounting only. Stage 1, electrical acceptance, mechanical fit and native qualification remain OPEN.

## Findings and corrections

- Front return branch coordinates used an X translation instead of each instance’s actual pad transform. The code now reads transformed instance pads. The present selector has no AGND pad, so this was a latent defect and did not change present length findings.
- Evidence extraction omitted the imported footprint parser from its hash closure. The parser is now bound.
- The previous “every signal endpoint pair” wording overstated local route coverage. The report now distinguishes crossing branches from the 171 local-net node inventories.
- The source guard previously reproduced only stage 1. It now checks all five stage 2 generators explicitly, with no native or aggregate entrypoint.
- Eight shared bypass associations are explicit and the packing targets their retained IC packages. This preserves association and improves locality; it does not prove loop inductance, feedback stability or routed bypass performance.

- Follow-up consistency fixes reset the supply graph to compact rear geometry independently of alternative iteration order, and record Euclidean pad separation for shared-reference rows too. Both were inspected and covered by two added tests; all 47 tests were rerun at this final source.

## Independently checked

Ran `python3 -m unittest discover -s scripts/architecture278/implementation -p 'test_*.py'`: **47 tests passed** (26 original candidate, 18 assembly, 3 matching). Negative tests exercise endpoint/return/NC deletion, whole-package coverage, numeric/allowance weakening and protected paths. Matching tests exhaust all 512 three-net/three-pin adjacency graphs against brute-force permutations. Generated-report tests are paired with fresh deterministic reproduction; report tests alone would not prove generator behavior.

Ran `python3 scripts/architecture278/implementation/check_source.py`: **PASS**. It reproduced the unchanged design packet, stage 1 and all stage 2 reports and enforced the isolated implementation paths. No native KiCad or aggregate campaign was invoked.

Ran `pnpm circuit:check`: **PASS**. SCOPE: manual inventory, 68 lines, 0 declared placements; schematic/placement binding not performed; pin-asset check performed.

Inspected actual footprint pad transforms, selector rotations, mirrored faces, endpoint and duplicate-reference branch conservation, connector terms, octilinear segment arithmetic, wire tolerance/service-slack accounting, unknown return/supply fields and source hashes. The inventory retains 806 endpoint tuples including 38 NCs and places 249 physical packages. Signal rows preserve individual endpoint identities; return records retain unknown impedances rather than claiming equal current sharing.

Reviewed finite placement search: every moving original path round-trips before search; all 3,840 slot assignments/180-degree masks are enumerated or bounded by the stated minimax objective. A common injective 26-signal pin mapping preserves adjacent b-row returns. The minimum maximum remains 488.311 mm in this finite family. Its selected tie solution has 101 overlength endpoint paths versus 100 in the original assignment; minimax does not minimize the number of failures. This is not a universal infeasibility proof.

## Acceptance boundary

The compact O1/O2 original-origin comparison still has 20 overlength endpoint paths, maximum 355.814 mm. Full five-card original-origin comparison has 100, maximum 488.311 mm; three selected-search pad separations exceed 300 mm even before connector/wire allowances. The former 299.760 mm scalar result is not a complete-assembly pass. The 15% octilinear reservation, 5 mm segment allowance and 1 mm endpoint tolerance are candidate assumptions, not obstacle-aware routed upper bounds. Ground/source connectivity, common impedance, capacitance, current/state maxima, exact passive identities, all-five electrical instantiation, occupied solids and local timing/feedback routes remain unresolved. Native KiCad/ERC/DRC/physical checks: **NOT RUN**.

No remaining blocking implementation-arithmetic finding was identified in this bounded review. That statement does not accept the electrically failing candidate or authorize adoption, hardware or native work.

## Reviewed source and output SHA-256

- `scripts/architecture278/implementation/assembly.py`: `7d453aea98dabe67640c40c381011b0cd4327d5c28141f141bcf513c927c4c39`
- `scripts/architecture278/implementation/front_evidence.py`: `3cc090eedc698b91373ed27d59b7d5c583206bcea68b9156ed0047e9900d7357`
- `scripts/architecture278/implementation/mechanical_feasibility.py`: `2483d0dff28e2aa5a7f036e6013f852ece5aefa871fef228dcd6e3a36851b749`
- `scripts/architecture278/implementation/assembly_mechanical_review.py`: `e9607cb5a3d5d47657095282a0fd7cff34ee1150559161b218120e38cf244405`
- `scripts/architecture278/implementation/placement_search.py`: `e514016fbdfde05f070401fddbd8f2f7e10a746d27aba77920fcef7a0090a852`
- `scripts/architecture278/implementation/check_source.py`: `a7758b672b24974453fcc5e6b9c5aa60e825663f3e5544e2589a0c48fdcebc2c`
- `scripts/architecture278/implementation/test_assembly.py`: `4f542491e037dcc679eed03e27798949b7d7a11ad730c5a5398fb1df05d8afc0`
- `scripts/architecture278/implementation/test_candidate.py`: `b3d2ea3e2f29fcff33251acc3b18776d7cac579c82cd1b0f9994a13055673480`
- `scripts/architecture278/implementation/test_placement_search.py`: `9335d47442dd074da2bf6afe7389f5f6b7974d819fb1f384234188ed5ec37587`
- `design/architecture-278/implementation/assembly.json`: `a90f5c24ad06f302c2a95161ccb9706e6e5bbf7be4c77d364cb9657a0e74a325`
- `design/architecture-278/implementation/compact-rear.json`: `54f3763d49e9712e9a51f553ff1e15b4c8e7814d6cd9c80f6f28e46b72299bb2`
- `design/architecture-278/implementation/assembly-report.json`: `2d8f9cbb7316011c8885fe46c1e2a785a7afb07f8ec4efdb5630bde124c498b0`
- `design/architecture-278/implementation/front-evidence.json`: `6f04deb55555d3035fb1bbf6bef3f36a7f4ae003f397a0c606592fc83e73bf62`
- `design/architecture-278/implementation/mechanical-feasibility.json`: `24d0a96854df73a1702e7b1eeecc8d95f448a5b2a531a04c4cdcb92f5150a8b9`
- `design/architecture-278/implementation/assembly-mechanical-review.json`: `b9ad1cc96ae07c76490de6fcec9873a1cf1663cb1f8dee63d7a36be6cb60c4dc`
- `design/architecture-278/implementation/placement-search-report.json`: `6bf2c7813f2ea3ef809412f9a2cefd8beacb46e77d6cf6ce94d2cbf04ebf29c5`
