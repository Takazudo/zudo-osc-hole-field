# Stage14 integrates moved capacitor paths; application remains conditional

This finite increment starts at `df671f7a1e2598de3294f375509d8a73dc508d9d` on existing draft PR286. It binds the Stage13 capacitor geometry to the complete A01 graph and assesses the selected pair's operating and transient evidence. All314 predecessor source/evidence files remain unchanged, excluding only the three explicitly mutable integration files (README, WORK, check_source). Stage13 calibration and all mechanical/strap/support geometry remain frozen. Five OSC,33 functions,438 locked centres, canonical boards, decision.json and KEEP_K1402_INCUMBENT are preserved.

## Four pads and five edges are rebound

[Graph](stage14/interfaces-report.json), [complete paths](stage14/paths-report.json) and [rebudget](stage14/rebudget-report.json) regenerate from all Stage13 actual pads using the retained graph constructor. They retain555 nodes,318 edges,269 connected local endpoint walks,21 crossing-signal paths and all106 power/return endpoint paths. The only changed node coordinates are C7101:1/2 and C7102:1/2. Incident edges238,264,265,293,294 are all recomputed. All other edge bytes and path topology remain unchanged.

| Allocation | Historical mm | Stage14 mm |
| --- | ---: | ---: |
| Middle power boundary → C7101 positive |291.225|303.568|
| Middle ground boundary → C7101 negative |290.391|302.734|
| Middle ground boundary → C7102 negative |301.316|290.057|
| C7102 positive → REF5050 VOUT |14.993|13.477|
| C7102 positive → U7104 buffer input |41.680|40.976|

Three power/return walks and five local walks change; the21 crossing-signal walks do not. Crossing maximum remains467.579376mm and retains its historical comparison. These are developed **allocations**, using1.15×octile XY+7mm+absolute Z per local segment. They are neither actual copper nor obstacle-aware routes. A300mm complete path is not a universal electrical limit. Physical harness lengths, contact counts and wire-only capacitance sensitivity remain unchanged; actual package/PCB/loop parasitics remain unknown.

The frozen, unselected strap option is also rebound through all26 core suffix paths, with80 front endpoints retained: C7101 positive336.158→348.501mm, C7101 negative317.734→330.077mm and C7102 negative328.659→317.400mm. No strap geometry, material, joint or contact is changed or selected. Both original PCB-only0.5/1mΩ requirements and expanded whole-path comparisons remain explicit on every endpoint, with no waiver, reset or equal-sharing credit. Unknown actual copper, upstream feed, return-current distribution and complete resistance remain null. Historical Stage10–13 reports are not rewritten.

## The exact pair remains a conditional candidate

[Electrical input and primary locators](stage14/electrical-input.json) and [conditioned assessment](stage14/electrical-report.json) concern TI **REF5050AIDR**, its **OPA4197IPWR** buffer, KEMET input **T491C475K050AT**4.7µF50V and output **T491D226K035AT**22µF35V. C7107 stays100nF. Supplier availability/order allocation is not established. No capacitor search, protection/bleed addition or circuit redesign occurs.

The TI REF50 RevO and KEMET T491 primary PDF bytes were reacquired and match Stage13 hashes. TI OPAx197 RevC matches its owner hash. Locators distinguish AI from EI and the PW buffer package. The conditioned evidence is:

- TI REF50 §6.3, printed5/physical4: ±10mA is recommended operating current. §6.5 printed7/physical6:25mA short-circuit current is typical at VOUT=0. Printed8/physical7:200µs turn-on to0.1% is typical with1µF and no load. None guarantees startup current or settling with22µF.
- Initial output tolerance19.8–24.2µF gives99–121µC and247.5–302.5µJ at5V. An **assumed**10ms linear ramp needs9.9–12.1mA capacitor current before leakage or buffer input current. This neither rejects an unspecified startup ramp nor proves one. Input initial4.23–5.17µF gives55.836–68.244µC at the retained13.2V proposal, plus C7107's separate nominal1.32µC. Actual source impedance, overshoot and charging current remain unknown.
- RAW5V has exactly C7102:1,U7101:6,U7104:3. The reference drives capacitor leakage and one buffer input; the downstream pot/divider/inverter currents are buffer-output loads supplied from its rails. At25°C, output leakage7.7µA plus a separately conditioned15nA full-temperature PW bias sensitivity gives7.715µA; the125°C qualification multiplier gives92.415µA. These are explicitly separate-condition subtotals, not guaranteed operating or startup bounds. Input leakage belongs to the+12V supply/AGND budget. REF IQ, input leakage and raw output demand are separately listed; complete supply/load currents remain open.
- KEMET's output ESR maximum0.7Ω applies at100kHz/25°C. TI's≤1.5Ω stability requirement and separate1–1.5Ω noise recommendation are retained. Combined effectiveC/ESR versus bias,temperature,frequency and age remains unqualified. Separate qualification tests are not compounded into service lifetime.
- Maximum leakage gives no minimum discharge rate. Operating sink capability gives no guaranteed off-state sink. Thus no finite guaranteed safe discharge wait or startup time can be derived. TI does not provide a supported VOUT-to-VIN off-state reverse-current bound here.
- OPAx197 §7.3.7 printed25–26/physical24–25 describes input rail ESD steering. Charged RAW5V can inject into a collapsed buffer supply; normal input bias is not an off-state current limit. Actual common-rail collapse, unequal positive/negative rails and external injection require assessment. Absolute input-current limits are not intended operating targets.
- KEMET permits only short transient reverse exposure at its stated temperature fractions and prohibits continuous reverse operation. Those capacitor allowances do not override REF5050's−0.3V pin absolute minimum, establish allowed transient duration for this assembly, or qualify hotplug/inrush. Factory surge screening is not blanket inrush permission.

The finite disposition is **CONDITIONAL_CANDIDATE, NOT QUALIFIED**. No deterministic rejection is justified solely by the missing transient evidence. Ten named cases retain concrete stimuli, observables and criteria: normal operation, fast startup, slow ramp/brownout, reference-supply loss, buffer-supply loss, unequal rail sequencing, rapid restart, reverse/ringing, discharged service and effectiveC/ESR/stability. All are **NOT RUN**. Actual operating temperature, ramp/settling requirements, source impedance and safe test limits must be specified before later physical admission; this document grants none. A failure would require an evidenced rejection or separately scoped necessary correction, not automatic redesign.

## Stop here; precision accuracy needs a separate remedy or product decision

The frozen Stage13 result stands: two user controls cannot independently correct OFFSET-CV gain. Its retained resistor witnesses leave roughly±20mV at5V after achievable IN-gain/zero adjustment; these are conditional source results, not measured failures. Larger capacitors and rebudgeted graph lengths do not remove that error.

Recommended separate scope: evaluate a precision matched-ratio implementation or explicit independent adjustment of `R7124/R7123 × R7126/R7125` for OFFSET-CV gain against the retained **2mV total static** budget, including all remaining errors. No resistor values, matching claims, adjustment hardware or topology are adopted here. Product alternative: explicitly restrict A01 to nonprecision modulation/manual offset rather than promise calibrated precision pitch-CV service. The current2mV static and1mV load-change criteria remain unchanged until a decision; accepting the alternative is not implied.

## Reproduction and evidence boundary

Run `stage14_paths.py --check`, `stage14_electrical.py --check`, `stage14_assessment.py --check` and the source tests under `scripts/architecture278/implementation/`; the full `check_source.py` additionally protects canonical and historical evidence. Stage13 review hashes for mutable integration files are checked at exactdf671f7a; all immutable bindings remain live-checked. Current integration has fresh independent code and electrical review. [WORK](WORK.md) records final executed checks; [review receipts](stage14/) bind exact reviewed bytes and disclose authorship.

Native KiCad10.0.6/CAD/ERC/DRC/simulation/physical validation are **NOT RUN**, by scope. Source test success is not electrical acceptance. No site build is claimed for this isolated implementation-only change. Publication uses `[skip ci]` because the unchanged default workflow invokes excluded native work. PR286 remains draft/unmerged; PR285/260/277 stay parked, issues278–284 remain open. No architecture adoption, replication, POWER hosting, fabrication, procurement or energization follows.
