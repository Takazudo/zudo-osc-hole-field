# MC04-S12 brief: one joint link search for U1415, U5110, U8409, U5209 and U5210 (DS-151), Revision 2

2026-11-27. Issue #367 (MC-04 paper gate). The owner's choice DS-151 (option 1 of
`mc04-s10-revision-2-decision-packet-20261127.md`, packet revision 3), briefed by the design authority under DS-03
(Fable design agent at high effort, model `claude-fable-5-2`). Executor: one session in the Cloud container.

**Kind:** study only, one run. It produces candidate scenes and evidence. It adopts nothing, edits no board,
schematic, spec, BOM, gate record, options file or generated file, and adds no slot hold to the repository. A
generator task and S11's remaining scope follow only on a design-authority ruling on this result. Every board and
schematic stays an unvalidated draft, and check 5 stays NEEDS_DESIGN.

**State:** PLANNED, not admitted. DS-151 requires an independent review of this brief before the run. Revision 1
(SHA-256 `bee0bca7…ab036`) was reviewed ACCEPT WITH CORRECTIONS; this Revision 2 applies all twelve corrections
(revision history at the end). The manager admits the run after the admission checks in "Run bounds".

## What this study answers

Does one scene exist in which the eight named P-K links sit at rule-legal slots within 35 mm of their search
centres, all five open ICs stand at their paper poses, and no protected footprint (DS-150) is displaced, shifted,
turned or moved by an overlay block?

- If yes: up to three ranked candidate scenes, each with the gate rows it produces and its evidence.
- If only for some ICs: the largest clean subset, and a stated reason for each IC left out.
- If no: a negative result, labelled either exhaustive on the stated domain or bounded by a named cap.

## Design-authority rulings made in this brief

These are rulings under DS-03 with the owner notified. None changes DS-150's protected-part rule, DS-06, the panel
centres, a sleeve, a fixing keep-out, a cable or a connector. The manager records them as decision rows; proposed
row text is at the end.

### Ruling 1: locality is judged against the larger of the accepted figure and the pre-S10 effective figure

For every figure of every entry in `design/partition/locality-acceptances.json`:

```text
limit(figure) = max(accepted record value, value recomputed on the base scene at 6e5716e7)
a scene is not clean if recomputed(scene) > limit(figure)
```

- "Base scene" is paper, then the gate rows of `6e5716e7`, then the link-era block poses of `6e5716e7`.
- Larger is worse for every length, distance and capacitance figure. A face or turn field must equal its base
  effective value.
- Values are compared at the precision the record's own generator uses (`overlay.py` `locality` and
  `ancillary_geometry`). The unrounded value is reported beside each. No rounded display number becomes a limit;
  that is the lesson of 7.93.
- A figure whose base value already exceeds its record is labelled `INHERITED EXCESS, UNRULED` in every output. This
  ruling does not accept it. It only forbids making it worse.

Reasons:

1. The accepted figure is the only ruled limit, so a scene inside it needs no new ruling.
2. DS-151 starts the study from the pre-S10 base, so the base is the state a scene is compared with.
3. The accepted-record basis alone fails the base itself in five records (next ruling). Every scene would stop for a
   cause no link search can cure.
4. A base-only basis would turn each inherited excess into an accepted limit without a ruling.
5. The packet's two regressions stay caught: `/E5/HOLD_N` limit 39.81 mm against 65.25 mm, `/E5/READY` limit
   22.39 mm against 30.64 mm.

This replaces, for this study only, the S10 Revision 1 stop "a worse figure in `locality-acceptances.json`".

### Ruling 2: the five inherited mismatches stay outside this study

U5113 (JL), U5112 (JL), U4646 (JR), U4417 (K) and U4526 (K) carry figures that the pre-S10 effective geometry
already exceeds (U5113 at 84.77 mm against an accepted 65.97 mm; U4417 nets up to 29.01 mm over). They are not
ruled here, for these reasons:

- **They are not caused by any of the eight links.** They predate S10 and exist at `6e5716e7` with every link at its
  recorded slot. No scene of this study can cure them.
- **Their disposition is a judgment on an accepted far pose**, not a search result. Each needs either a re-acceptance
  at the effective figure with a reason, or a re-opened placement. That needs its own evidence per record.
- **Ruling them inside a search brief would rebase limits as a side effect**, which is the unlabelled ruling the
  packet review rejected (defect 5).
- **Three of the five cannot move in this study.** All eight links are P-K links; JL and JR rows must stay byte-equal
  to the base (acceptance item A6).

They become a separate design-authority item, **MC04-L1 (locality record reconciliation)**: recompute each of the 16
entries on the effective scene, then re-accept or re-open each of the five with a reason. MC04-L1 does not gate this
study. Whether it gates a later generator task is decided in the ruling on the S12 result. Until it is ruled, the
five are reported in every S12 output as `INHERITED EXCESS, UNRULED`, and Ruling 1 keeps them from growing.

### Ruling 3: a tail does not displace; protected parts under a tail are counted, ranked and reported

The study follows the gate: `links_gate.displaced` displaces footprints under the front connector field, the slot
(both K faces), the K connector field and, for non-exempt packages, the latch margin. It does not displace a
footprint under a front tail or a K tail. A protected footprint under a tail of a searched link is therefore not a
rejection.

- Each scene lists every protected footprint under a tail of a searched link, with the link and the nets it carries.
- The count of protected footprints newly under a tail (not under any tail at the base) is the second ranking term.
- Each such case is an open coupling item for check 4, which a study does not run.

Reasons: DS-150 protects against displacement, and a tail displaces nothing. At the base 71 protected footprints
already sit under a K tail, so a tail rejection would contradict the retained record. A stricter rule would be a new
electrical rule with no evidence behind it. This asserts no electrical acceptance of any node under a tail.

The five open ICs are treated more strictly than this, by rule 4 below: no rectangle of a moved link, tails
included, may meet their courtyards.

### Ruling 4: the protected set and its reference pose

- **Protected set:** every footprint with at least one pin on a net whose name ends `_FB`, `_SUM` or `_SENSE`, ICs
  included, and every IC with a unit whose role starts `high_impedance_input` or `remote_buffer`. Source:
  `design/reports/io-partition.json` (`package_units`). At `6e5716e7` this is 1734 references: K 1182, JL 287,
  JR 265, P 0. A test pins these counts.
- **Reference pose:** in a clean scene each protected footprint is either at its paper pose, or at its base effective
  pose with position, face and rotation unchanged. Nothing else is allowed.
