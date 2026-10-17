# Stage33 large-radius study (generated)

Design study only. Calculations on planning geometry and stated inputs; nothing is measured, and a clear envelope is not physical non-interference.

## Candidates

| Candidate | What it is | Class | Why |
|---|---|---|---|
| B32 | Stage32 recommendation, front-face headers, 5 mm bends | INFEASIBLE | 5 mm bends are below every identified maker rule, and the bounded Stage33 search found no wire with a smaller rule inside the JST OD window; the uniform-bow case also fails K4 |
| F33 | Front-face headers, every bend at R 12.0 | INFEASIBLE | J-SIG slot spare -0.35 mm, J-PWR -0.06 mm (K4 0.15); 15 mm release envelope reaches z 10.35 |
| R33 | Rear-face headers, one arch per cable at R 12.00, keeper K1 | CONDITIONAL | meets S1-S11; needs owner decisions and a wire |

## R33 criteria

| Criterion | Result |
|---|---|
| S1_static_clear | yes |
| S2_robust_K4 | yes |
| S3_retention_modelled | yes |
| S4_sweeps_and_access_clear | yes |
| S5_core_clear | yes |
| S6_strength_planning_load | yes |
| S7_release_15mm_clear_and_outside_front_volume | yes |
| S8_no_foreign_requirement | yes |
| S9_bend_maker_rule | yes |
| S10_straight_lead_every_state | yes |
| S11_constant_length_and_cover | yes |
| S12_keeper_above_installed_arch | yes |

## Results by class

| Result | Class |
|---|---|
| R33 static and robust clearance (all bow cases) | FEASIBLE_WITHIN_STATED_ASSUMPTIONS |
| R33 15 mm release and core 40 mm | FEASIBLE_WITHIN_STATED_ASSUMPTIONS |
| R33 bend radius 12 mm vs 10x OD at the JST maximum OD | FEASIBLE_WITHIN_STATED_ASSUMPTIONS |
| R33 at R 12 under the 15x/20x flex-rule sensitivity | INFEASIBLE |
| R33 geometry at the 15x/20x radii (longer cables, taller keeper) | CONDITIONAL |
| R33 rear-face header move | CONDITIONAL |
| R33 keeper K1 and its strength | CONDITIONAL |
| R33 arch lateral position without measurement | UNKNOWN |
| Wire selection | UNKNOWN |
| AWG28 current qualification | UNKNOWN |
| Finger/tool operability at the latches | UNKNOWN |
| F33 front-face large radius | INFEASIBLE |
| B32 5 mm bends | INFEASIBLE |
| B32 uniform 1.282 mm bow | INFEASIBLE |

## R33 geometry

- A01:J-PWR:middle: [283, 150] front → [290.0, 150.0] rear face (z 50), 0°, exit [290.0, 150.0, 57.3], sweep [283.525, 146.9, 296.475, 157.0] z [50, 72.3]; BROADER_CHANGE_PROPOSAL (mounting face)
- A01:J-SIG:middle: [260, 150] front → [250.0, 152.0] rear face (z 50), 0°, exit [250.0, 152.0, 57.3], sweep [241.65, 148.9, 258.35, 159.0] z [50, 72.3]; BROADER_CHANGE_PROPOSAL (mounting face)
- Keeper K1 on crossmember:rear:0: XY [241.0, 170.5, 258.0, 172.5], z [62.0, 96.0] (2.0 mm thick); a fence between the J-PWR arch and the core withdrawal volume (y >= 174) where the arch comes within 10 mm of it; it does not touch either cable
- J-SIG: design length 116 mm (minimum installed 90.88 + 15 mm release extra 15.00 + 10 slack; not a cut length); installed arch top centreline z 83.86; straight from the exits [27.961945, 14.561945] mm; nearest board:A01-jack 5.45, board:A01-middle:0 5.45
- J-PWR: design length 139 mm (minimum installed 113.71 + 15 mm release extra 15.00 + 10 slack; not a cut length); installed arch top centreline z 83.95; straight from the exits [28.046983, 14.646983] mm; nearest keeper:K1 1.16, core-extraction-40mm 2.77, tool:A01-jack:M4 3.03

