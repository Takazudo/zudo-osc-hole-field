# Isolated monitor bypass candidate

Replace only C101-C108/C110 identity in the isolated monitor source with KEMET
C0603C104K5RACTU, retaining 100 nF and all nets. C109 and the global instrument
Murata population are unchanged. This is a DNP/unselected instrument candidate,
not a canonical protection implementation.

Retain the exact four-page specification (generated 2026-10-01) and C1002_X7R
(2026-09-01) family PDF with actual SHA-256 receipts. Exact nominal capacitance,
tolerance, rated voltage, dimensions, aging and insulation resistance are
conditioned facts. Family Density B lands are separately sourced. Lifecycle,
stock, effective biased capacitance, capacitor leakage, startup and installed
qualification remain open. REF still has nominal 0.3 uF, not the common-table
10 uF condition. Do not generalize simulation curves or shelf life into guarantees.

Add an incremental owner/inventory record and publication selection, a passive
symbol, dedicated footprint and maximum-body display. Pad corners are a project
choice; the manufacturer's minimum courtyard survives normalization. Enforce
catalogue capacitance parity before schematic generation. Extend fresh native
geometry checks with independent source pad/body/courtyard dimensions and a
swapped-pad negative control. Existing CAD receipts remain historical; new
candidate assets have their own derivation receipt. Refresh all affected current
source-bound reports through their generators.

Baseline: guarded aggregate replay passed in 186 seconds. Focused native
schematic ERC and pin/value/MPN checks passed with 42 components and 113 pins.
A first body check rejected the new two-corner rectangle because its helper
expects at least four points; use four explicit source-bound body edges and
rerun. Final native geometry, focused tests, generation, documentation and CI
results are recorded with the PR. No original acceptance limit changes.

Final local verification: the first aggregate/native/documentation build completed,
but its final link command used the wrong CLI subcommand (guard FAIL, exit 2,
374 seconds); it is not recorded as a fully passing run. The corrected guarded
run passed affected report regeneration, fresh native checks, 35 focused tests,
component contract, generated-output checks, site build and strict links in
63 seconds. Subsequent native-only review fixes pass 19 display cases and eight
rejected mutations, including duplicate physical pads and a 90-degree pad
rotation that leaves stored size and centre unchanged; 180-degree symmetry is
accepted. The 35 focused tests pass again. Exact final aggregate replay is a CI
gate. Capacitance and tolerance now explicitly carry the 48-hour referee time.

Independent review confirms unchanged global standard, panel lock, Murata symbol
and shared C0603 footprint. Current and RC numerical results and qualification
flags are unchanged; source hashes and the explicit zero-capacitor-leakage
assumption are the only corresponding report changes. Issues 87 and 59 remain
open, as do physical qualification and procurement.
