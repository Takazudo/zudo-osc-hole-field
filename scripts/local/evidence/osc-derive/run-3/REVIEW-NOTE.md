# Review note: C1111.2 <-> U1105.12 (AGND) after the F.Cu AGND fill (derive run 3)

Static note from already-saved evidence and read-only source text. No native
load, fill or DRC was run for it. It gives a human reviewer a concrete target; it
does not change the recorded class `UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN`, is not
a defect verdict and is not a repair instruction.

## Identity of the boards

| item | value |
| --- | --- |
| source `osc-core.kicad_pcb` (frozen commit fa16c6ff, published, unfilled) | SHA256 `fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10`, 49,819,556 bytes |
| derived copy (F.Cu AGND zone filled, nothing else) | SHA256 `4a55e0c165efcc2215d920272da25476b54df1cc56ba59e95a31049b29ba4dc8`, 61,320,854 bytes, identity key `ecf170dbb48e07980d8c08e149ff6e5c223745b58cdd9f9abb09cfa4b5001d16` |
| non-fill semantic hash, source and derived | both `a97c70f0809d8d43b68e70df3eb3998aa978bc5551cf66b85cc6050cdf29aa65` (host recomputed) |
| project / rules | `118d3a49...0136fe` / `14989a90...c27ac`, identical on source and derived |
| fill ownership on the derived copy | only zone `601e02b2-8ccb-5c28-83e5-03789d47fbbd` (AGND, F.Cu), 236 outlines |
| tooling / image | 4bc4a152 / `kicad/kicad@sha256:18693567...`, pcbnew 10.0.6 |

The derived copy differs from the source only by that zone's fill cache, so every
pad, track, via, rule area and setting below is the canonical board's.

## The two pads

| pad | UUID | footprint (layer) | absolute position (mm) | shape | copper layer |
| --- | --- | --- | --- | --- | --- |
| C1111.2 | `6e370474-ba32-594b-8c28-3b65ab475ff1` | `zudo-osc-hole-field:C0603` at (111.21, 224.39) rot -90 (F.Cu) | (111.210, 225.090) | rect 0.8 x 0.9 SMD | F.Cu only |
| U1105.12 | `608c587b-7aab-54c1-b46c-3773193ec4c0` | `zudo-osc-hole-field:SOIC-16_3.9x9.9mm_P1.27mm` at (119.72, 221.59) rot 0 (F.Cu) | (122.195, 222.225) | roundrect 1.95 x 0.6 SMD | F.Cu only |

Both pads are AGND (`osc_frozen_topology.EXPECTED`). Pad 12 is the only AGND pad
of U1105; its neighbours 11 and 13 (1.27 mm pitch) carry signal nets. Distance
between the two pads is about 11.3 mm.

## What the saved connectivity shows (zone.json, `reloaded` phase)

| | before the fill (source) | after the F.Cu AGND fill (derived, reloaded) |
| --- | --- | --- |
| C1111.2 cluster | 1 item: the pad | 558 items: 447 pads, 85 tracks, 25 through vias, zone 601e02b2 (`selected_zone_member` true) |
| U1105.12 cluster | 1 item: the pad | 2 items: the pad and zone 601e02b2 (`selected_zone_member` true); 0 tracks, 0 vias, 0 other pads |
| pair connected | false | false (also false in the `after` phase before save/reload) |
| board unconnected count | 4283 | 3342 |

Reading: the F.Cu fill does touch U1105.12 (the zone is in its cluster), but the
copper island that touches it contains nothing else. KiCad lists the zone object in
every island's cluster, so sharing the zone UUID does not mean the two pads share
copper. No U1105 pad is in the main 558-item AGND cluster.

## Static source facts around U1105.12 (read-only text of the frozen board)

- No F.Cu track segment within 1.2 mm of either pad.
- No AGND via within 2.5 mm of U1105.12; the five nearest vias (1.6 to 2.3 mm)
  belong to other nets. The board has 177 AGND vias in total.
- The pad lies inside rule area `0b3a2f2d-a8db-5ec7-b328-2073823d9722`
  (`pcbgen:osc-core:neckdown`, F.Cu/B.Cu/In2.Cu/In3.Cu, rectangle 114.27..125.17
  x 217.54..229.76). Its flags allow tracks, vias, pads, copper pour and
  footprints; it is one of 326 identical "allowed" areas named by the design rules
  (`osc-core.kicad_dru`: neck-down clearance and track width for Default-class
  signals; "Rails and AGND keep their net-class clearance"). It does not forbid the
  AGND pour. C1111.2 is inside no rule area.
- F.Cu AGND zone settings: `connect_pads yes`, clearance 0.25 mm, min_thickness
  0.15 mm, thermal_gap 0.5 mm, `island_removal_mode 0`; zone outline covers both
  pads (104..414 x 58..342 mm).
- The 20 true keepouts on the board (all flags not_allowed) do not contain either
  pad.

## What this does and does not establish

Established by the saved run:

1. On the derived copy, U1105.12 is reached by the F.Cu AGND fill only on an
   island holding no via, track or other pad; C1111.2 is on the main AGND copper.
2. The pair stays open after that fill; the B.Cu and In1.Cu AGND zones are still
   unfilled on that copy, which is why the class is `UNEVALUABLE`.

Hypothesis for human copper review, not proved:

3. A B.Cu or In1.Cu AGND fill connects to F.Cu copper only through vias (all 9,646
   vias are F.Cu-B.Cu through vias). Since the island that reaches U1105.12 holds
   no via, filling the remaining AGND zones is not expected to join it to the main
   AGND copper. If that holds, the open is not a missing fill cache but copper
   geometry around U1105.12: the signal pins at 1.27 mm pitch on both sides of pad
   12 plus the 0.25 mm zone clearance may leave no path from the pad's fill stub
   to the surrounding pour, and there is no AGND via or track near the pad to
   bridge it. Candidates a reviewer could check in the canonical board: an AGND
   via or short F.Cu stub at pad 12, or the fill geometry (clearance, thermal
   relief, island handling) in that pin row.

Not established:

4. Whether the canonical, fully filled board (all five copper zones) shows the same
   island: only a chained derivation adding the In1.Cu and B.Cu fills, or the
   canonical filled board, can move the class to `OPEN_WITH_ALL_NET_ZONES_FILLED`
   or `CONNECTED_VIA_SELECTED_FILL`. Neither was run; the single approved probe is
   consumed.
5. Whether any DRC item corresponds to this pad: no DRC was run on this copy.
6. Any electrical or manufacturing consequence; this report never claims board
   acceptance.

Evidence: `scripts/local/evidence/osc-derive/run-3/` and cclogs
`osc-local-wsl/derive-run-3/` (`SHA256SUMS` c760369a...); this note is also copied
to cclogs `derive-run-3/review-note/`.
