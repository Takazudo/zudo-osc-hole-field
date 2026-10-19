# Stage33 large-radius study (generated)

Design study only. Calculations on planning geometry and stated inputs; nothing is measured, and a clear envelope is not physical non-interference.

## Candidates

| Candidate | What it is | Class | Why |
|---|---|---|---|
| B32 | Stage32 recommendation, front-face headers, 5 mm bends | INFEASIBLE | infeasible for every identified wire (5 mm bends are below each maker rule; the bounded search found no smaller rule inside the JST window); for an unidentified wire it is UNKNOWN. K4 holds for the half-sine bow (0.199 mm) and fails for the uniform 1.282 mm bow (-0.382 mm) |
| F33 | Front-face headers, every bend at R 12.00 | UNKNOWN | slot path fails K4 (J-SIG -0.35 mm, J-PWR -0.06 mm); the +y descent meets foreign columns of unknown depth (largest clear radius 5.25 mm); 15 mm release envelope down to z 1.96 |
| R33 | Rear-face headers, one arch per cable at R 12.00 | CONDITIONAL (CONDITIONAL_PENDING_RETENTION) | meets 11 of 12 criteria; fails S3_lateral_retention; needs owner decisions and a wire |

## R33 criteria

| Criterion | Result |
|---|---|
| S1_static_clear | yes |
| S2_robust_K4 | yes |
| S3_lateral_retention | **no** |
| S4_sweeps_and_access_clear | yes |
| S5_core_clear | yes |
| S6_strength_planning_load | yes |
| S7_release_15mm_clear_and_outside_front_volume | yes |
| S8_no_foreign_requirement | yes |
| S9_bend_maker_rule | yes |
| S10_fan_in_every_state | yes |
| S11_constant_length_and_cover | yes |
| S12_reservations_clear_of_designed_parts | yes |

## Results by class

| Result | Class |
|---|---|
| R33 static and robust clearance, all bow cases (arch in its ideal plane) | CONDITIONAL |
| R33 15 mm release and core 40 mm (arch in its ideal plane) | CONDITIONAL |
| R33 bend radius 12 mm vs 10x OD (inner-surface convention) and the fan-in at every exit | FEASIBLE_WITHIN_STATED_ASSUMPTIONS |
| R33 at R 12 under the 15x/20x flex-rule sensitivity | INFEASIBLE |
| R33 geometry at the 15x radius (scan: clearance, K4 with the catch-all stack, core, cover with bow; longer cables) | CONDITIONAL |
| R33 geometry at the 20x radius (scan: clearance, K4 with the catch-all stack, core, cover with bow; longer cables) | INFEASIBLE |
| R33 rear-face header move | CONDITIONAL |
| R33 lateral retention (no part; position not measured) | UNKNOWN |
| Wire selection | UNKNOWN |
| AWG28 current qualification | UNKNOWN |
| J-SIG conductor current | UNKNOWN |
| Finger/tool operability at the latches | UNKNOWN |
| F33 slot path (front-face headers) | INFEASIBLE |
| F33 descent beyond the jack board +y edge | UNKNOWN |
| B32 5 mm bends with every identified wire | INFEASIBLE |
| B32 uniform 1.282 mm bow | INFEASIBLE |

## R33 geometry

- A01:J-PWR:middle: [283, 150] front → [290.0, 150.0] rear face (z 50), 0°, exit [290.0, 150.0, 57.3], sweep [283.525, 146.9, 296.475, 157.0] z [50, 72.3]; largest pad move 14.45 mm; BROADER_CHANGE_PROPOSAL (mounting face)
- A01:J-SIG:middle: [260, 150] front → [250.0, 152.0] rear face (z 50), 0°, exit [250.0, 152.0, 57.3], sweep [241.65, 148.9, 258.35, 159.0] z [50, 72.3]; largest pad move 21.29 mm; BROADER_CHANGE_PROPOSAL (mounting face)
- J-SIG: design length 133 mm (minimum installed 107.65 + 15 mm release extra 15.00 + 10 slack; not a cut length); fan-in 10.39 mm at each exit; installed arch top centreline z 92.36; straight from the exits 36.46 / 23.06 mm; nearest board:A01-jack 5.45, board:A01-middle:0 5.45
- J-PWR: design length 149 mm (minimum installed 123.52 + 15 mm release extra 15.00 + 10 slack; not a cut length); fan-in 6.91 mm at each exit; installed arch top centreline z 88.95; straight from the exits 33.05 / 19.65 mm; nearest core-extraction-40mm 2.77, tool:A01-jack:M4 3.03, tool:A01-core:M1 4.05

## Lateral retention (S3 fails)

