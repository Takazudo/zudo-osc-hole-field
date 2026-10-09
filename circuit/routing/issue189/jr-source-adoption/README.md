# JR133 source-regeneration pilot

Prepared on main d644b527 after PR213's exact803bba6 head passed all five checks
in run37991181938 attempt2. **Native pilot NOT RUN yet; no source placement or
canonical PCB is changed by this preparation.** Source translations remain empty.

The read-only worker must start clean, with JR SHA256
35b52972dd70b4186cf3f3b7ee2ac3d70432f3476c2f56c9fcf9c1c4d7d4d445 and the original
floorplan/project/rules. It refuses to replace prior pilot directories. It:

1. Replays the existing RB4413[0,-0.2]mm move and eight additive copper objects;
   requires the reviewed native fresh candidate hash
   ae6e998c8b490394c6d3f7e2749e7d1521b4f9c6120067358a6bdf766cead5ff.
2. Preserves the original netlist, schematic, native baseline and every canonical
   PCB hash, then activates the one reviewed source translation only in the
   disposable worker checkout.
3. Runs partition and schematic regeneration. Requires exactly the reviewed
   placement row change, unchanged fixed lock/board definitions/other-board
   netlists, and unchanged JR components/pin-net assignments except that one
   `FootprintOriginMm` field.
4. Syncs and places a disposable copy with the regenerated source. Requires the
   ordinary native gate, zero DRC/parity, no original pad-group splits,133edges,
   every51177prior copper blocks plus exactly8reviewed additions, no cuts, and no
   physical/metadata change except the reviewed origin and its source field.
5. Repeats independent fresh validation, full source generation and native
   sync/refill. Requires deterministic source patch, board bytes and connectivity.

The driver requires three settled membership repeats per native check. All native
reports must identify pinned10.0.6. The pilot never publishes a board. Even on
success, inspect the complete generated patch and independent artifact receipts
before adopting source and copper together. Keep the sole core worker37984573591
untouched and issue189 open.

Nineteen focused source/geometry/rejection tests pass. They cover altered values,
footprints, sides, other components, pins/nets, source origins and native metadata.
The real-placement regression now checks original versus generated translated
source, so activating the record does not translate the part twice in the test.
Native execution and the updated-source acceptance gates remain unrun.

Once pinned-native access is available on a fresh supported runner, use the
existing read-only local-pilot job with a worker-only override invoking:

```sh
timeout --signal=INT --kill-after=2m 80m \
  python -u circuit/routing/issue189/jr-source-adoption/pilot.py
```

Use the shared heavy guard for any local equivalent. Do not retry local image
unpacking in this cloud environment. Preserve `.circuit-cache/issue189-jr-source-adoption`,
the original `issue189-rb4413-move` result, all `osc-jack-right-grid-189-jr-rb4413-*`
and `osc-jack-right-grid-189-source-*` workspaces, and the full console log. Upload
hidden project/rule files; exclude only transient `~*.lck` files. The source patch
is evidence to review, not an instruction to apply blindly. No fabrication or
hardware qualification is implied.
