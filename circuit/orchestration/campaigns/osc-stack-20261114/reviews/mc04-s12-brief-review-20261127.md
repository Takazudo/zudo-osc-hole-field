# Review of the MC04-S12 brief (DS-151): ACCEPT WITH CORRECTIONS

Reviewer: independent read-only session, model Fable 5.2 (`claude-fable-5-2`), the same model family as the brief's
author but a separate session. Nothing was edited, committed, pushed or run beyond short read-only scripts in a
scratch directory. This file is the only file written, at the coordinator's request after the review.

Under review: `../mc04-s12-five-ic-joint-search-brief-20261127.md`, SHA-256
`bee0bca7793f8222c970c94780607aa3bdce0ee79b5fd15f8e7dae30c28ab036` (matches the expected value). Repository
`zudo-osc-hole-field` at `622168b1`. At review time the brief was untracked and the DS-151 row was an uncommitted
change to `decisions.md`. Every board and schematic stays an unvalidated draft.

## The brief stays inside DS-151, with five required corrections before admission

It keeps the five ICs, the eight links, 35 mm, the `6e5716e7` snapshot, S10 Revision 1 returned, DS-06 and the
fallbacks. Every addition beyond the owner's text is labelled as a design-authority ruling, apart from the points in
corrections 6 to 8.

### Required corrections

1. **HIGH: A2 and Ruling 4 fail every scene as written, including the base (lines 109, 360–361).**
   - A2 forbids any protected row without a position, and Ruling 4 counts such a row as a violation.
   - At `6e5716e7`, seven protected footprints have a base row with `step: "no position"`: U1318 (JL), U4647 (JR),
     U1415, U5110, U5209, U5210 and U8409.
   - U1318 and U4647 can never change in this study (A6), so the full five-IC scene fails A2 too.
   - A1 says an unclaimed IC "keeps its base row", which contradicts A2 for every partial scene.
   - STOP 6 forces the stricter reading, so the run would return an empty result.
   - Fix: a positionless protected row is a violation only when it is not that footprint's unchanged base row.
   - Add a control P11: the all-stay base scene passes A1 to A11 with zero ICs placed.
   - Add a mutation: a protected footprint that has a position at the base and loses it is rejected.

2. **MEDIUM: the brief says the pinned KiCad image is not required, but its own start and end checks need it
   (lines 458–466).**
   - `scripts/checks/regen-all.sh` calls `bash scripts/kicad/run.sh python3
     scripts/libgen/fixtures/check_wrl_dimensions.py`, plus `smoke.sh` and `export-master.sh`.
   - Project rule 4 makes a missing oracle a failure, not a skip.
   - Fix: require the pinned image for the start and end checks, and record its digest in the admission fingerprint
     (ORCHESTRATION.md section 3 asks for the tool or image digest).
   - "No oracle step inside the study" can stay.

3. **MEDIUM: the run bounds do not cover the start and end checks (lines 396–409, 458–462).**
   - `regen-all.sh` runs twice, at about 313 s each per `cloud-verification-20261127.md`.
   - `slot_moves_a2.py --check` runs twice (P2 and the end check), at about 20 minutes each.
   - `joint_search.py --check` "reproduces `result.json`". If that is a re-run, it is a second 2 to 3 hour
     computation outside `timeout 6h` and outside the memory watchdog.
   - Fix: say what `--check` recomputes, give it a ceiling and an expected time, and put all these steps under the
     one-heavy-process rule, the 8 GiB budget and a total wall-time figure.

4. **MEDIUM: the brief does not say what happens when a stage ceiling is reached, and East's ceiling is smaller than
   its caps (lines 320–324, 404–406).**
   - STOP 3 names only the 6 h ceiling.
   - East has up to seven target sets. Each may use 400 rows-only replays at about 4 s, which is about 27 minutes
     before any legality call, against a 75 minute stage ceiling.
   - The first target set can therefore starve the subset fallback that is meant to deliver "the largest clean
     subset".
   - Fix: state that the stage ends, the affected ICs are labelled `BOUNDED BY` that ceiling, and the driver
     continues. Either give each target set its own time slice, or state that subsets may go unsearched.

