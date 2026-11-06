# Stage31 independent source review

Reviewer: independent Claude Code subagent (local), 2026-10-18, baseline `698d91398db411d94117a4298810b1bd58f38d61`. Status `PASS_SOURCE_REVIEW_ONLY`: source review only. Native KiCad, ERC/DRC, simulation, rail strength and physical checks are NOT RUN; M-01, M-09 and M-12 stay NOT_RUN; B is recommended for the next prototype study and nothing is adopted.

## B geometry reproduces from independent code

Own header rotation, fillet construction and 0.05 mm sampling give installed lengths 108.71 / 119.58 mm, exact clearances 0.80 / 0.79 mm (reported 0.70 / 0.69 after the 0.1 mm deduction), cable gap 5.89 mm (reported 5.69), and SW1401/SW1501/SW1601 bounds z 44.59 (reported 44.49). A and C reproduce the same way.

## Release sweeps keep the 0.5 mm margin, tightest 0.575 mm

With both middle headers turned 90°, J-PWR:middle is 0.575 mm from SW1701 and 0.825 mm from crossmember:jack:1; J-SIG:middle is 1.9 mm from J1610/SW1601. B is the only candidate meeting K1–K4; its K4 spare (0.19 mm) clears the 0.15 mm design-choice threshold by 0.04 mm, which is disclosed.

## Release surrogate now keeps r 5 bends; the middle dip is an open unknown

Extras +15 (middle), +4.0 / +3.8 (local) and +19.0 / +18.8 (both) re-derive by hand and give design lengths 138 / 149 mm. The middle release puts the hook envelope near z 17.6, through the foreign PCB plane whose outline is unknown; this is disclosed and carried by M31-07.

## Copper allocations at the moved headers reproduce exactly

19/19 edges for B and C match an independent Stage10 trace_length recomputation; B path changes (6 signal, 28 power/return) match.

## All 10 findings resolved or accepted; none MEDIUM/HIGH open

| Severity | Finding | Resolution |
|---|---|---|
| HIGH | H1: B met K2 by 0.05 mm because release sweeps were screened against foreign XY with no margin; any margin >= 0.05 mm left no candidate meeting K1-K4 | sweep_screen expands every sweep by the 0.5 mm placement margin against known obstacles (3D) and foreign XY and reports nearest gaps; B redesigned with both middle headers turned 90 deg at (268.0, 171.5) / (288.0, 174.7); independently re-verified: tightest sweep gap 0.575 mm (SW1701), J-SIG:middle 1.9 mm (J1610/SW1601), crossmember:jack:1 0.825 mm |
| MEDIUM | M1: README rejected a 90 deg turn on a false claim (rotated sweeps fit the strip side by side) | claim removed; B now uses the 90 deg orientation; re-verified |
| MEDIUM | M2: C "0.1 mm beyond the margin" misstated the geometry (0.2 mm geometric, 0.1 mm after the sampling deduction), and the 0.15 mm DESIGN_CHOICE K4 threshold alone separates B (0.193) from C (0.1) | README/WORK state 0.7 mm per side, 0.2 mm geometric, 0.1 mm after deduction; B 0.19 mm spare vs 0.15 threshold disclosed; candidates carry tightest_spare_note; re-verified |
| MEDIUM | M3: local-withdrawal release polyline reversed on itself (negative extras), not bend-feasible | release_cases moves the nearest loop-top/hook waypoint pair just enough for lead + r 5 and passes fillet_route; extras B J-SIG 0/+15/+4.0/+19.0, J-PWR 0/+15/+3.8/+18.8 re-derived by hand; release rows report keep-out hits, foreign bounds and the lowest dip (centreline z 19.1, envelope about z 17.6, through the foreign PCB plane); disclosed in README, common not_modelled and M31-07 |
| MEDIUM | M4: A and C kept status CANDIDATE_UNDER_MODEL_CONDITIONS although they fail K2/K3 and K4 | status derived from K1-K4 (REJECTED / REJECTED_BY_CRITERIA / RECOMMENDABLE_UNDER_MODEL_CONDITIONS) with failed_criteria; re-verified A [K2,K3], C [K4], B RECOMMENDABLE |
| LOW | L1: notch wall pieces named N2:a for the rail between N1 and N2 | pieces named by y range (e.g. rail:middle:0:y173.8-180.9); re-verified |
| LOW | L2: README K3 numbers for A slightly off (D15101 32.1, J1710 10.7 mm) | corrected; re-verified |
| LOW | L3: topic headings in stage31/README.md; no Stage31 verification block in WORK.md | README headings now verdicts; WORK.md verification block to be appended by the lead after this review (WORK.md is not in the review binding) |
| LOW | L4: check_source.py runs --check-review and fails until this review record exists | accepted; this record now exists |
| LOW | L5: K2 wording in design-input.json recommendation.criteria still says "outside every foreign XY projection" without naming the 0.5 mm margin the generator now applies (README and rationale state it) | accepted as wording only; results unaffected; suggest adding "by the 0.5 mm placement margin" at the next edit |

## Scope held: only README, WORK and check_source.py changed

No canonical, locked, decision or past-stage file changed; Stage31 files are new. File hashes are in [independent-review.json](independent-review.json).
