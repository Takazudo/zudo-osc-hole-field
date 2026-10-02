# Module report scope correction

## Request and preserved limits

Acceptance reconciliation for issue #25 found stale A/B current prose and a two-stage offset estimate after issue #60 introduced a third selected-path amplifier. The model report also called its sampled error a complete DC path result despite starting after the input buffer. A related pilot sentence incorrectly grouped REF5050 input demand with +5 V logic. This change corrects those reporting boundaries. Issues #22, #25 and #59 remain open; original complete-current and electrical requirements are unchanged.

No hardware coordinates, components, nets, current values, simulation decks or numeric limits change. These remain unvalidated drafts. No complete current maximum, source applicability, switch behavior or hardware qualification is established.

## Source and calculation

The current `manual_ab.family()` allocates exact TI OPA4197IPWR channels to both input followers, the local control-region follower and the jack-output stage. Either selected signal crosses three channels. With ideal DC unity followers, jack-sensed unity DC output and selector attenuation α=10 MΩ/(10 MΩ+2.2 kΩ), the offset contribution is (α+2) times a per-channel allowance. The retained SBOS737C section 6.7, physical index 6 / printed 7, VOS row explicitly specifies ±18 V for the ordinary common-mode offset value. Its default conditions include 25 °C, mid-supply common-mode/output and a 10 kΩ load to mid-supply. The exact PDF SHA-256 is `27653a7d5e965cbb2d23f7998919ebd774efd5cd3e126b8f0881469ae91166fd`. Its 100 µV figure is retained only as conditional planning arithmetic, not a guarantee for the project's ±12 V/±5 V path. The rounded preliminary offset allowance is 0.3 mV, with existing 1.1 mV selector loss and 1 mV load target giving 2.4 mV / 2.88 cents. Bias, gain, leakage, tolerance and temperature effects remain outside that incomplete budget.

A/B current prose now points to `design/reports/current/manual_ab.json`, which already counts two OPA4197 packages. It no longer duplicates earlier single-package figures. Its full maxima remain null. Pilot prose separates unquantified REF5050 input/reference demand on +12 V from HC14/HC221/pull-up/switching demand on +5 V; report arithmetic is untouched.

`run_manual_ab_spice.py` starts its ideal source at the selected A_BUFFER/B_BUFFER boundary, includes selected 2.2 kΩ / 10 MΩ loading, the local harness follower and precision jack-output cell. It excludes source-facing protection, the input amplifier and contact transitions. Its 2 mV criterion is an error sampled 400 µs after each source transition; the 1 mV settling, 1 mV late ripple and 10% overshoot criteria are unchanged.

## Verification

- Fresh branch from main b305c0f; entry component contract PASS. Guarded combined baseline PASS in 221 seconds with no tracked drift.
- All 24 simulation deck hashes identical before/after the reporting-label change. Fresh pinned guarded TI-model run PASS 24/24 in 26 seconds. Every case record and numeric value equals the prior report; only limits prose and recorded source hashes change. The fresh run also refreshes previously stale `manual_ab.py` and `io_partition.py` hashes after earlier LED/partition changes; those files are unchanged in this branch. The original rejected remote-feedback diagnostic remains historical and unchanged.
- 16 focused MULT/A/B/pilot tests PASS; component validation PASS (65 records). The source checks remain capture/report tests, not electrical qualification.
- Final guarded aggregate, documentation check/build and strict site checks PASS in 437 seconds. The existing workbench template-link allowlist exception is unchanged. No other tracked regeneration occurred.

## Remaining

Complete per-rail typical/max current deliverables remain unestablished. A complete input-jack-to-output model, contact transition/bounce, source/fault/power sequencing, stability, physical fit and worst-case pitch error remain unqualified. No issue closure or fabrication action is part of this correction.
