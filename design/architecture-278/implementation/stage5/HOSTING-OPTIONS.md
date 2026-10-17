# Non-OSC and POWER hosting options

This is a source ownership comparison, not a new board partition implementation or an architecture decision. Each option accounts for all **5,904 packages, 8,226 units and 1,067 bypass associations**, without changing the 33 functions or 438 fixed panel centres. Exact source Ref/unit/pin/NC records remain bound through zero-based source-ledger indices and its SHA-256. Whole packages and bypass targets never split between hosts.

The population requiring an explicit replacement K host is **2,572 non-OSC packages / 3,811 units**, plus **13 POWER packages**. The 30 shared-reference packages are separately accounted on the proposed middle host; the five rear OSC populations contain 770 packages. Carrier groups are concrete source assignments and per-function Ref lists, not assertions that new carrier shapes or occupied volumes fit.

| Option | Concrete retained/proposed ownership | Consequences |
|---|---|---|
| Historical whole instrument | All original boards and 5,904 source packages retain original ownership | Unchanged physical K contains 3,385 packages, including 770 OSC and 30 shared packages. New rear cards cannot silently replace those active functions while the old packages remain connected. This is the incumbent/control comparison, not an adopted coexistence design. |
| Proposed front redesign with replacement hosts | Five OSC rear groups; 30 shared packages on middle; all 2,572 non-OSC K packages assigned to a source-preserving carrier group; 13 POWER packages on a separate service group; OSC front groups and other mixed-front replacement groups explicit | Requires new carrier placement, local routing, interfaces, support/occupied/service geometry, and mixed-front replacement boards. Per-function sectors are inventory groups, not 22 newly selected PCBs. No geometry, connector count, cost saving or source/inlet placement is invented. |
| Core-only comparison with full front reuse | Same explicit non-OSC/POWER hosting obligation; retain all 2,519 front packages on original JL/JR/P/EL/selectors | Preserves full original front source/copper as a comparison. Existing front endpoints, depths and interfaces must be used; the current redesigned-front placement and GH path totals cannot be transferred. New rear interface adapters and complete dual length/capacitance/return analysis remain necessary. |

## Mixed front ownership is material

| Source board | OSC packages | Other-function packages | Implication |
|---|---:|---:|---|
| JL | 285 | 775 | Front redesign must explicitly preserve/rehost the 775 non-OSC packages. It cannot claim the old physical JL board is unchanged while replacing only its OSC portion. |
| P | 35 | 250 | The same rule applies to 250 non-OSC control packages. |
| JR | 0 | 1,031 | Historical ownership retained in this comparison; installed coexistence still needs checking. |
| EL | 0 | 138 | Complete stage optical circuitry remains accounted. |
| O1–O5 adapters | 5 total | 0 | One whole selector package per adapter; interface/fit remains conditional. |

The proposed front-redesign option assigns all original JL and P packages to explicit replacement source groups: 285+775 and 35+250 respectively. The core-only comparison retains both complete mixed boards, not a copper subset. Source reuse is not old native-receipt reuse: changed joins, connectors, power distribution or mechanics still need qualification.

## Physically retaining historical K

The retained source K board occupies depths 100–101.6 mm. With its conditional 5 mm rear component allowance, it reaches **106.6 mm**, exceeding the candidate's 105 mm cover by **1.6 mm** before new tolerance/insulation evidence. The historical 120 mm enclosure proposal gives 13.4 mm nominal rear clearance under those assumptions; it is not an installed-solid certificate.

More cover depth does not clear the extraction obstruction. A declared candidate rear envelope beginning at 69.2 mm, with 1.6 mm PCB and 5 mm rear component allowance, sweeps to 115.8 mm during 40 mm straight withdrawal. All five card projections intersect the retained K polygon, and their withdrawal intervals cross its 100–101.6 mm board plane. This package-backed envelope is distinct from the longer handle withdrawal envelope. These are conditional envelope intersections, not measured insertion tests. Retaining K therefore requires a separately designed service arrangement, not just a deeper cover or an assumption that K disappears.

Leaving only 2,572+13 packages on historical K would require a new electrical/physical depopulation or replacement design: unmodified K also carries 770 OSC and 30 shared packages. No cuts, removals, depopulation, duplicate active oscillator circuits or canonical edits are performed or implied here. An external isolated testpiece can retain the incumbent instrument as comparison, but does not prove whole-instrument coexistence.

## Recommended next bounded source work

For continuing the source comparison of the proposed front-redesign candidate, use the explicit non-OSC carrier, POWER service and mixed-front replacement groups as inputs for actual placement and occupied/service reservations. Preserve source-local timing/feedback/bypass circuits while assigning carrier outlines, board faces, supports and interfaces; then calculate complete power/return and signal metrics. Until those data exist, new carrier geometry and service volume remain null, never free space.

Keep core-only full-front reuse as the control alternative if preserving front copper becomes the priority. It does not eliminate the non-OSC/POWER host or service problem. Choosing either architecture, changing source functions, fabrication or native campaigns is outside this source comparison.

`stage5_hosting_options.py --check` reproduces the compact report. Eight tests cover complete unit/pin-index and bypass conservation, missing POWER, split bypass, mixed-front counts, partial reuse, silent old-board retention, historical depth/withdrawal consequences and unknown geometry. Native/ERC/DRC/physical checks: **NOT RUN**. No option is implemented, adopted or declared feasible.

Final source/report SHA-256:

- `scripts/architecture278/implementation/stage5_hosting_options.py`: `a8b31885259cb32c17410fa94b48b7efcb7b66f50a027fa8b16179ae46d1afce`
- `scripts/architecture278/implementation/test_stage5_hosting_options.py`: `db8c879f2bc78b2fdd789acfb3c0c5a06b3ddca05e4519909eefc95b1f561004`
- `design/architecture-278/implementation/stage5/hosting-options-report.json`: `61661b3358780d171b74d347316eac09de3f17b4e5b5ed28a2fea3786ceb9008`
