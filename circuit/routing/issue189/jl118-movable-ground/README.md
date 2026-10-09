# Source-defined movable ground comparisons on JL118

Seven isolated-ground resistors are explicitly movable in `design/partition/floorplan-candidate.json`, on JL and outside bypass clusters. Screen all1,680 translations per part at0.1mm steps within±2mm, preserving side/orientation, the exact fixed outline,0.35mm source courtyard spacing,0.25mm copper clearance, every old copper object and a full0.2mm additive bridge to the old signal landing.

| Reference | Static candidates | Direct/plane comparisons |
| --- | ---: | ---: |
| R8105 | 0 | not run |
| R8173 | 0 | not run |
| R8273 | 1 | 4 |
| RB2214 | 4 | 10 |
| RB2315 | 8 | 18 |
| R8270 | 10 | 22 |
| R8107 | 86 | 174 |

Every direct and In1 plane-fanout comparison includes an unmoved control on the identical native JL118 input. All228comparisons fail to produce a complete route; guardPASS697s. Search diagnostics show exhausted connectivity or no legal via site, not an expansion-limit failure. `summary.json` pins every complete static/routing result hash. Partial signal landing bridges are not submitted.

No footprint was moved and no native moved-board acceptance is claimed. Exact native DRC/parity, original-group preservation, project/rule/physical invariance except an explicitly reviewed source-authorized movement, and deterministic source regeneration would all remain mandatory for a positive candidate. Do not repeat this unchanged scope or merely raise its search budget.

`peer_route_screen.py R8107` is a separate changed-target comparison: connect to the actual isolated R8105 group instead of only the main ground group, using the same feasible R8107 placements and unmoved control. All87comparisons also fail with exhausted searches; guardPASS280s. Its complete result and hash are recorded separately. Thus315routing comparisons in total yield no complete transaction.
