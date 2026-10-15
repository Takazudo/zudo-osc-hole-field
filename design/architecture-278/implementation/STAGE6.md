# Model binding, drawing correction and redesigned hosting increment

Stage6 continues from `28b97e629f187da570903f8efa06a1e08ae72c9a`. The owner approved prioritizing clear modular partition and redesigned behind-panel copper while preserving fixed jack/control surface positions. [scope.json](stage6/scope.json) records the delegated direction; it does not adopt the architecture, select procurement or authorize native/simulation/hardware work.

## TI model and analytical budgets

[Electrical evidence and calculations](stage6/electrical.md) bind the official TI SBOMAF9 archive and its plaintext OPAx196.LIB, Final1.5 dated29AUG2022. The manufacturer explicitly lists OPA196/OPA2196/OPA4196 applicability. The exact selected project identity remains Texas Instruments OPA4196IDR, SOIC-14. All120 captured candidate OPA4196 channels map the macro IN+/IN-/VCC/VEE/OUT nodes to their actual package pins and source nets. No model or bundled test circuit was executed; no amplifier substitution is made.

Archive SHA256 is `9c264813a36536f743c166b6a101904b76ed08f049f2eeb127a438cc6e8ccdf5`; the library member is `31142f5dbd71b758d887ee8a411692fc4c1309c8f47100af4ba5bed7e173c430`. Raw manufacturer bytes remain ignored. The committed receipt provides the URL, member inventory, line evidence and independent raw-archive verification command. A source-available family macro is distinct from tested simulator compatibility, validated circuit behavior or guaranteed manufacturer limits.

Position-correlated ideal-reference loading calculations tighten the old independent15.691mV bound to6.146606mV for bipolar TUNE/FINE and9.340464mV for unipolar PW under the same planning extremes. An explicit two-node passive RC expression separates direct interconnect capacitance from the local filter; the maximum-midpoint example has poles450.098Hz and177.443kHz. These calculations exclude amplifier dynamics, finite reference impedance and unextracted parasitics. Model bias/offset/capacitance parameters remain nominal internal constructs, not replacement worst-case device specifications.

At the retained704.5mA planning current, the proposed200uV return-error term would require0.283889mOhm, tighter than the existing0.5mOhm goal. Neither value is achieved evidence. The collective pitch/modulation/pulse targets remain proposals, nine shared direct-capacitance obligations remain UNKNOWN and five selected1k/100nF receiver dynamics remain separate. Model availability does not close reference-buffer, return, stability or pulse qualification.

## Exact drawing transforms and complete rebudget

The selected female09032966824 and male09031966922 board-drilling views use opposite row orientation. Stage6 registers both drawing views to the same96 named mating contacts and preserves the existing electrical contact identities. The female flange axis is0.3mm toward rowa, rather than an unsigned guessed offset. The source screen uses an explicitly proposed1.8mm contact pad envelope; this is an engineering input, not a manufacturer pad recommendation or fabricated board result.

Instead of assuming unspecified underside cavities clear the twelve Stage5 projections, nine whole headers receive cumulative translations from the original assembly source. Full GH courtyard exclusion covers the proposed contact pads and signed female flange-hole envelopes. Installed solid/support/tail/fastener/cable qualification remains separate from this conservative source screen.

[Current candidate report](stage6/candidate-report.json) recomputes all225OSC crossings,240return groups and270conductors. Relative to Stage5,29signal rows and24return groups change; rear return groups and all non-middle segment allowances remain unchanged. The explicit middle PCB datum places DIN at50mm and opposite-face GH pads at48.4mm. Rebinding all270wire XYZ endpoints gives13.138613mm minimum-cut straight-distance slack against the10mm planning reservation; the former conservative50mm reference-plane result12.086068mm remains recorded separately. The maximum complete allocation remains334.018298mm with38historical strict300mm exceedances. Wire cut, connector developed allowances and PCB trace allocations remain distinct; every electrical result remains UNKNOWN/NOT QUALIFIED.

## One complete hosting increment

The bounded increment is the complete X1 manual A/B selector:56packages,76units,10bypass associations and seven fixed panel devices. It creates candidate front-jack/control hosts and a middle signal/power/return interface reservation. X1 has no K population; this work does not solve the separate2572non-OSC K+13POWER hosting obligation. Other functions remain in the complete source ownership ledger; new unknown volumes are not treated as free space.

Three cross-host signal nets—A_BUFFER, B_BUFFER and SELECTOR_REMOTE—remain independent, with all rail/AGND endpoints and local feedback included. The compact control host is29.03×22.66mm and clears the85prior OSCfront envelope intersections. A_BUFFER span rises80.086→153.987mm while local selector/drive spans shrink; this tradeoff is explicitly unqualified.25opposite-face courtyard overlaps,13support-strip/fixed-hardware intersections and5middle/rear fixture projections remain unresolved. New connector choices, routing, electrical budgets and installed mechanics require their own evidence. A virtual middle handoff is a reservation, never a physical pad or routed path. Fixed panel positions, all33functions/fiveOSC and rear-local trims remain unchanged.

## Acceptance boundary

This is a candidate source checkpoint. NativeKiCad10.0.6/ERC/DRC/simulation/bench/physical checks are NOT RUN. Stage1 and incomplete acceptance issues remain OPEN. Canonical boards/grid/decision/workflow and KEEP_K1402_INCUMBENT remain unchanged; no merge, adoption, purchase, fabrication or energization occurs. [WORK.md](WORK.md) records final checks and independent review scope. Publication uses `[skip ci]` to prevent unauthorized default native campaigns.
