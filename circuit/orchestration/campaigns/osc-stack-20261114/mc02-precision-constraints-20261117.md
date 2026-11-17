# MC02 precision-function constraints from retained sources

Exact engineering source: `2c53715d49a4a7639723595590d1fd4eeb3a3c1f`. Read-only source map for unplaced U1518 and U4341; no native execution, placement, routing allowance or gate decision.

## U1518: O5 pitch follower

`design/reports/io-partition.json` identifies U1518 as OPA4197IDR. Unit 1 output and inverting input are `/O5/1V_BUFFER`, noninverting input `/O5/C1e2eb4_SENSE`; other units are unused grounded followers. `oscillator.py:157–162` selects the high-impedance input precision variant for 1V. Line176 feeds 1V_BUFFER through 100 kΩ into EXPO_SUM. Moving this function therefore involves its SENSE, follower feedback and downstream precision summing relationship, not just the IC courtyard.

The electrical standard's `signals` and `calibration` objects establish 1 V/oct; passing range −5..8 V, but calibrated tracking target only 0..5 V at25°C after20-minute warmup/calibration. Tracking target5 cents shares a total4.166667mV-equivalent budget with core/exponential and temperature error. Static precision and octave-step targets are2mV; precision-output load error is1mV. These are system/function targets, not an allowed incremental PCB error for this move, and the output load target must not be reassigned to an input follower.

The `high_impedance_input` cell in the electrical standard uses100kΩ R_PD and10kΩ R_LIMIT, unity feedback, precision BAV199 rail clamp plus BAT54S bootstrap clamp. Clamp leakage and input current remain part of the error budget. `scripts/checks/s2b_protection_map.py:153–164,196–203,218–276` retains a conditional clamp calculation: BAV199 curve readings5nA at25°C,6.6nA at40°C,13nA at70°C; TMUX RON14Ω is from a ±15V table. OPA4197 offset100µV and drift4.5µV/°C rows use ±18V conditions. The retained report's pitch row gives0.1276mV clamp bound plus0.0797mV bootstrap typical drift over0–40°C, and0.198mV plus1.4385mV over0–70°C. These mixed bound/typical diagnostics are not a guaranteed full-temperature budget: bootstrap guarantee remains UNKNOWN and the BAV199 mirror/source qualification remains explicitly limited. No recalculation or source-strength upgrade was performed here.

`oscillator-reference.json` contains15nA bias,100Ω isolation/feedback,1nF compensation and0.3m/1nF harness limits for the LOCAL/BASE/SINE reference fanout with OPA4197IPWR. They are a different reference function/package scope; do not silently apply them as U1518 IDR routing limits.

## U4341: E3 fall converter and storage buffer

`io-partition.json` maps U4341 to OPA4197IPWR: FALL_EXPO_SCALE (unit1), FALL_EXPO_SERVO (unit2), ENV_BUFFER (unit3), unused grounded follower(unit4).

`envelope.py:213–219` retains100kΩ FALL_EXPO input,200kΩ REFN5 offset feed,3.3kΩ plus1kΩ scale trim feedback,1kΩ base limiting, and300kΩ plus50kΩ base/reference trim with the BCM847BS matched-pair converter. Preserve the source topology and associated passive/transistor function group in any later proposal; these values do not establish phase margin or allowable added trace capacitance.

`envelope.py:234–239` joins the OTA currents to ENV_STORAGE through100Ω, specifies100nF C0G storage (exact1206CG104J500NT is asserted by `test_envelope.py:72–73`), places the precision unity buffer on ENV_STORAGE, and uses100Ω hold/idle clamp paths. `test_envelope.py:45–50` explicitly requires ENV_STORAGE sensitive status, exactly six contacts, all in the ENV_CORE instance island and none on the panel. This is an existing executable isolation/topology constraint.

`check_envelope.sh:26–29` checks exported per-instance storage net identity; its receipt scope explicitly excludes physical timing, dynamics and board/harness qualification. `run_envelope_spice.py:1–5,15,29–33,53–67` uses ideal amplifier/OTA/switch boundaries with100nF CAP and500µA bias fixture. Its checks include −25mV..8.1V storage envelope and ideal rise/fall timing within3%; the retained report explicitly excludes device spread, offset and leakage. These are behavioural fixture criteria, not U4341's real leakage/droop or routing tolerance.

