# Stage36 verification evidence

Baseline `8fd10c4a4841daf4d8e1e92346ce7d7282227764`; source-only Codex Cloud.
Pinned Python3.12.14, Node24.19.0, pnpm11.5.2 through Corepack. Portable startup
already consumed in this chat; runtime restoration skipped. No installer/native run.

- `python3 scripts/architecture278/implementation/stage36_interface_cassette.py`:
  generated analysis/summary and original SVGs after substantive corrections.
- `python3 -m unittest discover -s scripts/architecture278/implementation -p test_stage36_interface_cassette.py`:
  final seven tests PASS,0.301s. Same with `python3 -O`: seven PASS,0.328s.
- `COREPACK_HOME=/workspace/shared/corepack corepack pnpm circuit:check`: PASS.
  Manual-inventory scope:68 lines,0 declared placements unverified; no schematic/
  placement binding; pin-asset check performed. Baseline also passed before edits.
- `COREPACK_HOME=/workspace/shared/corepack corepack pnpm check`: PASS; canonical
  source validator, generated freshness/models/footprints and documentation tsc.
- `git diff --check`: PASS before staging.
- Rendered final plan-r01/service-r02 SVGs with PyMuPDF and visually inspected
  both. Service-r01 had overlapping labels; r02 fixes them and records the
  stud-head stop. r01 retained under diagram-history. PyMuPDF font/dash fallback
  is documented; final text is readable and unclipped. No external image assets.

## First failures and corrections

- CairoSVG import failed (ModuleNotFoundError); used installed PyMuPDF, no install.
- Initial guessed GH-bundle/check_source paths were absent; located actual paths
  using rg. No source data inferred from the failed lookups.
- Initial root/post draft put its solid post through the bushing and had an
  inconsistent short-screw reach. Corrected before final review to posttop90,
  bushing90..100, thread84..90 and M3x16 bearing101/tip85. Still unqualified.
- Independent review found D6 head cannot pass D4.4 bushing. Kept the same failed
  concept, documented +32mm stop; +75mm audit is hypothetical, not feasible.
- Review found inherited scalar registration insufficient for new ±1mm each-axis
  obligation. Changed cross-carrier norm to sqrt(3), added regression. Clarified
  newly signed bow sensitivity and exit-path screen scope. Re-reviewed final fixes.

Native KiCad/oracle, regeneration, ERC/DRC, manufacturing, physical, energization,
fabrication, ordering, release/deploy/merge: NOT RUN. No wire/current/stiffness
qualification. No follow-on mechanism or Stage37. CI intentionally skipped by
commit marker because ordinary PR workflows include excluded native operations.

## Final composed acceptance

`python3 scripts/architecture278/implementation/check_source.py`: PASS after
final substantive review. This runs Stage36 `--check --check-history --check-review`,
replays Stage35 at8fd10c4 (which replays34→33→32), and verifies all review hashes.
Stage36 history is bounded at900s for the Stage35 composed command and120s per
Stage35 test command; nested historical limits are unchanged. No unbounded replay
of older stages was added. Temporary worktrees were removed.

Normal/optimized test counts: Stage32 15/15, Stage33 16/16, Stage34 14/14,
Stage35 14/14; all PASS. Final output: PASS isolated candidate current acceptance
scope; canonical bytes unchanged; native NOT RUN.

`python3 -O scripts/architecture278/implementation/stage36_interface_cassette.py
--check --check-review`: PASS. Independent reviewer separately confirmed both
review records faithfully reflect their final review and32-file hash manifest.
No substantive source changes followed final review; only this execution-evidence
record and review bookkeeping were finalized afterwards. Fresh remote reads
confirmed PR287 baseline8fd10c4, parent286 b58068f,31issue comments (latestStage35),
no PR comments/new work claim before commit.