## Service states (constant design length)

| Cable | State | Travel (mm) | Arch top centreline z | Envelope top / bottom z | Straight leads (mm) | Min clearance (mm) | Below carrier |
|---|---|---|---|---|---|---|---|
| J-SIG | installed | 0.0 | 83.86 | 85.61 / 42.15 | [27.961945, 14.561945] | 5.45 | no |
| J-SIG | middle | 7.5 | 87.61 | 89.36 / 42.15 | [31.711945, 10.811945] | 5.45 | no |
| J-SIG | local | 7.5 | 87.61 | 89.36 / 49.65 | [24.211945, 18.311945] | 5.45 | no |
| J-SIG | both | 7.5 | 91.36 | 93.11 / 49.65 | [27.961945, 14.561945] | – | no |
| J-SIG | middle | 15 | 91.36 | 93.11 / 42.15 | [35.461945, 7.061945] | 5.45 | no |
| J-SIG | local | 15 | 91.36 | 93.11 / 55.55 | [20.461945, 22.061945] | 5.45 | no |
| J-SIG | both | 15 | 98.86 | 100.61 / 57.15 | [27.961945, 14.561945] | – | no |
| J-PWR | installed | 0.0 | 83.95 | 85.40 / 42.44 | [28.046983, 14.646983] | 1.16 | no |
| J-PWR | middle | 7.5 | 87.70 | 89.15 / 42.44 | [31.796983, 10.896983] | 1.16 | no |
| J-PWR | local | 7.5 | 87.70 | 89.15 / 49.94 | [24.296983, 18.396983] | 1.16 | no |
| J-PWR | both | 7.5 | 91.45 | 92.90 / 49.94 | [28.046983, 14.646983] | 1.16 | no |
| J-PWR | middle | 15 | 91.45 | 92.90 / 42.44 | [35.546983, 7.146983] | 1.16 | no |
| J-PWR | local | 15 | 91.45 | 92.90 / 55.84 | [20.546983, 22.146983] | 1.16 | no |
| J-PWR | both | 15 | 98.95 | 100.40 / 57.44 | [28.046983, 14.646983] | 2.45 | no |

Cable to cable: plan bound 4.23 mm in every state; sampled minimum over the 16 state pairs at 15 mm 4.03 mm.

## K4 after the tolerance stack (R33)

| Bow case | State | Tightest | Robust spare (mm) | K4 |
|---|---|---|---|---|
| base (half sine 142-292) | installed | J-PWR keeper:K1 | 0.56 | yes |
| base (half sine 142-292) | middle | J-PWR keeper:K1 | 0.56 | yes |
| base (half sine 142-292) | local | J-PWR keeper:K1 | 0.56 | yes |
| base (half sine 142-292) | both | J-PWR keeper:K1 | 1.85 | yes |
| edge-M1-M3 | installed | J-PWR keeper:K1 | 0.56 | yes |
| edge-M1-M3 | middle | J-PWR keeper:K1 | 0.56 | yes |
| edge-M1-M3 | local | J-PWR keeper:K1 | 0.56 | yes |
| edge-M1-M3 | both | J-PWR keeper:K1 | 1.85 | yes |
| length-142-292 | installed | J-PWR keeper:K1 | 0.56 | yes |
| length-142-292 | middle | J-PWR keeper:K1 | 0.56 | yes |
| length-142-292 | local | J-PWR keeper:K1 | 0.56 | yes |
| length-142-292 | both | J-PWR keeper:K1 | 1.85 | yes |
| uniform-diagonal | installed | J-PWR keeper:K1 | 0.56 | yes |
| uniform-diagonal | middle | J-PWR keeper:K1 | 0.56 | yes |
| uniform-diagonal | local | J-PWR keeper:K1 | 0.56 | yes |
| uniform-diagonal | both | J-PWR keeper:K1 | 1.85 | yes |

