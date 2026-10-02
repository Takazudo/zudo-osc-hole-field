# Captured circuit to model binding

This batch repairs two reproduced correctness gaps in the precision-output and
MIX4 model producers. Grounding the captured precision amplifier's noninverting
input previously left the simulated input unchanged. Changing captured MIX4
TIA feedback from 100 kΩ to 200 kΩ also left its simulated 100 kΩ resistor
unchanged. The current captured circuits and retained decks agree; these were
missing guards against circuit/model drift, not observed hardware failures.

The precision producer now checks the complete five-part template and its nine
compiled units, including exact selected amplifier, primitive types, physical
pin maps, supplies and instance identities. The 100 Ω feedback resistor and
1 nF capacitor still have unresolved exact-value MPNs. A change to a valid
feedback value reaches the deck; unsupported topology or identity changes fail
before invoking the oracle. The historical 10 kΩ/100 pF failing fixture remains
independent of the current source.

The MIX4 producer now checks the captured summer, OTA divider, offset trim,
IABC series resistor, physical OTA1 pins and TIA connections. Its resistor
values and trim ranges are intentionally locked to the reviewed fixture;
retuning the source requires reviewing and regenerating that fixture. Extra
fitted branches on modeled internal nodes fail. Four coherent input sources,
ideal references, imposed current servo, ideal amplifiers and the 100 kΩ load
at SUM_POSTVCA remain explicit model substitutions. This is not a complete
input-to-jack or servo/headroom model.

Reports retain the evaluated source projection and exact model/deck hashes.
Portable checks compare those projections and decks with the current source;
missing or duplicate vectors and nonfinite simulator measurements fail. Source
bytes are checked for changes during execution. This does not reinterpret
historical source epochs or extend the model boundary to excluded circuits.

Validation results are recorded after the fresh pinned runs. The original
failure fixtures, fixed calibration, numerical limits and all physical gates
are preserved. Issues #49 and #50 remain open pending acceptance reconciliation;
actual protection in #59 and physical circuit/PCB qualification remain open.

## Fresh verification

Entry canonical regeneration passed in 325 seconds with no tracked drift.
Component validation passed before and after the implementation. The guarded
native batch passed in 50 seconds: precision 12/12; the actual original-network
nonzero-exit regression and strict threshold test; thirteen mixer decks; and a
fresh 24-case candidate PhotoMOS diagnostic. The following 52 focused tests
passed, including retained source/deck checks and rejection of changed earlier
decks, malformed compiled packages, nonfinite vectors and zero-exit simulator
errors. Two earlier queued attempts were canceled before execution to apply
review fixes (exit 143, NOT RUN).

The existing precision and mixer report fields are exactly unchanged after
excluding newly added binding fields and schema versions. All thirteen retained
mixer decks are unchanged. The candidate PhotoMOS report's only changed field is
the hash of its updated measurement helper producer; every case, numerical result
and qualification flag was reproduced by its fresh native run. Its seven optional
local manufacturer-PDF cache checks were NOT RUN in this clone; the retained
source receipts and all circuit assumptions are unchanged. Prior reports and
complete baseline/native logs are retained in the session review archive.

Final combined-head CI must run the complete portable/native suite and canonical
regeneration. No prior native or physical acceptance is inferred merely from an
updated hash; the refreshed candidate remains a static-contact diagnostic.