5. **MEDIUM: A12 cannot replay a 26-way L07 scene (lines 133, 326–331, 338–339, 371).**
   - A slot hold carries only link, front board, centre, slot centre, direction, reason and ruling
     (`links_gate.slot_holds`). It has no size.
   - `_place_ladder` tries P-K links at 40 circuits first. If that fails at the held slot, it re-clusters at 26 under
     new ids, which makes the hold stale ("no such link" or "link not placed").
   - Fix: state how a 26-way scene is judged. For example, rows-only with the 26-way geometry, labelled "gate replay
     NOT RUN: no size selector, not a candidate without a generator change". Otherwise make it a STOP.

### Lower-severity corrections

6. **LOW to MEDIUM: A4 differs from DS-146 rule 3, "a re-placed trimmer keeps its face" (line 363).**
   - A4 requires every new or shifted K trimmer row to be on B.
   - The base has RV4204 with an F to F row, so a shifted RV4204 that keeps its face would be rejected, while an F to
     B flip would pass.
   - Fix: reword to "keeps its paper face, and none newly lands on K's front face".

7. **LOW: Rulings 5 and 6 are missing from the proposed decision rows (lines 520–528).**
   - Ruling 6 carries the reading of "35 mm join radius" that the owner should see.
   - In `link-gate-options.json`, 35.0 is `clustering.join_radius_mm`. The retained slot search radius is 24.0 and
     `way_2_radius_mm` is 36.0.
   - The brief's metric (slot-centre distance from the search centre) matches the S11 brief and is reasonable, but it
     is an interpretation.
   - Also add to "After the run": `links_gate.check_placement_terms` rejects a slot beyond 24 mm, so a 24 to 35 mm
     scene needs a checker or options change in the generator task.

8. **LOW: "hard keep-out" is implemented as "not newly displaced and not shifted", with two exceptions the owner
   notification should name.**
   - Tails (Ruling 3) follow the packet's requirement table and are sound.
   - The T1 "anchored" exemption (rule 5, lines 234–239) lets a moved link newly cover a protected footprint that a
     non-searched link already displaces. It is not listed among the rulings.
   - Fix: list those footprints per scene, since their return to paper is then blocked by two links.

9. **LOW: there is no label for a negative result where no numeric cap is hit (lines 294–296, 448–449).** The pool
   keeps one candidate per direction and 2 mm cell, so such a result is still not exhaustive. Name the pool reduction
   as a standing bound.

10. **LOW: the fingerprint lacks items section 3 asks for (line 403).** Missing are OS and architecture,
    `memory.current`, and the interpreter. The probes used system Python 3.13.18, while
    `cloud-verification-20261127.md` used Python 3.12 with pinned packages. Name the one the run uses.

11. **LOW: M4 and M5 use two-decimal coordinates (lines 386–387).** The recorded slot is (201.1667, 197.4167), and
    the S9-A pose is (202.1667, 195.6667). Use exact values, as the brief's own "lesson of 7.93" says.

12. **LOW: admission needs "a clean tree", but the brief and the DS-151 row are uncommitted.** Commit both before
    admission.

## Rulings 1 to 5 are sound and correctly labelled

- **Ruling 1 (locality basis, max of accepted and base):** settles the first open ruling item of the packet. It is
  scoped to this study and still catches both U4526 regressions.
- **Ruling 2 (the five inherited mismatches go to MC04-L1):** matches "own disposition outside S10". The 16
  acceptances were all made in design-authority brief revisions (S7, S8, DS-144), so a design-authority item is the
  right owner.
- **Ruling 3 (tails):** follows the gate, as the requirements table demands. `links_gate.displaced` has no tail term.
- **Ruling 4 (reference pose):** the "unchanged base effective pose" allowance goes beyond the table's "paper for
  every protected footprint". It is necessary because of the 131 inherited rows, and it is consistent with DS-150's
  "newly displaced".