- **A return to paper is allowed**, including its face change. This is a footprint whose base gate row disappears
  because its cause moved away.
- **New, shifted, turned and overlay-moved cases all count** as violations.
- **A row without a position** is a violation only when it is not that footprint's unchanged base row. Seven
  protected footprints have a positionless row at the base: U1318 (JL), U4647 (JR), U1415, U5110, U5209, U5210 and
  U8409. Such a row kept unchanged is the base, not a violation. A protected footprint that has a position at the
  base and loses it is a violation.
- **U5209 and U5210** are judged at paper: (157.95, 206.58) B and (180.97, 204.70) B 0°.
- **Coordinate equality** (ruled 2026-11-27, see `cloud-verification-20261127.md`) follows from this: R5257 stays at
  (174.66, 199.89) B 90°, R5259 at (177.89, 194.16) B. No distance number is a limit.

131 protected footprints already have a gate row at the base (K 103, JL 16, JR 12), seven of them without a
position. They are inherited, they are listed in the report, and they are not improved or accepted by this study.

### Ruling 5: gate rows decide; the S9 ring re-placement does not

DS-148 made the gate `replacement` rows canonical. S10 failed where the S9-A2 scene model and the gate replay
disagreed. In this study a scene is judged on the rows the gate's own re-placement produces for it
(`links_gate_part2.replace_all`), then on the DS-148 overlay rules, then on one full gate replay. The S9-A2
`evaluate` scene model is not an acceptance test here.

### Ruling 6: what widens and what does not

- Only the link search radius widens: 24 mm becomes 35 mm, measured as slot-centre distance from the link's recorded
  search centre (`slot_distance_from_centre_mm`), the metric of the retained 24 mm radius.
- The class distances (PRECISION 40, ANALOGUE 45, WIPER 55, LOGIC 55 mm), cable stock lengths, loop ≥ 0, the DS-87
  compliance limit, the tail rule and the slot web are unchanged.
- The re-placement limits of displaced parts are unchanged: the DS-97 steps (12, 12 and 25 mm) for gate rows and
  24 mm for an S8 block pose.
- No DS-148 hold is carried into the search. Each of the eight links may stay at its recorded slot or move.
- P-K-P-L07 may be tried as a 26-way, exactly as the S11 brief specified. No other link changes size.

**This reading of "the 35 mm join radius" is an interpretation, stated here for the owner.** The retained options
hold three different numbers: `clustering.join_radius_mm` 35.0 (a site joins a link within this distance of the
link's centroid), the slot search radius 24.0, and `way_2_radius_mm` 36.0 (one link's way out). DS-149 and DS-151
say "out to the 35 mm join radius". This brief reads that as the slot search radius of the eight links becoming
35.0 mm, with the clustering itself unchanged. If the owner meant something else, the brief must be revised before
admission.

### Ruling 7: "hard keep-out" means not newly displaced and not shifted; an anchored footprint may be covered again

DS-151 calls every protected part a hard keep-out. This brief implements that as Ruling 4: no protected footprint
may be newly displaced, shifted, turned or overlay-moved. It is not a literal ban on any link rectangle over any
protected courtyard, for two stated reasons:

- the recorded slot of a link ("stay") already covers protected footprints at the base, and that is the base;
- **the anchored exemption of rule 5:** a moved link may cover the paper position of a protected footprint that a
  non-searched link, or an active fixing's part move, already displaces at the base. That footprint is displaced
  either way and its row must still be unchanged (A2), so the moved link adds no displacement.

Every scene lists the anchored protected footprints that a moved link covers, with the anchoring link. A reader can
then apply the literal reading by rejecting any scene whose list is not empty. Tails are covered by Ruling 3.

## Pinned inputs

Snapshot commit: `6e5716e7fc011e2f028982f645d18b8d802acb29`. Every design input is read from this commit, never
from the working tree: HEAD carries the returned candidate's gate rows and four S10 holds.

| Input at `6e5716e7` | SHA-256 |
| --- | --- |
| `design/stack/geometry/links/link-gate.json` | `bcbee2ca955ae06f0d42031899cb3d74501916545893f9454eaa18c89ccbecc3` |
| `design/stack/geometry/links/link-gate-options.json` | `441c998f7801136ebb68e124ae4ac0c1c948533676c815560f716fc7afac2aad` |
| `design/stack/geometry/links/link-era-replacements.json` | `a9af0e8ca4162822dc0608943c8c0813f347b9e5f8ca2b7b612a522ecd25f4d0` |
| `design/stack/geometry/links/link-options.json` | `b0a60bf721b155200fc6a5b9304b20b84767638959c7f009a794f93f4e7bb4c9` |
| `design/stack/geometry/stack-candidate.json` | `22e817eae2af189119ff0a751a8f08099edd735b690954f7c3fbe6e66ff4004d` |
| `design/stack/fixings/fixing-sites.json` | `da13bede1a49ac047540c2236e88659a93f17f74567225dad9d9490f087d92a5` |
| `design/stack/gate-a-open-items.json` | `235619a3c916db1bf9f3eb7a49c79d2df21f0b51a9f877dafe4bf567b9ca9a63` |
| `design/stack/trimmers/relocation-plan.json` | `56ce0dac92688e2a1d7a2844a8a56b1c122c04e92bd03a3db4463600d20075dd` |
| `design/stack/connectors/flex-links.json` | `68700f7190c3e0d86ec942b4811aee470ce3a71b7a15a1599500c9a732094339` |
| `design/partition/locality-acceptances.json` | `54f2c5a5fd64314a4cfee812fe7e781013c3a11bef176d1c31408bed7da45dc7` |
| `design/partition/floorplan-candidate.json` | `12083ea177cad1492f07fa96ad6dbfea8e5f8d2d347199bb555475c5b9e75a38` |
| `design/partition/adopted-placement-pins.json` | `9e827879ebcccea57d247e433a496db71ee1213c87af27b90c81fada2d1218b2` |
| `design/reports/io-partition.json` | `235277959121d8599cbe1b6c6ae65ed4cd3fd3813cf2a8db05d2951ce5b633ce` |
| `design/grid/placements.lock.json` | `297300b067fd646624b9e501791163fa2d60702862b61568753bf92e5b88dbe8` |

Git tree objects at `6e5716e7` (each equals the tree at `8243acdf`, the snapshot the S8 and S9 studies read):
`design/partition` `c4fb824f`, `design/grid` `a07b5141`, `design/mechanical` `673070f1`, `design/stack` `80917ba4`,
`design/power` `6c384211`, `design/reports` `97a4c5ad`, `boards` `f97cf1a3`.

