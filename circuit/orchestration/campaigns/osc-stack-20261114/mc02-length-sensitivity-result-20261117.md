# MC02 conditional 51 mm length sensitivity

2026-11-17, x0x WSL. DS-137 executed once on implementation
`c0e09dfe0bc7256e1e6b20224eba7236497db2f9`, using unchanged engineering inputs
`2c53715d49a4a7639723595590d1fd4eeb3a3c1f`. This is a conditional calculation in
the retained electrical model, not Molex product qualification or a cable change.

## Controlled experiment

First reproduced the retained baseline: all61 detailed pair maxima/witnesses/counts
and complete mixed branch ground-share results matched at retained serialization
precision. Only copied lengths on the28C29534 links changed from50to51mm.
The existing pair kernel recomputed those links; the ground kernel recomputed all61
mixed-length paths. Five intentional STATIC/WIPER nulls remained, giving56numeric
ratios. All other material, end-equivalent, drive, impedance, position, ordering,
ground and source parameters stayed fixed. No automatic remedy search was called.

Eight independent fixture tests passed before execution. Source pinning covers13
actual input/kernel files, including power-post joint data and numerical helpers.
The implementation refuses baseline mismatch, a different override set, changed
null classification, source drift or mutation of frozen inputs.

## Result

| Quantity | Original model | Only28C29534 lengths at51mm |
| --- | ---: | ---: |
| Largest ratio among changed links |0.9308620676691287|0.946375540163643|
| Largest ratio over all links |0.9781012674297533|0.9781012674297533|
| Numeric ratios above1 |0|0|
| JL all-posts-open worst contact,A |0.08958060364319424|0.0895976215253899|
| P all-posts-open worst contact,A |0.09977720424463946|0.09999353251637606|
| JR all-posts-open worst contact,A |0.11625222178122142|0.11625222178122142|

The retained model therefore does not reject this isolated1mm increase on the
specified28links by its pair-ratio or retained ground-current screens. The largest
global ground figure remains JR, not P. Output also retains normal and one-post-open
cases; the table is not a replacement for that complete receipt.

This does not establish that150200075 has the retained dielectric, conductor,
contact resistance, end-equivalent dimensions or tolerance limits. It does not
prove the cable fits a slot/fold, allows latch access, has the correct contact-1
mapping or supplies a complete replacement for the five selected configurations.
Unknown product evidence cannot be filled by this conditional computation.

## Execution and evidence

Run ID `fa393cc34efc46329397530db765c5d3`; exit0;3.181seconds; cleanup VERIFIED.
Worker verified numerical venv, actual canonical shared-lock exclusion,1CPU,
1GiB RAM,zero swap,128PIDs,whole-unit OOM termination and480second service cap.
External controller had a540second TERM/600second KILL ceiling and survived the
worker lifetime independently. The shared guard ran inside the capped service.
No tracked drift, native tool, DRC, zone fill, adoption or manufacturing action.

Result SHA-256:
`8768bb1cb657069d9d136a5ee1f555f8d1ffcffe6a184602c60b2107859e9472`.
Runner SHA-256:
`a0f6e033100922604fbbb24b07bc5ada5046d11d833d693338863bea16d84315`.
The13 lifecycle fixtures and one no-study control preflight passed before actual
execution. Raw logs, result, runner bytes and control/cleanup receipts are retained
in ignored `.circuit-cache/osc-coordinator/20261117/mc02-length/`.
Archive index SHA-256:
`af47729dffcccb4d2daf628116fc6230d45a309e2f8f4d6236635c0762eb8b61`.

Independent `candidate_paper_ruling` audit confirmed result hash,13input pins,
28overrides,33unchanged pair rows,56numeric/5null outcomes and all branch currents.
Live unit/cgroup absence and released canonical lock were separately checked.
No unchanged rerun or wider sweep follows from this result. Source dimensional
and material gaps remain distinct from the now-measured conditional model margin.
