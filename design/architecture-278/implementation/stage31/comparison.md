# Stage31 cable-entry comparison (generated)

Design study only. All values come from planning geometry and stated assumptions; nothing here is measured, and a clear envelope is not physical non-interference. Design lengths are not cut lengths.

## Criteria

- **K1:** every modelled check passes: routes clear every known keep-out and the other cable by the placement margin, all bends fit at the design radius, moved sweeps clear all known obstacles
- **K2:** all four release sweeps lie outside every foreign XY projection
- **K3:** no route needs a foreign rear-side height below 12.4 mm (the Stage30 cap, z 34, above the foreign PCB rear z 21.6)
- **K4:** the tightest spare beyond the placement margin is at least 0.15 mm

| Candidate | Headers | Rail | Dressing | K1 | K2 | K3 | K4 | Tightest spare (mm) | Smallest foreign rear-side allowance (mm) | Design length J-SIG / J-PWR (mm) |
|---|---|---|---|---|---|---|---|---|---|---|
| A | unchanged | two top notches | round bundles | yes | **no** | **no** | yes | 0.19 | 10.42 | 139 / 159 |
| B | J-SIG:middle and J-PWR:middle moved and turned 90 degrees (pin rows along y) | two top notches | round bundles | yes | yes | yes | yes | 0.19 | 22.89 | 138 / 149 |
| C | J-SIG:middle and J-PWR:middle translated, not turned | unchanged | flat single layer through the slot, round elsewhere | yes | yes | yes | **no** | 0.10 | 18.90 | 131 / 140 |

Recommended: **B** (the only candidate that meets K1-K4).

- B is the only candidate meeting K1-K4.
- Moving J-SIG:middle and J-PWR:middle into the strip between the J*10 jacks and the SW*01 switches and turning them 90 degrees keeps both release sweeps at least 0.5 mm from every foreign XY projection and known obstacle; at the Stage10 positions both sweeps overlap J1510/J1610/J1710.
- With the pin rows along y, each hook bends about the pin-row axis, so all conductors of a cable bend with the same radius.
- The notch depth can grow if a later check needs more clearance; C has no such freedom inside the 2.4 mm slot.

## A: Headers kept; two shallow notches in the middle carrier left rail

- Notch N1 (J-SIG): y 162.1–166.7 (4.6 mm), top z 43.7 → 2.3 mm deep, 9.7 mm of 12 left (local I ratio 0.528); route needs y 162.40–166.40 and top ≤ 44.00. Strength NOT_CALCULATED.
- Notch N2 (J-PWR): y 180.9–185.1 (4.2 mm), top z 44.2 → 1.8 mm deep, 10.2 mm of 12 left (local I ratio 0.614); route needs y 181.29–184.71 and top ≤ 44.59. Strength NOT_CALCULATED.

| Cable | Dressing | Installed pad-to-pad (mm) | Release extra (mm) | Design length proposal (mm) | Straight lead local / middle (mm) | Bends (r 5) | Max uniform r (mm) | Min surface clearance (mm) | Nearest keep-outs | Foreign bounds (max top z) | Core motion clearance (mm) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| J-SIG | ROUND_BUNDLE | 109.52 | 19.00 | 139 | 7.5 / 2.0 | 7 | 5.00 | 0.70 | rail:middle:0:N1:floor 0.70, rail:middle:0:y142-162.1 0.70, rail:middle:0:y166.7-180.9 0.70 | D1510 ≤ 32.02, D15101 ≤ 32.07, J1510 ≤ 43.05 | 8.80 |
| J-PWR | ROUND_BUNDLE | 129.41 | 18.80 | 159 | 7.6 / 2.0 | 8 | 5.00 | 0.69 | tool:A01-jack:M4 0.69, board:A01-middle:0 0.79, board:A01-middle:1 0.79 | J1710 ≤ 32.29, SW1401 ≤ 44.49, SW1501 ≤ 44.49 | 2.39 |

