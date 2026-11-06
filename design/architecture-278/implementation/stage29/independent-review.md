# Stage29 independent source review: PASS_SOURCE_REVIEW_ONLY

Baseline `0c1871791a866ba3de64472cac360b81f9cb90ab`. Reviewer: an independent agent teammate
(Claude Opus 5.5). Effort and harness settings are unknown. This is a source review only.
Hardware acceptance and architecture adoption are both false.

## Drawings re-derived: the column reversal meets both required handedness values

- The two PDF SHA256 values match `sources.json`, Stage5 and Stage28.
- Female view A: columns 32 → 1 from left to right, rows a/b/c from top to bottom. Arrow A
  comes from above the body and the tails point down.
- Male view B: columns 32 → 1, rows c/b/a, and only the 96 holes. Arrow B comes from below
  the body and the tails point up.
- The reviewer's own PyMuPDF extraction reproduces the rows, the 2.54 mm pitch and the Ø2.8
  holes. The holes are 90.000 mm apart, symmetric, and 0.3 mm toward row a.
- The board sides (female body +z of A01-middle, male body −z of A01-core) require
  determinants of +1 for the female and −1 for the male. The mated-coincidence argument
  gives the same result.
- Stage10 gives −1/+1. The candidate gives +1/−1 with zero residual.
- The candidate maps all 96 contacts of each connector one-to-one onto the unchanged hole
  set. Board planes and the female fixing holes (299.3, 183.0)/(299.3, 273.0) are unchanged.
- b1–b8 stay AGND, c1–c8 keep their signals and 80 contacts stay NC.
- a1 is at (301.54, 188.63) on both connectors.

## Checks passed

- unittest: 16 tests OK, both normally and under `-O`.
- `--check --check-cache`: PASS.
- `--check-vector --check`: PASS.
- Scope: only the allowed paths changed against the baseline.

## LOW notes only

- Float noise such as `201.32999999999998` in the contact map.
- The view-error test is caught by the protected Stage22 guard, not by Stage29 logic.
- Vector and crop drift is detected only with `--check-vector`.
- `implementation/README.md` and `WORK.md` are not hash-bound by this review.

## Not run by the reviewer

- native KiCad, ERC and DRC
- `regen-all.sh`
- simulation
- physical M-01
- `--check-history` replay
- CI

D02 stays `CONFLICT_REQUIRES_DECISION`.
