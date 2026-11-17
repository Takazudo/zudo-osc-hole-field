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
with project applicability unestablished. The source rebind at
`109c8914d54c918f71a665f8af49e0b635f9133f` adds four conditioned table facts:
HC00 propagation maximum 23 ns and output-transition maximum 19 ns, plus HC74
D setup requirement 25 ns and D hold requirement 0 ns, all at the retained
4.5 V / -40..85 C table corner and with their full measurement conditions.
The HC00 switching-test numeric load remains unspecified; its 19 ns output
maximum does not prove a cascaded input meets the source <6 ns test edge.
The HC74 setup row is printed under MAX (the worst required setup), while hold
is a MIN requirement. Neither supplies minimum CLK-to-Q/contamination delay.
Actual voltage, load, edge, clock/skew and corner applicability remain open.
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

Historical execution: implementation commit `991296b9` passed the coordinator's
bounded extraction and 128 source Boolean comparisons in run
`df0b1dcc6796446da47de553dc536fff`, using the original owner-fact pins from source
`36cd059c224b49f2e2266bf9d6087263a86fb752`. That receipt remains evidence for those
bytes; it does not claim to have consumed the four subsequently retained facts.
The rebind changes only two owner-fact hashes among the fourteen input pins;
the other twelve inputs, including the Boolean source graph, are unchanged.
Full extraction on the rebound metadata has NOT RUN during this update.

Pre/post component checks pass (84 manual records; 445 declared placements
unverified). Tiny fixture tests use independent Boolean references and verify
that even the four new conditioned timing facts cannot populate physical slack
or layout budgets.
