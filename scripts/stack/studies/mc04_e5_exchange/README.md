# One E5 room-only exchange feasibility pilot

This implements the independently admitted exchange disposition after the E5
blocker diagnostic, not a new unrestricted placement search. Diagnostic receipt
`f9f21bf97ad346268762cd7a7be3c00e/result.json` has SHA-256
`a932d3693b9b64e1527599ac111889082dde113ad164cebe717c24b31785ca46`.
Its unique accepted-body-only point is U4527 offset index214, radius2.25mm,
(+1.591,-1.591). All16 hits there belong to U4517 and R4577. The pilot validates
that exact receipt and reproduces that one point's complete blocker IDs before
enumeration; it never reruns the7,203-point attribution audit.

U4517 occurs at retained replacement row85, before unresolved U4527 row89.
Changing this previously inserted body is a genuine extra freedom over that
historical failed search. R4577 row377 was placed later: it obstructs the final
conservative scene, but is not claimed as the historical cause.

## Exact geometry scope

Only U4527, U4517 and R4577 may differ in the ignored candidate output. U4527 is
fixed at the one diagnostic offset, B face/original orientation. U4517 and R4577
retain their accepted B faces and orientations. Each uses2,401 ordered0.25mm /
24-direction ring offsets about its current accepted center, through25mm. Both
current and cumulative original-center displacement must be<=25mm. Four-decimal
coordinate differences are compared with exact decimal squared distance: no
extra clearance/displacement epsilon is added. Boundary points rounded outside
the hard circle are explicitly filtered, not silently treated as inside.

All other bodies, including unresolved U4524/U4526, are frozen. The reviewed R1
scene retains412 accepted transformations and26 original unresolved liabilities,
complete pads/courtyards, opposite-face protections and all fixed link, panel,
slot, tail, latch, fixing and outline constraints. Overlaps within this forbidden
union never authorize omitting an obstacle. C4534 stays K/F(190.96,137.59),
angle-90 in the actual retained extractor representation (physically equivalent
to270 degrees; strict equality is not normalized or weakened); C4544 stays accepted K/B(189.2026,136.8974),angle90. C4541/C4543 and the
R4577 analog anchors U4541/Q4504/R4576 also remain frozen.

Only the exact three moving models are excluded from candidate/final fixed-scene
queries. Individual candidate lists must clear the fixed U4527 probe as well.
The pair loop is lexicographic by retained offset index, U4517 outer and R4577
inner; it stops at the first joint witness, exhaustion or100,000 combinations.
`SEARCH_CAP_REACHED` applies only if unexamined pairs remain, never as proof of no fit.
Exhausting the complete declared pair domain exactly at the cap is
`NO_PAIR_FIT_IN_DECLARED_DOMAIN`. Source/predicate mismatch and any unrecognized
status exit nonzero while retaining the receipt; only the four completed
experiment outcomes exit zero. Every apparent witness
is checked again as all three complete models against the frozen scene and each
other. No canonical geometry is written.

## Function and interface evidence

The original45-contact E5 external ledger remains intact. U4517 unit4 pin12 on
RISE is now annotated as belonging to the explicitly movable package; the other
44 remain frozen counterparts. The expanded ledger retains all contacts on the
additional U4517 and R4577 E5 signal nets, with each contact's pin/unit/role and
movement scope. Complete package identities retain supply units separately.
U4517's four NAND units and supply unit cannot be split or reassigned.

R4577 is the1kohm FALL_BASE_LIMIT analog boundary between FALL_EXPO_DRIVE and
FALL_EXPO_BASE, not an incidental logic resistor. Its exact MPN remains blank.
The retained R0603 footprint is a geometric model, not a selected exact body.
No timing, skew, analog error, return, decoupling or routing allowance follows
from a room witness. The fixed decouplers remain obligations even if a moved IC
is farther from them. All26 canonical unresolved ICs remain unresolved.

## Execution and tests

Synthetic fixtures only:

```sh
python3 -B scripts/checks/frozen_studies.py discover scripts/stack/studies/mc04_e5_exchange
```

One actual run requires separate implementation review and verified external
admission:1CPU,1GiB RAM,zero swap,128PIDs,total600s (setup60/analysis480/cleanup60),
canonical machine-wide heavy lock and verified process-tree cleanup. No automatic
retry. The script does not establish these controls itself.

```sh
python3 -B scripts/stack/studies/mc04_e5_exchange/study.py --output "$PWD/.circuit-cache/mc04-e5-exchange/result.json"
```

Output is exclusively reserved before analysis, with no overwrite or symlink
acceptance; exceptions preserve a failure receipt. All consumed inputs and reused
predicate/extractor code are pinned, including the ignored diagnostic/logic
receipts. Another checkout requires those exact receipts via authorized handoff.
Pre-edit component validation passed84manual records/445unverified placements.
Actual exchange enumeration NOT RUN by the implementation author. No native,
DRC, fill, physical acceptance, hardware adoption or manufacturing is performed.

The source-angle correction is limited to C4534's frozen spec angle270 -> -90.
The prior failed receipt remains historical evidence of a representation mismatch;
no source position, orientation, clearance or comparator changed. A source-only
regression parses the pinned K board with the retained plain-Python extractor,
applies the retained accepted transforms, and compares all seven frozen anchors
with the exact spec representation, including accepted C4544. It does not build
a placement scene or run the exchange search.
