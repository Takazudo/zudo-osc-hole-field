# Trimmer annotation candidate contract

This fixture is a source-only front/back sample. `two-face.kicad_pcb` carries two
trimmer references, a separate owner text object, a pad and an edge object. Its
poses and Ref/Block/Role values come from the reviewed #248 inventory at the
coordinator input `6700ccb1a9a64630cd26bccf751f537f3cc25d42`.

Run focused checks with `python3 -m unittest scripts.pcbgen.test_trimmer_labels`.
The native fixture command is
`bash scripts/kicad/run.sh python3 scripts/pcbgen/trimmer_labels_native_regression.py`.
The latter must be scheduled within the epic's global two-worker limit; until
then native load, SVG render, reload and physical clearance remain **NOT RUN**.

`trimmer_labels.py` takes an explicit input board, JSON policy and fresh output
path. The policy uses schema version 1, `board_id`, SHA-256 of the exact input
board and `design/service/trimmer-inventory.json`, and `labels` entries with
`ref`, `block`, `role`, `face`, `x_mm`, `y_mm`, `angle_deg`, plus optional `text`.
`text` may introduce one newline at an existing word boundary but cannot change
the reviewed function label. Example (replace hashes with actual full digests):

```json
{
  "schema_version": 1,
  "board_id": "osc-core",
  "input_board_sha256": "<exact SHA-256>",
  "inventory_sha256": "<exact SHA-256>",
  "labels": [{
    "ref": "RV1601", "block": "OCTAVE_REF",
    "role": "octave_reference:RV_GAIN", "face": "F.Cu",
    "x_mm": 141, "y_mm": 265, "angle_deg": 0
  }]
}
```

For an update/removal pass, add `base_board` as a policy-relative path to the
original input board. The input may then be a previous candidate, but after
removing this tool's annotations all remaining bytes must match the original.
Only UUIDs derived from `uuid_tools.stable_uuid(board_id,
"trimmer-labels-v1", ref)` belong to this tool. Repeated application gives
identical bytes. Existing Ref fields, hidden Block/Role, owner artwork, copper,
pads, nets, placements, outline, and all other bytes are untouched. The tool
does not adopt candidate output onto a canonical board.

The source stage **does not certify clearances**. Every run reports body, mask,
pad, edge and text clearance as unresolved until the pinned native fixture and
a separate candidate-specific geometry review pass. Do not conceal a label to
resolve a conflict. Fixture coordinates demonstrate behavior, not a reviewed
production annotation layout. Manufacturer legibility and physical fit remain
unknown. Common command registration belongs to the foundation owner.
