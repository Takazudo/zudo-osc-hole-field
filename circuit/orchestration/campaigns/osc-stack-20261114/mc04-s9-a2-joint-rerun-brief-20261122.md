# MC04-S9-A2 brief: joint re-run for U5209, U5110, U5210 and U8409

2026-11-22. Ruled by the design authority (DS-146) on the S9-A result (`254d1cbf`, report `mc04-s9-a-report-20261122.md`).
Executor: the Windows/WSL Claude Code session. Branch `claude/project-thread-iw3gai`.

**Kind:** study only, one run. Extend `scripts/stack/studies/mc04_s9_slot_moves/` with a new result file, new tests and
the report `mc04-s9-a2-report-20261122.md`. No canonical change. Inputs, fixed items and acceptance are as in S9-A,
pinned at `254d1cbf`. Start with `bash scripts/checks/regen-all.sh` and `pnpm circuit:check`.

## Why the U5210 result is held

The S9-A move of P-K-P-L13.01.01.01 is not accepted yet, for three reasons:
- its slot `[199.42–204.92, 194.92–196.42]` covers U8409's recorded courtyard `[198.25–207.88, 188.77–196.17]` by
  5.5 × 1.25 mm, which would close R1 for U8409;
- it moves RV8407, a rear trimmer (`KEEP_REAR_NEEDS_SERVICE_REVIEW` in `design/stack/trimmers/relocation-plan.json`), to
  K's front face, where trimmers are `FRONT_BLOCKED_IN_CLOSED_STACK`;
- the search stopped at the first clean candidate.

## Rule changes (only these)

1. **Input-buffer parts by kind.** This table replaces the blanket input-buffer guard:

   | Part | May it move within 24 mm? | Condition |
   | --- | --- | --- |
   | The buffer IC | No | Hard stop. |
   | Parts on a `*_FB`, `*_SUM` or `*_SENSE` node (R_FB, C_FAST, C_FB, R_IN, protection) | No | No budget exists; hard stop. |
   | Decoupler (for example C8438) | Yes | Same face as its IC, no farther from it than in the current record; report the original distance. |
   | R_ISO (touches only `*_DRIVE` and `*_REMOTE`) | Yes | No farther from its op-amp than now, so `DRIVE` does not grow; the `REMOTE` site keeps its class distance. |

2. **Covered block members are re-placed.** A target's block members that a fixed link covers are re-placed under the
   S8 block rules instead of failing the candidate. Decouplers stay on the IC's face and no farther from the IC than
   originally. For example, C5234 must come back to 5.7 mm or less from U5209, where the gate put it about 10.1 mm away.
3. **Trimmers keep their face.** A re-placed trimmer (`RV*`, `RVO*`) keeps its face.
4. **The five ICs stay clear.** A candidate may not cover the recorded courtyard of any of U1415, U5110, U5209, U5210 or
   U8409, whether it is open or not.

## Runs

- **U5209:**
  - variant A: L13.01.02.01 stays fixed, U5209 stays put, and its covered members (C5213, C5234, R5228, R5250, R5251,
    R5253) are re-placed;
  - variant B, only if A fails: L13.01.01.02 and L13.01.02.01 are both movable under the clean rules.
- **U5110:** all accepted P-K-P-L12.02.01.02 candidates.
- **U8409:** all accepted P-K-P-L03.01 candidates (183 known), with a cap of 200 per link and grid and a 4 h ceiling.
- **U5210:** all accepted P-K-P-L13.01.01.01 candidates on the 2.0, 0.5 and 0.25 mm grids, not only the first clean one.
- **Joint scene:** one scene with every chosen move. If U5210 and U8409 cannot both be clean, report both single results
  and say which excludes which.

## Report per clean move

Give the step 2c figures: loop, compliance, hold-by-hand, leads to trim and riders. Also give:
- every part re-placed, with its distance to its IC before and after;
- trimmers and their faces;
- any logic block moved that has a clock or RC timing node.

## Tests

- The outcomes are pinned.
- A candidate covering U8409's courtyard is rejected.
- A trimmer face flip is rejected.
- An R_FB move is rejected, and an R_ISO move within its condition is accepted.
- A mutation fails.

## Stop conditions

Stop on any of these:
- input drift;
- the S9-A result fails to reproduce under the old rules;
- the cap or the time ceiling is reached (report it as a cap);
- any need for a panel centre, sleeve, hold, cable or connector change.

No second run, no wider radius and no adoption. Oracle checks that did not run are written `NOT RUN`, with the reason.

## After it

Every clean move goes to one generator task, so c6 and checks 3 and 4 are rebound once. Each IC with no clean result
goes to the owner. U1415 already goes to the owner (DS-146), and the manager will put all remaining ICs on one card
after this run.
