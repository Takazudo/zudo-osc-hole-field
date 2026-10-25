# F3 integrator placement v1: one pose, no fit

**The one sealed source-only pose fails the frozen service-hook reservation
screen. No combined signal/return route was produced. No second pose, route
search, native run, accepted-board change or adoption occurred.** The prior
weighted-search failure was a path-dependent new-via conflict; this placement
trial does not prove that changing placement was necessary or that no placement
can fit.

Source execution commit: `f6f95aff815c87684303b1491670196ce15a9989`.
Base input checkpoint: `8b82fabd546cae859deade6c05ae110c4d0090b2`.
The [sealed epoch](pose-epoch.json) contains all 24 references, exact old/new
poses and eight input hashes. [Execution receipt](evidence/execution-receipt.json),
[raw result](evidence/result.json), [independent review](evidence/independent-review.json).

## Explicit pose and fit result

U2306 stays at `(239.84,255.08)` mm, B.Cu, 270°. Seventeen of the 24 references
stay fixed. These seven move; coordinates are physical KiCad mm (candidate-local
coordinates plus `(100,50)` mm), all on B.Cu:

| Ref | New XY (mm) | Rotation |
|---|---|---:|
| U2312 | 235.45, 242.58 | 270° |
| C2337 | 234.75, 237.57 | 180° |
| C2338 | 234.75, 247.59 | 180° |
| U2313 | 212.95, 245.47 | 270° |
| C2339 | 212.25, 240.46 | 180° |
| C2340 | 212.25, 250.48 | 180° |
| C2312 | 232.46, 251.40 | 90° |

The two SOIC14 bodies reuse the existing U2312/U2313 sites, with a 0.27 mm
origin correction for U2312's asymmetric serialized courtyard. U2312's bypass
relative poses are retained; U2313's positive/negative bypasses use the vacated
U2312 bypass sites without changing their net identities. C2312 uses the vertical
channel beside U2306. Source identities remain Texas Instruments OPA4196IDR for
U2312/U2313 and LM13700M/NOPB for fixed U2306; no component substitution or
package qualification is implied. C2312's empty source MPN remains unresolved.

The seven moved courtyards have **zero** same-face 0.35 mm gap violations against
the full candidate placement set, **zero** 0.30 mm edge-allocation violations
and **zero** analytic service-hole intersections. This does not certify
preexisting whole-board fit. Two frozen hook reservations still fail:

| Proposed occupant | Fixed hook reserve XY bounds (mm) | Overlap | Prior whole-cluster occupancy |
|---|---|---:|---:|
| C2338 | K-P-50-K: `[232.75,248.25,239.05,249.75]` | **0.984 mm²** | 2.880 mm², previously C2339 |
| U2313 | K-P-45-K: `[215.75,248.25,222.05,249.75]` | **1.7296 mm²** | 1.7296 mm², previously U2312 |

Both proposed occupants had zero overlap with those specific reservations in
their old poses. At the region level, the first occupancy decreases and the
second is inherited from the reused site. Neither is waived: this is **no fit
under the frozen source reservation policy**, not a new native mechanical
collision result. The service-hook model itself remains a proposed access
envelope with installed mating/latch/tool fit NOT RUN. These two failing shapes
are rectangles, so their intersection areas do not depend on circle tessellation.
[Complete polygons and comparisons](evidence/placement-checks.json) are retained.

C2312.1 and U2312.12 become 8.030893475 mm and 9.830031790 mm from U2306.5,
respectively. Meeting the proposed 10 mm proximity objective does not override
the reservation failures or prove a route. The 10 mm target is an engineering
objective, **not an owner constraint**.

## Copper impact and original demands

The source screen authenticated **133,902 accepted source objects**: all
**133,551 segments/vias**, 346 rule areas and five zones. It checked moved pads
against every accepted segment/via, rather than only the reduced fixture's
64,747 segments/vias. Every original object remains byte-identical.

- **33 old same-net pad/object contacts** need explicit continuity review after
  moving their pads.
- **67 candidate pad/foreign-copper clearance conflicts** involve 49 objects/pad
  pairs present in the fixture and 18 absent from that reduced fixture. These
  are source distance checks against retained accepted copper, not native DRC
  counts or proof that all accepted copper belongs in a split candidate.
- **63 unique directly affected objects** have exact UUID, original source hash
  and source-span records. **26 net selectors covering 5,001 source objects**
  define a conservative replay/recheck obligation; they are not a cut list.
  All five original zones remain explicit refill/return obligations.
