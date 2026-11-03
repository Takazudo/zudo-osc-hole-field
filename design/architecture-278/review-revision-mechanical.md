# Independent mechanical/service revision review

Reviewer: independent `revision_mechanical_review` agent, separate from the mechanical author. Platform: local WSL Linux; no native CAD, fabrication, physical assembly or energization. Review is of the bounded design and checking code, not architecture adoption.

## Scope and disposition

The planar rear-core proposal establishes a useful capacity witness: 154 physical rear packages / 193 package units, including all six trimmers, are retained per O1. The source conserves 219 O1 physical packages: 57 front-jack, seven front-control, one selector and 154 rear; the power flag is a nonphysical declaration. O2 has the corresponding six trim references. The front 57-package inventory is not a populated redesigned front board, and the remaining 28 instrument functions have not been fitted into the fragmented remaining rear area. These limits must remain explicit in the implementation handoff.

The proposed 103 × 115 mm planar tiles remove the incorrect inference that 17 mm selector pitch mandates 17 mm rear-card pitch. Calibration uses axial tool corridors; fingers need only access rear handles during power-off replacement. Independent support and separate power straps are a sound design direction subject to implementation verification. A conditional one-zone source/schematic/PCB investigation is distinct from physical qualification or adoption.

## Findings raised in this review

1. Initial checker silently accepted deletion of every support, guide, probe and handle, 100 mm package heights, zero tool diameter/withdrawal/sweep, and deletion of O3–O5 reservations. These independent mutations exposed incomplete checks, despite the initial 12 tests passing.
2. Handle solids/finger depth, power-screw tool corridors and extraction against occupied neighbors needed explicit checking. A 2-D package courtyard alone does not prove these operations.
3. Initial equal-radius, symmetrically placed guides did not substantiate polarized mating. Round versus relieved prevents overconstraint but does not itself prevent reversal.
4. Complete O2 package/unit mapping was missing from generated output, although the six trim references were mapped.
5. Rendered SVG obscured O1/O2 labels with support rectangles and omitted handles/power screw axes.
6. Exact selected female manufacturer-authored mirrored PDF now supports the stated 90 N insertion / 60 N withdrawal limits; original mechanical prose still classified those exclusively as unsupported planning bounds. Pair alignment and structural proof remain unqualified.

Findings were sent to the author/root for correction. All six were addressed in the bounded model; the additional inverted/zero-width rectangle finding was also fixed. Final rechecks and exact file hashes follow.

## Evidence inspected

Read `AGENTS.md`, `circuit/WORKFLOW.md`, project brief/current next-actions, mechanical source/input/report/narrative, original interface contract and retained footprint courtyards, revised connector evidence and checking code/tests. The exact female HARTING 09032966824 PDF, printed pages 1–2 (physical indices 0–1), confirms 96 contacts, 2.9 mm wave-solder tails, fixing flanges, 20 mΩ maximum, 2 A at 20 °C subject to derating, ≤90 N insertion, ≤60 N withdrawal, ≥400 cycles and no hot plugging. This is a manufacturer-authored distributor mirror, not successful official-host retrieval. The 18.3–20.0 mm stack remains dependent on the cited manufacturer pairing guide; exact mounting/alignment transfer is future work.

SVG rendered locally using installed librsvg/libcairo through Python ctypes and inspected visually; the unavailable Python cairo module was not used as evidence. `/O1/TRI_SCALED` is an existing buffered rear node shared with the front output path, not a new raw timing test point.

Physical fit, routed placement, exact solids/heights, formed strap and insulation solids, guide first-engagement, support stiffness, joint torque, connector force in the assembly, six-trim service access and powered-off replacement: **NOT RUN**. No calculation or drawing passes those physical criteria.

## Final independent recheck

**Conditional recommendation accepted for the separately authorized one-zone implementation study; no architecture or physical acceptance.** The final geometry uses 18 mm handles with unchanged 20 mm finger envelopes, leaving 2 mm allocated depth clearance above the 5 mm own/neighbor rear-height bound after tolerance. The guides are asymmetrically located at (6,30)/(97,28); final solid/datum/alignment and first-engagement details remain implementation work. Power screw tool corridors, handle foot collisions, package/cover depth, axial extraction versus every populated/reserved neighbor, and complete O2 package/unit mapping are now checked. Existing board reservations are not substitutes for future actual neighboring population.

