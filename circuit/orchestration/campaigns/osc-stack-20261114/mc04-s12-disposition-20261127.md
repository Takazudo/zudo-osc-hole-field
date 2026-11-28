# MC04-S12 disposition: the negative result stands, link-only search is closed, and the five ICs go to the owner

2026-11-27. Issue #367 (MC-04 paper gate). Design authority under DS-03 (Fable design agent at high effort, model
`claude-fable-5-2`). Subject: the S12 study at `4c216473` (study commit `6708d192`), report
`mc04-s12-report-20261127.md` (SHA-256 `d3b9a330…470a19`), result review
`reviews/mc04-s12-result-review-20261127.md` (`77f8039f…58f2d9`, ACCEPT WITH CORRECTIONS, all verdicts kept),
`result.json` (`32532262…da02ed`). This disposition changes no file but itself. Nothing is adopted. Every board and
schematic stays an unvalidated draft, check 5 stays NEEDS_DESIGN, and #318 stays HOLD.

## Ruling on the result: accepted as a study, with these limits

| IC | Verdict accepted | Binding cause |
| --- | --- | --- |
| U1415 | no candidate on this domain (exhaustive) | every one of P-K-P-L08's 787 class-legal slots covers U1415 |
| U5110 | no candidate on this domain (exhaustive) | every P-K-P-L12.02.01.02 slot newly displaces a protected part (U5205, C5218, R5149, R5268) |
| U8409 | no candidate on this domain (exhaustive) | all 183 P-K-P-L03.01 slots displace C8313 and R7216 (new) and U8411 (shifted) |
| U5209 | no candidate on this domain (exhaustive) | P-K-P-L13.01.01.02 has no slot; its three class-S-only slots are the recorded slot of L13.01.02.01, which has nowhere to go |
| U5210 | no scene found (bounded by the pool reduction) | with L03.01 at its record, R8356 is newly displaced on all 104 remaining P-K-P-L13.01.01.01 slots |

**What the study establishes**

- On the 2.0, 0.5 and 0.25 mm grids within 35 mm of each search centre, with the DS-150 protected rule (DS-156,
  DS-159), the retained class distances and the five ICs at paper, no joint scene exists.
- Four of the five negatives are census zeros of a single link, reproduced by the reviewer's own code. They do not
  depend on a cap, a pool or the search order.
- Widening the radius was not the missing ingredient. The blockers are the protected parts next to each link and,
  for U1415, L08's own class distances.
- The gate-row scene test and its controls reproduce the returned S10 candidate exactly, so the method is sound for
  any later search.

**What it does not establish**

- Any electrical behaviour, margin or acceptance of any node. No simulation ran.
- That no placement exists at all. It shows none exists while protected parts may not move, the link search centres
  and clustering are fixed, and the five ICs stay at paper.
- U5210 exhaustively: scenes with P-K-P-L15.02.01.01 at a moved slot were not enumerated. This does not reopen the
  search, because L03.01 has no slot of its own and R8356 blocks every remaining L13.01.01.01 slot.
- c6, checks 2, 3 and 4, latch access, threading, routing, DRC and ERC: NOT RUN, as the report states.

## What the design authority rules now

1. **S12 is closed as a valid negative study.** Its verdicts stand as worded in the table above.
2. **No further link-only search is admitted under the present rules.** A wider radius, a finer grid or another
   search order cannot change a census zero caused by protected neighbours or by class distance.
3. **Class S stays strict, and relaxing it for U5209 alone is refused.** The report and its review show it opens no
   scene: the three slots it frees are L13.01.02.01's own recorded slot.
4. **S10 Revision 1 stays returned, and the S11 brief is closed as contained in S12.** The five ICs stay open on the
   Gate A card. Ruling 6 of the brief (the 35 mm reading) needs no owner answer now: no ring slot led to a scene.
