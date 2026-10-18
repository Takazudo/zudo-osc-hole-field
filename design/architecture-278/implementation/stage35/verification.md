# Stage35 verification evidence

Source-only checks in Codex Cloud; no physical/native qualification. Baseline
`9d9aa404a27dc7e5b8476e0d9f826fc44c517fbe`. Python 3.12.14, Node 24.19.0,
pinned pnpm 11.5.2 through Corepack. No Docker/KiCad installation or regeneration.

## Passed

- `python3 -m unittest discover -s scripts/architecture278/implementation -p test_stage35_cover_service.py`: 14 tests, 3.747 s on final test file.
- Same command with `python3 -O`: 14 tests, 5.995 s.
- `python3 scripts/architecture278/implementation/stage35_cover_service.py`: generated deterministic source artifacts after the final substantive edits.
- `python3 -O scripts/architecture278/implementation/stage35_cover_service.py --check --check-review`: deterministic outputs and final independent-review byte bindings passed.
- `COREPACK_HOME=/workspace/shared/corepack corepack pnpm check`: canonical validator, generated pages/preflight/models/footprint freshness and documentation TypeScript check passed; no regeneration invoked.
- `COREPACK_HOME=/workspace/shared/corepack corepack pnpm circuit:check`: baseline and final checks passed. Scope explicitly says manual inventory; schematic/placement binding not performed (68 lines, 0 declared placements unverified); pin-asset check performed.
- `git diff --check`: clean.

- `python3 scripts/architecture278/implementation/stage35_cover_service.py --check --check-history`: PASS. Detached Stage34 at `9d9aa404` passed generator/review/history, which replayed Stage33 at `2c41e8cd` and Stage32 at `9a3b9116`; Stage32 15 tests, Stage33 16 tests and Stage34 14 tests each passed normal and optimized. Observed normal/optimized test times: Stage32 46.416/55.037 s; Stage33 52.005/51.962 s; Stage34 83.798/78.198 s. Final Stage35 deterministic check passed.

- `python3 scripts/architecture278/implementation/check_source.py`: PASS after the final substantive review. Its complete `--check --check-history --check-review` command passed deterministic Stage35 output, all historical replay/tests and final review hashes. Composed-run normal/optimized test times: Stage32 41.661/42.983 s; Stage33 63.581/64.534 s; Stage34 91.272/99.705 s. Final output: `PASS isolated candidate current acceptance scope; canonical bytes unchanged; native NOT RUN`.
- Final staged `git diff --cached --check`: PASS, including new files. Fresh GitHub reads confirmed PR #287 still at baseline, parent #286 still at `b58068fbaeb65886958a67a4f4978613414e31c5`, and no new issue/PR comments before the Stage35 commit.

No substantive source change followed the independent review. Only this actual
execution-evidence record was finalized after the composed check. The independent
reviewer separately confirmed the review records accurately represent their work.

## First failures and review corrections retained

1. Baseline plain `pnpm circuit:check` selected host fallback pnpm 11.19.0 and
   failed because `/home/agent/.local/share/pnpm` was absent. No sandbox denial or
   fallback rebuild occurred. Used the repository's pinned version through
   `COREPACK_HOME=/workspace/shared/corepack corepack pnpm install --frozen-lockfile
   --store-dir /workspace/shared/pnpm-store`, then the checks passed.
2. Independent review round 1 requested occupancy/access corrections (HIGH) and
   screen regression tests (MEDIUM). Round 2 caught stale README text/values
   (LOW). Final substantive changes and generated outputs were independently
   re-reviewed and approved PASS_SOURCE_REVIEW_ONLY. See independent-review files.
3. Fresh `git fetch origin <PR branch> <parent branch>` succeeded, but the combined
   `git rev-parse origin/<parent branch>` failed because this single-branch clone
   has no parent remote-tracking ref. `git ls-remote` checks the actual remote refs;
   this is a lookup limitation, not a branch change or permission failure.

## Boundaries

Unit/source checks are not physical verification. Native KiCad/oracle, regen-all,
ERC/DRC, simulation, fabrication/manufacturing outputs, orders, energisation,
deployment, merge and M35 physical measurements: NOT RUN. CI is intentionally
skipped by commit marker for this bounded source-only study. No claim of hardware
qualification, current limit, wire flex capability or measured stiffness follows.

Historical replay is bounded at 600 seconds per Stage34 subprocess/test command,
using immutable detached worktrees; Stage34 retains its existing nested Stage33/
Stage32 limits. No unbounded older-stage regeneration is added. Temporary worktrees
are removed. All historical and canonical bytes are protected against the baseline;
only the three reviewed current-stage entrypoints may differ.
