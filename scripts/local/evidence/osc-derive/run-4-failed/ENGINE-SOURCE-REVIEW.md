# KiCad 10.0.6 engine source review for the chained-fill questions (read-only)

Requested by coordinator instruction `osc-moya-pinned-engine-source-review-8d393e7d`.
Read-only public retrieval only; no container, binary or native invocation. Prior
analyses (TIMEOUT-ANALYSIS.md 4d9d5c52..., correction 6aa2320b...) are reused, not
repeated; where this review settles a point they left open, it says so.

## Sources retrieved (public, read-only)

Repository `https://gitlab.com/kicad/code/kicad`, tag `10.0.6`, raw file URLs of the
form `https://gitlab.com/kicad/code/kicad/-/raw/10.0.6/<path>`, retrieved
2026-10-23 07:26:34Z to 07:26:42Z (HTTP 200 for all 18 files; see
`retrieval.log`). Retrieved-content SHA256 (full list in `SHA256SUMS` of the
`kicad-src-10.0.6/` evidence copy):

| path | SHA256 |
| --- | --- |
| pcbnew/zone_filler.cpp | 28fa2b555869485254154bbd12b372f6f1057b91b7e3f09d3687eb253a1059dc |
| pcbnew/zone_filler.h | 267544b2f537b521d4bb4bfe54843e51d6deb8df24f0e4fc89368a1a8818f409 |
| pcbnew/zone_settings.h | f3e315d62151569a04a2697008d031fd7bbfe54d3ae64413600de75b492628b7 |
| pcbnew/zone.cpp | 42dbc55c0f3660e2bfe576a09e8f881a4f5121c9f1c6a4e15b89a610b4a10f4c |
| pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr_parser.cpp | 017f74d4fc6476fc1ceec230734fb828640a3c27b52174f6975b749f46458e43 |
| pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr.cpp | 7bb4cbcd549b970e6b615bdf7ef2cc4b439408d4f41e531c442dc2336b817e96 |
| pcbnew/connectivity/connectivity_algo.cpp | 363acbe8bb5ab2ea3e6f14c2dd60952f9d6169e3ef5da92d099c4ca58a0c0d1e |
| pcbnew/connectivity/connectivity_items.h | 4122bbe063360e21ceb0746c581f89aa39285403dd2598b968d58325c9110cb8 |
| pcbnew/connectivity/connectivity_items.cpp | b03acfd6b50f09d95dcb301a9f16eb6b9dc2de772bc5eb1abf41d3c335465a34 |
| pcbnew/python/swig/zone.i | 5671af2a594eaf2ce7f7daa504dc86d0015fdb03f0d14728822db1c0dac76588 |

Image recipe repository `https://gitlab.com/kicad/kicad-ci/kicad-cli-docker` (branch
`main` as of retrieval, 07:27:27Z to 07:30:03Z): README.md 323ec100078edd6694f242bff8f3b3a3edf51bc2a9d77dc865d1287a9af654d6, .gitlab-ci.yml a98b121da828cab79853a90702778349eecc19041bcabb575ec3b448394ba6ce,
Dockerfile.10.0-stable 951871c53466877b8df4363dee3a0d5acbd3b9ba5ffbb3a369160af861face13. Not retrieved: nothing was denied; six guessed
Dockerfile paths returned 404 before the CI file named the real one.

## Relationship between the pinned image and the tag

- The pinned image `kicad/kicad@sha256:18693567...` carries OCI labels naming
  `https://gitlab.com/kicad/kicad-ci/kicad-cli-docker` as its source and was created
  2026-09-22T14:31:54Z; it carries no version or commit label (retained
  `docker image inspect` output, no container run).