5. **Two evidence-only items may be briefed regardless of the owner's choice.** MC04-L1 (locality record
   reconciliation, DS-154), and a vendor-model simulation of the fold cell, the wiper-sense buffer and the REF9 cell.
   Evidence alone changes no rule. Using it to let a protected part move is the owner's decision below.

## What is the owner's to decide

- Any change to the DS-150 protected-part rule, by a capacitance budget or by a geometric test.
- Any new part (the dual op-amp for U1415), any far-pose rule exception (U5110 at 40.61 mm), and any change to
  L08's clustering that alters the DS-128 workload.
- Stopping: leaving the five open, so check 5 fails, the DS-60 alternatives return and the prototype order review
  (#318) stays held.

## Owner question

**How should the last five ICs be resolved, now that no connector move can place them while protected parts stay
fixed?**

| Option | What happens | Cost and risk | Unblocks |
| --- | --- | --- | --- |
| **1. Simulate, then allow budgeted moves (recommended)** | Vendor-model simulation sets a capacitance budget per protected node. A new search may then move a protected part within its budget. U1415 gets its own L08 or dual-op-amp study. | An ngspice campaign plus one more search. It may show a cell needs a compensation part, which is a circuit and BOM change. Changes the DS-150 rule. | Potentially U8409, U5210, U5209 and U5110 with electrical evidence; U1415 only through its separate study. |
| 2. Allow moves that do not lengthen a node | A protected part may move if its node's pad extent, pad-to-pin distance and face set are no worse than paper. No simulation. | Cheapest and fastest. A geometric proxy only: no stability evidence, and the fold cell already looks marginal on a first-order estimate. Changes the DS-150 rule. | Possibly the same four ICs, with weaker evidence the order review may not accept. |
| 3. Take the DS-149 fallbacks only | U8409: remote-buffer simulation. U1415: one dual op-amp (new part, evidence bundle, footprint). U5110: far pose with a fold-cell simulation and a rule exception. | Three separate tracks, one new part and one rule exception. Nothing in DS-149 covers U5209 or U5210. | U8409, U1415 and U5110 at best. U5209 and U5210 stay open, so check 5 still fails. |
| 4. Leave the five open | No further work on them now. They stay on the open-IC card. | No cost now. Check 5 fails, the DS-60 alternatives return, and the prototype order review stays held. | Nothing. |

Options 1 and 3 overlap: the simulations of option 1 are the same ones the U8409 and U5110 fallbacks need.

**Recommendation: option 1.** It is the only route that gives electrical evidence for the moves the geometry
forces, and that evidence is what the prototype order review will ask for.

### The options as they appear on the decision card

Question: How should the last five ICs be resolved now that no connector move can place them?

| # | Label | Consequence |
| --- | --- | --- |
| 1 | Simulate, then allow budgeted moves | Vendor-model simulation sets a capacitance budget per node; protected parts may then move within it. Slowest, may add a part. Can unblock four ICs; U1415 gets its own study. |
| 2 | Allow moves that keep nodes short | Protected parts may move if their node gets no longer than on paper. Fast, no simulation, weaker evidence for the order review. May unblock four ICs. |
| 3 | Use the per-IC fallbacks only | Simulation for U8409, a dual op-amp for U1415, a far pose for U5110. One new part. U5209 and U5210 stay open, so the gate still fails. |
| 4 | Leave the five open for now | No work on these ICs. The paper gate fails for five ICs, earlier alternatives return, and the prototype order review stays on hold. |

Recommended: 1. Reason: Only route with electrical evidence for the moves the geometry forces; the prototype order
review will need that evidence anyway.

## After the owner answers

- Option 1 or 3: the design authority briefs the simulation first (ngspice through the pinned oracle, the retained TI
  OPAx196 model, the MC04-S4 loop-break method), with its own independent review. No search starts before its result.
- Option 2: the design authority writes the no-growth test as a rule with its own controls, then one search brief.
- Option 4: the manager records the stop; the DS-60 alternatives are prepared for the owner.
- In every case MC04-L1 proceeds, and nothing is adopted without a generator task and its review.
