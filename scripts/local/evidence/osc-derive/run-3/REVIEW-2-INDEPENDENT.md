# Independent static review of the U1105.12 evidence, with diagram and decision boundary

Requested by coordinator instruction `osc-moya-independent-static-2bb3137a`.
Read-only: no KiCad, no fill, no DRC, no copper edit, no install. The original
artifacts (derive run 3 evidence, `REVIEW-NOTE.md` b3dac7a0...) are unchanged;
corrections to the note are recorded here, not applied to it. The class of
C1111.2 <-> U1105.12 stays `UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN`. Nothing here
is a defect verdict or a repair instruction.

## Reviewer and inputs

- Reviewer: a separate general-purpose subagent in this session (fresh context;
  model inherited from the session, not independently reported by the tool), given
  the pinned data and the note, asked to re-derive every claim before comparing.
  Its scripts are kept in the session scratchpad (`review-scripts/`).
- Inputs: frozen source `osc-core.kicad_pcb` SHA256
  `fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10`; derived copy
  `4a55e0c165efcc2215d920272da25476b54df1cc56ba59e95a31049b29ba4dc8`;
  derive-run-3 `zone.json`, `manifest.json`, `receipt.json`; `osc-core.kicad_dru`,
  `osc-core.kicad_pro`; `osc_frozen_topology.EXPECTED`.

## Reviewer findings (verbatim substance, condensed)

1. **Hashes: CONFIRMED.** Both boards match; run-3 checksum list and manifest
   hashes match the files on disk.
2. **Pad positions and identities: CONFIRMED.** abs = footprint_at + R(rot) x
   pad_at with R = [[cos, sin], [-sin, cos]] in KiCad's y-down frame. C1111.2
   (111.210, 225.090); U1105.12 (122.195, 222.225); UUIDs match EXPECTED; both
   SMD on F.Cu/F.Mask/F.Paste only; pad 12 is the only AGND pad of U1105; no
   zone-connect or clearance override on the pad; pad-to-pad distance 11.35 mm.
   Rotation sign cross-checked against the native fill (C1111.2 inside the main
   outline, C1111.1 not).
3. **Cluster reading: CONFIRMED as sound.** Cluster A 558 = 447 PAD + 85 track +
   25 via + 1 zone; cluster B = pad + zone, layers {F.Cu: 2}; connected and
   symmetric false in `after` and `reloaded`; unconnected 4283 -> 3342. KiCad
   models a zone as one connectivity item per filled outline, so the zone parent
   appears in every island's cluster; sharing the zone UUID with connected=false is
   the per-island semantics. Alternatives excluded: BFS through the zone object
   (would have merged the clusters), stale connectivity (fresh Build per phase and
   a fresh load for `reloaded`), outline-only touch (all four corners of pad 12 are
   strictly inside outline 177). Refinement: "main AGND copper" means the largest
   F.Cu outline (86) plus what it reaches; C1129.2 and C1142.2 (AGND, F.Cu) sit on
   outlines 178 and 169 and are also outside the 558-item cluster.
4. **Source facts within 3 mm: CONFIRMED with refinements.** Nearest F.Cu segment
   to U1105.12 is 1.431 mm (pad-11 net); none within 1.2 mm of either pad. Vias
   within 3 mm: six, all other nets, all plain F.Cu-B.Cu through vias (the board
   has no blind or micro vias). Nearest AGND via 4.306 mm at (123.85, 218.25).
   **Omitted by the note:** U1107.3 (AGND, B.Cu, 1.95 x 0.6) at (122.195, 222.38),
   0.155 mm in plan directly under pad 12 on the other side of the board; U1107 is
   an SN74HC14DR on B.Cu. Rule area 0b3a2f2d (neck-down, all flags allowed)
   contains pad 12 and not C1111.2; the 0.15 mm neck-down clearance applies only
   when both items are NetClass Default; AGND is class Ground at 0.25 mm. Zone
   settings confirmed; `connect_pads yes` means solid pad connection.
5. **Filled outline at U1105.12: CONFIRMED and quantified.** Outline 177: 75
   points, bbox 120.909..123.374 x 221.490..223.030 (2.47 x 1.54 mm), area
   3.30 mm2 (pad 1.17 mm2); extends 0.31 mm west of the pad row under the SOIC
   body and 0.20 mm east of the pad edge; stays between pads 11 and 13. No via
   centre and no other pad inside it (all 9,646 vias checked). Its boundary sits
   at the zone's 0.25 mm clearance from: the pad-15-net track X9F96... running
   along the whole outer pin row (x about 123.6..123.7, y 219.1..225.6) to the
   east; pads 11 and 13 north and south; vias X4F82.../XD6A1.../X18B7... and
   their F.Cu stubs under the body to the west. Nearest other AGND outlines: main
   86 at 3.03 mm (west of the three signal vias), 169 at 1.10 mm and 178 at
   1.11 mm (both east of the X9F96 track).
