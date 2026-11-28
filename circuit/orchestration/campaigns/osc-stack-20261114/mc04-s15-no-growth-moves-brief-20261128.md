# MC04-S15 brief: a no-growth rule for protected parts, then one search for U5110, U8409, U5209 and U5210, Revision 3

2026-11-28. Issue #367 (MC-04 paper gate). Design authority under DS-03 (Fable design agent at high effort, model
`claude-fable-5-2`). Written at head `935a2943` of `local/cloud-engineering-20261127`. Status: **Revision 3; not admitted to
run until the manager confirms its edits against the re-review**. Revision 1 (`c7dd0d32…c9be97dc`) was reviewed
ACCEPT WITH CORRECTIONS (`reviews/mc04-s15-brief-review-20261128.md`, 7 blocking and 6 non-blocking findings).
Revision 2 (`f7c0ed3f…57f7e98b`) met all 13 and was re-reviewed ACCEPT WITH CORRECTIONS (same file, "Revision 2
re-review", 1 blocking and 4 non-blocking points, no third review needed). The tables "Revision 3 changes" and
"Revision 2 changes" map every finding.

Basis: the owner chose option 1 of DS-187, "Close route; try no-growth moves" (2026-11-28 12:26Z). The capacitance
budget route is closed (DS-186). This brief does the two things that option names: it writes the geometric rule, with
its own controls, and it admits one placement search under that rule.

Study only. Nothing is adopted. No board, schematic, specification, BOM, gate record, options file or generated file
changes. Every board and schematic stays an unvalidated draft, check 5 stays NEEDS_DESIGN and #318 stays HOLD. Panel
hardware stays at `design/grid/placements.lock.json` (SHA-256 `297300b0…5b88dbe8`, pinned below).

## What this study answers

Can any of U5110, U8409, U5209 and U5210 stand at its paper pose if a link may displace a protected part, provided
no node that part sits on gets longer than it is now?

It answers that question on pad-centre geometry only. It says nothing about stability, noise, coupling or any other
electrical behaviour. U1415 is out of scope: its blocker is P-K-P-L08's class distance, not a protected part
(S12 disposition, DS-161).

## Inputs this brief builds on

| Item | Path | SHA-256 |
| --- | --- | --- |
| S12 brief, Revision 2 | `mc04-s12-five-ic-joint-search-brief-20261127.md` | `1ecf7da6…e2069a2a` |
| S12 report | `mc04-s12-report-20261127.md` | `d3b9a330…23470a19` |
| S12 disposition | `mc04-s12-disposition-20261127.md` | `6c21cb39…e8516f0b` |
| S14 disposition | `mc04-s14-disposition-20261128.md` | `347e016c…b1e40b3f` |
| S12 library | `scripts/stack/studies/mc04_s12_five_ic_joint/s12.py` | `b1e99358…4c7aadcd` |
| S12 driver | `…/mc04_s12_five_ic_joint/joint_search.py` | `97697c00…e60b6d28` |
| S12 guard | `…/mc04_s12_five_ic_joint/guard.py` | `941c9130…fa88284a` |
| S12 census | `…/mc04_s12_five_ic_joint/census.json` | `92f6fded…dbda095e` |
| S12 result | `…/mc04_s12_five_ic_joint/result.json` | `32532262…99da02ed` |

The design snapshot is the S12 snapshot, `6e5716e7fc011e2f028982f645d18b8d802acb29`, read through the S12 `World`
(a git archive in a scratch root). The fourteen input pins, seven tree pins and ten code pins are those of `s12.py`
(`PINNED_INPUTS`, `PINNED_TREES`, `PINNED_CODE`) and are not restated here. At head `935a2943` the trees
`design/stack`, `design/power` and `design/reports` differ from the snapshot; the study does not read them from the
working tree. `joint_search.py --check` passes at `935a2943` (run by the design authority while writing this brief,
read-only).

## What the existing machinery can measure honestly, and what it cannot

Facts found while writing this brief (read-only probe of the S12 `World`; no file written in the repository):

- **Nothing is routed.** There is no routed length and no copper area for any net. A rule on "routed length" or
  "area" would be a claim the machinery cannot support.
- **Pad centres are available.** Every footprint record carries its pads (`center`, `bbox`, layers), its origin, side
  and angle. `overlay.ancillary_geometry` already places a pad in a scene (mirror on a face change, rotate by the
  effective turn). Net membership per pin comes from `io-partition.json` `package_units` (`s.pins`, `s.net_refs`),
  passives included.
- **The gate re-placement is net-blind.** `links_gate_part2.replace_all` puts each displaced footprint on the nearest
  free ring offset, in a fixed order. The search steers only the link slot; where a displaced part lands is the
  gate's result. A candidate is therefore judged after a rows-only replay, not before it.
- **One rows-only replay costs about 7.3 s** (452 rows) and the `World` builds in about 8 s on the 4-core, 15 GiB
  container.
- **"Paper" has three layers.** The interim board pose (`s.fps`), the base effective scene (paper, then gate rows,
  then retained block poses; `s12.base_effective`) and the scene. At the base 138 of the 1734 protected footprints
  already stand off their `s.fps` pose, and 5 have no position. 21 protected footprints differ from the `6093081c`
  floorplan record and 37 are absent from it, so that record is not used as the reference.
- **The blockers sit on small nets.** The protected nets under the S12 blockers have 2 to 6 pads on board K. Some of
  the blockers' other nets cross a link (for example `/M4A/C24ce01_W` on K and P).
- **Facts added by the brief review** (its read-only probe; not re-measured here): the five open ICs are the five
  positionless protected footprints of the base; board P carries no protected footprint; all 397 protected nets that
  span two boards resolve to a link; 26 of the 41 signals on the six searched links are on protected nets; a link's
  K connector centre lies about 9.5 mm from its slot centre and changes side with the direction; on K, 418
  footprints have pads and no pin record (196 `J`, 204 `MH`, 18 `TP`).

## Design-authority rulings made in this brief

All are provisional until the second review accepts them. Each has a proposed decision row at the end.

### Ruling N1: the measure is taken on pad centres and connector centres, per board

**Poses.** A footprint's pads are placed at its effective pose in a scene (origin, face, turn), transformed as
`overlay.ancillary_geometry.current_pad` does. Three scenes exist: *paper* (every footprint at its `s.fps` pose,
every link at its recorded geometry), *base* (`s12.base_effective`) and the *scene* under test.

**Open ICs.** U1415, U5110, U8409, U5209 and U5210 are positionless at the base. They enter every point set at
their paper pose, in the paper, base and scene figures alike, whether the scene claims them or not. An open IC at
its paper pose is never a moved footprint.

**Point set.** For a net `n` on board `b`, `P(n, b, scene)` is:

- the centre of every pad on `n` of every footprint on `b`; and
- for every live link whose signals include `n` and which has an end on `b`: the centre of `geometry.K_connector`
  when `b` is K, and the centre of `geometry.front_connector` when `b` is the link's front board.

**Figures**, all unrounded:

- **extent**: the half-perimeter of the bounding box of `P` (`hpwl`, the campaign's standing estimate);
- **tree**: the length of the rectilinear (Manhattan) minimum spanning tree over `P`;
- **pin distance**: for each pin `q` of a protected IC on `n` and `b`, and each other point `x` of `P`, the Euclidean
  distance from `x` to `q`. A protected IC is a protected footprint whose reference starts with `U`, open ICs
  included. `overlay.ancillary_geometry` reports the same figure as `input_passives_to_buffer_mm`.

A net with fewer than two points on a board has extent and tree 0 there. The figures are lower-bound style
estimates of the copper a router would need. They are not routed lengths, areas or capacitances, and the report
never calls them that.

### Ruling N2: the no-growth rule (NG), which replaces the displacement stop inside this study only

A footprint is **moved** in a scene when its effective origin, face or turn differs from its base effective pose. A
return to paper is a move like any other. An open IC at paper is not moved (Ruling N1).

A net is **evaluated** when all of these hold:

- it is not a rail (`replacement.RAILS`: `AGND`, `GND`, `+12V`, `-12V`, `+5V`);
- a protected footprint has a pad on it on any board;
- a footprint with a pad on it, on any board, is moved, **or** the `geometry` record of a link carrying it differs in
  any field from that link's base geometry.

An evaluated net is tested on every board where it has a point, board P included. Each board's figures are tested
separately. The sum over boards is reported and is never the test.

A scene passes NG only if all seven tests hold.

| # | Test | Passes when |
| --- | --- | --- |
| NG1 | extent | on every board of every evaluated net, scene extent ≤ limit + 1e-9 mm |
| NG2 | tree | on every board of every evaluated net, scene tree ≤ limit + 1e-9 mm |
| NG3 | pin distance | on every board of every evaluated net, every (point, protected IC pin) pair has scene distance ≤ limit + 1e-9 mm |
| NG4 | face | every moved footprint with a pad on an evaluated net keeps its base effective face |
| NG5 | cover | the scene courtyard of every moved protected footprint, grown 0.35 mm on its face, meets no rectangle of any live link in the scene (`slot_moves.link_rects`, tails and latch margin included), unless that footprint met a rectangle of the same kind of the same link at the base |
| NG6 | position | every footprint that has a position at the base has one in the scene, and no footprint with a pad on an evaluated net is positionless |
| NG7 | pin record | every moved footprint that has pads has a pin record in `io-partition.json` |

Three fixed conventions:

- "No longer" means less than or equal. A tie passes. No figure is rounded before it is compared.
- A point, or a (point, pin) pair, that exists in the scene and not at the limit fails its test. A figure that
  cannot be computed fails NG1, NG2 and NG3 for that net.
- NG4 compares faces only for a footprint that has a position at the base and in the scene; a lost position is
  NG6's to fail. NG4 and NG5 pass when no footprint qualifies. NG1 to NG3 are "not evaluated" when no net is evaluated, and the
  scene then passes them.

Inside this study NG replaces S12 rule 5 (T1), rule 6 (T2), acceptance item A2 and the protected clause of A10. It
does not change DS-150. Outside this study the protected-part rule is unchanged until the owner decides otherwise.

The link clause binds a link move that displaces no part on the net. That goes beyond the owner's sentence and is
kept as the strict reading. Every candidate or scene that fails only through a link-end change, with no footprint
on the failing net moved, is tallied.

### Ruling N3: the limit is the smaller of paper and base wherever a protected part moves

The owner's words are "no longer than on paper". The interim board pose and the base effective scene differ for 138
protected footprints, so the limit is set per evaluated net:

| Net class | Limit for every figure and pair on every board |
| --- | --- |
| **P-moved**: a moved protected footprint has a pad on the net | `min(paper figure, base figure)` |
| **Other**: evaluated only through an unprotected mover or a link end | the base figure |

A P-moved net therefore satisfies the owner's sentence and also may not grow from where the paper gate has it now.
Where the base already exceeds paper (`INHERITED EXCESS`), a protected part on that net may move only if the node
comes back to its paper figure or below. Two tallies make the strictness visible: scenes that fail the limit but
pass `max(paper, base)` ("stricter limit alone"), and scenes that fail only on an inherited-excess net.

### Ruling N4: no exemption for large nets or for ICs, with visible tallies

Only the five rails are exempt. A reference or bus net with many pads is evaluated like any other. A moved
protected IC has every non-rail net evaluated (10 for U8411, 5 for U5205), so a net-blind ring shift of an IC is
unlikely to pass; that is a property of the owner's choice. The screen reports first failures by test, by net and
by moved footprint with ICs and passives separated, and tallies candidates that fail only on nets with more than 8
points. Nothing is relaxed in this run on any tally.

### Ruling N5: a negative is labelled by how it was reached

Because the gate decides where a displaced part lands, a link's single-move screen (stage 2) is not a proof for
joint scenes. The verdict vocabulary is fixed. "A link the IC needs" means `s12.must_move` for that IC:
L12.02.01.02 for U5110, L03.01 for U8409, L13.01.01.02 for U5209 and L13.01.01.01 for U5210.

| Verdict | Allowed only when |
| --- | --- |
| `CANDIDATE SCENE, GEOMETRIC ONLY, NOT ADOPTED` | a written scene passes A1, A3 to A9, A11, NG and A12 |
| `NO SINGLE-MOVE CANDIDATE (COMPLETE SCREEN, OTHER LINKS AT RECORD)` | every rule-4 survivor of a link the IC needs that is gate-legal with all other links at record was replayed and failed, no cap was reached, and the count of survivors illegal at record is given beside it |
| `NO SCENE FOUND (BOUNDED)` | anything else, with the bound named |

No verdict may say "exhaustive" without the qualifier above.

### Ruling N6: everything else is S12, unchanged

- Fixed: every non-searched link (L07 and L08 included), panel hardware, fixings, boards JL, JR, O1, O3 and O5, the
  35 mm radius, the 2.0, 0.5 and 0.25 mm grids, class distances, cable stock, and the five open ICs at paper.
- Rules 1 to 4 of the S12 brief apply as written. Rule 4 keeps protecting U1415's courtyard as well, so this study
  forecloses nothing for it.
- Acceptance items A1, A3 to A9, A11 and A12 apply as written, including S12 Rulings 1, 3, 5 and 6 and the six
  interpretations in the S12 report. A8 and A9 stay in force for a moved protected IC and its decouplers.
- Tails: S12 Ruling 3 still holds for footprints that do not move. NG5 adds a stop only for a protected footprint
  that moves.

### Ruling N7: no real-data positive control exists before the run

NG is shown to pass only on the all-stay scene, on the claimed-IC control and on synthetic fixtures. C18 adds
real nets: it forces every protected net of the all-stay scene through the tests and requires equality. No real
moved scene with a known passing result exists, and none is invented. A real passing scene can arise only from the
search; its check is then `--verify-scene` and the result reviewer's own recomputation of every figure.

## Scope: six links, four ICs

| IC | Link it needs (`s12.must_move`) | Other East links that may have to move with it | S12 blockers now judged by NG |
| --- | --- | --- | --- |
| U5110 | P-K-P-L12.02.01.02 | none | U5205, C5218, R5149, R5268 |
| U8409 | P-K-P-L03.01 | none | C8313, R7216, U8411 |
| U5209 | P-K-P-L13.01.01.02 | P-K-P-L13.01.02.01 | R5253, R5251, C8409, R2335, U5205, RV5205 |
| U5210 | P-K-P-L13.01.01.01 | P-K-P-L03.01, P-K-P-L15.02.01.01 | R8356, U8411, C8313, R7216, R8340, R8456, R4238, R8471, C8408 |

The six links in the table are the **searched links** of S15. P-K-P-L07 and P-K-P-L08 stay at their records. Clusters are S12's South (L12.02.01.02) and East (the other five).
Base link and IC tables are `s12.BASE_LINKS` and `s12.BASE_ICS`.

## Procedure

New code lives in `scripts/stack/studies/mc04_s15_no_growth_moves/`. No S12 file is edited, and no file outside
that directory and the report is written.

### Derived code: four S12 functions cannot be used unchanged

`s12.census` and `joint_search.legal_entry` both call `World.check_rules`, which applies T1 and T2;
`joint_search.cluster_search` rejects on A2 and orders pools by the A2 screen. S15 therefore carries its own copies
in `no_growth.py`, each with one switch `rules` taking `'s12'` or `'ng'`:

| S15 function | Derived from | With `rules='ng'` |
| --- | --- | --- |
| `census_ng` | `s12.census` | stops after rule 4; keeps `D` and the unanchored protected count |
| `legal_entry_ng` | `joint_search.legal_entry` | applies rules 1 to 4 only |
| `check_rows_ng` | `s12.check_rows` | A2 replaced by NG on the effective scene |
| `cluster_search_ng` | `joint_search.cluster_search` | rejects on NG instead of A2; pool order by the stage 2 result |
| `judge_ng` | `s12.judge` and `s12.overlay_part` | A2 and the protected clause of A10 replaced by NG on the effective scene after the overlay; the A8 block search unchanged |

With `rules='s12'` each must behave as its original. Nothing else in them may differ. The README lists, per
function, the lines that differ from the original. The stage 4 driver and `--verify-scene` call `judge_ng`, never
`s12.judge`. The driver and the stage 2, 3 and 4 loops are new code by nature; they are written for S15 and follow
the S12 ones in order and caps. Every other S12 function is imported and called unchanged.

### Arm 0: controls (stop on any failure)

| # | Control | Expected |
| --- | --- | --- |
| C1 | `joint_search.py --check` of S12 | passes: input pins, P3, P4, P11, 0 scenes, 6 checkpoint digests |
| C2 | S12 P8, the full base replay | links, rows, `ways_out` and `consolidation` equal to the base |
| C3 | pad function at paper | for every footprint on K, JL, JR and P, every pad equals its recorded `center`; count reported |
| C4 | pad function under a move | three synthetic poses of R8356 (shift, 90° turn in place, face flip in place) give the hand values written in the test file before the run |
| C5 | extent against the retained estimate, **pads only** | for each S12 locality entry with `input_runs` (nets on JL and JR that cross no link), where the record carries the figure, 1.5 × extent at the base equals the `ancillary_geometry` recomputed `routed_estimate_mm` at one decimal, and each pin distance equals `input_passives_to_buffer_mm` at one decimal |
| C6 | tree figure | equals a brute-force rectilinear spanning tree on every base net with 2 to 7 points; tree ≥ extent on every net |
| C7 | link point | for P-K-P-L03.01 at the base, the K point is the centre of the K connector (y 179.83 to 185.93) and the front point the centre of the front connector (y 204.73 to 210.83), against hand values written before the run; with the direction flipped at the same slot centre the K point moves by more than 15 mm |
| C8 | all-stay scene | 0 moved footprints, 0 evaluated nets, NG passes, A1 to A11 pass; `judge_ng` with `rules='s12'` on this scene equals S12 P11 (passes A1 to A11, places 0 ICs, changes no row, no locality figure above its limit) |
| C9 | claimed open IC | the all-stay scene with U5110 claimed synthetically (its row removed, nothing else changed): 0 moved footprints, 0 evaluated nets, NG passes |
| C10 | S12 census reproduced | `census_ng` with `rules='s12'` for the six links gives counts and accepted lists equal to `census.json`: 0, 0, 27, 0, 0 and 73 survivors for L12.02.01.02, L03.01, L13.01.01.01, L13.01.01.02, L13.01.02.01 and L15.02.01.01; with `rules='ng'` the legal, after-2 and after-4 counts equal `census.json` |
| C11 | S12 stage 3 reproduced | the derived code with `rules='s12'`, pools built as S12 stage 2 did, reproduces `checkpoints/stage3.json` for South and the seven East sets in pool sizes, legality calls, replays, complete scenes and bound; for {U5210}: 13 legality calls and no complete scene |
| C12 | returned S10 scene (`s12.RETURNED`) | the moved protected footprints include new R5249, R5256, R8221, R8331, R8356 and shifted R5253; its NG table is recorded as an observation with no expected verdict (Ruling N7) |
| C13 | base tail count | 71 protected footprints under a K tail at the base (S12 Ruling 3) |
| C14 | link signals | every live link exposes its signal list, `geometry.K_connector` and `geometry.front_connector`; the count of protected nets spanning two boards with no link is 0 (the review found 397 such nets, all resolved) |
| C15 | pin records | footprints with pads and no pin record are listed by board and prefix; on K the list is 196 `J`, 204 `MH` and 18 `TP`; a synthetic scene that moves one of them fails NG7 |
| C16 | worker determinism | the first 12 stage-2 candidates give identical row digests run in sequence and through the worker pool |
| C17 | detachment and guard | a no-op child (a 5-minute heartbeat loop) is started detached under `guard15.py` from a background command whose tool limit is 2 minutes; after the tool limit ends the wrapper, the heartbeat and the guard's per-sample file both keep growing until the child exits |
| C18 | forced evaluation on the all-stay scene | every non-rail net that carries a protected pad (about 2357 by the re-review) is evaluated as if triggered, against the base limit, on every board: every extent, tree and (point, pin) pair equals its base value and passes; the count of those nets whose base figure is above paper is reported beside it |

### Stage 1: census to rule 4, and legality at record (complete, no cap)

`census_ng` for the six links on the three grids. Candidates are reduced to distinct (slot centre, direction, size)
triples, keeping the finest grid's record. Each keeps its displaced set `D` and its unanchored protected count.

Each distinct candidate is then tested once for gate legality with every other link at its record
(`legal_entry_ng`, no replay) and classed:

- **legal at record**;
- **joint-only**: illegal at record, and legal when the call is repeated with the other five searched links
  skipped and everything else placed;
- **dropped**: illegal at record against anything else, L07 and L08 included.

The three counts are reported per link. The geometry a candidate carries into stage 2 is the one its at-record
legality call returns.

### Stage 2: single-move screen under NG

For each legal-at-record candidate, with every other link at its record: build the scene, run one rows-only
replay, apply A1, A3, A4, A6 and NG. Record per candidate the moved footprints, every evaluated net with its class,
its paper, base and scene figures per board, and every failing test.

Replays are spent in this order, up to the cap of 1000:

1. every legal-at-record candidate of L12.02.01.02, L03.01, L13.01.01.02 and L13.01.02.01 (at most 66, 183, 86 and
   179);
2. every legal-at-record candidate of L13.01.01.01 (about 104 by the S12 result review);
3. L15.02.01.01: its S12 survivors of T1 and T2 first, then the rest ordered by unanchored protected count
   ascending, then the S12 cost key.

A link whose legal-at-record candidates were all replayed has a **complete** at-record screen. If the cap cuts
step 3, L15.02.01.01 is **pooled** and the bound is recorded; no IC needs that link, so no complete verdict depends
on it. If the cap would cut step 1 or 2, STOP 5.

A candidate that fails NG as a single move is dropped, which is a bound (Ruling N5). Joint-only candidates are not
replayed here; they go to stage 3.

### Stage 3: scenes per cluster

`cluster_search_ng`, best-first. The pool of a link is its record plus at most 60 entries, one per spot (direction
and 2.0 mm cell): stage 2 passers first by the S12 cost key, then joint-only candidates by unanchored protected
count ascending, then cost. Each complete scene gets one rows-only replay and is judged by A1, A3 to A6 and NG.

Target sets and time, with S12's carry-forward of unused time and a checkpoint after each set:

| Order | Cluster | Target set | Minutes |
| --- | --- | --- | --- |
| 1 | South | {U5110} | 6 |
| 2 | East | {U8409, U5210, U5209} | 14 |
| 3 | East | {U5209, U5210} | 8 |
| 4 | East | {U8409, U5210} | 5 |
| 5 | East | {U8409, U5209} | 5 |
| 6 | East | {U8409} | 4 |
| 7 | East | {U5210} | 4 |
| 8 | East | {U5209} | 4 |

The sets total 50 minutes inside the 55-minute stage ceiling. With carry-forward no set may run longer than 20
minutes. A set whose ICs all have a clean scene is skipped, as
in S12.

### Stage 4: joint scene, overlay rules and full replay

As S12 stage 4, with NG applied to the effective scene after the overlay (paper, rows, overlay poses) in place of
the protected clause of A10, and a checkpoint after each combination. A scene that passes everything but A12 is
reported as "rows clean, gate replay differs" and is not a candidate.

### Ranking

1. ICs placed (more first). 2. Moved protected footprints (fewer first). 3. Protected footprints newly under a tail
(fewer first). 4. The S12 cost key. A node made shorter earns no rank.

## Tests and mutations

Unit tests in `test_s15.py`, written before the recorded run. Each mutation has its full expected vector over NG1
to NG7, in that order: `P` pass, `F` fail, `–` not evaluated. STOP 3 applies when a computed vector differs.

**Fixtures.** All on board K, face B, base equal to paper unless stated. Every part's second pad is on `GND`.
`U1` is a protected IC with its pin on net `N` at (0, 0).

| Fixture | Points on `N` besides the U1 pin | Base extent, tree |
| --- | --- | --- |
| F | protected R2 pad (3, 0), origin (3, 0.75), other pad (3, 1.5); protected R4 pad (5, 2), origin (5, 1.25), other pad (5, 0.5); protected R1 pad (10, 0), origin (10.75, 0), other pad (11.5, 0) | 12, 14 |
| F2 | protected R1 pad (10, 0); protected R3 pad (0, 4); protected R5 pad (0, 1) | 14, 14 |
| F3 | F without R4 | 10, 10 |
| F4 | F3 plus unprotected C9 pad (6, 0) | 10, 10 |
| F5 | F3 plus the K connector centre of link L at (6, 0) | 10, 10 |
| F6 | K: R2 pad (3, 0) and the K connector centre of L at (10, 0). P: the front connector centre of L at (0, 0) and unprotected R9 pad (4, 0) | K 10, 10; P 4, 4 |
| F7 | F3 with R1 pad at (10, 0) on paper and (12, 0) at the base | paper 10, 10; base 12, 12 |
| F8 | F3 with R1 pad at (10, 0) on paper and (8, 0) at the base | paper 10, 10; base 8, 8 |
| F9 | F4 with C9 pad at (6, 0) on paper and (12, 0) at the base | paper 10, 10; base 12, 12 |

| # | Fixture and mutation | NG1 to NG7 | Also expected |
| --- | --- | --- | --- |
| M1 | F: R1 shifted so its pad is at (10.25, 0) | F F F P P P P | extent 12.25, tree 14.25, pin 10.25 |
| M2 | F: R2 shifted so its pad is at (7, 0) | P P F P P P P | extent 12, tree 14, pin 7 against 3 |
| M3 | F2: R5 shifted so its pad is at (0.5, 0.5) | P F P P P P P | extent 14, tree 15, pin 0.7071 against 1 |
| M4 | F: R1 shifted so its pad is at (9, 0) | P P P P P P P | extent 11, tree 13, pin 9 |
| M5 | F: R4 shifted so its pad is at (5, −2) | P P P P P P P | every figure equal: a tie passes |
| M6 | F: R4 pad at (5, −2.000001) | F F F P P P P | |
| M7 | F: R4 flipped to face F in place (pads lie on the mirror axis) | P P P F P P P | |
| M8 | F3: R1 turned 90° in place | F F F P P P P | pad at (10.75, ±0.75): extent 11.5, tree 11.5 |
| M9 | F: M4, with a K tail of a link over the new courtyard and not over the base courtyard | P P P P F P P | |
| M10 | F: M9, with the same link's K tail over the base courtyard as well | P P P P P P P | the NG5 exemption |
| M11 | F4: C9 shifted so its pad is at (12, 0) | F F F P P P P | net class Other, limit base |
| M12 | a part whose non-rail nets carry no protected pad is moved | – – – P P P P | 0 evaluated nets; scene passes |
| M13 | F5: L's geometry changes so its K connector centre is at (12, 0); no part moves | F F F P P P P | tallied "link end alone" |
| M14 | F5: L's direction flips at an unchanged slot centre, K connector centre at (6, −19) | F F F P P P P | the net is evaluated |
| M15 | F6: L moves so its K connector centre is at (9, 0) and its front connector centre at (−1, 0) | F F P P P P P | K 9, 9 passes; P 5, 5 fails; the sum is 14 before and after |
| M16 | F7: R1 shifted so its pad is at (11, 0) | F F F P P P P | P-moved, limit 10; tallied "stricter limit alone" and "inherited excess" |
| M17 | F7: R1 returned to paper, pad at (10, 0) | P P P P P P P | |
| M18 | F8: R1 shifted so its pad is at (9, 0) | F F F P P P P | limit 8; tallied "stricter limit alone" |
| M19 | F8: R1 returned to paper, pad at (10, 0) | F F F P P P P | a return to paper that lengthens a net fails |
| M20 | F9: C9 shifted so its pad is at (11, 0), then (12.01, 0) | P P P P P P P, then F F F P P P P | class Other, limit base 12 |
| M21 | F with U1 an open IC, positionless at the base and claimed in the scene | – – – P P P P | 0 moved, 0 evaluated |
| M22 | M21 with the open-IC convention switched off in the fixture: U1 counts as moved and the base and paper point sets lack its pin | F F F P P P P | scene 12, 14 against 9, 11; the pin pairs are absent at the limit |
| M23 | F: R2 has no position in the scene | F F F P P F P | |
| M24 | F: a footprint with pads and no pin record is moved | – – – P P P F | |
| M25 | M1 with `GND` renamed `AGND2` in the fixture (U1 has no pad on `GND` in any fixture) | F F F P P P P | two nets evaluated, `N` and `AGND2` |
| M26 | one row of a written scene file is changed | not an NG test | its digest check fails |

## Caps

| Cap | Value | Reaching it |
| --- | --- | --- |
| Stage 2 replays | 1000 | cuts L15.02.01.01 only (recorded); STOP 5 if it would cut any other link |
| Stage 3 pool per link | 60 plus the record | recorded as the bound |
| Stage 3 rows-only replays | 400 | recorded as the bound |
| Stage 3 legality calls | 100 000 | recorded as the bound |
| Clean scenes kept per cluster | 3 | recorded |
| Joint combinations | 9 | recorded |
| Overlay searches | 6 | recorded |
| Full gate replays (C2 excluded) | 8 | recorded |
| Worker processes | 3 | never more |
| Resumes | 4 | STOP 6 on a fifth |

## Run bounds

- One executor session on the Cloud container (4 cores, 15 GiB). No GitHub Actions job, second VM or paid capacity.
- **Guard.** `guard15.py`, derived from the S12 guard with the same budgets (tree RSS 8 GiB, `MemAvailable` floor
  7 GiB). It appends every sample to a file and rewrites its summary at every sample, so an interruption loses at
  most one sample.
- **Detachment.** The driver is started detached, in its own session, and C17 proves beforehand that a detached
  child and its guard survive the end of the tool call that started them. If C17 fails, the run does not start.
- **Slices.** The executor watches the detached driver with background commands of at most 100 minutes. If the
  driver is nevertheless interrupted, it resumes from the last checkpoint after re-checking the input pins.
- **Resume cap.** 5 hours in 100-minute slices gives at most 3 boundaries; one more is allowed for a transient
  failure. Hence 4.
- **Checkpoints.** One per arm-0 control, per stage, per 25 stage-2 candidates, per stage-3 target set and per
  stage-4 combination. No unit between checkpoints is longer than 20 minutes.
- **Clock.** The driver adds its own wall time to `checkpoints/run.json` at every checkpoint and refuses to
  continue past a cumulative 5 hours. No outer `timeout` restarts the clock on a resume. Start and end checks are
  timed by the executor and added to the same record.

| Step | Ceiling | Expected |
| --- | --- | --- |
| Start `regen-all.sh` and `pnpm circuit:check` | 15 min | 6.5 min |
| Arm 0 (C10 and C11 rerun the S12 census and stage 3; C17 takes 5 min) | 35 min | 20 min |
| Stage 1 | 15 min | 5 min |
| Stage 2 | 125 min | 45 min. The 3 workers are required: C16 failing is STOP 1. At the cap, 1000 replays take about 41 min of replay time on 3 workers |
| Stage 3 | 55 min | 5 to 50 min |
| Stage 4 | 30 min | 0 to 30 min |
| End `--check`, tests, `regen-all.sh --check`, `pnpm circuit:check` | 15 min | 7 min |
| **Sum** | **290 min** | |

**Wall-time ceiling: 5 hours cumulative across resumes. Expected: 1.7 to 2.7 hours**, and about 1.5 hours if stage 2
leaves no pool.

## Outputs

In `scripts/stack/studies/mc04_s15_no_growth_moves/`: `no_growth.py` (rule, derived functions, driver, `--check`,
`--verify-scene N`), `guard15.py`, `test_s15.py`, `README.md`, `screen.json` (stage 2, one record per candidate), `result.json` (fingerprint, controls,
tallies, verdict per IC, digests), `checkpoints/`, and `candidates/scene-N.json` only for scenes that pass everything.
The report is `mc04-s15-report-20261128.md` in the campaign folder.

The report must give:

- per IC, the verdict in the fixed vocabulary. When a negative verdict would change with the "link end alone" or
  the "stricter limit alone" failures set aside, the verdict line itself names that dependence and gives the count
  of such candidates or scenes, as S12 did for class S;
- per link, the legal-at-record, joint-only and dropped counts, and the counts after each test;
- first-failure tallies by test, by net and by moved footprint, with ICs and passives separated;
- the four strictness tallies: "stricter limit alone", "inherited excess alone", "link end alone" and "large net
  alone";
- for every written scene, every moved footprint with its nets, net class, and paper, base and scene figures per
  board;
- every cap reached, every resume and the cumulative wall time.

## STOP conditions

Stop, write what was found, and return to the design authority. Do not work around any of these.

1. Any control C1 to C18 fails, or an input, tree or code pin differs.
2. `regen-all.sh` at the start leaves a tracked change, or the KiCad oracle it needs is missing (a failure, not a
   skip).
3. The computed vector of a mutation differs from its expected vector.
4. The machinery cannot supply something a ruling assumes: a pad centre, a net's pins, a link's signals or
   connector rectangles, a scene courtyard. No substitute measure may be invented. A moved footprint without a pin
   record is not this STOP: it fails NG7 and the search continues.
5. The stage 2 replay cap would cut a link other than L15.02.01.01, or stage 1 counts differ from C10.
6. The cumulative 5-hour ceiling, a step ceiling, the memory guard, or a fifth resume.
7. An ambiguity in a rule. Take the stricter reading only if it cannot change a verdict, record it, and continue;
   otherwise stop.
8. Any step would write outside the study directory and the report, touch a sibling repository, or need an outward
   action.

A result with no candidate is a valid result, not a STOP.

## What the result can and cannot claim

**It can claim**

- that a written scene places the named ICs at their paper poses at courtyard level, under S12's rules, with no
  evaluated node longer in extent, tree length or pin distance, on any board, than its limit: the smaller of paper
  and base where a protected part moved, the base elsewhere;
- which footprints move in that scene, and by how much each node's figures change;
- that a complete at-record screen of a link found no slot that passes, with the other links at record.

**It cannot claim**

- any electrical behaviour. Equal or shorter pad-centre figures do not bound capacitance, coupling, noise or loop
  stability. A moved part sits beside different copper and different neighbours. S13 and S14 found no node with
  model headroom, so a scene from this study has no electrical evidence behind it at all;
- routed length, area, via count or clearance, because nothing is routed;
- that no placement exists, beyond the labelled domain and bounds;
- c6, checks 2, 3 and 4, latch access, threading, DRC or ERC. These are `NOT RUN`: a study creates and edits no
  board or schematic file, and they are rebound only in a generator task;
- that anything is validated, qualified or released.

**A candidate scene adopts nothing.** Adopting a move needs, in order: a design-authority disposition, an owner
decision to change the DS-150 rule for the named footprints, a separate generator task that edits the options
source and regenerates, and its own independent review. The prototype order review may still refuse geometric
evidence alone, as the S12 disposition warned.

## What the independent reviewer must check

1. That each finding is met as the "Revision 3 changes" and "Revision 2 changes" tables say.
2. That NG as written can be computed from the named data, and that no figure is described as more than it is.
3. That no scene the owner's sentence would reject can pass: open ICs, link ends, every board, the limit of
   Ruling N3 and the pin distance.
4. That every mutation vector follows from its fixture by hand.
5. That dropping T1, T2 and A2 leaves no footprint unjudged: every changed effective pose must reach NG.
6. That the verdict vocabulary cannot overstate a pooled or single-move result.
7. That the run bounds are now consistent, and that nothing lets the executor loosen a test after a result.

## Decision rows proposed for the manager

| ID | Decision |
| --- | --- |
| DS-188 | Owner chose option 1 of DS-187; S15 brief at Revision 3 after two reviews, pending the manager's confirmation of the Revision 3 edits (row in `decisions.md`, updated with this revision) |
| DS-189 (proposed) | S15 Rulings N1 and N2: inside the study, a protected footprint may move if no evaluated net grows, on any board, in pad-centre extent, rectilinear tree length or distance to a protected IC pin, with face, cover, position and pin-record tests; link ends are connector centres; open ICs count at paper; a tie passes |
| DS-190 (proposed) | S15 Ruling N3: the limit is the smaller of the paper and base figures on a net with a moved protected footprint, and the base figure on a net evaluated only through an unprotected mover or a link end |
| DS-191 (proposed) | S15 Rulings N4 to N7: no large-net or IC exemption, fixed verdict vocabulary, all other S12 rules unchanged, U1415 out of scope, and no real-data positive control before the run |

## Evidenced, assumed and not established

- **Evidenced:** the facts in "What the existing machinery can measure"; the S12 counts; `--check` passing at
  `935a2943`.
- **Evidenced by the brief review, not re-measured here:** the facts listed under "Facts added by the brief
  review".
- **Assumed:** that the link records give signals and connector rectangles in a usable form (C7 and C14 test it);
  that 3 workers give identical results (C16); that a detached child survives the tool limit (C17); stage 3 and 4
  times, taken from S12.
- **Not established:** whether any slot passes NG. No candidate was replayed while writing this brief.

## Revision 3 changes

| Point | Change |
| --- | --- |
| R1 (blocking) | "Derived code": `judge_ng` added, from `s12.judge` and `s12.overlay_part`; the stage 4 driver and `--verify-scene` call it; C8 extended so that `judge_ng` with the old rules on equals S12 P11; "everything else is imported unchanged" replaced by a statement that the driver and stage loops are new code |
| R2 | Control C18: forced evaluation of every protected non-rail net on the all-stay scene, equality required, with the count of nets whose base is above paper; Ruling N7 reworded; STOP 1 now covers C1 to C18 |
| R3 | "Outputs": an IC's negative verdict line names its dependence on "link end alone" or "stricter limit alone" failures, with the count |
| R4 | DS-188 cites the review file's current hash and the Revision 3 hash, and keeps the Revision 2 hash as history |
| R5 | Stage 1 says how joint-only is decided and which geometry goes to stage 2; the "120 min in sequence" figure is removed and the worker requirement and cap margin stated; C5 gains "where the record carries the figure"; M25 states that U1 has no `GND` pad |

## Revision 2 changes

| Finding | Change |
| --- | --- |
| 1 (blocking) | Ruling N1: open ICs enter every point set at paper and are never moved; NG6 and the conventions say what a positionless footprint means; control C9; mutations M21 and M22 |
| 2 (blocking) | Ruling N1: link points are the K and front connector centres; Ruling N2: any geometry change triggers, every board is tested, the sum is reported only; "link end alone" tally; C7; M13 to M15 |
| 3 (blocking) | Ruling N3: `min(paper, base)` on nets with a moved protected footprint, base elsewhere; "It can claim" reworded; M16 to M20 state their paper figures |
| 4 (blocking) | Pin distance added as figure and as NG3; C5 checks it against `input_passives_to_buffer_mm`; M2 is the review's example |
| 5 (blocking) | Fixtures F to F9 and a full NG1 to NG7 vector per mutation; STOP 3 reworded; mutations added for the NG5 exemption (M10) and a lengthening return to paper (M19) |
| 6 (blocking) | "Derived code" names the four S15 copies and their switch; C10 and C11 require them to reproduce the S12 census and stage 3 with the old rules on |
| 7 (blocking) | Run bounds rewritten: tested detachment (C17), 100-minute slices, resume cap 4 derived, checkpoints inside stages 3 and 4, a cumulative clock in place of `timeout 5h`, step ceilings summing to 290 minutes, East sets restated to 44 minutes, guard samples appended |
| 8 | Stage 1 classes every survivor as legal at record, joint-only or dropped; the complete verdict is redefined on legal-at-record survivors with the illegal count beside it; L07 and L08 conflicts are dropped; "needs" is `s12.must_move` |
| 9 | Stage 2 replays every legal-at-record survivor of L13.01.01.01 before any pooling; only L15.02.01.01 can be pooled |
| 10 | Ruling N7 states that no real-data positive control exists; C15 lists footprints without a pin record and NG7 fails a scene that moves one |
| 11 | C5 says "pads only"; the link point has its own hand-value control C7 |
| 12 | Ruling N4 and "Outputs": first-failure tally by moved footprint, ICs and passives separated |
| 13 | DS-188 reworded with the Revision 2 rule, this revision's SHA-256 and the review; DS-189 to DS-191 aligned |

## Revision history

| Revision | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-28 | First draft after the owner's choice of DS-187 option 1 (`c7dd0d32…c9be97dc`) |
| 2 | 2026-11-28 | All 13 findings of `reviews/mc04-s15-brief-review-20261128.md` applied (`f7c0ed3f…57f7e98b`) |
| 3 | 2026-11-28 | Points R1 to R5 of the Revision 2 re-review applied; no rule changed |
