# Stage55 independent review

Fresh-context reviewer, read-only, on commit `f6bab9a`. It re-ran `native.py check`,
`decoupling.py --check` and the unit tests and independently rebuilt rail geometry
from the canonical PCB and receipts. Verdict: the evidence supports "the disposable
candidate passes the stated native rule gates, with the stated limits"; wording to
tighten before any citation for adoption.

| # | Finding | Severity | Disposition |
| --- | --- | --- | --- |
| 1 | Ratsnest gate compares per-net edge counts; a cut could hide behind a removed island | should-fix | Fixed: `rail_clusters.py` pad-membership gate. Candidate rail clusters equal baseline minus removed pads. README now says which pads were isolated (OPA4197) vs already joined (OPA4196) |
| 2 | Centreline end test kept one 0.5 mm +12 V stub (C240.1 overlap) | note | Documented as known exception; harmless, not flagged by KiCad; rule unchanged to keep the bound PCB |
| 3 | Baseline inputs and candidate schematic hashes not bound | should-fix | Fixed: both `require`d in `native.py` |
| 4 | Capped types accept any new signature | should-fix | Kept NOT ESTABLISHED; added informational 6 mm proximity screen (0/0 markers); complete marker list remains future work |
| 5 | Parity classifier too broad | should-fix | Fixed: exact (U111, Role) allow-list; PCB and schematic values must be U111 unit values |
| 6 | U111 unit-selection mechanism inferred | should-fix | README labels it a hypothesis; symbol positions/UUIDs unchanged, H1 sheet 91→49 symbols |
| 7 | Neighbourhood metric hides survivors losing a closer bypass; 10 ICs listed | should-fix | Fixed with `survivors_whose_nearest_rail_cap_is_removed`. Eight of the reviewer's ten (U2203, U8204, U2318, U8213, U2302, U3401, U8106, U8202) are on board JL, whose floorplan coordinates are a different frame. The valid osc-core set is U101 and U207 (both also found by the reviewer) plus U107. Flagged for PDN/layout review |
| 8 | First-run FAIL output overwritten | note | First-run gates summarised in VERIFICATION.md |
| 9 | No overclaiming found | note | – |
