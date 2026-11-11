# Warning-shard fixture triple

Disposable boards for the sharded complete-warning audit (`scripts/pcbgen/warning_shards.py`). They are not a design board and prove nothing about any product PCB.

- `before/` has two segments, silkscreen text and a line, and one footprint with a silk reference and an SMD pad.
- `after-clean/` adds 70 segments and 10 untented vias, all clear of silkscreen. That is 80 added objects, so 32-fixture shards are 32/32/16.
- `after-planted/` adds one more untented via centred on the F.SilkS line. Native DRC reports it as `silk_over_copper`, the positive control.

`python3 scripts/pcbgen/fixtures/warning-shards/build.py` regenerates the nine board files and `manifest.json` deterministically; `--check` verifies the committed bytes. Do not hand-edit them.

The native controls run on the pinned image through `scripts/kicad/run.sh`, one process at a time:

12. Clean pair: compare the monolithic silk audit with 32/32/rest shards assembled by `warning_shards.py`, sharing one holes/zones run. `silk/result.json` must be identical after dropping `report_sha256`. Every fixture `drc.json` must be identical after dropping `date`. `proof.json` may differ only in the silk entry of `audit_result_sha256`.
13. Planted pair: both arms must report the same non-empty `new_mask_identities` and end in `new complete native silk warning identities`.
14. Capped fixture: a via under 200 silkscreen lines must fail its shard at the 199-row report cap.

`native-controls-receipt.json`, when present, records their outcome for one tool commit and image digest. Without it, controls 12-14 are NOT RUN.

The receipt covers only the tool bytes it names in `results.clean.receipt.tool_files`, and `test_warning_shards` checks that they equal `warning_shards.tool_files()`. Any change to a `TOOL_FILES` member, or to the pinned image, makes controls 12-14 NOT RUN until they are executed again and a new receipt is committed. The receipt bytes are never edited by hand.

Control 14's capped input is not committed. The control script derives it from the staged copy of `before/warning-shards.kicad_pcb`:

- It inserts 200 `gr_line` items on `F.SilkS` immediately before the board's `(embedded_fonts` line. Item k = 0..199 runs from (139.7 + 0.003k, 74.5) to (139.7 + 0.003k, 75.5) mm, with x formatted to three decimals, stroke width 0.1 mm and `(type default)`. Its UUID is uuid5(`0d3c8e7a-91b2-4c55-8d2e-7a1f4b6c9e01`, `cap-line-<k>`).
- The capped before board is that text. The capped after board adds, at the same place, one via at (140, 75) with size 0.6, drill 0.3, layers F.Cu/B.Cu, net GND and UUID uuid5(same namespace, `cap-via`).
- Both boards use the fixture's `.kicad_pro` and `.kicad_dru`. The control runs `warning_shards.py run-unit … --unit silk:0:1` and expects the shard to fail with `silk fixture reached report cap; subdivide it`, leaving no `shard-result.json` and no unit receipt.

`host_children_maxrss_kib` in a unit receipt is the Docker client's RSS, not the container's. The container is covered only by `host_used_memory_peak_kib`, a host-wide used-memory sample.
