# Terminal core reconciliation — rejected, not adopted

Run 37984573591 at a89ff33adc26675b7cdf2f22616dcb1a9826cb59 finished with workflow success but adoption false. Bot ff6faebab30c5fbb97682ce0cd62569d3b1d9843 changed only two routing receipts, no PCB. The native zone subprocess exited 137; its cause is not established.

Artifact 11650664778 is 724,422,573 bytes, SHA256 b5c112a5c9336a27cb08369ec42a11b7cc51a39bb569215d24075ccd3ab11567. Read-only export 38006210148 split that exact ZIP into three downloadable parts. `download.json` pins their IDs, hashes and reassembly; `reassemble.py` verifies every part and the original archive.

`reconcile.py` independently checks source, replay, native reports, fresh membership, copper multisets, all 217 completed zone fixtures and their native geometry/context. The guarded reconciliation passed in 104 seconds. The first attempt failed on a tuple accessor in the reconciliation script; correcting that accessor produced the passing run without changing any assertion or board.

The candidate has 1,402 versus 1,441 open edges, zero DRC/parity errors and no splits. All 133,169 prior copper objects remain, with 344 segments and 38 vias added and no removals. Fresh board bytes agree. All 3,807 nonrouting objects remain unchanged. The raw warning gate rejects a surfaced hole pair; complete warning evidence remains mandatory.

Only first-zone stage 0 (144 fixtures) and 73 of stage 1 completed. Full zone coverage is false. Completed hole and added-copper silk sections are extracted with per-file hashes in `reconciled.json`; incomplete zone fixtures remain preserved in the original ZIP. These facts do not authorize adoption.

Replay the independent read-only verification from repository root, using the supported numerical Python environment and heavy guard:

```sh
bash "$HOME/.codex/scripts/heavy-guard.sh" -- PYTHON \
  circuit/routing/issue189/core-complete-terminal/reconcile.py \
  VERIFIED_ORIGINAL_ZIP NEW_EXTRACTION_DIRECTORY OUTPUT_JSON
```

The destination must not exist. Preserve the exact archive and successful canonical copper. Continue the separately running full paired zone audit 38005209241; independently reconcile its complete artifact before testing combined warning eligibility. Do not treat timing samples or detection controls as complete coverage. Issue #189 remains open; canonical JL/JR/core remain 118/134/1441.
