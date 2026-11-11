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
