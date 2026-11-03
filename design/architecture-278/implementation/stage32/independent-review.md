# Stage32 independent source review

Reviewer: independent fresh-context Claude Code subagent (cloud). Status `PASS_SOURCE_REVIEW_ONLY`: source review only. Native KiCad, ERC/DRC, simulation, rail strength tests and physical checks are NOT RUN; nothing is adopted.

## Round 1 at 25dfc932 requested changes (2 HIGH, 6 MEDIUM, 6 LOW)

The reviewer re-derived the notches, strap clearances, bow, tolerance stacks, B31 failure, release dip, section properties, Kt, allowable loads, deflection, 2MS3 bound, bend radii, design lengths and sweep gaps with independent code; all matched except where a finding applied.

## Round 2 at 58d857c7 passed; all 14 findings resolved

The reviewer re-checked every finding with independent code: RV containment over every travel and case (0 samples outside), constant 136.000 / 150.000 mm lengths, worst-point stacks (0.199 / 0.200), panel datum, cable-aware access (3.53 / 4.62 / 3.83 mm), blocked strap latches, S9 status, and the LOW items. 15 tests pass in normal and `-O` Python.

## All findings are resolved; R1–R3 were fixed by the lead after round 2 and not re-reviewed

| Severity | Finding | Resolution |
|---|---|---|
| HIGH | H1: RV-DIP reservations did not contain the hook envelope (housing sweep XY only); the installed hook already reached below z 34 | RV-DIP = union of hook envelopes below z 34 for installed and every release case at constant length + sweep + margin; independent test sweep; re-verified (0 samples outside) |
| HIGH | H2: Static model left out ~29 mm stored slack; release lengthened the hook without shortening the loop | installed at design length with the surplus in the local loop; every release case keeps the design length; slide = change of middle-side arc length; re-verified (136.000 / 150.000 mm) |
| MEDIUM | M1: Tolerance taken at one point; strap bow at guide centre | min over samples of clearance - margin - stack; strap rows use the footprint maximum bow; re-verified |
| MEDIUM | M2: K4 depended on unstated stack choices (bore, seating, bow span, interior bow) | strap bore and saddle seating added; bow over the board length; bow sensitivity reported; uniform diagonal bow fails K4 and is an open condition; runs lowered 0.2 mm; re-verified 0.199 / 0.200 |
| MEDIUM | M3: panel_rear_z 2.0 misquoted Stage10 (rear z 0) | panel rear z 0, front z -2, pinned by validation; toggle bound recomputed (15.13); re-verified |
| MEDIUM | M4: Latch access ignored cable bundles and own guide | rigid (incl. all guides) and cable distances reported separately; re-verified 3.53 / 4.62 / 3.83 |
| MEDIUM | M5: Strap reopening by front access contradicted the data | both front corridors BLOCKED; reopen only with A01-middle removed; re-verified |
| MEDIUM | M6: Machine status hid the maker bend-rule failure | S9 added; B32 CONDITIONAL_PENDING_WIRE_SELECTION, failed [S9]; re-verified |
| LOW | L1: MAKER_DOC could cite a NOT_OBTAINED document | rejected; test added; re-verified |
| LOW | L2: pcb_bow_fraction cited the JLC page that states no bow | JLC removed as a source, noted as negative evidence; re-verified |
| LOW | L3: Tip deflection ignored the grooves; README N2 wording | grooved section used (0.08634 mm); wording fixed; re-verified |
| LOW | L4: Criteria coverage gaps (default rule, S8 release bounds, S4 robust) | explicit per-prefix rules; S8 includes release bounds; S4 includes robust sweep; re-verified |
| LOW | L5: Tests missed the bugs | containment, min-over-samples, cable-aware access, pins and constant-length tests added; re-verified |
| LOW | L6: 2MS3 bound took nut/washer at nominal | -0.25 applied; re-verified |
| LOW | R1: Uniform diagonal bow used 171.3 mm instead of the 170.95 mm outline diagonal | derived from the A01-middle outline (1.282 mm, spare -0.382); fixed by the lead after the re-review |
| LOW | R2: Local slack loop shape not stated as a surrogate | README open condition and assembly step state it is a surrogate tied to M32-08 / M-12; fixed by the lead after the re-review |
| LOW | R3: RV containment test reused middle_envelopes() | test builds release envelopes itself for every travel and case incl. local-only; fixed by the lead after the re-review |

File hashes are in [independent-review.json](independent-review.json).
