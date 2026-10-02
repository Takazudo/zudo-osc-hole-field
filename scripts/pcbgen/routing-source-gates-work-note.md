# Current-source routing acceptance repair

Scope: issues #23 and #53, after the native connectivity repair from #67 was integrated. This change repairs two independently reproduced false-success paths and refreshes the stale synthetic dense receipt through fresh native execution. It does not route the instrument or close physical/electrical acceptance.

## Reproductions and fix

1. A newly produced DRC object containing only `kicad_version: 10.0.6` previously passed because missing result collections defaulted to empty. Required violation, unconnected-item and schematic-parity collections now must be lists of objects. The fresh native report must also name the actual board and include error, warning and exclusion severity categories. Malformed categories, missing scope, wrong source and invalid violation severities fail closed.
2. A completed board with the same routing-spec digest could retain manually weakened project clearance and minimum-width rules and report UNCHANGED. Source-owned project settings now synchronize before every pre-route DRC, preserving unrelated project fields and board copper. A repaired project reports UPDATED; a subsequent byte-identical run reports UNCHANGED. Prepared rules/parity, post-route DRC and fresh native connectivity gates remain mandatory.

Focused mocked regressions reproduce both failures. The pinned native dense replay additionally weakens an actual disposable project and checks repair before DRC, exact copper preservation, native zero-open-edge status, and subsequent idempotence. Final native connectivity is checked again after canonical serialization so the receipt hashes the retained board's exact bytes.

## Evidence and execution boundary

Baseline component validation and guarded aggregate regeneration passed; baseline regeneration changed no tracked file. Thirty-nine focused Python tests passed, including wrapper dispatch tests. Fresh guarded dense replay plus bounded one/four/six/timeout native routing checks passed in 127 seconds. Actual KiCad 10.0.6 emitted the expected source basename and all three severity names. Dense results: 0 rule errors, 0 schematic-parity issues, 0 DRC unconnected items, 0 native open edges and 159 unsuppressed warnings. Details and hashes are retained in `fixtures/dense-evidence/verification.json`; the historical failed routing attempts remain separate.

The dense board definition had changed from domain J to JL since its old receipt. Retained evidence was replaced only after the current-source native replay passed. Existing fixed centres, routes, copper sources and design-rule targets were not relaxed. No exact-component facts, protection boundaries or board ownership are changed.

GitHub-hosted CI runs the deterministic dense replay directly; local/shared and self-hosted runs retain the mandatory machine-wide guard. Both GitHub environment identifiers are required and tested. The quick heuristic experiment remains a separate local check; the CI replay does not invoke Freerouting.

Post-change aggregate regeneration and documentation/site checks are tracked in the PR. All physical, electrical, mechanical, thermal and fabrication qualification remains NOT RUN: the fixture and instrument are unvalidated drafts.
