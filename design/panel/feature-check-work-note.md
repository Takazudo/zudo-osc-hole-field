# Panel feature verification repair

Date: 2026-10-02. Scope: original issue 20's source/board feature checks.
All panel geometry and artwork remain unvalidated drafts.

Two failures were reproduced against the existing checker using temporary
native KiCad boards: a 3 mm optical window passed while the report said 1.6 mm;
a duplicate reference passed with 439 actual footprints while the checker
reported 438 and no extras. Source board bytes were not changed by the probes.

The checker now counts actual footprints as well as unique references. It
checks circular pad dimensions against the source diameter, both mask layers
and no additional layers, and both drill axes for holes. Optical-window
report dimensions come from panel-params.json rather than a 1.6 mm literal.
The optional --params argument supports checking an explicitly supplied
parameter file; invalid/nonpositive/nonfinite diameters fail.

Eight pinned native tests cover the canonical panel, duplicate references,
window and hole-mask dimensions, shape, mask/copper layers, invalid source
diameters and a temporary 1.8 mm source/board pair whose report must say 1.8 mm.
The canonical panel remains 1.6 mm. CI runs these controls separately from
aggregate regeneration. An initial test mutation created a non-drilled slot
and was already rejected by the original type gate; the final hole-mask
mutation instead exercises the newly covered dimension gap.

Before edits, component validation passed (manual inventory 65 lines, no
schematic/placement binding, pin-asset check performed), and guarded baseline
regeneration passed in 309 seconds. The independently checked main changes
through 2bec1d3 were then integrated. Native readback and all eight final
regression tests pass. Final aggregate, ownership, DRC and CI results are
recorded in the PR.

The existing top render and retained R21 reference were opened side by side.
The new title, fixed grid, divider, brackets, labels and headings remain;
reference hardware pictures and review annotations are absent from the
native panel. This patch changes no board, lockfile, hole/window dimension,
parameter, image or owner artwork. The existing visual-review report remains
historical evidence for unchanged render bytes. No fabrication output is
created. Optical performance, installed fit and manufacturing qualification
remain NOT RUN.