- The recipe's release-10 job (`.gitlab-ci.yml` lines 236-243, `build_10_amd64`,
  `DOCKERFILE_PATH: Dockerfile.10.0-stable`, template lines 76-92) builds with
  `--build-arg KICAD_VERSION=<release tag>` (input described at lines 13-14 as "the
  release tag"); `Dockerfile.10.0-stable` line 43 does
  `git clone -b $KICAD_VERSION https://gitlab.com/kicad/code/kicad.git` and lines
  55-66 build it with CMake in Release configuration. README lines 27-33: a
  major.minor.patch tag is locked to that release.
- Retained runtime evidence: every native run requires
  `pcbnew.GetBuildVersion() == '10.0.6'` (payload worker) and the receipts record it.
- Gap, labelled: the digest-pinned image cannot be tied from retained metadata to
  a specific pipeline run or to the Dockerfile revision in force on 2026-09-22; the
  Dockerfile read today is the current `main`. The reading "image binaries were
  built from tag 10.0.6 of the repository read here" is strongly supported by the
  public recipe plus the runtime version string, not proven byte-for-byte.

## What ZONE_FILLER::Fill does (anchors in pcbnew/zone_filler.cpp at tag 10.0.6)

- Entry `bool ZONE_FILLER::Fill( const std::vector<ZONE*>& aZones, bool aCheck, wxWindow* )`
  (zone_filler.h:61; zone_filler.cpp:446). The Python object is constructed through
  the SWIG compatibility constructor with a null COMMIT (zone.i:19-37), so no undo
  commit exists; the payload's `Fill(selection, False)` is this function with
  `aCheck=false`.
- 448: takes the connectivity lock. 501-502: `ClearRatsnest()` then a full
  `connectivity->Build( m_board )` "from scratch, ignoring dirty flags". The build
  (connectivity_algo.cpp:500-523) creates one `CN_ZONE_LAYER` per filled outline per
  copper layer of **every** copper zone on the board, so an existing fill cache
  (the parent's 236 F.Cu outlines) participates in this rebuild before the new
  fill starts. 521: `CacheBoundingBox()` for all zones (no fill change).
- 717-741: only zones in `aZones` are processed: their old fill hash is recorded,
  each (zone, layer) is appended to `toFill`, an island map entry is created, and
  `zone->UnFill()` clears their existing polygons (zone.cpp:478-492). This is the
  only `UnFill` in `Fill`.
- 751-772 (dependency lambda) and 540-584 (`findHighestPriorityZone`): other zones'
  filled areas are read for same-layer higher-priority knockouts only.
- 799-813 (`fill_lambda`): `fillSingleZone` then `SetFilledPolysList` for items of
  `toFill` only. 926: `run_fill_waves( toFill, ... )`.
- 941: `FillIsolatedIslandsMap( isolatedIslandsMap )` with the map keyed by the
  selected zones only. connectivity_algo.cpp:728-790: the selected zones are
  removed and re-added to the graph, then `SearchClusters` runs over the **whole**
  graph; an outline is recorded as isolated when its cluster `IsOrphaned()`, which
  is "no origin pad in the cluster" (connectivity_items.h:537-540). Clusters span
  layers through vias, so copper on other layers (including a non-selected zone's
  cached fill) decides whether a selected outline counts as an island.
- 947-953: `SetIsFilled(true)` for `aZones`. 956-1035: island removal for the map's
  zones: `ALWAYS` deletes every isolated outline, `AREA` deletes small ones, else
  `SetIsIsland`; 973-990 keep a layer untouched when all of its outlines are
  isolated.
- 1037-1130 and 1195-1265: the iterative refill is seeded by removed islands
  (selected zones) and by same-net overlaps where the lower zone is in `aZones`;
  the comment at 1204 states "Only zones in zonesToRefill can change their fill";
  1213-1250 clone the fills of all zones as a read-only snapshot; 1260 writes only
  refill items. 1375-1401: board-edge and minimum-area checks for `aZones`.
  1510-1528: spatial indexes built from every zone's fill (read).
- Settings enum: `enum class ISLAND_REMOVAL_MODE { ALWAYS = 0, NEVER, AREA }`
  (zone_settings.h:68-73). The file reader maps `island_removal_mode N` by
  `static_cast` of the integer (parser 8135-8136). All five copper zones of the
  frozen board carry `island_removal_mode 0` = ALWAYS (board text lines 2510039,
  2520898, 2521119, 2521141, 2521164 region). This settles the enum question left
  open in the correction note: the reviewer's earlier "mode 0 (never)" reading was
  wrong; the engine removes every orphaned outline of a selected zone.
- Serialization: the writer emits `(fill yes)` when `IsFilled()` (2990-2991) and
  every outline of every layer of the zone as `(filled_polygon (layer ...) [(island yes)] (pts ...))`
  (3074-3090). The reader reconstructs one outline per `filled_polygon` into the
  per-layer polygon set and restores the island flag (8314-8366), sets
  `IsFilled` from `(fill yes)` (8016-8017), and clears `NeedRefill` (8576).
  Coordinates are integer nanometres on both sides, so the round trip of outline
  geometry is lossless; triangulation caches and connectivity are not serialized
  and are rebuilt on demand.

## Answers to the research questions

**Q1. Which paths can clear, recompute or modify non-selected filled polygons or
derived connectivity, and when?** In `Fill`, none writes a non-selected zone's
polygons: `UnFill` (741), `SetFilledPolysList` (813, 1260) and island deletion
(1013-1018) all operate on `aZones` or sets derived from it. Non-selected fills
are read (connectivity build 502, same-layer knockouts 751-772, snapshot
1213-1250, index 1510-1528). Derived connectivity is recomputed from scratch at
every `Fill` (501-502) and again by the payload before classification; it is
never serialized. On save the unchanged in-memory outlines are re-emitted by the
same formatter; on reload they are reconstructed losslessly. Caveats: this is a
reading of the tagged source, not an observation on this board (the only chained
run did not reach the post-fill check), and byte-identity of the re-serialized
block is expected from the formatter but not verified; the wrapper's existing
check compares outline counts only (correction note item E1).

**Q2. Does Fill(A), save/reload, Fill(B) equal Fill(A+B)?** Not in general, and the
source shows exactly where they differ. The pre-island polygon of each
(zone, layer) depends only on same-layer geometry and knockouts (fillSingleZone
inputs; 540-584, 751-772), so it is order-independent. Island removal is not: it
is decided on the connectivity graph as it stands when the fill runs (941;
algo 728-790). In a batched call both new fills are in the graph when each
zone's islands are judged; in the sequential order A then B, A's outlines are
judged without B's copper, and under ALWAYS an A-outline whose only path to a
pad runs through a via into B's future copper is deleted, while the batched call
keeps it (and the reverse order has the symmetric case). The iterative refill
(1037-1170) then re-evaluates only zones inside `aZones`, so in a sequential run
the two zones never re-evaluate each other. For this board the condition is
realistic in general: AGND has 177 through vias and 2,286 pads, and only 25 of
those vias sit on the main F.Cu outline of the parent (run 3 cluster data), so
In1.Cu outlines can exist whose pad connection would depend on B.Cu copper.
Whether any such outline actually occurs cannot be decided without computing
the fills.

For the pair C1111.2 <-> U1105.12 the order does not matter, and this is
source-backed: the pad's F.Cu island on the parent contains no via and no track
(saved run-3 clusters; the island is preserved by every `Fill` that does not
select the F.Cu zone, see Q1), the connectivity graph joins items only through
copper contact and vias (algo 823-990), and no B.Cu or In1.Cu polygon can touch
an F.Cu outline. So the pair stays open after either a batched or a sequential
fill of the remaining AGND zones, and its class would be
`OPEN_WITH_ALL_NET_ZONES_FILLED` in both. This is a statement about this pad
pair only, not about equivalence of the two boards.

**Q3. Provable statically here; general observation; unproved.**
Provable for this saved parent and selection: (i) `Fill` does not write
non-selected zones' polygons; (ii) reload reconstructs outline geometry and
island flags losslessly; (iii) all five copper zones use ALWAYS island removal;
(iv) each copper layer carries exactly one copper zone, so same-layer priority
knockouts do not arise (board zone table); (v) the U1105.12 island cannot be
joined by any fill of another layer, so the pair verdict is order-independent.
General observations only: the sequential/batched difference mechanism; the
lossless round trip (integer coordinates). Unproved: whether order-dependent
islands occur elsewhere on this board; byte equality of the re-serialized
parent block; measured runtime of any zone (B.Cu never measured); whether the
image binaries equal a build of tag 10.0.6 beyond the recipe and version
string. Counts are not geometry identity; a synthetic comparison would show its
cases only.

## Smallest next step and conditional proposal

The engine reading removes the preservation uncertainty (E1) at the source
level and settles the enum (E2 part); it does not remove the runtime unknown.
If the parent wants the oracle's class for the pair, two single-zone chained
runs (In1.Cu, then B.Cu, each under the `chained-agnd` numbers) would be
sufficient for this pair's question; they would not be a proof of general
batched/sequential equivalence, and the B.Cu runtime stays unmeasured. Each run
needs its own approval, slot and binding; nothing is proposed as ready here.

Minimal comparison experiment, only if general equivalence itself is wanted
(unapproved, not implemented, all budgets unmeasured): hypotheses H1 the
parent's F.Cu `filled_polygon` text is byte-identical in every child output; H2
sequential (In1 then B.Cu; and B.Cu then In1) and batched outputs differ, if at
all, only in outlines that are orphaned at decision time; H3 the pair class is
identical across all three. Inputs: parent 4a55e0c1... (identity ecf170db...),
zones e389d344 and e67a5bc7, pairs unchanged. Operations: batched Fill(A+B)
(already attempted once, timed out at 260 s), sequential A then B, sequential B
then A, each save/reload. Observables per output: per-layer outline counts,
per-outline vertex hashes and island flags, pad cluster membership, the
non-selected-zone text block hash as an invariant. Stop criteria: existing stage
caps and bounds; first failure preserved; owned cleanup as today. What it would
not prove: equivalence for other boards, other zone sets or other engine builds;
it would show this board's three orders only.
