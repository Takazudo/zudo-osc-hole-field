# Stage25: smallest loading candidate, honest error allocation, and DIN route

Source proposal from `88b75411d61d705fd5c89281b62b3462837db007`; **not adopted,
not electrically qualified, no production CAD change**. The 2 mV calibrated static
and separate 1 mV same-setting load-change targets remain fixed. The candidate
changes only RV1308's proposed resistance/MPN, with pins, NCs, placement and historical
unit identity retained. No runnable native request or fabrication files are emitted.

## Recommendation and the requirement that actually applies

Retain the existing reference/inverter circuit and real OFFSET baseline adjustment.
If lower wiper impedance is wanted, the smallest defensible source candidate is
**Bourns PTV09A-4020F-B103 (10 kΩ)** in place of B104 (100 kΩ). It has the same
`4|0|20|F` configuration: horizontal/rear bushingless housing, no detent, 20 mm flat
shaft. The resistance code alone changes. This is a concrete candidate for comparison,
not evidence that a substitution is necessary to meet calibrated accuracy. Keep the
current 1 kΩ series resistor, 10 MΩ pull-down, 10 nF filter and follower. No new
amplifier, trim, feedback path or undefined open-wiper input is introduced.

The retained [owner decision](../stage15-procedure/owner-decision.json) explicitly
makes manual OFFSET a continuous musical control without prescribed-voltage accuracy
at knob positions. The [existing factory procedure proposal](../STAGE15-PROCEDURE.md)
uses the actual front control and an independent meter to establish a predeclared
baseline, then holds it. Thus Stage24's negative fixed-knob allocation is a valid
**uncalibrated diagnostic only**; it does not prove the adopted intended use fails
2 mV after setup. Historical calculations and FAIL receipts remain unchanged.
Replacing reference parts simply to cancel that diagnostic would be unjustified.

For absolute acceptance use
`OUT − (Btarget + Gdesired*INmeasured + CVmeasured)`.
Never redefine Btarget to measured OUT0, subtract a fitted intercept from raw
acceptance data, or assume the physical setup error is zero. Stable initial loading,
reference error and constant amplifier offsets can be absorbed by *actual* reachable
baseline adjustment; their later changes cannot. No calibration has been performed.

## Quantified one-part comparison

| Quantity, ideal nominal electrical fraction | Retained 100 kΩ | Proposed 10 kΩ |
|---|---:|---:|
| Maximum loading error with 1 kΩ / 10 MΩ | 5.094 mV | 0.797 mV |
| Maximum source impedance before pull-down | 26 kΩ | 3.5 kΩ |
| Center settling to 1%, 10 nF | 1.194 ms | 0.161 ms |
| Current from +5 to −5 V through track | 0.1 mA | 1 mA |
| Total track dissipation at 10 V | 1 mW | 10 mW |
| Open-wiper sensitivity | 10 mV/nA | 10 mV/nA |

The generator also evaluates all 16 combinations of pot ±20%, series ±0.1%, return
±1% and capacitor ±5%. It does not silently promote these into pot taper/contact,
noise, temperature or lifetime bounds. At 8 kΩ and nominal 10 V the track draws
1.25 mA and dissipates 12.5 mW; both reference buffers carry this current, with
opposite signs, and their other loads remain additional. This is not a completed
rail budget. Bourns specifies 0.05 W, 20 VDC, −10 to +50°C, and 300°C/3 s soldering;
no unprovided hot power derating or assembly profile is inferred. The published
residual-resistance/sliding-noise specifications do not establish full-position
precision, stable contact resistance or post-adjustment drift.

The lower impedance reduces bias/leakage voltage sensitivity while the pull-down
continues defining the ideal open-wiper state. The filter passes more high-frequency
noise and settles about 7.4 times faster. No accepted A01 response requirement exists,
so this tradeoff must be accepted before applying the part change. Enlarging C to
recover settling would be a second candidate change needing its own exact dielectric,
value, assembly and transient review; it is deliberately not smuggled into this patch.

### Stability is assessed, not asserted

No active feedback topology changes. C7105 remains behind the same ≥999 Ω series
resistance, rather than becoming a new direct 10 nF reference-buffer load. Both
reference outputs see a lower passive track resistance (≥8 kΩ). The OPA4197 data
sheet describes unity-gain operation and capacitive-load isolation; its direct
1 nF feature is **not** a blanket qualification of this remote/filter network.
Existing reference-capacitor ESR, remote interconnect, output feedback and startup
qualification remain open. There is no computed phase-margin or bench stability
claim. The source recommendation is to preserve these loops, then verify with the
actual parasitic/load matrix under separately authorized testing. No native simulation
was executed. Audio attenuverter compensation stays unchanged and remains a separate
DC/CV-versus-audio-null behavior question.