Diagnostic references, read with `git show`, never replayed into a result: the returned candidate
`32580f77c9d0aa9c6067cbad965a6f701050ca5d` (`link-gate.json` `fa944359…ab03a6`, `overlay.json` `5a7a07a8…fc07d3c`).

Code is run from the commit that carries this brief. The executor records its hash and these file hashes, and
stops if a file differs without a recorded reason:

| Code | SHA-256 at `622168b1` |
| --- | --- |
| `scripts/stack/geometry/links_gate.py` | `f4960081d667cc3852cdadb431ba280e11bfae5d0a96cbc3da788514327edf44` |
| `scripts/stack/geometry/links_gate_part2.py` | `e0d584c55f823ceb4743e5cd51ad181b505ac751b7bd71641652ab9397de12ca` |
| `scripts/stack/geometry/links.py` | `928814c730d87538e3eadcb03394bfd7ccc53fd45a86ea92e20c1149d0715f50` |
| `scripts/stack/geometry/stackgeom.py` | `70db6b0833512a20029b743c49d9adf0fe1b69ef8bb4d0063afc3515cb07d7ab` |
| `scripts/stack/studies/mc04_s8_replacement/replacement.py` | `543b02b7baf9d0a1ed531985c4b584fb1a254cc0507903e1c08b95e0ab07916e` |
| `scripts/stack/studies/mc04_s8_replacement/replacement_r7.py` | `81398e90be87f58640f67252dfa5057a9747f4ecae6f7154ffa3a8a5c4091d94` |
| `scripts/stack/studies/mc04_s8_replacement/member_faces.py` | `90f094da93fdeb8c177104d28648c42d1b6b1b16b11cdf01dc788c92df196e81` |
| `scripts/stack/studies/mc04_s9_slot_moves/slot_moves.py` | `7fcbcd8fa5e0d19e8ecd309d6e15a1f94caad6eee237fb635b1ca908b1b16898` |
| `scripts/stack/studies/mc04_s9_slot_moves/slot_moves_a2.py` | `26874e1f7d1e71923ccc88d977f6097bbf1a0c226cd9c9f54c8f00a5c58708d1` |
| `scripts/stack/studies/mc04_s10_l13/overlay.py` | `8acf3bb86873612fed99daf798435fff8301bdd6302a83df2d67ec3b731f3519` |

## The eight links and the five ICs at the base

| Link | Search centre | Recorded slot | Size, cable | Circuits | Members and riders |
| --- | --- | --- | --- | --- | --- |
| P-K-P-L07 | (29.375, 215.9375) | (47.375, 213.9375) +y | FH12-N40, C26618 50 mm | 23 / 40 | 8 sites |
| P-K-P-L08 | (67.3889, 211.6056) | (73.3889, 213.6056) +y | FH12-N40, C26618 50 mm | 27 / 40 | 9 sites |
| P-K-P-L12.02.01.02 | (150.5, 241.0) | (159.0, 237.0) +y | FH12-N8, C29534 50 mm | 6 / 8 | K-P-74; three WIPER riders |
| P-K-P-L03.01 | (232.6667, 184.3333) | (214.6667, 192.3333) −y | FH12-N26, C32128 60 mm | 25 / 26 | 6 sites |
| P-K-P-L13.01.01.01 | (190.1667, 189.6667) | (184.1667, 193.6667) +y | FH12-N8, C29534 50 mm | 8 / 8 | K-P-19, K-P-39, K-P-57 |
| P-K-P-L13.01.01.02 | (167.5, 185.0) | (167.5, 195.0) +y | FH12-N8, C29534 50 mm | 7 / 8 | K-P-54; `/M4B/1_REMOTE`, `/M4B/2_REMOTE` (ANALOGUE) |
| P-K-P-L13.01.02.01 | (167.5, 199.0) | (159.0, 198.5) −y | FH12-N8, C29534 50 mm | 8 / 8 | K-P-75; four WIPER riders |
| P-K-P-L15.02.01.01 | (184.5, 213.0) | (193.0, 213.0) +y | FH12-N8, C29534 50 mm | 7 / 8 | K-P-62, K-P-78, K-P-79 |

The base record holds 72 link records: 62 live and 10 dissolved (P-K-P-L03.02.02.01 among the dissolved), with one
slot hold (JL-K-JL-L02).

| IC | Paper pose | Recorded courtyard [x0, y0, x1, y1] | Link rectangles on it at the base |
| --- | --- | --- | --- |
| U1415 | (62.95, 222.97) B | [58.0, 219.27, 67.63, 226.67] | L07 K field and latch margin; L08 K field, K tail and latch margin |
| U5110 | (157.93, 247.72) B | [153.25, 244.02, 162.88, 251.42] | L12.02.01.02 K field and latch margin |
| U8409 | (203.2, 192.47) B | [198.25, 188.77, 207.88, 196.17] | L03.01 slot and K tail |
| U5209 | (157.95, 206.58) B | [153.0, 202.88, 162.63, 210.28] | L13.01.01.02 K field and latch margin |
| U5210 | (180.97, 204.70) B | [177.27, 199.75, 184.67, 209.38] | L13.01.01.01 K field, K tail and latch margin |

The executor recomputes both tables from the snapshot and stops on a difference (input drift).

## Fixed

- the 438 panel centres and `design/grid/placements.lock.json`; a slot that conflicts with panel hardware is
  rejected and reported with its dimensions, never resolved by moving hardware;
- the 33 modules, the ruled sleeves and the fixing keep-outs;
- every link other than the eight, in centre, slot, direction and geometry;
- every link's size, connector, cable code, stock length and stock-FFC direction, except L07's 26-way variant;
- the allocation, the ground rule, the conductor order and the dissolved set;
- DS-06, and the ten link-era block poses with their acceptances;
- the DS-150 protected-part rule, as defined in Ruling 4.

## Rules a candidate slot must meet (stage 1)

A candidate is one slot centre and direction of one link, with the geometry the retained `links_gate.candidate`
returns for it. It is accepted only if all of these hold.

1. **Gate legality.** `links_gate.search` accepts it with every non-searched live link fixed at its record, the
   other seven searched links left out of `placed`, on the offsets `ctx.grid(step, radius=35.0)` for the 2.0, 0.5
   and 0.25 mm grids. Panel hardware, fixing keep-outs, the P outline, "slot under its own front board", the slot
   web and the tail rule all apply as retained.
