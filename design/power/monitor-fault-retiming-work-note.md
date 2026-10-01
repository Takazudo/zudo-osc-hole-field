# Negative-fault veto through the supervisor

The unselected native candidate now connects both TLV9022DR output drains to
REF_SENSE, so a detected negative-rail fault asserts the TPS37044MJOFDDFRQ1
reference channel. Only the two supervisor reset outputs drive FAULT_N. No
components or physical pins were added; the candidate remains 39 components and
119 pins. Canonical protection remains unimplemented and issue #59 stays open.

This change puts detected negative faults through the programmed nominal 10 ms
supervisor timeout. It addresses the direct path that previously let short
negative faults reset the latch without discharging its timing capacitor.
It does not establish a guaranteed minimum reset pulse or automatic re-arm.
The raw GOOD_FAST low-pulse diagnostics remain useful downstream tests; they
bypass the monitor and do not represent external negative-fault durations.

## Conditional load and threshold screen

The source-bound report `monitor-fault-retiming-report.json` uses the captured
7.25 kΩ top and 1 kΩ bottom divider. At forced REF 3.3 V and an assumed 175 mV
clamp, top current is 0.431 mA and bottom current is 0.175 mA. The comparator drains
must sink their difference, 0.256 mA total. The retained TLV VOL maximum 175 mV is
specified at 4 mA, 5 V, VCM=V− and −40…125 °C. Applying it at this different operating
point remains conditional. The lowest source UV threshold is 0.366048 V.

A zero-volt clamp draws 0.455 mA from REF, compared with 0.400 mA released. The DC
allocation therefore uses only R109..R112 for its conservative clamped feed
bound. Reference output demand still charges +5V once; original allowances
and limits are unchanged.

Both released TLV drains now load REF_SENSE. At nominal resistance, 1 µA of total
sense-node leakage moves the reference-equivalent threshold by 7.25 mV. The
retained 100 pA TLV drain-leakage row is typical at 25 °C and VPULLUP=V+; it is not
a full-temperature maximum or a bound at this sense voltage. The reference
validity study explicitly assumes zero drain leakage, with both drains released.
Its separate 350 nA sensitivity includes the TPS input only. Fault-dependent REF
load can also feed back through real reference impedance and settling into the
negative comparator thresholds. Possible chatter and coupled dynamics remain
unmodeled; the top-only DC budget does not qualify them. The broad reference
window and forced REF 3.14 V / VN −10.9 V counterexample persist.

## Timing boundaries

Healthy nominal REF_SENSE=0.4V is only 7.527% above the nominal 0.372 V UV trip.
The source reset-delay tolerance requires 10% overdrive. Thus its 7–13 ms table
interval is not an established actual recovery bound here. The report keeps
physical assertion/recovery bounds null. The 2 µs glitch-immunity entry is NOM
at 5% overdrive, not a guaranteed detectable-pulse threshold.

The reroute also adds supervisor detection latency to negative-fault assertion.
Its conditional 10 µs source maximum does not complete the TLV, logic, NPN and
isolation release chain or close the cold-collapse budget. Ground loss,
partial-power/backfeed, effective bypass, precision-reference validity and
installed timing remain open. No physical qualification or energization.

## Verification

Regressions cover the removed direct bypass, separate divider branch currents,
leakage sensitivity and the recovery-overdrive condition. The fresh KiCad 10.0.6 schematic/ERC/netlist check passes with zero errors
and warnings, and all 119 physical pins match. Fresh passive ngspice RC checks,
component validation and 51 focused regressions pass. Aggregate regeneration
and documentation build/site checks are pending in the guarded queue. Bench checks are
NOT RUN because no assembled candidate is available.
