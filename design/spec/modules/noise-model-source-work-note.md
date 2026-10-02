# Noise filter source binding

Requested continuation: fix stale model acceptance while retaining the fixed panel and draft scope.

- Before edits: component contract PASS, 65 manual inventory lines, no schematic/placement binding; native pin assets checked. Canonical baseline log: `/tmp/osc-noise-baseline.log`.
- Reproduced gap: noise AC producer used fixed independent decks and never inspected the captured family; edited filter values or colour wiring could keep old passing results.
- Add a checked source projection before writes/oracle execution; require unique fitted roles, exact nominal values, amplifier identities/pins and no additional internal connections. Level stages and output loading remain excluded.
- Include four fresh native AC runs in canonical regeneration; preserve original deck bytes and numerical results when source is unchanged.
- Correct brown DC's omitted white-follower offset. Conditional nominal coefficient sum is 123, giving 12.3 mV at 100 µV per amplifier. This is not a complete DC bound.
- Exact source: Texas Instruments OPA4196IDR, SOIC-14, SBOS869 July 2017, retained `circuit/sources/ic-library/OPA4196.pdf`, SHA-256 `d89dd6009d109bf18b349e77ff46e4df60bf7d4faaefd4c3ebe6ec0e2fc7793d`; physical index 6 / printed 7 §6.7 VOS max 100 µV at ±18 V, 25 °C. No application guarantee inferred at ±12 V.
- Remaining: NOISE2 spectra/drive, equal RMS, DC/leakage, real amplifier behavior, physical stability, supply/fault currents, sourcing and factory socket acceptance remain open. No hardware or manufacturing qualification performed.

Independent review: bind passive primitive identity/prefix/unit, and disclose WHITE/PINK synthetic finite-gain readout followers. The first final guard was canceled while confirmed queued (NOT RUN); no active check or source was changed.
Final independent review confirmed source graph and DC algebra; explicit mid-supply common-mode/output and 10 kΩ load conditions added. Second queued final attempt likewise canceled before execution (NOT RUN).
Final source identity check also binds the exact library name and amplifier prefix; wrong-library same-name symbols are rejected. Third queued attempt canceled before execution (NOT RUN).

Final validation: baseline regeneration PASS (334 s), seven source-mutation tests PASS, guarded canonical regeneration plus 14 AO/noise tests and documentation checks/build/strict links PASS (240 s). Four fresh native decks and all numerical report fields equal the retained before-state; only the source projection was added. Remaining site host/assets, built component references and publication scan PASS. One existing strict-link allowlist exception remains unchanged.
