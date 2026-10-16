# Stage15 whole-cell allocation completion — analysis only

This completes the approved Stage15 analysis at `10e3fbbdc2fcfe954da7aa7df5b02db1230ff8f0`. It changes no component, placement, graph edge, calibration setting, canonical board or acceptance envelope. Historical Stage15 null bounds remain intact; the new reports replace an uncomputed discussion with finite conditional calculations and necessary limits, not an invented guaranteed bound.

## Decision

No single investigated correction suffices for the retained 2mV static criterion. Reference-inverter ratio dominates several intercept states; attenuverter ratio dominates negative IN; manual loading dominates quarter-position behavior. Correcting only reference inversion leaves 11.012mV worst modeled error. Idealizing both ratios and manual loading leaves 1.99955mV **before reference initial error or amplifier/input/output terms**, effectively no margin. Idealizing all four effects leaves 1.00005mV resistor-only, but 6.00105mV when the selected reference's ±0.1% initial sensitivity is included.

Recommend a separately authorized **joint accuracy correction**, beginning with both retained discrete ratio functions and control loading, accompanied by reference accuracy and amplifier/input error allocation. Do not implement one ratio fix and call precision solved. With all four idealized, the 5V endpoint's network contribution is1.00005mV. Reserving0.5mV for every remaining contribution requires reference initial fraction ≤99.970005ppm (about0.49985mV at5V), roughly one tenth of the retained1000ppm sensitivity. This is a necessary algebraic condition, not an adopted specification, selected replacement, hypothetical calibration, or proof that0.5mV covers the remaining circuit. If these joint corrections are not acceptable, the product must abandon the2mV fixed-setting claim; even16.48mV is only a sampled nominal-pot sensitivity, not a guaranteed replacement rating.

## Metrics and compatible conditions

Absolute error is output minus `(2a−1)IN + CV +5(2x−1)` at fixed electrical fractions and the same physical corner. Paired gain is a ±5V difference with other conditions held constant: it cancels a constant intercept, but does not repair absolute error. The ideal knob law describes electrical fraction, not shaft angle. No fitting or calibration is performed.

Each scenario enumerates1024 coherent physical resistor corners (64 shared network corners ×16 retained discrete corners), with both reference signs. Shared resistor products remain coupled. Network matching uses initial25°C100ppm only; full-temperature matching and tracking TC are not summed. REF5050AI initial±0.1% is an evidence sensitivity: actual22µF capacitor/rail/load conditions remain unqualified. Nominal pot resistance/load are explicit; continuous knob/pot tolerance/aging coverage is not claimed. Signed decompositions retain product terms and a stated attribution order. Counterfactual deltas compare the identical physical corner, never subtract unrelated maxima. Counterfactual idealization is diagnostic only; approved networks remain.

## Compact before/after

Intervals below are mV, excluding amplifier/input/return errors and finite output loop. “Four idealized” removes both discrete ratio errors and both control loading effects; it retains the selected network and reference initial sensitivities.

| Fixed state | Existing modeled interval | Four idealized interval |
|---|---:|---:|
| CV_only | -5.996368 … 5.988081 | -0.999850 … 1.000050 |
| IN_positive | -6.997069 … 4.988980 | -0.999850 … 1.000050 |
| IN_negative | -16.010079 … 15.974397 | -1.000050 … 0.999850 |
| IN_centre | -11.755512 … 8.236046 | 0.000000 … 0.000000 |
| manual_low | -15.521522 … 16.475227 | -6.001050 … 5.998850 |
| manual_high | -6.498200 … 5.500500 | -5.998850 … 6.001050 |
| manual_quarter | -5.568545 … 15.390048 | -3.000525 … 2.999425 |
| manual_three_quarter | -10.415854 … 0.562414 | -2.999425 … 3.000525 |
| mixed | -11.647681 … 0.931248 | -3.299380 … 3.300540 |
| zero | -4.998017 … 4.988031 | 0.000000 … 0.000000 |

Every row in [allocation-report.json](stage15-completion/allocation-report.json) includes ranked signed CV slope, IN gain/loading/ratio, manual network/reference/loading and inverter-intercept contributions. Each also has paired IN/CV gain and six open/10k conditional output cases, with signed output finite-loop/load terms and coherent extrema. The CV paired10V span error is−1.999700…+2.000100mV; a single5V point is about±1mV. These are distinct metrics.

| Idealized effects | Worst resistor-only mV | With reference initial mV |
|---|---:|---:|
| none | 16.005086 | 16.475227 |
| atten_loading | 16.005086 | 16.475227 |
| manual_loading | 16.018068 | 16.023074 |
| manual_loading, atten_loading | 16.018068 | 16.023074 |
| attenuverter_ratio | 12.902951 | 16.475227 |
| attenuverter_ratio, atten_loading | 12.902951 | 16.475227 |
| attenuverter_ratio, manual_loading | 11.012062 | 16.023074 |
| attenuverter_ratio, manual_loading, atten_loading | 11.012062 | 16.023074 |
| reference_inverter_ratio | 11.012062 | 11.012062 |
| reference_inverter_ratio, atten_loading | 11.012062 | 11.012062 |
| reference_inverter_ratio, manual_loading | 11.012062 | 11.012062 |
| reference_inverter_ratio, manual_loading, atten_loading | 11.012062 | 11.012062 |
| reference_inverter_ratio, attenuverter_ratio | 6.157702 | 8.652275 |
| reference_inverter_ratio, attenuverter_ratio, atten_loading | 5.726662 | 8.221236 |
| reference_inverter_ratio, attenuverter_ratio, manual_loading | 1.999550 | 6.001050 |
| reference_inverter_ratio, attenuverter_ratio, manual_loading, atten_loading | 1.000050 | 6.001050 |