2. **Class distance, riders, cable and compliance.** The retained accept of `slot_moves.Arm1.accept_for`: member
   class distances, every hosted rider within its class distance, loop ≥ 0 within the stock cable, K-field
   compliance ≤ 1.0 mm/N (listed above 0.25 with the hold-by-hand flag).
3. **Radius.** Slot-centre distance from the search centre ≤ 35.0 mm. Each candidate is labelled `≤ 24 mm` or
   `24–35 mm`.
4. **Rule 4 of S9-A2, restated.** No rectangle of the candidate (front field, front tail, slot on either K face,
   K field, K tail, latch margin; `slot_moves.link_rects`) meets the recorded courtyard, grown 0.35 mm, of U1415,
   U5110, U8409, U5209 or U5210, whether that IC ends up placed or not. Reuse `slot_moves_a2.Arm1A2.accept_for`.
5. **Protected preflight T1 (paper poses).** Let D be the footprints the candidate displaces under the gate rule
   (`links_gate.displaced(model, front, geo, ctx.latch)`: front field, both slot faces, K field, latch neighbours of
   non-exempt packages). A protected footprint in D is allowed only if it is *anchored*: at the base it is in the
   `displaced` list of a non-searched live link, or it is a `part_moves` entry of an active fixing. Otherwise the
   candidate is rejected and the footprint named. Rejections are tallied in two classes: N (not displaced at the
   base) and S (displaced at the base only by searched links).
6. **Protected preflight T2 (inherited rows).** No rectangle of the candidate, tails and latch margin included, meets
   the base-row courtyard, grown 0.35 mm on its face, of an anchored protected footprint. Such a row would have to
   shift.

The recorded slot of each link ("stay") is always in its pool and is exempt from rules 4 to 6: it is the base.

T1 is deliberately strict for class S. A class S candidate might in principle reproduce the identical row. The
census reports the number of candidates rejected for class S alone, so a zero that depends on this strictness is
visible. They are not explored.

## Search procedure

One driver runs the stages as sequential child processes, never two at once. Iteration order is sorted and
deterministic everywhere. There is no randomness.

### Arm 0: premise and positive controls (stop on any failure)

| # | Control | Expected |
| --- | --- | --- |
| P1 | Recompute the input pins and the two base tables | equal to "Pinned inputs" and the tables above |
| P2 | `slot_moves_a2.py --check` | `result-a2.json` current (`9d524988…48d2`), about 20 minutes |
| P3 | Rows-only replay of the base: `links_gate_part2.replace_all(ctx, inp, links)` on the 72 base link records | 452 rows, byte-equal to the base `replacement.footprints` |
| P4 | Rows-only replay with the `32580f77` geometries of P-K-P-L13.01.01.01, L13.01.01.02 and L13.01.02.01 substituted and `displaced` recomputed | each `displaced` equals the `32580f77` record; rows byte-equal to the `32580f77` `replacement.footprints` |
| P5 | Preflight T1 on those three geometries | class N exactly {R5249, R5256, R8221, R8331, R8356}; class S = {R5253}; a different class S set is reported, a different class N set stops the run |
| P6 | Scene checker on the `32580f77` rows and its `overlay.json` placements | new protected rows exactly the five of P5; shifted protected rows exactly {C8405, R5148, R5253, R8431}; R4238 overlay-moved; ten protected rows removed, all classed "return to paper" or "open IC placed" (R5226, R5228, R5247, R5250, R5251, R5260, R5263, U5207, U5209, U5210), four with a face change (R5251, R5260, R5263, U5207); 56 movements, 16 face changes |
| P7 | Locality recompute | base: the five inherited excesses reproduce (U5113 84.77 mm; `/E5/READY` 22.39 mm, `/E5/HOLD_N` 39.81 mm); `32580f77`: `/E5/HOLD_N` 65.25 mm and `/E5/READY` 30.64 mm are flagged under Ruling 1 |
| P8 | Full gate replay of the base in a scratch root (`links_gate.gate_run`, then `links_gate_part2.run`) | links equal to the base in centre, slot, direction, geometry, size and members; rows, `ways_out` and `consolidation` equal |
| P9 | Full gate replay in a scratch root whose options carry the four S10 holds | the three moved links at their held slots and rows byte-equal to the `32580f77` record; a difference is reported with its diff and stops the run only if a link slot or a protected row class of P6 differs (the gate code changed after `32580f77`) |
| P10 | Protected-set counts | 1734 total; K 1182, JL 287, JR 265, P 0; 131 with a base row, seven of them positionless (U1318, U4647, U1415, U5110, U5209, U5210, U8409) |
| P11 | The all-stay scene: every one of the eight links at its recorded slot | passes A1 to A11 with zero ICs placed, no row change and no locality figure above its limit |

Notes on the replay machinery:

- A scratch root is a `git archive` of the snapshot paths (`replacement.SNAPSHOT_PATHS`) into a temporary
  directory, with only `link-gate-options.json` rewritten there. Nothing in the repository is rewritten.
- Do not call `links_gate.generate` for a replay. It reads the working-tree link-era record (`LINK_ERA`) and applies
  the c6 pins of HEAD. Use `gate_run` and `links_gate_part2.run`.
- Some module-level paths resolve to the working tree, not to the scratch root (for example the cluster baseline).
  The executor lists every working-tree file a replay reads. P8 is the proof that they do not change the result.

### Stage 1: census per link (complete, no cap)

For each of the eight links, and for L07 in both sizes, enumerate every candidate under rules 1 to 6. Write per link
and grid:

- the count legal under rule 1, then the count remaining after each of rules 2 to 6, split by ring;
- the rejection tally by reason, as `result-a2.json` does;
- the T1 tally by class and by footprint, and the count rejected for class S alone.

The census has no cap. A link that an IC needs moved and that has zero candidates is a negative result for that IC
that is **exhaustive on this domain** (three grids, 35 mm, the stated rules). The links an IC needs moved are those
in the base table above, recomputed.

### Stage 2: pools and single-move screen

- **Pool.** Per link: its "stay" slot, plus the cheapest accepted candidate of each *spot*, where a spot is one
  direction and one 2.0 mm cell of slot centre. At most 60 spots per link, cheapest first (gate cost, then the
  retained search key). A pool that is cut at 60 is reported as a cap.
- **The pool reduction is a standing bound.** One candidate per spot means the cluster search is never exhaustive
  over the census, even when no numeric cap is reached. A negative result from stages 3 and 4 is therefore always
  bounded, at least by the pool reduction. Only a census zero is exhaustive.