## Wire qualification

Route R 12.00 mm (bundle centreline). Innermost conductor radius = R − (bundle envelope radius − OD/2). Selection: NULL: no identified wire passes every check (see failed).

| Wire | AWG | OD (mm) | Rule | Required R J-SIG / J-PWR (mm) | Current basis | Failed checks |
|---|---|---|---|---|---|---|
| Alpha Wire 1852 | 28 | 0.8382–0.9398 | 10× OD | 10.59 / 10.31 | UNCONFIRMED | current |
| Alpha Wire 1853 | 26 | 0.9398–1.0414 | 10× OD | 11.71 / 11.40 | JST 1.0 A (AWG26) | od_window |
| Alpha Wire 2843/7 | 26 | 0.7366–0.8382 | 10× OD | 9.47 / 9.22 | JST 1.0 A (AWG26) | od_window, tin_plated |
| Alpha Wire 422607 | 26 | 0.9398–1.0414 | 10× OD | 11.71 / 11.40 | JST 1.0 A (AWG26) | od_window, temperature |
| Alpha Wire 782607 | 26 | 2.0066–2.2098 | 5× OD | 13.51 / 12.86 | JST 1.0 A (AWG26) | od_window, bend_rule_at_route_R |

Any wire in the JST window under 10× OD needs 11.25 / 10.96 mm. Flex sensitivity: 15× needs 16.25 / 15.96 mm (not met at R 12.00); 20× needs 21.25 / 20.96 mm (not met at R 12.00).
J-PWR conditional rail maxima +12V 12.87 mA, -12V 11.67 mA, +5V 0.10 mA; AGND return bound 24.64 mA; Stage10 contact limit 0.5 A. J-SIG current UNCONFIRMED.

## Strength (conditional)

- rail:middle:0 has no notch in R33: allowable tip load 174.55 N vertical / 87.27 N lateral (root joint not evaluated).
- Keeper K1: allowable top load 35.56 N at Kt 1.5, 26.67 N at Kt 2.0, 17.78 N at Kt 3.0; deflection 0.083 mm at 5 N. At 20 N it fails for Kt 3.0.
- B32 (Stage32, preserved): notched rail allowable 11.36 N; 11 notch cases fail at 20 N.

## Access (R33, rear cover off)

- A01:J-SIG:middle (middle): faces -y rigid – / cable –; +y rigid 13.00 / cable – mm; +z corridor clear; own straight bundle above 14.56 mm; finger operation NOT_DETERMINED; a CAD gap is not finger operability (M33-03).
- A01:J-SIG:local (local): faces -y rigid 8.49 / cable –; +y rigid – / cable – mm; +z corridor clear; own straight bundle above 27.96 mm; finger operation NOT_DETERMINED; a CAD gap is not finger operability (M33-03).
- A01:J-PWR:middle (middle): faces -y rigid – / cable –; +y rigid 15.00 / cable – mm; +z corridor clear; own straight bundle above 14.65 mm; finger operation NOT_DETERMINED; a CAD gap is not finger operability (M33-03).
- A01:J-PWR:local (local): faces -y rigid 8.26 / cable –; +y rigid – / cable – mm; +z corridor clear; own straight bundle above 28.05 mm; finger operation NOT_DETERMINED; a CAD gap is not finger operability (M33-03).
- Core 40 mm: arches 2.77 mm and K1 1.50 mm from the core envelope.

## Reservations proposed (not adopted)

