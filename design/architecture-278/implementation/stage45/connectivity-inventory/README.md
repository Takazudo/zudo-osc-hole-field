# Stage45 — B1/B2 reuse and unfinished JL connectivity

The accepted B1/B2 studies reuse their circuit, physical pin assignments, library
packages and nonplacement BOM metadata. They do **not** yet constitute identical
manufactured or interchangeable PCBs. All **117 inherited JL opens remain**.
Two bounded attempts at one additive ground repair found no path; no candidate
board was written, no copper was applied, and no canonical adoption is proposed.

The starting PR #287 head is `7431cfa5cc515d897726645bd55dc4f3407cea95`.
The accepted Stage44 board remains SHA256
`d1f79d02ac20ecca28591a1332fd217603ac53ce114bcd4aa1290f78ba3d2b73`.
Stage42 B1, Stage44 B2, all historical evidence and parent PR #286 at b58068f are
preserved. This stage adds an actionable inventory and a failed routing experiment.

## What the 117 opens mean

| Native missing edges | Affected nets | Disposition |
|---:|---:|---|
|68|60|Unfinished local JL routing on nets that also have a harness interface|
|35|29|Unfinished local JL signal circuitry without an interface contact|
|14|1|AGND split into 15 native components|
|117|90|No intentional local open or waived failure|

An interface-associated net may have three components, including two disconnected
IC groups. The 68 count therefore does not mean 68 direct connector-to-IC links.
It is the sum of component-count minus one over those 60 nets. Routing topology
is not uniquely determined by this count.

[OPEN-NETS.md](OPEN-NETS.md) gives every net and disconnected pad group.
`inventory.json` adds hashed/native and semantic names, per-pad block/value,
actual panel XY and layers, complete membership fingerprints, the closest
cross-component pad pair, and every associated JL header/mate contact. All mate
pins are checked against both partition assignments and the current board
netlists. The intentional wire between two boards is separate from missing
copper *within* JL. No new harness, contact assignment or electrical crossing is
introduced. Existing GH entries describe the retained draft, not a new choice
or a freezing of the owner's standard-connector investigation.

`open-partitions.json` preserves the complete 2,657 stable native object keys and
metadata in the 90 affected nets. It is an extracted subset of the previously
accepted native snapshot, not a fresh connectivity calculation. The full ignored
snapshot hash is bound to Stage44's committed local-artifact ledger. Export
replay checks the original snapshot and board hashes; normal source replay works
without those large local files. A source check cannot independently recreate
native connectivity from hashes alone.

## What B1/B2 reuse establishes

The generated comparison verifies 36 package pairs, 115 physical contacts per
cell and a bijection across 33 native net pairs (24 private, four shared rails,
five NC nets). Five fixed front packages per cell remain the corresponding four
jacks and indicator: J109/J309, J209/J409, J110/J310, J210/J410, D109/D309.
Every package/contact mapping and actual B2 pose is exported. B1 coordinates are
the exported B1+34mm pose minus 34mm X; these are actual accepted-study poses,
not stale placement properties.

Two relative poses differ: R3204 has the accepted +0.15mm Y clearance adjustment;
R3209 retains its canonical B2 site instead of the translated B1 site. These
local repairs and site-specific copper invalidate a claim that the accepted
layouts are exact translated copies. The three retained external B2 supply vias
are exported by occurrence geometry and their foreign track contacts:
`06b2530e-ef31-5ad6-b94a-011fdc6dd3ee` (+5V),
`37554070-fa4e-53f3-914c-e0c6853be413` and
`7a00c49a-6561-587f-bc28-376cc5279391` (+12V).
They remain anchors, not B2-owned copper eligible for blanket retirement.

