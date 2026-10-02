# AO model source and illustrative error budget

Issue 26's ideal DC runner checked resistor values but ignored captured wires.
A changed summer connection or amplifier polarity could therefore keep the same
seven passing ideal decks. The new source projection checks exact participating
roles, fitted state, passive values/nets, amplifier unit pins, pot polarity and
additional internal branches before execution. The report names the projection
and excluded physical/input/output behavior. Canonical regeneration runs this
bounded ideal model so future source mutations cannot silently retain a pass.

The AO page also retained the superseded 10 kΩ / 100 pF output network and described
a separate wiper buffer that is not fitted. The selected output uses 100 Ω jack
sense and 1 nF local feedback. The wiper instead feeds the attenuverter's positive
input through 1 kΩ with a 10 MΩ return.

Independent source review confirmed the five nominal IN-path offset coefficients
(2β−1), 2β, 2, −4, 2: the three-input summer has noise gain 4, not 2. Their absolute
sum is bounded by 11 for the stated nominal wiper fraction. The conditional
illustration becomes 1.1 mV for 100 µV per stage and 1.375 mV for 2.5 µV/°C over
50 °C. It omits the OFFSET input, reference/manual and jack-output stages and is
not a complete tolerance, drift or pitch-CV qualification result.

The exact Texas Instruments OPA4197IPWR evidence owner was read. The retained
SBOS737C source was reacquired from TI with the existing SHA-256
27653a7d5e965cbb2d23f7998919ebd774efd5cd3e126b8f0881469ae91166fd;
no source hash or component selection changed. Printed page 7 confirms the VOS
row's ±18 V/25 °C condition and drift row's ±18 V, VCM=(V+)−3 V condition;
those cannot silently become whole-cell ±12 V guarantees.

Entry component validation and guarded aggregate regeneration passed; baseline
206 seconds, no tracked drift. Seven focused source-mutation tests pass; duplicate capture identities also
cannot disguise an extra branch under a checked part key. Independent review also identified
coherent private wiper/sense aliases into named circuit nodes; those are now
rejected, with valid private renaming retained as a positive control. The first
post-change heavy run was canceled while still queued (NOT RUN) to include this
fix before execution. Guarded full regeneration, native master ERC/netlist and AO capture checks,
original seven ideal decks/results equality, documentation build and strict
site checks passed in 306 seconds (one existing link exception). Final
combined-parent checks are recorded in the PR. No circuit, hardware coordinate, source requirement, simulation
threshold or fabrication output changes. Complete current maxima and physical
qualification remain open; issue 26 is not closed by this bounded correction.

The fresh native capture keeps all 48 AO warnings and zero ERC errors. It refreshes
the older source/netlist hashes and reports 180 other master warnings (formerly
192), matching the current 228-warning master. No warning checker or criterion
was weakened; source/schematic bytes are unchanged by this task.
