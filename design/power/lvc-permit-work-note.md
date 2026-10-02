# LVC permit logic and passive discharge continuation

This revision changes only the isolated, unselected monitor/permit candidate.
It remains non-orderable, non-energizable and physically unvalidated. Issue #59
and the unchanged protection/current acceptance limits remain open.

The prior HC timing tables were conditioned at 4.5 V, outside portions of the
candidate's 4.81–5.2 V normal supply. Two TI SN74LVC1G17DBVR buffers and one
SN74LVC1G74DCTR latch have timing tables explicitly covering 5 V ±0.5 V.
Retained sources are SCES351Y (October 2025) and SCES794G (September 2021).
This fixes that table-supply mismatch only: actual input edges, output slew,
loads, asynchronous clear removal and intermediate-power states remain open.
The 4.5 pF input value is typical at 3.3 V/25 °C, not a maximum. Discrete
Schmitt thresholds at 4.5 V and 5.5 V are not interpolated into a guarantee.

U104 buffers FAULT_N to GOOD_FAST; U106 buffers DELAY_IN to PERMIT_CLK.
U105's clear is GOOD_FAST, D and preset are +5 V, and Q drives the existing
NPN stage. The complementary output is unconnected. C110 supplies the extra
package's nominal bypass. The TLV comparator drains still veto REF_SENSE.

R125 provides a passive 100 kΩ DELAY_CAP-to-AGND discharge path. With nominal
10 kΩ R120 and 10 nF C109, driven gain is 10/11 and the time constant is
90.91 µs. Disconnecting the drive changes that constant to 1 ms at zero pin
capacitance and leakage. An explicitly assumed 20 µA injection instead leaves
a 2 V equilibrium. No actual leakage bound, minimum off interval, powered-off
LOW or automatic restart is established by those diagnostics.

The SN74LVC1G17 ICC input condition is VI=5.5 V or GND, with IO=0;
it is not a general VI=VCC condition. Both U104 and U106 actual HIGH inputs
lack direct application coverage. U106 also retains a divided steady HIGH.
Additional steady input-stage current remains an open DC budget item. The 210 µA device table-row sum and 6.699 mA largest +5 V screen
remain conditional; the ΔICC row at VCC−0.6 V is not extrapolated.

The new DCT footprint follows TI drawing DCT0008A 4220784/D, physical PDF
indexes 18–20 (printed page labels absent): 1.1 × 0.4 mm pads, R0.05 corners,
row centres ±1.9 mm, pitch 0.65 mm. Its 3.1 × 3.1 × 1.3 mm body display omits
leads/seating and excludes the drawing's mold/interlead flash allowances.
The DBV part reuses the retained SOT-23-5 family footprint and display model.
Neither is physical-fit qualification.

The manual inventory now contains 64 lines, 48 fitted and 16 not fitted/hand
fitted. Both new identities are not fitted to the instrument. The candidate's
42 physical components and 113 pins are a separate proposed population.
Original HC owner records and all 438 fixed panel centres are preserved.

Sixty-four focused regression tests pass. Both child sheets were exported to
PDF and visually inspected; labels and package pins remain readable.
Fresh KiCad 10.0.6 ERC reports zero errors/warnings with full candidate pin and
identity parity. Twenty-two fresh ngspice 44.2 runs agree with independent RC
equations, charge conservation and timestep refinement. Native display checks
cover 18 cases and five rejected mutations. Independent electrical and CAD
reviews identified the pad-corner, flash-scope and sustained-HIGH current gaps;
those findings are corrected. The prepared batch passes guarded aggregate regeneration,
documentation checks, build and strict site checks (guard exit 0; the one existing
workbench template-link exception is allowlisted). Applying it atop the merged
display-model/source-epoch fix passes 79 focused tests and generated-output checks;
an independent integration review found no blockers. Exact-head CI remains the
final combined-source check before merge. Installed electrical, dynamic and bench
qualification is NOT RUN.
