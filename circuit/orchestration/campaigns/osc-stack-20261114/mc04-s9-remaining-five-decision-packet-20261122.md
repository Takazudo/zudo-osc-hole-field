# MC04-S9 decision packet: remedies for the last five analog ICs (Gate A check 5)

2026-11-22. Prepared by the Claude Project lead, branch `claude/project-thread-iw3gai`, at the stage 8 close (`4f78edb6`).
**FOR THE DESIGN AUTHORITY. Nothing here is adopted. The stack stays NOT ADOPTED, and check 5 stays NEEDS_DESIGN.**

## Where check 5 stands

The MC04 candidate disposition (`mc04-candidate-disposition-20261117.md`) left 26 fourteen-pin ICs with no position in
the link-era model (K 14, JL 6, JR 6). The owner chose option D in stages (packet `mc04-remedy-decision-packet-20261120.md`).
Stages 1–8 have been completed and independently reviewed:

- **Stages 4–6:** six input buffers became OPA4197IPWR (TSSOP-14) on their front boards, after a vendor-model simulation.
- **Stage 7:** 73 K-block packages moved from the jack boards to the core, with stable headers and links.
- **Stage 8:** placed what remained in the link-era model.

The stage 8 record is in these files:
- `design/stack/geometry/links/link-era-replacements.json` (generator `scripts/stack/geometry/link_era_replacements.py`);
- `design/stack/gate-a-open-items.json` (generator `scripts/stack/gate_a_open_items.py`);
- the S8 reports `mc04-s8-*-report-20261122.md`;
- the brief `mc04-s8-open-replacement-native-brief-20261122.md`, Revisions 1–8.

Result in the link-era model (`links_gate_part2.Field`, GH headers dropped, gate-displaced parts at paper positions):
- 9 ICs are placed and RESOLVED FOR THE LINK ERA. Three of them are under recorded locality acceptances: U1318 as an
  input buffer at 29.09 mm, and U4417 and U4526 as logic. U4647 has an LED-drive distance acceptance.
- **U4433** (SN74HC74, logic) is open at 25.5 mm. Its clock net `/E4/CLOCK` grows by only 4.47 mm (0.89 pF on a
  150 mm, 30 pF net); `/E4/LOOP` grows by 45 mm. **Manager ruling below: accepted on the U4417 terms.**
- **Five analog blocks stay OPEN: U1415, U5110, U5209, U5210 and U8409**, all on K. Each sits under a P-K link
  connector, tail or slot keep-out:
  - U1415: P-K-P-L07 and L08;
  - U5110: P-K-P-L12.02.01.02;
  - U5209: P-K-P-L13.01.01.02;
  - U5210: P-K-P-L13.01.01.01;
  - U8409: P-K-P-L03.01 and L03.02.02.01.

All five are proven to have no legal pose within 24 mm on a 0.5 mm shift grid with 4 turns, both faces, displacement of
small passives, and block-on-block moves of up to two neighbour blocks. U5210 and U8409 also failed a complete joint
search with U8412, U5208 and U8408, with neighbours allowed up to 40 mm. Continuous poses are not covered.

## The five: function and cheapest far pose

The figures are estimates: 1.5 × HPWL at 0.20 pF/mm, per `gate-a-open-items.json`.

| IC | Function | Cheapest pose | Worst grown nodes |
| --- | --- | --- | --- |
| U1415 | O4 sine shaper | 38.71 mm | SINE_MINUS and SINE_GAIN_SUM feedback/summing nodes grow by 69 and 45 mm |
| U5110 | W2 fold cells F1–F4 | 40.61 mm | F1_SUM +45.6 mm, F1_CLIP non-inverting input +83 mm |
| U5209 | W1 drive and folder sums | 49.65 mm | EMITTER +92.7 mm, FOLDER_SUM, PRE_GAIN_SUM |
| U5210 | W1 fold cells | 80.61 mm | F1_OUT +172 mm, F1_SUM +129 mm |
| U8409 | M4B input buffer and VCA drive | 113.22 mm | 1_GAIN +235 mm, the W_SENSE nets near 27 pF |

The far poses of U5110, U5210 and U8409 overlap each other, so they are alternatives, not one solution.

## Manager ruling on U4433 (within the delegated stage authority)

U4433 is accepted as a link-era logic locality exception on the U4417 terms, at F 270°, 25.5 mm. The clock and sync
nodes grow by under 1 pF, and the 45 mm `/E4/LOOP` growth is a logic output. The re-route keeps `/E4/CLOCK` away from
analog high-impedance nodes. The record is updated in the next native task.

## The question for the design authority

Which remedy to develop for U1415, U5110, U5209, U5210 and U8409, or whether to return check 5 to the owner with
alternatives. The candidate remedies, none of them evaluated yet:

