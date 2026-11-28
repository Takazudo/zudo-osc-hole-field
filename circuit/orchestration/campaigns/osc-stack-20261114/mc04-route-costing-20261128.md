# MC04 route costing: no remaining route covers all five ICs, U8409 has no supported route but its connector, and only a link re-plan leaves the circuit and the protected rule alone

2026-11-28. Issue #367 (MC-04 paper gate). Design authority under DS-03 (Fable design agent at high effort, model
`claude-fable-5-2`). Written at head `27448163` of `local/cloud-engineering-20261127`. Draft, uncommitted.
Revision 2: the first issue (`d4bda821…da95830e`) was reviewed ACCEPT WITH CORRECTIONS
(`reviews/mc04-route-costing-review-20261128.md`, 2 blocking and 9 non-blocking findings). All are applied; the
table "Revision 2 changes" maps them.

Basis: the owner chose option 1 of DS-198, "Cost the remaining routes first" (2026-11-28 14:41Z).

This is a desk comparison. No search and no simulation was run for it, and it changes no file but itself and one
row of `decisions.md`. Nothing is adopted. Every board and schematic stays an unvalidated draft, check 5 stays
NEEDS_DESIGN and #318 stays HOLD. Nothing here is a purchase, a quote or a supplier contact.

**Every workload, part count, capacitance and risk figure below is an estimate** unless it is quoted from a named
record. Figures quoted from records are geometric or model evidence, never measurements.

## What was read

| Record | Used for |
| --- | --- |
| `mc04-s9-remaining-five-decision-packet-20261122.md`, DS-145 | routes R1 to R5 as first ruled; far-pose estimates |
| `mc04-s9-a-report-20261122.md` | the TSSOP-14 room arm and the far-pose distances |
| S12 report and disposition | which link blocks which IC, and why |
| S13 and S14 dispositions (DS-175 to DS-187) | model evidence on node headroom and the 10 pF what-if |
| S15 report, disposition and the cached screen (`screen.json`, `76d2e8e5…3304152f`, pinned in `bulk-manifest.json`) | single-move results and how far nodes grow |
| `design/stack/geometry/links/link-gate.json` at head | sizes and loading of the blocking links |
| `.claude/skills/component-spec-audit/references/inventory.json` | parts that exist in the inventory |

One new reading was taken from the cached S15 screen for route C: for each needed link, the smallest "largest tree
growth on any evaluated net" among its replayed slots. It is arithmetic on recorded figures, not a search.

## The five ICs and what blocks each

All five are OPA4196IDR quads (C2057385, SOIC-14, board K, rear face).

| IC | Cell | Units in use | Blocking link | Link size and load | Why no slot works (record) |
| --- | --- | --- | --- | --- | --- |
| U5110 | W2 fold cells F1 to F4 | 4 of 4 | P-K-P-L12.02.01.02 | 8-way, 6 circuits, 3 riders | 16 legal slots, all lengthen a node; 28 more are illegal while the East links stand (S15) |
| U8409 | M4B remote buffers and attenuverters | 4 of 4 | P-K-P-L03.01 | 26-way, 25 circuits (15 signals, 11 grounds on 26 positions), 6 member sites | all 131 legal slots leave a displaced footprint with no free position (S15, A3) |
| U5209 | W1 servo, pre-gain, drive sums | 4 of 4 | P-K-P-L13.01.01.02 (with L13.01.02.01) | 8-way, 7 circuits, 2 riders | 25 legal slots fail; L13.01.02.01 has nowhere to go (S12, S15) |
| U5210 | W1 fold cells F1 to F4 | 4 of 4 | P-K-P-L13.01.01.01 (and L03.01) | 8-way, 8 circuits | 81 legal slots fail; 5358 others collide mostly with L03.01 (S15) |
| U1415 | O4 sine shaper | 2 of 4 (two unused grounded followers) | P-K-P-L08 (and L07) | 40-way, 27 circuits, 9 member sites | every class-legal slot of L08 covers U1415 (S12) |

The link record holds 62 links and 124 latches today, against the 61 and 122 the owner accepted in DS-128 (DS-143).

## How workload is counted

One **cycle** is a design-authority brief, an independent review, one run, a result review and a disposition, as
S12 to S15 each were. A **generator task** is a cycle that changes sources and regenerates, followed by the gate
checks that are still `NOT RUN` for these ICs (c6, checks 2, 3 and 4, latch access, threading). An **evidence
task** is the component workflow for a part that is new to the inventory: sources, spec, symbol and footprint
assets, previews, generated page and validation. All counts are estimates.

