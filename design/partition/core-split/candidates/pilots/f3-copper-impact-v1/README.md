# F3 local-site copper-impact decision

**Recommendation: retire this local proposal and preserve the accepted copper.**
Do not approve reconstruction for the selected group: it has three courtyard
overlaps and two pad-clearance failures before any copper is changed. This is a
rejection of one proposal, not proof that every pose or the entire site is
impossible. A different site or revised joint placement/copper contract requires
an **owner decision**. No such work is started here.

The requested bounded source-only investigation is complete. One group was
selected from already-screened v2 records and censused once; **no new pose search,
domain expansion, alternate selection, cuts or native work** occurred.

## Concrete proposal and placement prerequisite

The [frozen selection](selected-pose.json) ranks eligible saved records by squared
XY distance to the v1 pose, then angular change and deterministic coordinates.
IC eligibility means a saved copper refusal after fixed courtyard/reservation
checks; capacitor eligibility means a saved individual pass. This makes a
reproducible local-site impact probe, not a jointly valid placement. All 17 other
closure refs, including U2306, remain fixed. Physical coordinates are in mm:

| Ref | X | Y | B.Cu rotation |
| --- | ---: | ---: | ---: |
| C2312 | 213.64 | 264.46 | 0° |
| C2337 | 234.75 | 237.57 | 90° |
| C2338 | 235.25 | 246.59 | 90° |
| C2339 | 212.25 | 240.46 | 180° |
| C2340 | 212.25 | 250.48 | 180° |
| U2312 | 235.45 | 242.58 | 270° |
| U2313 | 213.20 | 244.47 | 90° |

The [single joint check](evidence/placement-checks.json) found:

- C2337/U2312 courtyard overlap **0.6336 mm²**, C2338/U2312 **2.5536 mm²**,
  C2339/U2313 **2.1320 mm²**; all require 0.35 mm separation.
- C2338.2/U2312.11 pad gap **0 mm** and C2339.1/U2313.11 **0.11 mm**,
  below 0.25 mm. These are conflicts between moved parts, not neighboring cells.
- C2340/U2313 center distance **6.08462 mm**, exceeding its conservative
  original-distance policy of **5.69 mm**. This is a proposal policy, not a newly
  invented owner requirement.
- C2312.1 is **29.97861 mm** from fixed U2306.5; U2312.12 is **9.83003 mm** away.
  The 10 mm proximity preference is not achieved for C2312 and is not a hard
  owner constraint. No fixed reservation, edge, analytic hole, fixed foreign-pad
  or fixed-drill failure was found in the source screen.

No second selection was made to repair these findings. A joint-legal proposal is
still required before conditional copper reconstruction can become executable.

## Exact copper impact and neighboring ownership

All **133,902 accepted object hashes** were authenticated; all **133,551 segment
and via rows** were considered without the previous29 exemption. The complete
selected-pad conflict census has **55 pairs**, not merely the first witnesses.
Together with **33 old moved-pad contact pairs**, it identifies **52 directly
affected objects: 46 segments and 6 vias across 23 nets**. This includes all
29 prior segment obligations plus **23 additional objects (17 segments / 6 vias)**.

[Every affected object](evidence/affected-objects.json) has its UUID, exact source
span/hash, original width/layer/endpoints or via center/drill, full impact pairs,
source-contact topology and conditional disposition. Source spans/hashes preserve
the eight inherited duplicate-UUID distinctions; no UUID-only object collapse is
used. [Full net/pad ownership](evidence/net-ownership.json) is retained separately.
The additions for this one pose are:

| Net | Added segments / vias | Endpoints outside the 24-ref placement closure |
| --- | ---: | --- |
| F3 HP_PLUS | 5 / 0 | R2356.2, R2357.1 |
| F3 RES_CONTROL_CLAMP | 3 / 2 | D2305.3, R2385.2 |
| F3 REFN5 | 2 / 1 | R2302.1, RV2309–RV2312.1, U2308.7 |
| F3 Cb5b1dc_SUM | 2 / 0 | C2307.2, R2333.2, R2334.2, U2311.2 |
| F3 RES_NEG4 | 2 / 0 | D2321.2, D2322.1 |
| F3 EXPO_REF_TRIM | 1 / 0 | R2352.2, RV2308.1 |
| F3 RES_CONTROL_SUM | 1 / 0 | None; endpoints within closure |
| F3 RES_CONTROL_INV | 1 / 0 | None; endpoints within closure |
| F2 C2b474d_W | 0 / 1 | J900221.3, R2223.1 |
| AGND | 0 / 2 | Shared return; full ownership retained in evidence |

