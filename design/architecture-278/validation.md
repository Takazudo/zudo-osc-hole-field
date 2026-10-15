# Validation receipt — local WSL design checkpoint

Current results are in **Revision 2 actual checks** below; revision-1 results remain historical.

Platform: Linux x0x, kernel 6.18.33.2-microsoft-standard-WSL2, x86_64. Node v24.13.1; pnpm 11.5.2; Python 3.12.3; git 2.43.0; gh 2.87.3. Linux source/arithmetic/documentation evidence only. No Windows-native executable, container oracle, macOS evidence, native campaign or numerical campaign was executed. Other tmux sessions were inventoried; old worktrees retained. No claim that a shell's presence proves an active campaign.

| Command/check | Actual outcome and scope |
|---|---|
| pnpm circuit:check before and after edits | PASS, unchanged scope below |
| python3 scripts/architecture278/check_packet.py | PASS: four deterministic generators and protected-path guard against main 65cefd41fc39e064d38319115ad96016a1c6b71c |
| python3 -m unittest discover -s scripts/architecture278 -p 'test_*.py' | 43 tests PASS: 6 ledger, 13 interface, 11 mechanical, 13 electrical |
| pnpm check | PASS: unchanged generated pages/preflight/models/31 previews, site type checks |
| bash /home/takazudo/.codex/scripts/heavy-guard.sh -- pnpm build | PASS: 298 pages; guard verdict=PASS exit=0 secs=232 min_mem_mb=9155 reason=- |
| pnpm check:site | PASS exit=0: publication/host/assets/strict links; inherited workbench template exception remains allowlisted |
| git diff --check | PASS |
| Mechanical SVG | XML parsed; parent rendered with local librsvg/cairo and inspected 1200×900 preview; fixed clipped plane/overlapping UID labels; reviewers checked resulting generator/output. Not 3D/physical verification |
| Full regen-all, ERC/DRC, KiCad10.0.6 native, old E16/numerical campaigns | NOT RUN: owner prohibits this execution; regen-all also mutates canonical CAD |
| Complete electrical load/physical path closure, structural/package fit, bench/physical tests | NOT RUN: candidate not implemented/qualified, missing exact parts/datums and authorization |
| Default GitHub CI | Intentionally skipped via [skip ci]: inspected workflow automatically launches native tests and board DRC. No admission supplied. Skipped is not passed; local applicable checks above completed |

Actual circuit output, with **no SKIP line emitted**:

    SCOPE: inventory provider=manual; schematic/placement binding not performed (68 lines, 0 declared placements unverified); pin-asset check performed
    PASS: component-spec contract; 68 lines; offline=True; refreshed=none

Actual protected packet output:

    PASS: 33 functions, 438 centres, complete retained package/unit ledger; no native qualification
    PASS source extraction parity; NOT RUN electrical/physical qualification
    PASS source calculations/current outputs; mechanical fit NOT RUN; recommendation REVISE
    PASS: deterministic electrical report; physical electrical acceptance OPEN
    PASS: owned-output reproduction and protected-path guard; native/physical qualification NOT RUN

The strict site check prints one known broken template link `${esc(x.url)}` in the inherited workbench HTML and explicitly excludes it under the existing allowlist; exit0. No allowlist was changed. It inspected 27,764 internal links and 3,913 ID attributes. Publication scan's `docs-to-agent not scanned (pass --agent-skill <dir>)` is retained scope, not agent-publication acceptance.

One incorrect test invocation, `python3 -m unittest scripts.architecture278.test_mechanics`, failed because the test uses discovery-local imports. The documented discovery command then passed all 11 cases; all43 passed through the packet's advertised discovery command. No test assertion was weakened. Early checker defects found independently were fixed before this receipt: endpoint/net/owner conservation, shared reference classification, electrical finite numbers/group/limit lock, mechanical parameter-driven drawing/collision/extraction and retained bend bound. See exact reviewed hashes/findings in the three review files.

No production CAD, canonical copper, locked placement, source circuit or decision.json changes. No fabrication/order files, credentials, deployments, procurement or hardware operations. Original main checkout remains clean. Draft PR publication and SHA readback are recorded in WORK.md after commit.


