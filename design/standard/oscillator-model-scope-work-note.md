# Oscillator fixture scope and current publication

This follow-up to issue #29 corrects source/model selection and stale published current counts. It does not alter the captured oscillator circuit, panel hardware, component selections, model thresholds or physical qualification.

The old sine fixture selected every `R_SINE_` source key. Local-reference fanout added four similarly named resistors whose drivers and capacitors were excluded; the resulting deck contained two disconnected three-node resistor chains. A graph regression reproduces these fragments. This is a demonstrated deck membership defect, not a claim that a previous native run failed.

The sine fixture now requires twelve resistor roles and two amplifier roles, preserving source order and values. Missing, duplicate, DNP and unsupported primitive members fail before writing decks or invoking the oracle. The generic pair, ideal 1.5 V symmetry-wiper source and fixed 5.5 kohm level rheostat remain explicit model fixtures. Local fanout and actual symmetry-pot/output loading are excluded, and the separate reference-fanout report retains its narrower vendor-model scope.

The architecture page now obtains package counts, instance names, planning subtotals and unknown guaranteed maxima from the current oscillator worksheet. Current source has four OPA4197 packages per oscillator and total planning allowances of 339.5 / 335 / 30 mA (+12 / -12 / +5 V), rather than the old two-package, 254.5 / 250 / 30 mA summary. The VEE/reference relationship and retained ERC wording are also corrected. No worksheet value is changed by this publication fix.

Canonical schematic regeneration now runs all three bounded oscillator decks, so subsequent source changes cannot leave their retained results stale. The reference-fanout 24-case vendor-model run is not repeated or rebound; its existing source/load verification remains separate.

Validation: entry component contract PASS (66 manual records); guarded baseline PASS in 215 seconds with no drift; 26 focused tests PASS. Fresh pinned native three-case run PASS in 5 seconds: all numerical results equal the retained report, and the sine deck only loses the four disconnected resistors. Final aggregate/publication checks are recorded in the PR and retained review log. All physical oscillator, tracking, startup, stability, fit and fault qualification remain NOT RUN.
