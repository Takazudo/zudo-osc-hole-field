# Stage32 service envelope (generated)

Design study only. Calculations on planning geometry and stated inputs; nothing is measured, and a clear envelope is not physical non-interference.

## Criteria per candidate

| Candidate | S1 static | S2 robust K4 | S3 retention | S4 sweeps | S5 core | S6 strength | S7 release | S8 foreign allowance | S9 bend maker rule | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| B31 | yes | **no** | **no** | **no** | yes | yes | yes | yes | **no** | NOT_ROBUST_UNDER_STAGE32_CHECKS |
| B32 | yes | yes | yes | yes | yes | yes | yes | yes | **no** | CONDITIONAL_PENDING_WIRE_SELECTION |

## Tightest clearances after the tolerance stack

| Candidate | Cable | Obstacle | Sampled (mm) | Margin | Tolerance WC / RSS (mm) | Robust spare (mm) | K4 0.15 |
|---|---|---|---|---|---|---|---|
| B31 | J-PWR | board:A01-middle:1 | 0.79 | 0.50 | 1.05 / 0.86 | -0.76 | **no** |
| B31 | J-PWR | board:A01-middle:2 | 0.79 | 0.50 | 1.02 / 0.83 | -0.73 | **no** |
| B31 | J-SIG | board:A01-middle:2 | 0.80 | 0.50 | 0.85 / 0.67 | -0.55 | **no** |
| B31 | J-SIG | board:A01-middle:0 | 0.80 | 0.50 | 0.80 / 0.62 | -0.50 | **no** |
| B31 | J-PWR | tool:A01-jack:M4 | 0.69 | 0.50 | 0.28 / 0.16 | -0.08 | **no** |
| B32 | J-PWR | board:A01-middle:1 | 2.14 | 0.50 | 1.44 / 0.92 | 0.20 | yes |
| B32 | J-PWR | board:A01-middle:1 | 2.14 | 0.50 | 1.44 / 0.92 | 0.20 | yes |
| B32 | J-SIG | board:A01-middle:0 | 1.95 | 0.50 | 1.25 / 0.74 | 0.20 | yes |
| B32 | J-SIG | board:A01-middle:0 | 1.95 | 0.50 | 1.25 / 0.74 | 0.20 | yes |
| B32 | J-SIG | board:A01-middle:2 | 1.95 | 0.50 | 1.25 / 0.74 | 0.20 | yes |

## K4 sensitivity to the bow model (B32)

| Bow case | Tightest | Robust spare (mm) | K4 |
|---|---|---|---|
| edge-M1-M3 (half sine along the M1-M3 mount line) | J-PWR board:A01-middle:1 | 0.27 | yes |
| length-142-292 (base: half sine over the board length) | J-PWR board:A01-middle:1 | 0.20 | yes |
| uniform-diagonal (0.75 % of the A01-middle outline diagonal applied everywhere (interior bow of a four-corner-supported board)) | J-SIG board:A01-middle:0 | -0.38 | **no** |

## B32 geometry

- J-SIG: design length 136 mm (minimum installed 106.73 + 15 mm release extra 19.00 + 10 slack); installed with the slack in the local loop, top z 71.04
- J-PWR: design length 150 mm (minimum installed 121.16 + 15 mm release extra 18.80 + 10 slack); installed with the slack in the local loop, top z 70.92
- A01:J-PWR:middle: [283, 150] → [288.0, 174.0], 90°, sweep [281.0, 167.525, 291.1, 180.475] z [26.1, 48.4]
- A01:J-SIG:middle: [260, 150] → [268.0, 171.5], 90°, sweep [261.0, 163.15, 271.1, 179.85] z [26.1, 48.4]
- R1 (J-SIG): notch y 168.8–174.2, floor z 41.5 (4.5 mm deep); bundle centre [245.0, 171.5, 44.1], seat R 1.75 (radial clearance 0.25); saddle 8.0 x 5.1 mm, seat 0.85 mm, end flare R 2.0; strap 3.0 x 0.6 mm, top z 46.45, latch -y
- R2 (J-PWR): notch y 181.2–186.0, floor z 41.9 (4.1 mm deep); bundle centre [245.0, 183.6, 44.2], seat R 1.457107 (radial clearance 0.25); saddle 8.0 x 4.514214 mm, seat 0.842893 mm, end flare R 2.0; strap 3.0 x 0.6 mm, top z 46.257107, latch -y

