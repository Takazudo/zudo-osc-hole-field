# Independent cross-board review of new direct-mating candidates

The direct-study's per-card geometry pass does **not** survive the retained middle-board population. Both best variants have four same-middle-face reservation conflicts. Neither is a mechanically qualified candidate, even before unresolved other-function volumes or overlength electrical paths are considered.

This independent source screen reads `direct-study-report.json`, the actual assembly placement, all438 locked-hardware proxies and the separate stage3 reservation report. It never executes the direct-study search, native KiCad or canonical generation. Reproduce `python3 scripts/architecture278/implementation/stage3_direct_mechanical.py --check`; four focused tests verify face classification, distinct variant poses, five removal obligations and rejection of a local-card-only clearance claim. The generated `direct-mechanical-report.json` binds exact input/checker hashes and all finding coordinates.

## Two geometry variants screened

Both use five44×238 mm cards at x2/48/94/140/186 mm, a local DIN centre[8,105] mm rotated180°, the baseline middle50/core69.2/cover105 mm stack, and the40 mm removal stroke. The baseline best uses card origins at y45; bypass-refined uses y30. These are new outlines/cluster/bank proposals, not another permutation of the old fixed slots.

| Finding | Baseline best | Bypass-refined best |
|---|---:|---:|
| Reported maximum path allocation |334.018 mm|336.199 mm|
| Overlength endpoint paths |38|50|
| Same middle rear-face DIN/shared reservations |4|4|
| Opposite-face DIN/GH projections |14|14|
| DIN nominal through-contact points inside GH courtyards |23|16|
| New DIN/all438 hardware XY projections |57|59|
| Old K intersections during withdrawal, if K retained |5|5|
| Qualified-free geometry queries |0|0|

Counts are categories, not additive physical-collision totals. In particular, through-contact findings can occur within the opposite-face projection set.

## Same-face source conflicts: reject the current combination

The O2 middle DIN body reservation intersects **U1601, C1601, C1603 and R1615** on the shared-reference island's rear face. The baseline O2 DIN reservation is x48.5..63.5/y100..200 mm; the bypass-refined reservation is x48.5..63.5/y85..185 mm. The retained shared island occupies x50..95/y135..172 mm, with these four actual package courtyards inside the overlap.

These are source-reservation conflicts on the same physical PCB face, unlike a front/rear projection that might be separated by the substrate. They reject this combined arrangement at its stated envelope model. Exact native and physical solids are still unavailable; this review does not pretend to have measured contact or package interference. A future candidate must either place the complete shared local reference/feedback/bypass group outside the new bank reservation or change the bank/card arrangement, then recalculate all shared-source paths and local loops. Moving only an inconvenient passive out of its source cluster is not an adequate resolution.

## Opposite-face and through-contact findings

All85 retained middle headers were included. Fourteen new DIN rear-body/GH front-body projections remain in each variant. Different PCB faces can separate their bodies, but DIN is through-hole: exact pad/drill/tail and mounting-land exclusions still matter. The screen therefore also enumerates all96 DIN nominal contact positions at2.54 mm pitch under the selected180° rotation. It finds23 baseline and16 refined contact points inside a GH courtyard.

A contact-centre/courtyard intersection is a source exclusion finding, not a fabricated exact drill-size or solid-intersection measurement. Qualify actual through-hole pad/drill/tail geometry against GH signal and hold-down lands before treating opposite faces as sufficient clearance. Retain exact pin numbering and both mating faces when reassigning bank contacts.

The additional57/59 new DIN/hardware XY projections remain unresolved in Z, separate from the stage2 assembly's350 original hardware projections. The new bank has been screened against all438 proxies, but proxies are not complete body/terminal/latch/cable/tool solids. No claimed freedom comes from leaving these out of the per-card model.

## Service and other-function occupancy

The other28 function volumes remain explicitly UNKNOWN in the candidate stack. All five new card removal sweeps intersect the old K board's100..101.6 mm plane if that board is physically retained. This is a separate conditional scenario; the source audit does not silently adopt, move or delete K to clear space. The reservation report explains why an old source placement and an empty new candidate drawing cannot establish whole-instrument capacity.