- **RV-ARCH-J-SIG**: XY [207.65, 149.65, 252.35, 175.35], z [41.55, 101.211945]. the arch occupies this volume above the A01 boards; no other part is designed there.
- **RV-ACCESS-J-SIG-local**: XY [201.15, 169.4, 218.85, 180.5], z [36.6, 105.0]. +z access with the rear cover off.
- **RV-ACCESS-J-SIG-middle**: XY [241.15, 148.4, 258.85, 159.5], z [50, 105.0]. +z access with the rear cover off.
- **RV-ARCH-J-PWR**: XY [223.942893, 147.942893, 292.057107, 175.057107], z [41.842893, 101.00409]. the arch occupies this volume above the A01 boards; no other part is designed there.
- **RV-ACCESS-J-PWR-local**: XY [219.025, 169.4, 232.975, 180.5], z [36.6, 105.0]. +z access with the rear cover off.
- **RV-ACCESS-J-PWR-middle**: XY [283.025, 146.4, 296.975, 157.5], z [50, 105.0]. +z access with the rear cover off.

**R33 assembly**

1. Fit A01-middle on the middle carrier as in Stage10 (front carrier, spacers, M1-M4).
2. Fit the rear carrier (crossmember:rear:0 with keeper K1) and the core as in Stage10.
3. From the rear (rear cover off): mate J-SIG and J-PWR at the A01-jack local headers (+z), then at the A01-middle rear-face headers (-z), each housing pushed along its axis.
4. Dress each cable into one vertical-plane arch on the -y side of K1; check by eye that neither arch rests on K1, a tool column or the core handle.
5. Refit the rear cover; the installed arch envelope tops (z 85.6 / 85.4) stay below its inner face (z 105).

**Core service (unchanged order)**

1. Power off; remove the rear cover.
2. Disconnect K-PWR, release the four core screws, hold both handles and withdraw the core 40 mm along +z. J-SIG/J-PWR and K1 are not touched; the installed arches stay on the -y side of K1 and below its top (z 96).
3. Do not move the core while a J-SIG/J-PWR housing is withdrawn: the raised arch can reach above K1 (up to z 100.6 with both ends withdrawn).

**Middle connector service**

1. Power off; remove the rear cover. The core may stay installed.
2. Press the GH latch with a finger or a flat tool from the rear (latch face UNCONFIRMED: both long faces are open toward +z).
3. Hold the vertical bundle above the housing (about 14.6 mm straight installed, 7.1 mm at 15 mm withdrawal) and pull within 15 degrees of +z (S-JST-HANDLING p.961). The arch rises; the cable keeps its design length.
4. Re-mate by pushing the housing along -z until the latch engages.

**Harness replacement**

1. Power off; remove the rear cover.
2. Unmate both middle ends, then both local ends, all from the rear. No board, carrier or the core is removed.

**Front jack board removal**

1. Unmate J-SIG and J-PWR at the middle ends from the rear, lift each free end back over the A01-middle edge to x < 232, then remove the front panel assembly as in Stage10 with the cables attached to A01-jack.

## Measurements still NOT RUN

- **M33-01** Selected wire MPN: OD with tolerance, strand count, plating, maker bend rule (installation and repeated flexing) and a current basis at its gauge with the GH contact.
- **M33-02** GH unmating on a bench coupon: stroke to free, force, latch side; mating force on a rear-face header and the A01-middle deflection under it.
- **M33-03** Latch press and pull at all four housings from the rear, with the core, K1 and the arches in place (finger or tool).
- **M33-04** Mock-up of both arches at the design lengths: installed shape, lateral sag in each enclosure orientation, rise during each release case.
- **M33-05** Enclosure rear inner face and rear-cover features over the RV-ARCH volumes.
- **M33-06** Keeper K1 and crossmember:rear:0 coupon: root fillet, stiffness and strength; rail:middle:0 root joint.
- **M33-07** Cut lengths for the design lengths (M-09) and repeated-release abrasion at the housing exits (M-12).
- **M33-08** A01-middle bow (M32-04) and rear-face header position after assembly.
