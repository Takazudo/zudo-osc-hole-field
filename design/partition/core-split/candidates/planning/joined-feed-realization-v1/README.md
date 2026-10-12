# Joined two-core supply realization: source design not established

**STAGE BLOCKED — no complete physically instantiated A/B source candidate was produced. Keep K1402 as the fallback.** This is the requested consolidated architecture decision on the bounded stage, not another endpoint ledger presented as implementation. No new PCB, feed terminal, distribution copper or carrier is claimed ready for native validation. The evidence does not prove that a feasible two-core construction is impossible.

The latest 58 mm-offset proposal is materially different from the old failed two-110 mm assumption. Independent electrical and mechanical/code reviews were joined before deciding readiness. The shorter feed has positive conditional arithmetic and no sampled collision counterexample, but the concrete board-access/contact/return network and complete carrier have not been constructed. Generating twelve pads and copying plane definitions would leave those source-design obligations unanswered. Missing supplier measurements alone are not the reason for this stop.

## Updated electrical alternatives

The exact existing 5859 wire identity, three rail wires, three AGND wires, 20 mV distribution limit and legacy interfaces remain unchanged. Use the latest **104 mm main / 85 mm new-feed ceilings**, including preparation. The older inherited `maximum_cut_length_mm:110` within copied wire records cannot override the new 85 mm effective ceiling. Source wire/contact bounds are requirements, not measurements: 13 mΩ/m hot wire; 0.2 mΩ combined ends for each complete wire. Both serial sections pay their ends. Board copper and common return access are charged globally once.

| Conditional construction | Rail / common return copper | +12V drop | Result and limitation |
| --- | --- | ---: | --- |
| Historical 110 + 110 mm; one return | 1 / 0.5 mΩ | 26.2420 mV | Fails; historical only |
| Latest 104 + 85 mm; one return | 1 / 0.5 mΩ | 23.5419 mV | Shorter cuts alone do not meet the bound |
| Latest 104 + 85 mm; one return | 0.1 / 0.1 mΩ | 19.8119 mV | Conditional pass; copper construction unproved |
| Latest cuts; three accessible returns in each section | 1 / 0.5 mΩ | 14.780433 mV | Conditional two-port construction; full joined network absent |
| Latest cuts; two accessible returns in each section | 1 / 0.5 mΩ | 16.9708 mV | Illustrative two-port sensitivity; not fault acceptance |

The tight-copper result also gives −12V 19.5162 mV and +5V 15.0807 mV. Its limiting margin is only **0.1881 mV**: 2.159587 mm extra aggregate two-section cut length, or 1.079793 mm added to each section, when rail/return lengths change together. Alternatively it permits only 0.040891 mΩ more common return resistance with rail resistance held fixed. Those are separate sensitivities, not simultaneously spendable margins.

The 0.1 mΩ allocation is not a realized conductor. At the source nominal 70 °C resistivity, 70 µm copper has 0.294907 mΩ/square; 0.1 mΩ permits 0.339090 squares. An ideal uniform 140 × 310 mm single-plane transport strip contributes **0.133184 mΩ** before spreading or access. A nominal full-1.6 mm transfer using 25 barrels with 0.3 mm finished bore and 25 µm wall contributes **0.051760 mΩ**; two contribute 0.103519 mΩ before foil. These comparisons reject those specific nominal constructions as 0.1 mΩ certificates. They are not lower bounds for every possible parallel-layer, distributed-source or shorter-depth construction. No stack-depth, parallel-layer or equal-current assumption is silently credited.

For a genuinely connected two-port return section with three separately bounded conductor/contact paths, conductance addition gives `R_effective <= R_section / 3` without assuming equal currents. The common copper/access term remains undivided. This is a promising alternative within the existing interface count, but it requires actual shared endpoint access. The instrument's signed multiport load/GH network is not two ideal nodes. All 380 GH returns, peripheral ports, shared necks and required outage states need a compatible joined model; every individual main return retains its 4.6 A requirement. Patch sleeves are not credited as power feeds. The previous sum-of-all-omitted-access 0.5 mΩ certificate is sufficient, not a necessary physical impossibility criterion.

The existing finite main-contact trial provides another conditional refinement, with published main-wire upper values JL 1.406588, JR 1.382586 and P 1.361676/1.360171 mΩ. Those source fields cannot be subtracted from unrelated PCB transfer intervals or assigned to new CS247 contacts merely because the wire MPN matches. The existing endpoint adapter's small-angle class does not establish the new approximately 57° wire-to-board-normal transition. New angled fan/solder/adapter geometry needs compatible finite source and current traces, contained metal, and a paid resistance bound. This is load-side design work; no upstream protection implementation is added or demanded by this stage.

[budget-comparison.json](budget-comparison.json) and [compare-budgets.py](compare-budgets.py) reproduce the alternatives. The [independent electrical design review](evidence/electrical-design-review.json) retains exact sources, layer roles, roster counts, scope and additional arithmetic.

