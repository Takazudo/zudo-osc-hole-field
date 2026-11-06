# Stage 3 independent all-five crossing identity audit

The audit passes source identity and coverage checks. The controlling overlength findings remain genuine findings of the declared placement/allocation model; they are not explained by substituting an O1 reference for an O5 circuit. Electrical, native and physical acceptance remain OPEN.

The audit loads the live canonical `design.spec.instrument.specification()` and computes each reference with the canonical designator function. It then compares every physical unit/pin/net/region against `design/reports/io-partition.json`. All1,435 oscillator unit records (287 per instance) plus42 shared-reference unit records agree. Nonphysical flags are accounted separately from the retained physical ledger. The retained interface packet previously supplied explicit instance mappings only forO1/O2/O5; this new audit supplies allfive, includingO3/O4, directly from live source rather than numeric reference offsets.

`stage3-crossing-audit.json` maps all495 endpoint-path rows across the four retained alternatives to actual instance/ref/pin/net identities. All225 rows of the five-instance alternative are included. It independently reconstructs expected crossing endpoint combinations from live units, permitted source nodes and each functional link, detecting an omitted receiver even if another receiver keeps the link present. All80 locked jack/control UIDs agree with live panel references, positions and rotations. Front jack identity is checked against the actual packed amplifier unit's LogicalCellKey; control endpoint identity is checked against the exact PanelUid. Shared source drivers are resolved independently from output-typed canonical symbol pins when the earlier partition crossing table lacks a shared-middle split.

Every return group is also mapped to actual AGND reference/pin identities. The audit checks complete owner-group endpoint membership, return contact polarity, adjacent DIN return membership and preservation of unknown impedance. These are inventory assertions, not proof of common-plane continuity, current sharing or a completed return network.

## Controlling negative endpoints

The table uses actual references, not template O1 labels. Segment decomposition includes all declared front trace, GH pair, toleranced wire, middle trace, DIN and rear trace terms.

| Instance / actual net | Actual endpoint pair | Actual panel UID | Allocation mm |
|---|---|---|---:|
| O5 `/O5/C42d8cd_W` | `RV508:2` ↔ `R1525:1` | `C:O5.PWM±` | 488.311094 |
| O5 `/O5/Ca449b7_W` | `RV507:2` ↔ `R1533:1` | `C:O5.PW` | 487.293802 |
| O5 `/O5/PWM_REMOTE` | `RV508:3` ↔ `R1523:2` | `C:O5.PWM±` | 480.398896 |
| O5 `/O5/C1eb779_W` | `RV506:2` ↔ `R1519:1` | `C:O5.FM±` | 456.978508 |
| O3 `/O3/C42d8cd_W` | `RV308:2` ↔ `R1325:1` | `C:O3.PWM±` | 448.736302 |

The controlling PWM wiper is RV508 pin2 → R1525 pin1 on `/O5/C42d8cd_W`, sourced by `C:O5.PWM±`. Its decomposition is:

- `DIN_mm`: 25.000000 mm.
- `GH_pair_mm`: 15.000000 mm.
- `front_trace_mm`: 16.002691 mm.
- `middle_trace_mm`: 295.209809 mm.
- `rear_trace_mm`: 74.098594 mm.
- `wire_max_mm`: 63.000000 mm.

These terms total488.311094 mm. The adjacent PWM_REMOTE path uses RV508 pin3 and R1523 pin2; it must not be confused with the raw wiper on pin2. The exact identities and canonical source-node list are retained for every row.

## Applicable limits and cap status

`design/standard/electrical-standard.json` remote_controls supplies0.3 m and1e−9 F for permitted buffered signals/references, wipers into high-impedance receivers and conditioned logic/returns. The actual per-instance allowed_crossings records independently retain0.3 m/1e−9 F for these candidate crossings. The architecture packet applies the limit to the complete remote path, including traces, connectors, wire and probe. PWM, PWM_REMOTE, all five raw-wiper functions per oscillator and every applicable shared-reference branch receive no exemption or relaxed limit.

All nine shared networks (REF5, REFN5, GATE_REF and OCT0–5) have explicit five-instance coverage. Aggregate direct capacitance remains unknown: common source segments must be counted once and combined with actual branch conductor/contact/trace/probe contributions. Counting endpoint rows or adding duplicated all-pairs lengths is not a capacitance calculation. The octave source's aggregate direct1 nF envelope remains distinct from the five switched1 kOhm/100 nF receiver dynamics. Every modeled crossing capacitance is still null; no loading/settling or stability acceptance is inferred.

Power/return qualification is kept separate from blanket signal300 mm/1 nF acceptance. This does not exempt power wiring from its own mechanical length or impedance requirements. Full source/common-distribution/branch/contact/via/load/return connectivity, <=0.5 mOhm combined branch+K return, <=1 mOhm rail transfer, <=20 mV hot drop, <=0.20 V complete path and <=0.5 A/GH contact remain OPEN. Return identity correctness cannot substitute for unknown source regulation, dynamic/fault current, parallel sharing or installed joint resistance.

## Validation and limits

Seventeen focused tests PASS: wrong instance, net, pin, UID, even a jointly changed template/actual UID, feedback-pin substitution for a driver, wrong shared driver, relaxed length/capacitance, missing wire decomposition, missing PWM branch, missing shared-instance receiver, omitted one-of-multiple receiver endpoints, duplicated endpoint, missing return endpoint and wrong return contact. The positive all-five live-source comparison also passes. Deterministic generation/reproduction and whitespace checks pass.

This audit materializes all-five electrical identities; it does not produce native all-five schematic/PCB files. Template labels in the existing assembly report are preserved and explicitly resolved by this new report. No canonical source or existing assembly model was modified. No KiCad/native/ERC/DRC, routing, installed fit, hardware or bench test was run. No architecture adoption or replication acceptance is claimed.

## Reviewed hashes

- `scripts/architecture278/implementation/stage3_crossing_audit.py`: `68cc3c0ffd4ae9ee5deb9f65c2f2651b982a40af5fdd285251d63ca155226a23`
- `scripts/architecture278/implementation/test_stage3_crossing_audit.py`: `c09ca879d7b4ae4b0312e58784c60f52cb3eb57961c643124d62c60a8c600112`
- `design/architecture-278/implementation/stage3-crossing-audit.json`: `9585d9be2c93e69ab4a580127e6157b0f135654ebaf6731d41795898abdeb6ed`
- `design/architecture-278/implementation/assembly-report.json`: `2d8f9cbb7316011c8885fe46c1e2a785a7afb07f8ec4efdb5630bde124c498b0`
