# Validation receipt — local WSL design checkpoint

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
