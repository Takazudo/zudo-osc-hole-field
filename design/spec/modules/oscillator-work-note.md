# Issue #29 work note

Requested: complete draft capture of the oscillator family and shared octave reference, following the latest OSC-ES-1 issue amendment. No production or physical-validation claim.

Read the issue/epic, canonical workflow, imported contracts, current cells, pilot, exact placement lock and retained IC pin maps. Initial regeneration produced no tracked changes; initial circuit contract passed with 11 manual inventory records and CAD pin checking enabled.

Retained ALFA RPAR's own 2020 v7 AS3340/AS3345 document from the domain named in its header. Confirmed AS3340D SOIC-16 identity, all sixteen pins, package drawing and application diagram; replaced the old source-unavailable pin receipt. Its negative-supply wording is contradictory, so the draft uses a locally buffered -5 V supply and leaves actual rail-order behavior as a hardware gate. Factory sourcing remains open.

Implemented one shared oscillator source family with its local supply declaration, five instances, and a single shared reference family. Packed compatible op-amp sections only within the same local circuit island, completed unused channels as grounded followers, and counted whole packages. Standard-cell connections and value-specific MPN boundaries are explicit. The generator's 99-ordinal stride is preserved; additional resistors use the RB prefix. This is source-owned design logic, not a generator change.

Reserved indices: H1/H2/pilot power remain 1–3; O1–O5 use 11–15; OCTAVE_REF uses 16. Additive registration is in `design/spec/instrument.py`. Panel UIDs are resolved from the lock; no geometry edits.

Checks: `check_oscillator.sh` regenerates and checks full master ERC/netlist parity, 80 UID bindings and five separate timing nets. `test_oscillator.py` checks source identity, topology, sensitive nodes, reference endpoints, ratios, package completeness and model supply naming. `run_oscillator_spice.py` generates/runs ideal-reference, ideal-scaling and generic-pair decks. `build_oscillator_current.py` produces per-instance and shared planning currents with guaranteed maxima explicitly unestablished.

Review corrections: explicitly tied the two ladder endpoints to their drivers; bounded sine trim range covers model output calibration; prevented positive and negative supply names from collapsing in generated SPICE; used explicit triangular PWL sources instead of zero-width PULSE defaults; corrected unpatched lower command frequency; fixed unittest discovery imports; reused exact known 1k/10k trimmer and matching 100k/100n/100p identities.

Remaining: no AS3340 vendor model or bench unit; V/oct/temperature, sync, PWM limits, real waveform levels, factory sourcing, unmatched passive MPNs, output and harness stability, buffered VEE startup/fault behavior and actual maximum rail currents remain open. Shared full build is manager-owned. No browser, board placer, inventory, supplier action or shared issue tracker was changed.

## Issue #62 local reference fanout (2026-09-28)

Baseline circuit validation and full regeneration passed without tracked drift.
Ten 10 kohm trimmers previously loaded the global pair directly (13.333 mA at
minimum retained resistance, before panel and fixed loads). Three local precision
pairs per oscillator now isolate panel/fixed, BASE trim and SINE trim loads. All
original control values and sensitive/timing islands remain; 438 centres are fixed.

Source: oscillator.py and oscillator-reference.json. The source-derived fanout
report bounds all six outputs, shared source loads, connector branches, reverse
current rail attribution, driver swing/headroom and exact package/bypass refs.
Two added OPA4197IPWR quads per oscillator add 60 mA Iq per analog rail; a separate
25 mA output reserve is additive to all previous reserves. No source limit changed.
The historical three-source candidate A is now rejected at -15.344091 mA margin;
the selected EXT requirements still pass all existing current/return/loss limits.

Foreground review corrections: include nonprecision receiver-current allowance,
book reversed current on the opposite rail, trace a real amplifier behind each
allowed reference isolation resistor, refresh all dependent count/rail reports,
and fix a pre-existing MDX less-than parsing error exposed by the required build.
The retained TI model passes 24 powered load/passive/rail cases. Physical loaded
precision/temperature, exact 100 ohm/1 nF identities, startup and partial-power are
NOT RUN. #59 protection and #57 physical source qualification remain OPEN.