## Release travel sensitivity (middle withdrawn)

NB-CAN gap is to recorded solids only; the rear-side parts of those boards have no recorded height, so the gap is the height they may have.

| Cable | Travel (mm) | Slide through guide (mm) | Local loop top z (mm) | Envelope bottom z (mm) | NB-278 plane | NB-CAN gap to recorded solids (mm) |
|---|---|---|---|---|---|---|
| J-SIG | 2.45 | 2.45 | 69.81 | 30.15 | clear | 17.20 |
| J-SIG | 5 | 5.00 | 68.54 | 27.60 | clear | 14.73 |
| J-SIG | 7.5 | 7.50 | 67.29 | 25.10 | clear | 12.35 |
| J-SIG | 10 | 10.00 | 66.04 | 22.60 | clear | 9.90 |
| J-SIG | 12.5 | 12.50 | 64.79 | 20.10 | conflict | 7.40 |
| J-SIG | 15 | 15.00 | 63.54 | 17.60 | conflict | 4.90 |
| J-PWR | 2.45 | 2.45 | 69.70 | 30.44 | clear | 17.05 |
| J-PWR | 5 | 5.00 | 68.42 | 27.89 | clear | 14.52 |
| J-PWR | 7.5 | 7.50 | 67.17 | 25.39 | clear | 12.04 |
| J-PWR | 10 | 10.00 | 65.92 | 22.89 | clear | 9.58 |
| J-PWR | 12.5 | 12.50 | 64.67 | 20.39 | conflict | 7.13 |
| J-PWR | 15 | 15.00 | 63.42 | 17.89 | conflict | 4.73 |

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
| N1 | 4.5 | 7.5 | 105.2 | 5.74 | 14.64 / 11.36 |
| N2 | 4.1 | 7.9 | 92.8 | 5.53 | 19.12 / 14.13 |

Tip deflection at 5 N: 0.0634 mm without, 0.0863 mm with the notches.

## Reservations proposed to the owner (not adopted)

- **RV-DIP-J-SIG** (A01:J-SIG:middle hook below the carrier bottom, installed and released (2.45-15 mm, constant length), and the housing sweep): XY [256.0, 162.65, 271.6, 180.35], z [17.0, 48.4]. the hook envelope reaches z 17.60 at the 15 mm Stage10 travel; installed it already reaches z 32.60, below the carrier bottom z 34. No neighbouring board, part or wiring may occupy this volume.
- **RV-ACCESS-J-SIG** (A01:J-SIG:middle latch press and pull from the panel side): XY [260.5, 162.65, 271.6, 180.35], z [0.0, 48.4]. only needed if the middle connectors are serviced with the neighbouring front boards in place; otherwise those boards must come out with the front panel.
- **RV-DIP-J-PWR** (A01:J-PWR:middle hook below the carrier bottom, installed and released (2.45-15 mm, constant length), and the housing sweep): XY [276.292893, 167.025, 291.6, 180.975], z [17.292893, 48.4]. the hook envelope reaches z 17.89 at the 15 mm Stage10 travel; installed it already reaches z 32.89, below the carrier bottom z 34. No neighbouring board, part or wiring may occupy this volume.
- **RV-ACCESS-J-PWR** (A01:J-PWR:middle latch press and pull from the panel side): XY [280.5, 167.025, 291.6, 180.975], z [0.0, 48.4]. only needed if the middle connectors are serviced with the neighbouring front boards in place; otherwise those boards must come out with the front panel.
- **RV-GUIDE-R2-SW1501** (guide:R2:leg+): SW1501 top ≤ z 38.40 (16.80 mm above z 21.6).
- **RV-RUN-SW1401** (J-PWR run under A01-middle): SW1401 top ≤ z 42.39 (20.79 mm above z 21.6).
- **RV-RUN-SW1501** (J-PWR run under A01-middle): SW1501 top ≤ z 42.39 (20.79 mm above z 21.6).
- **RV-RUN-SW1601** (J-PWR run under A01-middle): SW1601 top ≤ z 42.39 (20.79 mm above z 21.6).
- 2MS3 drawing bound: terminal tips at z ≤ 15.13 if exact MPN gate OPEN (-5 drawing vs unsuffixed lock MPN); panel-bushing mounting with the front nut fully engaged; no foreign wiring, PCB or connector behind the terminals (UNKNOWN).