- **Screen.** Each pool entry is replayed rows-only with that one link moved and the other seven at their records.
  The result (protected-clean or the protected rows it changes) is an ordering key only. It never excludes an
  entry, because a knock-on row can differ in a joint scene.

### Stage 3: scenes per cluster

Three clusters are searched separately and joined in stage 4:

| Cluster | Links, in this fixed order | ICs |
| --- | --- | --- |
| West | P-K-P-L07, P-K-P-L08 | U1415 |
| South | P-K-P-L12.02.01.02 | U5110 |
| East | P-K-P-L03.01, P-K-P-L15.02.01.01, P-K-P-L13.01.01.01, P-K-P-L13.01.02.01, P-K-P-L13.01.01.02 | U8409, U5210, U5209 |

Per cluster, for a target set of ICs (first all ICs of the cluster):

1. Every link whose base rectangles meet a target IC must move; every other link of the cluster may stay or move.
2. Best-first enumeration over the pools in the link order. A link is added to a partial scene only if
   `links_gate.candidate` returns a legal geometry at that slot and direction with the fixed links and the earlier
   chosen links placed, and that geometry still meets rules 2 to 6. Priority: screen-clean entries first, then total
   cost.
3. A complete scene is re-verified link by link with all its other links placed (`ctx.evaluate`).
4. Each complete scene is replayed rows-only and tested with acceptance items A1 to A6 below.
5. Stop the target set at 3 clean scenes, at 400 rows-only replays, at 100 000 legality calls, or at the end of
   its time slice, whichever comes first.

If the full target set of the East cluster yields no clean scene, repeat for {U5209, U5210}, then {U8409, U5210},
{U8409, U5209}, then each IC alone, in this order, stopping at the first set that yields a clean scene for each IC
not yet placed. An IC outside the target set keeps its links free to stay or move, and rule 4 still protects it.

Time slices inside the East ceiling of 75 min, so that the first set cannot starve the others: the full set
25 min, {U5209, U5210} 15 min, and 7 min for each of the five remaining sets. Unused time carries forward to the
next set. A set whose slice ends is closed with what it found.

**When a stage ceiling or a time slice is reached**, the stage or set ends, its partial results are kept, every IC
it leaves undecided is labelled `BOUNDED BY <that ceiling>`, and the driver continues with the next stage. A
target set that was never started is reported as "not searched". Only the 6 h driver ceiling stops the run.

West runs with L07 as a 40-way first. The 26-way variant runs only if the 40-way yields no clean scene for U1415:

- cite `FH12-26S-0.5SH(55)`, C202113 and cable C32128 (60 mm) from `link-gate-options.json` `sizes` and
  `flex-links.json` (`item1_factory_listing`); they are already used by P-K-P-L03.01;
- show with the retained allocation and ground rule that 23 circuits fit 26 positions, or declare the variant dead;
- the variant closes nothing in Gate A check 1;
- **a 26-way scene cannot pass A12 and is therefore not a candidate.** A slot hold carries no size
  (`links_gate.slot_holds`), and the gate's `_place_ladder` tries 40 circuits first and re-clusters at 26 under new
  link ids, which makes the hold stale. A 26-way scene is judged on the rows-only replay with the 26-way geometry
  and on A1 to A11, then written as `ROWS-CLEAN 26-WAY SCENE; gate replay NOT RUN: slot holds carry no size
  selector; NOT A CANDIDATE WITHOUT A GENERATOR CHANGE`. It is ranked below every candidate and goes to the design
  authority as a finding. No full replay is spent on it.

### Stage 4: joint scene, overlay rules and full replay

1. Combine the clean cluster scenes, best first, at most 27 combinations. Replay each rows-only and apply A1 to A6
   on the whole scene. Keep at most 6.
2. For each kept scene, apply the DS-148 overlay rules on its rows (A7 to A11).
3. For each scene that passes, run one full gate replay in a scratch root whose options carry one hold per searched
   link, moved or staying (A12). If an unheld live link moves, one retry is allowed with a hold at that link's
   recorded pose, up to three such holds per scene (DS-148); each is listed with its cause.
4. Rank the survivors and write the best three.

At most 8 full replays in total, retries included.

### Ranking

1. more of the five ICs placed;
2. fewer protected footprints newly under a tail (Ruling 3);
3. fewer links in the 24–35 mm ring;
4. lower total gate cost of the eight links;
5. fewer new and shifted rows;
6. slot coordinates, as the final deterministic tie-break.

## Acceptance of a scene

A scene is a candidate only if every item holds. Each failed item is recorded with the footprints or links named.