| Option | What changes | Main costs and risks |
| --- | --- | --- |
| R1. Local P-K slot moves | Move one or more of P-K-P-L03, L07, L08, L12, L13 slots a few mm to free each block's area | The link gate, coupling (check 4), current (check 3), the c6 record, fixings reach, latch access (check 2) and the threading procedure all regenerate. P-side neighbours move too. Holds and the stock-FFC direction must survive. |
| R2. Smaller package | OPA4196 in TSSOP-14 (as stage 5 did for six input buffers with OPA4197IPWR) | Needs exact-component evidence for a TSSOP OPA4196 variant (the repository has `component-ti-opa4196idr`, `-opa4197idr` and `-opa4197ipwr` owners only). TSSOP saves about 2.7 × 2.4 mm per package. It may or may not open a pose; a cheap room study would answer that first. |
| R3. Package split | Replace a quad with two duals placed apart, each near its cell | Schematic and BOM change, new component evidence, more decouplers and area. Unit assignment and protection boundaries change. |
| R4. Far pose with an electrical budget | Accept 38–113 mm on feedback, summing and sense nodes | Needs per-node stability and noise budgets and vendor-model simulation with parasitics (stage 4 method). U5210 and U8409 are likely to fail. |
| R5. Return to the owner | Check 5 stays NEEDS_DESIGN and goes to the owner with R1–R4 | Stops the stack at the paper gate until the owner decides. |

## Other Gate A-paper checks (context, not for this ruling)

- **Check 1** (connector and cable identity): NEEDS EVIDENCE.
- **Check 2** (latch opening and access): NOT SHOWN for 31 latches.
- **Checks 3 and 4:** passed within the retained candidate model at the 2026-11-17 disposition. Stages 7–8 regenerated
  the gate with 62 links and 531 signals, so checks 3 and 4 need a rebind before the final packet.
- **Interim locality, reach and slot-drift items** are listed in `gate-a-open-items.json` for the Gate A mechanical review.

## What this packet does not establish

- No routing, DRC, fill or electrical acceptance of any re-placement.
- No assembled or measured state.
- The stage 8 poses are not checked against the interim GH boards, by design (`board_conflicts.py` is the evidence).

## Design authority ruling, 2026-11-22 (DS-145)

An in-session Fable design authority at high effort ruled read-only at `5c8e23b9`. Its rulings:

1. **All five are OPA4196IDR quads** (C2057385, SOIC-14, K, B.Cu):
   - U1415 (O4): SINE_DIFF, SINE_GAIN and two unused grounded followers;
   - U5110 (W2): fold cells F1–F4;
   - U5209 (W1): CURRENT_SERVO, PRE_GAIN, DRIVE_SUM and DRIVE_INVERT;
   - U5210 (W1): fold cells F1–F4;
   - U8409 (M4B): two remote buffers and two bipolar attenuverters.
2. **R1 (local P-K slot moves) is the lead remedy for all five**, because the analog cell does not move and the cost
   lands on cable and mechanics, which have checkable rules. The order:
   - U5209: R1 only;
   - U5110: R1 only;
   - U8409: R1, then R2;
   - U5210: R1, then R2;
   - U1415: R1, then R2, then R5.

   R2 means an OPA4196-family TSSOP-14, not OPA4197IPWR. The +12 V margin is 0 mA, and the stage 4 simulation does not
   cover these cells. R3 is rejected for the four full quads. For U1415, a single dual goes to the owner as an
   alternative. R4 is developed for none, because the per-node budgets do not exist and are not to be invented.
3. **Stop conditions:**
   - one study, with no automatic widening;
   - a clean R1 result goes to a generator task;
   - an R2-only result waits for component evidence and an owner decision (a new BOM line);
   - an IC with neither result goes to the owner by itself;
   - workload changes are shown to the owner at Gate A.
4. **Next task:** `mc04-s9-a-slot-move-study-brief-20261122.md`.
5. **U4433:** the acceptance is sound in substance, but it is its own exception (DS-144), not "on the U4417 terms".
   Conditions are in the brief.
6. **Packet corrections:**
   - U8409's second link, P-K-P-L03.02.02.01, is dissolved, and `gate_a_open_items.py` must filter `gone` links;
   - the TSSOP saving is 3.64 mm in length and −0.3 mm in width (courtyards 7.4 × 9.63 against 7.7 × 5.99 mm), not
     2.7 × 2.4 mm;
   - R1 was partly evaluated before (steps 2b and 2c, before stage 7);
   - the overlap sizes run from 0.07 mm (U5209) to 8.68 mm (U5110);
   - U1415 has two unused units;
   - the decision log lacked the 2026-11-21 owner decisions (now DS-142 and DS-143);
   - checks 3 and 4 are rebound once, after the S9 link moves.

The R2 evidence task (before any spec change) needs:
- the exact TSSOP-14 MPN, from the retained datasheet's package addendum;
- a new owner bundle, with located facts for the PW drawing, land pattern, pinout, thermal resistance, electrical
  tables, quiescent current and MSL;
- the vendor file stored unmodified in circuit-dev-resources, with a matching SHA256;
- the supplier code, or an explicit open gap;
- the footprint checked against the drawing;
- `pnpm circuit:check` before and after, then `circuit:generate`.
