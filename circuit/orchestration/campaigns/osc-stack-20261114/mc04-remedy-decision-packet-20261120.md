# MC04 remedy decision packet for the 26 unplaced ICs (Gate A check 5)

2026-11-20 JST. Prepared by the Claude Project lead (thread "Resume OSC instrument order-readiness
campaign"), branch `claude/project-thread-iw3gai`. **DRAFT FOR THE DESIGN AUTHORITY. Nothing here
is adopted.** Check 5 stays NEEDS_DESIGN until a ruling is recorded.

## Owner decision, 2026-11-21: develop option D in stages

The owner chose "Yes, develop it in stages" on the decision card. That authorizes the staged work below; it
accepts no move. Each stage still needs independent review, and check 5 stays NEEDS_DESIGN until the
generator change passes it.

Stage 1a (`scripts/stack/studies/mc04_s1_budgets/`, revised after independent review) drafts electrical
limits from retained OPA4196 and TMUX7412 facts and the retained cable model. Under those draft limits the
protected input nodes fail the crosstalk limit by a wide margin (unpatched 100 kΩ: 374 mV even with two
grounds on both sides, against 10 mV, or 1 mV for the pitch CV), so six input-buffer blocks (U1216, U1416,
U1518, U4346, U8314, U8417) cannot move as drawn. Two output blocks (U1417, U2218) can, with a ground on
both sides of each isolation midpoint, or plainly on the keep-front boundary. Four blocks (U2119, U4347,
U4348, U8318) depend on LED bridge nets inside op-amp feedback loops, which need a loop-stability criterion.

Stage 1b (`scripts/stack/studies/mc04_s1b_indicator_loops/`, paper screen, independently reviewed)
finds that only `*_LED_A`/`*_LED_K` cross for all 13 indicator units in both boundaries. With a single-pole
OPA4196 model and ASSUMED diode ideality, the worst small-signal phase margin over 0.1 µA–1 mA falls from 82° to 69°
with the 7.22 pF cable, and to 40° at four times that capacitance. The screen passes the ASSUMED 45° criterion, so the
four blocks stay conditional on case 5 of the stage 4 WSL simulation, which covers the bridge dead band and
slewing that the screen cannot see.

Stage 4 (WSL vendor-model simulation, `design/spec/cells/sweep_input_buffer_vendor.py`, report
`design/reports/spice/input-buffer-vendor.json` sha256 `445df865…c2ae` at `fb88d9f`, revision 1 independently
reviewed, all six revision items closed). Model evidence only, not hardware qualification:

- No sustained oscillation in the 90 evaluated of 112 rows (22 are AC or non-conducting rows, NOT EVALUATED). In
  the sine rows the 1 mV residual threshold is frequency weighted by a 1 µs moving average: about 15 mV at
  200 kHz, so slow oscillation in the sine rows is weakly screened (review SHOULD, disclosed here; step and hold
  rows use unfiltered peak-to-peak).
- OPA4197 settles as fast as OPA4196 or faster, except five RC-limited cases where it is up to 0.40 µs slower.
  At ±15 V overdrive the clamps conduct, with no phase reversal; recovery is 1.0–1.1 µs against 2.1–5.2 µs.
- Plain followers, Middlebrook double injection: OPA4196 54.8° at 2.6 MHz, OPA4197 64.0° at 10 MHz.
- Indicator loops (OPA4196): worst margin of four bias points 58.5° / 52.5° / 46.6° / 40.1° with 0 / 7.2 / 15 /
  30 pF on each LED net. The one-cable case (7.2 pF) passes the ASSUMED 45° criterion; about twice that is the
  draft ceiling, so an indicator LED net must not cross more than one cable span (DRAFT limit, needs ruling).

Consequence: on model evidence, OPA4197IPWR is an electrically acceptable replacement for the six input-buffer
packages, and the four indicator blocks may move if each LED net stays within about 15 pF. Still open before a
generator change: the rail ruling (#34; the swap adds +17.2 mA typical and +25.0 mA maximum on each analog rail,
on a −12 V rail already over its ceiling), and the 25 mm rule for the four buffers placed 26–32 mm away.

Owner decision, 2026-11-21 10:18Z: "Accept, fix the rail in #34". The six input-buffer packages (U1216, U1416,
U1518, U4346, U8314, U8417) change from OPA4196 SOIC-14 to OPA4197IPWR TSSOP-14 and stay on their front boards.
The added analog-rail current (+17.2 mA typical, +25.0 mA maximum per rail) is carried to #34, which owns the
−12 V overshoot. The 25 mm rule for the buffers placed 26–32 mm away is still an open review item for the
generator stage.

Owner decision, 2026-11-21 12:55Z: "Accept 0 mA, track in #34". The swap raises the canonical +12 V continuous
rule result to 1700 mA, equal to the PD contract, so the +12 V contract margin kept on 2026-11-04 is now 0 mA.
Consequences recorded by the regenerated power-contract ledger: the positive-converter efficiency needed at
15 V / 3 A rises from 0.939 to 0.973, and the ideal-high low-power case now needs a 21.3 mA +12 V reduction
(previously 0). Both are an open rail follow-up; issue #34 is closed, so this packet is the live record until a new rail issue is opened.

Stage 5 result (WSL, `b610521` spec, revision 1 at `af1a35e9`, `c1c9043c`, `cfaf745f`; independently reviewed,
accepted). The six packages are OPA4197IPWR on their front boards: five within 0.5–1.6 mm of their old slots,
U1518 back on its original TSSOP slot. Panel hardware and `placements.lock.json` are unchanged. Revised indicator
margins (shared DC point): OPA4196 58.3 / 53.8 / 48.1 / 40.2° at 0 / 7.2 / 15 / 30 pF; OPA4197 (U8417) 61.2 / 51.8°
at 0 / 7.2 pF. Open:

- **D4309 fit conflict (E3 input diode, JR B.Cu).** Its old slot (courtyard x 264.1–266.6, y 43.8–48.76 mm)
  overlaps the U4346 TSSOP courtyard by about 0.22 × 0.34 mm plus the 0.35 mm clearance. The floorplan's
  net-cost ranking chose a pose 21.5 mm from the slot, 26.4 mm from U4346 and 37.5 mm from U4347; free B.Cu poses
  exist about 4–7 mm from the slot (for example 261.85, 39.95). No coded rule is broken (the locality rule covers
  only BAV199/BAT54S). The next generator stage adds a distance cap for evicted input-protection diodes.
- `test_rail_options` count tripwire (rail follow-up) and `test_instrument_readiness` (24 PCB footprint
  mismatches until the layout stage). `regen-all.sh --check` and the simulation `--check` are NOT RUN in the cloud
  (no oracle); WSL ran them.

## The question for the design authority: which remedy to develop for the 26 unplaced ICs

The cumulative record has 438 displaced footprints. 412 have courtyard-level replacements and 26
fourteen-pin ICs (JL 6, JR 6, K 14) have none. The studies below were each independently reviewed
and corrected. They are room and count studies only: no electrical review, routing, allocation or
canonical write.

## Evidence

| Step | Study | Reviewed result |
| --- | --- | --- |
| 1 | `scripts/stack/studies/mc04_c1_capacity/` | Each IC alone has room on its own board. Joint first-fit: JL 6/6, K 14/14, **JR 3/6**. JR is short of room, not just congested. |
| 2b | `scripts/stack/studies/mc04_c2b_link_shift_replace/` | Moving links inside the retained rules, with retained re-placement, frees **3 ICs cleanly (26 → 23)** via P-L02.01.01, P-L12.02.01.02 and P-L13.01.01.02. More moves reach 20 only by stranding other parts. No link move helps JL. |
| 2c | `scripts/stack/studies/mc04_c2c_moved_link_checks/` | The moved links pass cable, compliance, member and rider class-distance checks. The c6 contract must be re-run, because it pins the geometry digest. |
| 4 | `scripts/stack/studies/mc04_c4_blocks/` | On room, all 26 pack onto K as functional blocks (IC + decouplers + one-hop passives and diodes); every position passes the exact predicate. JR → K adds a net 16 cable nets (31 new, 15 removed) and JL → K a net 8 (24 new, 16 removed), against 75 and 128 spare positions. The new nets include 15 `*_PROTECTED` input nets and 14 `ISO_MID` splits. Thirteen ICs move beyond the 25 mm rule. |
| 5a | `scripts/stack/studies/mc04_c5_crossing_nets/` | All 55 new crossing nets classify ANALOGUE; none is raw-sensitive or forbidden, and none has an allowed-crossing kind yet. 26 are LED drives, 15 protected input nodes and 14 isolation midpoints. |
| 5b | `scripts/stack/studies/mc04_c5b_keep_front_pairs/` | Keeping the protection and isolation parts on the front board crosses the same 31 + 24 nets: the crossing moves to the clamped IC input (`*_SENSE`) or IC output (`*_DRIVE`). Also keeping the LED resistors makes 13 raw-sensitive nets cross, so that variant is ruled out. |

## Options

| Option | What changes | Remaining unplaced | Main risks |
| --- | --- | --- | --- |
| A. Clean link moves only | 3 link moves plus re-placement, within the retained rules | 23 | Does not solve the problem; JR stays short of room. |
| B. Partition change: JR and JL blocks to K | 12 blocks move to K. Panel hardware stays on the front boards. | K's own 14 still need room (option C or D) | 15 protected input nodes and 14 isolation midpoints would cross the cable; +24 net crossing nets (55 new, all ANALOGUE) need allocation and coupling review; module tests (envelope ENV_STORAGE isolation, mix4 protected inputs, filter core isolation) must still pass. Keeping the protection and isolation parts on the front board (step 5b) does not reduce the count; it makes the clamped IC input or output node cross instead. |
| C. K blocks relocated within K beyond 25 mm | DS-88 radius rule relaxed for whole blocks | — | A rule change; longer runs for wavefolder, VCO and mixer cores; needs an electrical budget that does not yet exist. |
| D. A + B + C together | All of the above | 0 on room (13 moves beyond 25 mm) | Every risk above, plus re-running the links_gate and c6 records and the independent review. |

## Recommendation: develop option D, in stages, as an engineering change with the generator

Option A alone leaves 23 ICs unplaced and cannot fix JR. Options B and C are the only routes
that show room for all 26. The cost of D is a partition change and a rule change, and that cost is
an electrical question, not a room question. So the next work should be:

1. **Electrical budgets.** The analog remedy brief lists the missing physical budgets per function:
   allowed added length, R/L/C, phase margin, noise and the stationary endpoints. Without them no
   relocation can be accepted.
2. **Crossing-net classes.** Classify the 24 new crossing nets and run the retained allocation and
   coupling kernel on the affected links.
3. **Generator change.** Implement the accepted subset through `scripts/stack/geometry/links_gate.py`
   (with the pending place() accept and A7 input-hash fixes), regenerate, and get an independent review.
4. **Native verification.** Only then hand the native KiCad phase to WSL.

## What this packet does not establish

- Room is raster-only and greedy. It is neither exact-confirmed nor a minimum.
- No electrical or stability acceptance. No routing, DRC, fill or manufacturing step.
- The 16-IC analog brief covers only OPA4196 packages. The logic and precision packages (U1518,
  U4341 and others) have their own briefs, which a ruling must also read.
