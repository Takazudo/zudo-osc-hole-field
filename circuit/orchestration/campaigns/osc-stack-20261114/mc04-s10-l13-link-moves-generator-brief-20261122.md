# MC04-S10 brief: generator task for the three L13 link moves (U5209, U5210)

2026-11-22. Ruled by the design authority (DS-147) on the S9-A2 result (`8243acdf`, report `mc04-s9-a2-report-20261122.md`).
Executor: the Windows/WSL Claude Code session. Branch `claude/project-thread-iw3gai`.

**Kind:** a generator change in the link-era model. No interim board, spec or BOM change. Every result stays an
unvalidated draft. Check 5 stays NEEDS_DESIGN, with U1415, U5110 and U8409 open and with the owner.

## Inputs

- `scripts/stack/studies/mc04_s9_slot_moves/result-a2.json` (sha256 `9d524988…48d2`) at `8243acdf`
- `design/stack/geometry/links/link-gate-options.json`
- `links_gate.py`, `links_gate_part2.py`, `links_gate_c6.py`, `link_era_replacements.py`, `gate_a_open_items.py`
- `design/stack/link-electrical/`, `design/stack/fixings/`, `design/stack/trimmers/`

Start with `bash scripts/checks/regen-all.sh` and `pnpm circuit:check`.

## Allowed changes

1. **Three new `slot_holds` entries** in `link-gate-options.json`, at the joint-scene poses. Each entry gives the link,
   centre, slot centre, direction, reason and the ruling "DS-147 / S10". Take the exact values from the result file,
   not from this text:
   - L13.01.01.01: slot (201.17, 197.42) +y;
   - L13.01.01.02: slot (176.0, 198.25) −y;
   - L13.01.02.01: slot (159.0, 193.0) −y.
2. **A reviewed source input** for the re-placed parts of the joint scene, read by `link_era_replacements.py`, with the
   conditions below.
3. **Generators and tests** needed to read items 1 and 2. No hand edit of any generated file.

## Conditions from DS-147

- **R5257** (U5210 F2 feedback, `/W1/F2_OUT` to `/W1/F2_SUM`, 100 kΩ) must sit at 7.93 mm or less from U5210, on
  U5210's face. If the cheapest set cannot meet this, choose once from the other clean sets in `result-a2.json` (16 U5209
  pairs, 81 U5210 candidates). If none meets it, stop.
- **R5259** (`F2_OUT` to `F3_SUM`): keep it on U5210's face if a place exists. Otherwise, record the via on `F3_SUM`
  as an open electrical item.
- **U4537** (SN74HC74DR, `/E5/CLOCK`), 17.87 mm, B→F: record the per-net run estimates. At re-route, check the clock
  edge against `fact-flipflop-input-transition45` and the retained hold-time fact, and keep `/E5/CLOCK` away from the E5
  analog nodes on that face.
- **RV4503 and RV8407** stay on the rear face. Service access stays UNMEASURED. Regenerate
  `design/stack/trimmers/relocation-plan.json`, which still describes 61 links and 438 displaced parts.
- **The 12 face changes:** list each one with its nets in the record and the Gate A items.
- **P-K-P-L13.01.01.02 changes direction** (+y to −y). Show that its cable, connector and conductor order are unchanged
  and that c6 accepts it.
- **Workload:** the trim list changes (RV1001 out, RV1102 in; RV1101 out, RV1201 in), and two front tails lengthen by 6
  and 8 mm. Report this as a workload change against DS-128.

## Regenerate, in this order

1. The link gate: `link-gate.json`, `.md` and the chain.
2. The c6 record and `c6-pass.json`.
3. The `link_electrical` results (checks 3 and 4) for 62 links and 531 signals.
4. The fixing sites, the reach exceptions and the threading procedure.
5. The latch verdicts (check 2).
6. The link-era record.
7. The trimmer relocation plan.
8. `gate-a-open-items.json`.
9. The floorplan report, if it repeats any of these.

## Fixed

- the 438 panel centres and `placements.lock.json`;
- the 33 modules;
- every link's size, connector, cable, stock length and stock-FFC direction;
- the ruled sleeves and fixing keep-outs;
- all existing slot holds;
- DS-06;
- the ten link-era poses and their acceptances;
- every link other than the three.

## Acceptance

- **Links:** the three links sit exactly at the held poses. Every other link's centre, slot and direction is byte-equal
  to `8243acdf`. The record holds 62 links, 124 latches and 531 signals.
- **Positions:** U5209 and U5210 are no longer displaced. The list without a position holds exactly U1415, U5110 and
  U8409, as NEEDS_DESIGN. Every part the moves newly displace has a recorded pose.
- **Placement conditions:**
  - R5257 is 7.93 mm or less from U5210, on its face;
  - re-placed decouplers keep their face and distance;
  - RV4503 and RV8407 are on the rear face;
  - `member_faces.py` is all clear for every placed block, old and new.
- **Checks:** c6, check 3 and check 4 are run, and their verdicts reported as computed. Count pins are updated by the
  generators, with a test for each.
