# Rear bypass placement comparison

This bounded source alternative preserves all 154 rear packages, 193 units, eight functional clusters, source pin/net ownership and six original trim axes. It moves whole ICs and small packages only inside the unchanged compact cluster rectangles. No canonical CAD, remote length allocation or electrical requirement changes. This comparison is not adopted into the assembly path report.

`cluster_refinement.py` uses the retained `Decouples` keys and actual capacitor/IC power pad coordinates, not package centroids. It first places whole IC packages near cluster centres (the core is below its fixed trim reservations), then positions bypasses and remaining small packages. The search uses a 0.5 mm placement grid with quarter-turn package rotations. Every transformed pad, courtyard and trim reservation is checked against rigid source geometry. All packages and their complete units remain together.

The worst capacitor-rail-to-IC-rail Euclidean distance falls from **20.286 mm to 6.504 mm**. Every original cluster rectangle still fits; no enlargement is needed. All package/tool pairs have at least 0.5 mm nominal courtyard separation, and the unchanged DIN/support/guide/handle/probe/power fixture screen passes. Six 6 mm rear trim-tool reservations and their axes remain fixed.

The objective includes both rail and dedicated package-ground leg distances where the retained device has a dedicated ground supply pin. For the op amps, a grounded signal input or spare amplifier is deliberately not credited as a supply return: their bypass return pad is recorded but the power/ground-plane loop remains unresolved. Rail-distance improvements alone are not loop-inductance or stability evidence.

| Capacitor | IC | Before rail leg mm | After rail leg mm | Dedicated two-leg sum before → after mm |
|---|---|---:|---:|---|
| C1129 | U1105 | 20.286 | 3.492 | 37.227 → 7.083 |
| C1130 | U1105 | 17.597 | 3.032 | 33.133 → 11.062 |
| C1131 | U1106 | 2.671 | 3.106 | 12.532 → 11.261 |
| C1132 | U1107 | 11.243 | 3.427 | 13.826 → 12.638 |
| C1133 | U1108 | 2.671 | 3.106 | 12.532 → 11.261 |
| C1134 | U1109 | 5.709 | 2.438 | OPEN: no dedicated AGND supply pin |
| C1135 | U1109 | 4.675 | 2.438 | OPEN: no dedicated AGND supply pin |
| C1136 | U1110 | 5.709 | 2.438 | OPEN: no dedicated AGND supply pin |
| C1137 | U1110 | 4.675 | 2.438 | OPEN: no dedicated AGND supply pin |
| C1138 | U1111 | 12.538 | 2.488 | OPEN: no dedicated AGND supply pin |
| C1139 | U1111 | 14.095 | 2.438 | OPEN: no dedicated AGND supply pin |
| C1142 | U1112 | 7.065 | 2.825 | OPEN: no dedicated AGND supply pin |
| C1143 | U1112 | 6.565 | 2.825 | OPEN: no dedicated AGND supply pin |
| C1144 | U1113 | 12.073 | 2.825 | OPEN: no dedicated AGND supply pin |
| C1145 | U1113 | 10.976 | 2.825 | OPEN: no dedicated AGND supply pin |
| C1146 | U1114 | 6.147 | 6.103 | OPEN: no dedicated AGND supply pin |
| C1147 | U1114 | 6.310 | 2.825 | OPEN: no dedicated AGND supply pin |
| C1148 | U1115 | 19.526 | 6.504 | OPEN: no dedicated AGND supply pin |
| C1149 | U1115 | 18.419 | 2.825 | OPEN: no dedicated AGND supply pin |

Two comparator rail legs, C1131 and C1133, increase from 2.671 to 3.106 mm while each dedicated rail-plus-return leg sum decreases from 12.532 to 11.261 mm. This is an explicit geometric tradeoff, not an assertion that either arrangement is electrically qualified. No dedicated two-leg sum regresses. The remaining longest rail legs are C1148/U1115 at 6.504 mm and C1146/U1114 at 6.103 mm; their local body/courtyard constraints and neighboring complete packages limit this simple greedy placement. The result is not a global optimum.

Feedback, summing, timing and grounded-spare endpoint sets are conserved, but moved passives may alter their eventual routed locality. Route all local circuits, assign a complete ground/rail topology, inspect loop areas and via/plane continuity, verify exact capacitor identities and frequency/temperature behavior, and repeat full endpoint remote-path calculations before consuming these positions. Whole-cluster translation/rotation into a narrower/taller card must also transform pads, reservations and all six trim axes and repeat fixture/adjacent-volume checks.

## Sensitive-net tradeoffs

The report includes every non-rail rear net's source endpoint list and before/after maximum pairwise pad separation. This is a geometric span screen, not a route-length bound; some nets also have external endpoints. The bypass-focused comparison makes several sensitive spans worse:

| Net | Before mm | After mm |
|---|---:|---:|
| TIMING_CAP | 12.513 | 13.516 |
| HF_PIN | 7.963 | 13.776 |
| SINE_REF5_FB | 18.355 | 27.409 |
| SINE_REFN5_FB | 16.266 | 23.308 |
| HARD_DRIVE | 3.780 | 16.190 |
| HARD_EDGE | 10.783 | 18.897 |
| TRI_RAW | 16.374 | 44.874 |
| SAW_RAW | 15.259 | 32.065 |

EXPO_SUM improves from 24.071 to 19.174 mm and LINEAR_REF from 23.203 to 14.370 mm. These mixed results mean the alternative is **not electrically superior overall**. Preserve the comparison as evidence, then optimize sensitive circuitry with explicit constraints before adoption. In a new card arrangement, whole-cluster translation preserves intra-cluster spans, while inter-cluster spans such as raw waveform paths must be recalculated. Lower bypass distance does not close timing/feedback/ground-return acceptance.

Reproduce with `python3 scripts/architecture278/implementation/cluster_refinement.py --check`. Nine targeted tests exercise package omission, pad warping, trim movement, overlap, cluster transfer, source bypass/ground semantics and rigid rotations. Native KiCad/ERC/DRC/physical checks are **NOT RUN**. Stage 1 remains OPEN.

Source input hashes are embedded in `cluster-refinement-report.json`. Final reviewed local files:

- `scripts/architecture278/implementation/cluster_refinement.py`: `a0df3b0612867653adcfa78301e2ebc4baa16498f240153e48e48211c609fc38`
- `scripts/architecture278/implementation/test_cluster_refinement.py`: `57006682428d66352a473eea82df086265cdfb33de83c4921ffb5425d17c06e3`
- `design/architecture-278/implementation/cluster-refinement-report.json`: `4a165b296e1269032a00a2626ca99b8caa17372a328c61a2107f8e20e874779e`
