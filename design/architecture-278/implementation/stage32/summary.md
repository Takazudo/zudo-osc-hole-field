# Stage32 service envelope (generated)

Design study only. Calculations on planning geometry and stated inputs; nothing is measured, and a clear envelope is not physical non-interference.

## Criteria per candidate

| Candidate | S1 static | S2 robust K4 | S3 retention | S4 sweeps | S5 core | S6 strength | S7 release known | S8 foreign allowance | Status |
|---|---|---|---|---|---|---|---|---|---|
| B31 | yes | **no** | **no** | yes | yes | yes | yes | yes | NOT_ROBUST_UNDER_STAGE32_CHECKS |
| B32 | yes | yes | yes | yes | yes | yes | yes | yes | CONDITIONAL_WORKING_DESIGN |

## Tightest clearances after the tolerance stack

| Candidate | Cable | Obstacle | Sampled (mm) | Margin | Tolerance WC / RSS (mm) | Robust spare (mm) | K4 0.15 |
|---|---|---|---|---|---|---|---|
| B31 | J-PWR | board:A01-middle:1 | 0.79 | 0.50 | 0.98 / 0.79 | -0.69 | **no** |
| B31 | J-PWR | board:A01-middle:2 | 0.79 | 0.50 | 0.94 / 0.76 | -0.65 | **no** |
| B31 | J-SIG | board:A01-middle:2 | 0.80 | 0.50 | 0.72 / 0.54 | -0.42 | **no** |
| B31 | J-SIG | board:A01-middle:0 | 0.80 | 0.50 | 0.62 / 0.45 | -0.32 | **no** |
| B31 | J-PWR | tool:A01-jack:M4 | 0.69 | 0.50 | 0.28 / 0.16 | -0.08 | **no** |
| B32 | J-PWR | board:A01-middle:1 | 1.94 | 0.50 | 1.14 / 0.81 | 0.30 | yes |
| B32 | J-SIG | board:A01-middle:0 | 1.75 | 0.50 | 0.92 / 0.60 | 0.33 | yes |
| B32 | J-SIG | board:A01-middle:2 | 1.75 | 0.50 | 0.92 / 0.60 | 0.33 | yes |
| B32 | J-PWR | board:A01-middle:2 | 1.97 | 0.50 | 1.14 / 0.81 | 0.33 | yes |
| B32 | J-PWR | rail:middle:0:N2:floor | 0.99 | 0.50 | 0.10 / 0.10 | 0.39 | yes |

## B32 geometry

- A01:J-PWR:middle: [283, 150] → [288.0, 174.0], 90°, sweep [281.0, 167.525, 291.1, 180.475] z [26.1, 48.4]
- A01:J-SIG:middle: [260, 150] → [268.0, 171.5], 90°, sweep [261.0, 163.15, 271.1, 179.85] z [26.1, 48.4]
- R1 (J-SIG): notch y 168.8–174.2, floor z 41.7 (4.3 mm deep); bundle centre [245.0, 171.5, 44.3], seat R 1.75 (radial clearance 0.25); saddle 8.0 x 5.1 mm, seat 0.85 mm, end flare R 2.0; strap 3.0 x 0.6 mm, top z 46.65, latch -y
- R2 (J-PWR): notch y 181.2–186.0, floor z 42.1 (3.9 mm deep); bundle centre [245.0, 183.6, 44.4], seat R 1.457107 (radial clearance 0.25); saddle 8.0 x 4.514214 mm, seat 0.842893 mm, end flare R 2.0; strap 3.0 x 0.6 mm, top z 46.457107, latch -y

## Release travel sensitivity (middle withdrawn)

NB-CAN gap is to recorded solids only; the rear-side parts of those boards have no recorded height, so the gap is the height they may have.

