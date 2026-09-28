# Offset ERC notes

Pinned KiCad 10.0.6 `--severity-all` reports zero errors and eight `pin_to_pin` warnings on each A01–A06 sheet. Each of the four locked indicator LED symbols has two Unspecified pin types that KiCad reports against its active driver; these are retained library pin-type warnings, not suppressed errors. The six sheets contribute 48 warnings to the combined instrument. Netlist parity is checked separately. Physical indicator behavior, clip threshold and output protection are not established by ERC.

KiCad netlist export additionally emits a generic annotation warning for the locked suffix-A clip LED references (for example D1310A). A read-only mixer-sheet diagnostic confirmed these references cause the message; ERC and pin/net parity still pass. An integration fix will assign numeric KiCad-compatible references without moving or renaming any panel UID.
