# Stage33 independent review

Status **PASS_SOURCE_REVIEW_ONLY**: a fresh-context subagent reviewed the source in two rounds and recomputed the key numbers with its own code. This covers source review only.

- **Round 1:** CHANGES_REQUESTED, with 1 HIGH, 5 MEDIUM and 11 LOW findings. All were resolved, and round 2 re-verified them.
- **Round 2:** CHANGES_REQUESTED, with 2 MEDIUM (N1, N2) and 4 LOW findings. The lead fixed them; tests and `--check` pass. They were not re-reviewed.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| H1 | HIGH | S3 retention passed on keeper K1, which retained nothing and did not fence the J-PWR arch's closest approach to the core volume (x 234.5, 2.87 mm) | K1 withdrawn; S3_lateral_retention fails (no retention part; validation rejects one without a design); R33 CONDITIONAL_PENDING_RETENTION; clearance/K4/release/core results CONDITIONAL in the ideal plane; lateral allowance and straight zones reported; re-verified in round 2 |
| M1 | MEDIUM | RV-ARCH bounding boxes overlapped 19 / 14 designed parts including the core withdrawal volume | in-plane slabs (leg columns + top band) tested against every designed part and the core envelope by a separating-axis test (S12); reviewer's point-grid check found no overlap; re-verified |
| M2 | MEDIUM | committed report.json stale at f90d142 (--check drift); drift test skipped report.json | regenerated; test compares committed report.json with the baseline normalised; --check PASS; re-verified |
| M3 | MEDIUM | pin-row to round-bundle fan-in at each housing exit not checked; J-SIG had 7.06 mm at middle-15 | fan-in S-bend (rho = 10xOD + OD/2, worst OD) is the straight lead in every state and in the design length (133 / 149 mm); S10; re-verified 10.389 / 6.906 mm |
| M4 | MEDIUM | J-PWR-to-K1 stack used carrier_face only; inter-carrier registration unstated | K1 removed; core check carries the catch-all stack (robust 1.89 mm); registration UNCONFIRMED stated; re-verified |
| M5 | MEDIUM | F33 screen missed the +y descent path and called the result INFEASIBLE on a code-default plane | F33 UNKNOWN; slot path INFEASIBLE; +y descent screened against foreign XY columns (clear radius 5.25 mm) and found below the code-default plane even installed; re-verified |
| L1-L11 | LOW | radius convention and derivation text; bow z-shift; B32 wording and half-sine; K1 electrical note; PCB impact; thin radius scan; per-cable wire checks; core stack; tests (independent RV sampler, negative S1/S7); text slips; SVG projection notes, ticks, labels, widths | all fixed; re-verified in round 2 |
| N1 | MEDIUM | radius scan accepted R 22 with a looser cover rule than S11 (bow omitted), misclassifying the 20x sensitivity | scan uses the S11 rule with the uniform bow; largest fitting R 17; 15x CONDITIONAL, 20x INFEASIBLE inside the cover; README/summary updated; fixed by the lead after round 2, tests and --check pass; not re-reviewed |
| N2 | MEDIUM | J-SIG lateral allowance ignored the J-PWR cable (reported >= 4.63 mm) | allowance includes the cable plan bound (J-SIG 3.36 mm, J-PWR 1.89 mm) and states that the gap is shared; fixed by the lead after round 2; not re-reviewed |
| L-a..L-d | LOW | RV-ARCH above z 105 unexplained; F33 'must move to y > 185' wording; grip-length wording; stale test name | reservation text notes cover-off service states; wording softened; grip above the fan-in stated (12.7 / 5.2 mm); test renamed; fixed by the lead, not re-reviewed |

Bound files and hashes are in `independent-review.json`.