## The routes, across all five ICs (the six asked for, and route G added in Revision 2)

### A. Re-plan or split the blocking links: the only route that keeps the circuit, the parts and DS-150 as they are

- **What it is.** Move the signals of a blocking connector to other links, split it into smaller connectors, or
  change which sites it joins, so that no connector stands on the IC.
- **On record.** Never studied. S12 and S15 moved connectors but kept every link's signals and members fixed. The
  link gate had 339 unused positions on 122 connectors when DS-110 was merged (2026-11-15). At head the `unused`
  fields of the 62 live links sum to 322 on 124 connectors (the review's reading). Spare positions exist in
  principle; whether they are near enough is not known.
- **Link count and hand work (estimate).** Splitting one link adds 1 link and 2 latches. Folding a small link
  into neighbours as riders removes 1 link and 2 latches. For the five blockers the plausible range is 60 to 65
  links and 120 to 130 latches, against 62 and 124 today. The 83 parts with cut leads would change by an unknown
  amount. Any change from the DS-128 figures needs the owner to accept the new workload.
- **Workload (estimate).** One total: **3 to 5 cycles for all five ICs, generator tasks included.** That is 1 to
  2 feasibility cycles (East and South together, West apart or with them), 1 to 2 generator tasks, and room for
  one repeat. The per-IC figures further down are not additive: the East links share one study and one generator
  task. Learning whether L03.01 can be re-planned at all is the first of those cycles. The link gate is
  cumulative, so a re-plan can shift other links and other displaced parts; parts and blocks that earlier stages
  placed (73 K-block packages in stage 7 alone, DS-143) would have to be re-checked inside the generator task.
- **Parts.** Connector and cable sizes already listed in `link-gate-options.json` are expected to suffice
  (estimate). No new part type is expected.
- **Risk.** Assembly: more or fewer latches and cut leads, and a changed threading order. Electrical: riders put
  signals beside new neighbours in a cable, which check 4 (coupling) judges and which has not run. Programme: a
  regression among already placed ICs.
- **Owner decision.** Yes if the link count or hand work changes (DS-128). No rule on protected parts changes.

### B. Far poses with a locality exception: contradicted by the model evidence for four of the five

- **What it is.** The IC and its block move 38 to 113 mm to the nearest free area, and the nodes that leave the
  block get longer.
- **On record (S9 packet, estimates at 1.5 × HPWL and 0.20 pF/mm).** Cheapest poses: U1415 38.71 mm, U5110 40.61 mm,
  U5209 49.65 mm, U5210 80.61 mm, U8409 113.22 mm. Grown nodes: U5110 F1_SUM +45.6 mm; U5209 EMITTER +92.7 mm;
  U5210 F1_SUM +129 mm; U8409 1_GAIN +235 mm with the W_SENSE nets near 27 pF; U1415 SINE_MINUS +69 mm. The far
  poses of U5110, U5210 and U8409 overlap, so at most one of the three can use its pose.
- **Against it.** S13 and S14 found no node with model headroom that frees an IC. They were the "simulation for
  U8409" that DS-149 names as its fallback. The largest budget found was
  16 pF, on three plain control sets, and only with the 10 pF what-if. A +45 mm summing node is roughly +9 pF by
  the campaign's estimate, on a class of node that showed no headroom.
- **Workload (estimate).** Per IC: reopening the simulation route (closed by DS-186), 1 simulation cycle, 1
  generator task. 2 cycles per IC, with a low chance of a positive result for U5210 and U8409 (the S9 packet
  already called them "likely to fail").
- **Owner decision.** Yes, twice: a locality exception per IC and the reopening of DS-186.

### C. Bounded growth of protected nodes: rows-level slots exist for U5110 and U5210, and no evidence supports any growth

- **What it is.** DS-150 is loosened so a protected node may lengthen by a set amount, then one search.
- **On record (new reading of the S15 screen).** Among the slots that are gate-legal with every other link at
  record and pass A1, A3, A4 and A6, the slot with the smallest "largest growth of the tree figure". Growth is
  measured against the base effective scene. "Failing nets" counts nets that fail any of NG1 to NG3.

| IC | Best recorded slot | Nets failing NG1 to NG3 | Nets whose tree grows | Largest tree growth against base | ICs moved (protected) | Face changes |
| --- | --- | --- | --- | --- | --- | --- |
| U5110 | L12.02.01.02 at (159.0, 229.0) +y, one of four slots tied | 8 | 5 | 5.5 mm | 1 (0) | D5107, R5149, R5152, R5268; two of them protected |
| U5210 | L13.01.01.01 at (200.92, 199.67) +y | 11 | 9 | 11.1 mm on two link-carried nets on P; 6.4 mm at most on a protected node | 2 (0) | R5260, R5263 |
| U5209 | L13.01.01.02 at (167.75, 189.0) +y | 26 | 18 | 19.7 mm (27.2 mm against the S15 limit, the smaller of paper and base) | 1 (1) | not read |
| U8409 | none: every slot fails A3 first | 25 or more | not read | 12 mm or more | 4 or more (1 or more) | not read |

  With the campaign's standing estimate (1.5 × length × 0.20 pF/mm) the three figures are about 1.7, 3.3 and
  5.9 pF. The estimate was made for half-perimeter lengths; applied to a tree figure it is rougher still.
- **U5210 does not need L03.01 moved on this route.** Its best slot is legal with L03.01 at its record. 51 of its
  81 legal slots pass the four acceptance items and fail only the no-growth rule. These are rows-level results:
  the overlay items (A5, A7 to A9, A11) and the full gate replay (A12) were not run on them.
- **Against it.** No electrical evidence supports growth of any size. S13 labelled 38 of the 64 protected nets
  FAILS AT ZERO STRAY. S14 then re-scored class A's 11 rows to "no headroom", 2 pF against the 4.3 to 16.3 pF they
  would need, and the 15 class B rows fail only at the pair corner with IN- at 50 pF. Parts that change face need
  vias on their nodes. U8409 is not helped.
- **Workload (estimate).** 1 cycle for a search under a bound the owner names. A generator task only if a scene
  appears. Realistic yield: U5110 and U5210 at rows level at best, each still to pass the overlay items and A12.
- **Owner decision.** Yes: a change to DS-150 with a number in it, set without evidence.

### D. A part change: a credible route for U1415 only

- **In the inventory.** OPA4196IDR (SOIC-14, fitted), OPA4197IDR (SOIC-14, "precision candidate") and OPA4197IPWR
  (TSSOP-14, fitted on six input buffers by DS-143).
- **Candidate, not in inventory.** An OPA4196-family TSSOP-14, and an OPA196-family dual for U1415. Exact part
  numbers are for the evidence task to establish; none is asserted here.
- **On record (S9-A, room only, no part selected).** With a TSSOP-14 courtyard (7.70 × 5.99 mm) the nearest legal
  pose is still 40.61 mm for U5110, 49.34 mm for U5209, 79.21 mm for U5210 and 113.22 mm for U8409. U1415 has
  room at 22.5 mm, but only by displacing seven passives, three of them input-buffer parts (C1302, C1303, R1321).
  Combined with connector moves, none was clean for U5209, U5110, U8409 and U1415; the combined arm was not run
  for U5210. The study kept the links at record and searched within 24 mm. It was not repeated under the 35 mm
  radius of DS-149. A dual for U1415 has never had a room study.
- **OPA4197IPWR is not a drop-in here.** DS-145 excluded it: the +12 V margin is 0 mA after DS-143, and no
  simulation covers these cells with that part.
- **Workload (estimate).** For U1415: 1 evidence task, 1 room study cycle, 1 generator task with a specification
  change. For the other four quads: none on record (S9-A, 24 mm); a repeat at 35 mm would be 1 cycle.
- **Parts and BOM.** One new BOM line. A dual frees two unused op-amp units and their grounded-follower wiring.
- **Risk.** A new part needs its own evidence and model. The room result for U1415 depends on moving three
  protected parts, which is again a DS-150 question.
- **Owner decision.** Yes: a new BOM line, and DS-150 for the three input-buffer parts unless the dual fits
  without them.

### E. Circuit or value changes: one is on record, and it frees no IC

- **On record.** 10 pF of feedback (KEMET C0603C100J5GACTU, already in the inventory as `C_FB`) on the nine weak
  summer cells cures the weak loops in the model at about 7° of phase at 20 kHz (S14). It gave a 16 pF budget to
  three plain control sets and freed no IC. Class B, which holds U8409 and U5210, already carries that capacitor.
- **What it could do with route C.** Little: the rows that block U5110, U5209 and U5210 are in classes A, B, F
  and G or lack a diode model, and all stayed blocked with the capacitor (S14 disposition).
- **A remote buffer for U8409.** The S15 disposition listed this as a DS-149 fallback. That was loose: DS-149 says
  "simulation for U8409", and S13 and S14 were that simulation. No remote-buffer change is on record as a route.
- **Other circuit changes** (a different cell topology, fewer fold stages, a buffer moved to another board) have
  no record at all. Each would be a design change with new evidence, not a placement remedy, and none is costed
  here.
- **Workload (estimate).** The capacitor proposal: 1 cycle plus a generator task, and nine new 0603 parts that
  must themselves find room beside crowded nodes.
- **Owner decision.** Yes: a specification and BOM change. It addresses design item DS-185 (a), not the gate.

### G. An exception to a link's class distance: U1415 only, unstudied

- **What it is.** U1415's blocker is not a protected part. Every one of L08's 787 class-legal slots covers it
  (S12). L08 has 2189 gate-legal slots before the class-distance rule, so slots exist that the class distances
  exclude. Whether any of them clears U1415 was not read.
- **Cost (estimate).** 1 cycle to read the existing census and judge the slots, then a generator task. The class
  distances bound how far a signal's sites may sit from its connector, so an exception lengthens those signals
  on the board. No evidence on record says which may.
- **Owner decision.** Yes: an exception to a link-gate rule, per signal class.

### F. Leave the IC open

No work. Check 5 fails for that IC, #318 stays held and the DS-60 alternatives return. One open IC holds the gate
as surely as five.

## Per IC: what each route would cost and unblock

Workload is in cycles (estimate). "Rule" marks a route that needs an owner rule decision.

### U8409: only the link re-plan has support on record

| Route | On record | Workload | Parts | Risk | Unblocks | Rule |
| --- | --- | --- | --- | --- | --- | --- |
| A. Re-plan L03.01 | unstudied; 25 circuits (15 signals, 11 grounds), 6 sites | 1 to learn; the rest shared (East) | none new (est.) | regression in other links; hand work | U8409; under the present rules also the way for U5210 | DS-128 if counts change |
| B. Far pose | 113.22 mm; W_SENSE near 27 pF (est.) | 2 | none | high; contradicted by S13 | unlikely any | locality, DS-186 |
| C. Bounded growth | every slot fails A3 first | n/a | none | n/a | nothing | DS-150 |
| D. Part change | none on record (S9-A, 24 mm: nearest 113.22 mm; combined arm failed on C8438) | 1 to repeat at 35 mm | candidate, not in inventory | new part evidence | nothing on record | BOM |
| E. Circuit change | already has `C_FB`; no other record | not costed | n/a | n/a | nothing on record | spec |
| F. Leave open | | 0 | none | none | nothing; holds #318 | none |

What each exclusion rests on, and what was never studied:

- The far pose is rated unlikely, not excluded: 113.22 mm and W_SENSE nets near 27 pF are estimates, set against
  model evidence of no headroom.
- The part route rests on one room study at 24 mm with the links at record.
- Route C fails because parts lose their position. U8411 loses it in 124 of the 131 slots, U8313 in 48 and U8310
  in 31. No study has asked whether those ICs could be given poses another way, for example by a block search.
- So "only the link re-plan" means: no other route has support on record.

### U5210: waits on L03.01 under the present rules, but not under a growth bound

| Route | On record | Workload | Parts | Risk | Unblocks | Rule |
| --- | --- | --- | --- | --- | --- | --- |
| A. Re-plan L13.01.01.01 with L03.01 | unstudied; 8 of 8 circuits | shared (East) | none new (est.) | as U8409 | U5210 if L03.01 clears | DS-128 if counts change |
| B. Far pose | 80.61 mm; F1_SUM +129 mm (est.) | 2 | none | high; contradicted by S13 | unlikely any | locality, DS-186 |
| C. Bounded growth | best slot legal with L03.01 standing: 11.1 mm largest growth, 6.4 mm on a protected node, 11 failing nets; rows level only | 1 | none | no evidence for growth | possible at rows level | DS-150 |
| D. Part change | none on record (S9-A, 24 mm: nearest 79.21 mm; combined arm not run) | 1 to repeat at 35 mm | candidate, not in inventory | new part evidence | nothing on record | BOM |
| E. Circuit change | class B and the missing diode model block (S14) | not costed | n/a | n/a | nothing on record | spec |
| F. Leave open | | 0 | none | none | nothing; holds #318 | none |

### U5209: two small connectors, one with nowhere to go

| Route | On record | Workload | Parts | Risk | Unblocks | Rule |
| --- | --- | --- | --- | --- | --- | --- |
| A. Re-plan L13.01.01.02 and L13.01.02.01 | unstudied; 7 and 8 circuits, 2 and 4 riders | shared (East) | none new (est.) | riders already crowd these links | U5209 | DS-128 if counts change |
| B. Far pose | 49.65 mm; EMITTER +92.7 mm (est.) | 2 | none | high | unlikely | locality, DS-186 |
| C. Bounded growth | one acceptance-clean slot: 19.7 mm against base, 26 failing nets, one protected IC moved | 1 | none | largest growth of the four | unlikely | DS-150 |
| D. Part change | none on record (S9-A, 24 mm: nearest 49.34 mm) | 1 to repeat at 35 mm | candidate, not in inventory | new part evidence | nothing on record | BOM |
| E. Circuit change | no record beyond S14 | not costed | n/a | n/a | nothing on record | spec |
| F. Leave open | | 0 | none | none | nothing; holds #318 | none |

### U5110: the least stuck of the four, on any route

| Route | On record | Workload | Parts | Risk | Unblocks | Rule |
| --- | --- | --- | --- | --- | --- | --- |
| A. Re-plan L12.02.01.02 | unstudied; smallest load: 6 circuits, 3 riders | shared (South, with East) | none new (est.) | lowest of route A | U5110 | DS-128 if counts change |
| B. Far pose | 40.61 mm; F1_SUM +45.6 mm (est.); DS-149 fallback | 2 | none | class A has no headroom in the model | possible, unproven | locality, DS-186 |
| C. Bounded growth | best slot 5.5 mm, 8 failing nets, four passives change face (two protected), no protected IC moved; rows level only | 1 | none | no evidence for growth | possible at rows level | DS-150 |
| D. Part change | none on record (S9-A, 24 mm: nearest 40.61 mm) | 1 to repeat at 35 mm | candidate, not in inventory | new part evidence | nothing on record | BOM |
| E. Circuit change | class A, F and G rows block (S14) | not costed | n/a | n/a | nothing on record | spec |
| F. Leave open | | 0 | none | none | nothing; holds #318 | none |

### U1415: a different problem, with a part route the others lack

| Route | On record | Workload | Parts | Risk | Unblocks | Rule |
| --- | --- | --- | --- | --- | --- | --- |
| A. Re-cluster L08 (or L07) | unstudied; 27 of 40 circuits, 9 sites | shared (West: 1 study, 1 generator task) | none new (est.) | largest connector; widest knock-on | U1415 | DS-128 if counts change |
| B. Far pose | 38.71 mm; SINE_MINUS +69 mm (est.) | 2 | none | sine shaper never simulated | unknown | locality, DS-186 |
| C. Bounded growth | does not address the cause: the blocker is L08's class distance, not a protected part | n/a | none | n/a | nothing | n/a |
| G. Class-distance exception for L08 | unstudied; 2189 gate-legal slots, 787 class-legal, all 787 cover U1415 | 1, then a generator task | none | longer member signals, no evidence | unknown | link-gate rule |
| D. Dual op-amp, or TSSOP-14 | TSSOP room at 22.5 mm by moving three input-buffer parts; dual unstudied | 3 | 1 new line (candidate, not in inventory) | new part evidence | U1415 | BOM; DS-150 for three parts |
| E. Circuit change | none | not costed | n/a | n/a | nothing on record | spec |
| F. Leave open | | 0 | none | none | nothing; holds #318 | none |

## What the comparison shows

1. **No route covers all five.** B and C have the model evidence against them, D has support for U1415 only, E
   frees no IC on record and G concerns U1415 alone.
2. **Route A is the only one common to all five**, and the only one that keeps the circuit, the parts and DS-150
   untouched. It is also the least studied: its cost range is the widest in this document.
3. **L03.01 decides U8409 on the record.** U8409 has no other route with support on record. Under the present
   rules and under route A, U5210 also waits on L03.01: S12 and S15 both show its slots blocked by that connector.
   Under a growth bound (route C) U5210 does not wait on it. The gate needs all five ICs, so U8409 alone makes
   L03.01 the first question.
4. **#318 needs all five, and more.** A pose for every IC closes check 5 only. c6, checks 2, 3 and 4, latch
   access and threading are still `NOT RUN` for any re-planned link, and the two design items of DS-185 stand.
5. **Lowest total estimate if route A works:** 3 to 5 cycles, generator tasks included, and no new part. If L03.01
   fails its feasibility cycle, no placement route with support on record is left for U8409 on the present link
   plan.

## Owner options

Question: Which route should be pursued first for the five open ICs?

| # | Label | Consequence |
| --- | --- | --- |
| 1 (recommended) | Test the L03.01 re-plan first | One study asks if the 25 circuits (15 signals and their grounds) of the connector on U8409 can go elsewhere. It decides U8409 on the record. Nothing changes yet; hand work may change later. |
| 2 | Re-plan all five blocking links | One larger study re-plans every blocking connector at once. Most work and the widest knock-on to placed parts; link count and hand work change. Fastest if it succeeds. |
| 3 | Start with U1415's part route | An evidence task for a dual or smaller op-amp, then a room study. A new BOM line; frees U1415 at best. The other four ICs and the order hold are untouched. |
| 4 | Leave ICs open; order stays held | No more work on these ICs now. The paper gate fails for five ICs, the earlier alternatives to the flat-link stack return, and the prototype order review stays on hold. |

Recommended: 1. Reason: U8409 has no other route with support on record, and the gate needs all five ICs. One
small study shows whether placement can close the gate before work is spent on the other four.

Bounded growth, far poses and a class-distance exception are not offered as options: the only evidence on record
speaks against the first two, and the third has none. The owner can still ask for any of them. Options 1 to 3 each need a design-authority brief and an independent review
before anything runs. Nothing is bought, built or ordered, and any adopted change is a separate reviewed generator
task.

## Decision rows proposed for the manager

| ID | Decision |
| --- | --- |
| DS-199 | Owner chose option 1 of DS-198; the route costing is drafted (appended to `decisions.md` with this document) |
| DS-200 (proposed) | Route costing accepted as a desk estimate: no route covers all five ICs; far poses and bounded growth have the S13 and S14 model evidence against them, though rows-level slots exist for U5110 and U5210 under a growth bound; a part change has support for U1415 only; a link re-plan is the one route common to all five; U8409 has no route with support on record other than a re-plan of P-K-P-L03.01 |
| DS-201 (proposed) | Owner choice pending: (1) test the L03.01 re-plan first (recommended), (2) re-plan all five blocking links, (3) start with U1415's part route, or (4) leave the ICs open with the order review held |

## Revision 2 changes

| Finding | Change |
| --- | --- |
| 1 (blocking) | The U5210 claim is limited to the present rules and route A. Route C states that U5210 has a rows-level slot with L03.01 standing; point 3, option 1, the reason, DS-199 and DS-200 are reworded |
| 2 (blocking) | "No other route with support on record" throughout; the U8409 section says what each exclusion rests on and names the ICs that lose position |
| 3 | Route C column is "ICs moved (protected)"; face changes are named and are passives |
| 4 | Route C states its reference (base), its count rule, the tie, the 27.2 mm figure and one estimate basis with the 1.5 factor |
| 5 | Route C marked as not addressing U1415; route G (class-distance exception) added |
| 6 | One route A total, 3 to 5 cycles with generator tasks, and per-IC cells marked as shared |
| 7 | "25 circuits (15 signals and their grounds)" |
| 8 | The S13 label count is cited as such, with the S14 re-score and the class B corner |
| 9 | Route D for the quads reads "none on record (S9-A, 24 mm)", with the arm not run for U5210 and the 35 mm repeat |
| 10 | Route E reconciles the "remote buffer" wording of the S15 disposition with DS-149 |
| 11 | The head figure (322 on 124) is given beside the DS-110 one |

## Not established

- Whether any class-legal or class-excluded slot of L08 clears U1415, and whether a TSSOP-14 finds room at 35 mm.
- Whether any link can be re-planned. Route A has never been studied, and its cycle counts are the least certain
  figures here.
- Any link count, latch count or cut-lead count after a re-plan.
- The exact part number, availability or suitability of any candidate that is not in the inventory.
- Any electrical property of any pose, growth or part. The capacitance figures are the campaign's standing
  estimate, not a measurement.
- Any circuit change other than the 10 pF what-if of S14.
