# Independent native coupon review — 2026-10-18

Reviewer: separate `/root/coupon_review` agent. Verdict: **PASS_REVIEW_ONLY**,
no remaining blocking finding. The reviewer did not edit files or interact with
existing development sessions.

The reviewer independently read the pinned source design, manufacturer JST eGH
catalog printed pages 2–3, native PCB/schematic text, exported netlist, BOM/CPL,
drill files, Gerbers, audit JSON, actual-Gerber rendering and native-PDF raster.
The schematic's original local `/GHn` vs PCB `GHn` names were identified and fixed;
the final exported names and pin correspondence match.

Confirmed:

- J1 top view, zero rotation, pin 1 left; six exact lands and four independent
  noncrossing routes to their respective testpads.
- Overall 80×100 rectangle; 80×80 functional area; full-width V-cut annotations
  at y10/y90 on the drawing layer, separate from Edge.Cuts.
- Three fiducials, three Ø2 NPTH holes, both-face clamp/V-cut reservations.
- Exactly six header paste apertures, no TP/fiducial paste, empty bottom copper.
- NPTH export uses absolute mm: (15,−5), (15,−95), (65,−5); PTH export empty.
- J1-only BOM and CPL; CPL (40,−50), top, 0 degrees agrees with KiCad Y-up export.
- Retained final author-run ERC reports zero errors/warnings; DRC reports zero
  violations, unconnected pads and footprint/schematic-parity errors. The reviewer
  inspected these reports; native commands were not independently rerun.

Independently verified SHA256:

| Artifact | SHA256 |
|---|---|
| Source design.json | `925a7b6ce211797d4736fe2c40fe71bb551b98bb3f720738f26e49a36e26dd7c` |
| Pinned upstream footprint | `c0e5c962366864b39ad3a295bb6419547e18f0f5ac49060d75ea51d0e7079732` |
| gh4-coupon.kicad_pcb | `13618b4eb37d851a7329b7498001787b5dd99f8706c6bd75fb81275533d4c6f5` |
| gh4-coupon.kicad_sch | `eade3dd11efdede5a37a09a56f3980d027f160bf79afced21d09e837431505c8` |
| review-only/netlist.xml | `fe00836bd58524f24356214b29f5ab2795290452364d4466635ffbd2fd6fb375` |
| review-only/placement-native.csv | `b03ccf9d3f4364d9ea1ce0bc416b637a4b0869ddcad7dc23d37afada94a2d89f` |
| review-only/gerber-review.png | `11fc112c23dbd8269712673f79792ab5771ebf5337e86f6a6756389f5fa01ebe` |
| review-only/board-top.png | `8d15364afce67d99fa33593b815c1caa5de30369aa2370732f293e71807ffdc0` |

Limits: limited Gerber renderer, not CAM certification; supplier placement/V-cut
interpretation and physical solder/continuity/handling remain untested. No release
or physical assembly acceptance. All exports remain review-only.

Follow-up review verified the README, omission of transient `.kicad_prl` from the
audit hash list, and the source SHA guard. Final generator hash:
`8ecc71f9624737212bba19af7a6ee54df19eb40fd68e9424d1dc5cc87c38aa64`;
final audit JSON hash:
`1bc66e511b9b8edaa4b145aa6abf9eb1e3fb2b5df6dcb61aba65448ebe381675`.
These scripts use assertions and must be run normally, without Python `-O`.
