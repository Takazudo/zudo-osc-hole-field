# Available source inventory — 2026-10-18

2026-10-18, baseline5e39d5a265a27d8cbdb3385a10d32a27f37d5f10. Inventory retained from preparation; CONCRETE-DESIGN.md now supplies the finalized source design. Owner correction supersedes the earlier supplier-enquiry workflow: **we design the board; JLC fabricates it. No enquiries will be sent.** Earlier question lists are historical gap inventories, not an execution queue. No viewer/native/canonical change.

## Evidence actually available

| ID | Document / local evidence | What it supports; limit |
| --- | --- | --- |
| J1 | `design/connectors/sources/jst-gh.pdf`, public JST eGH catalog, SHA256 b1dcb317b6b9a4fbbedd2dbf42c64c95306a252d23de8933b85fcf161240b722; same bytes verified2026-10-18 | Page2 top-entry land pattern; page3 exact four-way header/housing row, pin1 views; page6 naming. Reference drawing, revision not printed. Not missing merely because separate product drawing is gated. |
| J2 | Owner CHM-1-2149 rev2 /2019-10-23, private8page PDF; SHA25691e47c17dde5a3cbbed7d969f5e192a5ea84d3ef5472b9e2456c3be089ee4f3b | Page4 housing-surface reflow and stencil recommendation; pages5–8 mating/latch/full-row grip. Stencil recommendation0.12–0.15mm, openings matching land area; greater thickness requires reduced openings/paste adjustment. Keep original/text/images private. Exact limits and applicability must be read accurately; no pixel-derived dimensions. |
| J3 | Owner CHM-1-2111 rev6 /2019-10-25, private10page PDF; SHA2564ab8e9b49f9c5b8c7605f8474583683c46cff07019d9115ffecc4523ac4bf8a6 | Contact/crimp/handling guidance; tensile criteria do not rate connector service load. Keep original private. |
| J4 | Stage32 sources.json identifies JST public eP-Handling.pdf (printed959–962; hash b4319c3cf6cf0cd253cb9bdad3645fa56b26fdabdf637dba630757bc6aa86679) and eP-Crimp.pdf (printed963–966; hash75c84d5c8287586b3ab303d72de4d26218907b0040f8e26ffad7deb33e269096) | Retained source receipts; not newly rehashed local PDFs this turn. General handling, not more specific than J2/J3. |
| J5 | `.claude/skills/component-jst-gh/{manifest,sources,facts,pin-map}.json`; existing GH3/GH7/GH8 footprints; contact-mapping receipt | Existing exact records are3/7/8way, not a GH4 footprint. Mapping-aid footprints explicitly NOT FOR PCB. Derive/audit4way from J1; do not stretch another footprint without checking lands/pin numbering. |
| J6 | JST exact BM04B drawing request page | No separate drawing obtained; form/license not submitted. Its absence is a gap in toleranced geometry, not automatic proof that catalog-based coupon drafting cannot proceed. |
| F1 | JLC official assembly capabilities, inspected2026-10-18; linked in STANDARD-ARRANGEMENTS.md | Standard70mm minimum, rails/fiducials,240±5°C published profile. Full thermal applicability remains open. |
| F2 | JLC official PCB Panelization article updated2026-09-09, inspected2026-10-18 | Straight full-panel V-cuts, zero-gap adjacency,70mm minimum, default rail fiducials/tooling under panel-by-JLC. No need to ask JLC to choose our array. |
| F3 | JLC stencil-fiducial article updated2026-09-01; medium/low paste article updated2026-09-09 | Stencil marks differ from paste apertures; lower-temperature paste joint-strength warning. No arbitrary substitution. |
| F4 | Stage32 S-JLC-CAP receipt, https://jlcpcb.com/capabilities/pcb-capabilities, inspected2026-10-17 | Historical source reading: thickness±10% at≥1mm, routed outline±0.2mm regular, hole position±0.075mm. Historical tolerance reference only; current source design does not claim manufactured tolerance validation. Eurocircuits stage8receipt is not a JLC rule. |

Private J2/J3 files exist outside git in `/workspace/gh-manual-private-intake/extracted/`; hashes verified this turn. No new redistribution. Prior FAQ(N) explanation remains parent-reported after local403; not used to infer new thermal limits.
