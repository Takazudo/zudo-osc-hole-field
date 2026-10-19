# Stage44 — B2-specific disposable layout

This stage replaces the rejected Stage43 exact translation with B2-specific
placement and routing on an owned working copy. It preserves the common circuit,
physical pin IDs/nets and existing parts. No canonical CAD or manufacturing output
is adopted or changed. Parent PR286 remains at b58068f; Stage42 B1 remains the
accepted disposable baseline. Stage43's negative results remain historical evidence.

All four native passes pass on board SHA256
`d1f79d02ac20ecca28591a1332fd217603ac53ce114bcd4aa1290f78ba3d2b73`: zero
rule errors/parity differences, all 24 private nets and 18 power paths connected,
retained partitions unchanged, 117 inherited opens and 476 warnings. No new
uncapped warnings occur; capped silkscreen coverage remains unresolved.

## Scope and geometry

The baseline board is Stage42's accepted fresh copy, SHA256
`975cd15d5ba69b9695e8d32a575a289306a27f1ea17d6b5f7a5819071dc5505b`.
Thirty electronic packages change pose within a 31-package B2 scope. Four jack
packages and the front indicator remain byte-identical, as do B1 and every foreign
footprint. R3209 remains at its canonical B2 position, native (146.8,205.37),
B.Cu90, clearing the named rear keepout rather than repeating Stage43's conflict.
R3204 is shifted +0.15mm Y from the B1+34mm template, to native
(146.75,187.65), B.Cu90. Every other scoped package uses the actual native B1
pose +34mm X, avoiding Stage43's rounded-capacitor origins. These are study poses,
not changes to the canonical placement inventory.

The first placement had one clearance failure: R3204 pad2 versus retained foreign
via098815c7-6361-5ba2-9475-43271862772f, 0.145mm against a 0.200 mm rule.
The selected 0.15mm displacement is a bounded local repair, not a proof of globally
minimal placement. R3209's canonical courtyard has a 5.6 mm X gap to the named
keepout. Native DRC still evaluates all other obstacles.

Exactly 830 B2 private copper occurrences and 28 separately reviewed local supply
objects (19 segments/9 vias) are retired. The latter include all 11 retained objects
that Stage43 wrongly renetted. All three external supply anchors and their
foreign tracks remain. The ownership screen is necessary but not sufficient:
complete native partition equality is separately required after routing.

New copper totals 938 objects:18 power segments/12 vias,14 rear-layer segments for
a real R3202:+5V feed to retained anchor06b2530e-ef31-5ad6-b94a-011fdc6dd3ee,
and 818 signal/rail segments/76 vias. No existing object is renamed or waived.
The router uses actual obstacles, 0.05mm raster,0.25mm clearance,0.20mm signal
width,0.40mm rail width and0.70/0.30mm vias, within native bounds
X140.5..173,Y168..213.5 on F.Cu/In2.Cu/B.Cu. The first signal order missed
C3203.1 on X4C67F313FD4F29BCBD2D; prioritizing that net routes all47 links.
Both attempts are retained. Raster completion is only a proposal, not acceptance.

## Preservation and qualification boundary

The identity gate compares all retained copper occurrences, including the
pre-existing duplicate-UUID geometry, every physical pad ID/net, zones/rules,
foreign/fixed footprints, project and recursive schematic/library dependencies.
For moved packages it replays only native position/rotation/side operations from
the pinned baseline, then compares complete serialized packages. Library IDs,
DNP/BOM attributes, pad shapes/drills/offsets and models cannot silently change.

All 36 B1/B2 package pairs retain common library IDs and non-placement properties.
Block/panel IDs and old placement properties differ as expected. Those unchanged
placement properties are provenance, not authoritative working-copy coordinates.
No new component substitution is made. R3214's exact MPN and jack manufacturer/
CAD bridge remain inherited unresolved inputs; manual inventory still has 68 lines
and 0 declared placements. Metadata reuse is not supplier or placement qualification.

Acceptance requires three stable native memberships plus a separately loaded
fresh copy: zero rule errors/parity differences, all 24 B2 private nets closed,
18 power paths, exact retained partitions, identical board hash and no additional
uncapped warnings. Each DRC execution is bound to its saved board, exact command,
report hash and unchanged baseline dependencies. The 117 pre-existing opens remain.
KiCad caps silk_overlap and silk_over_copper at 199 each; their varying samples
cannot establish exhaustive silkscreen nonregression. This is never a full-board
DRC pass or analog/physical qualification.

See `VERIFICATION.md`, `evidence/settlement.json` and `REVIEW.md` for final results.
Large boards, native snapshots and first failures remain ignored locally; portable
source/proposal evidence and their hashes are committed. The next stage requires
parent review before any adoption or wider layout work. No manufacture, order,
energization, release, deployment or merge occurs here.