| Cable | Travel (mm) | Extra length (mm) | Envelope bottom z (mm) | NB-278 plane | NB-CAN gap to recorded solids (mm) |
|---|---|---|---|---|---|
| J-SIG | 2.45 | 2.45 | 30.15 | clear | 17.20 |
| J-SIG | 5 | 5.00 | 27.60 | clear | 14.73 |
| J-SIG | 7.5 | 7.50 | 25.10 | clear | 12.35 |
| J-SIG | 10 | 10.00 | 22.60 | clear | 9.90 |
| J-SIG | 12.5 | 12.50 | 20.10 | conflict | 7.40 |
| J-SIG | 15 | 15.00 | 17.60 | conflict | 4.90 |
| J-PWR | 2.45 | 2.45 | 30.44 | clear | 17.05 |
| J-PWR | 5 | 5.00 | 27.89 | clear | 14.52 |
| J-PWR | 7.5 | 7.50 | 25.39 | clear | 12.04 |
| J-PWR | 10 | 10.00 | 22.89 | clear | 9.58 |
| J-PWR | 12.5 | 12.50 | 20.39 | conflict | 7.13 |
| J-PWR | 15 | 15.00 | 17.89 | conflict | 4.73 |

## Bend radius against the maker rule

| Wire | AWG | OD range (mm) | In JST window | Meets 50 V / 105 °C | Required centreline R J-SIG / J-PWR (mm) | Route R (mm) |
|---|---|---|---|---|---|---|
| Alpha Wire 1852 | 28 | 0.8382–0.9398 | yes | yes | 10.3378 / 10.062539 | 5.0 |
| Alpha Wire 1853 | 26 | 0.9398–1.0414 | **no** | yes | 11.4554 / 11.150381 | 5.0 |
| Alpha Wire 2843/7 | 26 | 0.7366–0.8382 | **no** | yes | 9.2202 / 8.974697 | 5.0 |

| Cable | R (mm) | Installed hook envelope bottom ≤ z (mm) | 15 mm release ≤ z (mm) | Route waypoints admit R |
|---|---|---|---|---|
| J-SIG | 5.0 | 32.60 | 17.60 | yes |
| J-PWR | 5.0 | 32.89 | 17.89 | yes |
| J-SIG | 7.5 | 30.10 | 15.10 | **no** |
| J-PWR | 7.5 | 30.39 | 15.39 | **no** |
| J-SIG | 8.9 | 28.70 | 13.70 | **no** |
| J-PWR | 8.9 | 28.99 | 13.99 | **no** |
| J-SIG | 10.0 | 27.60 | 12.60 | **no** |
| J-PWR | 10.0 | 27.89 | 12.89 | **no** |
| J-SIG | 11.0 | 26.60 | 11.60 | **no** |
| J-PWR | 11.0 | 26.89 | 11.89 | **no** |

## Notched rail strength (conditional)

Model: cantilever rail:middle:0 fixed at the top crossmember (y 142, joint stiffness not evaluated), free end y 274, tip load P; moment at the notch edge nearest the root. Kt: Inglis upper estimate 1 + 2 sqrt(depth / corner radius); conservative for a flat-bottomed groove, not a chart or FEA value.

| Notch | Depth (mm) | Remaining (mm) | Lever (mm) | Kt | Allowable tip load vertical / lateral (N) |
|---|---|---|---|---|---|
| N1 | 4.3 | 7.7 | 105.2 | 5.64 | 15.72 / 11.90 |
| N2 | 3.9 | 8.1 | 92.8 | 5.42 | 20.51 / 14.81 |

Tip deflection at 5 N: 0.0634 mm without, 0.0838 mm with the notches.

## Reservations proposed to the owner (not adopted)

- **RV-DIP-J-SIG** (A01:J-SIG:middle release (15 mm Stage10 travel)): XY [260.5, 162.65, 271.6, 180.35], z [17.1, 48.4]. the hook envelope falls to z 17.6 while the housing is withdrawn; no foreign board, part or wiring may occupy this volume.
- **RV-ACCESS-J-SIG** (A01:J-SIG:middle latch press and pull from the panel side): XY [260.5, 162.65, 271.6, 180.35], z [2.0, 48.4]. only needed if the middle connectors are serviced with the neighbouring front boards in place; otherwise those boards must come out with the front panel.
- **RV-DIP-J-PWR** (A01:J-PWR:middle release (15 mm Stage10 travel)): XY [280.5, 167.025, 291.6, 180.975], z [17.392893, 48.4]. the hook envelope falls to z 17.89 while the housing is withdrawn; no foreign board, part or wiring may occupy this volume.
- **RV-ACCESS-J-PWR** (A01:J-PWR:middle latch press and pull from the panel side): XY [280.5, 167.025, 291.6, 180.975], z [2.0, 48.4]. only needed if the middle connectors are serviced with the neighbouring front boards in place; otherwise those boards must come out with the front panel.
- **RV-GUIDE-R2-SW1501** (guide:R2:leg+): SW1501 top ≤ z 38.60 (17.00 mm above z 21.6).
- **RV-RUN-SW1401** (J-PWR run under A01-middle): SW1401 top ≤ z 42.59 (20.99 mm above z 21.6).
- **RV-RUN-SW1501** (J-PWR run under A01-middle): SW1501 top ≤ z 42.59 (20.99 mm above z 21.6).
- **RV-RUN-SW1601** (J-PWR run under A01-middle): SW1601 top ≤ z 42.59 (20.99 mm above z 21.6).
- 2MS3 drawing bound: terminal tips at z ≤ 16.63 if exact MPN gate OPEN (-5 drawing vs unsuffixed lock MPN); panel-bushing mounting with the front nut fully engaged; no foreign wiring, PCB or connector behind the terminals (UNKNOWN).

