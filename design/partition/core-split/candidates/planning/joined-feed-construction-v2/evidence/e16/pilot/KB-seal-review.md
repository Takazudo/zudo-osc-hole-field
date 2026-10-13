# KB +5V pilot corridor seal: all six sealed rules hold (geometry review, independent shapely)

Scope: CAND/evidence/e16/pilot/KB-seal.json, F.Cu, width 0.25 mm, path
(295.79,38.2)->(292.44,34.45)->(292.04,34.35)->(289.99,34.25), body = LineString.buffer(0.125, round caps, quad_segs=64);
via-to-path gaps re-checked analytically (point-to-polyline distance minus radii). Scripts: scratchpad/review_seal.py, review2.py.
Native KiCad DRC: NOT RUN (out of scope for this review; the KiCad 10.0.6 oracle was not invoked).

## Seal binding verified
- sha256(KB-preflight-c-same-net-drills-exempt.json) = e85cfef0...0d5e = seal.preflight_sha256.
- Seal path/width identical to preflight `proposal`; preflight input source sha 25124055...4f19 = sha of the normalized-caps.json reviewed.

## Rule 1 holds: min other-net F.Cu copper gap 0.2517 mm
- 0.25167 mm to via a8ab62d0-fd7c-5ad9-b9cc-6a5fa7924e88 (net X965884E569C2BD8409A5, centre 292.05,35.05) -- analytic; margin 1.7 um.
- next: 0.32325 via fffcb099-f4ba-5bd8-b24d-5d9cbc279898 (XDE32C496AC71F9F9E6D3); 0.4767 segment b1468884-70d4-58f8-aadc-b799dbe3e417 (X965884E569C2BD8409A5); 0.775 pad J900072.5 df344a8a; 0.83 pad R4340.2 (AGND).
- 0 violations among all F.Cu pads/segments/via annuli of other nets. All 7291 pads carry polygon_mm.

## Rule 2 holds: nearest other-net drill 0.4017 mm; no NPTH keepout nearby
- 0.40167 mm hole gap to a8ab62d0 drill, 0.47325 to fffcb099 drill; 0 other-net/NPTH violations (199 keepouts, all drilled, none near).
- Same-net drills inside 0.25 mm: only the two end vias -- start d23658ae (hole gap 0.00912 mm) and end e52b5e9d (0.01192 mm). The trace copper does NOT enter either hole; it ends 0.284 / 0.287 mm from the via centres, just outside the 0.15 mm drill radius.
- Exemption is sound: copper-to-hole clearance is a different-net rule. Conventional routing ends a track at its own via's centre, i.e. the track fully overlaps that via's drill, and KiCad treats that as a normal connection, not a hole-clearance error. This corridor is more conservative than that. The only same-net drill other than the end vias is 63c572fc (an orphan-component member) at 0.9214 mm.

## Rule 3 holds: no forbidding rule area crossed; inside the outline by 17.49 mm
- The only rule area touched is 9eca3306-54bb-5b67-b0b9-fd738859418a (F/In2/In3/B), and every rule in it is `allowed`. No rule area with tracks or vias `not_allowed` on F.Cu intersects the body; I checked all 346.
- The body lies inside the 0.6 mm-inset outline (layer_construction.outline_inset_0p6mm_polygon_mm), with a 17.485 mm margin. Same frame as the objects (object extents x 6.5-313.05, y 10.5-291.1).

## Rule 4 holds: positive overlap at both ends, orphan to feed
- Start d23658ae-2276-53ce-8c7b-c86cc977dfb4 is a +5V via on F.Cu. Overlap is 0.02629 mm2. In the graph its component is `862b8e1b-...|F.Cu|0`, with all_fragments_connected_to_feed=false and any=false. That is the same component id as target pad 2fd54753 (U4320.14, +5V, F.Cu), which is unresolved in port-obligations. It is also listed in the preflight orphan identities.
- End e52b5e9d-9c86-5cc7-bfcf-ce7e1a13667e is a +5V via on F.Cu. Overlap is 0.02562 mm2. Its component is `bf9a9d88-...|F.Cu|0`, with all_fragments_connected_to_feed=true. It is not in the orphan set.

## Rule 5 holds: additive and within limits
- Face segments only (3 <= 10), length 7.4932 mm <= 30, no drill/part/layer change. The whole path lies within 6 mm of the start via, so it is inside the 12 mm window margin around the orphan F.Cu copper.

## Rule 6 holds: no other +5V contact, no other-net crossing
- The only +5V F.Cu objects within 1 mm are the two end vias (overlap) and orphan via 63c572fc, which is 0.771 mm away with no contact. Its clearance does not matter, because both sit on the same net and the same orphan component. No other-net copper is crossed (min 0.2517 mm).

## Residual caveats do not violate a sealed rule
- The model's F.Cu holds only pads, segments and vias. clipped-sheets.json contains no F.Cu records, so any F.Cu zone fill absent from the normalized data is not checked here.
- The ends sit 16 um / 13 um inside the via copper edge, and the overlaps are about 0.026 mm2. Contact is positive, but the margin is thin; centring the endpoints on the vias would be more conventional, if the tool's rules allow it. A KiCad connectivity/DRC confirmation is NOT RUN.

VERDICT: PASS
