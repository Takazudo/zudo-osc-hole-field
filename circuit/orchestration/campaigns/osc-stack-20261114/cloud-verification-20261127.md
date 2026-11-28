# Cloud verification and inherited-failure repairs (2026-11-27)

Manager: Claude Code Cloud Project thread (Opus 5.5), single manager for #362. Base: `wsl/s10-review-continuation`
at `80569b5375087df519b79ead67d1bf56c16301e6` (full history fetched). Container: 4 CPU, 15 GiB, no swap; one heavy
process at a time, each under a `timeout` deadline. KiCad oracle: pinned image
`kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec` through `scripts/kicad/run.sh`,
`kicad-cli version` 10.0.6. Python 3.12 with the repository-pinned NumPy 2.2.6, SciPy 1.15.3, Shapely 2.1.2,
Playwright 1.62.0; matplotlib 3.9.2 in a separate venv for the wavefolder plots.

## The post-edit aggregate passes

`bash scripts/checks/regen-all.sh --check` at `80569b53` (same generator source as `4c0ec4aa`): exit 0 in 313 s, zero drift.
After the repairs below it passes again (exit 0, 307 s). `pnpm circuit:check` passes before and after. The interrupted
WSL runner bytes were not needed.

## Inherited failures repaired from current sources

| Area | Cause found | Repair | Verdict change |
| --- | --- | --- | --- |
| D4309 | MC04-S7 moved the whole E3 U4347 block, D4309 included, to K (`k-block-relocation.json`); the S6 test still required a JR eviction | The test checks the accepted relocation (released by the K block move, on its IC's board and face) and keeps the S6 assertion for a non-relocated case | none |
| Sub-toggle | `inputs_sha256_at_launch` hashed live files | Hashes are read from git at `78246cf0`; the Dailywell facts are read at `59d7e03b` (EV-01 ranges), the bytes the 21793ba3 refresh recorded. `spec.json` unchanged | none |
| Power posts | Partition and stack candidate changed under S5/S7 | `present_gh_bounds` (JL 100→108, JR 106→118 contacts; 0.4818→0.4772 and 0.4783→0.4717 A) and `header_agnd_positions` (JL 54→58, JR 54→60, same counting rule reproduces 54/54 at `c9d5761c`) re-read; every other cited term equals its source; pins refreshed with a `source_refreshes` entry | all "exceeds/meets" words unchanged |
| Thermal | Ledger gained six OPA4197IPWR rows (362→368) in MC04-S5 | `extract_inputs.py` re-extracted; README re-rendered; plan heat row follows (34.83→35.43 W; P 58.7–75.6 °C at 40 mm; K parts 68.8–95.1 °C) | none: pots EXCEEDED ON PAPER, 85 °C parts NOT SHOWN |
| Mechanics | Geometry predates JL-K-26/27 and JR-K-28..30 | `--refresh-geometry` and `--write-readme`; 197→202 rigid pairs, 777→807 K positions; DA-01's 825 kept as its own row; three pins refreshed | all pass/miss words unchanged |
| Envelope / wavefolder SPICE | Receipts pinned `io_partition.py` before MC04-S7 | Re-run through the pinned oracle's ngspice; results byte-identical except the source hash; plots re-rendered | none |
| Protection audit | `protection58-audit.json` drifted after MC04-S5 (required continuous 1.6→1.7 A) | Regenerated; `--check` PASS (consistency only); `--require-closed` still exits 1: "no topology selected" | gate stays BLOCKED (#59) |

## Remaining current-suite failures (integration holds)

`run-python-tests.sh current` stops in `scripts/checks/`: 51 failing cases after the repairs, against 78 at `80569b53`.
Every remaining case also fails at `80569b53`; none is new. They are the board/checkpoint successor receipts for the
K/JL/JR boards changed by MC04-S7 (`metadata_successor`, `osc_pcb_checkpoint`, adoption records), and the
`family_reuse` / `mult_common_board` proposals pinned to the pre-S7 partition. They need native evidence or a reviewed
disposition before any PR carries this source. No assertion was removed or marked expected.

## S10 Revision 2 packet

`mc04-s10-revision-2-decision-packet-20261127.md` (packet revision 3, SHA-256 `c918b815…6504` before path
localisation), design session Fable 5.2 (`claude-fable-5-2`, Agent tool model override; identity self-reported).
Independent review by a separate Fable 5.2 session: RETURN, then ACCEPT WITH CORRECTIONS, corrections applied
(`reviews/mc04-s10-revision-2-packet-review-20261127.md`). Scripts: `scripts/stack/studies/mc04_s10_r2_packet/`.
Design-authority rulings with owner notified: coordinate equality for R5257/U5210/R5259; no slot-only placement within
24 mm spares the protected passives. The owner choice among the four options is pending.
