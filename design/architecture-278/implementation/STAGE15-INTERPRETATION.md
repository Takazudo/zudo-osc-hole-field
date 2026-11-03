# Stage15 acceptance interpretation correction

This correction supersedes the blanket redesign/product-downgrade conclusion in [STAGE15-ALLOCATION.md](STAGE15-ALLOCATION.md) and its completion reports at `cc1b3dc68bce927f5299d3e090016f940addca86`. Their calculations, inputs, test evidence and bytes remain historical evidence. No component, geometry, tolerance, calibration or criterion changes.

## Correct requirement and disposition

The canonical [electrical standard](../../standard/electrical-standard.json), `calibration.static_precision_error_V` and `cells[id=precision_output].notes[1]`, specifies **full static path error ≤2mV after factory calibration**. It separately specifies **load-induced error ≤1mV for −5/0/+5V, no load to10kohm**. The earlier interpretation treated2mV as an unconditional fixed-electrical-setting knob-law bound. That was too broad.

The [A01 specification](../../../doc/src/content/docs/architecture/osc-block-ao.mdx), “Range, headroom and error choice,” requires observing centre/end gains, OFFSET-CV unity, manual midpoint/endpoints, output DC/drift and clip thresholds. It does not supply an accepted factory adjustment procedure. The [captured topology](../../spec/modules/offset.py) preserves `OUT=gain*IN+manual_offset+OFFSET_CV`. Neither the observations nor mathematical removal of an intercept establish physical calibration. No calibrated-path pass or failure has been demonstrated.

The retained6.00105005mV maximum under four diagnostic idealizations is at the manual±5V endpoints: about5.00100005mV reference initial sensitivity plus1.00005mV manual network-ratio sensitivity, with signs reversed between endpoints. IN=CV=0 there. It is **not external-CV transfer error and not demonstrated post-calibration residual**. The existing16.475227mV sampled maximum is also a fixed-setting uncalibrated diagnostic. Both numbers remain unchanged.

For comparison, the four-idealized CV-only5V interval is−0.999850…+1.000050mV under the retained resistor model; pairedCV10V-span error is−1.999700…+2.000100mV. The paired gain cancels a constant intercept at unchanged controls/conditions, but does not establish absolute static accuracy. Neither interval includes all actual-condition errors, and neither is an acceptance result.

Withdraw the conclusion that the matrix alone necessitates a joint hardware redesign or abandonment of the canonical2mV target. Retain precision intent and existing hardware candidate. The historical “single/four corrections suffice” flags answer only the hypothetical uncalibrated fixed-setting comparison, not calibrated-path acceptance. Likewise99.970005ppm remains an algebraic reference ceiling for its hypothetical uncalibrated endpoint budget, not a required product tolerance. No new tolerance is adopted.

## Four separate measurement lanes

The [proposed measurement contract](stage15-interpretation/measurement-contract.json) is **unadopted and unexecuted**. It identifies stimulus, held controls, independent reference, load and permissible adjustments for every lane.20minute warmup comes from the standard;25°C and10kohm static characterization are proposed conditions, not new acceptance requirements. Actual source impedance, rails, reference, ground plane, instrument uncertainty and settling must be recorded. Accuracy states must remain unclipped.

| Lane | Proposed stimulus and reference | Held controls and load | Adjustment and interpretation |
|---|---|---|---|
| Fixed-setting uncalibrated | Historical ten states; measured external inputs versus nominal electrical-fraction law | Record and hold ATTEN/OFFSET per state; proposed10k load | No adjustment within state. Characterizes knob-law/reference sensitivity; not post-calibration acceptance. |
| Paired external CV gain | IN=0; OFFSET-CV−5,0,+5V measured by independent source/meter | Same ATTEN/OFFSET, reference, rails, temperature and10k load throughout | No adjustment. Report slope, zero/intercept and raw errors separately; subtraction is diagnostic, not calibration. |
| Calibrated static path | Proposed CV/IN/manual/mixed verification grid against independently defined desired transfer | Approved factory setting held through verification; proposed10k static load must be decided | **Procedure missing.** No adjustment authorized or executed here. Specify real actuators, sequence, range, persistence and independent verification points before evaluating2mV. No fitted correction credited. |
| Same-setting load change | Nominal−5,0,+5V output setup; same meter/reference plane | Same input, controls and calibration state for open→10k pair | No rezeroing or stimulus adjustment between loads. Evaluate the distinct1mV output-difference target. |

The existing front controls cannot independently correct every gain. ATTEN controls the IN contribution; OFFSET controls the manual contribution. ExternalCV gain remains `gr*gcv`, independent of those controls. A paired measurement can identify that gain; it does not create an actuator. Stage13's actuator limitation remains valid. Do not claim that factory calibration necessarily removes the observed errors, or that it necessarily cannot satisfy the criterion, without a realizable approved procedure and evidence.

## Concrete product decision needed

Decide whether nominal manual±5V endpoints/full knob law must meet precision acceptance, or whether they specify selectable range requiring characterization while external signal paths have defined calibrated acceptance states. Define which settings must retain calibration after user operation, the path/state grid, and permitted factory adjustments. Keep2mV after-calibration and1mV same-setting-load targets unchanged. Once that contract is approved, evaluate actual post-procedure residuals and only then identify any necessary correction. This report authorizes no implementation stage, fitting, new calibration, part search or product downgrade.

The correction report binds the canonical standard, A01 specification, frozen numerical evidence and proposed contract. Independent review and source preservation checks accompany it. Canonical boards, locked placements, decision.json, KEEP_K1402_INCUMBENT, prior evidence and both resistance-domain comparisons remain unchanged. Allocated lengths remain distinct from actual copper. Native/CAD/ERC/DRC/simulation/hardware NOT RUN; test success is not electrical acceptance. PR286 remains draft/unmerged; PR285/260/277 remain parked.
