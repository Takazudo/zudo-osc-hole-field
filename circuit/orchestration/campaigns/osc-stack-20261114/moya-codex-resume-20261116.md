# Moya + Codex Cloud continuation of the OSC stack campaign
Prepared: 2026-11-16 JST
Revised: 2026-11-16 JST after the owner's attachment and takeover clarification
Repository: https://github.com/Takazudo/zudo-osc-hole-field
Campaign to continue: osc-stack-20261114
Target: main
Inspected engineering baseline: `85b2b489d6f47b34991e3d9b0d2e09991a458a97` (PR #361)

**Startup handoff prepared; incoming Moya acknowledgment pending. No implementation worker is dispatched by this documentation task.** This file's Git commit identifies its preparation revision; Moya must refresh actual `main` before admission. The setup changes management records only and does not adopt the stack.

Operational tracker: [#362](https://github.com/Takazudo/zudo-osc-hole-field/issues/362). Whole-instrument objective: [#315](https://github.com/Takazudo/zudo-osc-hole-field/issues/315). Historical coordination: [#288](https://github.com/Takazudo/zudo-osc-hole-field/issues/288).

Start with [the Moya execution prompt](moya-start-20261116.md), then this complete brief, the [campaign checkpoint](plan.md) and [decision log](decisions.md). Owner instructions recorded on 2026-11-16 JST / 2026-11-15 UTC are DS-128–132.

| Task | Tracking issue | Initial state |
| --- | --- | --- |
| MC-00 takeover | [#363](https://github.com/Takazudo/zudo-osc-hole-field/issues/363) | Planned; actual manager/capability acknowledgment pending |
| MC-01 coupling | [#364](https://github.com/Takazudo/zudo-osc-hole-field/issues/364) | Planned; depends on takeover |
| MC-02 gate evidence | [#365](https://github.com/Takazudo/zudo-osc-hole-field/issues/365) | Preparation after takeover; final packet depends on coupling |
| MC-03 trimmers | [#366](https://github.com/Takazudo/zudo-osc-hole-field/issues/366) | Planned; frozen geometry and refreshed brief required |
| MC-04 paper gate | [#367](https://github.com/Takazudo/zudo-osc-hole-field/issues/367) | Planned; exact final coupling/packet and independent authority required |

These are durable two-way issue links. Native GitHub sub-issue mutation was unavailable in the connected tools and the local GitHub CLI was not authenticated; no native hierarchy or reparenting is claimed.

## Purpose

Continue the existing direct-stack campaign with Moya as its single top-level manager and Codex Cloud as the implementation environment. Start a new implementation attempt from retained main and the recorded design contract, finish the paper evidence and its independent review, obtain the delegated design-authority ruling at Gate A-paper, then advance the accepted source and board work through the existing validation and integration gates.

The owner has confirmed that Fable automatic resumption is stopped and has directed that unpushed work be abandoned. Recovery and another stop confirmation are no longer startup dependencies. All six late-session text attachments, including the successfully re-uploaded c4, have been compared in full with repository evidence; none contains the missing post-#361 implementation. See section 14 for their exact relationship to main.

This plan does not restart the earlier parked routing campaigns, create a new orchestration product, or turn engineering drafts into qualified hardware. The most useful next deliverable is a reproducible, reviewed paper-gate packet and a recorded ruling, rather than a new routing run.

## 1. Verified starting point

GitHub inspection on 2026-11-16 JST established:

- main is 85b2b489d6f47b34991e3d9b0d2e09991a458a97, the merge of PR #361 on 2026-11-15 14:20 JST.
- The remote branch claude/project-thread-zao1qg points to that same commit.
- Before this setup created issue #362, both PR #362 and issue #362 returned Not Found; the latest existing PR was #361. The newly created #362 is the manager tracker, not recovered engineering work.
- PR #361 head 219e29d24b22a61cc5519e1966010b9cd1b33cd4 passed all eight checks in run 43678632021. The main push run 43680683898 succeeded.
- Queries for in_progress, queued, waiting, pending and requested Actions runs returned zero for this repository. This does not establish the state of Claude session workers or other repositories.
- Open PRs were #349, #293, #289, #290, #287 and #286. Recheck before acting. #349 is the browser preview of the current native drafts, not proof of the proposed stack. Preserve the historical/protected scope of the other five.
- The earlier investigation was read-only. The owner subsequently authorized this setup session to create #362–367, add backlinks and prepare/commit reviewed startup documents. Setup verification and the actual documentation PR/CI are recorded in #362. No stack implementation, native design adoption, purchase, manufacturing action or deployment is part of this setup.

Retained-evidence boundary and owner disposition:

The conversation reports completed post-#361 work: eight reordered links, maximum coupling ratio 0.978, 20 new tests with 18 fault-injection-sensitive tests, corrections to the coupling calculator, and independent review findings. Those completed implementation/review results were not found in the remote project branch.

DS-126 DOES retain the 0.978 expectation and the eight expected link outcomes as the previous manager's scratch prediction. DS-119 through DS-126 and the part-4 ST-02 brief retain a detailed implementation contract. The specification is retained; the subsequently reported implementation and verification remain unavailable. Recovery of those unpushed results is closed by owner instruction.

Do not describe the predicted 0.978 as an observed result on main. Do not report the missing historical reviews as closed. Give the new implementation its own attempt identity, verification and review. The user's statement establishes the automatic-restart disposition; it does not independently establish the state of every old child process. Check observable active jobs as part of ordinary admission without reopening an old-session export or generic confirmation request.

## 2. Accepted owner decisions

The existing campaign decision log records the following owner instructions in DS-128–132 and references earlier accepted choices. Preserve their provenance in current summaries. They are accepted choices, not questions to ask again.

A. Continue with the recommended stock-flat-cable option: 61 FFC links, accepting the recorded hand assembly and rework burden.

B. Accept DS-108 option A provisionally: retain the existing Bourns PTV09A panel pots; record the paper estimate above the maker's 50 C operating maximum as a risk until the first-article temperature test. Require approximately 10 mm feet or equivalent clearance keeping the rear wall off the table, plus ventilation at opposite enclosure edges. Verify the accepted physical enclosure in first-article test #64. This decision does not increase the manufacturer's rating or prove the ventilation sufficient.

C. Preserve the previously selected OSC2/OSC4 three-position SUB controls: PUL / one octave below / two octaves below. The divider clock is SAW_LOGIC, already decided in DS-30. Do not reopen the pulse-versus-saw decision.

D. Preserve the withdrawal of the separate connector coupon and Gate A-physical under DS-35. Do not reintroduce that coupon as a prerequisite. Actual-board assembly, continuity, temperature and other applicable physical checks remain open.

E. Preserve the fixed 438 front-panel hardware centres and the existing electrical/product constraints. Difficult design decisions remain delegated to a confirmed Astra design session in the new configuration. A negative paper gate or materially different product alternative is returned to the owner, with a recommendation.

F. Fable automatic resumption is stopped, as reported by the owner. Abandon recovery of unpushed post-#361 work and continue from retained main with a fresh attempt. This does not authorize deletion of old branches, private resources or already retained evidence.

## 3. Current engineering state

Canonical versus candidate:

- Canonical boards still use the ten-board cable partition, K at -100 mm, with the 120 mm enclosure proposal.
- The routing checkpoint is K2226 / JL184 / JR192, with parts-439 metadata-only successors. Native complete open-edge counts are 2,226 / 184 / 192. These are unfinished accepted drafts, not routed or qualified hardware.
- The new stack is candidate evidence only. Its latest interior depth target is approximately 40 mm, with K front at -30.6 mm and rear at -32.2 mm. The initial 34 mm figure is historical.
- The candidate removes O2/O4 as selector adapters and uses stock 0.5 mm same-side FFC links through K slots. Six rigid EL-to-P pairs remain. Custom flex circuits are not required by the current paper placement.

Current paper evidence:

- 511 signals assigned across 61 flat cables and 122 connectors.
- 22 fixings: 18 conductive posts plus four printed sleeves.
- 438 displaced footprints, 412 assigned courtyard-level replacement positions, 26 fourteen-pin ICs with no permitted position. Distribution: K 14, JL 6, JR 6.
- 122 latches to close and leads on 83 parts to shorten to 1 mm or less. Count parts, not individual leads.
- A 13-step assembly procedure lowering K in nine stages; the largest stage guides 17 cable ends.
- Latch access: 27 links shown open, three open after moves, 31 NOT SHOWN. Twelve K connectors need supporting pressure from the other hand.
- One service opening is recorded as 288 operations. Ten service openings put K ends at 11 of the sourced 20 insertion cycles.
- The committed coupling report is NEEDS_DESIGN: five links above the relative criterion, maximum 1.421. The criterion compares the modeled bound with the quietest existing harness carrying the same class pair; it is not a voltage, probability, measured crosstalk, or qualification of the baseline harness.
- Ground-current paper result: worst link ground contact 0.047 A with one post open, against the working 0.35 A bound. Recompute on the final reordered allocation.
- ST-07, the trimmer/test-point relocation study, has not been delivered. Its output folders are absent.
- Gate A-paper remains undecided. Its five checks are identity, access, allocation/current, coupling, and rework count.

Thermal screen at 40 C ambient with closed-case assumptions:

| Modeled location | 40 mm candidate | 120 mm current case |
| --- | --- | --- |
| P board / panel pots | 58.5 to 75.1 C | 57.2 to 68.2 C |
| K at 85 C-rated classes | 68.4 to 94.6 C | 68.3 to 92.7 C |

The pot maximum is 50 C; its derating curve is not permission to extend that range. All 101 pot dissipation calculations are NOT COMPUTED under the present accepted netlist rule. Keep the screen's verdicts. Feet/vents and first-article measurements are follow-up obligations, not a numerical pass. Thermal is outside the five Gate A checks under DS-94.

## 4. Manager and environment contract

Follow AGENTS.md, CLAUDE.md, circuit/WORKFLOW.md, circuit/ORCHESTRATION.md, circuit/orchestration/current-plan.md, the campaign plan and decisions, and circuit/templates/orchestration-task.md.

Use one active manager:
- Moya owns scope, dependencies, budgets, admission, decisions, review requests and integration authority.
- A selectable, confirmed Astra session handles hard architectural/electrical/validation decisions and the paper gate. Moya's name or an opaque Dots route is not evidence of the selected model.
- Codex Cloud handles bounded implementations and engineering tools with actual available workers. Do not assume Claude Project APIs, local CLI facilities, subagent model controls or automatic session creation.
- GitHub Actions and deterministic scripts handle admitted native checks, calculations, regeneration, waiting and evidence collection.
- Name one integrator. Keep independent review separate from implementation. If a Codex integration session performs remote Git operations, record its branch authority explicitly; ordinary workers do not independently promote their candidates.

Selected execution environment for the new work: Codex Cloud, with Moya coordination and the repository's existing GitHub Actions verification. Reapply the environment check before every wave. No new local WSL/Mac execution is selected by this plan. If an inseparable task needs unavailable native capability, physical hardware or another host, mark that task excluded/blocked with its unmet requirement; continue fully completable cloud slices. Legitimate CI does not substitute for physical evidence.

Before dispatch:
- Confirm actual session creation, model selection, credentials, repository access, Docker/native availability, completion notification and artifact retention capabilities.
- Fingerprint each real VM/pool. Worktrees and subagents on one VM do not add RAM/CPU.
- Re-observe account Actions headroom, other work, CI reserve and storage.
- Begin conservatively with at most three disjoint workers, one admitted heavy/native process per unprofiled VM, and one integration PR at a time. These are ceilings, not proof of available capacity or permission to start native work.
- Reserve the actual eight-check ordinary CI path. Phase 0 does not authorize speculative routing/compute fan-out.
- Assign finite time/memory/usage/attempt budgets in complete task briefs before launch. At most one infrastructure retry, only for an evidenced transient failure after the old attempt has stopped.
- Use completion events or bounded script monitoring. Do not spend repeated high-effort turns polling healthy jobs.
- Do not invent a session, automation, reservation or durable monitor because this plan mentions one.

## 5. Private source evidence

CLAUDE.md has an extra vendor-resource section that AGENTS.md lacks.

Read-only evidence repository:
https://github.com/Takazudo/circuit-dev-resources

The stack campaign's resources are present on:
claude/project-thread-zao1qg
Inspected revision:
d7cdf9e4dde7906abeafe82c7aa4f66134eee2f9

The thermal resource commit 1166eaa is also referenced by EV-01. Do not rely on default main alone, which does not contain the same stack evidence inventory.

Examples verified in the pinned README:
- hirose/fh12/fh12-catalog-pdf-2016-11-19-lcsc-mirror.pdf
  SHA256 9f056f58ff000739633cc3cb7697ba185967083dcf1429b7ab10783b3f55bac5
- bourns/ptv09/ptv09-series-datasheet-rev-01-25.pdf
  SHA256 411cdb6a62e61f9c5bc2df76ed64ee21d7bcfbee035c1ba36beff08c43f28558

Verify Codex's own access and the exact bytes it uses. This plan's successful README read does not prove the new environment's credentials. Preserve private evidence and the existing resource branch; do not republish vendor PDFs or delete the branch during cleanup.

## 6. Wave 0 — takeover and fresh-attempt checkpoint

Task key: takeover (MC-00 / #363)
Difficulty: moderate coordination; no heavy computation.

1. Refresh main, current remote branches, open PRs, current CI and campaign state. Preserve any work newer than the inspected SHA.
2. Record the former manager as historical context:
   https://claude.ai/code/session_01JXThoP3HSxfTMwSDwrkxP8
   Record the owner's statement that Fable automatic restart is stopped. The old screenshot's scheduled restart is superseded by that statement; do not ask for the same confirmation again.
3. Inspect observable active jobs and write ownership before admitting the new wave. Do not infer that every old child has stopped from the owner's automatic-restart statement alone. Reconcile a concrete conflict if one is observed; inaccessible old-session recovery is not a dependency.
4. Record the recovery decision as closed: unpushed implementation, test logs and historical reviewer findings will not be retrieved. Preserve existing branches and evidence. Do not request an export, wait for token reset or attribute the old reported test outcomes to the new attempt.
5. Start a distinctly named fresh attempt from retained main and the complete c6 clarification / DS-119–126 contract. Preserve main's a8 part-3 review corrections; the older attached a8 part-2 report is corroborating history, not a replacement input.
6. Verify the private source-resource access above.
7. Record new manager acknowledgment, dispatcher/integrator, source SHA, environment/model evidence, budgets, old-attempt disposition and next task in current-plan.md and the existing campaign. Do not create a parallel campaign solely because the manager changed.
8. Carry DS-128–132: accepted thermal and FFC-workload selections, automatic-restart disposition, fresh-attempt decision and incoming manager. Add the actual acknowledgment/session/admission receipt without presenting the prepared documents as a launch. Refresh current summaries while preserving dated history.

Acceptance:
- Single-manager ownership and old automatic-restart disposition recorded.
- Retained evidence and unavailable historical implementation clearly separated; the recovery path is closed.
- One canonical continuation checkpoint exists and identifies the next ready task.
- Actual session access and relevant resource limits are observed, not copied from the old Claude VM.

## 7. Wave 1 — finish the paper evidence

Task key: coupling (MC-01 / #364)
Difficulty: high; coupled calculator/algorithm verification.
Dependencies: takeover; source identity frozen.

Implement ST-02 a8 part 4 as a new attempt from the retained contract. Independently review the current ST-04 calculator and correct substantiated findings; the lost historical review text and fixes cannot be assumed or reconstructed from their reported count.

Contract:
- Preserve all 511 signals exactly once.
- Preserve link sizes, physical places, cable types, tails, slots, fixing geometry and the displaced-footprint projection.
- No logic run longer than three positions.
- Apply the SYNC_GATE ground rule and retained DS-62/77/78 rules and DS-79 adapter order.
- Apply SYNC_GATE grounding before counting the remaining logic runs. Every position freed by an outgoing rider becomes a ground inside its source link's logic runs even if the cap is already met. For a link giving no rider, move only the unused positions needed to satisfy the cap and retain the others for possible riders.
- Make logic runs as equal as possible under the c6 rules. Among equally admissible choices, keep lines from one site adjacent, then choose the lower ground position; equal-distance rider lines use the lower position. If runs of three still exceed the bound, try runs of two where unused positions permit before the specified rider remedies.
- Every actual class-pair bound on every link and host must be <=1.0; no epsilon waiver or 1.04 exception.
- For logic riders, use the fewest lines, same joint, <=55 mm. Host priority: all-logic hosts, then hosts already carrying logic, then other eligible hosts; nearest within each group; never a wiper host.
- Only when no logic-rider host works, use the documented precision/analogue rider fallback within 40/45 mm.
- Process full links in recorded order, trying other documented bounded orders if an order ends with a listed unresolved link. Stop unsupported cases with a named error; do not turn this into an unrestricted search. Mark each rider with its source link and reason "coupling" and report before/after orders, added grounds, distances, final ratios and unresolved links.
- Unsolved links are named with their nets, ratio and bound for Gate A. Do not silently change clustering, sizes, placement, length constraints or panel hardware.
- Treat the eight predicted changes and 0.978 in DS-126 as a comparison, not hardcoded expected output or a replacement acceptance limit.

Serialize the electrical-kernel boundary:
- DS-122/126 require the reorder pass to import the retained ST-04 pair function unchanged as its stop test.
- Review the retained calculator and freeze any substantiated new corrections first, then bind the final reorder/result to that same reviewed kernel. A reviewed calculation change requires the corresponding source identity and evidence to change together.
- If the kernel changes, recompute all 61 cable results and the affected ground-current evidence, not only the original five failures.
- Use precise input/projection hashes to connect placement, electrical report and assembly projection.
- Regenerate ST-08's affected projection after integration.
- Independently review the integrated code/result and retain the new attributed findings and dispositions. Record the historical findings as unavailable, without claiming they were resolved by the new review.
- Tests must detect substantive rule failures and stale evidence. Do not claim 175 tests or historical mutation results passed unless actually rerun on the new revision.

Task key: gate-evidence (MC-02 / #365)
Difficulty: high evidence/engineering review.
Dependencies: takeover; final coupling result for final packet.
Parallel boundary: read-only extraction and scoped evidence research can overlap coupling; no conflicting edits to its inputs.

Prepare a compact five-check packet with exact references and assumptions:
- Connector/cable identity at the exact counts, current, thickness, land patterns and supplier identity.
- Opening/locking geometry: FH12 open height, opening side and contact-1 orientation remain unsourced/assumed in the record; inspect retained evidence before requesting more.
- The 31 NOT SHOWN latch reaches; 12 support-hand operations; 17-end threading stage; assumptions about neighbour heights, nut/washer dimensions and cable folds.
- Allocation/current check on the final record.
- Coupling on the final reviewed kernel.
- The exact 26 unplaced IC references and search bounds, sensitive moves, total rework and viable bounded remedies.

DS-88 sends the nonempty 26-item list to the gate. Do not repeat unchanged placement searches or silently widen 25 mm. DS-97 treats courtyard locations as room evidence; the actual layout must preserve circuit functions, including local precision/timing/summing paths, rather than blindly applying 438 independent moves.

Task key: trimmer-plan (MC-03 / #366)
Difficulty: high circuit-sensitive placement proposal.
Dependencies: takeover; refreshed brief; frozen geometry projection.
Parallel boundary: own design/stack/trimmers/** and scripts/stack/trimmers/** only.

Refresh ST-07 before admission: K rear -32.2 mm, current FFC fields/slots/tails, 22 fixings, and already allocated cumulative replacement positions. Remove obsolete rigid-stacker, 48-fixing, pilot-hole and jack-screw assumptions. Replace the old VM/worktree/model budget with actual Codex evidence.

Re-inventory trimmers and test pads after applying the cumulative candidate placement transforms. The canonical inventory is 44 front-face trimmers and two test pads; it is not a hard final count. In particular, the link-gate candidate moves RVO1408 from K's rear to its front, so include newly front-facing or otherwise service-blocked adjustments. Deliver one mutually consistent plan with circuit-derived sensitivity, loop/guard/service implications, proposed positions or a named inability to place, and a retained checker. Keep panel hardware fixed and do not edit canonical boards.

ST-07 is useful parallel work but is not a formal Gate A-paper input under DS-47. Do not delay the gate solely to complete it. It must inform later source/K layout tasks, including ST-10/ST-25.

## 8. Gate a-paper — design authority

Task key: paper-gate (MC-04 / #367)
Dependencies: final reviewed coupling packet and current five-check evidence.
Difficulty: high; confirmed Astra decision, independent of the implementer.

Issue a durable ruling against the exact integrated revision:
- Decide each of the five checks, its evidence and unresolved assumptions.
- Explicitly decide the 26 unplaced ICs and access/assembly limitations. Passing coupling alone is insufficient.
- Record any bounded remedy and the exact candidate/source work it admits.
- Record how the owner's thermal/workload choices affect obligations without changing technical results.
- Re-decide DS-06 and the interface-routing hold. Until this ruling/source contract settles it, preserve the hold on K-joint interfaces on K/JL/JR/P, K GH-pad endpoints, front trimmers and power-land neighbourhoods.
- Preserve the withdrawn coupon. A positive paper gate is not actual-board fit, production qualification or automatic promotion of canonical PCB bytes.
- For NEEDS_DESIGN within the delegated scope, Astra defines the next bounded evidence task or design remedy and the manager continues without a redundant owner approval. Return a concrete recommendation and alternatives to the owner for a negative gate, a materially different product alternative, or a decision outside the delegated scope. Do not automatically revert to rigid connectors or old harnesses.

Exit artifact:
One concise gate matrix, exact evidence identities, explicit decision, remaining first-article obligations, and the next admitted task briefs.

## 9. After the gate — rewrite and execute the dependency graph

Do not dispatch historical ST-10..31 rows verbatim: several still describe rigid connector counts, obsolete EL shapes or jack-screw assembly.

Prepare the next bounded source wave from the accepted FFC decision:
- ST-10: partition, interface pin maps, planes, fixing/slot/source contracts and cumulative placement intent.
- ST-11: OSC2/OSC4 SUB schematic variant, SAW_LOGIC, exact connector/post identities, netlist parity and pinned ERC.
- ST-12: mechanical source, rear access, adopted feet/ventilation requirements and a truthful proposed-stack preview. Carry the c4 support constraint: keep the board gaps open along K's upper and lower edges, with no rail or carrier sealing either whole edge. Document the actual enclosure material and finish; c4 recommends a painted, anodised or plastic surface, while its assumed thermal terms are not a verified enclosure specification.
- Updated ST-20..25: P, retained adapters/EL, JL, JR and K candidate transactions, including O2/O4 retirement and the trimmer/SUB implementation.
- ST-26: new-interface K routing only once source/footprint decisions are stable and the gate releases the relevant hold.
- ST-30..31: joined parity/electrical rebind, interface evidence, checkpoint and documentation reconciliation.

At each step use specification/generator edits and actual regeneration, independent review and required native/full-warning gates before canonical promotion. Maintain a single writer for canonical boards and aggregate outputs.

Keep the wider completion objective visible:
- #59 and #343–348 own real on-board protection, independent return/GND-loss sensing, all-rail monitoring and signal isolation. A thinner stack does not close them.
- Reconcile the protection inventory against SUB/selector and interface changes before freezing a final board contract; do not assume old path counts remain universally applicable.
- #305 identity migration, #308 native transaction budgets, unfinished K/JL/JR routing and the other existing engineering tasks remain separate obligations.
- #55/#57/#64/#65 retain their actual physical/pre-power/first-article roles. #64's protocol should measure the actual accepted enclosure and placements, including the pots and the other hot classes. Preserve the existing proposed points RV204, SW607 and D1108 where still applicable.
- #318 remains HOLD until implementation and applicable pre-order gates genuinely pass. No fabrication package is part of the immediate migration/paper-gate wave.
- #349 may be reviewed as an independent preview task; it must not visualize the proposal as adopted. Do not bulk-merge the five older protected PRs or revive #242/#253 work.

10. TRACKING, REVIEW AND CONDITIONAL INTEGRATION

Use the operational super epic for the current summary and milestone progress:
https://github.com/Takazudo/zudo-osc-hole-field/issues/362

Preserve the existing whole-instrument objective:
https://github.com/Takazudo/zudo-osc-hole-field/issues/315

Reuse the coordination mailbox when appropriate:
https://github.com/Takazudo/zudo-osc-hole-field/issues/288

The #315 body and #288 contain old epochs. Read their later comments and the current campaign/checkpoint; do not restore K2518 or KEEP_K1402_INCUMBENT as the current board, or reinstate superseded WSL-only instructions.

The initial task records already exist: #363 takeover, #364 coupling, #365 gate-evidence, #366 trimmer-plan and #367 paper-gate, linked to #362. Reuse them and the existing campaign. Before later implementation, search for matching board/protection tracking and create only missing focused records linked to #362 and the relevant existing objective. Preserve existing native parent relationships; use durable two-way body links when native mutations remain unavailable. Do not duplicate or reparent #315, #310 or #59.

The implementing session is authorized to maintain in-scope tracking, development notes, commits, candidate branches and PRs under the owner's existing development authority. Record milestone decisions, exact checks and revisions, failures, PRs, blocked work and next actions. Re-read before modifying issue bodies, preserve others' text and read back writes. Do not call issue creation or an open PR delivery.

Refresh state before choosing each implementation PR. #362 is the newly created manager issue, not a recovered PR. The old conversation's PR-number prediction is historical; use the actual number GitHub allocates. Start a new scoped draft PR from current main unless a current read finds a matching continuation PR. The documentation setup PR is linked from #362 and is not the missing engineering implementation. Do not reset or force-update the old Claude branch.

Carry the existing conditional regular-merge authority: complete eligible in-scope merges after accepted scope, independent review, required approvals and all current-head required checks pass. Do not stop at "merge-ready" merely for a redundant generic confirmation. Hold incomplete/failed PRs. Confirm main integration and its CI separately. Close only fully satisfied delivery children after integration; #315 and coordination records remain open while their broader scope remains incomplete.

The inspected CI builds/checks documentation without deploying it. No separate deployment, release, purchase, quote, supplier contact, fabrication-service upload, order, energization or Cloudflare credential action is authorized. Do not bypass access controls, gates or protected environments.

## 11. Verification and source consistency

Read the current commands and their prerequisites before invoking them. Retain full history needed by frozen-study replay; the research checkout's shallow history is not a suitable execution baseline.

Core entry points:
- pnpm circuit:check before and after evidence/source edits.
- The project's source-regeneration requirement before each task, coordinated through the integrator so workers do not run duplicate heavy suites.
- bash scripts/kicad/run.sh kicad-cli version
- bash scripts/checks/regen-all.sh
- bash scripts/checks/regen-all.sh --check
- pnpm check
- pnpm build
- pnpm check:site
- python3 scripts/checks/frozen_studies.py discover scripts/stack/geometry
- python3 scripts/checks/frozen_studies.py discover scripts/stack/link_electrical
- Corresponding affected fixings/trimmer checks.
- scripts/checks/osc_pcb_checkpoint.py and applicable native/identity gates.

The pinned KiCad image recorded in the project is:
kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec
Verify the actual version is 10.0.6 through the wrapper. A convenient installed version is not equivalent.

Use current .github/workflows/check.yml. The present eight-check structure is Documentation checks; Python and native checks; Superseded study replay; Aggregate source regeneration; Python unit tests aggregate gate; and native DRC for K/JL/JR. Observe current-head evidence, not only an old green badge.

If Codex lacks Docker/native support, record local checks as NOT RUN with the exact reason and use legitimate existing Actions after admission. If a required pre-edit regeneration cannot be completed either there or through an authorized suitable execution boundary, do not pretend it ran; continue independent reads/proposals while resolving that capability.

Retain regression evidence from fixes and fail-closed identity checks. Re-run dependent studies and aggregate generation after merged source/evidence changes; hash-only updates still need proper source binding. Do not hand-edit generated reports to clear staleness.

## 12. Continuation and stop conditions

After every bounded batch:
1. Refresh current main, live jobs, task states and holds.
2. Review actual output and update the five-check packet/queue.
3. Recheck environment, dependency, budget and write ownership.
4. Admit only ready in-scope work; run applicable checks.
5. Independently review, integrate serially when eligible and verify actual main.
6. Checkpoint and select the next ready task.

Continue across individual PRs within the accepted stack campaign. Do not end merely because one task or PR is done. Stop with a durable checkpoint when the current accepted scope is completed, a fresh review finds no ready compatible work, a finite budget is exhausted, or an exact owner/access/physical/design gate prevents further safe progress. Do not broaden into unrelated issue cleanup or silently expand native budgets.

The checkpoint must identify manager/session, allowed host, source/main/working SHAs, decisions, exact task-to-issue/branch/PR/session mapping, live attempts, candidate/evidence paths and hashes, terminal state, checks, blockers, next safe operation and retained resources. Conversation prose alone is insufficient.

## 13. Terminal resource audit

Record initial branch/status, pre-existing diffs and worktrees before editing. At each wave boundary and before the final report enumerate touched issues, PRs, branches, worktrees, processes and tracked/untracked changes with owners and current states.

Protect user-owned, unexplained and uncommitted work. Commit/push or durably checkpoint wanted changes. Do not use blanket reset/clean/restore, forced branch deletion, forced worktree removal or an automatic stash hiding unknown work. Remove only individually verified disposable output created by this work.

Return the primary checkout to its safe original parent/default branch when task work is protected and doing so will not overwrite changes. Remove only clean workflow-owned temporary worktrees with ordinary git worktree remove. Delete only confirmed merged, unused workflow-owned branches after checking current refs and PR dependencies. Retain unmerged/held branches, foreign resources, the old Claude branches and the private resource branch while they contain needed evidence.

A worker unable to complete a permitted remote cleanup returns repo/ref/expected SHA, PR merge state, attempted action and exact error. The manager independently checks safety and authority before any retry; never bypass an explicit denial or branch protection. Each host owns its local cleanup; a cloud manager must not claim to have removed an inaccessible worker worktree.

Recheck status, current branch, worktree list and relevant remote refs. Report kept/closed issues, kept/removed worktrees, retained/deleted branches, failed actions, ambiguous resources, exact final checkout/diffs and the next operation. Keep incomplete parents and coordination issues open.

## 14. Resolved owner inputs and attachment reconciliation

The owner has resolved both earlier startup questions:
- Fable automatic restart is stopped.
- Unpushed work is abandoned; continue with a fresh attempt from retained main.

Do not ask these questions again or make old-session recovery a prerequisite. Ask for exact missing Codex access/model/resource capabilities only after inspecting what is actually available. Do not ask again about SUB, thermal option A, FFC workload or the withdrawn coupon.

All six attachments were read and compared in full with the retained project. The original uploads are not an execution dependency: their substantive bodies are retained in the public source paths indexed below. Hashes identify the supplied reading copies, not additional missing required resources:

A. design-review-a3-continuation-c5.md
   Its c5 body is byte-identical to the c5 section in the current reviews/da-03.md. Only the reading-copy preface is additional. It records the thermal ruling before EV-01 and ST-05 a3 were delivered; their old NOT RUN state is not a reason to repeat their subsequently merged work. The operative pot rating stays 50 C. The scratch model with approximately 10 mm feet and 20 cm2 of vents still estimates P at 51.7–61.4 C across the stated 40 C ambient orientations. These are model results, not measured temperatures or a guaranteed enclosure design. Carry the accepted feet/vents and first-article test obligation without declaring thermal compliance.
   Attachment SHA256: fc123b3b8a81b95997eb6406a1e68553095464ce12fa6e70a53bb2264fc6cb12
   Shared c5 body SHA256: 3d86a72cff57dba15f0211e616e3cadea82fd9e5caa0d8e57ffbbafe9d9a1517

B. design-review-a3-continuation-c6.md
   Its c6 ruling and clarification are byte-identical to the current reviews/da-03.md. It is the retained reorder contract, not the missing implementation. The pass, ST-04/ST-08 regeneration, study tests, KiCad and aggregate regeneration are explicitly NOT RUN in that document. Its scratch numbers are predictions. The later DS-126 eight-link result and 0.978 likewise remain predictions on main; use actual fresh results and the <=1.0 contract.
   Attachment SHA256: 8f5b88c6e5965fdae73a82112b731036ed43f8625b2460366a07123a9465049c
   Shared c6 body SHA256: f42eef8f74e017e558af6a9f0986e7a71eb11bdbe0002aa40c89d9d34d96ad88

C. link-placement-record-a8.md
   Exactly matches design/stack/geometry/links/link-gate.md at historical merge b483876 (a8 part 2). Current main has a8 part-3 corrections: one rider order tried with a documented 5,040-order ceiling; an explicit SleeveTrialNotImplemented stop for the unimplemented sleeve-movement trial; and the thermal handoff's rotation/reference-point explanation. Preserve these corrections. The 61 cables, 511 signals, 438 displaced footprints, 412 provisional positions, 26 unplaced ICs and 83 trimmed parts agree. The attachment contains neither the later coupling-reordering code nor its 20 reported new tests.
   Attachment SHA256: f8574a5904f9a0ebd51ebf8df4a67c483eb8c8c1a7b3408a7406045d0a0042bf
   Current main report SHA256: 3af0fa173c74a1c9920bb64d7c459e3a91ffa67d343577e9c72b39cc05a06340

D. assembly-procedure.md
   After its three-line reading-copy preface, the body is byte-identical to current design/stack/fixings/threading-procedure.md. It includes the corrected 1.0301 mm bend term and the 13-step / nine-stage / maximum-17-end procedure. Its geometry/access projection intentionally excludes signal positions. A pure signal-order change should preserve this procedure, subject to its projection check; no mechanical evidence is gained by copying or rewriting it.
   Attachment SHA256: e35510ddd9745b2533cf69c0eb9ac74023c5eb327bb40cdd1a3ae9db9158389e
   Shared body SHA256: 518129c2cb1053fa5810ddc75be8b37af5b47f0dd1888be7768c71703b34ab2c

E. README.md
   This is the spacer bench handoff, not the repository root README. It matches current design/stack/spacers/README.md after the copy preface and exported relative links are normalized. It specifies two 18.8 mm sleeves for 19 mm board gaps and two 16.8 mm sleeves for 17 mm gaps; the 10-long / six-short plate includes spares. No STL bytes accompanied these attachments. The source and generated STLs are retained in the repository; no new printing or STL-regeneration task is required merely because this README was attached. Physical fit and load capacity remain unverified.
   Attachment SHA256: 3afafaf9dda9e37faf6344c4f1e57a6354ff98bd710d419e3397fa38bf7461c4
   Normalized body / main source SHA256: 8742586cba768f259f9debe7a82655f734625baceffef98bba53fb923ebca6ff

F. design-review-a3-continuation-c4(1).md
   The initial c4 upload was unavailable; the replacement arrived during the review and was read in full. Its c4 body is byte-identical to the current reviews/da-03.md, with a reading-copy introduction added. It retains the earlier thermal ruling: thermal remains outside the five Gate A-paper criteria; compare the board at the exact part with that part's retained limit; carry the upper/lower K-edge airflow reservation into ST-12; give sensitive functions priority in the courtyard study without adding a thermal-distance term. Its old NOT RUN entries for ST-05 a2 and ST-02 a8 part 2 are historical and do not supersede their later retained outputs. No new implementation or unresolved owner choice is supplied by this copy. The feet/vents choice is already settled by the owner's instruction.
   Attachment SHA256: e70bd825e16b5579759d5ee6f7561223f7b27ebc312e9e09ceab0b3fef00bbe1
   Shared c4 body SHA256: b8dd03a53933e35230d3232f42db43ef2141eec5c50b268e8a36ce0385eda09b

Consequent next task:
   Finish the takeover checkpoint, then admit the fresh ST-02 a8 part-4 / ST-04 implementation-and-review task in section 7. Complete the gate packet and obtain the delegated Gate A-paper ruling. The new attachments do not close the 26 unplaced ICs, the access/assembly assumptions or ST-07.

## Primary evidence index

Operational tracker and startup:
https://github.com/Takazudo/zudo-osc-hole-field/issues/362
https://github.com/Takazudo/zudo-osc-hole-field/blob/main/circuit/orchestration/campaigns/osc-stack-20261114/moya-start-20261116.md

Repository workflow:
https://github.com/Takazudo/zudo-osc-hole-field/blob/85b2b489d6f47b34991e3d9b0d2e09991a458a97/circuit/ORCHESTRATION.md

Campaign and decisions:
https://github.com/Takazudo/zudo-osc-hole-field/tree/85b2b489d6f47b34991e3d9b0d2e09991a458a97/circuit/orchestration/campaigns/osc-stack-20261114

Retained c4/c5/c6 rulings and c6 clarification:
https://github.com/Takazudo/zudo-osc-hole-field/blob/85b2b489d6f47b34991e3d9b0d2e09991a458a97/circuit/orchestration/campaigns/osc-stack-20261114/reviews/da-03.md

Historical geometry report matching the a8 attachment:
https://github.com/Takazudo/zudo-osc-hole-field/blob/b483876/design/stack/geometry/links/link-gate.md

Spacer source and retained generated models:
https://github.com/Takazudo/zudo-osc-hole-field/tree/85b2b489d6f47b34991e3d9b0d2e09991a458a97/design/stack/spacers

Canonical checkpoint:
https://github.com/Takazudo/zudo-osc-hole-field/blob/85b2b489d6f47b34991e3d9b0d2e09991a458a97/circuit/routing/osc-pcb-current-checkpoint.json

Stack plan:
https://github.com/Takazudo/zudo-osc-hole-field/blob/85b2b489d6f47b34991e3d9b0d2e09991a458a97/doc/src/content/docs/decisions/osc-direct-stack-plan.mdx

Geometry:
https://github.com/Takazudo/zudo-osc-hole-field/blob/85b2b489d6f47b34991e3d9b0d2e09991a458a97/design/stack/geometry/links/link-gate.md

Electrical:
https://github.com/Takazudo/zudo-osc-hole-field/blob/85b2b489d6f47b34991e3d9b0d2e09991a458a97/design/stack/link-electrical/README.md

Assembly:
https://github.com/Takazudo/zudo-osc-hole-field/blob/85b2b489d6f47b34991e3d9b0d2e09991a458a97/design/stack/fixings/threading-procedure.md

Thermal:
https://github.com/Takazudo/zudo-osc-hole-field/blob/85b2b489d6f47b34991e3d9b0d2e09991a458a97/design/stack/thermal/README.md

Merged PR:
https://github.com/Takazudo/zudo-osc-hole-field/pull/361

PR and main CI:
https://github.com/Takazudo/zudo-osc-hole-field/actions/runs/43678632021
https://github.com/Takazudo/zudo-osc-hole-field/actions/runs/43680683898

Private retained resource revision:
https://github.com/Takazudo/circuit-dev-resources/tree/d7cdf9e4dde7906abeafe82c7aa4f66134eee2f9

Full-instrument objective and latest cloud-first handoff context:
https://github.com/Takazudo/zudo-osc-hole-field/issues/315
https://github.com/Takazudo/zudo-osc-hole-field/issues/315#issuecomment-6799629390

Protection and later manufacturing review:
https://github.com/Takazudo/zudo-osc-hole-field/issues/59
https://github.com/Takazudo/zudo-osc-hole-field/issues/318