- Cable to cable: minimum surface gap 5.69 mm (required 0.5). Tightest spare 0.19 mm after the sampling deduction.
- Release sweeps: smallest gap 0.00 mm to any known obstacle or foreign XY (required 0.5).
- Release cases (bend-feasible surrogate, 15 mm travel): J-SIG extra 15.0, 4.0, 19.0 mm, envelope dips to z 17.6; J-PWR extra 15.0, 3.8, 18.8 mm, envelope dips to z 17.9.
- Release sweeps over foreign XY: J-PWR:middle: D1610, D16101, J1709, J1710; J-SIG:middle: D1510, D15101, J1509, J1510, J1609, J1610.
- Core withdrawal: minimum clearance 2.39 mm to the core motion box; K-PWR first, then 40 mm, unchanged.
- Retention:
  - R1 (J-SIG) at notch N1 floor: saddle in the notch with a strap or tie over the bundle; strap anchorage formed in the rail flank (local carrier shape); dimensions null.
  - R2 (J-PWR) at notch N2 floor: saddle in the notch with a strap or tie over the bundle; strap anchorage formed in the rail flank (local carrier shape); dimensions null.
- Assembly (NOT RUN):
  1. Fit the jack carrier, A01-jack, the middle carrier and A01-middle as in Stage10.
  2. Mate the GHR housings into J-SIG:middle and J-PWR:middle along -z to +z from the panel side, with the front panel off.
  3. Lay each bundle over its notch saddle and fit R1/R2.
  4. Form the free loop at the local end and mate J-SIG:local and J-PWR:local from the rear, left of the A01-middle edge (x < 232).
  5. Fit the core onto the DIN connector and connect K-PWR last. Service: disconnect K-PWR, then withdraw the core 40 mm; J-SIG and J-PWR are not touched.

## B: Middle headers moved into the clear strip and turned 90 degrees; two shallow notches

- Header move: A01:J-PWR:middle [283, 150] → [288.0, 174.7], rotation 90°, pin row along y; nearest other sweep gap 9.9 mm
- Header move: A01:J-SIG:middle [260, 150] → [268.0, 171.5], rotation 90°, pin row along y; nearest other sweep gap 9.9 mm
- Notch N1 (J-SIG): y 168.6–173.8 (5.2 mm), top z 43.7 → 2.3 mm deep, 9.7 mm of 12 left (local I ratio 0.528); route needs y 168.95–173.50 and top ≤ 44.00. Strength NOT_CALCULATED.
- Notch N2 (J-PWR): y 180.9–185.1 (4.2 mm), top z 44.2 → 1.8 mm deep, 10.2 mm of 12 left (local I ratio 0.614); route needs y 181.29–184.71 and top ≤ 44.59. Strength NOT_CALCULATED.

| Cable | Dressing | Installed pad-to-pad (mm) | Release extra (mm) | Design length proposal (mm) | Straight lead local / middle (mm) | Bends (r 5) | Max uniform r (mm) | Min surface clearance (mm) | Nearest keep-outs | Foreign bounds (max top z) | Core motion clearance (mm) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| J-SIG | ROUND_BUNDLE | 108.71 | 19.00 | 138 | 7.5 / 2.0 | 8 | 5.00 | 0.70 | rail:middle:0:N1:floor 0.70, rail:middle:0:y173.8-180.9 0.70, board:A01-middle:0 0.80 | none | 3.12 |
| J-PWR | ROUND_BUNDLE | 119.58 | 18.80 | 149 | 7.6 / 2.0 | 7 | 5.00 | 0.69 | tool:A01-jack:M4 0.69, board:A01-middle:1 0.79, board:A01-middle:2 0.79 | SW1401 ≤ 44.49, SW1501 ≤ 44.49, SW1601 ≤ 44.49 | 2.39 |

- Cable to cable: minimum surface gap 5.69 mm (required 0.5). Tightest spare 0.19 mm after the sampling deduction.
- Release sweeps: smallest gap 0.57 mm to any known obstacle or foreign XY (required 0.5).
- Release cases (bend-feasible surrogate, 15 mm travel): J-SIG extra 15.0, 4.0, 19.0 mm, envelope dips to z 17.6; J-PWR extra 15.0, 3.8, 18.8 mm, envelope dips to z 17.9.
- Release sweeps over foreign XY: none.
- Core withdrawal: minimum clearance 2.39 mm to the core motion box; K-PWR first, then 40 mm, unchanged.
- Retention:
  - R1 (J-SIG) at notch N1 floor: saddle in the notch with a strap or tie over the bundle; strap anchorage formed in the rail flank (local carrier shape); dimensions null.
  - R2 (J-PWR) at notch N2 floor: saddle in the notch with a strap or tie over the bundle; strap anchorage formed in the rail flank (local carrier shape); dimensions null.
