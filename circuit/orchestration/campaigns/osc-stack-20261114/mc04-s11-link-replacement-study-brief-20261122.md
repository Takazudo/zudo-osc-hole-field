# MC04-S11 brief: re-placement study of P-K-P-L07, L08, L12.02.01.02 and L03.01 (DS-149)

2026-11-22. The owner's choice (DS-149), briefed by the design authority. Executor: the Windows/WSL Claude Code session.
Branch `claude/project-thread-iw3gai`.

**Kind:** study only, one run. No canonical geometry, spec, BOM, board or gate change. A separate generator task
follows only on a design-authority ruling on this result. Every board stays an unvalidated draft, and check 5 stays
NEEDS_DESIGN.

**Start gate:** do not start until S10 Revision 1 is accepted after independent review. The manager will say when.
Pin every input by SHA-256 to the S10 result commit: `S10_RESULT_COMMIT = <executor fills in>`. If S10 stops or is
revised, this brief waits for a new pin.

## Inputs (at the pinned commit)

- `design/stack/geometry/links/link-gate.json`
- `design/stack/geometry/links/link-gate-options.json`, with the S10 slot holds
- `design/stack/geometry/links/link-era-replacements.json`
- `scripts/stack/geometry/links_gate.py` and `links_gate_part2.py`
- `scripts/stack/studies/mc04_s9_slot_moves/` (the method and the DS-146 rules)
- `design/partition/locality-acceptances.json`
- `design/grid/placements.lock.json`
- `design/stack/trimmers/relocation-plan.json`
- `design/stack/connectors/flex-links.json`

## Allowed changes

- A new directory `scripts/stack/studies/mc04_s11_link_replacement/`: a script with `--check`, tests, a result file and a
  README.
- The report `mc04-s11-report-<date>.md`.

Start with `bash scripts/checks/regen-all.sh` and `pnpm circuit:check`.

## Fixed

- the 438 panel centres and the 33 modules;
- the ruled sleeves and fixing keep-outs;
- every slot hold in the pinned options file;
- DS-06;
- every link other than the four;
- every cable code, stock length and stock-FFC direction;
- the overlay poses and acceptances of the pinned link-era record.

## Arm 0: premise

Reproduce the pinned gate record and the S9-A2 result for U5110 and U8409 under the old 24 mm radius. If they do not
reproduce, stop.

## Arm 1: search

**Keep-outs.** Use the recorded courtyards of U1415, U5110 and U8409, grown 0.35 mm, with their S8 blocks. No candidate
of any of the four links may meet them. U5209 and U5210 stay protected the same way.

**Radius.** Take candidates from the retained `links_gate.search` on the 2.0, 0.5 and 0.25 mm grids, first within
24 mm, then out to the 35 mm join radius. Report which radius each clean candidate needs. Nothing goes beyond 35 mm.

**L07 as a 26-way.** L07 needs 23 circuits. Run it in two sizes: 40-way as recorded, and 26-way.
- The evidence must be cited, not assumed. The 26-way connector is `FH12-26S-0.5SH(55)`, C202113, with cable C32128
  (60 mm). Cite them from `link-gate-options.json` `sizes` and `flex-links.json` (`item1_factory_listing`); they are
  already used by P-K-P-L03.01.
- Show that the retained allocation and ground rule fit 23 circuits in 26 positions. If they do not, the 26-way option
  is dead, and the report says why.
- The 26-way option closes nothing in Gate A check 1. Connector and cable identity stays NEEDS EVIDENCE.
- L08 needs 27 circuits and stays 40-way. No other link changes size.

**A candidate is accepted only when all of these hold:**
- member and rider class distances are kept (PRECISION 40, ANALOGUE 45, WIPER 55, LOGIC 55 mm), including riders the
  link hosts;
- the cable fits its stock length with loop ≥ 0, and compliance is ≤ 1.0 mm/N, listed above 0.25 with the hold-by-hand
  flag;
- there is no way-4 field growth, and the slot lies under the link's own front board.

**Re-placement of newly covered parts (DS-146 and DS-148 rules):**
- gate-style rows first (the DS-88 steps), and a block pose under the S8 rules where the gate pose breaks the block rule;
- no input-buffer IC and no part on a `*_FB`, `*_SUM` or `*_SENSE` node may move;
- decouplers keep their face and distance;
- R_ISO may move only if `DRIVE` does not grow;
- trimmers keep the rear face;
- nothing is stranded, no IC that has a position loses it, and the overlay poses stay legal.

**Joint scene.** L07 and L08 are searched as a pair. Then one scene holds the chosen moves for every IC that has one. If
two ICs' moves exclude each other, report both single results and say which excludes which.

## Success per IC

An IC succeeds when a candidate set leaves it legal at its recorded position with its whole S8 block, every rule above
holds, and the joint scene is clean.

Report per IC:
- the links moved, the radius used and the size of L07;
- the step 2c figures: loop, compliance, hold-by-hand, leads to trim, and members and riders against their limits;
- every part re-placed, with its distance to its IC before and after;
- the trimmers and their faces;
- any logic block with a clock or RC timing node.

Also report the workload change against DS-128: links, latches, leads to trim, the hold-by-hand list, lengthened tails,
and connectors by size.

## Tests and checks

- The outcomes are pinned, and `--check` reproduces the result.
- These candidates are rejected: one covering any of the three ICs, a rider beyond its class distance, a candidate beyond
  35 mm, an `*_FB` part move, and a trimmer face flip. A mutation fails.
- Every existing `--check`, the stack suite and `pnpm circuit:check` are unchanged.
- List what is not established: c6, checks 2, 3 and 4, threading, routing, DRC and any electrical acceptance. Oracle steps
  are written `NOT RUN`, with the reason.

## Stop conditions

Stop on any of these:
- S10 is not accepted, or the inputs drift from the pinned commit;
- arm 0 fails to reproduce;
- a clean result would need a panel centre, sleeve, hold or fixing change, a new part, a cable or connector code not
  already in the retained evidence, or a size change on any link other than L07;
- a cap or the time ceiling is reached. State both before the run, and report it as a cap, not as "no fit".

No second run, no radius beyond 35 mm, no adoption, no supplier contact and no order files.

## If an IC still fails

That IC goes back to the owner by itself, with its reason and its DS-149 fallback, without holding the others:
- **U8409:** a vendor-model simulation of the remote-buffer cell, so its feedback parts may move within 24 mm.
- **U1415:** one dual op-amp in place of the quad. This is a new part needing an evidence bundle, a BOM line and a
  footprint, and the room is unproven.
- **U5110:** the 40.61 mm far pose, backed by a fold-cell simulation and a rule exception.

The owner card also carries "stop": check 5 fails and the DS-60 alternatives return.
