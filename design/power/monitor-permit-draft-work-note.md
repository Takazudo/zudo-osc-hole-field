# Native monitor/permit candidate

Status: **unselected, unvalidated draft; not orderable or energizable**.
The [source](monitor-permit-draft.json) captures a six-package monitor/permit
circuit with a finite dummy load. Canonical instrument protection remains
unimplemented and issue #59 remains open.

## Captured circuit

The isolated project is in `schematic/candidates/monitor-permit/`. It contains
39 proposed physical components and an ideal test-supply declaration. That
declaration is not an inlet and KiCad omits it from the board netlist export.
The native check compares all 119 physical pins, values, footprints, complete
MPNs and manufacturers against the source. Its fresh pinned KiCad 10.0.6 run
currently has zero ERC errors and zero warnings. The
[native receipt](monitor-permit-native-report.json) lists the default checks
KiCad did not run; none of this establishes electrical performance or fit.

- TPS37044MJOFDDFRQ1 monitors +12 V and +5 V on its 0.8 V channels. Its spare
  0.4 V channel provides a coarse reference window using 7.25 kΩ over 1 kΩ.
  That channel has different accuracy and hysteresis rows. Its divider adds
  nominally 0.4 mA to the reference load.
- TLV9022DR uses the previously studied negative-rail resistor network.
  Both comparator outputs now veto REF_SENSE; detected negative faults pass
  through the supervisor reset timer. Only supervisor resets drive FAULT_N.
  See [retiming conditions](monitor-fault-retiming-work-note.md).
- REF3433TIDBVR supplies the sensing reference. Three nominal 100 nF output
  capacitors are captured as a draft choice. Their effective capacitance remains
  unestablished because the existing Murata source is unavailable.
- Two SN74HC14DR gates turn FAULT_N into a fast GOOD_FAST reset signal.
  A separate 10 kΩ / 10 nF delay and two further gates drive SN74HC74DR's clock.
  Another 10 kΩ resistor limits the retained timing capacitor's input-clamp
  current; it does not prove that supply backfeed is harmless.
- SN74HC74DR clears the output on a fault and clocks a high data level after
  the delay. Its unused half has defined normal powered inputs. MMBT3904,215
  drives a 10 kΩ dummy load from +12 V, through a 10 kΩ base resistor with a
  100 kΩ base bleed. This is not the instrument's output-isolation driver load.

Directly connecting the latch reset to the pulled-up RC node would create a
slow CMOS input transition. The buffered reset avoids that topology error.
A short raw GOOD_FAST low pulse can still clear Q while the timing capacitor remains charged,
leaving no new clock edge after recovery. Automatic re-arm is not claimed.

## Evidence and CAD

The component-evidence catalog now includes 13 exact candidate identities,
marked not fitted to the instrument. Its manual inventory has 62 lines,
48 fitted and 14 not fitted/hand fitted, with no declared placement binding.
The isolated candidate's proposed population is separate from that instrument
population. Supplier allocation is unverified.

New owner records retain exact source hashes, pin functions, conditional limits
and open application gates. Source-backed HC14/HC74 timing rows are recorded at
their actual 4.5 V / 50 pF conditions, and their SN74 temperature range is
−40…85 °C. That is not a revision of the instrument's environmental requirements.
The stale HC14 source date/revision has been corrected from its retained PDF.

The source-driven candidate assets reuse an existing 1 kΩ symbol unchanged.
Three additional family footprints use pinned KiCad 10.0.0 imports and original
8.0.0 WRL models. The resistor gets a separate candidate footprint so the
instrument's existing resistor footprint is preserved. Per-part CAD receipts
record source files, transforms and hashes. Package-family previews do not prove
exact lead fit, seating, solderability or installed thermal behavior. The family
model URI follows the existing board-project directory convention; a future PCB
under this deeper candidate directory must receive a suitable project-relative
model path before any 3D assembly check.

## Verification of this checkpoint

The guarded aggregate regeneration passes, including fresh KiCad 10.0.6 native
ERC and pin/identity checks. Sixteen focused regression tests pass. Component
validation, documentation checks, guarded build and built-site checks pass (the
site retains its existing single allowlisted link exception). Both child sheets
were exported to PDF and visually inspected; overlapping component labels were
moved and the native checks rerun. Independent source/topology and portability
reviews were completed, with their value-binding, input-closure and model-binding
findings fixed. These checks do not establish installed electrical performance.

## Open gates

The conditional [behavioral diagnostics](monitor-permit-behavior-report.json)
reproduce latch-off and re-arm for forced short/long GOOD_FAST low pulses in an ideal single-pole
RC abstraction. They enumerate all six arrival/failure orders as Boolean rail
sequences, not device-level transient simulations. Control-power loss and
subsequent recovery remain UNKNOWN. Device propagation, input capacitance,
reference trajectories and stored-charge clamp behavior are not simulated.

The report also accounts for nominal resistor currents and capacitor charge,
including the released coarse-reference divider. The separate conditional DC
allocation includes source-table active currents and the clamped divider feed;
dynamic current and actual isolation loads remain unbounded.
Original auxiliary allowances and current limits are retained.

The coarse reference window cannot certify the earlier 3.29–3.31 V precision
assumption. The combined FAULT_N capacitance is not shown to match TPS37044's
10 pF detection-delay test. TLV maximum delay/cold negative-input leakage,
reference startup/slow-slew behavior and effective bypass, HC partial-power
behavior, and the NPN's passive-base turn-off bound remain open. A 100 kΩ bleed
does not reproduce the transistor's −1 mA reverse-base switching test.

Independent inlet-return/local-GND validity and the actual 82 output, 16 sense
and 30 reference isolation paths are outside this dummy-load capture. Installed
mechanical, thermal, as-built and bench qualification remain **NOT RUN**.
