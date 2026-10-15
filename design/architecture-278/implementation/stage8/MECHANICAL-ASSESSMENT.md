# Stage 8 mechanical source assessment

This is the mechanical author's assessment; independent review is separate. Stage7 files are preserved. The candidate retains all56 X1 packages,76 units and7 fixed centres. Native/ERC/DRC, simulation, fabrication and physical validation are NOT RUN. No other function or incumbent copper is changed.

## Substrate and machining

The original42 foreign-pin apertures produced two0.54mm bridges between SW708 pins;0.42mm bridges between J707/J708,J708/J709,J709/J710,J807/J808,J907/J908,J1007/J1008; further0.92mm column bridges and four0.8mm control-edge strips. The generator identifies every pair and rectangle. These widths select specific obsolete ligaments for removal; they are not universal acceptable PCB-web limits. Joining each connected cutout group removes these strips with zero ideal-cut/package intersections. No existing copper route is credited through a removed bridge.

Eurocircuits' primary [mechanical guidelines](https://www.eurocircuits.com/technical-guidelines/pcb-design-guidelines/mechanical/) describe standard2mm contour tooling, explicitly requested smaller radii, minimum0.5mm slots, and separate dimensional/positional tolerances of±0.2mm. The report binds a fetched-page hash and extracted process values. This source does not rate PCB webs structurally or guarantee this candidate's requested tolerances.

The proposed0.5mm tool is offset inside the contour. Its0.25mm corner radius consumes0.07323mm of the retained0.1mm foreign-pin margin at the rounded corner; tool radius is **not** added to the entire aperture. Tolerance must protect both directions: enlarge the nominal cut by one total boundary allowance, and screen the worst outward cut at twice that allowance. The standard0.4mm combined allowance therefore requires0.8mm worst-outward expansion and causes actual land conflicts. This negative is retained separately.

The candidate explicitly requires dimensional±0.05mm and positional±0.05mm, total0.1mm: nominal cut expands0.1mm; worst outward cut expands0.2mm; worst inward cut retains the original pin margin. **Supplier acceptance of this requested precision process is absent.** The six fixed J809/J909/J1009 S/T lands retain0.32mm clearance; the maximum combined allowance compatible with the proposed0.25mm land-edge criterion is0.135mm. That0.25mm value is a named candidate engineering requirement, not an inferred universal fabrication rule. Source pad/drill rectangles and their signed margins are reported separately from package courtyards; courtyard overlap alone does not prove body or copper incompatibility.

Connectivity and web diagnostics use the same worst-outward cut bounds supplied to the locality generator, clipped to each outline, plus conservative boxes around actual mounting holes. Both substrates remain connected. These diagnostics do not establish a load-bearing perforated plate or routed-copper acceptance. Known foreign pins are accommodated; unknown neighboring bodies/PCBs are not declared free.

## Carrier and supports

The obsolete nonfixed jack M2 at(160,119) is removed. Three noncollinear jack supports remain at(107,125),(107,160),(160,160), and three control supports remain unchanged. Package placement around the old M2 forced a355mm routed load path; preserving that arbitrary support would defeat the source repair.

Six new enclosure anchors are explicitly proposed at x3/315,y119/289/164. They are not existing holes. Proposed M3 through-bolts use3.2mm holes and7mm contact/tool envelopes. A proposed enclosure inner X envelope[-2,320] is322mm wide versus318mm panel projection, leaving1.5mm beyond each anchor tool/contact envelope. Fixed panel centres do not move. Enclosure wall thickness, captive-nut engagement, torque, joint stiffness and installation sequence need final detailed design.

A0.5mm graph routes every retained mount to an anchor around all438 fixed-hardware envelopes and every panel-facing X1 SMT courtyard, using3mm ribs plus0.2mm lateral clearance. Every resulting straight segment and anchor tool envelope is independently rescreened against these exact rectangles. The rejected straight beams and their59 hardware projections remain as negative evidence. Wider4/5mm rib alternatives are evaluated explicitly; disconnected mounts are reported rather than silently dropped.

