# Backlog inventory: Takazudo/zudo-osc-hole-field (main ebfbc094, audited 2026-11-11, read-only)

Canonical checkpoint (circuit/routing/osc-pcb-current-checkpoint.json, recorded 2026-11-07): K = osc-core K2518 (open edges 2518, a1c69885), JL = JL184 (92d3e71d), JR = JR192 (b9aa748a). Status: unvalidated drafts, routing incomplete.

## Open PRs: 30 total, all draft, all created 2026-10-10..2026-10-22, none updated after 2026-10-22. No PR is new since 2026-11-09. All match the owner list exactly.

Mergeable state is GitHub's reported value (unknown = not computed). "Files" = changed_files. Every PR has a hold reason in its body unless stated. Many bases are stacked/integration branches, not main.

| PR | Title (short) | Head sha | Base | Files | Created / Updated | Mergeable | Diff summary | Hold reason stated | Label | Justification |
|---|---|---|---|---|---|---|---|---|---|---|
| 221 | Two rejected JL signal trials + native evidence | da646b12 | main | 19 | 10-10 / 10-10 | unknown | Evidence/scripts under circuit/routing/issue189/jl-layer-escape; JL118 era | "do not merge these rejected proposals" | REJECTED_EXPERIMENT_RETAINED | Negative evidence for JL118 (now JL184) |
| 225 | JL -12V fill rejection native confirmation | 52f0367e | main | 9 | 10-10 / 10-10 | unknown | Native probe evidence jl-d8208-native-probe | "Do not adopt or redispatch" | REJECTED_EXPERIMENT_RETAINED | Rejected geometry retained |
| 226 | [WIP] JL U8215 native rejections | cd8e9dd0 | main | 33 | 10-10 / 10-10 | unknown | Two rejected pilots, bounded-search evidence | "Preserve both rejections; never adopt" | REJECTED_EXPERIMENT_RETAINED | As above |
| 229 | JL118 R8107 via-branch repair | 38113a5f | main | 7 | 10-10 / 10-10 | unknown | Rejected 118->119 candidate + checker | rejected, terminal | REJECTED_EXPERIMENT_RETAINED | As above |
| 233 | U8202 joint -12V rejection + rollback | 729dff64 | main | 39 | 10-10 / 10-10 | unknown | Rejected stages, rollback proof (large add/del vs old main) | "Keep this draft as negative evidence" | REJECTED_EXPERIMENT_RETAINED | As above; base far behind main |
| 236 | Three whole supply exclusions vs core AGND splits | 424e0a71 | main | 24 | 10-10 / 10-10 | unknown | Core1402->1312 hypothesis source/proof | native outcome pending then; 1312 later REJECTED (see #238) | REJECTED_EXPERIMENT_RETAINED | Core1312 rejected; K is now K2518 |
| 238 | Recover core236 warning audit | 617082dc | main | 19 | 10-10 / 10-10 | unknown | Audit-recovery scripts/proof | "adopted=false"; 1312 rejected | REJECTED_EXPERIMENT_RETAINED | Audit-only recovery for rejected candidate |
| 239 | Bound native fixture lifetimes (stacked on 238) | 7add2a44 | #238 branch | 16 | 10-10 / 10-10 | clean | Process-isolation harness + 18-case comparison | "STOP for parent review"; no adoption | OWNER_HOLD | Possibly reusable harness; owner decision |
| 240 | Guarded isolated core audit recovery (stacked on 239) | 63f9541a | #239 branch | 7 | 10-10 / 10-10 | clean | Isolated recovery controller | run 38069793801 terminal pending at write; no replacement | OWNER_HOLD | Stacked chain 238-241 |
| 241 | After-stage core audits bootstrap (stacked on 240) | b3509059 | #240 branch | 111 | 10-10 / 10-11 | clean | StageBindings, 355/426 task reauth, KEEP_K1402 proposal | explicit "core1312 remains unadopted", parent review | OWNER_HOLD | Largest evidence in chain; contains unique recovery evidence; do not close |
| 260 | [Parked] Epic 242 integration branch | 5af0e7b6 | main | 2856 | 10-11 / 10-14 | unknown | 1.2M-line baseline + E16 evidence | PARKED, active plan #278 | OWNER_HOLD | Parent of 261-271 and 274-277 stacks |
| 261 | 100 trimmer functions + 23 gaps | 7aba720c | integration/epic-242 | 8 | 10-11 / 10-11 | clean | Trimmer inventory builder + docs | draft; CI deferred | OWNER_HOLD | Parked #242/#248 family; trimmer inventory may feed #249 later |
| 262 | Core split power/AGND contracts | 6494b3b4 | integration/epic-242 | 11 | 10-11 / 10-11 | dirty | Core-split power contract generators | "Do not merge as adoption decision" | OWNER_HOLD | Parked |
| 264 | Core stack mechanical alternatives | eff65d5a | integration/epic-242 | 25 | 10-11 / 10-11 | dirty | Mechanical comparison SVGs/tool | "Keep draft" | OWNER_HOLD | Parked |
| 265 | Two/three-core candidates + fixtures | c3c480f5 | integration/epic-242 | 19 | 10-11 / 10-11 | dirty | Candidate data and fixture recipes | "No merge" | OWNER_HOLD | Parked |
| 266 | JR129 endpoint evidence diagnostic | 06228d71 | integration/epic-242 | 10 | 10-11 / 10-11 | clean | JR129 cut-only diagnostic [skip ci] | not run, parent slot needed | OWNER_HOLD | Parked; JR is now JR192 |
| 267 | Trimmer silk annotation tool | 62281e83 | integration/epic-242 | 4 | 10-11 / 10-11 | clean | Annotation tool, 4 files | "Do not merge, adopt labels" | OWNER_HOLD | Parked; small, possible future reuse |
| 268 | K1402 core pilot for #252 | b3ced3bf | integration/epic-242 | 5 | 10-11 / 10-11 | clean | Core pilot case manifest/replay | blocked on artifact 403 | OWNER_HOLD | Parked (also env blocker historically) |
| 269 | JL117 U8202 first-via negative diagnosis | e45b69f6 | integration/epic-242 | 16 | 10-11 / 10-11 | clean | JL negative diagnostic | HOLD stated | OWNER_HOLD | Parked |
| 270 | Two-core feed placement feasibility | b3d72e10 | integration/epic-242 | 8 | 10-11 / 10-11 | clean | Geometric blocker + proposals | "Keep draft; no merge" | OWNER_HOLD | Parked |
| 271 | Joined power/interface gates | d7b4deed | integration/epic-242 | 8 | 10-11 / 10-11 | clean | Joined return-network bound | "BLOCKED"; no merge | OWNER_HOLD | Parked |
| 274 | E16 selective annulus policy | a811c2dd | integration/epic-242 | 52 | 10-14 / 10-14 | clean | E16 source + gates | "No merge/adoption"; CI skipped | OWNER_HOLD | Parked E16 stack (274->275->276->277) |
| 275 | E16 resistance attribution (stacked on 274) | 0159f8ac | #274 branch | 32 | 10-14 / 10-14 | clean | Attribution source + spec | same | OWNER_HOLD | Parked |
| 276 | E16 reconstruction fixtures (stacked on 275) | dec36940 | #275 branch | 20 | 10-14 / 10-14 | clean | Reconstruction bridge | paused by owner 10-15 | OWNER_HOLD | Parked |
| 277 | [Parked] E16 executor (stacked on 276) | fdac23b2 | #276 branch | 375 | 10-14 / 10-14 | unstable | Executor, qualification attempts | PARKED, owner-paused | OWNER_HOLD | Parked |
| 286 | O1 no-detent OFFSET candidate source (Stage1..19) | b58068fb | design/278-modular-gate | 809 | 10-15 / 10-17 | clean | Architecture-278 schematic/source stages | draft, unadopted; protected | OWNER_HOLD | Protected architecture observation; base branch is not main |
| 287 | Stage28 DIN decisions + A01 harness (stacked on 286) | e1969027 | candidate/278-o1... | 937 | 10-17 / 10-19 | clean | Stage28 on top of 286 | draft, stacked | OWNER_HOLD | Protected |
| 289 | Combined OSC demand / zudo-pd supply ledger | 3570012a | agent/278-stage28... | 9 | 10-20 / 10-20 | clean | Arithmetic ledger + pd pin verify | draft; adoption needs owner (#288) | OWNER_HOLD | Protected power observation |
| 290 | Stage55/56 idle-quad cleanup study | fa16c6ff | agent/278-stage28... | 85 | 10-20 / 10-20 | clean | Disposable osc-core candidate verification | "candidate verification, not adoption" | OWNER_HOLD | Protected; frozen source for #293 |
| 293 | CI: read-only frozen O1 topology observations | 8bdf7703 | main | 13 | 10-22 / 10-22 | clean | Diagnostic workflow/payload + 9 tests | "Leave PR unmerged; merge not authorized"; one run pending | OWNER_HOLD | Only draft PR based directly on current-lineage main besides 221-236; protected |

Notes: #293 base sha a133464c is older than main ebfbc094. Several of 221-236 bases are very old main shas, so any merge would conflict/regress; irrelevant since held.

## Label counts (PRs)

- REJECTED_EXPERIMENT_RETAINED = 7 (221, 225, 226, 229, 233, 236, 238); OWNER_HOLD = 23 (239, 240, 241, 260, 261, 262, 264, 265, 266, 267, 268, 269, 270, 271, 274, 275, 276, 277, 286, 287, 289, 290, 293). 7 + 23 = 30.

SUPERSEDED_OR_DUPLICATE: none proposed. No concrete merged commit was found that carries these PRs' unique evidence (diffs unmerged; evidence exists only on these branches).

## Open issues: 61 total

Status: paused = carries label "status: paused". Dates are last updated.

### Active campaign lane
| # | Title | Labels | Updated | Relationship / state |
|---|---|---|---|---|
| 315 | Complete accepted instrument implementation, order-ready review | paused | 11-11 | overall goal; no sub-issues attached via API |
| 311 | [K routing] new chain from K2518: signals-06..12 + escapes | paused | 11-11 | execution tranche; child of #310 likely |
| 310 | WSL continuation: receipts, copper identity, doc migration, K2518 routing | paused | 11-09 | execution tranche; parent of #308 |
| 308 | OSC4: K transaction budget (~95 vs 80 min), native lifecycle replay | none (NOT paused) | 11-11 | child of #310; active, only unpaused campaign issue |
| 318 | Reproducible selected-order manufacturing package after readiness gates | paused | 11-09 | manufacturing review prep |
| 305 | osc-core: 5 segment + 1 via UUIDs label two different copper objects | paused | 11-09 | copper identity defect |
| 324 | Fitted rail reservoirs and bleeders owner evidence | paused | 11-09 | new since 2026-11-09 |
| 326 | Regional SEL hold placement correction | paused | 11-09 | new since 11-09 |
| 327 | MIX4 OTA input-bias impedance imbalance | paused | 11-09 | new since 11-09 |
| 328 | NOISE2 filtered-rail bypass locality | paused | 11-09 | new since 11-09 |

### Qualification / follow-up gates (active-lane evidence, still open)
| # | Title | Labels | Updated | State |
|---|---|---|---|---|
| 65 | Measure board-stack supports, loom, hot distribution | - | 11-09 | open qualification (referenced as preserved gate) |
| 64 | Compact indicator optical/hot-current fit | - | 11-09 | open qualification |
| 57 | Source realization, capacity, thermal, startup, programmed-state gates | - | 11-09 | open qualification |
| 59 | Exact protection circuit evidence after conditional EXT draft | paused | 11-09 | follow-up |
| 55 | Physically qualify stepped five-selector assembly | paused | 11-09 | qualification |

### Historical umbrella / original epic subs (children of #1)
| # | Title | Labels | Updated | State |
|---|---|---|---|---|
| 1 | Epic: doc site, KiCad schematics/PCBs from R21 handoff | epic | 10-14 | historical umbrella |
| 45 | Whole-project verification, status pages, resource migration | sub | 11-09 | historical umbrella, recently touched |
| 43 | PCB group E core boards, power entry | sub | 11-09 | historical umbrella; recently touched |
| 39 | PCB group B oscillator control boards | sub, paused | 11-09 | historical |
| 21 | Component evidence bundles/catalog (ICs, semis, passives) | sub, paused | 11-09 | historical |
| 31 | Module design/capture: AR envelope | sub | 11-09 | likely complete-needs-owner-check |
| 28 | Module capture: four-colour noise source | sub | 11-09 | likely complete-needs-owner-check |
| 44 | KiCad checks in CI and published views | sub | 09-30 | likely complete-needs-owner-check |
| 42 | PCB group D envelope/offset control boards | sub | 10-03 | likely complete-needs-owner-check |
| 38 | PCB group A jack field boards | sub | 10-14 | likely complete-needs-owner-check |
| 32, 30, 29, 26, 25, 22, 13 | Module design/capture subs (wavefolder, filter+VCA, oscillator, attenuverter/offset, multiples/selectors, S&H pilot, toggles/pushbutton footprints) | sub | 09-28 | likely complete-needs-owner-check (stale 6 weeks) |

### Parked (owner policy)
189, 242 (parked epic), 243-259 (core recovery / core split / calibration / routing / integration 01-17), 253 (parked decision). All updated 10-14 20:22-20:25 (bulk-parked); none labelled paused. #214 deferred-verification (KiCad storage/CI pull failures, 10-10) is historical evidence for #189.

### Protected architecture studies
278 (epic, label epic, 10-20), 279-284 ([Design][01-06], label sub), 288 ([Coordination] Claude-Moya, 10-20).

### Out of scope
#2 Deploy doc site (deferred, outside epic).

### Not in owner's lists
- #308, #305, #324, #326, #327, #328 (campaign), #315/#318/#310/#311 as expected.
- #214, #64, #65, #57, #59, #55, #45, #44, #43, #42, #39, #38, #32, #31, #30, #29, #28, #26, #25, #22, #21, #13, #1: pre-campaign legacy issues; not named in owner policy, treated as historical/qualification.
- #325 is not an open issue (merged PR #325 per git log), #329 merged. #309, #312-314, #316-317, #319-323 are not open.

## Surprises
1. No open PR is later than 2026-10-22; nothing new since 2026-11-09. All 30 are drafts, none mergeable-clean against current-lineage main in a meaningful way (bases are old integration/stacked branches).
2. Open PR #293 and #221-#236 share base `main` at stale shas, but are all held.
3. Chain stacking means closing a parent (#238, #239, #240, #260, #274-276, #286) would retarget/orphan children; #241 holds 111 files of unique recovery evidence; #260 holds 2856 files.
4. Canonical checkpoint says rrr-01 stage accepted JL184/JR192 on 2026-11-05/06, so the JL117/118, JR129-133 figures in #221-#241/#266/#269 are outdated references (historical evidence only).
5. #308 is the only non-paused campaign issue and is a child of #310 (paused).
6. Issue sub-issue relationships for #315 returned empty; hierarchy for #310/#311/#318 not exposed via API.
