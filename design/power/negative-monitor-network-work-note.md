# Ground-referenced negative-rail sensing continuation

This is an **unselected passive sensing subnetwork**, not an implemented permit
or protection assembly. It replaces the direct floating-regulator assumption
with a ground-referenced candidate using TLV9022DR and REF3433TIDBVR. No installed
part, current ceiling, panel coordinate or historical native receipt changes.

The [source input](negative-monitor-network.json) captures exact resistor
identities and device pin connections. The [primary-source records](negative-monitor-network-sources.json)
bind retained manufacturer PDFs. The [calculator](../../scripts/checks/negative_monitor_network.py)
and [report](negative-monitor-network-report.json) cover the following network:

| Connection | Resistance |
| --- | ---: |
| VN to SENSE | 51 kΩ |
| REF to SENSE | 4.99 kΩ |
| SENSE to AGND | 1 kΩ |
| REF to AGND | 14 kΩ |
| REF to UV; UV to AGND | 8.06 kΩ; 1 kΩ |
| REF to OV; OV to AGND | 9.09 kΩ; 1 kΩ |

UV drives the first comparator's positive input, SENSE its negative input.
SENSE drives the second comparator's positive input, OV its negative input.
Their open-drain outputs share FAULT_N. The output pullup, receiver, reference
bypass and startup/permit circuitry remain uncaptured.

## What the passive calculation establishes

The solver uses exact rational nodal equations and all 256 independent resistor
corners. Tolerance and temperature factors multiply. With other variables fixed,
each node voltage is a linear-fractional function of any one branch conductance;
the grounded passive matrix has positive determinant. Thus the endpoint corners
enclose the resistor box. Voltage-source extrema occur at their interval ends.
This deliberately allows independent resistor extremes even though temperature
may correlate them in an actual assembly.

For the cold case, the reference output is replaced by a bounded current
source, not assumed to regulate or clamp. The nonnegative inverse conductance
matrix bounds independent currents at REF, UV, OV and both SENSE input pins.
Combining separately worst voltage and impedance bounds is conservative.

With the proposed ±10 µA per-pin envelope and forced VN between −12.48 and
+12.48 V, the cold SENSE interval remains within approximately ±0.239 V.
The sufficient uniform per-pin leakage budget is approximately 37.6 µA.
These are qualification targets and conditional DC bounds. The manufacturer's
high-impedance fault-tolerance statement covers **0 to 5.5 V**; it cannot establish
the input-current envelope at a negative cold SENSE voltage. An absolute-rating
screen does not prove functional operation, leakage or dynamic behavior.

For a proposed total reference envelope of 3.29–3.31 V, ±100 nA per powered
input and ±3 mV comparator error, the normal −12 V load band is accepted with
at least 86.706 mV and 425.628 mV remaining at its lower and upper magnitude
edges. The initial 8.87 kΩ OV leg failed this same conditional check by about
28.587 mV; 9.09 kΩ corrects that static conflict. These broad trip intervals
are not accepted emergency shutdown thresholds. Fault timing, injection,
precision and complete isolation remain to be established.

The 25 °C resistor reference temperature is still an analysis assumption.
The reference envelope includes a proposed total error requirement; typical
long-term drift, thermal hysteresis, noise and startup rows do not establish it.
Likewise, the comparator's typical input bias does not establish the proposed
powered or cold current limits. Resistor-only reference loading is reported
separately from IC current, bypass charging and the complete auxiliary budget.

## A reference can hide a bad rail

The topology has a concrete ideal counterexample: VN = −8 V and REF = 2.2 V
give SENSE = 0.232801 V, UV = 0.242826 V and OV = 0.218038 V. Both comparator
outputs release even with their +5 V supply valid. These are forced nominal
values, not a demonstrated reachable trajectory. They show why independent
reference validity is required in addition to comparator power qualification.

The current TLV9022 datasheet also removes the earlier POR feature and provides
no internal hysteresis. Its propagation and bias entries are nominal only;
the REF3433 startup entry is also nominal. No maximum response/startup limit or
universal cold-output state is inferred. The complete permit remains rejected.
REF34 section 9.2.2.3 also warns that slow input transitions can produce output
overshoot and shutdown anomalies, recommending a slew near 6 V/ms. The T variant
has no EN pin. A slower source ramp therefore does not automatically improve
this reference's behavior; the forced DC reference interval does not bound those
transients. This is a missing dynamic envelope, not a demonstrated rating failure.
Native schematic, state-sequence, dynamic, installed thermal and bench checks
are **NOT RUN**. Issue #59 remains open.
