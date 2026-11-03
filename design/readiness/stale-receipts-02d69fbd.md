# Receipts left stale by main 02d69fbd (G06 confirmation, 2026-10-27)

**Not rebound.** This list is for the user's policy review. Nothing here changes a receipt.

## What 02d69fbd changed

| Input | Old sha256 → new sha256 | Content change |
| --- | --- | --- |
| `design/spec/modules/filter.py` | `9d8d71be…cfed0c` → `a558a912…dc62f` | Module docstring only: the "owner confirmation remains open" line becomes "user-confirmed 2026-10-27; see E10". No code, part, value or net changes |
| `project/osc-hole-field/block-contracts.json` | `fe6a8260…c0a9` → `ebcad1c6…c6b1` | Three G06 `engineering_to_finish` strings: "decide whether GAIN scales LP/BP/HP" becomes "confirmed E10: GAIN affects dry OUT only…" |
| `project/osc-hole-field/electrical-decisions.json` | `5f7bfab1…` → `a07d89a4…` | Adds decision E10 |
| `project/osc-hole-field/open-issues.json` | `e52818bc…` → `b280c40e…` | G06 `resolution_required` text |
| `design/spec/modules/filter-work-note.md`, `doc/.../osc-block-vcf.mdx` | — | Narrative only. No receipt binds them, apart from the history checkpoint |

## Receipts that a test checks (these fail now)

| Receipt / check | Bound input | Does the change affect what it asserts? |
| --- | --- | --- |
| `design/architecture-278/implementation/stage37/family-reuse/proposal.json` (`scripts/checks/test_family_reuse.py` determinism) | filter.py | **No.** The proposal is derived from the filter family structure, which a docstring cannot change. Only the embedded source hash differs |
| `design/architecture-278/implementation/stage54/power-cleanup/sources.json` (`test_cleanup.py` `test_source_bindings`) | filter.py | **No.** It is a power-cleanup bypass study, and the filter circuit is unchanged |
| `design/architecture-278/implementation/stage36/whole-layout-review/view-data.json` (`test_source.py`) | block-contracts.json | **No** for the review content. `view-data.json` and the HTML contain neither the old nor the new G06 text |
| `design/architecture-278/source-ledger.json` (`scripts/architecture278/ledger.py`, `test_ledger.test_complete_counts`, "protected source drift") | block-contracts.json, pinned to base `65cefd41` | **Yes, for the G06 row text only.** The ledger embeds the superseded "decide whether GAIN scales LP/BP/HP" text. Counts (33 contracts, 438 centres) are unaffected. The ledger deliberately freezes its sources at the base, so this is a policy question, not drift to fix |
| `scripts/checks/architecture_history.py` retained checkpoint | All six inputs above, plus every owner bundle, generated page and report changed since the checkpoint (phases 6–11 fact promotions, monitor reports) | Mixed. 02d69fbd contributes 6 of the listed files, and the rest come from later branch work. The gate asserts byte identity of the checkpoint, not circuit behaviour |

## Receipts that bind the old hashes but no current check runs

Some stage reports bind the old filter.py hash: stage3-crossing-audit, stage4 power-inventory, stage6 hosting, stage7 electrical and mechanical, stage8 currents and electrical, stage10 inventory, stage38/39/40 mult studies, and `interface-contract.json`. These are historical stage records. The change is a docstring, so none of their electrical or mechanical assertions is affected.

- `design/architecture-278/linked-sources.json` binds the old block-contracts.json hash. It holds no G06 text, so it is not affected.
- `design/panel/current-audit/audit.json` binds both old hashes. It is a panel current audit, so it is not affected, and no run gate rehashes it.
- `stage12/criteria-history.json` binds the old electrical-decisions.json hash, before E10. It is history by design.

## Pristine manifests (do not rebind)

- `project/osc-hole-field/handoff/SHA256SUMS.json`
- `pristine-SHA256SUMS.json`
- `_temp-resource/.../handoff-r21/.../SHA256SUMS.json`
- `project/osc-hole-field-import-log/20260927T194517802338Z/receipt.json`

These record the imported R21 handoff bytes. Their purpose is to keep the pre-change hash.

## Policy options (user)

1. Rebind the four test-checked receipts whose assertions are unaffected: stage37, stage54, stage36 whole-layout-review and the history checkpoint. Record that the change was docstring/text only.
2. For `source-ledger.json`, either keep the base `65cefd41` freeze and mark the G06 text as superseded by E10, or move its base past 02d69fbd.
3. Leave the historical stage reports and pristine manifests unchanged.