- Assembly (NOT RUN):
  1. Fit the jack carrier, A01-jack, the middle carrier and A01-middle as in Stage10.
  2. Mate the GHR housings into J-SIG:middle and J-PWR:middle along -z to +z from the panel side, with the front panel off.
  3. Lay each bundle over its notch saddle and fit R1/R2.
  4. Form the free loop at the local end and mate J-SIG:local and J-PWR:local from the rear, left of the A01-middle edge (x < 232).
  5. Fit the core onto the DIN connector and connect K-PWR last. Service: disconnect K-PWR, then withdraw the core 40 mm; J-SIG and J-PWR are not touched.

## C: Middle headers translated; flat single-layer conductors through the existing 2.4 mm slot, rail unchanged

- Header move: A01:J-PWR:middle [283, 150] → [283.0, 174.2], rotation 0°, pin row along x; nearest other sweep gap 3.175 mm
- Header move: A01:J-SIG:middle [260, 150] → [265.0, 165.0], rotation 0°, pin row along x; nearest other sweep gap 3.175 mm
- Rail unchanged.

| Cable | Dressing | Installed pad-to-pad (mm) | Release extra (mm) | Design length proposal (mm) | Straight lead local / middle (mm) | Bends (r 5) | Max uniform r (mm) | Min surface clearance (mm) | Nearest keep-outs | Foreign bounds (max top z) | Core motion clearance (mm) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| J-SIG | FLAT_SINGLE_LAYER | 103.97 | 16.60 | 131 | 8.7 / 2.0 | 6 | 5.00 | 0.60 | board:A01-middle:0 0.60, rail:middle:0 0.60, board:A01-middle:2 0.66 | none | 5.48 |
| J-PWR | FLAT_SINGLE_LAYER | 116.24 | 13.59 | 140 | 8.7 / 2.0 | 8 | 5.00 | 0.60 | board:A01-middle:1 0.60, rail:middle:0 0.60, tool:A01-jack:M4 0.70 | SW1301 ≤ 47.78, SW1401 ≤ 46.10, SW1501 ≤ 40.50 | 2.20 |

- Cable to cable: minimum surface gap 2.49 mm (required 0.5). Tightest spare 0.10 mm after the sampling deduction.
- Release sweeps: smallest gap 0.55 mm to any known obstacle or foreign XY (required 0.5).
- Release cases (bend-feasible surrogate, 15 mm travel): J-SIG extra 15.0, 1.6, 16.6 mm, envelope dips to z 17.6; J-PWR extra 12.0, 1.6, 13.6 mm, envelope dips to z 17.9.
- Release sweeps over foreign XY: none.
- Core withdrawal: minimum clearance 2.20 mm to the core motion box; K-PWR first, then 40 mm, unchanged.
- Retention:
  - R1 (J-SIG) at slot over rail:middle:0 at y 165.6: comb or lacing that keeps one layer, on a low-friction liner bonded to the rail top; dimensions null.
  - R2 (J-PWR) at slot over rail:middle:0 at y 183.8: comb or lacing that keeps one layer, on a low-friction liner bonded to the rail top; dimensions null.
- Assembly (NOT RUN):
  1. Fit the jack carrier, A01-jack, the middle carrier and A01-middle as in Stage10.
  2. Mate the GHR housings into J-SIG:middle and J-PWR:middle along -z to +z from the panel side, with the front panel off.
  3. Fan each bundle out into one layer before the A01-middle edge, slide it through the slot over the rail with the liner and comb, and gather it again inside the ring.
  4. Form the free loop at the local end and mate J-SIG:local and J-PWR:local from the rear, left of the A01-middle edge (x < 232).
  5. Fit the core onto the DIN connector and connect K-PWR last. Service: disconnect K-PWR, then withdraw the core 40 mm; J-SIG and J-PWR are not touched.

