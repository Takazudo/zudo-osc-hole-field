# Stage30 J-PWR route study (separate from the DIN correction)

Centreline comparison only. Wire size, bundle size and bend radius are **assumptions** (route-input.json). Clear centrelines are not physical non-interference. Measured lengths, cut lengths, fit, M-09 and M-12 are NOT RUN.

Envelope: OD 1.0 mm, 4-wire bundle radius 1.2071 mm + margin 0.5 mm = required centreline clearance **1.7071 mm** to every keep-out.

## Ways into the middle carrier ring

- Slot between ring top z=46 and A01-middle front face z=48.4: **2.4 mm** (bundle needs 3.4142 mm).
- Left rail gap y=[274, 286]: the C-SIG middle release sweep leaves [0.9, 1.0] mm.
- Jack board edge to left rail: 2 mm.
- Open front below z=34: over locked foreign panel hardware (A02-A05 jacks/LEDs, E2-E5 switches) whose depth is unknown (Stage10: XY projection is not free space). Stage30 assumes that depth ends at the middle carrier front, z=34 (ASSUMPTION; see the foreign-depth sensitivity below).
- The top crossmember (y 138-142) and the right rail have the same 2.4 mm slot under A01-middle.
- J-PWR local housing exit z=43.9: a route that turns directly toward the ring below the A01-middle face has at most **2.7929 mm** of axial lead there, so its first 90° bend radius is at most that.

| Slot sensitivity: OD mm | margin mm | gap needed mm | fits 2.4 mm slot |
|---|---|---|---|
| 0.76 | 0.0 | 1.8348 | True |
| 0.76 | 0.5 | 2.8348 | False |
| 1.0 | 0.0 | 2.4142 | False |
| 1.0 | 0.5 | 3.4142 | False |

## Candidates

| ID | Geometry | Status | Keep-out hits | Unknown-depth hits (blocks) | Clearance to known keep-outs mm | Max bend R mm (assumed need) | Longest required cut mm (Stage10 90±3) |
|---|---|---|---|---|---|---|---|
| W1 Bypass the J-SIG middle release sweep at proxy height | existing | **BLOCKED_BY_KEEP_OUT** | rail:middle:0 | — | 0.0 | 2.1 (5.0, short) | 112.455 |
| W2 Run in the slot between the middle carrier rail top and the A01-middle front face | existing | **BLOCKED_BY_KEEP_OUT** | board:A01-middle:0, board:A01-middle:2, rail:middle:0 | — | 1.2 | 2.6483 (5.0, short) | 113.467 |
| W3 Wrap below the jack board edge and pass in front of the middle carrier | existing | **UNKNOWN_FOREIGN_DEPTH** | — | foreign-depth:D16101, foreign-depth:J1710, foreign-depth:SW1401, foreign-depth:SW1501 (A04, A05, E2, E3) | 2.0 | 2.1 (5.0, short) | 154.122 |
| W4 Pass a local relief in the middle carrier left rail (minimum change, proposal only) | PROPOSED CHANGE | **CENTRELINE_CLEAR_UNDER_ASSUMPTIONS** | — | — | 2.0743 | 2.0671 (5.0, short) | 111.479 |

Foreign-depth sensitivity: the unknown depth of the locked foreign hardware is capped at the middle carrier front by assumption. The cap (z) at which each candidate first meets unknown-depth hardware:

- W1: z = 34.293 mm
- W2: z = 34.293 mm
- W3: z = 30.293 mm
- W4: z = 34.293 mm

## Minimum change proposal (not adopted)

Relieve `rail:middle:0` (middle carrier left rail, z 34.0-46.0) to top z=43.5 mm over y=[158, 177] mm: 2.5 mm deep, leaving 9.5 mm of rail. The W4 centreline needs at least y=[163.391, 169.943] and top z <= 43.898. W4 then reads `CENTRELINE_CLEAR_UNDER_ASSUMPTIONS` with 2.0743 mm centreline clearance to known keep-outs; it meets unknown-depth foreign hardware if that depth reaches z = 34.293 mm. Status: PROPOSAL_NOT_ADOPTED; needs owner approval and a mechanical re-check of the middle carrier rail.

Still open after the relief: rail stiffness after relief (Stage10 planning model, 90 N DIN sensitivity); J-PWR cut length after M-09; local-end bend radius accepted by the harness maker; J-SIG crossing of the same rail.

Even then the J-PWR cut must be re-derived after M-09: the Stage10 cut is shorter than every routed candidate needs under the Stage10 release and slack rule. The local-end bend stays tight: the J-PWR local housing exit is 4.5 mm below the A01-middle front face.

## Stage28 straight proxies against the full keep-out set

Board slabs are left out (straight lines through boards are expected for proxies).

- H-J-SIG-1: rail:middle:0
- H-J-SIG-2: rail:middle:0
- H-J-SIG-3: rail:middle:0
- H-J-SIG-4: rail:middle:0
- H-J-SIG-5: rail:middle:0
- H-J-SIG-6: rail:middle:0
- H-J-SIG-7: rail:middle:0
- H-J-PWR-1: rail:middle:0, release:A01:J-SIG:middle
- H-J-PWR-2: rail:middle:0, release:A01:J-SIG:middle
- H-J-PWR-3: rail:middle:0, release:A01:J-SIG:middle
- H-J-PWR-4: rail:middle:0, release:A01:J-SIG:middle

Service is unchanged: disconnect K-PWR, then withdraw the core 40 mm; no candidate enters the core withdrawal volume.