## Reference alternatives assessed

1. **Retain REF5050AIDR and 10 kΩ inverter pair — recommended.** Its 5 mV initial
   source sensitivity and roughly 10.010 mV worst independent resistor-ratio
   sensitivity affect manual baseline/range, not external-CV slope. Physical setup
   corrects a constant intercept, but not subsequent reference, resistor, amplifier
   or pot change. No guaranteed temporal allowance is invented.
2. **Reuse RN7102 R3/R4, LT5400AIMS8E-2#PBF — do not apply.** Matching reduces the
   initial ratio contribution to 0.500 mV (25°C) / 0.625 mV (I-grade matching envelope),
   but 100 kΩ versus 10 kΩ raises bias sensitivity tenfold and changes four currently
   NC terminals. At 107.5 kΩ, the OPA4197 PW full-temperature 15 nA table limit gives
   1.6125 mV absolute sensitivity; between two arbitrary opposite-sign endpoints
   the conservative difference is 3.225 mV. The table-conditioned 25°C **20 pA max**
   gives 2.15 µV, not an installed full-common-mode or service-temperature guarantee.
   These are local inverter-output sensitivities before actual manual-path weighting.
   Added impedance/parasitics and noise need review; there is no CV-gain benefit.
3. **Higher-grade REF50 — insufficient as a guaranteed fix.** The manufacturer's
   high grade reduces initial accuracy from 0.1% to 0.05% and box drift from 8 to
   3 ppm/°C. The latter is `(Vmax−Vmin)/(Vnom*165°C)`, not a maximum derivative near
   25°C. Its full specified temperature span is therefore bounded by 2.475 mV versus
   6.6 mV for standard grade. Neither number is a prediction for a narrower service
   interval or a guaranteed post-setup error. Hysteresis, noise and aging are typical
   entries, not lifetime maxima. No exact higher-grade JLC candidate is qualified
   or selected in this stage; a grade swap cannot close the other unknown terms.
4. **Additional buffering / huge pull-down resistance — reject as minimum remedy.**
   A buffer after the present loaded wiper does not remove its loading; moving the
   only return after a new buffer leaves an open wiper undefined. Bootstrapping the
   return adds a positive-feedback/fault-state obligation. Raising 10 MΩ to 100 MΩ
   raises open-wiper sensitivity tenfold. The one-pot candidate avoids those changes.

No reference trim, digital calibration or component tolerance question is delegated
to the owner. None is proven necessary by fixed-knob diagnostics. If a real paired-CV
slope failure is later isolated, the Stage15 independent CV-gain actuator proposal
remains the relevant remedy; changing the manual reference does not correct it.

## Complete allocation ledger; closure remains explicitly open

The generator retains a single simultaneous remainder, not a separate full remainder
for every mechanism. At initial 25°C, the two coherent network ratios bound the
5 V CV gain contribution by **1.00005 mV**, leaving **0.99995 mV**. Using the network's
full I-grade envelope alone changes these to **1.250078 mV / 0.749922 mV**; this does
not grant the pot or whole cell that temperature range.

The complete equation is:
`|actual baseline residual| + CV ratio contribution + sum(disjoint uncertainty/change bounds) ≤ 2 mV`.
The following all share that one remainder:

| Ledger term | What must be bounded; present status |
|---|---|
| Achieved baseline setting | Actual resolution/reachability/error to predeclared Btarget; unknown |
| Measurement uncertainty | Source/meter uncertainty at jack and OUT planes, without duplicate device error; unknown |
| Input/protection change | Source impedance, 100 kΩ pulldown, ADG5412F resistance/leakage and sense loading; unknown actual-condition delta |
| Amplifier/bias/nonlinearity change | Common-mode, supply, temperature, bias and finite gain after setup; table sensitivities do not cover installation |
| Reference/control/ratio change | Manual path reference, inverter ratio, pot contact/taper stability and mechanical motion after setup; unknown |
| Source/receiver return change | Shared current and real interconnect voltage shift; not ideal AGND or an allocation-as-copper claim |
| Output/load change | Finite output-loop response within the fixed static load; source/physical bound missing |
| Noise/aging/repeatability change | Time-window noise, hysteresis and drift not already included above; no lifetime maxima available |

