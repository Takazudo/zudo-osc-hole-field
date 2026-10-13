# Matched WSL native evidence — 2026-10-13

Execution head: `093f14b55c8a85d5d14be26f20868df2551d3b14`; implementation source: `26cfc65d5699b7e5c2edbd4957c1f4e231de4e1c`. Requests were prepared at that exact clean head. The owner separately invoked the control, startup-success, startup-failure, single-oracle and KA-t2 scripts, then explicitly invoked a serial batch approving KB-t2 and KB-p1 separately. Preparation supplied no approval. Historical PREPARED/NOT RUN records are immutable snapshots; later approvals/receipts establish these actual runs.

## Results

| Stage | Result |
|---|---|
| Harmless whole-worker controls | PASS: smoke, timeout, parent death, watchdog death; owned image/workloads removed |
| KiCad startup success | PASS: pinned KiCad 10.0.6, expected exits 0/0, cleanup verified |
| Intentional startup failure | PASS qualification: raw guard exit 1 and container exits 0/1 preserved |
| Deferred oracle unittest | PASS: exactly one test, 2.562 s, no aggregate or duplicate discovery |
| Matched fill/DRC/census command execution | PASS for all three separate variants |
| Complete rail/AGND pad/feed/peer reconciliation | PASS: zero source/native differences on every variant |
| Exhaustive DRC findings | INCOMPLETE: pinned engine per-category reporting caps reached |
| Board/electrical acceptance | FAIL / NOT ACCEPTED: unresolved connectivity and reported DRC findings |
| Production finite reduction/coupled/variant numerics | NOT RUN / NOT ADMITTED |
| Physical source/protection/load/full-path resistance | Unresolved; no manufacturing readiness |

| Variant | Rail/AGND pads | Unresolved source/native pad identities | Complete all-net open edges | DRC-listed unconnected errors | DRC-listed warnings |
|---|---:|---:|---:|---:|---:|
| KA-t2 baseline | 1,568 | 196 / 196 | 479 | 479 | 813 |
| KB-t2 baseline | 2,281 | 486 / 486 | 1,220 | 499 | 815 |
| Separate KB-p1 | 2,281 | 480 / 480 | 1,219 | 499 | 815 |

Pad identities, all-net open edges and listed DRC errors are different quantities. KB-p1 retains six-pad improvement separately; no electrical acceptance follows. Prior KA long-B194 remains source evidence only, with zero newly disconnected identities; it was not substituted for KA196. Parallel/combined/wider-face KA variants remain196 with no new native run.

## DRC limitation diagnosed

Pinned KiCad10.0.6 [DRC engine source](https://gitlab.com/kicad/code/kicad/-/raw/10.0.6/pcbnew/drc/drc_engine.cpp) sets per-category report limits of199, extended to499 for clearance/unconnected items. The implementation stops at those limits. All three reports have exactly199 entries in each of hole-to-hole, library-footprint issues, silk overlap and silk-over-copper. KB's499 listed open errors are demonstrably incomplete against its1220/1219 complete native open-edge census. The813/815 warning figures are **reported findings, not established totals**. Five project-configured ignored checks are preserved and listed in summary.json. `--severity-all` was used; it selects severities, not an unlimited engine report. No cap was bypassed, rule severity changed, pinned tool replaced or board rerun. Full DRC enumeration remains unresolved.

## Integrity and resources

Every variant has three exact phase receipts, six admitted pinned-image containers, matching command/input/source/hook hashes and a verified filled-board chain. Fill ran once; DRC and connectivity read the same saved filled bytes. Matching project/rule sidecars and all550 protected canonical files remained unchanged. All native workers used existing6GiB worker/12GiB aggregate/no-swap guards and the shared heavy queue; all final owned workloads are absent, without cleanup errors. Recorded worker-cgroup peaks: KA1,826,295,808 bytes; KB-t2 1,811,476,480; KB-p1 1,644,081,152. Each board run recorded three successful noninteractive sudo refreshes; no password input/transcript was saved. This proves renewal during these runs, not indefinite runner qualification.

The oracle retained its exact unittest/guard output, admitted ngspice command and exit lifecycle. The unchanged test captures inner ngspice stdout and deletes its temporary deck; no newly measured ngspice-version banner or raw electrical measurement report is claimed. The earlier cloud storage failure and WSL sudo failure remain preserved in their original evidence directories.

## Retention and continuation

index.json binds original bytes/hashes to compressed or verbatim copies of119 original files. Gzip is lossless, with decompressed hashes recorded. Native filled boards and large staged/materialized inputs remain in their original ignored WSL paths, listed by hash; they are not reset or deleted, and no Git LFS is used. The three filled .kicad_pcb hashes are recorded in summary.json. Independent reviewer verified the chains, all pad comparisons, cleanup and cap diagnosis; review.md records the result.

Source checks at the implementation commit remain136 affected tests PASS plus circuit/doc/build/site PASS. This evidence update does not rerun the aggregate suite, independent t2 replay, finite-path coverage or552-omission work. KEEP_K1402_INCUMBENT. Draft PR260 remains unmerged, issue253 open. The next production numerical request must be freshly bound to final HEAD and separately approved as one bounded batch; completed native receipts cannot approve it.

Read-only production-input preparation: all118 retained finite-step ledgers and263 unique input/method/output files match their recorded hashes, with no mismatch, rebuild, pickle load or solve. The completed finite coverage work can therefore be reused unchanged for a fresh baseline reduction/coupling request. Verification took7.31s with about16MiB peak RSS, under the shared guard. Variant operators are not inferred from baseline coverage.
