# Peripheral conductor admission

Status: mandatory native/source admission implemented; full numerical runs and
physical contact/material/current/common-path acceptance remain separate.

The actual EL prerequisite uses two 35 um foils, a 0.33 mm dielectric and
0.4 mm total depth. Its sole source-owned 0.7/0.3 mm AGND via connects F/B at
source (218,166) mm. All 72 source contacts (60 own returns and 12 GH grounds)
must be connected, with zero native rules/parity and exact fixed hardware,
physical pad/hole/reservation, source/companion and board/export bindings.
The reference is exactly J900379:2 on B.Cu, not a physical mainland or sink.

`solve_conductor_volume.py` requires `--peripheral-receipt` and
`--peripheral-manifest` before extraction for all six actual peripheral IDs.
It requires `--port-limit 0`; EL also requires `--include-loads`. The complete
EL diagnostic has 71 balanced functions. The five O boards have seven GH
contacts and six functions each, with their source-specific B references.
There is no default sampled or omitted own-load mode. All native/helper/profile
bindings enter the cache and result; full dependency checks run again before
publication. The prerequisite does not select any physical uniform-current
profile or ideal GH termination.

Native EL v3 is the current positive authority after correcting the source
added-copper summary. Earlier EL v1/v2 and all older O receipts retain their
original bytes; changed generator/source epochs require fresh native authority,
not metadata rebinding. No full EL/O solve is authorized by unit-test success.
A bounded initial nominal EL scope, if dispatched, is coarse/fine 2/0.25 mm,
refinement 1, adaptive regions and every source function; resource guard and
same residual/conservation/energy gates remain mandatory. Actual source/contact
families and the joined observation proof continue to control issue38 closure.
