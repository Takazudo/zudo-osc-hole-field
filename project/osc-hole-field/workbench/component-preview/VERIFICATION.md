# Source/browser verification — 2026-10-18

Scope: owner-authorized pot appearance correction and current-panel browser 3D preview after green CI checkpoint `49cb773954a24439f0fd302f5937c5a1a9aca013`. No physical architecture is adopted. Parent PR #286 and all historical stages remain untouched.

## First failures and corrections

- Initial 3D browser run: 2 tests, 1 failure, 141.292 s; heavy guard `verdict=FAIL`. Test converted scene coordinates back to panel coordinates and compared `20.650000000000006` with `20.65`. The correction compares actual scene coordinates directly with the same forward transform of locked coordinates, exactly; no dimensional tolerance was relaxed. Original placement values remain separately checked.
- Independent review detected a determinant −1 pot transform, reversing source signed volume +936.9043035 mm³ and normals. Corrected to the documented determinant +1 rigid transform. A source regression verifies source/derived signed volumes and pins both runtime transforms.
- Review then detected selection through an opaque panel. Added nearest visible panel-surface occlusion, using the extruded panel with actual aperture holes. Browser regression now clicks a visible pot, confirms a different hidden body is not selected through panel, and confirms the same click selects it with the panel hidden.
- Initial continuous rendering made software WebGL unnecessarily busy. Rendering now occurs on camera, visibility and texture changes. Final three-test browser suite completes in about 23 s.
- Uppercase PTV09 PDF download initially returned HTTP403. The public manufacturer lowercase URL linked from the model contribution succeeded; inspected bytes match retained SHA256. No access restriction was bypassed.

## Actual commands and results

Browser commands use this prefix (normal and optimized commands run separately):

```
HEAVY_GUARD_DIR=/workspace/shared/.agent-guard/heavy bash /workspace/codex-settings/.portable-profile-home/.codex/scripts/heavy-guard.sh --label <label> -- <command>
```

| Command | Result |
| --- | --- |
| `python project/osc-hole-field/workbench/component-preview/tessellate.py` | Imported both original STEP files using CadQuery2.7.0/OCP7.8.1.1; pot7870/jack9542 triangles; source/derivative hashes retained |
| `python project/osc-hole-field/workbench/component-preview/build.py --check` | PASS deterministic standalone HTML and receipt binding |
| `node project/osc-hole-field/workbench/current-editor/build.cjs --check` | PASS deterministic editor |
| `python -m unittest scripts.panel.test_component_preview scripts.panel.test_current_audit` | 7 PASS |
| Same unit command with `python -O` | 7 PASS |
| `python project/osc-hole-field/workbench/component-preview/test_browser.py` | Final 3 PASS,22.967s; guard PASS |
| Same browser command with `python -O` | Final 3 PASS,22.082s; guard PASS |
| `python project/osc-hole-field/workbench/current-editor/test_browser.py` | 7 PASS,11.688s; guard PASS |
| Same editor command with `python -O` | 7 PASS,11.397s; guard PASS |
| `python -m unittest discover -s scripts/checks -p test_architecture_history.py` | 12 PASS (negative controls deliberately emit missing-revision failures) |
| Same history-adapter command with `python -O` | 12 PASS |
| `verify_binding(Path.cwd(), commit, modules)` for all `CHECKPOINTS` | 7 immutable checkpoints / 8 retained modules PASS; historical assertions not replayed locally |
| `COREPACK_HOME=/workspace/shared/corepack corepack pnpm check` | PASS evidence, generated drift,31 model/footprint previews and doc TypeScript |
| `COREPACK_HOME=/workspace/shared/corepack corepack pnpm circuit:check` | PASS before edits and after; manual inventory68lines, no schematic/placement binding; pin-asset check performed |
| `git diff --check` | PASS |

Chromium performs actual offline WebGL rendering, not a mocked canvas. Browser checks assert438 feature identities and exact scene positions, current51/48/2 electrical pot selections, model rendering, caps, visibility, real canvas selection/occlusion, zero page errors and no HTTP requests. The editor additionally covers preserved silk behavior, presets, SVG/PNG exports and fixed apertures. Front/back/orbit/pot-detail screenshots were inspected; editor screenshots were refreshed after the authorized capless correction.

Source tests are discovered by the existing scripts runner; browser suites under project/ must be invoked explicitly. The prior exact-head all-green CI receipt remains at Issue278 comment6251697090. That result applies to49cb773, not automatically to this new change. Full historical suites and native KiCad checks were not rerun locally for this appearance-only task. No regeneration, ERC/DRC, physical measurements, energization, fabrication, ordering, deployment or merge was performed locally.

## Review

Independent agent `/root/browser_ci_review` reviewed the source, provenance/receipt binding and updated front/back/detail screenshots. The two findings above were fixed and followed by review of the final substantive change. See REVIEW.md for the final disposition. Independent review is source/browser review, not engineering qualification.
