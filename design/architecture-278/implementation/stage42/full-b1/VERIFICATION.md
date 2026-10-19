# Stage42 verification boundary

Starting draft287 head: `b133738065e8c013dbdc0a3a8afde6bff68d43d9`.
Parent286 remains `b58068fbaeb65886958a67a4f4978613414e31c5`.
Canonical board SHA256: `e984c0a01156b5f282f0c849077c61572df30ee0c70dfe6c9db94fbfcfe52107`.
Accepted Stage41 board SHA256: `9fbdb51c891ee21abfe0c4242baf5b789aee05fd1a7403464d2ddd54aec4fcef`.
Both are preserved byte-for-byte.

The first full-B1 final candidate is `975cd15d5ba69b9695e8d32a575a289306a27f1ea17d6b5f7a5819071dc5505b`.
Repeated/fresh acceptance is recorded in `evidence/settlement.json`; no DRC process exit code substitutes for those parsed gates.

## Source checks

68 focused tests pass in normal Python and68 in optimized Python, including33 retained Stage41 tests,8 retained Stage40 tests and27 new Stage42 tests. All7 historical checkpoint bindings pass normal/optimized. Scope and copper metrics reproduce byte-identically normal/optimized; scope also equals the committed evidence. Commands and log hashes are recorded in `evidence/commands.json`.

`pnpm circuit:check` and `pnpm check` pass. Circuit validation remains manual68line inventory/0declared placements: schematic/placement binding is not performed; pin-asset check is performed. Full historical replay and aggregate regeneration are left to the existing exact-head CI budget, not duplicated locally. The Issue278 report records terminal CI status for the pushed SHA separately.

## Native and physical distinction

Exact-release KiCad10.0.6 ran on disposable copies under the shared heavy guard. Full raw occurrence identity, prepared/foreign footprint structure, all retained connectivity partitions, exact24 target-net closure and18 power paths are separate mandatory checks. All6 IC-to-bypass links and12 native plane connections are checked.

The117 baseline native open edges remain:103 foreign-net entries and14 sharedAGND entries, with no direct B1 endpoint. The14 other AGND components contain foreign pads and are real board-level defects. Zero error-level entries in the rule-violation list and zero schematic-parity issues do not constitute a full-board DRC pass. Both silk categories reach199; exhaustive nonregression remains unresolved. No project threshold, severity or reporting cap was changed.

First failures remain in `evidence/native-attempts.json` and the ignored `.circuit-cache/stage42*` directories:6 initial clearances; subsequent courtyard/clearance failures; rejected incomplete raster trials; rear-pad verifier API correction;10 old dangling supply leaves; and the shared+5via warning revealed by cleanup. These were not erased or relabeled as passing.

No physical qualification was performed. Required mock-up inputs and reject criteria are in README.md. No canonical adoption, B2 replication, energization, fabrication, ordering, release, deployment or merge occurred.

## Completed repeated/fresh result

Three equal complete native memberships and one separately copied/reloaded/refilled fresh candidate pass every settlement gate at the exact candidate hash above. Normal and optimized settlement outputs are byte-identical. Each pass reports476 warning entries (including both capped199 silk categories),117 pre-existing unconnected items and0parity. No new uncapped warning identities occur; the sole removed uncapped warning belongs to an explicitly retired private track. See the bound receipts for exact counts and hashes.