## Access and procedure

- J-SIG middle housing: long faces -x free 15.00 mm to rail:middle:0:N1:floor, +x free 11.90 mm to release:A01:J-PWR:middle; panel-side corridor known hits none, foreign XY none; straight bundle below the housing 2.0 mm; finger operation NOT_DETERMINED; a CAD gap is not finger operability (M32-03).
- J-PWR middle housing: long faces -x free 11.90 mm to release:A01:J-SIG:middle, +x free 16.90 mm to rail:middle:2; panel-side corridor known hits none, foreign XY none; straight bundle below the housing 2.0 mm; finger operation NOT_DETERMINED; a CAD gap is not finger operability (M32-03).

**assembly**

1. Bench: dress each cable as a tight round bundle (sleeve or wrap) and crimp/insert per JST tooling (vendor, Q-H01).
2. Fit the jack carrier and A01-jack; fit the middle carrier with R1/R2 saddles snapped into notches N1/N2 (legs into the flank grooves).
3. Mate J-SIG:local and J-PWR:local from the rear (+z) and form the free local loops left of x 232.
4. Lay each bundle in its saddle and close the strap latch (rail top exposed, A01-middle not yet fitted).
5. Bench: mate the J-SIG/J-PWR middle housings onto the A01-middle headers; before the rear (core) carrier is fitted, lower A01-middle onto its spacers along -z with the hooks hanging below it, feeding slack back through the guides; fit the four screws, then the rear carrier.
6. Fit the core onto the DIN connector and connect K-PWR last.

**service_core**

1. Power off and discharge; remove the rear cover.
2. Disconnect K-PWR; release the four core screws; support both handles and withdraw the core 40 mm along +z. J-SIG and J-PWR are not touched.

**service_middle_connectors**

1. Power off. Remove the front panel; front access to the middle headers needs the corridor in reservation RV-ACCESS (owner decision).
2. Press the GH latch with a flat tool, hold the bundle and pull within 15 degrees of -z until the housing is free; the cable slides back through R1/R2 from the local loop.
3. Refit: push the housing on until it latches; draw the slack back to the local loop.

**harness_replacement**

1. Requires removal of A01-middle (core removed first) or front access through RV-ACCESS; open the strap latches R1/R2 with a flat tool from +x.

## Measurements still NOT RUN

- **M32-01** Selected wire MPN with the maker minimum bend radius, OD and the dressed 4/7-conductor bundle diameter.
- **M32-02** GH unmating on a bench coupon: stroke to free, force, latch side, bundle grip length within 15 degrees.
- **M32-03** Latch press and pull at the moved middle headers with the real neighbours fitted (finger or tool).
- **M32-04** A01-middle bow at the notch positions after assembly, spacer length, tab and notch-floor heights.
- **M32-05** Neighbouring board planes, outlines and rear-side heights in RV-DIP / RV-ACCESS / RV-RUN.
- **M32-06** Notched rail coupon: stiffness and strength at the notches with the real corner radius.
- **M32-07** R1/R2 saddle fit, strap latch, axial slide force, abrasion after repeated release (M-12).
- **M32-08** Mock-up path and cut lengths for installed and release states (M-09).
- **M32-09** Panel-to-carrier registration (sweep gap to SW1701 / J1610).