## Revision 2 actual checks

Same actual local WSL2 Linux environment: kernel6.18.33.2-microsoft-standard-WSL2, Node24.13.1, pnpm11.5.2, Python3.12.3, git2.43.0, gh2.87.3. No Windows-native, macOS, container/KiCad or energized evidence. Source is the reviewed revision-2 engineering tree on the existing PR285 branch; WORK.md pins its publication commit. Parent verified both final review receipts against actual file hashes before commit.

| Final command/check | Result and exact limit |
|---|---|
| `python3 scripts/architecture278/check_packet.py` | PASS: seven deterministic generators, exact owned outputs and protected paths against unchanged65cefd41 base |
| `python3 -m unittest discover -s scripts/architecture278 -p 'test_*.py'` | PASS:86 tests, comprising43 retained +24 populated-mechanical +19 revised-electrical cases |
| `pnpm circuit:check` before/after | PASS; same actual manual-inventory SCOPE below; no SKIP line |
| `pnpm check` | PASS; generated pages/preflight,31 selected model/preview assets and site type checks |
| `bash /home/takazudo/.codex/scripts/heavy-guard.sh -- pnpm build` | PASS final298-page build; `verdict=PASS exit=0 secs=14 min_mem_mb=9203 reason=-` |
| `pnpm check:site` | PASS exit0;27764 links/3913 IDs; inherited `${esc(x.url)}` exception excluded by unchanged allowlist |
| `git diff --check` | PASS |
| Independent reviews | Mechanical24 tests plus adverse geometry/cluster mutations; electrical19 tests plus optimized-Python geometry/contract checks; both hash-bound final receipts |
| SVG | Final mechanical reviewer rendered/inspected the updated cluster drawing; parent also rendered/inspected earlier corrected handle/tool geometry with local cairosvg. Neither is 3D/physical proof |
| Aggregate regen-all / native CAD or numerical campaigns / ERC/DRC | NOT RUN: prohibited scope; aggregate also changes canonical CAD |
| Actual front-board packing, circuit-aware routed placement, all-path length acceptance, full state current/resistance qualification | NOT RUN/INCOMPLETE:14 named current non-wiper allocations exceed300mm; exact component solids/joints/state bounds remain implementation/physical tasks |
| Physical calibration, source/fault/reference recovery, support/fit/force/service and adjacent units | NOT RUN; no hardware operation authorized or performed |
| Default GitHub CI | Intentionally skipped with `[skip ci]` because inspected jobs invoke prohibited native tests/DRC. No workflow/guard weakened, no CI PASS claimed |

Actual circuit output:

```text
SCOPE: inventory provider=manual; schematic/placement binding not performed (68 lines, 0 declared placements unverified); pin-asset check performed
PASS: component-spec contract; 68 lines; offline=True; refreshed=none
```

The seven generators include the historical four generators, which deliberately still print their original REVISE/NOT RUN limitations, plus populated_mechanics.py, revision_electrical.py and orientation_sweep.py. Reproducing a negative result is a code/output PASS, not a passing architecture: the orientation checker explicitly reports that no examined orientation closes all paths.

The site scan still excludes docs-to-agent without an explicit agent-skill argument and reports40 binary artifacts not text-scanned. No exception/allowlist changed. Build log skips local doc-history generation by the repository's existing default; no deployment occurred.

Transient stale-report failures during coordinated source edits were corrected by regenerating dependent electrical/orientation outputs after mechanical inputs stabilized. Fresh final checks above passed. Independent review defects remain recorded in the review receipts; no acceptance test was weakened. Unsupported geometry now fails explicitly instead of silently using old coordinates.

Manufacturer source PDFs are inspected local evidence, not republished assets: exact HARTING bytes are under ignored `.circuit-cache/sources/architecture278-harting/document.pdf`, TC33 under `.circuit-cache/sources/architecture278-tc33/document.pdf`. Hashes, source URLs, conditions and locators remain in the committed receipts. Raw redistribution permission was not assumed. No oversized artifact or Git LFS was introduced.