- **Ruling 5 (gate rows decide):** consistent with DS-148.
- **Requirements table:** every item is met, apart from the points in the corrections above.
- **Re-review correction 1:** met, because L15.02.01.01 is released.
- **Project rules:** the panel lock is fixed and its hash is pinned; drafts stay unvalidated; nothing is adopted;
  there is no outward action.

## Every factual claim checked reproduces

| Claim | Result |
| --- | --- |
| 14 input SHA-256 pins at `6e5716e7` | all match |
| 7 tree hashes, equal to `8243acdf` | all match |
| 10 code hashes at `622168b1` (HEAD) | all match |
| `result-a2.json` `9d524988…48d2`, `caps_reached: []`, radius 24.0 | match |
| `32580f77` `link-gate.json` `fa944359…ab03a6`, `overlay.json` `5a7a07a8…fc07d3c` | match |
| 72 link records, 62 live, 10 dissolved (L03.02.02.01 among them), one base hold (JL-K-JL-L02); five holds at HEAD | match |
| Eight-link table: centres, slots, directions, sizes, cables, circuits | match |
| IC table: paper poses, courtyards, which links cover each IC | match; no non-searched link meets any of the five courtyards |
| Protected set: 1734; K 1182, JL 287, JR 265, P 0; 131 with a base row (K 103, JL 16, JR 12) | match by an own derivation; the role clause adds nothing beyond the net-suffix set |
| 71 protected footprints under a K tail at the base | match (24 of them under searched links) |
| 452 base rows | match |
| P5: class N {R5249, R5256, R8221, R8331, R8356}, class S {R5253} | match from the `32580f77` `displaced` lists |
| R5259 under the K tail of L13.01.01.02 at `32580f77` | match |
| P6: new, shifted and the ten removed protected rows; 21 new, 18 removed, 15 shifted in total | match |
| Named functions and attributes (`search`, `candidate`, `displaced`, `gate_run`, `generate`, `LINK_ERA`, `Ctx.grid(step, radius)`, `Ctx.evaluate`, `replace_all`, `run`, `Arm1.accept_for`, `Arm1A2.accept_for`, `link_rects`, `effective_scene`, `effective_turns`, `movement`, `locality`, `ancillary_geometry`, `SNAPSHOT_PATHS`) | all exist |
| 26-way identity `FH12-26S-0.5SH(55)`, C202113, C32128 60 mm in `sizes`; L07 needs 23 circuits | match |
| M1, M2, M4, M5 poses against the S9-A2 report, the S10 brief and the S10 holds | match (rounding aside, correction 11) |
| 438 panel centres, 33 modules, 16 locality entries | match |
| Container: 4 CPU, 15 GiB, no swap, about 15 GiB available at review time | match |

## Not verified in this review

- The three timing and memory probes (159 s and 2115 MB; 4.0 s; 3.9 s) and the stage time estimates.
- The P7 locality figures. The earlier packet review confirmed them; they were not recomputed here.
- P6's R4238 overlay move, the four face changes, and the 56 movements and 16 face changes.
- P8 and P9 gate replays.
- `regen-all.sh`, `pnpm circuit:check`, KiCad and ngspice: NOT RUN, because this was a read-only review limited to
  cheap checks.

## Re-review of brief Revision 2: ACCEPT

Same reviewer and model (`claude-fable-5-2`), same read-only constraints. Under review: brief Revision 2, SHA-256
`1ecf7da618924bf1a21b825ad1ce682ffa057b66cc950b0285f110e9e2069a2a` (matches the expected value), repository at
`622168b1`. The verdict heading at the top of this file applies to Revision 1 only. Only this section was added to
this file; nothing else was edited, committed or run beyond short read-only checks.

### All twelve corrections are closed

