# Filter native ERC notes

Unvalidated draft — not bench tested. The authoritative input is
`design/spec/modules/filter.py`; never repair generated KiCad files by hand.

Run `bash design/spec/modules/check_filter.sh`. KiCad 10.0.6 reports zero
errors and eight warnings per F1/F2/F3 instance (24 total). Each of the four
retained panel white-LED symbols has two pins typed `Unspecified`; connection
to the ordinary passive protection/resistor network yields `pin_to_pin`
warnings. Their anode/cathode mapping is preserved from the source-owned
symbol. The checker verifies each warning involves an actual bound panel LED
reference and the expected warning type. No ERC suppression was added and no
pin type was changed to silence the oracle.

The pre-existing H1/H2 sheets contribute twelve warnings of the same class.
Other families are outside this report. The complete assembled netlist matches
the source spec; the six filter integrator nets remain separately scoped under
F1/F2/F3. All 54 fixed panel UIDs are bound once.

ERC and connectivity parity do not establish analog operation, model fidelity,
physical LED orientation, board routing, power-off protection or supply budget.
See `architecture/osc-block-vcf` and `design/reports/spice/filter.json` for model
boundaries and unresolved hardware gates.
