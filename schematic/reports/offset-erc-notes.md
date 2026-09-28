# Offset ERC notes

Pinned KiCad 10.0.6 `--severity-all` reports zero errors and eight `pin_to_pin` warnings on each A01–A06 sheet. Each of the four locked indicator LED symbols has two Unspecified pin types that KiCad reports against its active driver; these are retained library pin-type warnings, not suppressed errors. The six sheets contribute 48 warnings to the combined instrument. Netlist parity is checked separately. Physical indicator behavior, clip threshold and output protection are not established by ERC.

The earlier suffix-A clip LED references caused KiCad's generic annotation warning. The geometry source now assigns numeric clip references (for example D13101) without moving or renaming any panel UID; full-instrument netlist export is warning-free apart from the ERC pin-type notes above.
