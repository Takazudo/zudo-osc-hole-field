# Two-core G1/G2 source feasibility continuation

Input: integrated `9e0aceda2f1d55052a8c9c03f958e8d93271a81c`, #253 decision matrix and current integrated #247 contract. Branch `topic/246-feed-feasibility-20261011`. Outcome: **PRECISE GEOMETRIC BLOCKER UNDER RETAINED CARDINAL ENVELOPE/RESERVATION MODEL**, not architecture selection. Accepted K1402 remains incumbent. No canonical board or power-lane source was changed.

## New result, beyond the prior comparison

`feasibility.py` uses all actual #245 serialized F-side footprint courtyard polygons (each checked to be a rectangle), the 0.35 mm requirement, copied support/tool/loom reservations and KA-only protection. It tests a whole 91×34 mm endpoint row-plus-corridor projection: 91×6 terminal row and separate 91×28 corridor. It compares horizontal/vertical orientations (180/270 have the same footprint projection), with a 1 mm grid for an interpretable least-occupied example and a **continuous translation event sweep** for feasibility. Feasibility events are every inflated obstacle/domain X boundary; forbidden open Y intervals are merged. Touching inflated obstacles retains the full gap. The two rectangular origin domains implement the notched outline and 0.3 edge allocation.

| Retained source plane | Horizontal continuous event origins | Vertical | Meaning |
| --- | ---: | ---: | --- |
| KA / two-A | 0 | 0 | Complete endpoint envelope cannot be placed under these retained masks |
| KB / two-B | 24 | 0 | XY openings exist; not a complete paired feed or Z/service solution |

The best horizontal KA grid attempt is `[167,43,258,77]` mm: row origin (167,43), angle 0°, then corridor Y49–77. It conflicts with **JR-K-2-K, JR-K-3-K and JR-K-4-K tool reservations**. The best vertical attempt `[144,84,178,175]` conflicts with **C303 and TP990026/TP990028/TP990030**. Exact inflated obstacle rectangles and intersection areas are retained in JSON, not hidden in aggregate occupancy. A concrete KB XY opening is origin **(8.45,134.52), 0°**, terminal row to (99.45,140.52), corridor to (99.45,168.52). The SVG displays these explicitly as unpaired examples, not connected conductors. No independent pad/track/via clearance is claimed: KA already fails before adding copper obstacles, and the permissive KB result remains subject to those checks.

All 191 inherited tool passage reservations are retained as obligations, including those needed through the other core. Reallocating a tool axis, changing assembly sequence or allowing a corridor to share service space might change the result, but requires a reviewed lifecycle/access contract. This screen does not silently release them as “empty area.” Components, supports, routing/copper and complete pin identities cannot be moved by this lane.

## Edge escape and stack bounds

The retained proposed enclosure is `[-2,-2,320,300]` in XY. With identical uncut KA/KB outlines, all maximal cardinal boundary-coordinate empty rectangles outside KA are enumerated. **None contains a 91×28 corridor projection.** The side margins are 6 mm, top 10 mm, bottom 8 mm; the lower-right enlarged notch is 62×54 mm and also cannot hold a cardinal 91 mm length. Ignoring EXT/supports is generous: those obstacles cannot make an excluded escape fit. Arbitrary-angle corridors, split rows or redesigned envelopes are outside this proved model, not declared impossible.

Current 26 pitch leaves 24.4 bare PCB-face gap: **3.6 mm short** of the 28 corridor, or **8.6 mm short** when the opposing 5 mm body allowance is preserved. Translating both boards deeper does not help. Minimum bare-only pitch is 29.6; minimum body-allowance boundary is **34.6**, giving KA−100 / KB−134.6 / enclosure154.6 mm with the old 13.4 rear clearance. These are zero-contact-margin bounds, not tolerance-ready proposals or permission to enlarge the case. Wider pitch does not remove the KA XY blocker.

No aperture is adopted. At 26 pitch an overlapping passage would cut KA material and would require every affected footprint/pad/copper object and mechanical load path to be re-audited. Current source masks already prevent a complete cardinal placement without such obligation changes. Therefore no six-wire route or supported extraction can be certified. Alpha Wire 5859 maximum OD 2.5908 / minimum bend 25.908 and the 110 mm cut ceiling remain binding; neither 110 nor the 10 mm cut allowance proves service slack. No desoldering, live internal service or connector substitution is assumed.

## Strict courtyard gaps

All **40** listed same-face violations are real serialized **0.349999 < 0.35 mm** gaps, not waived by epsilon. The artifact gives each capacitor/IC pair, exact bounding boxes, a **1 µm capacitor shift away from its paired IC**, proposed origin and all affected pad UUID/net identities. Applying all 40 deltas in the comparison yields minimum checked same-face gap **0.350999 mm**, zero new strict conflicts and all 40 within the retained outline. Source polygons with unsupported nonrectangular geometry cause failure rather than silent bounding.

These deltas are **not applied** to any accepted source, footprint, pad or copper. #245/coordinator must decide the whole-package placement update and connected-copper replay/preservation strategy, then independently validate native connectivity/clearance. A tiny displacement is not permission to leave attached copper stale. Sensitive bypass locality remains a review obligation; no Ref, face, rotation, net or physical part is replaced.

## Reproduction and next coordination

```sh
PYTHONPYCACHEPREFIX=/tmp/osc246-feas-cache python3 design/partition/core-split/mechanical/feasibility.py --check
PYTHONPYCACHEPREFIX=/tmp/osc246-feas-cache python3 -m unittest discover -s design/partition/core-split/mechanical -p 'test_*.py'
```

Artifacts: `generated/two-core-feasibility.json` (input/tool hashes, all 40 deltas/pads, search origins/blockers and bounds), `generated/two-core-feasibility.svg` (dimensioned source view). Existing comparison outputs are unchanged. The focused tests cover strict corrections, continuous sub-grid openings, cardinal negative cases, nonrectangular rejection and determinism. Independent source review confirmed the sweep, all 40 corrections and all 24 serialized KB origins. These are numerical/source checks only.

#247 task `01a12973-8a2a-7569-adb0-d848f9071097`: next source change must specify whether the 91×6 row /91×28×28 service block is indivisible, or supply an evidenced alternative terminal arrangement/bend/support envelope and revised 110 mm service budget. #245/#253 and coordinator `01a12972-5482-766c-97c0-fb9a182940a4`: decide which exact service obligations/placement groups can move, or retain this blocker; own the 40 proposed pad moves and any copper replay. No architecture selected, no global native slot requested. Physical fit, arbitrary-angle/tilted arrangements, exact solids, extraction, return/loss/fault qualification and native acceptance remain open.