No part holds the arches laterally. Allowance = smallest clearance over every state − 0.5 margin − catch-all stack.

| Cable | Allowance (mm) | Nearest | Straight zone on the local leg in every state | Straight zone on the middle leg |
|---|---|---|---|---|
| J-SIG | 3.36 | the other cable (plan bound, both arches in their planes) (every state) | z 69.29–80.36 | none |
| J-PWR | 1.89 | core-extraction-40mm (installed 0) | z 65.81–76.95 | none |

## Service states (constant design length)

| Cable | State | Travel (mm) | Arch top centreline z | Envelope top / bottom z | Straight from exits (mm) | Min clearance (mm) | Below carrier |
|---|---|---|---|---|---|---|---|
| J-SIG | installed | 0.0 | 92.36 | 94.11 / 42.15 | 36.46 / 23.06 | 5.45 | no |
| J-SIG | middle | 7.5 | 96.11 | 97.86 / 42.15 | 40.21 / 19.31 | 5.45 | no |
| J-SIG | local | 7.5 | 96.11 | 97.86 / 49.65 | 32.71 / 26.81 | 5.45 | no |
| J-SIG | both | 7.5 | 99.86 | 101.61 / 49.65 | 36.46 / 23.06 | – | no |
| J-SIG | middle | 15 | 99.86 | 101.61 / 42.15 | 43.96 / 15.56 | 5.45 | no |
| J-SIG | local | 15 | 99.86 | 101.61 / 55.55 | 28.96 / 30.56 | 5.45 | no |
| J-SIG | both | 15 | 107.36 | 109.11 / 57.15 | 36.46 / 23.06 | – | no |
| J-PWR | installed | 0.0 | 88.95 | 90.40 / 42.44 | 33.05 / 19.65 | 2.77 | no |
| J-PWR | middle | 7.5 | 92.70 | 94.15 / 42.44 | 36.80 / 15.90 | 2.77 | no |
| J-PWR | local | 7.5 | 92.70 | 94.15 / 49.94 | 29.30 / 23.40 | 2.77 | no |
| J-PWR | both | 7.5 | 96.45 | 97.90 / 49.94 | 33.05 / 19.65 | 2.77 | no |
| J-PWR | middle | 15 | 96.45 | 97.90 / 42.44 | 40.55 / 12.15 | 2.77 | no |
| J-PWR | local | 15 | 96.45 | 97.90 / 55.84 | 25.55 / 27.15 | 2.77 | no |
| J-PWR | both | 15 | 103.95 | 105.40 / 57.44 | 33.05 / 19.65 | 2.77 | no |

Cable to cable: plan bound 4.23 mm in every state (robust 3.36); sampled minimum over the 16 state pairs at 15 mm 4.03 mm.
Core 40 mm (installed arches): 2.77 mm, robust 1.89 mm after the 0.38 mm stack; core carrier to middle/jack carrier registration UNCONFIRMED (panel_to_carrier_registration_mm null in Stage32); not in the stack.

## K4 after the tolerance stack (R33)

| Bow case | State | Tightest | Robust spare (mm) | K4 |
|---|---|---|---|---|
| base (half sine 142-292) | installed | J-PWR core-extraction-40mm | 1.89 | yes |
| base (half sine 142-292) | middle | J-PWR core-extraction-40mm | 1.89 | yes |
| base (half sine 142-292) | local | J-PWR core-extraction-40mm | 1.89 | yes |
| base (half sine 142-292) | both | J-PWR core-extraction-40mm | 1.89 | yes |
| edge-M1-M3 | installed | J-PWR core-extraction-40mm | 1.89 | yes |
| edge-M1-M3 | middle | J-PWR core-extraction-40mm | 1.89 | yes |
| edge-M1-M3 | local | J-PWR core-extraction-40mm | 1.89 | yes |
| edge-M1-M3 | both | J-PWR core-extraction-40mm | 1.89 | yes |
| length-142-292 | installed | J-PWR core-extraction-40mm | 1.89 | yes |
| length-142-292 | middle | J-PWR core-extraction-40mm | 1.89 | yes |
| length-142-292 | local | J-PWR core-extraction-40mm | 1.89 | yes |
| length-142-292 | both | J-PWR core-extraction-40mm | 1.89 | yes |
| uniform-diagonal | installed | J-PWR core-extraction-40mm | 1.89 | yes |
| uniform-diagonal | middle | J-PWR core-extraction-40mm | 1.89 | yes |
| uniform-diagonal | local | J-PWR core-extraction-40mm | 1.89 | yes |
| uniform-diagonal | both | J-PWR core-extraction-40mm | 1.89 | yes |

