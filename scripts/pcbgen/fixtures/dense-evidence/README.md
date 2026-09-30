# Dense routing repair work note

Issue #53 requires a complete 211-footprint, 30-cell, four-layer routing fixture with zero KiCad rule errors, schematic parity issues, and unconnected items after refill. Hardware centres and existing copper remain fixed. This remains an unvalidated synthetic draft, not an indicator circuit or fabrication release.

The historical report is preserved in `historical-attempts.json`. Its board and raw DRC were absent from this checkout and all current worktrees. Reconstruction therefore starts from the committed fixture sources; new measurements do not retrospectively validate the historical attempt.

Baseline: `pnpm circuit:check` passed (manual inventory, 42 lines, no schematic/placement binding; pin-asset check performed). `bash scripts/checks/regen-all.sh` passed and produced no tracked changes. Relevant owner mappings were read: WQP518MA S/T/TN remain CAD labels with exact terminal mapping UNSOURCED; OPA4196IDR uses its retained SOIC-14 pin map. No component evidence is changed here.

Diagnosis, repair, reproduction commands, and measured gates are recorded below as work completes.

## Diagnosis and recommendation

The new bounded reconstruction uses the same 211-footprint, four-layer, 30-cell slice and 40-pad connector. The historical C1607/J310 gaps could not be inspected without their missing board. In the reconstructed board those pads connect; the retained `baseline-drc.json` instead identifies seven GND connections, including C1907.2 at (134.8, 191.0) mm and C2907.2 at (151.8, 191.0) mm in the KiCad frame. The In1.Cu ground fill fractured into six polygons around connector escape tracks. Freerouting's five remaining connections became seven after the authoritative KiCad refill. Its three newly generated GND vias also violated the existing 0.25 mm clearance.

The adopted draft strategy keeps the In1.Cu GND plane and In2.Cu +12 V plane and adds a full-connect F.Cu GND pour. Existing ground through pads and vias join the fragmented inner-plane regions through the front pour. Two 0.7 mm / 0.3 mm ground vias connect the isolated capacitor pads. C2907's via requires a short 0.2 mm INPUT_20 detour on In1.Cu; the original new signal route ran directly under that ground pad. Three new router vias move 0.05–0.10 mm away from signal tracks, with their attached new GND segment endpoints following. `routing-corrections.json` retains the eight original/repaired copper records. All 1,080 pre-existing replicated track/via records are unchanged, verified by `preservation.json`.

No clearance, track-width, via or fixed-hardware targets were relaxed. The original track minimum remains 0.1 mm, ground clearance 0.25 mm, and four-layer stack unchanged. There is no added layer, blind/buried via, moved component, suppressed DRC category, or electrical qualification claim.

Alternatives considered: repeating the router timeout would not repair the observed plane fragmentation; a capacitor escape above/below C2907 collides with existing DRIVE/INPUT tracks. Short KiCad-only geometry trials and their failures are retained in `repair-attempts.json`. The accepted detour changes only new router geometry. Via-in-pad construction and the added front copper need eventual assembly/thermal review; this fixture proves only draft geometric routing.

## Reproduction and ownership

Run `bash scripts/pcbgen/test_route.sh --dense`. It enters the machine-wide guard, generates the complete schematic/netlist, syncs and places all footprints, replays `copper.json` and `stitching.json`, applies the source-defined planes, refills, and checks the complete KiCad 10.0.6 gate. The manifests are explicit retained routing sources, not a claim that the heuristic router is deterministic. Their pad-geometry fingerprint rejects a changed footprint, net, position, or side. Existing source copper must match exactly; unrelated owner objects are retained.

The pipeline checks DRC after source copper/planes are prepared and skips Freerouting when that complete gate already passes. A connectivity-complete rerun with a rule or parity error fails. A sync identity comparison now converts KiCad wxString library identifiers to Python text; otherwise an unchanged back-side footprint was replaced and flipped again on every regeneration.

`--dense-route` is an optional fresh bounded heuristic experiment. It archives earlier cache attempts, runs source-column routing and replication, then the full slice. It does not overwrite accepted evidence or claim completion unless the complete gate passes. The accepted solution is reproduced without any new heuristic router invocation.

The test also checks a second full generation, rejects stale copper and moved pads, retains an unrelated owner graphic, and removes C2907's required ground via on a disposable copy to verify that KiCad reports the missing GND connection. The checked-in PCB is retained for review; recreate its companion schematic/project through the reproduction command before schematic-parity inspection. No fabrication files are produced.

Physical circuit behavior, installed mechanical fit, current/thermal performance, via-in-pad assembly suitability, and fabrication qualification: **NOT RUN** — this is a synthetic routing fixture with no physical specimen or released manufacturing process.

KiCad serializes tracks/vias using transient net codes, so a reload can reorder identical copper objects. The fixture's final serialization sorts only source-owned copper slots by kind and retained UUID; owner objects and individual object bytes are preserved. This makes the first and subsequent complete source generation byte-identical. The normalizer does not change routes or DRC results.

## Final measured checks

- Pinned KiCad 10.0.6: 0 rule errors, 0 unconnected items, 0 schematic parity issues; 159 warnings (80 silk-over-copper, 79 silk-overlap), unsuppressed.
- Complete fixture: 211 footprints, 30 selected locked hardware centres, 40 connector pads, four copper layers, 2,001 tracks and 208 vias. All 1,080 original replicated copper records match their retained fingerprint.
- `bash scripts/pcbgen/test_route.sh --dense`: **PASS**; guard `verdict=PASS`, 38 seconds execution, 7,045 MB minimum available host memory. Fresh rebuild and second full generation are byte-identical. No heuristic router invoked during replay.
- Missing C2907 stitch regression: exactly one GND disconnection, no rule errors. Changed placement/copper are rejected; an owner graphic is preserved.
- Host PCB/region/router unit tests: 15 passed. `pnpm circuit:check`: PASS; manual inventory has 42 lines, no schematic/placement binding, pin-asset check performed. Baseline `regen-all.sh` passed with no tracked drift.
- Fresh bounded heuristic evidence: source column 59.638 router seconds / 633.0 MB sampled peak; full slice 266.266 router seconds / 734.7 MB sampled peak. Both incomplete results are retained; the repaired replay is a separate successful result.
- Visual inspection: front ground continuity, inner connector escapes/plane cuts, and bottom repeated-cell routing inspected from KiCad layer plots. This is a visual geometry review, not hardware qualification.

The verification receipt binds the accepted board, final DRC/statistics, copper sources, board definition, and placement lock by SHA-256. `python3 scripts/pcbgen/fixtures/write_dense_report.py --check` checks those inputs and the generated acceptance summary. Replacing any of them requires renewed oracle evidence.
