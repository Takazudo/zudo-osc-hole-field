# Verification and limits

The exact release toolchain is task-local KiCad 10.0.6 via
`source /workspace/task-tools/kicad-10.0.6/env.sh` and the repository
`scripts/kicad/run.sh`. Native jobs used
`bash /home/agent/.codex/scripts/heavy-guard.sh --label <label> -- bash <driver>`.
No Docker or KiCad installation was performed. The already-retained official
archive SHA256 is `8c789e36644856cff30a66801692881582b9ca7c7475699494e614ce1bcb1f9c`.
Exact release does not establish bitwise Docker-oracle equivalence; earlier
signature-key retrieval limits remain unresolved.

## Actual attempts

1. `prepare.py` first failed its source identity check because the checker
   compared raw-object hashes with geometry-only hashes. This was a checker bug,
   not a physical or DRC failure. `prepare-first.py`, `translate-first.sh` and
   `translate.log` preserve it locally. The corrected check resolves each exact
   raw hash through the baseline occurrence inventory.
2. `translate-v2.sh` prepared B2, used retained `grid_apply.py`, then ran
   `kicad-cli pcb drc --schematic-parity --refill-zones --save-board --format json
   --severity-all` and complete native connectivity. Process/guard PASS only
   means these commands completed. Native result: **rejected**, 154 DRC errors,
   487 warnings, 117 opens, zero parity differences. Already in the grid-apply
   save, 11 retained objects have wrong nets. They remain wrong after refill.
3. `audit.py` compares every retained occurrence and complete native partitions;
   expected exit1 confirms the 11 relabels and six changed-net partitions. All
   other source identity categories, prepared poses and foreign footprints pass.
   Normal and optimized final audit JSON are byte-identical.
4. `power.py` diagnoses 18/18 connected bypass/supply/return paths on the rejected
   board. This does not accept the board or prove dedicated-route performance.
5. `intended.py` writes a fresh raw diagnostic copy restoring exactly those
   11 baseline net identities, with no geometric edits. Its source audit passes.
   Fills inherited from the invalid board remain unqualified. `native_identity.py`
   rejects immediately after LoadBoard, before connectivity/refill/save: two
   -12V objects become C9c7ace drive and another -12V segment becomes the U3201
   pin12 NC net. The file itself remains unchanged. This confirms the native
   preservation failure independently of a subsequent save.
6. `mapping.py` verifies semantic source mapping, pin owners, all package faces
   and angles, and all 1,160 translated proposal objects. Strict pose equality
   rejects C3208/C3209: each origin and both pads differ from +34mm by +1nm X.
   The other 34 package origins and 111 pads are exact. No tolerance is loosened.
   An intermediate mapping-report path-binding exception is preserved; the
   corrected final run writes and validates the complete bound report. The
   earlier combined diagnostic driver only checked exit codes and is not used
   as evidence that mapping finished; `mapping-final.sh` checks the completed
   report explicitly.

The intended source board SHA256 is
`b745b4e5e844e6233c077bfcdea83602e79308b3ef8e6809418ab75a4886f3a7`.
The rejected native board SHA256 is
`5c9d62d36f155be81bb1668de22ec54ee05dec404b56784f0c3b88a77bbae20e`.
Neither replaces Stage42's accepted disposable board
`975cd15d5ba69b9695e8d32a575a289306a27f1ea17d6b5f7a5819071dc5505b`.

## Source checks and history

75 focused tests pass in normal and optimized Python: 33 Stage41, 8 Stage40,
27 Stage42 and 7 new translation tests. Tests reject absent/collapsed net maps,
unsupported copper and identity collisions between different source objects,
and check exact integer translation with preserved via/track parameters.
All seven historical checkpoint bindings pass normal and optimized Python.
`pnpm check`, `pnpm circuit:check`, Python compilation and whitespace checks pass.
Circuit validation remains manual inventory (68 lines/0 declared placements),
with no schematic/placement binding; pin-asset checks are performed.

Canonical regeneration was not run locally, honoring the explicit prohibition
on changing canonical/manufacturing outputs. Baseline Stage42 CI run39198270859
passed all seven jobs on d006225, including aggregate regeneration and2862 unit
tests. Long historical replay is not duplicated locally; use the repository's
existing exact-head CI budget after the additive Stage43 commit. Terminal status
and exact commit are reported in Issue278 rather than predicted here.

The source manifest binds final scripts, evidence, tests and these documents;
`REVIEW.md` records fresh-context independent review after substantive changes.
Native snapshots/boards and first failures stay ignored locally, with their
hashes and actual command/log bindings retained in `evidence/`.

No physical fit, accessibility, flex-life, current qualification, fabrication,
ordering, energization, release, deployment or merge verification occurred.
