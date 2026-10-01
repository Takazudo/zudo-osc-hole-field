# Coarse reference-validity integration

The TPS37044 reference channel in the isolated monitor/permit draft is useful
for detecting large reference errors, but it does not establish the narrow
3.29–3.31 V assumption used by the negative-rail network and current studies.
`monitor-reference-validity-report.json` now calculates that mismatch from the
captured divider, exact resistor evidence and the supervisor's **0.4 V** channel
accuracy/hysteresis rows. It does not reuse the 0.8 V rows.

With zero sense current and the stated resistor-temperature assumptions, the
possible settled retained-good reference extent is approximately 3.001–3.610 V. The
common static recovery interval across those corners is about
3.191–3.395 V. The first interval encloses independent device/resistor corners;
it is not the exact acceptance window of a single physical device. Recovery
means the strict interval interior with valid control supply, the other paired
sense inputs healthy or correctly unused, and sufficient settling. Neither
interval bounds behavior during startup or fault-detection delay.
A separate 350 nA input-current sensitivity retains the source's 5.5 V test
condition and leaves its applicability near 0.4 V unproved.

Propagating the wider retained-good extent through the existing negative-network
corner calculation gives UV trip magnitudes about 9.542–12.690 V and OV trip
magnitudes about 11.655–15.209 V. Both normal-band margins become negative.
The original narrow-reference report is preserved; its assumption is now
explicitly shown to be unestablished by this coarse monitor alone.

A forced nominal DC counterexample uses REF = 3.14 V and VN = −10.9 V, with
+5 V and +12 V present. The coarse reference sense is 0.380606 V; the negative
sense is 0.340598 V between thresholds 0.311199 and 0.346578 V. Both ideal
monitors can report healthy, although the negative rail is outside the required
normal band. This demonstrates an assumption gap; it does not claim that this
specific trajectory has occurred or is reachable in the physical assembly.

## Required continuation

Reference validity must come from an applicable reference/source/load argument
and startup qualification, or a separately realizable validity circuit. Do not
select the coarse monitor as proof of precision-reference validity, and do not
promote the earlier narrow-reference margins to complete permit acceptance.

REF34 source details must stay separate: the 6 ppm/°C temperature coefficient
uses the box method across the full 165 °C specified range; it is not a local
slope from 25 °C. Its line-regulation and load-regulation rows use different
input/load conditions. Adding those rows does not by itself bound an input ×
load interaction. Common table capacitance is 10 µF; the current draft has
nominal 0.3 µF whose effective capacitance is unqualified. The 2.5 ms startup
figure is nominal, and slow-slew/retained-charge behavior remains open.

The integration check binds the actual captured resistor/device identities,
rejects topology and evidence drift, and leaves canonical protection and
qualification false. No PCB, physical transient, thermal or bench qualification
is included.


Verification: seven focused regression tests cover the assumption gap,
counterexample, nonmutation of the original study, source sensitivity,
connectivity binding and JSON-key ordering. Guarded full regeneration, component
validation and fresh native candidate checks pass. Independent source/arithmetic
review found no remaining scoped blocker. Physical dynamic checks are NOT RUN.
