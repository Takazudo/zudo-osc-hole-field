# MC02 retained FH12 source reconciliation

Date: 2026-11-17. Coordinator: Codex on x0x WSL. Independent source reviewer:
`retained_fh12_review`. This addendum narrows the historical packet's source gaps;
it does not adopt hardware or close the five-check gate.

## Exact retained source

The existing pinned resource repository at commit
`d7cdf9e4dde7906abeafe82c7aa4f66134eee2f9` supplies catalog blob
`0f297c37db08eee71aad26ed62e5554d1c258a4d`. Its 708437 bytes hash to
`9f056f58ff000739633cc3cb7697ba185967083dcf1429b7ab10783b3f55bac5`,
matching the MC02 packet. The source is a manufacturer-authored Hirose catalog
retained through an LCSC mirror, not a newly fetched current manufacturer drawing.
The cover identifies `2013.11②`; its filename date is not a revision.
Read all 20 pages and visually reviewed printed pages 4, 11, 17 and 18.
Printed page numbers equal zero-based physical PDF index plus one.

## Supported statements and limits

| Claim | Source locator | Disposition |
| --- | --- | --- |
| Standard bottom-contact FH12-8S/14S/26S/40S-0.5SH(55) applicability | Printed pages 2–4 / physical indices 1–3, ordering information, configuration and dimension table | Exact standard variants are included; `(55)` is gold plating. This does not establish the revision of currently shipped parts. |
| Closed height 2 mm | Page 4 / index 3, standard bottom-contact drawing and note 5 | Supported nominal closed height. Do not substitute strengthened FH12S dimensions or interpret terminal coplanarity as body-height tolerance. |
| Polarizing marker | Page 4 / index 3, top view | Existence and depicted position are shown. This is not an explicit contact-1 label or a project placement mapping. |
| Contact-1 mapping | Page 11 / index 10 | The explicit No.1 labels belong to vertical-mount drawings. They cannot establish numbering for selected horizontal SH variants. Remains unresolved. |
| Bottom-contact insertion direction | Pages 17–18 / indices 16–17, operating instructions | Conductive side faces down during insertion. Project latch side, rotation and cable termination mapping remain unproven. |
| Open actuator and access envelope | Pages 4, 17–18 / indices 3, 16–17 | Illustrations provide no numeric open height, sweep or finger corridor. Existing 5 mm remains ASSUMED; all 31 latch-access items remain NOT SHOWN. |
| Mating FFC contact thickness | Page 2 / index 1, product specifications | Connector requirement is 0.3 ± 0.05 mm. This is not evidence of selected cable compliance. |
| Horizontal land geometry | Page 11 / index 10, upper drawing | Supports retained pitch and land geometry; 1.8 mm tab width is derived arithmetic, not a separately dimensioned tolerance. |

No exact selected same-side LX cable drawing was obtained for C26618, C29534,
C32128, C68390 or C81339. The retained opposite-side A771 drawing does not close
that gap. Do not measure an undimensioned catalog illustration to invent an open
envelope, infer horizontal contact numbering from a vertical variant, or promote
connector requirements to cable compliance.

## Remaining work and verification boundary

An exact SH source explicitly identifying contact 1 is needed before binding
numbering to footprint pads and placed rotations. Numeric opening-envelope evidence and exact selected cable tolerance drawings
remain missing; a mounted access model and placement mapping also remain required. This source review proceeds
independently of the admitted MC04-R1 room-only study.

The catalog hash and applicable drawings were independently inspected. No
engineering input, canonical geometry, source fact verdict or generated catalog
was changed by this note. Native KiCad, DRC, fill and hardware acceptance were
NOT RUN; existing native PASS remains scoped to its recorded source commit.
