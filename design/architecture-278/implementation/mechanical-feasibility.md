# Independent all-five rear mechanical feasibility

The original 103 × 115 mm rear-card reservation can contain the complete candidate rear population, its eight functional clusters, six 6 mm trim-tool reservations and all proposed fixture reservations. This is a new bounded source calculation, not adoption or native/physical qualification. It supersedes the need to replicate the prior 150 mm tile for this particular courtyard-capacity question; the previous review correctly identified that simply replicating that tile would collide.

The source is `scripts/architecture278/implementation/mechanical_feasibility.py`. It reads immutable implementation checkpoint `80000737f0a2fd97896ca654040ab65096aed352` with `git show`, translates whole clusters without changing any package-relative placement or pin geometry, and generates `mechanical-feasibility.json` and `mechanical-feasibility.svg`. Baseline report and compiler SHA-256 hashes are recorded in the report. It does not import or modify the evolving candidate compiler. Reproduce with `python3 scripts/architecture278/implementation/mechanical_feasibility.py --check`.

## Concrete preferred comparison

Retain five 103 × 115 mm cards at the original origins: O1 [2,122], O2 [107,122], O3 [2,5], O4 [107,5], O5 [212,5] mm on the 318 × 298 mm panel. Panel centres are untouched. Every card contains all 154 source rear packages, eight complete clusters and six rear trim-tool reservations. The five-card count is 770 rear packages and 30 trims; this is a mechanical copy comparison, not generated all-five Ref-pin/net parity.

Translate current cluster contents by these offsets, in mm, from the reviewed 150 mm candidate. Whole packages, bypass parts, pad offsets and relative intra-cluster placement remain unchanged:

| Cluster | Delta x | Delta y | Resulting occupied reservation |
|---|---:|---:|---|
| wave-scale | 0 | 0 | [25,2,44.08,21.01] |
| core-timing | 0 | -10 | [25,23,45.64,54.52] |
| tune-octave-vee | 0 | -38 | [25,57,44.04,70.05] |
| local-reference | -24 | -22 | [25,73,44.04,86.05] |
| sine | 0 | 0 | [49,2,78.74,19.66] |
| fm-pwm | 0 | -6 | [49,22,67.74,50.91] |
| sync | 0 | -10 | [49,53,68.08,67.37] |
| pw-lfo | 0 | -73 | [73,22,91.74,36.27] |

The old cluster allocation rectangles contained substantial unused height: timing occupied 31.52 mm inside a 60 mm allocation, and reference/tune each occupied 13.05 mm inside 29 mm. The compact alternative removes this unused allocation; it does not shrink footprints, tool diameters or electrical circuitry. When integrating into a shelf-placement compiler, preserve original cluster widths and package ordering and translate existing explicit overrides. In particular R1123 becomes [60,50] and R1117 [55,50]. Trim cluster rectangle heights to the occupied extent plus a small margin; do not keep the old overlapping 60/29 mm allocation rectangles.

Candidate-specific fixture reservations:

- DIN vertical body: [2.5,7.5,17.5,107.5], contact-bank centre [10,57.5]. This is still the inherited 15 × 100 mm allocation, not a new exact installed connector drawing.
- Supports, radius 3 mm: [6,4], [91,4], [6,111.5], [91,111.5].
- Guides, radius 2 mm: [20,7.5], [92,80].
- Handle feet, radius 3 mm: [30,111.5], [70,111.5].
- Probe reservations, radius 2 mm: [20,111.5], [45,111.5], [55,111.5], [80,111.5]; retain AGND, +12V, -12V and buffered TRI_SCALED assignments respectively.
- Four power reservations: [25,91,35,103], [43,91,53,103], [61,91,71,103], [79,91,89,103].

The same objects also fit a narrower 97 × 115 mm tile. The 103 mm width leaves more lateral space for routing and exact support implementation; shrinking width is an optional engineering alternative, not a requirement.

## Other checked arrangements

The generated report includes four alternatives:

1. **103 × 115 mm, original five origins**: preferred comparison because it preserves the design's rear-card origins and avoids an unnecessary all-five packaging change.
2. **97 × 115 mm, three columns**: O1/O2 [2,122]/[101,122]; O3/O4/O5 [2,5]/[101,5]/[200,5]. This frees 18 mm of total row width but changes O2/O4/O5 route geometry.
3. **115 × 97 mm, two columns, whole-card 90° rotation**: O1/O2 [2,101]/[119,101]; O3/O4 [2,2]/[119,2]; O5 [2,200]. Every package/tool/fixture box rotates together. It fits nominally, but neither its remote path lengths nor electrical superiority is established.
4. **103 × 120 mm, extra edge space**: O1/O2 [2,124]/[107,124]; O3/O4/O5 [2,2]/[107,2]/[212,2]. It offers extra lower-edge clearance using the same compact fixture pattern, at the cost of changed card origins.

All four passed the independent generator and deterministic reproduction. Every local package/tool/fixture pair has at least 0.5 mm nominal separation; every object fits the 97 × 115 mm local outline with at least 0.5 mm board-edge clearance. All complete card boxes pass a 1 mm combined XY tolerance separation screen and the fixed panel bounds. Six local trim tool reservation boxes remain disjoint per card. These tests account for the actual committed package courtyards rather than only cluster rectangles.

## Limits and next bounded work

The source establishes rear courtyard capacity. It does not establish routed electrical locality or fully occupied mechanical fit. Cluster translations and DIN movement change route lengths and must be consumed by complete front-header-to-rear-pad path/return/capacitance calculations. Relative intra-cluster geometry is preserved, but the existing shelf arrangement was not a routed timing/feedback design.

Keep the proposed middle/core/cover depths 50/69.2/105 mm, 5 mm package procurement bound, 18 mm handle projection, 40 mm straight withdrawal and 100 mm rear workspace as comparison inputs only. Exact rear heights, screw axes, guide alignment/engagement, connector flange/tail/keying solids, power-strap bends, insulation, fastener tooling and support strength remain unresolved. Handle finger volumes need their complete candidate-specific swept-solid check; the footprint drawing is not a service-access receipt.

Front jack/control packages and connector bodies/tails still require placement at the fixed panel hardware centres, including actual selector occupied depths. The remaining 28 functions are not populated by this analysis. Five rear cards fitting does not prove the whole instrument fits, nor authorize replication or architecture adoption. All-five electrical/reference/power parity and service isolation remain separate checks. Native KiCad 10.0.6/ERC/DRC and physical checks are NOT RUN without genuine separate admission and required capabilities. Hardware fabrication, purchase and energization remain outside this task.
