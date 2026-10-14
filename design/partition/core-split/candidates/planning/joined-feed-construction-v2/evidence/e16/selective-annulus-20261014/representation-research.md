# Independent representation and authority investigation

Date: 2026-10-14. Scope: read-only source inspection, upstream primary-source retrieval and retained original geometry inspection. Native calls: **0**. Production geometry/census rebuilds: **0**. No request or approval consumed.

## Result

The exact source-owned policy can describe removing the named via's outer In3.Cu annular land while retaining the continuous barrel and all other layer lands. The pinned native serializer must fail explicitly for that policy: a faithful, durable single-layer no-flash representation has not been established in KiCad 10.0.6. Source-fixture success must not be labelled native acceptance.

Pinned primary source inspection found:

- `PCB_VIA::FlashLayer` uses whole-via modes: KEEP_ALL, REMOVE_ALL, REMOVE_EXCEPT_START_AND_END, and START_END_ONLY. KEEP_ALL remains flashed on every copper layer. A per-layer diameter is not a per-layer no-flash setting. `GetMinAnnulus` explicitly treats an unflashed ring differently. [KiCad 10.0.6 pcb_track.cpp, lines 614–636 and 1964–2015](https://github.com/KiCad/kicad-source-mirror/blob/10.0.6/pcbnew/pcb_track.cpp#L1964).
- `parseViastack` accepts custom per-layer size, with no per-layer remove/keep selector. The existing global flags remain whole-via policies. [Pinned parser, lines 7749–7850](https://github.com/KiCad/kicad-source-mirror/blob/10.0.6/pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr_parser.cpp#L7749).
- The writer serializes the global modes and custom sizes. Its `zone_layer_connections` list serializes zone overrides, not an immutable layer-preservation policy. [Pinned writer, lines 2703–2815](https://github.com/KiCad/kicad-source-mirror/blob/10.0.6/pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr.cpp#L2703).
- Zone refill clears via overrides and recomputes them. Therefore forcing every non-target layer into `zone_layer_connections` alongside global removal cannot preserve the requested policy through refill. [Pinned zone_filler.cpp, lines 615–670](https://github.com/KiCad/kicad-source-mirror/blob/10.0.6/pcbnew/zone_filler.cpp#L615).

These are source-level findings, not an executed native experiment. No conclusion is transferred from master/current documentation to the pinned executable.

## Original AGND nonfunctionality evidence

[original-agnd-contact-review.json](original-agnd-contact-review.json) retains exact source, caps, planes and graph hashes with the measured read-only inspection. The KA source bytes match the prepared manifest (`b73bc3a7...`, 15,691,516 bytes, 73,699 objects). Against the named 0.6 mm annulus disk, the original In3 same-net objects contain 5 pads and 793 other vias, zero segments, and **zero intersections**. The nearest other copper is via `e821d480-c98b-5a04-aabc-98a573fdb88c`, separated by **5.5306174122 mm**. Existing graph shape conventions use 32-quadrant polygon approximations; that separation is much greater than approximation error. The retained cap document has no AGND In3 cap; the retained clipped document has no new objects and every AGND sheet is on In1.Cu.

The retained graph binds the target via's six fragments and U2314.10's B.Cu fragment to the same fed AGND component. Both have all fragments connected to feed. Consequently, within the retained source model, the In3 annular land provides no connection to another AGND object, and its outer land is not required by the original graph. This does not prove native connectivity, changed-geometry preservation, or the physical manufacturing process.

The continuous barrel remains electrically necessary. The existing source model explicitly assumes a 0.025 mm barrel wall outside a 0.3 mm bore: its outer diameter is **0.35 mm**, not 0.3 mm. A source projection must retain that barrel band even on In3.Cu. The historical 0.813 mm gap screen removed copper down to the drill; it therefore cannot be transferred to the barrel-preserving implementation. Under the same simple radial-clearance assumption, 0.663 + (0.600 − 0.350)/2 = **0.788 mm**, leaving **0.038 mm** over the 0.750 mm width-plus-clearances requirement. This is a dimensioned hypothesis only; no fresh clipping or native fill was executed.

## Admission boundary and next experiment

The actual local lane in `scripts/kicad/local_native_admission.py` and `scripts/kicad/README.md` permits only startup-success/failure, the exact deferred precision-vendor oracle, and E16 KA-t2/KB-t2/KB-p1 operations. At initial inspection it had no tiny annulus-fixture kind. This source change now extends that existing lane with only `annulus-fixture --target annulus`, a fixed tiny fixture worker, a 60-second deadline and unchanged native resource limits. Each native operation requires a separate genuine operator attestation, applicable qualification and global reservation. The standing numerical campaign authority does not cover native work or geometry variants; the prepared manifest and terminal disposition explicitly require separate future authority. No such authority was found or fabricated.

The prepared implementation now supplies one six-layer, two-via synthetic round-trip negative-control fixture through the narrowly extended existing admission lane, with unchanged native resource limits. The source-only fixture gate/API tests passed; actual native execution remains NOT RUN pending fresh exact request and genuine operator admission. Bind the fixture generator, input PCB bytes, pinned image, exact assertions, unique output directory, clean source SHA, run nonce and existing guard methods before asking for exact operator admission. The prepared fixture tests load/save/reload, preserving UUID, bore, span, layer diameters, exact F/In1/B functional tracks and owner artwork. It contains no zones; a separately scoped refill test remains required before any real candidate. Its native negative control characterizes custom diameter as still flashed; it cannot establish universal nonrepresentability by itself and does not treat global removal as the requested capability. The source parser/flash/refill inspection above is the present exact-policy limitation evidence. See [fixture preparation](native-fixture-preparation.json); this preparation is not an operator attestation.

A concrete **alternative research proposal**, not the current exact removal or an approved production change, is a custom native padstack with a **0.35 mm In3 land**, **0.60 mm lands on each other copper layer**, and unchanged **0.30 mm through bore**, center, net and UUID. This represents a 0.025 mm residual annular width, matching the existing source barrel envelope; it is not true per-layer no-flash. Pinned KiCad can serialize custom diameters, but applicability of unchanged minimum annular-width rules, refill contacts, fabrication tolerance and plating geometry is unresolved. Any resulting violation is a real rejection; do not lower severity or add an exemption. If those unchanged constraints disallow this alternative, a different physical repair needs separately reviewed geometry scope. The prior 23.554 mm × 0.2 mm long-B route remains a negative resistance comparison, not that remedy.

## Retrieved primary-source byte index

Files were retrieved read-only from `https://raw.githubusercontent.com/KiCad/kicad-source-mirror/10.0.6/` into `/tmp/kicad-annulus-review-20261014/`. Recovery uses the exact version URL and must verify these hashes; temporary files are not claimed persistent artifacts.

| Source path | Bytes | SHA-256 |
| --- | ---: | --- |
| pcbnew/pcb_track.cpp | 107642 | b97b29a84e3e732c9d96da030da0816350f31200c8127bedf973482a181c1d94 |
| pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr_parser.cpp | 264319 | 017f74d4fc6476fc1ceec230734fb828640a3c27b52174f6975b749f46458e43 |
| pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr.cpp | 126299 | 7bb4cbcd549b970e6b615bdf7ef2cc4b439408d4f41e531c442dc2336b817e96 |
| pcbnew/zone_filler.cpp | 168902 | 28fa2b555869485254154bbd12b372f6f1057b91b7e3f09d3687eb253a1059dc |
| pcbnew/drc/drc_test_provider_annular_width.cpp | 16135 | ef73e4c65331aa7ab87ec3bbed342758d6941500f36c0a1e82001b46488dafd1 |

Canonical adoption and physical qualification remain unperformed. KEEP_K1402_INCUMBENT is unchanged.
