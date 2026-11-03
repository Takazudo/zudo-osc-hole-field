# Independent electrical review: Stage 3 direct study

Result: source arithmetic and endpoint bookkeeping reviewed; neither placement variant closes the all-five-OSC 300 mm allocation. No new implementation defect found in the reviewed final bytes. This is not electrical, mechanical or Stage 1 acceptance. Native KiCad, ERC, DRC, routed extraction and physical tests NOT RUN.

## Independent checks

Reviewed `direct_study.py` and `cluster_refinement.py`, including their tests, and checked final report source-binding maps against files. Independently recalculated both winners without calling the direct-study path/return implementation: exact 225 crossing signatures and actual instance/net/ref/pin/panel UID/source-driver identities per winner match the live-canonical Stage 3 audit. The common 26-signal map is injective within c1..c32. All 195 changed signal paths were recalculated from reported package pads, card origins and the actual 180-degree DIN contact transform; all 30 off-card OCT rows retain their previous geometry and budget fields unchanged. Shared reference source pads, rather than a front-header approximation, anchor the three reference nets.

The unchanged model uses 1.15 times octile distance plus 5 mm routing allowance and two 1 mm endpoint allowances for each copper segment; the GH pair is 15 mm, front wire maximum 63 mm, and DIN developed path 25 mm. Both winner reports preserve explicit 300 mm and 1000 pF limits, including PWM and wipers. Independent sums, margins and direct pad separations agree. All 240 return records per winner were checked: front branches, contact polarity, header positions and 78 mm wire-plus-GH reservation remain unchanged; new middle branches reach their assigned b-row contacts and all rear AGND branches use the transformed new b contact and new whole-package pad. The b row is not silently treated as the c row. Endpoint sets are unchanged and resistance remains null. These branch allocations are alternative connections to a common return network, not independent proved complete low-impedance loops.

The nine shared-net aggregate capacitance obligations are retained exactly. No direct capacitance has been extracted: use the union of shared/common and branch conductor, connector and probe segments, without counting a common segment once per receiver. Five selected 1 kohm/100 nF octave receivers remain separate dynamic loads; their capacitors are not absorbed into the 1 nF direct-capacitance limit. Power distribution retains the compact source inventory with its old coordinate frame explicitly labeled; new rails, common return, planes, vias, current sharing, ground error, impedance, stability and local routed paths remain OPEN.

Focused test execution: `test_direct_study.py` 9/9 and `test_cluster_refinement.py` 9/9 PASS. These include missing endpoint, wrong instance, noninjective contact map, bad decomposition, pad warp, missing package, trim movement, overlap and cluster transfer mutations. The independent Stage 3 canonical audit supplies wrong-net/UID/driver and endpoint-completeness coverage. No expensive native or full search was repeated for this review; the reports' bindings were checked and both selected results independently recomputed.

## Negative results and locality tradeoffs

The finite study records 120 cases for each of two variants (240 total). This is a bounded family, not universal infeasibility. Baseline winner: 334.018298 mm maximum, 38 endpoint paths over 300 mm. Controlling actual path is O5 LOCAL_REF5, RB1510:2 to RV507:3 (C:O5.PW), with 13.850673 front trace + 15 GH + 63 wire + 156.369026 middle trace + 25 DIN + 60.798599 rear trace. Refined winner: 336.198722 mm maximum, 50 paths over 300 mm. Its controlling path is O5 PW wiper RV507:2 to R1533:1, with 16.002691 + 15 + 63 + 162.076710 + 25 + 55.119321 mm. Both fail the unchanged allocation despite neither winner having a direct XY pad separation above 300 mm. O1/O2-only favorable rows do not establish all-five acceptance.

Refinement retains 154 whole packages, 193 units, eight cluster memberships, every source pin and six fixed rear trim axes. The 19 bypass associations use retained `Decouples` ownership and actual matching supply pads. Dedicated AGND supply-return pins are limited to U1105:12, U1106:4, U1107:7 and U1108:4; grounded op-amp inputs are not supply returns. Tests independently compare every nonrail rear net's endpoint set and before/after maximum pair distance. Worst supply-pad distance improves from 20.286 mm to 6.504 mm, but C1131 and C1133 individually regress. No dedicated two-leg sum regresses. Timing/waveform/reference spans worsen: TIMING_CAP 12.513 to 13.516 mm; HF_PIN 7.963 to 13.776; TRI_RAW 16.374 to 44.874; SINE_REF5_FB 18.355 to 27.409. Those are Euclidean endpoint extents, not routed lengths or loop areas. The refinement is a tradeoff, not an adopted improvement in electrical performance.

## Split-interface proposal and remaining gates

STAGE3.md's proposed two fully populated 96-position DIN pairs per card correctly count 192 mating positions, 384 solder terminations across both halves, 26 signals, 26 AGND assignments and 140 NC positions. Relative to one pair, five cards add 480 mating positions and 960 solder terminations. Partitioning signals 13+13 preserves 26 total rather than duplicating them. The existing 17 GH links, 54 conductors and 108 crimps are unchanged. Added mount/guide/retainer counts and operations are proposal inputs, not measured assembly work or mechanically qualified hardware. No path saving, capacitance, contact resistance/current-sharing or return benefit is demonstrated by those counts; actual two-interface placement and complete-path analysis must precede such a claim.

Other 28 functions remain UNKNOWN_RESERVED. Exact identity gaps for 24 front/shared packages, local routing, full aggregate capacitance, power/return extraction and mechanical/service feasibility remain open. KEEP_K1402_INCUMBENT and parked campaigns are unaffected. No adoption, canonical placement change or Stage 1 closure is authorized by this receipt.

## SHA-256 bindings

- `scripts/architecture278/implementation/direct_study.py`: `c4ce0b23f01d4ecd6b6aef72ecde74fb082eae78d7294722b97376a14b814fa0`
- `scripts/architecture278/implementation/test_direct_study.py`: `f51de9f7ce41a17aa36f85969634d81372aee6a7df9a0384f38b0fb0da302485`
- `scripts/architecture278/implementation/cluster_refinement.py`: `a0df3b0612867653adcfa78301e2ebc4baa16498f240153e48e48211c609fc38`
- `scripts/architecture278/implementation/test_cluster_refinement.py`: `57006682428d66352a473eea82df086265cdfb33de83c4921ffb5425d17c06e3`
- `scripts/architecture278/implementation/stage3_crossing_audit.py`: `68cc3c0ffd4ae9ee5deb9f65c2f2651b982a40af5fdd285251d63ca155226a23`
- `design/architecture-278/implementation/direct-study.json`: `68c0972522874b3cd7981a4c0da3699a049f55baca8569eb3203735ec0211f7e`
- `design/architecture-278/implementation/direct-study-report.json`: `d2d8fe01d15bafdb555c09eb5d354bb3d1e178e533134849f143a2d3722ef15f`
- `design/architecture-278/implementation/cluster-refinement-report.json`: `4a165b296e1269032a00a2626ca99b8caa17372a328c61a2107f8e20e874779e`
- `design/architecture-278/implementation/stage3-crossing-audit.json`: `9585d9be2c93e69ab4a580127e6157b0f135654ebaf6731d41795898abdeb6ed`
- `design/architecture-278/implementation/assembly-report.json`: `2d8f9cbb7316011c8885fe46c1e2a785a7afb07f8ec4efdb5630bde124c498b0`
- `design/architecture-278/implementation/STAGE3.md`: `46e1c55813b8be3e3845bea2a7d543d664a7ba2716c7c0b937c1b5772e4d05c2`
