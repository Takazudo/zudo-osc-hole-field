# Same-input JR133 layer-domain pilot

Twelve bounded trials compare four original expansion-limited signal obligations on the same accepted JR133 native input. Every trial keeps the0.025mm lattice,300000expansion limit,6mm bounds, existing neck widths, all copper/obstacles and the -12V In3 fill guard. Only the allowed layer domain changes. GuardPASS64s. All four full-layer trials fail; three F/In3/B trials find whole paths. This is not native connectivity or a general speedup claim.

| Net | F/In2/In3/B | F/In2/B | F/In3/B |
|---|---|---|---|
|XE8DD7DCFD030742EDE49|5.729s / failed|4.518s / failed|5.106s / failed|
|XD0EC0FB162FC331E3F8D|3.997s / failed|4.118s / failed|5.019s / complete|
|XCD7957368B0652402848|3.474s / failed|4.344s / failed|3.780s / complete|
|X94EA1D24CF22A66FD76B|5.076s / failed|4.329s / failed|4.529s / complete|

The two U7406 alternatives intersect (minimum calculated gap−0.6mm), so the complete XD0EC0FB162FC331E3F8D proposal is omitted. Select whole XCD7957368B0652402848 (U7406.2–U7409.3) and X94EA1D24CF22A66FD76B (U7308.3–U7307.2),143segments/3vias, zero cuts/moves. Their minimum new cross-net gap is6.655824987mm. This geometric screen is not proof of native plane preservation. Every51256accepted copper object and every original pad group must remain.

Input board22189b127579271b2f2c219da5e4b7e2af59673cb04e002b0dc4966afe2170dd; native dump001e5809855b059239408859af16a9700d0af0fe5aae9320c96f266c560bcb5a; source maind25854092d89fa1253d05c95c21a225629f8c3f9. result.json pins the historical case source, router hash, all12positive/negative results and paths. selection.json pins exact whole-case selection/conflicts and proposal hash. prepare.py rechecks source, geometry and counts. No electrical rules or panel coordinates changed.

Native pilot remains UNRUN in this commit. Run routing-benchmark.yml with board=osc-jack-right,local_repair=true,local_mode=coupled on this isolated branch after checking no other JR writer. Automatic restoration is disabled. Own terminal artifact reconciliation against original groups, settled/fresh native connectivity, DRC/parity/warnings and exact retained copper. Even a positive pilot needs complete source-bound capped-warning evidence and a fresh adoption replay before publication. Issue189 remains open.
