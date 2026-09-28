# MIX4 VCA calibration work note

Issue #50, Wave 10. The affected circuit is the M4A/M4B `mix4_vca` family;
the fixed panel bindings and schematic topology did not change. Review this
topic against `base/osc-hole-field` in the shared PR #46 before merging.

The retained TI/National `LM13700.MOD` SHA-256 is
`666df501773da5e65f7fd3b3c806b2c1ae7770784685dd8191a9df33b382f390`.
Its single-OTA pin sequence matches OTA1 pins 1, 2, 3, 4, 5, 6, 7, 8, 11 in
the exact LM13700M/NOPB pin map. The old zero-offset fixture reproduced
+6.897454/−11.91074 V at four coherent 5 V peak inputs and +5 V command,
but returned success despite exceeding the ±10 V envelope.

The recommendation is to retain the existing offset and TIA trims. The
fixture now mirrors their captured resistor network and freezes an unloaded
+2.7 V offset wiper and 109 kΩ TIA feedback across all vectors. It models
+9.84187/−9.877432 V at full scale. The gain-law ±10% test is a bounded
fixture diagnostic, not a hardware tolerance. Zero bias is imposed for a
negative command request; the real PNP servo and clamp are not simulated.

The alternative of changing the circuit to cancel half-command feedthrough
was not justified: the single-OTA model predicts +0.5029 V at zero input and
2.5 V command under the fixed trim, but there is no numeric hardware
feedthrough requirement or measured result. This residual is explicit and
open. A complete servo, real opamp headroom, dual-package, temperature,
stability, output load and physical calibration remain untested. These risks
must be reviewed before treating the design as anything beyond an
unvalidated draft.