## Output load: computed, conditional

Feedback senses JACK through100Ω after the two499Ω series resistors; the998Ω drop is drive demand, not directly jack error. For unloaded internal Thevenin gainA0 and internal DC resistancero, `vJ=[A0(u+Vos+100Ib)−(998+ro)Ib]/[A0+1+(998+ro)/RL]`. At unchanged parameters, `Δv=−vopen Zcl/(10000+Zcl)` and `Zcl=(998+ro)/(A0+1)`. At5V,1mV permitsZcl≤2.00040008Ω; reserving half for loop droop requires≤1.00010001Ω. All ten states and coherent extrema are calculated, including positive/negative/nearzero demands. At5V,A0=1000/ro=100Ω predicts−547.844µV change;A0=10000/ro=100Ω predicts−54.888µV. These are engineering assumptions, not measured or guaranteed OPA4197 values.

TI minimumAOL120dB25°C/110dBtemperature is specified at±18V and stated load, not an independent unloadedA0 at±12V. Typical375Ω at1MHz is not maximumDCro. Combining those values would doublecount loading and mix conditions. Obtain a direct same-condition closed-loopDC transfer impedance, or compatibleA0/ro, atactual±12V,commonmode,current,temperature. For load-dependent parameters use the full two evaluations; offset/bias/leakage/return changes cannot be assumed to cancel. The report explicitly inverts allowable offset/bias/capacitorleak and return contributions. Ideal5V jack requires5.499V DRIVE and0.5mA before feedback/bias; settling/swing/stability remain validation conditions, not consequences of algebra.

## Remaining terms: explicit ceilings, not a reset budget

For each coherent state, the residual budget is `2mV−abs(known signed residual)`. Negative budgets are reported as deficits; no further contribution is allowed. Positive budgets give one-at-a-time source/input/return ceilings and common equal-amplifier-offset ceiling `budget/sum(abs(coefficients))`. All simultaneous contributions must share that same budget. The illustrative0.5mV reserve is not granted separately to each term.

OPA4197's25°C bias maximum is20pA, whereas15nA is the PW full-temperature maximum. Its100µV offset row is explicitly±18V. PSRR3µV/V permits only a conditional36V→24V midpoint transfer36µV, producing136µV atmidpoint25°C with output at midsupply and10k load to midsupply; this is not a guaranteed±5V commonmode rectangle. Do not sum100µV25°C with15nAtemperature as one compatible corner. Obtain signed/absolute offsets and per-pin currents atactual rail/commonmode/temp, convert through actual source impedances and the supplied ten coefficient gains, and sum within the remaining allowance. No offset/bias cancellation is credited without evidence. The load report also gives per-state internal bias-current ceilings through each retained impedance, including network7.5% absolute resistance sensitivity;20pA25°C and15nA full-temperature contributions are separate columns, never combined with incompatible offset corners. Unknown source/positive-input impedances are explicitly excluded rather than silently zeroed.

For either protected input, withS=source+cable+switchRon,100k pulldown and10k sense resistor, `e=−Vin S/(100k+S)−(S||100k)ID−(10k+S||100k)(Ib+Iclamp)`. At5V a sole0.25mV allowance requiresS≤5.00025Ω; a sole1mV permits20.004Ω. AtS=10Ω, a sole0.25mV current allowance permits24.975nA net sense current, but the divider already costs about0.49995mV at5V. These allowances cannot be added or used to hide that deficit. The actual IN transfer gain scales each state; CV gain is separately tracked. ADG5412F Ron11.2Ω maximum is at±13.5V, and its1.5nA leakage at±16.5V, notactual±12V. BAT54S leakage needs a bound atactual7…17V reverse bias andtemperature; reacquisition returnedHTTP403, so no fabricated value is used. Named missing parameters and inverse limits are in [load-input.json](stage15-completion/load-input.json) and [load-report.json](stage15-completion/load-report.json).

Source-to-receiver ground shift must share the remaining budget (one-for-one at output). Source path lengths remain allocated lengths, not copper; edge-use counts are not current. Temperature/drift/aging require an explicit service condition and compatible data, not a paper lifetime guarantee. Stage14 capacitor sequencing and validation cases remain open and unchanged.

## Evidence and boundary

[Allocation generator](../../../scripts/architecture278/implementation/stage15_allocation.py), [load generator](../../../scripts/architecture278/implementation/stage15_load_allocation.py), independent node/KCL tests and hash-bound reviews make the calculations reproducible. The completion guard preserves every immutable predecessor. No hardware acceptance, architecture adoption, new calibration, part search, implementation, mechanical elaboration, POWER hosting, replication, native/CAD/ERC/DRC/simulation/hardware execution or merge occurs. PR286 remains draft; PR285/260/277 remain parked. Source test success is not electrical acceptance.
