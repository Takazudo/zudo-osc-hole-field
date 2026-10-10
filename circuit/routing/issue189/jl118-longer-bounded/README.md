# Bounded JL118 longer-obligation negatives

All ten signal nets with a nearest endpoint pair spanning at most24mm on either axis were already in the cut-neighbour screen. An initial assertion expecting six additional short cases correctly stopped before any routing. Diagnostic inspection found79other signal nets with larger spans; no padless-island omission was involved. A system-Python diagnostic lackedShapely; rerun used the pinned numerical virtualenv, without installing anything.

Select the six shortest remaining obligations under a36mm maximum axis-span cap (approximately26.6–32.9mm endpoint distances). Compare F/In2/In3/B,F/In2/B,F/In3/B on identical native JL118 dump9d193cd974148e58b576d247edb5bce804f06a29d075098513a1292c21fbf136, boarda01df89dcab3d4fab8eb0ae80195b2825d2d47adc517cd73452d9b9aa6ea079a,0.025mm grid,6mm framing,300000expansions, existing neck widths, all obstacles and -12V fill guard. All18trials fail(PASS94s):10hit the expansion cap,8exhaust their search.

budget_probe.py repeats only those10capped cases against exactly the same input and router with a finite600000expansion bound. All10still fail(PASS46s). It pins the full baseline result hash. This is a bounded search comparison, not a speedup claim or physical impossibility proof. No PCB, copper, placement, keepout or electrical requirement changed; no native candidate or worker was produced. Preserve all positive/negative evidence from other methods and do not repeat these unchanged settings.

Scripts currently import the pinned router from /workspace/issue189-jl-layer-escape and use the saved native dump path under the primary checkout. Run through heavy-guard with the numerical virtualenv. result.json and budget-result.json include every obligation, endpoints, bounds, diagnostics, expansions and timing; exact source/dump/router hashes are recorded. Native acceptance gates are unchanged.

## Additional same-input comparisons

`coarse_probe.py` changes only lattice from0.025mm to0.05mm on the same18cases, bound300000. All18fail with search_exhausted; guardPASS46s. `weighted_probe.py` keeps the0.025mm lattice and300000bound, changes A*weight to2.5 for the ten previously capped cases. All10still fail expansion_limit; guardPASS43s. `coarse-result.json` and `weighted-result.json` pin source board/dump/router and baseline result hashes. No candidate, native run or board edit resulted. These are search heuristics, not relaxed electrical constraints.
