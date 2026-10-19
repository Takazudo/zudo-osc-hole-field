# Stage34 independent review

Status **PASS_SOURCE_REVIEW_ONLY** after three rounds by a fresh-context subagent that recomputed the key numbers with its own code. It covers source review only: nothing physical, native or measured.

- **Round 1:** CHANGES_REQUESTED: 2 HIGH, 4 MEDIUM, 7 LOW (Stage34); Stage33 round-2 corrections N1/N2 correct, 1 LOW.
- **Round 2:** CHANGES_REQUESTED: 1 MEDIUM, 4 LOW; every round-1 finding verified resolved.
- **Round 3:** PASS_SOURCE_REVIEW_ONLY; round-2 findings verified; final pass over the tree.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| A-H1 | HIGH | fixed parts and T2 checked only for the nominal cable: the middle sleeve bore was overrun at the lowest former setting and the cap had no registration term | tolerance corners (cut, bow, z registration) for every state; sleeve bottoms and block entries include the registration; sleeve extent over the corners; admissibility model reworked; verified round 2 |
| A-H2 | HIGH | rear-cover check omitted the RG34 tolerances and K4; J-SIG would fail | cover rule with margin, RG34 tolerances, registration and K4: J-SIG FAILS (needs z 106.21 vs 105); reported as BOUNDED_EXCEPT_REAR_COVER with owner options as proposals; verified |
| A-M1 | MEDIUM | post strength used bending only | bending plus torsion (von Mises): 39.8 N allowable, 50 N fails; root overhang not covered; verified |
| A-M2 | MEDIUM | wire ledger promoted conditional currents to PASS | AWG26 rating checks CONDITIONAL; verified |
| A-M3 | MEDIUM | current budget hand-entered, partly from X1-derived numbers | term-by-term budget summed by the generator with sources (ADG values from the ADI rev C table recorded in Stage8, cited with their condition); verified by independent sum |
| A-M4 | MEDIUM | SERVICE_ONLY exclusion changed the front jack board procedure without a proposal | proposal and result rows added; RG34 fit/removal path UNKNOWN; verified |
| A-L1..L7 | LOW | tautological criteria, fixed-former control not generated, former/sleeve model mismatch, labels, stranded check, review-record note, friction model note | all fixed or noted; verified |
| B-L1 | LOW | Stage33 largest_fitting_radius is only the largest scanned radius | recorded in report.stage33_notes; Stage33 bytes unchanged |
| M-R2-1 | MEDIUM | middle sleeve vs settable former ambiguous; a fixed sleeve arc would add about 0.6 mm slack | both bend corners belong to the settable former; sleeves carry no inner arc (design-input former_scope, README, summary, report); verified round 3 |
| L-R2-1..4 | LOW | Alpha 1852 missing from the UNKNOWN group; ADG typical values unused; shorter J-SIG not marked not evaluated; sleeve wording | fixed; verified round 3 |

This review also covers the Stage33 round-2 corrections that Stage33 recorded as not re-reviewed; the Stage33 record itself is unchanged.

Bound files and hashes are in `independent-review.json`.