## Access and procedure

- J-SIG middle housing: long faces -x free 12.00 mm to guide:R1:latch and 3.53 mm to the J-SIG bundle; +x free 11.90 mm to release:A01:J-PWR:middle and 4.62 mm to the J-PWR bundle; panel-side corridor known hits none, foreign XY none; straight bundle below the housing 2.0 mm; finger operation NOT_DETERMINED; a CAD gap is not finger operability (M32-03).
- J-PWR middle housing: long faces -x free 11.90 mm to release:A01:J-SIG:middle and 3.83 mm to the J-PWR bundle; +x free 16.90 mm to rail:middle:2 and – mm to the None bundle; panel-side corridor known hits none, foreign XY none; straight bundle below the housing 2.0 mm; finger operation NOT_DETERMINED; a CAD gap is not finger operability (M32-03).
- R1 strap latch: front access BLOCKED (hits rail:middle:0:N1:floor); reopen with A01-middle removed (+z), rail top exposed.
- R2 strap latch: front access BLOCKED (hits crossmember:jack:1, foreign:SW1501, rail:middle:0:N2:floor, SW1501); reopen with A01-middle removed (+z), rail top exposed.

**assembly**

1. Bench: dress each cable as a tight round bundle (sleeve or wrap) and crimp/insert per JST tooling (vendor, Q-H01).
2. Fit the jack carrier and A01-jack; fit the middle carrier with R1/R2 saddles snapped into notches N1/N2 (legs into the flank grooves).
3. Mate J-SIG:local and J-PWR:local from the rear (+z) and form the free local slack loops left of x 232 (modelled as a two-leg stand-up loop, top z about 71, 78.5 with the local end withdrawn; real loop shape is a surrogate until M32-08 / M-12).
4. Lay each bundle in its saddle and close the strap latch (rail top exposed, A01-middle not yet fitted).
5. Bench: mate the J-SIG/J-PWR middle housings onto the A01-middle headers; before the rear (core) carrier is fitted, lower A01-middle onto its spacers along -z with the hooks hanging below it, feeding slack back through the guides; fit the four screws, then the rear carrier.
6. Fit the core onto the DIN connector and connect K-PWR last.

**service_core**

1. Power off and discharge; remove the rear cover.
2. Disconnect K-PWR; release the four core screws; support both handles and withdraw the core 40 mm along +z. J-SIG and J-PWR are not touched.

**service_middle_connectors**

1. Power off. Remove the front panel; front access to the middle headers needs the corridor in reservation RV-ACCESS, or the neighbouring front boards removed with the panel (owner decision).
2. Press the GH latch with a flat tool, hold the bundle and pull within 15 degrees of -z until the housing is free; the bundle slides through the closed R1/R2 and the local slack loop shortens by the same length.
3. Refit: push the housing on until it latches; draw the slack back into the local loop.

**harness_replacement**

1. Remove the core (K-PWR first, 40 mm, then fully), the rear (core) carrier and A01-middle along +z; open the R1/R2 strap latches with a flat tool from +z with the rail top exposed. Front access cannot reach either latch (R1 tab over the rail, R2 corridor blocked by crossmember:jack:1 and the SW1501 column).

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
