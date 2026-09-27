# OSC-ES-1 cell harness ERC notes

The generated harness is an unvalidated proposal. Every standard cell appears once with test-only port markers and four test supply flags. These markers let ERC check an isolated cell without claiming an actual module source, load, or supply implementation.

KiCad 10.0.6 reports **zero errors and six warnings**. All six are `pin_to_pin` warnings at connections between project LED symbols with KiCad electrical type `unspecified` and passive diode, resistor or open-collector pins: two each in magnitude, clip and stage indicator cells. The documented LED polarity and source-backed signal-diode polarity are mapped by physical pin. The warning concerns symbol electrical types rather than a short or missing connection. The automated harness check enforces this exact whitelist and count.

ERC cannot establish amplifier compensation, hot-fault survival, output contention, diode brightness transfer, matched resistance, rail sequencing, source allocation or board fit. Those remain `NEEDS BENCH` or source gates.
