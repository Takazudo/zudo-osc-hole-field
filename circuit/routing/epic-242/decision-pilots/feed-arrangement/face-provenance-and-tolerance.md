# Face assignment and tolerance correction

The F/F assignment is a **provisional modeling choice**, not a discovered fixed
user requirement or a connector restriction. The prior request for an owner
permission decision was too restrictive. Source proposal work may continue under
the existing epic authorization. Architecture adoption remains a separate gate.

## Exact provenance

- Epic #242: “Core ownership/position can move under the contract; new feed
  interfaces use new explicit identities.” It also says that no “panel,
  electrical-limit, protection, factory-assembly or native-acceptance constraint
  is relaxed.” These obligations remain in force.
- Issue #247 directs the source owner to “Identify new main feeds/connectors/stars/
  decoupling, their exact identity or explicit candidate gap, layer/plane
  assignments and placement envelopes.” It requires “Factory-complete soldering”.
  Neither issue prescribes F/F for the new internal feed. Current #242 has no
  comments; the two current #247 comments request a redesigned row/corridor or
  explicit service/strain-relief alternative, preserving net order and cut budgets.
- `design/partition/core-split/power/build.py:268`, introduced by
  `49db18568844d6ca654f70838429415ca7cfdffe`, emits the literal
  `'side':'F.Cu'` for both `('SRC','KA')` and `('DST',board)`. The adjacent code
  emits `'global_origin_mm':None, 'installed_fit':'NOT RUN'`. This is the exact
  source of the F/F generated contract.
- `power/input.json/new_feed/interface`: “six factory-soldered wires between
  custom copper lands; no orderable connector selected or needed for this
  candidate”. Its placement status is “LOCAL ENVELOPE ONLY”. There is no keyed
  connector or supplier requirement forcing that face assignment.
- The older `partition-input.json/load_distribution/pad_side` says
  “B.Cu on J/P; F.Cu on K”. That concerns the existing JL/JR/P-to-K main feeds.
  Their identities, lands and non-core poses remain frozen. This proposal changes
  only the new CS247 KA-to-KB lands; it neither moves those old lands nor flips KA.

Issue sources: https://github.com/Takazudo/zudo-osc-hole-field/issues/242 and
https://github.com/Takazudo/zudo-osc-hole-field/issues/247, including current
comments, were read during this correction. The generated power producer remains
unchanged so its historical evidence stays reproducible; a reviewed source
contract revision is an integration dependency, not a new user-permission gate.

## Assembly and service meaning

F.Cu is the board's front copper face; B.Cu is its back. In the proposed stack,
KA's back faces KB's front. Moving the **new KA feed lands** to B.Cu makes both
ends face the inter-board gap. The wires can then connect through that gap instead
of escaping around an uncut KA edge from its front face. Existing circuitry,
panel, old harness identities/pin order, source/protection boundaries and retained
copper are not changed by this source proposal.

Factory assembly must solder those new KA lands from the back before closing the
stack, inspect those joints, and mount strain relief independently of solder.
The feed remains factory-soldered; this does not introduce a user connector or
user soldering step. KA collets stay on its fixed carrier; KB collets move with
its carrier through the proposed 10 mm withdrawal. Full removal is not established
by that limited travel. Common frame joints, assembly sequence, tool access,
insulation and retention still need engineering qualification.

Recommendation: retain KA B.Cu → KB F.Cu as a reversible candidate and reconcile
the power/mechanical source contract through its existing owners. **No question
to the user is needed for this design proposal.** A later architecture choice
requires the epic's measured evidence, not permission inferred from positive
nominal geometry.

## 0.145 mm is not a qualified physical margin

The saved Alpha5859 manufacturer specification gives insulation OD
`0.095 +/-0.007 in` and bend radius `10X Cable Diameter`. The model already uses
the upper OD0.102in =2.5908mm and radius25.908mm. Do not add that same OD tolerance
again. The source PDF is locked by SHA256
`ff9da35e471778f26ffc849985f73e53516d8c6cc60d5505aa96f7d446a5be87`.

However, no clamp material/process, bore/outer dimension tolerance, datum/position
tolerance, board warp/stack tolerance, carrier stiffness, thermal motion,
assembly repeatability or wire-shape repeatability has been selected or bounded.
The free Bézier is a kinematically possible curve family; endpoint clamps alone
do not prove a real wire will follow that family during service. Passive shape,
forces and any required intermediate guides remain unqualified.

The0.145325mm lower bound is therefore **nominal geometric separation only**.
A robust physical claim needs

`verified clearance >= 0.145325 - total worst-case relative closure > required service clearance`.

As an illustration, not a sourced process tolerance, two independent0.10mm
position errors closing the same gap sum to0.20mm and erase the guarantee by
0.054675mm. Even with zero required service clearance, two equally allocated
errors alone must each stay below0.0726625mm, leaving no budget for all the other
effects. The nominal collet-to-board gap is smaller still,0.113821mm. A positive
physical margin cannot presently be asserted; an RSS estimate or ignoring
correlated/service motion would not close the requirement.

Continue source engineering to select a process/datum/tolerance budget, increase
clearances or constrain the wire path as necessary, and then recompute worst-case
sweeps. No manufacturing tolerance values are invented, and no fabrication,
physical-fit, assembly-load or thermal qualification is claimed.
