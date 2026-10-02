# Sample-and-hold RC source binding

This follow-up to issue #22 binds the ideal post-hold lag diagnostic to the current captured circuit. The old runner read a static deck and repeated fixed 2.2 kohm/500 kohm/500 nF constants without inspecting the capture. Those values still matched the current source; no historical native failure or present numerical mismatch is alleged. An in-memory source-value mutation demonstrated that the old fixture could remain unchanged.

The new contract checks both unity followers, the minimum resistor, the B504 five-pin rheostat with strapped wiper and unconnected body pins, and all five fitted lag capacitors. It rejects missing/duplicate/DNP members, unsupported primitive identities, changed feedback/straps, private-node aliases and unprojected internal connections. Private-net renames are supported. Rmin and the capacitor sum come from captured values; nominal pot resistance comes from the exact B504 owner's retained fact, preserving its room-temperature and ±20% conditions without treating the nominal model as a tolerance sweep.

The runner generates fast/centre/slow cases at nominal resistance fractions 0/0.5/1, with unchanged ideal-buffer, pulse, 100 kohm fixture-load, transient and 1% comparison settings. The existing 1 milliohm fast-endpoint numerical resistor is explicitly recorded. The input and output boundaries exclude LF398, trigger logic, real output/indicator loading, leakage, contact/taper/tolerance and amplifier limits. Actual circuit source and hardware placement are unchanged.

Native parsing now rejects nonfinite times, non-increasing thresholds, invalid analytic times/errors and reported ngspice error/abort states even with zero process status. This closes a demonstrated arithmetic false-pass path: infinity minus infinity yields NaN, for which the old `error > 0.01` comparison is false. Regression inputs are synthetic; no historical native occurrence is asserted.

Canonical regeneration refreshes the generated lag deck and report. Physical acquisition, hold accuracy, direction/fit, factory calibration, stability, fault and complete rail-current maxima remain NOT RUN/unestablished as documented. Validation and exact retained receipt paths are recorded in the PR and foreground review log.

Entry component contract PASS (66 manual records); guarded baseline PASS in 227 seconds with no tracked drift.

The first source commit intentionally awaits native-generated deck/report refresh. The local native waiter was confirmed queued and canceled with exit 143 (NOT RUN) after extended contention. The authorized CI route uses the actual pinned aggregate oracle and its retained regeneration patch; generated drift is a failed check until the inspected outputs are committed and exact CI passes. Main PR122/123 was integrated before this source commit.
