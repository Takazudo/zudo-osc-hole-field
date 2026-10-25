# C2312 In2-only breakout: stopped before a native packet

The reviewed breakout is locally legal but does **not** repair the original
F3 signal failure under the unchanged router transition rules. Its new In2.Cu
handoff reaches an isolated 416-node pocket, with no U2306.5 goal landing and no
permitted via or through transition. No execution packet or route proposal was
created. All native slots remain free.

## Controlled before/after comparison

The complete original two-A dump, all 427 frozen source/control files, numerical
versions, reviewed repair producer, repair card and candidate files are checked
before analysis. Original input SHA256 remains
`613a358b340962e2d1fb13cd898fe8a9558edcbf1a5d69cb93b6d2bd7629e97c`.
The physical dump and every prior source alternative remain unchanged.

Both actual graph windows are `[99,343,37,420]` in `[y0,y1,x0,x1]` cells.
The free, via and goal masks are byte-identical. Exactly one In2.Cu source node
is added. No changed window or obstacle mask explains the result.

| Seeds in the same graph window | B.Cu nodes | In2.Cu nodes | Goal landings reached | Via/through exits |
|---|---:|---:|---:|---:|
| Original source seeds, before repair | 1,034 | 0 | 0 | 0/0 |
| Original source seeds, after repair | 1,034 | 0 | 0 | 0/0 |
| New breakout seed alone | 0 | 416 | 0 | 0/0 |
| All repaired source alternatives | 1,034 | 416 | 0 | 0/0 |

The new pocket occupies `(215.2,262.9)` through `(218.6,265.9)`mm. It does not
touch the window boundary. The six original U2306.5 goal alternatives remain
on In2.Cu at `(241.1,254.0/254.1/254.2)`mm and B.Cu at `(240.0,251.8)`,
`(241.0,251.8)`, `(240.2,253.8)`mm. Every original demand is retained.

Planar four-neighbor components have the same connectivity as the router's
eight-neighbor graph with no corner cutting. Layer unions require the actual
via predicate or a legitimate all-layer terminal, plus passability on both
layers. The source alternatives are graph seeds, not physical copper or
permission to switch layers. The diagnostic intercepts the router before A*
and explicitly forbids both its Python and native search entry points.

## Exact transitions and next obstacles

All **1,444 unique permitted planar edges** within the new pocket pass the
unchanged exact full-width capsule checks against the complete obstacle model.
This certifies movement within the pocket, not a path to the original goal.
The complete cardinal boundary has 148 directed exits: 18 fail exact geometry;
130 are exact-clear but rejected by the current raster predicates. All 148
exits fail the raster foreign-copper threshold; edge/keepout predicates pass.
The retained
receipt gives each exact margin, obstacle owner and individual raster predicate.
This is a disconnected method graph, **not physical impossibility**.

One immediate eastward exit from `(217.0,263.3)` to `(217.1,263.3)`mm fails
foreign-copper clearance by **0.023150681mm**. The exact obstacle is retained
via `9bc880ec-2717-59d4-98ee-1358bf13df02`, diameter/drill 0.6/0.3mm, at
`(217.775,263.350)`mm, on the R2372.1/RV2311.2 net. Southward exits also meet
retained In2 tracks `e3869137-9078-59d2-87c6-635c5cb87225` and
`035ad563-0ea6-501a-8b88-d73c169682c6`; other boundary obstacles and exact
records are included, without claiming one owner globally encloses the pocket.

For comparison, the exit `(217.0,262.9)` to `(217.0,262.8)`mm has a positive
exact clearance margin of **0.035023364mm** but remains raster-blocked.
Its raster foreign-copper distance is 0.424264069mm against the unchanged
0.480710678mm track threshold.
The diagnostic does not silently enable it or change the shared router.

Every one of the 416 pocket sites was also checked as a new through via. On
the untouched input, 406 fail foreign-copper clearance and 336 also fail SMD
restrictions. The leading exact limiting owners are:

| Owner | UUID | Sites where nearest failing foreign copper |
|---|---|---:|
| R2372.2 B.Cu pad | `2bdd7bfd-4621-5c13-961b-81ea50c34a75` | 178 |
| D2320.2/D2321.1 In3.Cu track | `a2851c8d-e2b3-5226-b397-378bfe43d432` | 102 |
| R2372.1 B.Cu pad | `0c36bfa3-d9d5-5b00-b08e-6f731d62b921` | 64 |
| J900213.3 F.Cu pad | `7c949be3-2aab-5659-aedb-8f7373b865a2` | 34 |
| J900213.MP1 mounting pad | `1fedf855-77fc-517d-b00b-b874204a16f4` | 14 |

The remaining ten exact-legal sites are all within 0.317mm of the proposed
breakout via. A *distinct* second via requires at least 0.700001mm by the
existing new-via spacing rule. Thus none provides a legal additional via after
this breakout. The physical breakout via spans all layers, but the reviewed
adapter supplies only an In2 source marker. Reusing that same attachment via
on another layer would require a separately justified transition change and
reachability proof; it is not implemented or credited here.

## Outcome and reproducibility

Stop this In2-only repair as a routing candidate. The local-geometry producer
and prior positive handoff proof remain historical evidence, and the original
empty O1/F3 proposals remain untouched. No second breakout, larger window,
budget increase, package move, copper cut or new physical input is introduced.
U2309 rails remain blocked by their own adjacent pads; AGND is unchanged.
Fixed panel, circuit intent, harness IDs/references/full pin order, sensitive
groups, poses and accepted copper are preserved.

Reproduce with the pinned numerical dependencies and authenticated candidate:

```sh
python3 circuit/routing/epic-242/decision-pilots/terminal-access/analyze_f3_breakout_region.py \
  --candidate design/partition/core-split/candidates/pilots/generated/f3-two-a-c2312-breakout-v1-reviewed \
  --output /tmp/NEW-f3-breakout-region-proof
```

The candidate can be recreated with the prior [repair producer and seals](../README.md)
from [artifact11709240803](https://github.com/Takazudo/zudo-osc-hole-field/actions/runs/38156907050/artifacts/11709240803)
member `fixture/before/dump.json`. Verify the full artifact SHA256
`552347595d8d0dd2bcca5437cbf83cb31ce92ea96cb8a395598faaa493240040`
and every ZIP CRC, then use that member as the input below; both output paths
must be fresh:

```sh
python3 circuit/routing/epic-242/decision-pilots/terminal-access/f3_breakout.py \
  --input /tmp/AUTHENTICATED-ARTIFACT/fixture/before/dump.json \
  --repair circuit/routing/epic-242/decision-pilots/terminal-access/local-breakout/repair.json \
  --output /tmp/NEW-f3-breakout-candidate
python3 circuit/routing/epic-242/decision-pilots/terminal-access/analyze_f3_breakout_region.py \
  --candidate /tmp/NEW-f3-breakout-candidate \
  --output /tmp/NEW-f3-breakout-region-proof
```

[region-proof.json](region-proof.json) binds exact inputs, diagnostic sources,
window/mask hashes and node sets; [exact-boundary.json](exact-boundary.json)
retains all boundary and via checks and complete named owners.

PASS: 83 terminal-access tests, including six new region regressions; six
independent component/geometry regressions; repository checks; baseline
preservation. Independent review is retained alongside these receipts.
Component validation remains manual 68 lines/zero declared placements, without
schematic/placement binding. Full regeneration is NOT RUN because it includes
unadmitted native operations. Full-pair routing, native closure/DRC/parity,
refill/full-warning/eligibility and hardware adoption are NOT RUN.