## Stage30 candidates rejected again

| Stage30 | Stage30 status | Stage31 reasons |
|---|---|---|
| W1 | BLOCKED_BY_KEEP_OUT | no J-SIG route: Stage30 studied J-PWR only and the J-SIG proxies still cross rail:middle:0; bend: bend radius 5.0 mm does not fit leg 0 (7.0 > 2.1 mm); keep-out clearance below the margin: rail:middle:0 |
| W2 | BLOCKED_BY_KEEP_OUT | no J-SIG route: Stage30 studied J-PWR only and the J-SIG proxies still cross rail:middle:0; bend: bend radius 5.0 mm does not fit leg 0 (5.96 > 2.1 mm); keep-out clearance below the margin: board:A01-middle:0, board:A01-middle:2, rail:middle:0 |
| W3 | UNKNOWN_FOREIGN_DEPTH | no J-SIG route: Stage30 studied J-PWR only and the J-SIG proxies still cross rail:middle:0; bend: bend radius 5.0 mm does not fit leg 0 (7.0 > 2.1 mm); needs foreign rear-side height below 12.4 mm at J1710, SW1401, SW1501 |
| W4 | CENTRELINE_CLEAR_UNDER_ASSUMPTIONS | no J-SIG route: Stage30 studied J-PWR only and the J-SIG proxies still cross rail:middle:0; bend: bend radius 5.0 mm does not fit leg 0 (7.08 > 2.1 mm) |

## Copper allocations for the moved headers (B)

Stage10 trace-length model over the Stage30 design DIN XY; routed copper NOT RUN.

| Edge | Kind | Net | From → To | Stage30 (mm) | Stage31 (mm) | Δ (mm) |
|---|---|---|---|---|---|---|
| 58 | middle_copper | /A01/REF5 | A01:J-SIG:middle:1 → DIN:middle:c1 | 68.61 | 47.70 | -20.90 |
| 59 | middle_copper | /A01/REFN5 | A01:J-SIG:middle:3 → DIN:middle:c2 | 72.72 | 50.10 | -22.61 |
| 60 | middle_copper | /A01/IN_BUFFER | A01:J-SIG:middle:4 → DIN:middle:c3 | 76.23 | 51.91 | -24.33 |
| 61 | middle_copper | /A01/OFFSET_BUFFER | A01:J-SIG:middle:5 → DIN:middle:c4 | 79.75 | 53.71 | -26.04 |
| 62 | middle_copper | /A01/SUM_NEG | A01:J-SIG:middle:6 → DIN:middle:c5 | 83.27 | 56.42 | -26.85 |
| 68 | middle_power_copper | +12V | A01:J-PWR:middle:1 → A01:K-PWR:middle:1 | 63.33 | 32.00 | -31.34 |
| 69 | middle_power_copper | -12V | A01:J-PWR:middle:2 → A01:K-PWR:middle:2 | 63.33 | 34.03 | -29.30 |
| 70 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → A01:J-SIG:middle:2 | 28.42 | 30.56 | +2.14 |
| 71 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → A01:J-SIG:middle:7 | 35.61 | 32.42 | -3.19 |
| 72 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → A01:C-SIG:middle:6 | 173.37 | 150.40 | -22.97 |
| 73 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → A01:K-PWR:middle:3 | 63.93 | 37.50 | -26.43 |
| 74 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b1 | 61.54 | 32.02 | -29.52 |
| 75 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b2 | 64.46 | 34.94 | -29.52 |
| 76 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b3 | 67.38 | 37.86 | -29.52 |
| 77 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b4 | 70.30 | 40.78 | -29.52 |
| 78 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b5 | 73.22 | 43.70 | -29.52 |
| 79 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b6 | 76.14 | 46.62 | -29.52 |
| 80 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b7 | 79.07 | 49.54 | -29.52 |
| 81 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b8 | 81.99 | 52.46 | -29.52 |