## Joined mechanical findings

The latest proposal retains KA B.Cu → KB F.Cu, two three-wire rows, 58 mm X offset, 2 mm anchors, 66 mm nominal free curve, 2.5 mm tails, and 0…10.1 mm service withdrawal. Required new cuts are 84.5…85 mm; main cuts are 103.5…104 mm. Existing source calculations give a conditional minimum bend radius 26.634658 mm against 25.908 mm, preparation 5.085133 mm against 4.5 mm, and local collet residual clearance 0.447966 mm against 0.25 mm. Proposed C0/C1/C2 shape and process bounds remain unqualified.

One bounded source-only audit examined the exact revised family at nominal 0, 5 and 10.1 mm withdrawal, including all six free curves, tails and land bridges against all 4,569 source/new reservation boxes, other wires, enclosure XY and foreign land reservations. The twelve 6×6 mm land reservations were checked against their own board-face source reservations. No alternative family or F3 pose was searched.

| Withdrawal | Minimum sampled source gap | Wire-pair gap | Enclosure XY gap |
| --- | ---: | ---: | ---: |
| 0 mm | 1.556498 mm | 2.075696 mm | 1.626767 mm |
| 5 mm | 1.947843 mm | 4.657355 mm | 2.885074 mm |
| 10.1 mm | 1.947843 mm | 4.657355 mm | 5.129916 mm |

Minimum land-reservation/source gap is 9.627041 mm. These samples supply **no counterexample**, not a full continuous clearance certificate. Reservation boxes are conservative source models, not detailed component solids. The audit does not contain revised arms, joints, fasteners, stripped-insulation/contact solids or their complete toleranced sweep. Old `clamps.py` uses the historical 52 mm / 1.5 mm / 0.3 mm-stem construction and cannot certify the revised carrier. All-100 adjustment access and the complete assembly/service load path remain undesigned for this candidate.

The run completed in 7.613 seconds, peak 194,588 KiB, under a 120-second / 2 GiB single-worker bound. [Geometry evidence](evidence/geometry-witness.json), its [producer](evidence/geometry-witness.py), and [independent code/distance review](evidence/geometry-independent-review.json) retain exact inputs and all sampled witnesses. Independent review checked 63 saved distance calculations without repeating the geometry run. No native run occurred.

## Consolidated architecture decision

Retain K1402 and do not issue a native-ready A/B candidate from this stage. The missing work is a **single physical load-side distribution and return design**, joined to its contact and carrier geometry:

1. Exact retained/reconstructed branch ownership and actual pad-to-feed paths for every A/B +12V, −12V, +5V and AGND contact, including local derived rails, bypasses and sensitive reference returns. The previous mixed +5V component reaches 38 A and 510 B pads; it cannot be treated as B-exclusive or copied blindly. The unchanged diagnostic A fixture has no global rail tracks/vias; adding twelve terminals would not repair its distribution.
2. Realized, source-bound CS247 footprints, unique Refs/pad UUIDs, angled contact solids and conductor geometry, with an electrically compatible termination model. The 12 nominal land locations in the mechanical sample are reservations, not implemented PCB pads. No B pad is invented on A.
3. A physically connected expanded return/access graph and copper/contact resistance certificate. The preferred quantified route to investigate is the **existing three-return topology**, with actual access and signed loads, rather than assuming the near-limit 0.1/0.1 mΩ allocation is achievable. This changes no required electrical limit or external interface; it is not an adopted topology or a finished graph.
4. Complete revised carrier, insulation, joints/fasteners and service geometry. Full continuous/tolerance sweeps and all adjustment access must be joined to the electrical layout. Measurements and process qualification can remain explicitly pending during source design; absent source geometry cannot be substituted by a measurement placeholder.

This is a bounded incomplete-design outcome, not a demonstrated physical impossibility, newly discovered fixture-filter defect or proof that fixed geometry must change. If the joined physical graph/construction can be supplied under #247/#245, these comparisons define its evidence obligations; otherwise K1402 remains the fallback. No isolated F3 trial, obstacle-removal experiment, native job, architecture adoption, PR merge, fabrication or energization follows this decision. The external protection boundary, fixed panel, non-core poses, legacy harnesses and accepted copper remain unchanged.

## Reproduction and validation

`python3 compare-budgets.py --check` replays the small source comparison; `python3 -m unittest discover -s . -p 'test*.py' -v` tests eight arithmetic/scope invariants. Archived witness producers document the one actual run and are not automatically rerun by these checks. Their original `/tmp` output paths are historical provenance.

Final repository checks and baseline preservation are recorded in [verification.json](verification.json); [ledger.json](ledger.json) binds the packet. This stage's acceptance condition—a complete physically instantiated A/B source candidate with supported budget and geometry—**was not met**. The packet records the requested stop decision and quantified alternatives honestly.
