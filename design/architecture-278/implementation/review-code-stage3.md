# Independent direct-study code review — stage 3

Reviewed the root agent’s direct-study source, model accounting and generated results on 2026-10-15. This reviewer authored the separate cluster-refinement source; its execution is recorded below, but this is **not** an independent review of that authored refinement. Independent electrical/mechanical review remains separate.

## Outcome

No remaining blocking code-arithmetic finding was identified in the bounded direct-study comparison. No candidate is accepted. Both alternatives exceed the unchanged 300 mm crossing-path limit: the best baseline arrangement is **334.018 mm with 38 overlength endpoint paths**, and the best bypass-refined arrangement is **336.199 mm with 50**. The 240 enumerated cases comprise 120 per placement variant; this finite comparison is not a global architecture feasibility proof.

All five candidate card boxes and local package/tool/fixture reservations pass the specified courtyard screens, while all other-function occupied volume remains explicitly `UNKNOWN_RESERVED`. The result does not establish installed fit, service clearance or available space. `accepted` stays false.

## Findings addressed

- New DIN mappings/poses initially lacked recomputed return branch allocations. The final source regenerates middle-header-to-adjacent-b-row corridors and b-row-to-rear-ground branch allocations, retaining unknown impedances and common return topology.
- The vertical DIN body reservation originally allowed unchecked future quarter-turn configurations. The source now restricts this study to 0/180 degrees.
- Copied power-distribution XY coordinates refer to the compact source inventory, not the new card. The final report explicitly labels that coordinate frame and states that new rail topology/extraction remains OPEN.
- The directly read candidate-report link source is now included in the hash inputs.
- Refined bypass positions improve a local metric but worsen several sensitive-net spans and the direct-study remote minimax. Both baseline and refined alternatives remain visible, with their tradeoffs; neither is silently adopted.

## Checks and model limits

Independently ran all **89 current implementation tests: PASS**. These include nine direct-study tests for complete crossing coverage, omission/wrong-instance/duplicate-contact/decomposition mutations, fixed octave allowances, package transformation, unknown-volume status and local collision detection. Also ran final `direct_study.py --check`: **PASS**, reproducing all 240 cases.

Performed an independent read-only recalculation of both best variants: 225 crossing rows each, segment sums, actual-source-identity presence, all middle/rear octilinear allocations, 154 whole-package unit/pad geometry, 26 unique DIN signal labels and 240 return branch records. Checked that all other-function reservations remain unknown and every geometry acceptance flag stays false. The source keeps the original 63 mm maximum wire, 15 mm GH pair, 25 mm DIN, 1.15 octilinear factor, 5 mm segment allowance and 1 mm endpoint tolerance. Thirty octave rows retain their unchanged shared/front geometry. The 300 mm and 1000 pF limits remain unchanged; capacitance stays unknown.

The per-path row correspondence consumes the separately audited all-five canonical identities; this review checked consumption and complete tuple coverage, not an independent reconstruction of the entire canonical source audit. Returned branch allocations do not solve common ground topology, impedance/current sharing, source regulation or the full power budget. Direct-study allocations are geometric reservations, not extracted routes or proven obstacle-aware upper bounds. Local feedback, timing, summing and stability still require routed review. Native KiCad/ERC/DRC/physical checks: **NOT RUN**.

## Refinement execution, not independent review

The separately authored refinement preserves 154 packages, 193 units, eight source clusters and six original trim axes, with complete rigid pad/courtyard geometry and 0.5 mm local separation. Its nine targeted tests and deterministic `--check` passed. Worst bypass rail-pad distance improves from 20.286 to 6.504 mm, but timing, HF, raw-wave and sine-feedback spans can increase. Every non-rail rear net has explicit before/after endpoint spans in the report; these are not routed lengths. This mixed result remains an alternative requiring further engineering, not electrical acceptance.

## Final reviewed SHA-256

- `scripts/architecture278/implementation/direct_study.py`: `c4ce0b23f01d4ecd6b6aef72ecde74fb082eae78d7294722b97376a14b814fa0`
- `scripts/architecture278/implementation/test_direct_study.py`: `f51de9f7ce41a17aa36f85969634d81372aee6a7df9a0384f38b0fb0da302485`
- `design/architecture-278/implementation/direct-study.json`: `68c0972522874b3cd7981a4c0da3699a049f55baca8569eb3203735ec0211f7e`
- `design/architecture-278/implementation/direct-study-report.json`: `d2d8fe01d15bafdb555c09eb5d354bb3d1e178e533134849f143a2d3722ef15f`
- `design/architecture-278/implementation/assembly-report.json`: `2d8f9cbb7316011c8885fe46c1e2a785a7afb07f8ec4efdb5630bde124c498b0`
- `design/architecture-278/implementation/stage3-crossing-audit.json`: `9585d9be2c93e69ab4a580127e6157b0f135654ebaf6731d41795898abdeb6ed`
- `design/architecture-278/implementation/stage3/reservations-report.json`: `de8998fe40aacf5145bf236cc9276be3c8acd00f94b0e71efa577926bc68944d`
- `scripts/architecture278/implementation/cluster_refinement.py`: `a0df3b0612867653adcfa78301e2ebc4baa16498f240153e48e48211c609fc38`
- `scripts/architecture278/implementation/test_cluster_refinement.py`: `57006682428d66352a473eea82df086265cdfb33de83c4921ffb5425d17c06e3`
- `design/architecture-278/implementation/cluster-refinement-report.json`: `4a165b296e1269032a00a2626ca99b8caa17372a328c61a2107f8e20e874779e`
