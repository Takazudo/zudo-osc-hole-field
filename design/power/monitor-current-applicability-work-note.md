# Buffer current source applicability

This bounded correction keeps the isolated monitor/permit topology, exact parts,
current allowances and qualification gates unchanged. It corrects prose that
called the SN74LVC1G17 ICC test a general rail-level input condition and singled
out only U106 as lacking application coverage. Both U104 and U106 actual HIGH
inputs remain unresolved.

The retained TI SCES351Y, October 2025, physical PDF index 5 / printed page 6
specifies ICC at VI=5.5 V or GND, IO=0 and VCC=1.65–5.5 V. The PDF SHA-256 is
`c76fa723fac4502423967a1aa087dd669106b52b8de620c024b26e56f5d59309`.
The existing owner fact retains these exact conditions. The current checker now
rejects a reinterpretation of that row as VI=VCC. The separate 3.6 V ICC row and
VCC−0.6 V DeltaICC test point are not used as arbitrary-input current bounds.

Under ideal rail-level drive and zero input current/leakage, U104's HIGH input
is 4.81–5.2 V. The existing R120/R125 divider gives U106 a conditional HIGH of
4.356564–4.744184 V. These endpoints use the catalog's independent ±1%
resistor tolerances and 100 ppm/°C coefficients, with the existing assumed
25 °C reference and −40…125 °C analysis envelope: resistor factors are
0.9801 and 1.0201. Gain bounds are R125_min/(R120_max+R125_min) and
R125_max/(R120_min+R125_max). R121 has no steady drop only under the stated
zero-input-current assumption. These are model intervals, not bounds on actual
loaded outputs or device inputs.

The original 210 µA source-row sum and 6.698818 mA largest conditional +5 V
screen remain unchanged. A modeled input-test-point match still does not
establish the actual input, load or temperature conditions. Extra steady
input-stage current, switching current, retained charge, partial-power states
and physical qualification remain open in issue #59.

The separately considered R125 relocation is not implemented. Although it
would remove the imposed steady divider and retain a passive discharge path,
it makes the illustrative nominal high-impedance LOW crossing slower
(0.893 ms to 1.087 ms). Those ideal threshold calculations are not a qualified
restart deadline or a deterministic violation of an instrument requirement.
No resistor relocation, buffer substitution or supply-feed resistor is selected
by this reporting correction.

Focused regressions cover both input intervals, source-condition changes,
resistor-corner sensitivity, invalid arithmetic domains, and refusal to promote
a modeled test-point match to qualification. The clean entry aggregate passed in 301 seconds. The changed-source guarded
aggregate, native checks, documentation checks, build and strict site check
passed in 263 seconds (one existing workbench link exception remains
allowlisted). All 76 focused monitor tests pass. A final report-only spacing
correction was followed by report regeneration, the focused suite and component
validation; it changes no native producer input. Every pre-existing numerical
value and Boolean qualification flag in the six regenerated monitor reports
is unchanged. Exact-head CI remains required; software checks do not qualify
the circuit.
