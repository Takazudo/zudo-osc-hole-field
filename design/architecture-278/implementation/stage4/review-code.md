# Independent stage 4 code and requirements review

Reviewed the root agent's single repair candidate and the electrical agent's requirements audit against final source bytes, 2026-10-15. This reviewer authored `stage4_power_inventory.py`; its execution is recorded separately and is not represented as an independent review. The electrical agent's `review-electrical.md` supplies the independent power-inventory review.

## Outcome

No remaining blocking source-arithmetic or requirements-attribution finding was identified in the reviewed scope. The candidate remains unaccepted because occupied volumes, installed/service geometry and electrical operating behavior are unqualified. The retained **334.018 mm / 38 strict-comparison exceedances** are historical planning-envelope comparisons, not evidence that the circuit is unsafe or that extra topology is required. The source's 300 mm / 1 nF envelope remains unchanged pending separate requirements review.

## Requirements provenance and classification

Independently read `electrical-standard.json` at initial commit `f0c8eaa0d16a0ab59427bef8d2e2fb5f9cf9c336` and at the current source. Both say PROPOSAL, unvalidated; `remote_buffer` is NEEDS BENCH, and `remote_controls` specifies maximum harness length 0.3 m and capacitance 1 nF. The later architecture electrical narrative explicitly expands the comparison to complete paths including connectors, traces and test equipment. The audit accurately distinguishes that later planning interpretation from the original harness wording. Neither source proves a measured failure boundary or universal physical stability threshold.

Checked all actual net classes represented by the 225 paths against live endpoint/source evidence and oscillator source topology. Pitch paths require DC accuracy/loading/ground error, temperature drift/calibration and dynamic modulation/settling assessment. Gate behavior is split correctly: analog SYNC_BUFFER before comparison; conditioned SYNC_GATE and switched HARD/SOFT commands; OSC_GATE_REF as a DC threshold reference. The source confirms 100 kΩ pulldown, 10 kΩ series and 1 nF AC coupling on the core HARD/SOFT branches. Guaranteed receiver margins, ringing, false/missed edges and pulse loss cannot be replaced by a scalar length check. The 1 V/oct conversion of 5 cents to approximately 4.167 mV is algebraic and does not assign the whole calibration budget to an interconnect.

The former catch-all FM/PWM classifier now admits exactly FM_BUFFER, FM_REMOTE, PWM_BUFFER and PWM_REMOTE; an unknown net fails closed. All eight current classes retain their specific proposed characterization, with no measured/native result invented. Canonical limits, circuit topology and local timing/storage-node restrictions remain unchanged.

## Single repair candidate

Verified the +6 mm X translation of all 30 shared packages and every associated pad, preserving units, local geometry and source connectivity. Exactly 65 shared path rows are recalculated, while all 225 endpoint identities remain present. The 240 front/GH/DIN/rear return branch allocations are geometrically unchanged; moved shared source AGND/rail pads are bound separately, without claiming a solved return impedance network.

The candidate cross-checks all 225 actual source endpoint Ref/pin XY values against the independently generated normalized power coordinate table. The table uses the declared +6 mm shared scenario and the same front/rear poses, avoiding inherited compact supply XY. Two handle centres move to local X=11/33 mm; current local fixture geometry passes its source screen. These are reservation/clearance arithmetic results only, not a frame-strength, guide-alignment, installed-fit or service certificate. Other 28 functions, POWER and services remain UNKNOWN_RESERVED.

## Executed checks

- Final `stage4_requirements.py --check`: PASS after the fail-closed classifier change.
- `stage4_candidate.py --check` and `stage4_power_inventory.py --check`: PASS at their unchanged final source.
- All **45 current stage 4 tests**: PASS, including six requirements, seven candidate and thirteen power-inventory tests plus the occupied/service tests present in this source.
- `git diff --check`: PASS.

No native KiCad, aggregate campaign, new SPICE run, hardware or physical test was performed. Native/ERC/DRC/physical checks remain **NOT RUN**. This receipt does not claim complete Stage 1 acceptance.

## Authored power-inventory execution

The compact 3.9 MB report preserves 5,904 packages, 8,226 units, 20,419 pins including 939 NCs, and 1,067 bypass associations. It binds 1,125 candidate packages / 1,472 units per variant and leaves all 4,766 other-function plus 13 POWER packages unplaced. All 6,929 global rail/ground pin nodes reference the authoritative placed-package pad table; absent placements resolve to null. Complete routed topology, common impedances, source limits/current sharing and operating-state maxima remain unknown. Thirteen mutation/conservation tests and deterministic reproduction pass; independent review of this authored work belongs to the electrical reviewer.

## Final reviewed SHA-256

- `scripts/architecture278/implementation/stage4_candidate.py`: `6bb1fc9c053aa48c615dccf8627041942adb4ec1909722c4ed0d996ded82161b`
- `scripts/architecture278/implementation/test_stage4_candidate.py`: `44637c14ef5cf5f422e49a1b0fb37322a16d040f5cfbc131d966ffc84b2d9fcf`
- `design/architecture-278/implementation/stage4/candidate-report.json`: `fde4939aeb285c9081cdbcc7ad9d4b0b95cfdaf713de829fcf89d5f4b7b32bcd`
- `scripts/architecture278/implementation/stage4_requirements.py`: `4eb0eee0a889bc8a22451abd2caa91a031692d041735d475b0d634d2acead413`
- `scripts/architecture278/implementation/test_stage4_requirements.py`: `5b0bb246c73677894ce3bc60a272b91580334f34f3622cc30709e1f9a5dcf003`
- `design/architecture-278/implementation/stage4-requirements-report.json`: `b425023140e76357583f474cb740317da8f8da2fa49b1d4d41a64f9d970228d9`
- `scripts/architecture278/implementation/stage4_power_inventory.py`: `985f9ce633c1c77069108051534cf0bae8876f08218294bb38ada789861408b6`
- `scripts/architecture278/implementation/test_stage4_power_inventory.py`: `5286aade8477e02916da237d54048b0c7a8ae5ed0f8ffd703e91a20e3001797d`
- `design/architecture-278/implementation/stage4/power-inventory-report.json`: `e49574f6be6567d8df68d0cd4cb1d68cae068b5a2438c21757bfd835285e9a2d`
- `design/standard/electrical-standard.json`: `185f4775082a36873954323a2377844e0694631418ac510db08e3a0d39b56e53`
- `design/spec/modules/oscillator.py`: `c83a10adb792265798ae453af4380300b6fde8d1e26afe6dca240412eb965d3e`
- `design/architecture-278/electrical.md`: `6fbcfe5bc37f265f371c5399d3cb03779680bbf0253fdcf27dc7dda09b6c4dd5`