The narrow-card handles introduce another service detail: their centres are16 mm apart, while the inherited finger reservation is20 mm in diameter. The two simultaneous grip envelopes overlap by4 mm in X on every card. This rejects reuse of the old simultaneous two-grip assumption, not every possible service solution. Define a different handle/grip/tool arrangement with actual access, force and retention evidence. A one-handle pull or tool-assisted extraction must be explicitly designed, not inferred from a footprint drawing. Handle envelopes also extend beyond the card's lower outline; they require actual enclosure/open-cover workspace checks.

## Required next bounded source changes

- Resolve the four same-face shared-island/DIN reservation conflicts while preserving all30 shared packages, reference/feedback topology and supply bypasses.
- Reconcile all96 DIN through-contact pads/tails, flange fixings and keying with the85 middle headers and new support/power infrastructure; exact opposite-face geometry cannot be replaced by a centre-point pass.
- Replace the inherited simultaneous grip assumption with a coherent new-card service geometry and procedure, retaining power-off/discharged removal without routine middle-board removal or owner soldering.
- Complete conservative other28 function reservations before using the new column space. Unknown space stays reserved. Recompute complete electrical path/return/capacitance budgets after every geometry change; both current best variants already exceed300 mm.

None of these is a new owner-approval question within the authorized engineering/source scope. Adoption, exact-run native admission, fabrication/purchase and energization remain separate. Native ERC/DRC, installed mechanical fit, stiffness, force, electrical/physical service and full Stage1 acceptance are **NOT RUN / OPEN**.

## Reviewed source hashes

Independent mechanical reviewer, 2026-10-15. This receipt applies to these exact bytes; future geometry changes need a new screen.

- `scripts/architecture278/implementation/direct_study.py`: `c4ce0b23f01d4ecd6b6aef72ecde74fb082eae78d7294722b97376a14b814fa0`
- `design/architecture-278/implementation/direct-study.json`: `68c0972522874b3cd7981a4c0da3699a049f55baca8569eb3203735ec0211f7e`
- `design/architecture-278/implementation/direct-study-report.json`: `d2d8fe01d15bafdb555c09eb5d354bb3d1e178e533134849f143a2d3722ef15f`
- `design/architecture-278/implementation/assembly-report.json`: `2d8f9cbb7316011c8885fe46c1e2a785a7afb07f8ec4efdb5630bde124c498b0`
- `design/architecture-278/implementation/assembly-mechanical-review.json`: `b9ad1cc96ae07c76490de6fcec9873a1cf1663cb1f8dee63d7a36be6cb60c4dc`
- `scripts/architecture278/implementation/stage3_reservations.py`: `5eeb77427603958d44906daeef1a6b1e6b8dfb5a22a0cafc47d68715213b9395`
- `design/architecture-278/implementation/stage3/reservations-input.json`: `8b5a063e6f901b6c10024d03cda5012a50ee71c95fbd37db03639c8a54a5c856`
- `design/architecture-278/implementation/stage3/reservations-report.json`: `de8998fe40aacf5145bf236cc9276be3c8acd00f94b0e71efa577926bc68944d`
- `scripts/architecture278/implementation/stage3_direct_mechanical.py`: `094561e5ef7df3cebdbea3fac1055afa962074d24d87f7132cfc0be55c156be9`
- `design/architecture-278/implementation/stage3/direct-mechanical-report.json`: `5b701e2ae4b72654c18203546b5495602bc1b1bc1d47f1866ab773e591450e24`
- `scripts/architecture278/implementation/test_stage3_reservations.py`: `847ad51cc97358ed9ccb5f24535794949c90ee18ce0570871121021cd1fad4dc`
- `scripts/architecture278/implementation/test_stage3_direct_mechanical.py`: `8f03ff108d0fe53eed0767f5a8003720a762be40448964f7e8f09ef6d38f4b7a`
