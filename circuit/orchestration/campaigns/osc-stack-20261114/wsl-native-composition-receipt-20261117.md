# WSL post-composition native receipt

Tested source: `fb0ed1066091f4e0c5595d699378c1184725a96f`. Tooling: `71046f8a9809f937958e63ac9e528fc38f123a89`. Coordinator: x0x WSL Codex thread `01a1e7fb-e191-7382-8c35-5f76d36934fa`, acting in Moya's role under DS-133.

The project post-merge regeneration gate was run once for this composed review candidate. It is separate from the earlier `2c53715` receipt. Command: `bash scripts/checks/regen-all.sh --check`; outcome PASS, exit 0, no tracked regeneration drift. Machine-wide heavy guard reported PASS in 370 seconds. Run identity: `osc-composition-run.w7Fycwum`. [Tracker receipt](https://github.com/Takazudo/zudo-osc-hole-field/issues/362#issuecomment-6944882807).

## Input and execution contract

The preflight verified exact clean source/tooling heads, the authorized 20-path diff from the engineering base and all 14 pinned aggregate inputs. Cached image: `kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`. No pull or host KiCad override was permitted.

A unique user slice covered setup, aggregate and runner cleanup, with effective CPU quota 100000/100000, memory 4294967296 bytes, swap zero and 256 PIDs. The unchanged adapter verified each owned native container at one CPU, 4 GiB RAM, no additional swap and 128 PIDs. An external bounded supervisor retained control if the slice failed. Native deadline remained 900 seconds; total declared admission/execution/teardown bound was 1730 seconds under the shared 1800-second guard. No second heavy transaction was launched.

Runner preflight, cleanup and supervisor failure tests and independent code review preceded launch. Strict inactive states and owned labels/names were required before teardown success. Post-run inspection independently confirmed no owned Docker container, inactive wrapper/aggregate scopes and slice, removed runtime slice overrides, no scratch worktree registration and a free shared heavy slot.

## Observed verification

- Ten board schematic ERCs: zero errors, 673 retained warnings.
- Master schematic ERC: zero errors, 228 exact baseline warning identities.
- Native specified pin/net parity and deliberate hold-node mutation rejection passed.
- Twenty-one SVG exports and 36 PDF pages matched the draft hierarchy.
- Monitor/permit checks, 24 display cases and 13 rejected placement mutations passed.
- Regeneration diff and source status were empty. Runner and supervisor receipts both recorded verified cleanup and command exit zero.

The retained panel DRC hash check is not a fresh DRC execution. No PCB DRC or zone fill was run. These checks do not establish physical fit, hardware acceptance or manufacturing readiness.

Full output, input pins, empty diff/status and control receipts were archived locally in ignored cache. Archive-index SHA-256: `d9861013da278984c8d20c04abb18d8ea5f13086496c1b5ee9304a248c0f963c`. Raw intermediate monitor caches inside the deleted scratch checkout were not archived; no claim is made that those bytes remain available.

## Remaining WSL phase

This completes the current review composition's aggregate obligation. It does not complete the WSL phase or the project. Gate/source disposition and existing routing/DRC/fill holds still govern subsequent native work. New engineering inputs, if admitted, need their applicable checks. Existing passed inputs should not be rerun merely to keep the session active. Main/PR integration must not trigger held board DRC/refill jobs. The coordinator continues ready WSL work and necessary preparation; if all next native operations remain held or depend on an essential decision, it reports that specific dependency without claiming phase completion.