For example, F3 Cb5b1dc_SUM segments
`29353aca-a4ee-5daf-a20c-b308b604f41a` and
`5423ca56-8888-5228-a12a-1e6082612aad` cross selected U2312 pad clearance.
F2 via `2189a99b-0752-520c-ae1e-91767560b651` interferes with U2313.13/.14;
its ownership is J900221.3/R2223.1, so this is demonstrably beyond an F3-only
copper change. AGND vias `0e00115c-875b-5991-b5b3-6914fd3d6635` and
`4a55a332-14d5-59a0-a378-fc1ec898c08b` interfere with U2313.8/.10. The latter
is a same-net via/SMD exclusion, so same-net exemption cannot resolve it.

These 23 additions are **directly affected objects for this pose**, not a minimum
cut set, proof of sufficient reconstruction, or globally necessary scope. The
exact-object continuation described here would extend copper ownership beyond
the prior29 to these23, while keeping neighboring footprints fixed. A minimally
sufficient scope change has not been established. It cannot be approved as sufficient: the selected joint pose is invalid,
and any later valid pose could change this list. No physical scope expansion is
justified by the current evidence.

## Continuity contract and shared rails

The [conditional reconstruction proposal](reconstruction-proposal.json) gives
one action/port obligation per exact affected object. The 52 objects have **99
same-net copper contact records** and connect to **56 distinct preserved frontier
objects**. All full-segment contacts, including midsegment T branches/overlaps,
are recorded; 33 original fixture-pad contacts retain pad UUIDs and destinations.

Any future segment repair must retain width/layer, every branch and all source
connections while reterminating moved pads. A conflicting via would require a
new exact-net transition preserving its 0.6 mm land, 0.3 mm drill, six-layer span
and all contacted branches. Replacement centers, split locations and routes are
**not designed**. No object has been cut or reconstructed. Native connected
groups, accepted-board pads missing from the fixture, zone-mediated contacts,
refill and all warning/eligibility gates remain unresolved.

The prior29 already include five +12V and five −12V contact segments, and one
AGND contact segment. This pose adds two AGND vias but no new supply objects.
Shared-return/supply obligations therefore cannot be isolated by calling this an
F3-only job. Full source net ownership includes 1,756 AGND, 575 +12V and 406 −12V
endpoint refs outside the closure; these are **continuity review scope**, not
instructions to reroute thousands of refs. All five original zones are retained
as [explicit recheck obligations](evidence/zone-recheck-obligations.json).

Original BP_INT C2312.1 → U2306.5 and AGND C2338.2 → U2312.5 demands remain.
The existing C2312.1 ↔ U2312.12 group and original U2309 positive/negative rail
access blockers remain unresolved/preserved as before. Source-byte preservation
is not proof of reconstructed continuity or demand completion.

## Decision comparison

| Choice | Concrete cost or scope | Assessment |
| --- | --- | --- |
| Reconstruct this local proposal | 52 direct objects; neighboring F3 cells, one F2 via, shared return and supply continuity; unresolved joint placement and distant C2312 | **Reject.** Copper edits cannot repair its courtyard/pad overlaps. Do not grant cuts or whole-net authority. |
| Retire this local proposal and leave canonical placement/copper unchanged | Zero copper edits; original open demands and rail blockers remain | **Recommended now.** Preserves accepted work without spending another search. |
| Commission a different site or revised joint-placement/copper contract | New bounded scope, sensitive-group and owner review; extent and routability not yet measured | **Owner decision required.** No alternative site, neighboring footprint move or new search is selected or authorized here. |

## Reproduction and checks

Census source commit: `511447010a84b5a1a0e8a9eba0deab03481d2d30`.
Its inputs are sealed in [input-seals.json](input-seals.json), including the
v2 retained pose records at integration `905c323da7fcce9230b2fae0e37923f970ec01c1`.
The [receipt](evidence/execution-receipt.json) retains the exact command, one
execution and raw output hashes. Elapsed 5.152 seconds; peak Linux RSS 601,184 KiB.
The original dump is recovered using the prior [v2 input instructions](../f3-integrator-cluster-v2/README.md).
Compressed owner source records retain the raw hash over decompressed bytes.

[Source review](evidence/source-review.json) passed before execution. Independent
[result review](evidence/result-review.json) verifies the complete census and
contact frontier alongside the [summary](evidence/summary.json).
`pnpm check`, frozen-baseline verification and pre/post `pnpm circuit:check`
passed. The circuit validator is still manual68/zero placements with no schematic
binding. Fresh native DRC/parity, full regeneration, original-group verification,
refill and full-warning/eligibility gates are **NOT RUN**; native work was
explicitly excluded. All canonical boards, fixed panel coordinates, harness
identities, source nets and noncore poses remain unchanged. No PR merge or issue
closure is part of this proposal.