## What is quantified, and what remains to specify

| Function | Existing constraint | Missing for a placement-change acceptance contract |
| --- | --- | --- |
| U1518 | Exact unity follower/clamp topology; system5-cent tracking scope and shared voltage targets; conditional clamp diagnostics | Allocated added layout error, actual common-mode/rail/temperature bias and offset bounds, parasitic loading/stability, leakage/contamination conditions and measured tracking after movement |
| U4341 converter | Exact fall scale/servo component network | Added feedback-loop R/C, acceptable converter timing/error and stability margins over actual corners |
| U4341 storage buffer |100nF storage, six-contact core-island isolation and no panel path; nominal ideal timing checks | Allowed physical storage leakage/droop, added capacitance, clamp leakage/injection and error/time limits for actual parts and temperature |

No numeric added-route/via allowance or per-node physical leakage acceptance limit was found in these inspected function/test sources. This is a bounded finding, not a claim that every repository document was searched. Existing quantified criteria should be carried into gate review with their scopes; missing budgets require an explicit design/validation contract. The26 unplaced list and DS-06 holds are unchanged.

## Exact source hashes

- `design/reports/io-partition.json` SHA-256 `37a773282d723d7f689d1e6cf009e4edd1947827a5ee45f0051e42cd4e907a0b`.
- `design/standard/electrical-standard.json` SHA-256 `0cdef30d4848414c794b7561c07bef6c5cf63a19f7f79a0fd21866412e0e40fe`.
- `design/spec/modules/oscillator.py` SHA-256 `18393b0a9f580a91d7394a69a90cf89e2853f882fc55f37eeaa97f306c7c4377`.
- `design/spec/modules/envelope.py` SHA-256 `015b02c5d84550e19bf92b9ec838a43b255a728e02de1e562e855ba632fc2ee5`.
- `design/spec/modules/test_envelope.py` SHA-256 `f7fd81ad2902c32d0951c4c7f08ef7a963a3dfb5b54a0768fd38d5e3ab682dfb`.
- `design/spec/modules/check_envelope.sh` SHA-256 `8e206f124de959dc573509a14dc79d42b40ac2d0c3c8e96a7cb2805c2bead764`.
- `design/spec/modules/run_envelope_spice.py` SHA-256 `2eafb29b6ed4fe0131617a07a60f07eee0c06277f744be5c2d148d31d09926f2`.
- `design/reports/spice/envelope.json` SHA-256 `06d257cf6e7fdbeaa02d3857517b7ea905e61cde7746f5aeaa6c015dbf33d9a1`.
- `scripts/checks/s2b_protection_map.py` SHA-256 `a8b3657660423d8bfae398b44d0dadd2961f7d242ab58e77a9a0fc9bd600a753`.
- `design/readiness/s2b-protection-map.json` SHA-256 `851e4c542c4d5e4a5aeba7eaa4943ca13ff4d06dfbededa4f489a7772af15eb2`.
- `design/spec/modules/oscillator-reference.json` SHA-256 `0a6f259b109c91ace3fc03c5b7e3205de8a3bce13a6d1d93313257a9a9ca0883`.

## Key JSON line locators at the pinned revision

- `design/standard/electrical-standard.json`: key `"pitch_linear_range_V"` at line(s) 87.
- `design/standard/electrical-standard.json`: key `"calibration"` at line(s) 168.
- `design/standard/electrical-standard.json`: key `"pitch_tracking_target_cents"` at line(s) 174.
- `design/standard/electrical-standard.json`: key `"id": "high_impedance_input"` at line(s) 409.
- `design/readiness/s2b-protection-map.json`: key `"precision_input_clamp"` at line(s) 787.
- `design/readiness/s2b-protection-map.json`: key `"role": "pitch (oscillator 1V/OCT)"` at line(s) 800.
- `design/reports/spice/envelope.json`: key `"Ideal OTA` at line(s) 222.
