# E5 NAND dependency and timing-evidence coverage

Source-only preparation for U4524/U4526/U4527 (all SN74HC00DR). This does not
admit moving these packages or their decouplers. The existing logic-function
brief lists package units; this executable contract adds the complete twelve-gate
DAG, external contacts and maximum gate counts from seven boundary inputs.

It independently varies STAGE_FALL, FALL, RISE, HOLD_N, TOP_RAW, CURVED and READY
across 128 Boolean assignments. These include unreachable state combinations:
they check the captured zero-delay truth functions, not a reachable-state model.
STAGE_HIGH, HOLD_ENABLE and RISE_LINEAR are compared with the pinned source
expressions; L074 is compared with the complement of RISE_CURVE. The latter
continues through stationary U4528. The shared L069 net also reaches U4528;
HOLD_ENABLE and RISE_LINEAR reach diode control networks, while STAGE_HIGH reaches
U4547. All other contacts on cluster signal nets are retained, not just these
required anchors. External contacts are not automatically classified as drivers
or permitted movement targets.

Owner pin-map correspondence and file hashes fail closed. Retained HC00/HC74/HC14
owner facts, complete conditions and source metadata are copied as observations,
with project applicability unestablished. The existing HC00 owner has no promoted
propagation-delay fact; the HC74 subset does not supply D setup/hold limits.
A physical clock cannot be inferred from the existing ideal 50-us SPICE fixture.
Gate counts are not nanoseconds. Physical delay, setup/hold slack, incremental
trace length and capacitance allowances remain null. No hazard, metastability,
load/corner or physical acceptance is claimed.

Tiny synthetic fixtures:

```sh
python3 -B scripts/checks/frozen_studies.py discover scripts/checks/mc02_logic_timing_contract
```

Actual extraction (expected runtime below 60 seconds) requires the coordinator's
separate bounded admission. This script does not establish external controls:

```sh
python3 -B scripts/checks/mc02_logic_timing_contract/audit.py --output "$PWD/.circuit-cache/mc02-logic/result.json"
```

Output must be new within this worktree's ignored cache. No files outside that
explicit output are written. No native KiCad, SPICE execution, placement search,
canonical generation, DRC, fill, adoption or manufacturing is performed.

Implementation checks: pre-edit component validation PASS (84 manual records;
445 declared placements unverified). Actual-source extraction and the full 128
source comparison have not been run by the implementation author. Tests use a
small synthetic fixture and independent Boolean references.
