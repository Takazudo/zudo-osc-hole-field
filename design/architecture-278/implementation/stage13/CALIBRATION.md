# A01 calibration feasibility with the two existing controls

This study uses only the captured ATTEN RV1307 B103 and OFFSET RV1308 B104 controls, their loaded wipers, and the Stage12 coherent resistor model. It adds no trim, correction network, firmware, calibration policy or acceptance criterion. All prior stages remain unchanged. Reproduce with `stage13_calibration.py`, `--check`, and `test_stage13_calibration.py` under the implementation scripts directory.

At a fixed operating setting the linear model has three independently observable parameters:

`OUT = G_IN(a) × IN + G_CV × OFFSET_CV + B(a,x)`.

Changing ATTEN changes IN gain and, with input/remote amplifier offsets, also changes the intercept. Changing OFFSET changes the intercept. Neither changes `G_CV = gr × gcv`. The control Jacobian therefore has rank two for these three observations, while a single zero-input measurement has rank one. Measuring three parameters does not supply three actuators. A fitted three-parameter mathematical correction can remove model residuals on paper but is not implemented by this circuit.

The bounded solver uses electrical fractions from 0 to 1, never extrapolated shaft settings. For nominal components, zero gain requires ATTEN approximately0.500175 because of actual wiper loading. Nominal clockwise gain reaches approximately0.999800, so exact+1 is outside the modeled range; its +5V signal error is approximately−0.9999mV. Exact+1 being unreachable does not by itself violate the retained0.5% endpoint gain target. The selected Stage12 resistor witnesses can also make endpoint requests unreachable. These are modeled electrical fractions, not measured knob markings, taper or repeatability guarantees.

Each witness sets a reachable requested IN gain and nulls zero-input offset if possible, then tests the same settings over independent IN and OFFSET-CV values. CV-only residuals at5V reach approximately−19.960 to+20.040mV in the retained witnesses, despite successful gain/zero adjustment. This is a conditional uncalibrated-resistor result, not measured hardware failure or a complete tolerance bound. The nominal case and ten witnesses are not an exhaustive all-error envelope. Independently fitted corrections are displayed separately and never promoted to hardware calibration.

The documented observations remain distinct:

- ATTEN centre and both endpoints can be observed; one operating knob cannot independently trim all three positions or preserve its correction when moved.
- OFFSET CV unity is observable but has no separate actuator.
- Manual midpoint and endpoints are observable; the manual knob sets an operating offset, with no independent midpoint/span adjustment.
- Output DC can be nulled at one zero-input state within range. This does not remove gain, load, temperature, noise or return errors.
- Output load change and drift have no independent adjustment and are absent from the ideal DC load/temperature model. Their errors remain unknown, not zero.
- Clip thresholds are observable against the nominal±10V internal threshold, but the user knobs alter the signal rather than calibrate the comparator threshold. Actual threshold/recovery remains unknown.

The retained2mV static and1mV output-load-change targets are shown as separate criteria. No complete static pass follows from a fitted zero, and no1mV load pass follows from a load-free algebraic model. Input-source/protection error, offsets/bias, reference behavior, setting resolution and environmental effects remain unresolved. ±15V mathematical demand cannot be produced linearly from±12V rails; overrail cases are explicitly excluded from linear acceptance rather than clipped numerically into a false pass. Inside-rail results also do not prove actual headroom.

The concrete result is that the existing controls can set two temporary operating quantities within available range, but do not implement independent correction of the full documented observation set. No new hardware remedy or calibration policy is adopted here.

Native KiCad, simulation and physical verification: **NOT RUN**.
