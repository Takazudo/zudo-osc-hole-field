# F3 copper-aware repair: bounded infeasibility

The one authorized source-only repair epoch completed with
`INFEASIBLE_IN_SEALED_FINITE_REPAIR_DOMAIN`. All **16,184** sealed poses were
screened. **U2312 and U2313 have no surviving individual poses**, even with the
other six movable footprints and exactly 29 conditional reconstruction segments
optimistically absent. Therefore no joint placement exists within this particular
finite model. There was no selected candidate, joint-assignment search, routing,
native run, copper reconstruction or adoption. No time or work cap interrupted
the screens. This is not proof of global or continuous placement impossibility.

## Frozen scope and geometry

Execution source: `4a1c3ec2ef1906ad5bfeb9a8f5ceef1f964d7b18`.
The [sealed contract](repair-contract.json) contains all input hashes and scope.
The same 24-reference F3/two-A closure is retained. Seven refs are movable:
C2312, C2337, C2338, C2339, C2340, U2312 and U2313; the other seventeen,
including U2306, remain fixed. Each movable ref has two fixed site seeds
(original and v1), x/y offsets from −2 to +2 mm at 0.25 mm intervals, four
orthogonal rotations and its original B.Cu face: 2 × 17 × 17 × 4 = 2,312
poses per ref. No adaptive seeds, expanded domains, retries or neighboring-group
changes were used. The 10 mm proximity target is only a preference. The
source-derived bypass-distance selection policy was never reached.

Screens use fixed courtyards with 0.35 mm separation, 0.30 mm edge allocation,
service/support/hook reservations, analytic service holes, fixed foreign pads,
and the complete retained accepted copper: **123,905 segments + 9,646 vias**.
All **133,902** indexed source-object hashes are authenticated, including 346
rule areas and five zones. The reduced input fixture's 64,747 copper records are
not the copper clearance authority. Via/SMD annulus exclusion applies regardless
of net, with the sealed 0.000001 mm margin; fixed circular drill envelopes also
retain the conservative 0.25 mm source-screen clearance regardless of net.
These source policies do not constitute fresh native DRC or connectivity proof.

The original dump SHA-256 is
`613a358b340962e2d1fb13cd898fe8a9558edcbf1a5d69cb93b6d2bd7629e97c`;
the accepted source PCB SHA-256 is
`fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10`.
See the [input recovery instructions](../../../../../../circuit/routing/epic-242/decision-pilots/terminal-access/local-breakout/region-stop/README.md).

## Exhaustive finite-domain result

| Reference | Screened poses | Individual survivors |
| --- | ---: | ---: |
| C2312 | 2,312 | 4 |
| C2337 | 2,312 | 337 |
| C2338 | 2,312 | 186 |
| C2339 | 2,312 | 109 |
| C2340 | 2,312 | 249 |
| U2312 | 2,312 | 0 |
| U2313 | 2,312 | 0 |

| IC | Fixed courtyard | Fixed reservation | Preserved foreign copper | Preserved via/SMD |
| --- | ---: | ---: | ---: | ---: |
| U2312 | 1,226 | 645 | 303 | 138 |
| U2313 | 1,194 | 654 | 312 | 152 |

These are first-refusal counts. All 441 U2312 and 464 U2313 poses which pass
courtyard/reservation checks fail retained copper checks. Capacitor survivors do
not imply a group fit or complete signal/return geometry. The epoch took
12.555 seconds, peaked at 459,880 KiB Linux RSS, and recorded 5,040 exact
foreign-copper pair checks and zero joint assignments.

[Recorded copper blockers](evidence/recorded-copper-blockers.json) identify
74 distinct preserved first-refusal objects across the seven domains, with exact
UUID, source span/hash, net/pad ownership and per-reference counts. They are
witnesses, not a complete conflict census per pose or a minimum cut set. U2312
has 51 and U2313 has 55 distinct recorded copper witnesses. All remain preserved;
none is permission to cut copper or expand the neighboring placement group.

## Object disposition and continuity

The [reconciliation](evidence/prior-conflict-reconciliation.json) retains all
67 prior conflict pairs, 57 distinct conflict objects and 18 pairs absent from
the reduced fixture. Thirty pairs involve original moved-pad contact objects.
The [63 directly affected object dispositions](evidence/object-dispositions.json)
classify **29 exact original segments for conditional reconstruction** and
**34 objects for preservation in place**, with **zero verified group transforms**.
Only those 29 segments were omitted from the optimistic geometry screen;
whole nets were never excluded. All original canonical bytes remain unchanged.

The 29 conditional plans retain original widths, layers, endpoint roles, source
hashes and net ownership, all 33 original fixture-pad contacts, and 39 complete
same-net segment/contact records, including midsegment T contacts and overlaps.
They are concrete obligations, not completed reconstruction or a continuity proof.
Fixture contacts cannot prove complete accepted-board native groups or zone
connectivity. Because no candidate exists, no transformed route or reconstructed
contact was produced.

Original demands remain BP_INT C2312.1 → U2306.5 and AGND C2338.2 → U2312.5.
The existing C2312.1 ↔ U2312.12 group (44 members / 42 copper objects) remains
unchanged. The +12V U2309.4 → C2331.1 and −12V U2309.11 → C2332.1 own-pad
blockers also remain unresolved. Preservation of source bytes proves neither
new demand completion nor continuity after a hypothetical move.

Independent review found eight inherited duplicate copper UUIDs among the
133,551 records (133,543 unique UUIDs), with distinct spans/hashes. All rows were
screened; none of the duplicate IDs intersects the 63 classified objects or the
29 relaxed segments. Any future classification touching them must use exact
source-object identity rather than treating UUID alone as unique.

## Execution and review evidence

[Execution receipt](evidence/execution-receipt.json) records the exact command,
source commit, single execution and raw output hashes. Exit zero means evidence
generation completed; it does not mean a candidate passed. The complete
[pose records](evidence/pose-screens.jsonl.gz) and [result](evidence/result.json)
are retained. The source was independently reviewed before execution.

[Independent result review](evidence/independent-review.json) passed: it derived
all 16,184 unique domain records and independently recomputed all 4,624 IC
rejection witnesses directly from source geometry, as well as all input seals,
object dispositions, reconstruction contact sets and the 67/57/18 reconciliation.
It did not rerun the search or introduce alternative poses. Its witness review
does not independently replay every preceding passing gate.

Validation passed: [seven focused unit tests](evidence/tests.txt),
[pnpm check](evidence/pnpm-check.txt),
[baseline input verification](evidence/baseline-check.txt), and
[pnpm circuit:check](evidence/circuit-check.txt). The circuit check remains a
manual inventory check (68 lines, zero declared placements), with no schematic
or placement binding. Baseline verification preserves 1,881 frozen inputs and
the two already-reviewed tooling replacements, 195 harnesses / 390 endpoints,
and inherited accepted JL117/JR129/core1402 receipts with DRC/parity 0/0.
Those accepted receipts are not fresh native evidence for this repair.

Full regeneration, native whole-chain/cross-path verification, refill and
full-warning/eligibility gates were **not run**; full regeneration includes
unadmitted native operations. No native capacity was used, no PR was merged,
and no canonical board was changed. After the reported environment disconnect,
Git/filesystem/tool access and retained evidence were verified without a rerun.

## Stop and next decision

This authorized epoch is complete. Routing admission remains blocked by the
empty IC domains and unresolved continuity obligations. The next useful step
is review of the exact retained-copper witnesses and ownership/contact plan
before any explicitly revised repair contract. No further pose search,
reconstruction expansion or neighboring-group movement is implied or authorized
by this finite-domain negative result.
