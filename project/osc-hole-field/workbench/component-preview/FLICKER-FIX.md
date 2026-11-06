# Panel artwork flicker correction

Owner-reported visual bug against `b81d0a19f18168a4da9578ef2d155b809ec40cd4`.

## Reference and reproduction

Library `libfile_5d9e87bfb88c819193c4d82573b11bcb` was materialized through the supported Library transfer into this executor, validated as a readable PNG and inspected. Resolved filename `ss-2026-10-19-005243.png`, 2,206,942 bytes, SHA256 `42a1dabfd89b8474d697981f5de275935ebb27742ea9f8da0444f740df996fe5`. The owner's screenshot remains local; it is not redistributed in the repository. The retained b81d0a19 orbit screenshot independently reproduces the visible panel stripes. The earlier visual review missed these artifacts.

The old renderer had both the extruded panel front at z=0 and a full artwork plane at z=0.02 mm. With a 24-bit depth buffer, near=0.1 mm and far=3000 mm, that separation was insufficient at normal orbit distances. This was depth-buffer interference between the two display surfaces, not a changed component model, bad normals or an animation loop. Rendering was already on demand.

Controlled probe: fixed camera target, camera positions `(329,250,390)` through `(331,250,390)` mm in 0.5 mm increments, six blank artwork points `(x,138,0)` with x=−50,−25,0,25,50,75. Before correction the unchanged dark artwork samples alternated between RGB `(16,18,17)` and underlying panel colors as bright as `(34,44,44)`. After correction all 30 samples remain `(16,18,17,255)` RGBA. Actual depth precision reported by WebGL: 24 bits.

[Before screenshot](flicker-evidence/before.png) · [After screenshot](flicker-evidence/after.png) · [Before samples](flicker-evidence/before.json) · [After samples](flicker-evidence/after.json).

## Correction

Artwork is now the material on the existing front triangles. There is no second artwork mesh, no arbitrary extra separation, no depth-test disabling and no polygon-offset workaround. Front UVs are `(x+159)/318, (y+149)/298`; front triangles are the original extrusion cap at local z=2, translated to world z=0. Back and walls retain their original material. The 438 actual aperture holes, panel vertices, component positions, source model bytes, attribution and seating assumptions are unchanged. Selection still raycasts the actual aperture-bearing panel.

Independent review checked byte-identical panel vertex positions, complete group coverage, 11,390 front triangles and 32,422 back/wall triangles, UV orientation, and refreshed orbit screenshot. Final disposition and reviewed hashes are recorded in FLICKER-REVIEW.md.

## Regression and first failure

The browser test instruments the exact bundled viewer bytes only in memory. It samples actual WebGL framebuffer colors at ten camera poses, covering small rotations, opposite orbit, front and zoom distances; it also checks one panel mesh, actual repeated mouse drag/wheel interactions, idle frame stability, existing front/back/detail views, toggles, electrical identities, selection/occlusion and all locked feature coordinates. The color tolerance is one 8-bit channel value, not a physical geometry tolerance.

First new browser suite: 4 tests, 1 failure, 64.478 s. The closest test camera put a sample outside the viewport; readPixels returned zero. Corrected the fixture to a visible zoom pose and added an explicit viewport-bounds assertion. No color or geometry criterion was relaxed.

Reproduce the controlled comparison through the heavy guard:

```
python project/osc-hole-field/workbench/component-preview/probe_flicker.py --before --output-dir /tmp/osc-flicker-before
python project/osc-hole-field/workbench/component-preview/probe_flicker.py --output-dir /tmp/osc-flicker-after
```

The before probe reads exact b81d0a19 files using git show; current source/model data are not modified. Original before/after diagnostic captures completed, 28/29 s; these scripts collect evidence rather than assert a pass/fail result. Guarded full browser tests are run in normal and optimized Python. Focused source tests (7) pass in normal and optimized Python; `pnpm check`, pre-edit `pnpm circuit:check`, and deterministic bundles pass. Final execution totals are recorded below after completion.

This browser fix does not qualify physical seating, service access, manufacturing fit or optional cap hardware. No native manufacturing outputs are changed.

## Final local execution

- Full browser suite: 4 PASS, normal93.661s and optimized107.946s; both heavy-guard verdicts PASS.
- Focused source suite: 7 PASS normal5.988s / optimized4.453s.
- `pnpm check`, `pnpm circuit:check`, deterministic HTML/receipt checks and diff check PASS. Manual inventory scope remains68lines with no schematic/placement binding.
- All7 historical checkpoint bindings PASS; no historical assertions/evidence changed.
- Refreshed front/orbit/pot-detail screenshots; back rendering is byte-identical. Independent final review has no blockers.
- CI results are reported against exact pushed heads in Issue278; no claim that local WebGL checks replace physical or native qualification.