The candidate uses17mm-deep ribs atZ2..19. Proposed monolithic6061-T6 material uses [Aalco's original supplier data](https://www.aalco.co.uk/datasheets/Aluminium-Alloy-6061-T6-Extrusions_145.ashx): modulus70GPa and listed minimum proof stress240MPa for the stated product form. Matching certified material/product form remains required; no weld strength is credited. Source hashes and applicability limits are retained.

The clamp is explicit: carrier bossZ2..19, insulating1mm spacerZ19..20, PCB20..21.6, rear washer/head21.6..24.1. A proposed M2.5×8 screw under the head passes1.6mm PCB plus1mm spacer and engages5.4mm of the boss. The spacer and rib do not interpenetrate. Thread, insulating washer/spacer, contact bearing and fastening torque are proposals requiring later qualification.

Analytical beam sensitivities compare the rejected3×2mm section with3×17mm. The named planning screen applies30N to a branch, a0.5mm deflection target and80MPa stress target (supplier proof reference/3). Straight-segment and full-path straight-cantilever surrogates are both reported. The final longest path is159mm, giving0.46753mm under the full-path surrogate. **A folded frame is not a straight cantilever:** torsion, bends, joined load paths, anchor rotation, fatigue and simultaneous loads are not bounded by this surrogate. It is planning evidence, not a structural pass or simulation result.

## Remaining precise constraints

The repaired topology and carrier proposal do not qualify the perforated PCB itself. [Isola370HR primary laminate data](https://www.isola-group.com/wp-content/uploads/data-sheets/370hr.pdf) supplies cross-direction modulus3178ksi for a separately identified material reference. The report gives actual maximum nearest-mount distances and5N/30N minimum-web strip sensitivities; these are deliberately distinguished from actual plate load sharing. The jack outline's upper-right corner is51.20mm from its nearest retained support. The strip surrogate is highly compliant there; no claim is made that an arbitrary service force can be carried through that corner. Jack nuts must react user insertion loads to the panel; a defined backing fixture/load path for connector service and perforated-board stiffness analysis remain necessary before hardware acceptance.

The smallest remaining work is concrete: obtain or reject the requested precision machining capability; complete the perforated-board support/load-sharing and service backing design; verify folded-frame/anchor compliance with selected material and joints; and establish actual neighboring board/body volumes. If the process cannot provide the required precision, use a different front hosting/cutout arrangement rather than moving locked panel centres or pretending standard tolerances pass. Neither full-instrument hosting nor A01 is accepted by this assessment.

## Final bounded source result and actual service loads

Fifteen focused tests and deterministic `--check` pass. All five cut/package/header/mount exclusion lists are empty; all208 actual front lands have at least0.32mm clearance to the requested-precision worst-outward boundary. Both substrates have one connected component; minimum positive axis-aligned diagnostic widths are1.65mm control and3.87mm jack. These are topology diagnostics, not physical strength or fabrication acceptance.

Actual force applications are mapped to unperforated1mm-wide source-substrate paths to washer contact reactions2mm radially from each mount centre. Actual own through-pad/drill bounds and every mount hole are excluded in addition to foreign cutouts, with exact final segment checking. SW608 has no route in this conservative model and is explicitly blocked rather than assigned a force budget. This deliberately avoids assigning the full30N jack load to an empty board corner. The jack bushings must carry user force to the panel/enclosure; residual PCB force is unknown. At the actual GH centres, the named0.5mm straight-strip planning surrogate gives conditional allowable PCB forces: J-SIG0.9784N over22.55mm; J-PWR1.5014N over19.55mm; C-SIG/C-PWR21.9115N over8mm each. These are not connector extraction ratings. The source5N cable/service assumption exceeds both jack-header strip budgets, so an unrestrained unplug procedure is not accepted: a local backing fixture or strengthened local support/load path must react that service force before physical use. Actual shipping mass is absent; the report gives an explicit uniform-mass surrogate and10g conditional mass budget without inventing a measured mass.

R3313 is relocated as a whole package to(108.5,282), removing its former pad-edge conflict. C3308 rotates180degrees as a whole package at its current origin; physical pad geometry changes but source pin/net identity is preserved. Current net/locality effects are reported by the separate electrical/locality work.

## Source receipt

| File | SHA256 |
| --- | --- |
| `design/architecture-278/implementation/stage8/mechanical-input.json` | `8f1b1ef377adea426818c7afa2beaf386cfa6ff5c7afa4511e6d421255c221e0` |
| `design/architecture-278/implementation/stage8/placement-input.json` | `f7dd385d0278ed3fc1ec8f9bf552394f19004769cf6c51b7b0ae444d43aa6269` |
| `design/architecture-278/implementation/stage8/interface-input.json` | `66715730c90f011246ff9800474412baa3c2ce84d509edb331cda01eae971f75` |
| `design/architecture-278/implementation/stage8/fabrication-evidence.json` | `62a849f8cd02674d7682278692c94ba087f01824c874d2f55b8201abc3d9e090` |
| `design/architecture-278/implementation/stage8/material-evidence.json` | `f818dac31525ef8d3f1d1f7322ff2510cada8e05ce2f628e513c44af553fcd3d` |
| `design/architecture-278/implementation/stage8/laminate-evidence.json` | `6a4fbac819d747b7059788b61060eea8ab73b7b6a6434caead2f72bad4f5d1d8` |
| `design/architecture-278/implementation/stage8/mechanical-report.json` | `613a29089a103ffb878933dd1a818e6c69bd074d1652d01da62cb70d64d78dab` |
| `scripts/architecture278/implementation/stage8_mechanical.py` | `40ca428db5c767226d0ed6d25c2413ef67d8f91e8cd6a8e5755a9766bc960441` |
| `scripts/architecture278/implementation/test_stage8_mechanical.py` | `101f26637a05416e6468b55ee69d3586ba08d94c42d4cd65b1ea5f273e378f0e` |
| `scripts/architecture278/implementation/stage8_locality.py` | `e52e3e04759b86a3a4486422864ea6ac7672a9f661bb80ce75a3d990efe70995` |
