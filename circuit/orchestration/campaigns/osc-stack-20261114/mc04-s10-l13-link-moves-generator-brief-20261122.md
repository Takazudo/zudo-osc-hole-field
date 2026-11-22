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
