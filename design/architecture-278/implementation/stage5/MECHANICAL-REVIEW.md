# Independent Stage 5 mechanical evidence and header repair

The eight-header candidate repair removes all prior seven nominal contact/tail-to-GH-land exclusions and passes a stronger official drill-envelope screen across all480 contacts,10 female flange-hole envelopes and85 headers. It remains **NOT QUALIFIED** mechanically. Twelve opposite-face GH-courtyard/hole projections remain unresolved; copper clearance does not prove body/tail/annular-pad clearance. Native/ERC/DRC/physical checks: **NOT RUN**.

## Verified official evidence

The exact official HARTING product pages expose unrestricted typesheets through their public download service. Both selected MPNs are explicitly listed in the inspected drawing tables. The raw drawings, metadata and catalogue are ignored cache evidence; source URLs and SHA256 hashes are committed in din-evidence.json. No restricted CAD, login or footprint download was accessed.

- Female [0903296X824, revision C](https://b2b.harting.com/files/download/PRD/PDF_TS/0903296X824_100173852DRW153C.pdf), page1:96 contact drillings diameter1±0.1 mm, positional tolerance diameter0.05 mm; flange holes diameter2.8+0.1 mm,90±0.1 mm spacing; row-b/flange-axis offset0.3±0.1 mm. Maximum length95 mm, width10.5±0.1 mm.
- Male [0903196X922, revision B](https://b2b.harting.com/files/download/PRD/PDF_TS/0903196X922_100216585DRW016B.pdf), page1:96 contact drillings diameter1±0.1 mm and positional tolerance diameter0.05 mm; flange holes diameter2.55±0.05 mm,88.9±0.1 mm spacing; maximum body94×11 mm. This does not imply the same flange geometry as the female.
- Official [Mezzanine selection guide](https://b2b.harting.com/files/livebooks/en/PRD0200000100124/downloads/livebook.pdf), physical page15: selected female09032966824 and male09031966922 are paired for18.3–20.0 mm PCB distance. Candidate19.2±0.3 mm lies inside that range, conditional on correct PCB-face and mating datums.

Drawing drill dimensions do not specify an annular copper pad. The exact view-to-board mirror, flange/body datum registration, plating/fabrication allowances, solder protrusion, fastener heads, carrier/frame and guide geometry remain unresolved. The checker keeps the candidate electrical contact grid and conservatively expands female flange-center uncertainty symmetrically; it does not invent a signed native transform.

## Whole-header moves

| Instance | Headers | Translation mm |
| --- | --- | --- |
| O3 | SAW and PUL middle headers | +1.2 X |
| O3 | K-O1-1 and K-O1-2 | +4.5 X |
| O4 | K-O1-1 and K-O1-2 | +0.4 X |
| O5 | K-O1-1 and K-O1-2 | −2.4 X |

All pads, pin links, package courtyards and origins translate rigidly. The larger drawing-based hole envelope exposed two additional O5 selector-header conflicts; O4 moves prevent the shifted O3 courtyards from overlapping their neighbors. These are explicit candidate inputs, not canonical edits or new fixed panel positions.

The independent screen reports zero drill-envelope/GH-land exclusions, zero same-face header courtyard intersections and zero shared30 courtyard/hole intersections. It uses contact radius0.55+0.025 mm; female flange radius1.45 mm plus symmetric offset/spacing uncertainty; maximum GH land dimensions with0.05 mm source-coordinate allowance. This is a bounded source exclusion test, not a complete manufacturing tolerance or full-solid proof. The inherited15×100 mm DIN reservation and exact signed body registration require reconciliation before physical acceptance.

## Electrical and service consequences

Parent rebudget is consumed and compared exactly with independently recomputed source output.26 path rows and23 return records change; all270 wire checks retain at least12.224881 mm slack against10 mm required. Maximum complete path remains334.018298 mm and38 paths remain over300 mm. All225 paths,240 returns,85 headers and480 contacts remain represented. No power-package movement is implied.

The revised two-grip proposal,19.2 mm nominal mating separation,40 mm withdrawal and100 mm external workspace remain conditional. Force/frame/guide/fastener validation and all438 hardware Z solids remain open. The2,585 non-OSC/POWER K packages still require explicit physical disposition; the header repair does not create qualified rear free space or authorize redesign of those functions.

Seven focused mechanical tests and deterministic --check pass. Tests cover full contact/header counts, preserved unknowns, stronger drill-versus-tail exclusion, official exact-MPN identity and wire slack. Evidence drill/flange mutations recompute envelopes; an unsupported connector angle fails closed. Imported geometry-helper source hashes are bound in the report. Parent rebudget tests are reported separately.

## Reviewed source hashes

| Source | SHA256 |
| --- | --- |
| `design/architecture-278/implementation/stage5/din-evidence.json` | `92e5c54c23ba6aab69e0036951f66ef5e1e2c4f6a1bbdc99d88e07a306c50f17` |
| `design/architecture-278/implementation/stage5/header-repair-input.json` | `2fe0d9d413eaab44139090e9651c2e56eaad7d724c48bc2305123f89c8d5245e` |
| `design/architecture-278/implementation/stage5/mechanical-report.json` | `eb7e0dab91307b7f20b1f2d3bc00d4b72042da1d01883d43aed911fc543e02ea` |
| `design/architecture-278/implementation/stage5/candidate-report.json` | `fb6861e71e98bd2ef6e26869101b6a4633b077fab7e7f4a6cacf422746675a91` |
| `scripts/architecture278/implementation/stage5_mechanical.py` | `48cc132d9b3ffe05f2b2f05a97c112b0f342a493cbf663aa6cfc208b2056d539` |
| `scripts/architecture278/implementation/test_stage5_mechanical.py` | `c96ab4058df85bbe2c92b9cce97f349bcf113e02d40d0552c7e48a64210781bf` |
| `scripts/architecture278/implementation/stage5_rebudget.py` | `ba122edfccf5b6e002ccbe067d96725e4db0b265a7466f9bd1fb76f2bb019fe9` |