Re-ran deterministic `populated_mechanics.py --check`: PASS. Re-ran focused discovery: **24 tests PASS**. Independently exercised 16 adverse mutations: missing supports/guides/probes/handles/card reservations, excessive package height, zero tool/withdrawal/sweep, oversized power driver, cover collision, short handle projection, zero-width connector, occupied neighbor collision, handle-foot collision and inverted power rectangle. All rejected. Independently confirmed 154 O2 packages /193 units and all12 O1/O2 trim axes. Final SVG was rendered and visually inspected: labels, handles and power driver corridors are visible and depth labels agree with inputs.

Read the updated GATE and NEXT-PROMPT. They correctly allow engineering choices in this revision and distinguish the next candidate-only source/schematic/PCB stage from adoption, fabrication or energization. The five raw-wiper placement refinement is integrated with the electrical report. A final engineering refinement relocates the whole U1110 package (all five units), all four ISO/FB/FAST feedback loops RB1110–RB1117/C1115–C1118 and both source-declared bypasses C1136/C1137 near DIN. Independently verified all 15 identities and rejected deletion of each member in 15 additional mutations. The deterministic report and 24 tests pass; the remaining generic package courtyards end at y=67.99 before the power band at y=72. Final SVG was rendered again and inspected; labels and the complete cluster remain visible with no modeled overlap. This grouping retains local feedback and bypass ownership; short actual copper loops remain a PCB implementation requirement. Broader transport lengths are planning allocations, not routed verification; exceeding any retained crossing envelope requires implementation refinement rather than an assumption of universal 300 mm closure. The final GATE/NEXT explicitly retain 14 current non-wiper allocations above 300 mm (maximum 374.93 mm), distinct from 23 historical coarse rows. The eight-orientation/19-pin comparison does not establish complete closure; whole-circuit placement and route checking must close these before Stage 1 acceptance. This is a specific acceptance conflict, not a passed geometry result.

`pnpm circuit:check` before and after this review: PASS, with actual scope:

```text
SCOPE: inventory provider=manual; schematic/placement binding not performed (68 lines, 0 declared placements unverified); pin-asset check performed
PASS: component-spec contract; 68 lines; offline=True; refreshed=none
```

No SKIP line was emitted. No schematic/placement binding or physical qualification is inferred.

## Exact final reviewed inputs

The receipt binds the following SHA256 values. A later replacement of the NEXT-PROMPT checkpoint placeholder with the resulting exact reviewed source commit is permitted as metadata-only publication; changes to engineering content require renewed review. Electrical report hashes are recorded in the separate independent electrical review; this review does not claim an independent full electrical proof.

| Path | SHA256 |
|---|---|
| `design/architecture-278/revision-mechanical-input.json` | `ab9d1d6fea53fb4b822d1297d5c8f61eb5ffb78579410104452a27b0c52db1a4` |
| `design/architecture-278/revision-mechanical-report.json` | `43e0023e80951181d0006ef82e9c1f1523e5975a70e8357fe373b2e25aa79c6d` |
| `design/architecture-278/revision-mechanical-sources.json` | `3de8d16ccc6f8521b56faa2c727c6b82b303edc676a940bdade57210d2302e98` |
| `design/architecture-278/revision-mechanical.svg` | `105f825a644e8cb43c3364fbaec1c617c2ee3815284a1a5c21ce162941b38c92` |
| `design/architecture-278/revision-mechanics.md` | `a84e71c4b4c9f5f8da67f7dbb1fec50725f77afdc67bf75ab1235fffb03f96ea` |
| `design/architecture-278/GATE.md` | `64fdf33171834c60153a8368b41e2cb216cc081cf84bab09c35292f0bf44f36f` |
| `design/architecture-278/NEXT-PROMPT.md` | `635c46c136e9becc3f16b3eb6902d1a71e5791cfcec83c05ee6c3047657ffe12` |
| `design/architecture-278/interface-contract.json` | `1a96d576f5b33536014da093b6d0bf1e34b7ef5816dd1a35fb6d26465d4e656b` |
| `design/architecture-278/connector-source-receipt.json` | `910a26c3f670f02c2f3eb4a5c7126be9bd90b28ffe252fe4179e16730cc5537c` |
| `scripts/architecture278/populated_mechanics.py` | `5ad7478ec90e186c9ced30b8d19e4425a1ca8b1266582092ce10a3c47f720f5f` |
| `scripts/architecture278/test_populated_mechanics.py` | `2ee8802c7ac661717f062a1fa79b7b65e04812cf75e7f8f3248affb5001f1af4` |
