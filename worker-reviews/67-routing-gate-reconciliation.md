# PR 67 routing-gate reconciliation — 2026-09-30

## Requested result and recovered state

Continue the ChatGPT review handoff from `zudo-osc-hole-field-review-20260930.zip`,
verified against every archive SHA-256 and the four Git blobs in PR 67 commit
`791d92d378fdded74a327c23924ce83ed9ff36d6` (reviewed main
`fac99297702eabd97bbc3fae58876af4017fcaea`). Reconcile into the preserved
`topic/38-jack-halves` worktree, whose initial HEAD was
`c0782a9d8313d7ea5277ad9726e14e40133c8b57`, with 633 modified/untracked files.
No exact component identity, panel coordinate or circuit source is changed by
this routing repair. The existing evidence inventory has 49 manual lines and
zero declared placements; schematic/placement binding is not performed, while
the pin-asset check is performed.

Baseline evidence check passed. Guarded aggregate regeneration passed in 183 s,
including ten native board ERC checks (zero errors, 673 retained warnings) and
438/438 fixed centres. Only the ten schematic-tree hashes in the existing ERC
report changed relative to the incoming worktree; commit `43c47a9` preserves
that generated refresh before task edits.

## Reconciliation

The issue-38 branch already adds complete native per-net cluster counts and an
optional ignored-class router argument. A three-way source merge retained both;
no whole-file replacement of newer local behavior or dirty-worktree cherry-pick
was used. The reconciled gate requires clean DRC/parity and fresh same-board
native zero, stops prepared rule/parity failures before routing, preserves
failure/timeout exits, and marks refresh-only output as diagnostic.

The native v2 receipt's board hash, named-net count and sum of positive integer
per-net edges are checked before publishing native result fields. A failed
refresh removes old native names/counts. Original DRC name samples remain
separate from complete native names. Mocked fixtures now model that existing
v2 receipt rather than dropping the issue-38 additions. Native fixture assertions
also require a matching board hash and zero native edges.

## Interrupted K calculation

No old solver process, final result/profile or terminal guard verdict was found.
The original checkpoint directory has 188 contiguous payload/manifest pairs,
ending at 1,504 of 2,287 current profiles. Every payload digest matches. Storage
admission also passes the stored numerical receipt/shape checks under run key
`7d21a6bc0c3128f9b6e682f127854811994646255662f6511ab88903832f27b3`.
Current native-source admission still finds 2,288 contacts and 82 matching source
hashes. All 102 dependencies in retained full preflight v3 remain unchanged.
These are recovery checks, not a completed calculation or a reassembled operand
check. A resume must reconstruct the same source/profile/library/operand key and
pass the original final matrix gates. Never rebind historical result hashes.

## Validation and remaining work

Validation is in progress. The 35 routing orchestration/unit tests, evidence
validation and `pnpm check` pass. Guarded aggregate check mode and actual JL/JR native diagnostics passed in 384 s.
Fresh canonical results (board bytes unchanged):

| Board | SHA-256 | Native open edges / nets | Rule / parity errors | Warnings | Open +12 / -12 / +5 edges |
| --- | --- | --- | --- | --- | --- |
| JL | `b0d3fc3e127a7f761c66e0324446c0826cdcc51ed0328c0ce829703c7d08695e` | 1400 / 645 | 0 / 0 | 548 | 135 / 143 / 59 |
| JR | `7ae9771554337af003432133b10a84f5206ac25cc865eb9699a47a4f3c02ac73` | 1439 / 645 | 0 / 0 | 526 | 139 / 132 / 59 |

Both have zero AGND open edges. Their DRC JSON each lists only 499 unconnected
items; complete native counts are authoritative. Diagnostic refresh returned
exit 2 / INCOMPLETE DRAFT for both. Reports are retained locally under
`.circuit-cache/review-20260930/`.
The first native routing fixture queue timed out with exit 75 after 1800 s;
no fixture ran in that attempt. The guarded routing retry passed in 153 s (minimum available memory 6572 MB).
Two-layer, four-layer and replicated fixtures had zero native/DRC/parity errors,
matching board hashes, preserved copper and unchanged reruns. The intentional
barrier retained TIMEOUT DRAFT / exit 3 with seven native open edges. Native
prerequisite regressions remain queued. Contention is not a test failure or a pass. The first full
suite launch used default Python without numerical packages and was stopped;
its replacement uses the existing environment with numpy 2.2.6, scipy 1.15.3 and
shapely 2.1.2, matching the repository pins.

The full pinned suite exposed six inherited discovery/expectation failures.
Four `test_*_native.py` files are standalone executables, not unittest cases;
their bytes were preserved under `*_native_regression.py` names and the new
`test_native_prerequisites.sh` executes all four through KiCad in fresh retained
fixture directories. This avoids importing pcbnew in the numerical Python
runtime without dropping native assertions. The peripheral refusal test now
expects the current missing-native-prerequisite message while still requiring
refusal before extraction/output. The coupling-screen authority test recomputes
current v7 native admission rather than asserting that a stale historical v6
solver prerequisite remains valid; wrong-board/export/failed-receipt mutations
remain tested. Those nine focused tests pass. No historical matrix or receipt
hash was rebound. The fresh complete Python run passed all 461 tests.

Issue 38 remains open: canonical power/ground selection, supported physical
contact/current model definition, matching complete operators and joined
common/current/rail/distribution/total-voltage bounds are not established.
Signal routing follows those prerequisites and its bounded-attempt contract.
Dependencies 39–45 are not completed by this repair. Physical checks remain
NOT RUN under 55/57/64/65; exact protection remains OPEN under 59. All schematic
and PCB artifacts remain unvalidated drafts. No fabrication outputs, supplier
contact, deployment or Cloudflare credential operations were performed.