- **Report contents:**
  - a workload table against DS-128: links, latches, leads to trim by reference, the hold-by-hand list, lengthened
    tails;
  - U4537's net estimates and the 12 face changes, in the record and the Gate A items.
- **Checks pass:** every `--check`, the stack suite, `regen-all.sh --check` and `pnpm circuit:check`. KiCad oracle steps
  are written `NOT RUN: no board change`.
- An independent review before the stage closes.

## Stop conditions

Stop, report and change nothing further on any of these:
- the gate's accept rejects a held pose, or any other link moves;
- c6, check 3 or check 4 fails. Do not change conductor order, grounds or limits to make it pass;
- any of the ten link-era poses becomes illegal, or a newly displaced part has no pose within 24 mm;
- R5257 cannot be met by any clean set in `result-a2.json`;
- any need for a panel centre, sleeve, hold, cable or connector change.

No second attempt without a ruling, no supplier contact, and no order files. Push and give the full hand-back with the
report `mc04-s10-report-20261122.md`.

## Revision 1: four holds, the gate rows canonical, and the overlay rules (DS-148, 2026-11-22)

The S10 stop (`f4b61ed2`, report `mc04-s10-report-20261122.md`) was correct. Replaying the gate with the three holds
let the not-yet-dissolved P-K-P-L03.02.02.01 take L15.02.01.01's slot. The design authority ruled as follows.

### Holds (replaces "Allowed changes" item 1)

- P-K-P-L13.01.01.01: slot (201.17, 197.42) +y.
- P-K-P-L13.01.01.02: slot (176.0, 196.25) −y. This is pair 8, which keeps R5257 at 7.93 mm on B.
- P-K-P-L13.01.02.01: slot (159.0, 193.0) −y.
- P-K-P-L15.02.01.01: slot (193.0, 213.0) +y, which is its recorded pose.
- Up to three further holds at a live link's recorded pose, when the replay moves that link. Each is listed with its
  cause; no new ruling is needed. A hold at any other pose needs a ruling.

Take the exact values from `result-a2.json` (pair 8, U5210 candidate 0) and from the record. P-K-P-L03.02.02.01 must
still end dissolved, with `/M4B/1_REMOTE` and `/M4B/2_REMOTE` riding on P-K-P-L13.01.01.02 inside the 45 mm limit.

### The reviewed input is a set of overlay rules (replaces "Allowed changes" item 2)

- **Gate rows** (`link-gate.json` `replacement`) are canonical for every displaced footprint, including the new and
  knock-on rows. They are the DS-88/DS-97 proof of room that check 5 reads.
- **The link-era record is an overlay.** It holds a block pose only in three cases:
  1. an IC the gate leaves without a position;
  2. an IC whose gate pose breaks the block rule (a decoupler on the other face, or farther from its IC than before);
  3. a part under a ruled condition (R5257, R5259, RV4503, RV8407).

  Where an overlay entry exists, it wins for that IC and its block members, and the record shows both poses. The
  generator derives which ICs need an entry and writes the reason for each.
- **Agreement:** the overlay plus the gate rows it does not replace have no courtyard conflict (`member_faces.py` over
  every overlay block), and every overlay pose is legal in the Field built from the new gate record.
- **U4222, U4223 and U4537** take their gate poses unless the block rule fails. In that case, search a block pose under
  the S8 rules and add it to the overlay. The S9-A2 poses are evidence of room, not the record.
- **RV4503, RV8407 and RV2310:** the gate rows stand if they are on the rear face. Otherwise, overlay them on the rear
  face.
- **Knock-on rows** are accepted as generated. Report each with its distance from its own origin and its step, and
  recompute every figure in `locality-acceptances.json`. R5259 is searched on face B first.

### Added acceptance

- Every unheld live link is byte-equal to `8243acdf` in centre, slot and direction. L03.02.02.01 ends dissolved, with
  the same riders and hosts.
- U5209 and U5210 are not displaced. The ICs without a position are exactly U1415, U5110 and U8409, plus any the overlay
  resolves.
- A table of the row changes (the stop showed 20 removed, 22 new and 15 shifted), regenerated, with face, distance and
  step.
- For each newly displaced IC: decoupler face and distance before and after, and whether it has a "gate pose" or an
  "overlay pose", with the reason.
- The ten existing overlay poses are re-checked in the new Field. A pose made illegal only by a knock-on row may be
  searched again once under its own ruled rules, with its acceptance figures recomputed.
- All trimmers in changed rows are on the rear face.

### Added stop conditions

Stop on any of these:
- a fourth recorded-pose hold beyond the three allowed is needed, or a hold at a non-recorded pose;
- the ways-out or consolidation result changes for any link other than through the holds;
- an overlay search finds no pose within 24 mm, or a re-searched pose worsens its recorded acceptance figure;
- a worse figure in `locality-acceptances.json`;
- a newly displaced part is an input-buffer IC or a part on a `*_FB`, `*_SUM` or `*_SENSE` node.

Everything else in the brief stands: the regeneration order, c6 and checks 3 and 4 reported as computed, the workload
table against DS-128, `NOT RUN` for oracle steps, the independent review, and no second attempt without a ruling.