The bow also shifts the rear-face exits in z; the rear-cover check adds the uniform bow: installed top 94.11 + 1.28 + 0.5 ≤ 105.0.

## Wire qualification

Route R 12.00 mm (bundle centreline). Required R = k × OD + bundle envelope radius (inner surface); the innermost-conductor reading is listed for comparison. Selection: NULL: no identified wire passes every check for either cable (see per_cable failed).

| Wire | AWG | OD (mm) | Rule | Required R J-SIG / J-PWR (mm) | Conductor-centreline reading (mm) | J-SIG fails | J-PWR fails |
|---|---|---|---|---|---|---|---|
| Alpha Wire 1852 | 28 | 0.8382–0.9398 | 10× OD | 11.06 / 10.78 | 10.59 / 10.31 | current | current |
| Alpha Wire 1853 | 26 | 0.9398–1.0414 | 10× OD | 12.23 / 11.92 | 11.71 / 11.40 | od_window, bend_rule_at_route_R, current | od_window |
| Alpha Wire 2843/7 | 26 | 0.7366–0.8382 | 10× OD | 9.89 / 9.64 | 9.47 / 9.22 | od_window, tin_plated, current | od_window, tin_plated |
| Alpha Wire 422607 | 26 | 0.9398–1.0414 | 10× OD | 12.23 / 11.92 | 11.71 / 11.40 | od_window, temperature, bend_rule_at_route_R, current | od_window, temperature |
| Alpha Wire 782607 | 26 | 2.0066–2.2098 | 5× OD | 14.61 / 13.97 | 13.51 / 12.86 | od_window, bend_rule_at_route_R, current | od_window, bend_rule_at_route_R |

Any wire in the JST window under 10× OD needs 11.75 / 11.46 mm. Flex sensitivity: 15× needs 16.75 / 16.46 mm (not met at R 12.00); 20× needs 21.75 / 21.46 mm (not met at R 12.00).
Fan-in at each housing exit (outermost pin to the bundle ring, S-bend at 10× OD + OD/2): J-SIG 10.39 mm; J-PWR 6.91 mm.
J-PWR conditional rail maxima +12V 12.87 mA, -12V 11.67 mA, +5V 0.10 mA; AGND return bound 24.64 mA; Stage10 contact limit 0.5 A. J-SIG current UNCONFIRMED.

## Radius scan

Checks: clearance with the catch-all stack (K4), slack, core envelope with stack, rear cover with the uniform bow (same rule as S11); access, other bow cases and strength not re-evaluated.

| R (mm) | Fits | Design lengths J-SIG / J-PWR | Installed top z | Service top z | Robust spare (mm) | Reason |
|---|---|---|---|---|---|---|
| 12.0 | yes | 133 / 149 | 94.11 | 109.11 | 1.89 |  |
| 17.0 | yes | 139 / 155 | 99.26 | 114.26 | 1.89 |  |
| 22.0 | **no** | 145 / 160 | 104.40 | 119.40 | 1.89 | installed arch + uniform bow + margin above the rear cover |

## Strength (conditional)

- rail:middle:0 has no notch in R33: allowable tip load 174.55 N vertical / 87.27 N lateral; it meets 20 N and 50 N (root joint not evaluated).
- R33 adds no retention part, so no guide strength exists to calculate.
- B32 (Stage32, preserved): notched rail allowable 11.36 N; 11 notch cases fail at 20 N.

## Access (R33, rear cover off)

- A01:J-SIG:middle (middle): faces -y rigid – / cable –; +y rigid 13.00 / cable – mm; +z corridor clear; straight bundle above the housing 23.06 mm; finger operation NOT_DETERMINED; a CAD gap is not finger operability (M33-03).
- A01:J-SIG:local (local): faces -y rigid 8.49 / cable –; +y rigid – / cable – mm; +z corridor clear; straight bundle above the housing 36.46 mm; finger operation NOT_DETERMINED; a CAD gap is not finger operability (M33-03).
- A01:J-PWR:middle (middle): faces -y rigid – / cable –; +y rigid 15.00 / cable – mm; +z corridor clear; straight bundle above the housing 19.65 mm; finger operation NOT_DETERMINED; a CAD gap is not finger operability (M33-03).
- A01:J-PWR:local (local): faces -y rigid 8.26 / cable –; +y rigid – / cable – mm; +z corridor clear; straight bundle above the housing 33.05 mm; finger operation NOT_DETERMINED; a CAD gap is not finger operability (M33-03).

## Reservations proposed (not adopted)

