# Issue 250 — JL117 source-bound negative diagnostic

This lane owns only `circuit/routing/epic-242/jl/**`. Status: **NEGATIVE_DIAGNOSTIC_READY / native NOT RUN / issue incomplete**. There is no routed candidate and no canonical adoption. All 117 native open edges remain obligations. The parent assigns native slots; the coordinator alone adopts copper and publishes epochs.

## Exact inputs and reconciliation

- Original assignment: `1da1909846dc3255888ecd36c88cee9737c85834`.
- Current assigned and inspected integration input: `40aa1cec58190487dc70aa5048a366e29a6b32a1`, epoch `epic242-e0`, draft PR260. The branch starts here and retains the newer accepted source deliveries. Production board, routing engine and harness inputs match the original assignment. New trimmer-label implementation/fixtures do not change this routing input.
- JL117 published and retained settled PCB: `e984c0a01156b5f282f0c849077c61572df30ee0c70dfe6c9db94fbfcfe52107`.
- Retained fresh native dump: `89430f34beaa157040e6222ad9c6c7ea0cc974c63c22363fbdd9ec6b199c3c6e`.
- [Accepted run 38038883190](https://github.com/Takazudo/zudo-osc-hole-field/actions/runs/38038883190), source `ccf1ae15619d7d8a9a027ef198bd742f9f350ac6`, artifact `11664813688`.
- Full ZIP: 45,476,297 bytes, SHA256 `452ffc9a1cf5e6e8d41e5e636e75d1e101fa28bd7ab23f2a21ebd461391d6138`; GitHub metadata retention expires 2026-11-09. Obtain it through the connected GitHub artifact tool or the artifact API, and compare complete size/digest before reading members. The temporary signed download URL is not a durable locator. Retain the whole ZIP before expiry; no Git LFS or large Git fixtures.

`prepare_diagnostic.py` authenticates all 26 source/workspace context files, full native group digests and every unresolved pad identity/pose. `cases.json` preserves all 90 unresolved nets, their complete endpoint projections and full-group digests: 103 signal edges, 14 AGND, zero rail. Full copper/group rows remain in the exact retained ZIP. The source contains 3,925 pads, 30,564 track rows and 2,861 vias. Eleven track UUIDs repeat in this accepted input; no track is deduplicated or renumbered. This is reported input state, not a new routing fix or permission to change copper identity.

All fixed 438 panel centres, 33 modules, six layers, sensitive circuit groups, 195 harnesses/390 complete connector identities/pin orders/poses and accepted copper remain unchanged. Frozen-input verification passes all 1,883 files. Canonical routed inputs were archived outside Git before source edits. Aggregate regeneration remains **NOT RUN**: the script invokes native KiCad and no slot is admitted. No drift is hidden or committed.

## Diagnosed cause and rejected evidence

`prior-rejections.json` extracts seven immutable proof receipts from PR221/225/226/229/233, with exact Git source/path hashes, candidate hashes, native run/artifact identifiers, original warning counts and negative dispositions. Their linked full receipts retain the full warning/group/boundary evidence. This lane verified those committed source bytes; it did not reauthenticate their complete old artifact ZIPs or rerun their geometry.

- PR221: both additive U2119 variants fragment original AGND.
- PR225: D8208 signal geometry fragments original −12V.
- PR226: both U8215 variants fragment J900035 AGND.
- PR229: R8107 ground gain leaves the cut signal victim and two retained boundaries unrestored.
- PR233: U8202 joint repair fragments a six-pad −12V group; partial rollback has 90 native errors; final merge/fresh bytes exactly restore JL117. Its lower intermediate count is not acceptance.

The new source diagnostic targets the still-stranded `U8202.14/.15/.16` AGND group, UUIDs recorded in the plan. It observes the **existing router's masks** with its A* entry point intercepted, never executing A*, compiling the native search library, cutting copper or changing physical geometry. Eight-neighbour same-layer flood connectivity is an optimistic upper bound on reaching the first through via. The exact source group has only three F.Cu pads and no existing through-copper source.

Hold the same 15.4 × 14.05 mm allocation, 0.025 mm lattice, 0.3 mm AGND width, 0.25 mm clearance, 0.6/0.3 mm via and all original fixed pad/drill/copper/edge/keepout masks. Change **only** the computational first-via window from 3 to 6 mm. Results:

| Window | Legal via cells anywhere in window | F.Cu source cells | Optimistically reachable cells | Reachable first-via cells |
| --- | ---: | ---: | ---: | ---: |
| 3 mm | 1 | 2,790 | 10,104 | 0 |
| 6 mm | 958 | 2,790 | 15,807 | 0 |

Both are bounded negatives: the problem precedes A* expansion budget on this tested no-cut fanout. Neither proves physical impossibility, a board-wide disconnected domain, or an absence of other legal layer/escape methods. The intercepted router's synthetic `search_exhausted` message is deliberately not published as measured search evidence. `no-copper-proposal.json` uses the existing grid format with zero cuts/additions; it is an identity diagnostic, never a copper improvement.

**Stronger review required before a new routing transaction:** choose a legal first-via/package escape and reconnect the signal victim, all outside anchors and original AGND/rail groups together. Explicitly preserve `C8122.1`, `C2322.1`, `U8106.4`, `C8124.1`, `U2304.4`, `U8105.4` on their original connected −12V group; exact UUIDs/poses are in the plan. No coupled-return strategy, electrical-rule change, H1/H2 regression fix or repeated failed geometry is improvised here.

## Replay and verification

Provision source dependencies in an isolated workspace venv using `requirements-source.txt`; these are source geometry dependencies, not a substitute KiCad oracle. From the repository root:

```bash
/workspace/jl250-venv/bin/python circuit/routing/epic-242/jl/prepare_diagnostic.py /workspace/jl250-cache/jl117.zip --check
/workspace/jl250-venv/bin/python circuit/routing/epic-242/jl/test_diagnostic.py /workspace/jl250-cache/jl117.zip
/workspace/jl250-venv/bin/python circuit/routing/epic-242/jl/native_diagnostic.py /workspace/jl250-cache/jl117.zip --label 250-u8202-firstvia-a1
python3 circuit/routing/epic-242/baseline/verify_inputs.py
pnpm circuit:check
```

Fourteen focused tests pass: full archive/input/context/pose/group binding, same-count changed membership, unexpected target copper, disconnected legal-via sites, unavailable starting layers, deterministic no-search regeneration and missing guard/admission, actual cgroup membership and whole-worker memory-cap refusal. Initial source generation took 3.90 seconds / 208,124 KiB peak RSS. All output/tool/input hashes and final checks are recorded in `verification.json`. Circuit contract validation is manual inventory only: 68 lines, zero declared placements, no schematic/placement binding; pin-asset check performed.

Real CLI help was inspected. `local_repair_pilot.py` accepts only `--board` and `--coupled`, with fixed issue189 plans; there is no `--plan`. `route_shards.py merge` can write canonical copper and is never invoked here. The lane does not replace the routing engine or exchange formats.

## Exact bounded native proposal — HOLD / NOT RUN

Only if the parent finds an optional fresh baseline observation useful, admit **one** baseline/fresh reproduction of this negative mask, with no search or candidate copper. It measures drift separately; a changed settled board, topology or context stops and preserves evidence. Existing `driver.workspace` copies the project/rules/sheets/both library tables at the required relative depth, and existing `driver.check` retains the max-six/three-equal refill procedure. The entire baseline/fresh directories and receipts remain in cache; transfer them as a retained supported artifact with all hashes after a run. Raw all-severity DRC identities are retained but are not a complete adoption warning audit.

Proposed command shape, to be pinned to the reviewed **actual lane head** at admission:

```bash
python3 circuit/routing/epic-242/baseline/native_guard_proposal.py \
  --admission-id PARENT_ASSIGNED_SLOT --worker jl250-firstvia-a1 \
  --sha REVIEWED_LANE_HEAD --seconds 600 \
  --hook-sha256 REVIEWED_INSTALLED_HOOK_SHA256 \
  --evidence /workspace/jl250-cache/native-guard-a1.json \
  -- /workspace/jl250-venv/bin/python circuit/routing/epic-242/jl/native_diagnostic.py \
  /workspace/jl250-cache/jl117.zip --label 250-u8202-firstvia-a1 \
  --native-slot PARENT_ASSIGNED_SLOT --execute
```

This is not executable authorization. Current guard is an unwired, operationally unqualified proposal and Docker hook is unapplied, so it fails closed. The parent must first qualify the existing Linux/systemd/local-Docker/version/cgroup/death/cleanup guard, preserve the 6 GiB whole-worker cap/no swap, 2 GiB free floor and 600-second deadline, and respect at most two native workers/12 GiB globally. Its current guard proposal excludes other native work during its admission. The parent must also provide any applicable existing managed-machine heavy guard through an accessible approved path; denied home paths are never read. No bypass or fallback is allowed.

A reviewed hook change/new integration input requires impact review and re-preparation of this lane's tool seals before admission; do not rewrite hashes to force old evidence. Native script refuses missing slot, missing bounded-guard environment, source drift and existing workspace labels. The exact head/hook/slot are admission inputs, presently unassigned. The command is optional topology evidence, not a cause remedy or a proposal to replay PR233. Prefer the retained negative unless stronger review needs current native observation. Full regeneration, full warning audit, native routing improvement, independent fresh candidate acceptance and canonical adoption remain NOT RUN.

## Session context and remaining work

Personal startup restoration/loader were denied earlier for protected runtime access. The owner explicitly waived optional personal-profile initialization for this session through the parent; no protected paths were retried, access controls changed or startup-success claim made. Accessible tracked AGENTS/WORKFLOW and relevant `.claude/skills/circuit-spec-integration` instructions were read; repository `.agents/skills` is absent.

Issue 250 remains open until zero complete native edges, all original groups/boundaries, zero DRC/parity, settled/fresh candidate agreement and full warning evidence are integrated/reviewable. Next source action is stronger review of the U8202 escape/return case or selection of another diagnosed case from `cases.json`. No merges, issue closure, default heavy CI, deployment, manufacturing, energization or credential creation are authorized.