| # | Item | Test |
| --- | --- | --- |
| A1 | Placed ICs | each IC the scene claims has no row in the scene's rows and stands at its paper pose; an IC not claimed keeps its base row |
| A2 | Protected footprints (Ruling 4) | for every protected footprint: no row (paper), or a row equal to its base row in `new`, `new_face` and `turned` (an unchanged positionless base row included); no new, shifted or turned row; a positionless row is a violation only if the base row had a position or did not exist |
| A3 | No lost position | every footprint with a position at the base has one; every new row has one |
| A4 | Trimmers | DS-146 rule 3: every new or shifted `RV*` or `RVO*` row keeps the trimmer's paper face, and none newly lands on K's front face (a base row such as RV4204's F to F row is unchanged and is not a violation) |
| A5 | Link figures | per moved link: loop, compliance, hold-by-hand, trim leads, members and riders against their limits, radius ring, direction change if any |
| A6 | Untouched boards | every row on JL, JR, O1, O3 and O5 is byte-equal to the base |
| A7 | Link-era poses | the ten link-era block poses of the base are legal in the Field built from the scene's rows (`member_faces.py`) |
| A8 | Block rule | for every IC with a new or shifted row, and every IC whose decoupler has one: decoupler on the IC's face and no farther from the IC than at the base effective scene, compared unrounded; where the gate pose breaks this, one S8 block search within 24 mm (`overlay.py` method); no pose means the scene fails |
| A9 | Placed-IC blocks | for each placed IC: its S8 block members are at paper, or (decouplers only) on the IC's face and no farther than at paper; an R_ISO with a new or shifted row is no farther from its op-amp than at the base |
| A10 | Effective scene | paper, then rows, then overlay poses (`overlay.effective_scene`, `effective_turns`, `movement`): no protected footprint differs from its base effective pose except by a return to paper; a rotation in place counts as a difference |
| A11 | Locality (Ruling 1) | every figure of all 16 entries within its limit; inherited excesses labelled |
| A12 | Full gate replay | no hold error; each of the eight links at its scene slot and direction; every unheld live link byte-equal to the base in centre, slot, direction and geometry; 62 live links; the dissolved set, `ways_out` and rider hosts unchanged except through the holds; the replayed rows equal the rows-only rows of the scene |

A scene that passes A1 to A11 but fails A12 is reported as "rows clean, gate replay differs", with the difference.
It is not a candidate. A 26-way L07 scene never reaches A12 (stage 3).

## Tests and mutations

All in `test_s12.py`. The outcomes are pinned. Slot coordinates are taken at full recorded precision from the
source records, never from the two-decimal figures of a report. The tests read `result.json` and run the mutations;
they do not re-run the search.

| # | Mutation or control | Must give |
| --- | --- | --- |
| M1 | P-K-P-L13.01.01.02 at (176.0, 196.25) −y, the returned S10 pose | T1 rejects, naming R5256 |
| M2 | P-K-P-L13.01.01.02 at (176.0, 198.25) −y, the S9-A2 joint pose | T1 rejects, naming R5257 |
| M3a | a P-K-P-L13.01.01.02 candidate with its slot over R5259 (x = 176.0, y in 192.75–195.0) | T1 rejects, naming R5259 |
| M3b | R5259 under the K tail only, as at (176.0, 196.25) −y, with the R5256 hit masked out | not rejected for R5259; R5259 listed under "protected under a tail" |
| M4 | P-K-P-L13.01.01.01 at slot centre (201.1667, 197.4167) +y, the returned S10 pose as recorded | T1 rejects, naming R8356 |
| M5 | P-K-P-L13.01.01.01 at slot centre (202.1667, 195.6667) +y, the S9-A pose as recorded in `mc04_s9_slot_moves/result.json` | rule 4 rejects: "covers the recorded courtyard of U8409" |
| M6 | a block pose that turns a protected member in place, position and face unchanged | A10 rejects (the case fixed at `557b5a6e`) |
| M7a | the base rows with R8431's row shifted by 0.25 mm | A2 rejects, naming R8431 |
| M7b | the base rows with R5251's row deleted (a return to paper with a face change) | A2 accepts |
| M8 | U4537's block at its withheld S10 overlay pose (149.97, 182.68) F 180° | A11 rejects `/E5/HOLD_N` and `/E5/READY` |
| M9 | a candidate at 35.25 mm from its search centre | rule 3 rejects |
| M10 | a rider beyond its class distance; a new trimmer row that changes face from paper B to K's front face | rule 2 rejects; A4 rejects |
| M11 | any written candidate scene with one slot moved by 0.25 mm | its pinned digest fails |
| M12 | the base rows with the position of a protected footprint removed (R8431's row set to "no position") | A2 rejects, naming R8431; the seven unchanged positionless base rows are still accepted |

## Run bounds (ORCHESTRATION.md section 3)

| Bound | Value |
| --- | --- |
| Environment | the Cloud container: 4 CPU, 15 GiB RAM, no swap |
| Interpreter | `/home/user/venv312/bin/python` (Python 3.12 with the repository-pinned NumPy 2.2.6, SciPy 1.15.3 and Shapely 2.1.2), as in `cloud-verification-20261127.md`; every study step and check uses it |
| Heavy processes | one at a time, for the start checks, the driver and the end checks alike; the driver runs stages as sequential children; single-threaded Python; `generate_chain` and any worker pool are not used |
| Memory budget | 8 GiB for the whole process tree, enforced (a cgroup scope if available, otherwise a watchdog that samples the tree's RSS every 5 s and aborts), over the start checks, the driver and the end checks, the oracle container included; expected driver peak 2.5 to 4.5 GiB; the peak of `regen-all.sh` is not measured by this brief and is recorded by the run |
| Admission | `MemAvailable` ≥ 11 GiB, no other heavy process running, at least 5 GiB of free disk, the pinned KiCad image present, and a clean tree. This brief, its review and the DS-151 decision row are committed by the manager before admission, so that the tree is clean and the code commit is fixed |
| Fingerprint | written to `result.json`: OS and architecture, CPU quota and affinity, cgroup `memory.max` and `memory.current`, `MemAvailable`, swap, disk, the interpreter path with Python and package versions, the KiCad image digest `kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec` with its `kicad-cli version` output, the process list and the commit |
| Start checks | `regen-all.sh` (about 313 s measured in this container; ceiling 15 min, `timeout 15m`) and `pnpm circuit:check` (ceiling 5 min) |
| Driver | 6 h, enforced with `timeout 6h`; stage ceilings: arm 0 45 min (it holds the one `slot_moves_a2.py --check`, about 20 min), stage 1 45 min, stage 2 45 min, stage 3 West 20 min, South 10 min, East 75 min in slices, stage 4 60 min; expected 2 to 3 hours |
| End checks | `joint_search.py --check` (ceiling 10 min, expected under 3 min), `test_s12` (ceiling 15 min), `regen-all.sh --check` (about 313 s; ceiling 15 min) and `pnpm circuit:check` (ceiling 5 min) |
| What `--check` recomputes | it does not re-run the search. It recomputes the input pins, re-runs P3, P4 and P11, re-runs the rows-only replay and A1 to A11 for every written scene, and compares the scene digests and the checkpoint digests recorded in `result.json`. A full re-run is `joint_search.py --rebuild`; it is a separate admitted run under these same bounds and is not part of the end checks |
| Total wall time | ceiling 7 h 10 min (20 min start, 6 h driver, 50 min end, each under its own `timeout`); expected 2.5 to 3.5 hours |
| Caps | pool 60 spots per link; 400 rows-only replays and 100 000 legality calls per target set; 27 joint combinations; 6 scenes into the overlay rules; 8 full gate replays |
| Pilot | before stage 1 proper: the census of P-K-P-L13.01.01.01 on the 2.0 and 0.5 mm grids, timed; if the projected stage 1 total exceeds 45 min, stop and report; do not drop a grid to fit |
| Checkpoints | one JSON per finished stage in the study directory; a resume is allowed only from a finished stage with unchanged input pins |
| Retries | at most one, and only for a proven transient failure; a cap or ceiling is never retried |

Measured while writing this brief, read-only, in a scratch directory, with the system Python 3.13.18 of this
container (the executor repeats them as P3, P4 and P8 and records its own figures):

| Probe | Result |
| --- | --- |
| Full gate replay of the snapshot (`gate_run` and `links_gate_part2.run`), HEAD code | 159 s (139 s in `gate_run`), peak RSS 2115 MB; links, 452 rows, `ways_out` and `consolidation` equal to the base |
| Rows-only replay of the base | 4.0 s, peak RSS 291 MB, byte-equal |
| Rows-only replay with the three moved S10 links | 3.9 s; all three `displaced` lists and all rows byte-equal to the `32580f77` record |

The probes used the system Python 3.13.18, not the run's interpreter; the executor's own figures with
`/home/user/venv312/bin/python` replace them. The stage estimates rest on these and on the S9-A2 run (19 minutes for about 25 link searches and 360 scene
evaluations). The census time at 35 mm is the least certain figure, hence the pilot.

A cap or ceiling that is reached is reported as a cap, never as "no fit". The study uses no GitHub Actions job, no
second VM and no paid capacity.

## Outputs

Allowed writes, and nothing else:

- a new directory `scripts/stack/studies/mc04_s12_five_ic_joint/` with the driver (`joint_search.py`, with `--check`
  and `--verify-scene N`), the tests, a README, `census.json`, `result.json` and `candidates/scene-N.json`;
- the report `circuit/orchestration/campaigns/osc-stack-20261114/mc04-s12-report-<date>.md`.

Each `candidates/scene-N.json` holds:

- the eight slots as `slot_holds`-shaped entries (link, front board, centre, slot centre, direction), plus any extra
  recorded-pose hold with its cause; these are candidate data, not entries of the options file;
- the A5 figures per link and the L07 size;
- the row changes against the base (removed, new, shifted) with face, distance and step, and their protected class;
- the effective-scene movement ledger, the protected ledger (returns to paper, inherited rows kept, parts under a
  tail, and the anchored protected footprints a moved link covers, with the anchoring link, Ruling 7), and the
  overlay block poses with their reasons;
- the locality table: accepted, base, scene, limit and label per figure;
- the workload change against DS-128: links, latches, leads to trim by reference, the hold-by-hand list, lengthened
  tails and connectors by size;
- logic blocks moved that have a clock or RC timing node, and every direction change;
- a digest of the scene and the status line "CANDIDATE SCENE, STUDY ONLY, NOT ADOPTED, UNVALIDATED DRAFT".

The report gives per IC one of: `PLACED IN THE JOINT SCENE`, `PLACED ONLY IN A PARTIAL SCENE`, `NO SCENE FOUND
(BOUNDED BY <cap or ceiling>)`, `NO SCENE FOUND (BOUNDED BY THE POOL REDUCTION)` when no numeric cap or ceiling was
reached, or `NO CANDIDATE ON THIS DOMAIN (EXHAUSTIVE)` for a census zero. It lists what is not established: c6, checks 2, 3
and 4, threading, routing, DRC, coupling under tails and every electrical acceptance.

Forbidden: any change under `design/`, `boards/`, `doc/`, any generated file, `link-gate-options.json`,
`link-gate.json`, `link-era-replacements.json`, `placements.lock.json`, `decisions.md`, a commit of a scratch root,
fabrication or order files, supplier contact, a deploy, and any GitHub action beyond what the manager orders.

## Start and end checks

- Start with `bash scripts/checks/regen-all.sh` (about 5 minutes) and `pnpm circuit:check`. Project rule 3 applies:
  a tracked regeneration is committed on its own before any study file and is named in the hand-back. It cannot
  change the study, which reads the snapshot.
- **`regen-all.sh` needs the pinned KiCad oracle** (`scripts/kicad/run.sh`, `smoke.sh`, `export-master.sh`). Under
  project rule 4 a missing oracle is a failure, not a skip: the run is not admitted without the pinned image, and
  its digest and version go into the fingerprint.
- End with `joint_search.py --check`, `python -m unittest test_s12`, `regen-all.sh --check` and
  `pnpm circuit:check`. Their output must be unchanged apart from the new study files.
- `slot_moves_a2.py --check` runs once, as P2. It is not repeated at the end; the end checks instead confirm that the
  hashes of the S8, S9 and S10 study files are unchanged.
- All start and end steps run one at a time under the bounds in "Run bounds".
- Oracle steps: `KiCad DRC, ERC: NOT RUN: a study creates and edits no board or schematic file`. `c6`,
  `link_electrical` (checks 3 and 4), latch access and the threading procedure: `NOT RUN: rebound once in the
  generator task`. `ngspice`: `NOT RUN: no simulation is admitted by this brief`. No oracle step runs inside the
  study itself; the pinned KiCad image is required only for the start and end checks above.

## STOP conditions

Stop, write what was found, and change nothing further on any of these:

1. input drift: a pin, a base table or a code hash differs;
2. any arm 0 control fails (P1 to P11), with the stated exceptions in P5 and P9;
3. the admission check fails (the pinned KiCad image missing included), the memory watchdog fires, a start or end
   check exceeds its ceiling, or the 6 h driver ceiling is reached;
4. the pilot projects stage 1 beyond its ceiling;
5. a clean result would need a panel centre, sleeve, fixing or hold change at a non-recorded pose outside the eight
   links, a fourth extra recorded-pose hold, a new part, a cable or connector code not in the retained evidence, a
   size change on any link other than L07, or a radius beyond 35 mm;
6. a rule of this brief turns out to be ambiguous in a way that changes an outcome: take the stricter reading, list
   it under "Interpretations made", and stop only if no stricter reading exists;
7. any need to write outside the allowed paths.

No second run, no relaxed rule, no radius beyond 35 mm, no adoption. A stage cap, stage ceiling or time slice that
is reached is not a STOP; it is reported as a bound and the driver continues.

## What the independent reviewer must check

The reviewer is not the executor and not the author of this brief. The review is read-only.

1. The inputs came from `6e5716e7`, and no working-tree design file reached a result; the list of working-tree
   files the replay reads, and P8.
2. P3 to P7 with own code: the five new protected rows, the four shifted rows, R4238, and the two U4526 figures at
   `32580f77`.
3. The protected set by an own derivation from `io-partition.json`: 1734, and the 131 base rows.
4. For each candidate scene, `--verify-scene N`: the rows-only replay, A1 to A12 and the scene digest.
5. For each candidate scene with own code: no protected footprint differs from paper or its base effective pose,
   rotation included; U5209, U5210, R5257 and R5259 at their paper coordinates.
6. Rule 4: no rectangle of a moved link meets a grown courtyard of the five ICs.
7. The tail list of each scene against Ruling 3, and that no tail case was counted as clean silently.
8. The locality table against Ruling 1, with the inherited excesses labelled and none treated as accepted.
9. Every negative result: whether it is exhaustive (a census zero) or bounded (which cap), and whether a class S
   strictness zero is disclosed.
10. All mutations fail as stated, and M3b and M7b pass as stated.
11. The run bounds: fingerprint, peak memory, wall time, caps reached.
12. Nothing outside the allowed paths changed, no hold entered the options file, and no output calls a draft
    validated, qualified or released.
13. The 26-way evidence for L07, if that variant was used, and that no 26-way scene is presented as a candidate.
14. P11, and that the seven positionless base rows are treated as the base.
15. Per scene, the list of anchored protected footprints a moved link covers (Ruling 7).

## After the run

- A candidate scene goes to the design authority for a ruling. Only then does one generator task rebind c6 and
  checks 2 to 4 once, as DS-146 intended.
- An IC without a scene goes back to the owner by itself with its reason: U8409, U1415 and U5110 with their DS-149
  fallbacks, U5209 and U5210 with options 2 to 4 of the packet. The fold-cell vendor-model simulation can be
  admitted alongside at any time; it is not part of this study.
- S11's start gate, its `S10_RESULT_COMMIT` pin and its "every slot hold in the pinned options file" are superseded
  by DS-151. Its link scope is contained in this study.
- **A scene with a link in the 24–35 mm ring cannot be adopted by holds alone.** `links_gate.check_placement_terms`
  rejects a recorded slot beyond the 24 mm search radius of its centre (36 mm only for a way-2 link). The generator
  task for such a scene needs a reviewed change to the checker or the options. The report flags every scene this
  applies to.
- S10 Revision 1 stays returned.

## Decision rows proposed for the manager

| Row | Text |
| --- | --- |
| Brief | MC04-S12 brief issued for DS-151: one joint search on the `6e5716e7` snapshot, eight P-K links to 35 mm, five ICs at paper, protected footprints a hard keep-out, gate rows as the scene test. Not admitted until its independent review. |
| Ruling 1 | Locality figures in S12 are limited by the larger of the accepted record value and the pre-S10 effective value; an inherited excess is labelled and not accepted. |
| Ruling 2 | The five inherited locality mismatches (U5113, U5112, U4646, U4417, U4526) stay outside S12 and become item MC04-L1 for the design authority. |
| Ruling 3 | In S12 a tail does not displace (the gate rule); protected footprints under a tail of a searched link are counted, ranked and reported as open coupling items. |
| Ruling 4 | The protected set is every footprint with a pin on a `_FB`, `_SUM` or `_SENSE` net and every input-buffer IC; its reference is paper or the unchanged base effective pose; a return to paper is allowed; an unchanged positionless base row is not a violation. |
| Ruling 5 | In S12 a scene is judged on the gate's own re-placement rows, then the DS-148 overlay rules, then one full gate replay; the S9-A2 ring re-placement is not an acceptance test. |
| Ruling 6 | "Out to the 35 mm join radius" is read as the slot search radius of the eight links becoming 35.0 mm; class distances, cable and compliance limits and re-placement limits are unchanged; no DS-148 hold is carried; L07 may be tried as a 26-way. This reading is an interpretation and is put to the owner. |
| Ruling 7 | "Hard keep-out" is implemented as not newly displaced, not shifted, not turned and not overlay-moved; a moved link may cover a protected footprint that a non-searched link already displaces, and each such footprint is listed per scene. |

Decided by: design authority (DS-03, Fable agent at high effort), owner notified. Reverse by: a design-authority
ruling on the S12 result, or an owner decision.

## Evidenced, assumed and not established

| Class | Items |
| --- | --- |
| Evidenced from retained sources | the pins and tree hashes; the two base tables; the protected counts; the `32580f77` row classes used as controls; the three probes above |
| Assumed | the stage time estimates other than the three probes; that 60 spots per link and the stage caps are wide enough to be useful |
| Not established | whether any scene exists out to 35 mm; any electrical behaviour; any link-era routing; c6 and checks 2 to 4 for any scene |

## Revision history

Revision 1: SHA-256 `bee0bca7793f8222c970c94780607aa3bdce0ee79b5fd15f8e7dae30c28ab036`, reviewed ACCEPT WITH
CORRECTIONS by an independent Fable 5.2 reviewer. Revision 2 applies all twelve corrections; nothing else changed.

| # | Severity | Correction | Where |
| --- | --- | --- | --- |
| 1 | HIGH | A positionless protected row is a violation only when it is not the footprint's unchanged base row (seven such rows exist at the base); control P11 and mutation M12 added | Ruling 4; A2; P10, P11; M12; STOP 2; reviewer item 14 |
| 2 | MEDIUM | `regen-all.sh` needs the pinned KiCad oracle; the image is required for the start and end checks and its digest is in the fingerprint | Run bounds (Admission, Fingerprint); Start and end checks; STOP 3 |
| 3 | MEDIUM | Bounds now cover the start and end checks; `--check` defined as a verification, not a re-run; `slot_moves_a2.py --check` runs once; total wall time stated | Run bounds; Start and end checks |
| 4 | MEDIUM | Behaviour at a stage ceiling defined; East target sets get time slices | Stage 3; STOP conditions (closing paragraph) |
| 5 | MEDIUM | A 26-way L07 scene is judged rows-only, labelled, and is not a candidate | Stage 3 (26-way list); Acceptance (closing paragraph); reviewer item 13 |
| 6 | LOW–MEDIUM | A4 reworded to DS-146 rule 3: a trimmer keeps its paper face and none newly lands on K's front face | A4; M10 |
| 7 | LOW | Rulings 5 and 6 added to the proposed rows; the 35 mm reading marked as an interpretation for the owner; the `check_placement_terms` consequence added | Ruling 6; After the run; Decision rows |
| 8 | LOW | The anchored exemption is listed as Ruling 7, and covered anchored footprints are listed per scene | Ruling 7; Outputs; Decision rows; reviewer item 15 |
| 9 | LOW | The pool reduction is named as a standing bound, with its own result label | Stage 2; Outputs |
| 10 | LOW | Fingerprint extended (OS and architecture, `memory.current`, interpreter); the run's interpreter named; the probes' interpreter noted | Run bounds (Interpreter, Fingerprint, probe note) |
| 11 | LOW | M4 and M5 use the recorded coordinates at full precision | Tests and mutations |
| 12 | LOW | The brief, its review and the DS-151 row are committed before admission | Run bounds (Admission) |
