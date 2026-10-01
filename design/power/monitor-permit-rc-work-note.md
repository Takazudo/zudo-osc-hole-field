# Passive permit RC transient diagnostics

This unselected draft now has fresh ngspice 44.2 runs through the pinned KiCad
10.0.6 wrapper, reported in `monitor-permit-rc-report.json`. The model includes
the captured R120 and R121 (Yageo RC0805FR-0710KL, 10 kΩ each), C109 (KEMET
C0805C103J5GACTU, nominal 10 nF), R125 (100 kΩ bleed), and a separate
0/4.5 pF input-capacitance sensitivity. The latter is typical at 3.3 V/25 °C
for SN74LVC1G17DBVR; it is neither a maximum nor
not a powered-off or nonlinear pin-network bound.

The source is an **ideal prescribed GOOD_FAST voltage**, with finite 1 ns edges.
No supervisor, reference, comparator, LVC buffer, LVC latch, transistor or
actual isolation-load model is inserted. The existing source qualifications and
all physical release limits remain open.

## Independent waveform checks

A separate closed-form two-node RC calculation follows the same finite input
ramps. At zero pin capacitance it reduces algebraically to the single
pole with R120 in parallel with R125 and becomes independent of R121. At positive pin capacitance it checks
both capacitor and input-node voltages. The fixture declares initial voltages
and uses transient initial conditions; the checker verifies them at the actual
first sampled time instead of assuming that ngspice writes a sample at t = 0.

Eleven cases run at two maximum timesteps: startup and charged short/long
GOOD_FAST low pulses at both pin-capacitance sensitivities, plus a separate
forced-discharge case and four open-drive cases. Both node waveforms must agree with the independent
equations within 50 µV, and sampled charge balance must agree within 2 pC.
Ideal Schmitt-observer crossings retain sample brackets and must remain
consistent within 5 ns after timestep refinement. They do not establish LVC latch pulse capture,
reset-removal timing, real Schmitt thresholds or physical permit behavior.

Short pulses leave the ideal observer high; longer pulses produce low and high
crossings. These are GOOD_FAST stimuli, not external rail-fault durations. The
bleeder gives a driven final voltage of 4.545 V for an ideal 5 V source, with a
90.91 µs nominal time constant at zero pin capacitance.

## Separate stored-charge diagnostic

In the seventh case, both resistor endpoints are forced to 0 V and only C109
starts charged to 5 V. Pin capacitance is deliberately omitted. Its nominal
47.619 µs decay constant follows from `(R120 || R121 || R125) × C109`; the ideal time-zero
current is 0.5 mA in each 10 kΩ branch and 0.05 mA in R125, and the initial available charge is 50 nC,
splitting into 23.8095 nC per 10 kΩ path and 2.38095 nC through R125. The report distinguishes these
time-zero values from the first sampled currents and integrates from the first
sample, checking the corresponding stored-charge change.

This is a forced resistor-boundary test, not a model of actual die clamps or a
floating control supply. It cannot bound an initially charged pin capacitor's
impulse, the other bypass/reference capacitors, surviving power, NPN release or
any real isolation path.

## Disconnected logic drive

Four additional cases remove the drive-to-ground source; a floating series
current probe must carry zero current. R125 then provides the only external
discharge path. Two cases assume zero injection; two add an explicitly assumed
20 µA current source to DELAY_CAP. At zero pin capacitance the nominal time constant is 1 ms.
Charge conservation includes the bleeder in every case. The zero-injection test assumes zero
leakage; the separate illustrative 20 µA injection sustains a 2 V plateau
through 100 kΩ. Neither that injected current nor zero leakage is a guarantee
for the actual partially powered circuit. Tolerance/leakage extremes, minimum
off duration, and automatic restart remain unqualified.

## Reproduction and evidence

`python3 scripts/checks/monitor_permit_rc.py --check` runs a fresh pinned native
worker every time. It requires ngspice 44.2, fresh finite waveforms with complete
time coverage, actual sample spacing within the declared timestep, matching
initial conditions and successful numerical checks. Parameters are evaluated
from frozen source bytes, with unchanged-source verification through the run.
Separate forced-discharge branch currents must also satisfy Ohm’s law.
Compact metrics, deterministic circuit-deck hashes and source hashes are
tracked; raw waveforms, decks and native logs remain under unique ignored
`.circuit-cache/monitor-rc-*` directories. No Git LFS or fabrication exports.

The deck uses the [ngspice documented table-output controls](https://ngspice.sourceforge.io/docs/ngspice-manual.pdf)
for one time column, named vectors and explicit numeric precision. The report
quantizes only display metrics on explicit physical-unit grids after the full-precision checks; source parameters
and waveform definitions remain explicit.


Verification: fresh 22-run native simulation and independent equations pass,
including open-drive zero-current rejection and separate forced-branch checks.
Final aggregate replay and source review are pending for this revision.
Physical dynamic, installed and bench qualification remain NOT RUN.