| # | Correction | Result in Revision 2 |
| --- | --- | --- |
| 1 | Positionless protected rows | CLOSED. Ruling 4 and A2 exempt an unchanged positionless base row and name the seven; P10 pins them; P11 (all-stay scene passes A1 to A11) and M12 are added. R8431 has a positioned base row at `6e5716e7`, so M12 is a valid mutation |
| 2 | KiCad oracle for `regen-all.sh` | CLOSED. The pinned image is an admission item, its digest is in the fingerprint and equals `scripts/kicad/pin.env`; a missing image is a STOP |
| 3 | Bounds for start and end checks | CLOSED. Each step has a ceiling; `--check` is defined as verification without a search re-run; a full re-run is a separate admitted run; total ceiling 7 h 10 min |
| 4 | Stage ceilings and East starvation | CLOSED. Ceiling behaviour is defined (end, keep, label, continue); East slices 25 + 15 + 5 × 7 = 75 min with carry-forward; "not searched" label added |
| 5 | 26-way L07 and A12 | CLOSED. A 26-way scene is rows-only, labelled, never a candidate, and spends no full replay |
| 6 | A4 against DS-146 rule 3 | CLOSED. A4 keeps the paper face and bars a new landing on K's front face; M10 follows |
| 7 | Rulings 5 and 6 in the rows; 35 mm reading; checker radius | CLOSED. Both rows added; the three retained numbers (35.0, 24.0, 36.0) are stated; the `check_placement_terms` consequence is under "After the run" |
| 8 | Anchored exemption | CLOSED. It is Ruling 7 with a decision row, a per-scene list and reviewer item 15 |
| 9 | Pool reduction label | CLOSED. Named as a standing bound with its own result label |
| 10 | Fingerprint and interpreter | CLOSED. `/home/user/venv312/bin/python` exists and reports Python 3.12.3, NumPy 2.2.6, SciPy 1.15.3, Shapely 2.1.2 |
| 11 | Exact coordinates in M4 and M5 | CLOSED. (201.1667, 197.4167) equals the S10 hold; (202.1667, 195.6667) is present in `mc04_s9_slot_moves/result.json` |
| 12 | Clean tree | CLOSED. The manager commits the brief, this review and the DS-151 row before admission |

### Both stated departures are acceptable

- **End-of-run `slot_moves_a2.py --check` dropped.** P2 already runs it in arm 0, the study writes nothing under the
  S8, S9 or S10 study directories, and the end checks confirm those file hashes. Nothing is lost.
- **Ruling 6 as a conditional interpretation.** The reading (slot search radius 24 mm becomes 35 mm, clustering
  unchanged) matches the S11 brief under DS-149 and the packet option the owner chose. Stating it to the owner and
  requiring a revision if the owner meant otherwise is the correct handling.

### Nothing new is broken; three notes for admission, none requiring a further brief revision

1. **The memory watchdog may not see the oracle container (LOW).** The budget is stated "oracle container included",
   but a container started through `scripts/kicad/run.sh` runs under the Docker daemon, not in the driver's process
   tree. A tree-RSS sampler will miss it. At admission, use a measure that includes it (a cgroup scope that covers
   it, `docker stats`, or an abort on low `MemAvailable`), and record which was used.
2. **The Docker daemon was not reachable at re-review time** (`Cannot connect to the Docker daemon`). The admission
   item "the pinned KiCad image present" already makes this a blocker until it is running; it is noted here so it is
   not found late.
3. **End-check arithmetic (trivial).** The four end ceilings sum to 45 min, not 50; the stated total of 7 h 10 min
   is therefore conservative by 5 min and needs no change.

### Not verified in this re-review

- The timing and memory figures, the P7 locality figures, and the P8 and P9 replays, as in the first review.
- `regen-all.sh`, `pnpm circuit:check`, KiCad and ngspice: NOT RUN, read-only review limited to cheap checks.
- Every board and schematic stays an unvalidated draft; this acceptance is of the brief as a study plan only, and
  admits nothing by itself.