6. **Logical limit (other-layer fills cannot join the island): CONFIRMED as
   sound, with one stated assumption.** Falsifiers checked: a through via inside
   the island (ruled out), a through-hole pad (ruled out, all nearby footprints
   SMD), F.Cu pad overlap (ruled out, 0.67 mm edge gap), island removal (mode 0,
   and the island touches a pad), same-layer zone interaction (the F.Cu AGND zone
   is the only copper zone on F.Cu and the rule areas allow pour). Assumption:
   a layer's fill is independent of other layers' fill caches, which holds for
   this zone's settings but is not something static text can prove for the
   engine. A B.Cu fill will reach U1107.3 directly under pad 12, but with no via
   that copper is on the other side of the board.
7. **Wording corrections to REVIEW-NOTE.md (not applied there):**
   (a) "thermal relief" is not a candidate: `connect_pads yes` is a solid
   connection, so `thermal_gap` is unused at pad 12. (b) The island does pass
   between the neighbour pins (1.04 mm of copper height); what fences it is the
   pad-15-net track along the outer pin row and the three signal vias under the
   body, not the pin pitch plus clearance. The note's vertex count 76 vs the
   reviewer's 75 is a counting convention. The frozen commit id fa16c6ff is
   unverifiable from the files alone (receipt only).

## Diagram (measured geometry, not illustration)

`diagram/u1105-12-island.svg` (labels, legend, clipped to the frame) and
`diagram/u1105-12-island.png` (raster of the same data), generated by a text
parser from the saved files; the extracted window data is
`geometry-window.json` in the cclogs copy. Axes in KiCad mm (y down), window
+/-4 mm around (122.195, 222.225). Shown: pads with net and side, F.Cu and B.Cu
tracks, vias with layer span, the two neck-down rule areas, the F.Cu AGND fill
outlines 177 (orange, holding U1105.12), 169, 178, and the in-window vertices
of the main outline 86. The picture shows the fence described in finding 5.

## Decision boundary

1. **What the saved evidence establishes.** On the derived copy, KiCad's own
   fill puts U1105.12 on a 3.3 mm2 F.Cu AGND island holding only that pad,
   bounded at 0.25 mm by Default-class copper on all sides; C1111.2 is on the
   largest F.Cu AGND outline; the pair is open before and after the F.Cu fill;
   the derived copy differs from the source only by that fill cache; every via is
   an F.Cu-B.Cu through via and none is inside or adjacent to the island.
   U1105 is an AS3340D and its pin 12 is GND in the component evidence
   (`component-alfa-rpar-as3340d/facts.json`), so AGND on this pad is the
   intended net, not a netlist question.
2. **What native evidence would settle full-net connectivity and why static
   analysis cannot.** A chained derivation on parent `ecf170db...` filling the
   B.Cu (`e389d344`) and In1.Cu (`e67a5bc7`) AGND zones and recording the same
   two pairs would move the class to `OPEN_WITH_ALL_NET_ZONES_FILLED` or
   `CONNECTED_VIA_SELECTED_FILL`; a DRC unconnected-items pass is optional.
   Static text cannot run the fill engine, cannot prove the layer-independence
   assumption for this build, and the classification scheme defines evaluability
   by the oracle's output, not by inference. Expected cost: the In1.Cu fill took
   131.9 s on the unfilled source and the F.Cu fill 150.8 s; a chained run starts
   from a 61.3 MB board and ends near 73 MB (one zone) or 84 MB (two zones), above
   the standard 64 MiB output bound, so a chained run needs its own approved
   profile (bound 128 MiB as for the probe; time chain standard or longer; memory
   peak unknown, 1.58 GiB was observed with a 61 MB board).
3. **What is a user product choice, not analysis.** Whether an open AGND at
   U1105.12 (GND pin of the AS3340D VCO) is a defect to repair, and how (a via at
   the stacked U1105.12 / U1107.3 location, a short F.Cu stub, or re-routing the
   pad-15-net track that fences the island), or acceptable; and whether to spend
   another approved native run on the chained derivation.
4. **Smallest recommended next action.** Run the chained fill of the two
   remaining AGND zones on the saved derived copy and record the same two pairs
   (scope: one derive run, parent `ecf170db...`, zones `e389d344` + `e67a5bc7`,
   same pairs, output bound 128 MiB, 1 CPU / 2 GiB / zero extra swap / network
   none unchanged, one serialized slot). If that run shows
   `OPEN_WITH_ALL_NET_ZONES_FILLED` for C1111.2 <-> U1105.12, the open is
   established on the oracle's output and the product choice in item 3 is the
   only remaining step. No defect verdict is implied before that.
