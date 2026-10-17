# Independent mechanical and service source review

Reviewer: independent delegated mechanical/service/code review agent, 2026-10-15. Scope: candidate sources and their generated inputs; no native tool or physical run. Read AGENTS.md, circuit/WORKFLOW.md, the entire NEXT-PROMPT.md, project brief/next-actions, prior populated mechanics, candidate generator/configuration/outputs and focused tests. Root completed portable startup and circuit evidence validation; this reviewer did not repeat environment startup or aggregate regeneration.

## Result

Bounded rear XY/tool/depth allocation is internally consistent at the reviewed source hashes below. Mechanical, service, routing and Stage 1 acceptance remain OPEN. KiCad 10.0.6 ERC/DRC and physical checks: NOT RUN; no exact-run admission. Source reproduction was independently run with `python3 scripts/architecture278/implementation/candidate.py --check` and passed. This review does not inherit the old design's support/service receipt.

All 154 rear packages remain allocated with complete units; six RVO trim origins reserve 6 mm diameter rear axial tool access. The vertical DIN body reservation is x2.5..17.5/y25..125 mm and clears the nearest cluster edge by 7.5 mm. Candidate fixtures, package courtyards and trim-tool reservation boxes are mutually disjoint in nominal XY. Geometry guards enforce card boundaries, connector datum, fixture counts, adjacent-card separation and depth envelopes. Probe declarations retain AGND, +12V, -12V and buffered TRI_SCALED; these are assigned measurement sites, not installed probe hardware or six separately qualified calibration measurements.

O1/O2 are 103 by 150 mm at [2,122] and [107,122]. Their nominal gap is 2 mm, leaving 1 mm under combined 0.5 mm XY tolerances. Middle/core/cover depths remain 50/69.2/105 mm: the proposed mating stack is 19.2 ±0.3 mm, cover-to-handle clearance is 15.8 mm after the 1 mm relative allowance, and inherited selector-to-middle allowance is 7 mm. Four support sites, two asymmetric guides, four power-strap reservations, four probes and two handles now have candidate-specific positions. These are engineering allocations, not qualified installed geometry. Rear package height is a 5 mm procurement bound pending exact variants. Handle finger height is checked with the inherited 20 mm diameter assumption.

## Findings resolved during review

- Replaced the stale horizontal DIN SVG label with the actual vertical reservation and drew candidate fixture reservations.
- Added connector/package/fixture and O1/O2/panel collision guards, tolerance/depth limits, six-trim count and corresponding focused mutation coverage.
- Replaced incompatible inherited fixtures. In the old receipt, power3 intersects new R1158/R1159; old probe2 intersects R1136/R1148, probe3 RB1114/RB1115, and probe4 R1134/R1137/R1167/R1168. Those old locations are not candidate evidence.
- Moved candidate handle sites away from initial nearby probe proposals and made probe nets explicit.
- Preserved O3–O5 as explicitly unpopulated 103 by 115 mm comparison reservations. They are not copies of the expanded candidate.

## Remaining acceptance blockers

1. Replicating 150 mm cards at the old upper-row origins would overlap O1/O2 by 33 mm. Two 150 mm rows with a 2 mm gap need 302 mm before edge tolerance, exceeding the 298 mm panel. A whole-instrument revised arrangement is required before five-card replication; retaining all five oscillator declarations and fixed panel centres does not prove this physical fit.
2. Front jack/control boards and actual placed header/tail geometry remain unimplemented. Body reservations do not establish latch access, cable bend/strain relief, connector flange support, seated datums or inter-board solids. Other 28 functions are not populated. No complete 438-centre occupied-volume qualification is claimed.
3. Candidate supports, guides, handles, fasteners and formed power straps are reservation boxes, not exact purchased parts or a load-bearing structure. Guide engagement before electrical contact, misalignment tolerance, insertion/extraction forces, fastener torque, strain relief, insulating barriers and strap bend geometry remain unqualified. The source's removal sequence is a proposed power-off/discharged service contract; discharge verification criteria and no-owner-soldering assembly evidence remain open.
4. Six trim XY corridors do not establish the complete shaft/tool/screw geometry through the cover or prove physical calibration access. Exact HF trim identity remains unresolved; source package/height and screw-axis assumptions need exact manufacturer/installed reconciliation.
5. The largest evaluated front-to-rear allocation is 299.760 mm, leaving only about 0.240 mm before the 300 mm limit. Obstacle routing, actual front pads/headers, capacitance and complete return paths remain unextracted. The arithmetic result cannot close all-path acceptance; shared-middle nets remain explicitly unmodeled.
6. Current five-card geometry check is a comparison of two expanded candidate cards with three old reservations. Its straight extraction projection and scalar depth checks do not prove swept solids, cover opening, neighbor handles/cables, stiffness or a fully assembled service operation.

Next bounded source work: populate exact front-board packages/headers and candidate mechanical solids/fixtures, then recalculate actual path/return/capacitance budgets and full O1/O2 swept volumes. Resolve five-card packing separately before replication. Native validation requires separate genuine admission; manufacture and energization are not authorized.

## Reviewed bytes (SHA-256)

- `scripts/architecture278/implementation/candidate.py`: `30b2d5f80343914ee30a2bc1829d55c509b4560cf5100bdeb1b5da1e232617a8`
- `scripts/architecture278/implementation/check_source.py`: `e70946da54c317db1f048073934128d5972ac4d80d2feea8a44f511c791df27d`
- `scripts/architecture278/implementation/test_candidate.py`: `b3d2ea3e2f29fcff33251acc3b18776d7cac579c82cd1b0f9994a13055673480`
- `design/architecture-278/implementation/candidate.json`: `6079c71de333c27eb3edea2e2aaea36d47863f9b79f9155900f36465e69095ab`
- `design/architecture-278/implementation/candidate-report.json`: `b68d2840c70f0fc556efe6d8a7d0d5a5b9c71b52a2ab270962032e6ebab76144`
- `design/architecture-278/implementation/candidate-netlist.json`: `7c238b4caa383fcc7721a1e58c1c883330d1865dea5c60e2e00fc7e6b7806913`
- `design/architecture-278/implementation/candidate-clusters.svg`: `7e3b0e945f8df875bea6f9c4ebd49bc9343f43ba3f6dec79613f0f3fd20e82d3`