CV network ratio drift already covered by the chosen ratio envelope is not counted
again in manual/reference drift. Baseline residual includes absorbed initial constants;
do not add them a second time. Nor does setup remove subsequent changes. IN and mixed
paths need their separate actual gain settings, nonlinear terms and headroom; CV-only
arithmetic is not a complete A01 guarantee. The distinct same-setting open→10 kΩ
**1 mV load-change** test permits no rezeroing and has no demonstrated bound here.

All missing bounds are JSON `null`, never zero. The checker refuses incomplete term
sets and refuses to return a total/criterion pass when any term is unknown. This is
a complete *accounting ledger*, **not a closed worst-case allocation or hardware
qualification**. It would be false to promise the requested complete guarantee from
these data. Source-only analysis has reached a concrete product boundary: specify
the required service temperature and time since setup/power cycle, and accept a
real factory setup/uncertainty protocol. Existing parts alone do not provide enough
maxima to promise an unrestricted lifetime/environment envelope. This is not a request
to loosen 2 mV. Even a chosen envelope still requires actual-condition evidence.

## JLC sourcing and DIN fabrication route

Dated raw JLC observations confirm the exact B103 **C5848782**, REF5050AIDR **C27804**
and OPA4197IPWR **C2057327** catalog identities. The pot explicitly lists Wave
Soldering, the ICs SMT Assembly; all list Economic and Standard. This retrieval
observed 200 B103, 11,697 REF5050AIDR and 1,988 OPA4197IPWR in the catalog's
`overseasStockCount` field. These dated counts supersede the older search-engine
zero-stock snapshot, but do not reserve inventory. Missing numeric stock fields
would mean unknown, not zero or available inventory. These
are catalog sourcing routes, not reservations, lead-time promises, order acceptance
or exact installed assembly qualification. The Bourns solder limit must be honored
in a process review. No supplier was contacted and no order/quote was initiated.

The exact HARTING drawings remain the authority. Their `board drillings` Ø1±0.1
callout does not itself spell out finished plated versus tool-drill diameter.
Stage24's finished-hole mapping remains a conservative proposed procurement
interpretation, to be resolved explicitly, not an excuse to enlarge holes.

Current JLC documentation offers **±0.05 mm** circular-hole sizing for **multilayer
ENIG, 0.55–2.0 mm**, specified in the PCB remark. At nominal 1.00, [0.95,1.05] fits
[0.90,1.10]. This resolves the documented *diameter-option comparison*. The published
±0.075 position specification does not guarantee the drawing's Ø0.05 position zone,
and the female Ø2.8 +0.1/−0 fixing holes are outside that tighter-option size range.
Those are unknown custom capability/interpretation questions, not proof all JLC
boards or every JLC route fail. Mixed SMT/THT wave assembly is documented, with exact
connector/material/process acceptance still unknown.

Prefer the retained connectors with the [unsent engineering specification](fabrication-request.md).
Changing DIN brand/termination is not a free tolerance waiver: an exact replacement
must preserve 96-contact identity, current/voltage, keying, mate, height, mechanics,
pin view, solder process and sourcing. No assessed evidence establishes a drop-in
replacement that solves all of these. A precision-fabricated adapter or alternate
board fabricator introduces new mating/height/assembly boundaries and is a fallback
manufacturing choice, not a qualified route. Sorting incoming parts can select good
samples but cannot establish guaranteed manufacturing capability. Do not enlarge
pads/holes or move locked hardware to label this resolved.

## Deliverables and next decision

`candidate.json` is the unapplied one-part proposal, `correction-report.json` its
deterministic calculation, `evidence.json` the source locators, and `sources.json`
the raw retrieval receipts. Supplier observations are dated and independent of
manufacturer performance claims. Tests cover identity/NC/placement changes,
missing allocation terms, zeroing unknowns, false baseline cancellation,
reference-bias deltas and invalid manufacturing-option promotion.

Recommendation: retain current reference/inverter; keep B103 as the smallest
loading-reduction candidate, pending acceptance of its faster response and higher
reference current. Decide the service temperature/time-after-setup envelope and
factory protocol before claiming precision closure. For DIN, decide whether to
pursue documented tighter-hole JLC manufacturing with explicit position/fixing/process
confirmation, or accept a different fabrication/connector architecture if that route
cannot be confirmed. No third-party contact is authorized in this task, so the
specification remains unsent. These are concrete product/manufacturing choices;
another unchanged parts audit will not close them.

All old files except WORK.md are byte-preserved. Canonical boards, locked placements,
decision.json, KEEP_K1402_INCUMBENT, historical FAIL evidence and parked PRs remain
unchanged. PR286 remains draft/unmerged. Next native request: **NONE**.
