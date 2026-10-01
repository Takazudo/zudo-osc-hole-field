# Rail-monitor continuation for issue 59

Status: **unselected study; protection remains unimplemented**. This work preserves
the original supply, current, precision and panel requirements.

The exact TPS37044MJOFDDFRQ1 option offers two paired 0.8 V channels with 7%
windows. Its 10 µs maximum detection delay has explicit overdrive, reset-delay,
supply, temperature, pullup and load conditions. The 1 ms startup entry is
nominal; adding it to a maximum reset timeout does not create a guaranteed
startup bound. TLV6700DDCR's 18/29 µs propagation rows are nominal, so that
part cannot close a maximum-delay argument using those numbers.

The first calculation checks the full allowed load-voltage bands, not only
nominal 12/5 V. It combines resistor tolerance and TCR multiplicatively, then
includes comparator accuracy,
hysteresis and conditional input bias. A monitor must both accept normal rails
and recover after a fault. The 350 nA input-current row is conditioned at a
5.5 V sense input; applying it at 0.8 V remains an explicit model condition.
The 25 C nominal-resistance reference is also an analysis assumption, not a
statement found on the retained exact resistor sheets.

Under those conditions, the remaining recovery margins are:

| Rail | Lower normal-band margin | Upper normal-band margin |
| --- | ---: | ---: |
| +12 V | 66.128 mV | 17.669 mV |
| +5 V | 36.701 mV | 10.979 mV |
| −12 V magnitude | 271.211 mV | 122.786 mV |

These downward-rounded values are conditional static results, not guaranteed
whole-circuit margins. The [generated report](rail-monitor-candidate-report.json)
also records all 27 input/receiver/signal state combinations. Its six arrival
and six failure orders are required test inventories, explicitly **NOT RUN**.

A direct floating negative monitor is also screened. TPS70933DBVR's reverse
current protection does not authorize a negative IN voltage relative to its
GND pin. If that GND is VN and VN rises above AGND, the proposed regulator
input becomes negative. Likewise, ISO7710FDR's default-low state requires a
powered receiver and the specified supply states; it is not a universal
brownout output guarantee. An externally driven HIGH on an unpowered input
can parasitically power VCC1 and also cannot borrow the default-low claim.
Its SOIC-8 pins 1 and 3 both connect to VCC1,
and pin 7 is NC.
The negative-divider sense values are unloaded predictions; actual clamp and
injection currents outside the pin rating remain unresolved.

These are constraints for the next realizable circuit, not an implementation
of the inlet-return detector, all-rail latch or output isolation. The
[inputs](rail-monitor-candidate.json) and
[primary-source records](rail-monitor-candidate-sources.json) retain exact
identities and conditions. Raw PDFs remain local and ignored. No part is added
to the installed BOM, no native receipt is rebound and no design is energized.