- **RV-ARCH-J-SIG**: vertical slab through [210.0, 173.0] along [0.885398, -0.464834], half thickness 2.35 mm, length 45.18 mm; parts local leg s [-2.35, 2.35] z [43.9, 109.711945]; middle leg s [42.827428, 47.527428] z [57.3, 109.711945]; top band s [-2.35, 47.527428] z [78.011945, 109.711945]. Designed parts inside: none.
- **RV-ACCESS-J-SIG-local**: XY [201.15, 169.4, 218.85, 180.5], z [43.9, 105.0]. +z access above the housing with the rear cover off. Designed parts inside: none.
- **RV-ACCESS-J-SIG-middle**: XY [241.15, 148.4, 258.85, 159.5], z [57.3, 105.0]. +z access above the housing with the rear cover off. Designed parts inside: none.
- **RV-ARCH-J-PWR**: vertical slab through [226.0, 173.0] along [0.941075, -0.338199], half thickness 2.06 mm, length 68.01 mm; parts local leg s [-2.057107, 2.057107] z [43.9, 106.00409]; middle leg s [65.950246, 70.06446] z [57.3, 106.00409]; top band s [-2.057107, 70.06446] z [74.889876, 106.00409]. Designed parts inside: none.
- **RV-ACCESS-J-PWR-local**: XY [219.025, 169.4, 232.975, 180.5], z [43.9, 105.0]. +z access above the housing with the rear cover off. Designed parts inside: none.
- **RV-ACCESS-J-PWR-middle**: XY [283.025, 146.4, 296.975, 157.5], z [57.3, 105.0]. +z access above the housing with the rear cover off. Designed parts inside: none.

**R33 assembly**

1. Fit A01-middle on the middle carrier as in Stage10 (front carrier, spacers, M1-M4).
2. Fit the rear carrier and the core as in Stage10.
3. From the rear (rear cover off): mate J-SIG and J-PWR at the A01-jack local headers (+z), then at the A01-middle rear-face headers (-z), each housing pushed along its axis.
4. Dress each cable into one vertical-plane arch with the fan-in straight above each housing; no part holds the arch laterally (open condition, M33-04).
5. Refit the rear cover; the installed arch envelope tops (z 94.1 / 90.4) stay below its inner face (z 105) with the uniform bow added.

**Core service (unchanged order)**

1. Power off; remove the rear cover.
2. Disconnect K-PWR, release the four core screws, hold both handles and withdraw the core 40 mm along +z. J-SIG/J-PWR are not touched; the J-PWR arch is 2.8 mm from the core volume in its ideal plane.
3. Do not move the core while a J-SIG/J-PWR housing is withdrawn: the raised arch reaches z 109.1 with both ends of J-SIG withdrawn and is not modelled against the core for that case.

**Middle connector service**

1. Power off; remove the rear cover. The core may stay installed.
2. Press the GH latch with a finger or a flat tool from the rear (latch face UNCONFIRMED: both long faces are open toward +z).
3. Hold the vertical bundle above the housing and pull within 15 degrees of +z (S-JST-HANDLING p.961). J-SIG has 23.1 mm straight installed and 15.6 mm at 15 mm withdrawal; above its 10.4 mm fan-in that leaves 12.7 / 5.2 mm to grip. The arch rises; the cable keeps its design length.
4. Re-mate by pushing the housing along -z until the latch engages.

**Harness replacement**

1. Power off; remove the rear cover.
2. Unmate both middle ends, then both local ends, all from the rear. No board, carrier or the core is removed.

**Front jack board removal**

1. Unmate J-SIG and J-PWR at the middle ends from the rear, lift each free end back over the A01-middle edge to x < 232, then remove the front panel assembly as in Stage10 with the cables attached to A01-jack.

## Measurements still NOT RUN

- **M33-01** Selected wire MPN: OD with tolerance, strand count, plating, maker bend rule (installation and repeated flexing) and a current basis at its gauge with the GH contact.
- **M33-02** GH unmating on a bench coupon: stroke to free, force, latch side, conductor fan-in length at the housing; mating force on a rear-face header and the A01-middle deflection under it.
- **M33-03** Latch press and pull at all four housings from the rear, with the core and both arches in place (finger or tool).
- **M33-04** Mock-up of both arches at the design lengths: installed shape, lateral position in each enclosure orientation against the allowance, rise during each release case.
- **M33-05** Enclosure rear inner face and rear-cover features over the RV-ARCH volumes.
- **M33-06** rail:middle:0 root joint and stiffness; any retention part added later.
- **M33-07** Cut lengths for the design lengths (M-09) and repeated-release abrasion at the housing exits (M-12).
- **M33-08** A01-middle bow (M32-04), rear-face header position after assembly and core-to-middle carrier registration.
