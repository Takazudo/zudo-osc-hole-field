# One local C2312.1 breakout repair

**Latest result:** the [one final weight-2 attempt](weighted-final/README.md)
found a graph path but failed full-chain new-via spacing. No candidate was
emitted. The unchanged-placement case is retired, with a
[separate placement recommendation](weighted-final/placement-recommendation.md)
for #245/#253. No native execution followed.

**STOPPED as an ineffective In2-only routing candidate.** The subsequent
[complete region proof](region-stop/README.md) finds a 416-node pocket with no
original goal or permitted exit. The local geometry remains valid; no native
packet, execution or hardware adoption followed.

**Historical implemented source-only repair:**
Parent accepted the F3/two-A negative result and released reservation1641. All
native slots are free. Unchanged O1/F3 matched trials are stopped.

The repair is one 0.3mm B.Cu segment from C2312.1 at `(213.7,264.1)` to
`(216.8,263.3)`mm, followed by one 0.6/0.3mm through via and an In2.Cu source
handoff. No package, pad, harness or existing copper moves. The physical input
remains byte-identical. [repair.json](repair.json) names the exact original
input, terminal, geometry and dimensions.

## What prevented the old search from leaving its source

Retained F3/two-A run38156907050 exhausted the signal search at1,077 expansions.
Its three saved C2312.1 source witnesses ended on B.Cu. The corresponding source
component contains1,034 distinct B.Cu lattice sites and zero router-approved
via sites; expansion count and distinct-site count are different quantities.
The additional two-A goal witnesses at U2306.5 were on In2.Cu, which that source
component could not reach. Merely counting those legal goal witnesses therefore
did not establish a usable route.

The selected local site demonstrates the limiting predicate precisely:

| Check at `(216.8,263.3)`mm | Result |
|---|---:|
| Conservative raster distance to foreign copper | 0.565685425mm |
| Frozen raster via threshold | 0.630710678mm |
| Exact physical gap to limiting foreign via | 0.321954446mm |
| Required physical clearance, unchanged | 0.25mm |
| Exact via clearance surplus | +0.071954446mm |
| Exact B.Cu segment clearance surplus | +0.117246531mm |
| C2312.1 start center's interior margin | 0.010mm |

The limiting via is `5c0e2b48-e6b8-50a6-af33-fc51f5fe0026` at
`(216.2,262.6)`mm, on net`XBACFAB119A723846F935` connecting R2390.2/U2307.1.
The new segment's limiting foreign object is **R2372.2 pad**
`2bdd7bfd-4621-5c13-961b-81ea50c34a75`, on the R2373.1/U2307.4 net.
Both remain untouched. The nearby J900213 pads and other retained tracks/vias
also remain obstacles. [geometry-proof.json](geometry-proof.json) retains
exact records and margins; [failure-analysis.json](failure-analysis.json)
records other limiting owners and the unchanged demands.

This is a legal explicit local breakout around a conservative raster limitation,
not a claim that the shared router is incorrect. Its3.201562mm segment exceeds
the former2mm diagnostic witness templates. It is a new repair and input epoch;
it must not be reported as the unchanged frozen6f078333 method.

The AGND source still has no legal via among its149 reachable B.Cu grid sites;
RV2309.1/.3 and the retained In2 track on U2312.7/R2348.1/R2349.1 are recorded
obstacles. The rail start certificates remain blocked by U2309's own adjacent
pads, including U2309.3 and U2309.12. Moving the whole package would not cure
that internal pad-spacing constraint. This one repair changes neither case and
makes no global impossibility claim.

## Concrete implementation and transition proof

[`f3_breakout.py`](../f3_breakout.py) authenticates the original two-A dump,
frozen427source/control hashes, packet and pinned numerical versions. It checks
exact source contact, the full-width segment, all-layer via geometry, unchanged
hole/SMD rules, bounds and cumulative original-baseline fill preservation. It
then appends exactly one named source witness to a copied adapter pool.

The disposable package is generated under
`design/partition/core-split/candidates/pilots/generated/f3-two-a-c2312-breakout-v1-reviewed/`.
It contains an unchanged original dump, the [repaired pool](adapter-pool.json),
[breakout receipt](breakout-receipt.json), repair card and
[source/file seals](source-binding.json). The large dump remains ignored.
Its original raw SHA256 is
`613a358b340962e2d1fb13cd898fe8a9558edcbf1a5d69cb93b6d2bd7629e97c`.
The source is authenticated artifact11709240803, `fixture/before/dump.json`.

| Adapter input | Before | After |
|---|---|---|
| Signal goal/source portal counts | 6/3 | 6/4 |
| Available source layers | B.Cu | B.Cu and In2.Cu |
| Source at selected breakout point | None | In2.Cu only |
| Synthetic all-layer through permission | False | False |
| Physically added copper in input dump | None | None |

[`prove_f3_breakout.py`](../prove_f3_breakout.py) revalidates those source/file
seals, builds the router's actual input masks, and intercepts A* before search.
Native A* is explicitly forbidden. The [before/after proof](transition-proof.json)
shows that all four adjacent In2 lattice nodes pass unchanged raster track
predicates and exact full-width segment checks. This proves a usable local
handoff, **not full-pair reachability**.

The via preview must never be pre-added to the original dump: the existing-hole
rule would reject a second via, and anchor-only masks would not automatically
reuse that physical via. Instead the existing `f3_adapter.run` pool interface
consumes the repaired pool. Its `portals`/`stitch` logic emits the chosen
attachment once, only after a complete pair passes exact geometry and cumulative
fill checks. Failed full-pair searches retain no breakout copper. The shared
router, existing adapter, native driver, workflows and guards are unchanged.

## Regression and claim boundary

All77 terminal-access source tests pass, including seven new breakout tests:
input/dimension/identity seals, foreign copper and self-hole rejection,
single-layer source binding, no fabricated through permission, original search
direction, atomic single via emission, empty failure output, fill veto and
numerical-version rejection. Independent review covers the actual original
geometry and the before/after source masks. Circuit/docs/generated-output,
TypeScript and frozen baseline-preservation checks pass. Component validation
scope is manual68lines,zero declaredplacements; no schematic/placement binding.

No new retained-board route search, native probe, native PCB apply, settle,
fresh-copy, full-warning audit or adoption occurred. Both original empty F3
proposals and all four original demands remain retained. Fixed panel,circuit
intent,harnessIDsRefsfullpinorder,noncoreposes,sensitive groups and accepted
copper are unchanged; the fill check is only a source screen.

This In2-only repair must not be rerun unchanged. Any separately justified future
method would require a newly sealed repair-method/input packet
and explicit parent admission. The old frozen method's fixture lock cannot be
reused for this new witness pool. No execution wrapper or workflow was added.
