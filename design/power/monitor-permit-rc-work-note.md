# Passive permit RC transient diagnostics

This unselected draft now has fresh ngspice 44.2 runs through the pinned KiCad
10.0.6 wrapper, reported in `monitor-permit-rc-report.json`. The model includes
the captured R120 and R121 (Yageo RC0805FR-0710KL, 10 kΩ each), C109 (KEMET
C0805C103J5GACTU, nominal 10 nF), and a separate 0/10 pF input-capacitance
sensitivity. The latter comes from the SN74HC14DR 5 V source-table row; it is
not a powered-off or nonlinear pin-network bound.

The source is an **ideal prescribed GOOD_FAST voltage**, with finite 1 ns edges.
No supervisor, reference, comparator, HC14 buffer, HC74 latch, transistor or
actual isolation-load model is inserted. The existing source qualifications and
all physical release limits remain open.

## Independent waveform checks

A separate closed-form two-node RC calculation follows the same finite input
ramps. At zero pin capacitance it reduces algebraically to the original single
pole and becomes independent of R121. At positive pin capacitance it checks
both capacitor and input-node voltages. The fixture declares initial voltages
and uses transient initial conditions; the checker verifies them at the actual
first sampled time instead of assuming that ngspice writes a sample at t = 0.

Seven cases run at two maximum timesteps: startup and charged short/long
GOOD_FAST low pulses at both pin-capacitance sensitivities, plus a separate
forced-discharge case. Both node waveforms must agree with the independent
equations within 50 µV, and sampled charge balance must agree within 2 pC.
Ideal Schmitt-observer crossings retain sample brackets and must remain
consistent within 5 ns after timestep refinement. They do not establish HC74 pulse capture,
reset-removal timing, real Schmitt thresholds or physical permit behavior.

For the declared nominal fixture, the 10 pF sensitivity delays the ideal rise
crossing by about 0.17 µs and the falling crossing by about 0.20 µs. Short pulses
leave the ideal observer high; longer pulses produce low and high crossings.
These are GOOD_FAST stimulus durations, not external rail-fault durations.

## Separate stored-charge diagnostic

In the seventh case, both resistor endpoints are forced to 0 V and only C109
starts charged to 5 V. Pin capacitance is deliberately omitted. Its nominal
50 µs decay constant follows from `(R120 || R121) × C109`; the ideal time-zero
current is 0.5 mA in each branch, and the initial available charge is 50 nC,
splitting equally between the two 10 kΩ paths. The report distinguishes these
time-zero values from the first sampled currents and integrates from the first
sample, checking the corresponding stored-charge change.

This is a forced resistor-boundary test, not a model of actual die clamps or a
floating control supply. It cannot bound an initially charged pin capacitor's
impulse, the other bypass/reference capacitors, surviving power, NPN release or
any real isolation path.

## Reproduction and evidence

`python3 scripts/checks/monitor_permit_rc.py --check` runs a fresh pinned native
worker every time. It requires ngspice 44.2, fresh finite waveforms with complete
time coverage, matching initial conditions and successful numerical checks.
Compact metrics, deterministic circuit-deck hashes and source hashes are
tracked; raw waveforms, decks and native logs remain under unique ignored
`.circuit-cache/monitor-rc-*` directories. No Git LFS or fabrication exports.

The deck uses the [ngspice documented table-output controls](https://ngspice.sourceforge.io/docs/ngspice-manual.pdf)
for one time column, named vectors and explicit numeric precision. The report
rounds only display metrics after the full-precision checks; source parameters
and waveform definitions remain explicit.