- The original **C2312.1 ↔ U2312.12** connected group has 44 members and 42
  accepted copper objects. All are identified in the retained account. The
  original touching segments include `2ddb798b-5af4-5dfd-b6a9-21978d734257`
  at C2312.1 and `fc6b2f47-d176-5ee4-ab1b-7e37af094b7d` at U2312.12.
  Their old connection must not be silently carried forward as connected after
  these different pad movements.

[Copper accounting](evidence/copper-accounting.json) records exact contacts,
clearance margins, impacted objects, full-net selectors and preserved native
group evidence. Selectors reference the sealed durable
[`copper-index.jsonl.gz`](../../copper-index.jsonl.gz); every selected UUID/hash
can be reconstructed. No object was removed, moved or added to accepted copper.
Retained old copper is neither wholesale discarded nor automatically transplanted.

The [demand records](evidence/demands.json) retain all four original demand
identities and both original/candidate pad records. Signal remains
**C2312.1 → U2306.5**; return remains **C2338.2 → U2312.5**. All 86 pads in the
24-reference scope retain UUID/net/pin/layer identity. Candidate pad coordinates
are source projections only; no native connected-group receipt is regenerated.
U2309.4/+12V and U2309.11/−12V own-pad escape blockers remain unchanged. No
partial path, single terminal witness or improved proximity solves a demand.

## Smallest justified continuation

**No neighboring placement-group expansion is justified by this one check.**
There is no external-reference courtyard offender. Both failing occupants are
already inside the 24-reference scope; the obstacles are fixed service reserves.
Moving an outside group while keeping these seven poses cannot remove those
two intersections. This does not prove the existing scope has a feasible pose.

The next bounded source task under #245/#253 should keep the complete 24-ref
accounting and fixed U2306, and explicitly revise **U2313 with C2339/C2340** to
clear K-P-45-K, plus **C2338 with its U2312 bypass relationship** to clear
K-P-50-K. Do not move either header, hook reserve, panel item or unrelated group.
C2338 intrudes 0.30 mm into its hook band; an upward-only 0.30 mm correction
would leave only 0.05 mm of its required 0.35 mm courtyard gap to U2312, so it is not an
automatically valid nudge. U2313 intrudes 1.88 mm horizontally and 0.92 mm
vertically into its hook rectangle. Those are intersection dimensions, not
validated replacement translations. No alternative pose has been evaluated.

Before a later routing attempt, that new pose must pass the complete source
placement/reservation checks, declare exact affected-copper preserve/replay
transactions (including BP_INT's old connection), and obtain complete original
signal/return geometry with whole-chain, cross-path, new-via and cumulative-fill
checks. Preserve all six sensitive groups and every bypass owner. If a later
pose actually requires another group to move, return that group's exact
sensitive/bypass closure and copper impact before expanding scope. Native work
still requires separate parent admission; no slot is reserved here.

## Reproduction and checks

The single executed command was:

```sh
PYTHONPATH=/tmp/epic242-numerical-deps python3 design/partition/core-split/candidates/pilots/f3-integrator-cluster-v1/check_pose.py \
  --input-dump design/partition/core-split/candidates/pilots/generated/f3-two-a-c2312-breakout-v1-reviewed/original-dump.json \
  --output /tmp/epic242-f3-placement-v1-result
```

Elapsed source-screen interval: **4.546924181 seconds**; peak memory not measured.
Numerical dependency: Shapely2.1.2 / GEOS3.13.1. The authentic full original dump
SHA256 is `613a358b340962e2d1fb13cd898fe8a9558edcbf1a5d69cb93b6d2bd7629e97c`;
recover it through the retained
[artifact instructions](../../../../../../circuit/routing/epic-242/decision-pilots/terminal-access/local-breakout/region-stop/README.md).
The tool accepts no pose overrides and refuses output overwrite. A future
historical reproduction must use a fresh output directory and the same sealed
inputs; it does not authorize a new candidate or native execution.

PASS: five focused unit tests, independent source and result review, project
checks, before/after circuit checks and frozen baseline verification. Commands
and outputs are retained in `evidence/`. The reviewer reconstructed geometry
and object queries from this same pose; no second main execution or alternative
pose was evaluated. `pnpm circuit:check` scope remains manual68lines/zero declared
placements, no schematic/placement binding. Full regeneration is NOT RUN because
it invokes unadmitted native operations. Whole-chain/cross-path/fill validation
and native closure/DRC/parity/full-warning/eligibility are **NOT RUN** after the
failed placement prerequisite. Accepted boards, fixed panel, circuit intent,
harness IDs/Refs/full pin order and noncore poses are unchanged.
