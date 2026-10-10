# JL bounded layer-domain pilot

Canonical JL remains118, board a01df89dcab3d4fab8eb0ae80195b2825d2d47adc517cd73452d9b9aa6ea079a. No canonical board changes. Related #189 remains open.

Four immutable saved obligations hit300000expansions with F/In2/In3/B. Eight same-input trials retain the0.025mm lattice,300000budget,6mm bounds, full obstacle/fill guards and existing electrical rules, but use F/In2/B or F/In3/B. GuardPASS43s. One F/In2/B trial succeeds for U2119.12–U2117.13:111segments/4vias, zero cuts/moves. The other seven failures are preserved. Narrowing the layer domain avoids competing search branches; this is not a router-wide speedup claim or native acceptance.

`probe.py SAVED_JL_DUMP` pins the accepted dump and baseline evidence from immutable35535749cf7f9f10dc3f2257767e3346250b3de1. `prepare.py` pins the sole whole candidate and read-only `jl-coupled-plan.json`. No ground restoration is inferred: any native original-group split rejects the pilot. The fixed panel, layers, source placement, electrical requirements and all successful copper remain unchanged.

Run the existing read-only native workflow on this exact branch with `board=osc-jack-left`, `local_repair=true`, `local_mode=coupled`. Check current runs first, record immutable source/run, and own through terminal artifact reconciliation. A positive ordinary pilot still requires fresh complete source-bound warning audits and all native publication/retention gates before adoption. Do not use raw capped-warning eligibility as complete acceptance. Never duplicate the independent core38011194282 or JR38018592247 writers.
