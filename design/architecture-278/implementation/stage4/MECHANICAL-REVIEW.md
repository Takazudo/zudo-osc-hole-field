# Independent Stage 4 mechanical/source review

The revised shared group and two-grip proposal remove their earlier nominal source conflicts, but the assembly remains mechanically unqualified. Native KiCad, ERC, DRC and physical checks: **NOT RUN**.

## Retained population and dependency

The compact occupied inventory preserves all 4,766 other-function packages, 13 POWER packages and 30 shared-reference packages, including DNP status, whole units, bypass targets, exact retained XY/rotation/courtyards and footprint hashes. Its 6,796 complete unit/pin records are referenced by source-ledger index and SHA, avoiding a duplicate netlist. All new occupied solids remain null; only the shared30 have proposed new XY.

Physically retaining old K conflicts with the proposed withdrawal sweeps and 105 mm cover. Keeping canonical K files unchanged does not choose physical retention. Physical replacement requires explicit disposition of 2,572 packages from 24 other K-bearing functions plus 13 POWER packages. Projecting these exact historical courtyards at the candidate core plane intersects 1,744 unique packages across 18 other functions plus POWER. Per-card counts are O1 92, O2 228, O3 427, O4 504 and O5 543; counts overlap. This is a conditional ownership exclusion, not an area multiplier or an adopted placement. Repartitioning these functions is a broader dependency, not work silently included in the bounded OSC candidate.

## Shared reference and service

All 30 shared packages and their pads translate rigidly +6 mm X. Their courtyard union is [64.36,138.59,92.41,170.41] mm, leaving nominal DIN reservation gaps 0.86 and 2.09 mm. Zero same-face nominal DIN/shared intersections remain. A new carrier outline/support solution is still needed; package fit does not establish PCB edge, flange, copper, tolerance or mounting clearance.

Two handle attachments remain, now at local (11,234)/(33,234), with radius3 attachments and 18 mm projection. Under the retained 20 mm finger-envelope assumption, same-card gap is2 mm, side edge margin1 mm and neighboring-card gap4 mm. Attachment/support box gap is1.5 mm. This is a source proposal for simultaneous axial extraction after unpowered cover/retainer/power release, with the assembly supported through its rigid frame and guides. Finger Z access, guide engagement/alignment, frame stiffness, force balance and load-bearing attachments are not proven. The connector limits of90 N insertion and60 N withdrawal do not certify the frame or handles.

## Connector evidence and exclusions

All 480 nominal DIN contacts and 85 middle GH headers were screened, including mechanical GH lands. Twenty-three DIN centers project into GH courtyards. Seven nominal contact/tail-to-copper exclusions remain, four with the contact center inside a land. The orientation-independent female tail test uses an inscribed circle of radius0.145 mm; a45-degree corner regression prevents the unsafe axis-aligned square assumption. These exclusions use nominal source datums and are not worst-case manufacturing tolerance claims. Missing drill dimensions cannot turn the remaining pairs into clearance passes.

Exact manufacturer-authored female09032966824 evidence gives2.9 mm termination and section0.68–0.75 by0.29–0.31 mm. Newly recovered exact male09031966922 evidence gives3.0 mm termination and section0.575–0.600 by0.500–0.550 mm. URLs and SHA256 hashes are retained in mechanical-input.json; ignored original PDFs remain reproducible. Neither recovered PDF supplies finished drill/pad recommendations, complete flange-hole coordinates or a complete mating alignment drawing. Those values remain null. Nominal15×100 mm DIN reservation is not an exact flange solid.

## Required next evidence

Obtain the exact mating/PCB/flange drawings and a supported carrier/frame/guide definition; resolve seven nominal middle-board copper exclusions with complete path/return rebudgeting. Establish a whole-package occupied-volume disposition for the24 other K-bearing functions and POWER before qualifying rear free space. If this requires repartitioning those functions, obtain a separate bounded design decision rather than treating unknown space as free. Full438 hardware depth solids remain unresolved. No33-function redesign, canonical-board edit, fabrication or energization was performed.

## Validation and source binding

Seven focused tests pass. Both deterministic generators pass `--check`. Tests cover complete unit ownership, null unknown solids, rigid shared-pad translation, retained-coordinate dependency counts, all-contact/header inclusion, two grips and the rotated-tail corner regression.

| Source | SHA256 |
| --- | --- |
| `design/architecture-278/implementation/stage4/candidate-report.json` | `fde4939aeb285c9081cdbcc7ad9d4b0b95cfdaf713de829fcf89d5f4b7b32bcd` |
| `design/architecture-278/implementation/stage4/mechanical-input.json` | `f493fe0573c990528e75348d67d3dd7ff4554fe6455f03234cdf2290bdfe5340` |
| `design/architecture-278/implementation/stage4/mechanical-report.json` | `6d7c1d473e790f334b3d4983523f9cdb6c36fca9ded77d7dca9532718dc9bce9` |
| `design/architecture-278/implementation/stage4/occupied-report.json` | `e61ba1d739e14c00c81db258bc01991a882b3ab79eaf1d63191585e6f309f219` |
| `scripts/architecture278/implementation/stage4_mechanical.py` | `81eb5feb04d99a06524ede26011e5090f6d3b87fac105198ca0288ce23388f49` |
| `scripts/architecture278/implementation/stage4_occupied.py` | `b3ffba87785bca7f3bffb1ac1a763639df7bce6302f7b5113c6238ccac0a17ce` |
| `scripts/architecture278/implementation/test_stage4_mechanical.py` | `9d8210f15cb356d5e74db573785f02939204a31d5a7fa43ca2c950f54b11f2df` |