Paths changed: signal_net_paths 6, power_and_return_endpoint_paths 28, local_endpoint_paths 0.

## Copper allocations for the moved headers (C)

Stage10 trace-length model over the Stage30 design DIN XY; routed copper NOT RUN.

| Edge | Kind | Net | From → To | Stage30 (mm) | Stage31 (mm) | Δ (mm) |
|---|---|---|---|---|---|---|
| 58 | middle_copper | /A01/REF5 | A01:J-SIG:middle:1 → DIN:middle:c1 | 68.61 | 51.72 | -16.88 |
| 59 | middle_copper | /A01/REFN5 | A01:J-SIG:middle:3 → DIN:middle:c2 | 72.72 | 55.81 | -16.91 |
| 60 | middle_copper | /A01/IN_BUFFER | A01:J-SIG:middle:4 → DIN:middle:c3 | 76.23 | 58.45 | -17.78 |
| 61 | middle_copper | /A01/OFFSET_BUFFER | A01:J-SIG:middle:5 → DIN:middle:c4 | 79.75 | 61.10 | -18.65 |
| 62 | middle_copper | /A01/SUM_NEG | A01:J-SIG:middle:6 → DIN:middle:c5 | 83.27 | 63.75 | -19.52 |
| 68 | middle_power_copper | +12V | A01:J-PWR:middle:1 → A01:K-PWR:middle:1 | 63.33 | 35.50 | -27.83 |
| 69 | middle_power_copper | -12V | A01:J-PWR:middle:2 → A01:K-PWR:middle:2 | 63.33 | 35.50 | -27.83 |
| 70 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → A01:J-SIG:middle:2 | 28.42 | 27.05 | -1.37 |
| 71 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → A01:J-SIG:middle:7 | 35.61 | 34.24 | -1.37 |
| 72 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → A01:C-SIG:middle:6 | 173.37 | 145.54 | -27.83 |
| 73 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → A01:K-PWR:middle:3 | 63.93 | 36.10 | -27.83 |
| 74 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b1 | 61.54 | 36.03 | -25.51 |
| 75 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b2 | 64.46 | 37.24 | -27.22 |
| 76 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b3 | 67.38 | 39.55 | -27.83 |
| 77 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b4 | 70.30 | 42.47 | -27.83 |
| 78 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b5 | 73.22 | 45.39 | -27.83 |
| 79 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b6 | 76.14 | 48.31 | -27.83 |
| 80 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b7 | 79.07 | 51.24 | -27.83 |
| 81 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b8 | 81.99 | 54.16 | -27.83 |

Paths changed: signal_net_paths 6, power_and_return_endpoint_paths 28, local_endpoint_paths 0.

## Measurements before a prototype (all NOT RUN)

- **M31-01** Wire MPN, insulation OD and dressed bundle diameter for 4 and 7 conductors. every envelope uses OD 1.0 and packing factors 2.414 / 3.0.
- **M31-02** Wire maker minimum static bend radius. the routes use 5 mm; each route reports the largest radius it admits.
- **M31-03** Straight length needed behind the GHR housing before a bend. 2 mm is a design choice; JST states none.
- **M31-04** Actual stack heights: A01-jack rear face, A01-middle front face, middle carrier rail top/front, mount spacer and screw-head heights. the corridor under A01-middle and the notch floors are sized from Stage10 planning z values.
- **M31-05** Rear-side height of the foreign parts each route passes over (bounds in candidates.json). foreign depth is unknown; the route is only clear below the reported bound.
- **M31-06** Middle carrier rail stiffness and strength with the notches, with notch edge radius and finish. rail strength after the notch is NOT_CALCULATED.
- **M31-07** GH unmating travel and release from the panel side at the moved middle headers: latch access, axial pull, finger/tool space and the space the cable needs below the hook while the housing is withdrawn. the Stage10 15 mm release makes the hook dip to about z 17.6, through the foreign PCB plane whose outline is unknown.
- **M31-08** Mock-up path length per cable, including the free loop at the local end and the release cases (M-09). design lengths are not cut lengths.
- **M31-09** Strap/tie geometry for the notch saddles and the pull load they take (M-12). retention dimensions are null.