Both cells still occupy one full JL substrate. Stage39's failed coplanar seam
and rear23 header/support reservations remain failures; Stage43's exact-copy
failure remains historical evidence. A common removable board would additionally
need a feasible outline, mounting/access geometry, an interchangeable interface
contract and a layout compatible with both sites. This stage neither supplies
those nor proves a different common-board design impossible. Circuit/BOM/library
reuse is useful but is not a per-board manufacturing cost or interchangeability
result. R3214's exact MPN, jack manufacturer/CAD bridge and inventory placement
binding remain unresolved; no supplier or availability qualification is added.

## Bounded repair experiment and first failures

The independent scope review proposed AGND pad R8270:2, panel
(170.31,83.19), toward the already connected R2305:2 at (170.31,79.09).
Their 4.10mm center separation is only a selection metric. R2305:1 lies between
them on a different net; a direct line would be wrong. The shortest signal
pad-pair gap is about 13.787mm on /M5A/1_PROTECTED, itself a three-component net,
so it was not treated as a trivial missing stub.

The existing native grid dump was taken from the pinned Stage44 board under the
shared resource guard. Two proposal searches retained **all obstacles** and
restricted only the AGND routing source/destination to the named pad UUIDs.
Both used native bounds X267..274, Y127..135mm (panel X167..174,Y77..85), 0.05mm
raster, 0.25mm clearance, 0.40mm ground track and 0.70/0.30mm through vias.
First B.Cu alone, then F.Cu/In2.Cu/B.Cu, returned NOPATH with no copper proposal.
Both guard verdicts are FAIL (real routing search failure, not memory deferral).
Evidence preserves both scripts/configurations, searches and logs. No attempt
was applied and no new DRC/parity/refill execution is claimed. These bounded
negative searches do not prove the board or even this connection unroutable.

## Smallest next implementation and decision

Recommend retaining the current shared-JL/interface architecture for the next
bounded repair study, with **no canonical adoption**. The concrete next task is
an obstacle-reviewed escape from R8270:2 to the existing main AGND component:
inspect its local pad/track/zone clearance and compare a via-to-plane escape with
a wider routing corridor, before increasing search bounds. Preserve the failed
7x8mm trial. A different single ground island is a fallback only after stating
its exact source/destination and affected partition. Do not start a full-board
routing campaign or move panel hardware to improve a routing score.

Acceptance for that next disposable repair:

- No existing footprint, pad ID/net, copper occurrence, rule area, zone definition,
  schematic, library or project setting changes; only reviewed AGND copper added.
- Exactly R8270:2's singleton merges into the existing main AGND component:
  117→116 opens, 15→14 ground components; every other native partition unchanged.
  B1/B2 private closure and retained power connectivity must remain intact.
- Zero new rule/parity errors; no new uncapped warnings; report the existing
  capped silkscreen limitation. Native process success alone is insufficient.
- Refill/save/reload settlement and independently loaded fresh-copy evidence
  agree on exact board hash and complete occurrence-aware memberships.
- Independent final review covers the final substantive changes. Only then can
  a disposable repair be accepted; any canonical adoption remains a separate
  parent/owner decision.

The minimal architecture decision is whether to continue the shared-substrate
route above or reopen the separate-common-board architecture with explicit new
outline/support/interface work. This stage recommends the former and has not
silently made the latter. Standard readily sourced connectors and identical PCB
cost savings remain goals, not achieved claims.

## Physical boundary

No physical results, analog stability, current limits, wire flex limits, retention
stiffness or manufacturing readiness are established here. Existing cover/service,
registration/bow, supported withdrawal, 50N retention, connector fit and protection
gaps remain. An approved unpowered mock-up should record actual part identities,
connector pin-to-pin continuity/NC isolation, board registration and bow, mating
and removal sweeps, tool access and support throughout withdrawal. Reject wrong
mates, crossed contacts, occupied-volume intersections, unsupported unplugging,
or violations of the retained drawing tolerances. Obtain actual wire static and
repeated-flex limits and material/load evidence before qualifying cable bends or
retention. These measurements do not waive the source failures above.

No manufacture, order, energization, release, deployment or merge occurs here.
