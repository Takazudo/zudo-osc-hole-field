# Explicit component catalogue coverage

Date: 2026-10-02. Every schematic, board and assembly remains an unvalidated draft.

Issue 21's owner records covered all 36 current shortlist parts, but selecting the
shared passives parent did not publish its ten subordinate records. The installed
renderer selects records individually. The original hold and slew capacitors
were consequently absent from the generated catalogue. Four additional current
JST housing/contact records were also unpublished; their evidence and physical
acceptance remain a separate issue 63 concern. None of these fourteen records is
a retired identity.

Publish four existing records with appropriate retained PDFs and existing family
CAD: KEMET C0805C103J5GACTU and C0603C101J5GACTU, Yageo RT0603BRD07100KL, and the
Fenghua 1206CG104J500NT proposal. The last record links a **FAMILY specification**
under the label **Specification PDF**, not an exact-part datasheet. Its record
description and conditions prominently retain exact-MPN applicability
**UNSOURCED**. The source's inspected cover title, revision, date, locator, mirror
authority and retained hash are unchanged. No new source bytes, footprint,
model geometry, part selection or qualification result is introduced.

`catalogue-publication.json` records ten remaining renderer blockers:

| Records | Existing evidence boundary | Renderer limitation |
| --- | --- | --- |
| Murata GRM21BR61E475KA12L and GRM188R71H104KA93D | Exact detailed datasheets unavailable; bulk lifecycle remains a distributor report, while bypass planned-discontinuation is a dated manufacturer catalogue observation | Version 0.1.0 requires exactly one linkable PDF-labelled document; no generic source-record or missing-document choice |
| Vishay TNPW080510K0BEEA, Yageo RC1210FR-07499RL, Bourns TC33X-2-102E and TC33X-2-103E | Retained footprints have no model reference | Version 0.1.0 requires a WRL for every selected PCB record |
| JST GHR-03V-S, GHR-07V-S, GHR-08V-S and SSHL-002T-P0.2 | Existing external numbering aids are explicitly NOT_FOR_PCB and have no WRL | Publish the evidence without inventing a housing/contact model or reclassifying an aid as physical PCB geometry |

No global CAD disable, homepage labelled as a datasheet, synthetic PDF or invented
model is used to bypass these limitations. The registry lists 0.1.0 as its only
released version at this audit. An upstream source-record patch and optional-model runtime prototype were prepared
outside the project with 24 focused tests; upstream typing and real browser
verification remain NOT RUN. No proposal has been released; the installed dependency and sibling checkout remain unchanged.
Catalogue completion remains **OPEN** until the blockers are resolved honestly.

The project coverage check requires every exact manual-inventory record,
including DNP, to be selected, explicitly blocked, or explicitly excluded with
a reason. No intentional exclusions are currently used. It rejects stale,
duplicate, conflicting and missing decisions, and requires blocker review when
the renderer version changes. A separate constraint prevents the Fenghua family
specification or its applicability gap from being promoted to an exact datasheet
or primary-confirmed claim.

Counts have different meanings: `selection.expect.records` and `.sources` lock
the **available corpus** (65 records, 135 sources), not the published subset.
This change selects **55 records and 117 sources**, with **10 explicit blocked
records**. Selected package previews rise from 27 to 30 because three existing
capacitor packages are now visible. The new 30-package expectation is a selected
preview count, not an inventory or qualification count. The compact Kingbright
LED owners remain selected. Monitor-only KEMET C0603C104K5RACTU remains an
unselected instrument candidate and does not replace global Murata bypasses.

Checks and actual results are recorded in the PR and retained review log. A green
coverage invariant proves that decisions are explicit; it does not waive the ten
publication blockers, sourcing work, electrical limits or physical gates.
