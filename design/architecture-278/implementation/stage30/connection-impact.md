# Stage30 A01 connection impact of the provisional DIN positions

Generated. Allocations are the Stage10 `trace_length` engineering model (1.15 × octile XY + 7 mm + |dz|), not routed copper. Straight = 3D pad-to-pad distance. Routed copper: NOT RUN (null everywhere).

## Assigned contacts and where they connect

| Contact | Net | A01-middle side (Ref:pin, board) | A01-core side (Ref:pin, board) |
|---|---|---|---|
| b1 | AGND | A01:J-PWR:middle:4 (A01-middle) | A01:K-PWR:local:3 (A01-core) |
| b2 | AGND | A01:J-PWR:middle:4 (A01-middle) | A01:K-PWR:local:3 (A01-core) |
| b3 | AGND | A01:J-PWR:middle:4 (A01-middle) | A01:K-PWR:local:3 (A01-core) |
| b4 | AGND | A01:J-PWR:middle:4 (A01-middle) | A01:K-PWR:local:3 (A01-core) |
| b5 | AGND | A01:J-PWR:middle:4 (A01-middle) | A01:K-PWR:local:3 (A01-core) |
| b6 | AGND | A01:J-PWR:middle:4 (A01-middle) | A01:K-PWR:local:3 (A01-core) |
| b7 | AGND | A01:J-PWR:middle:4 (A01-middle) | A01:K-PWR:local:3 (A01-core) |
| b8 | AGND | A01:J-PWR:middle:4 (A01-middle) | A01:K-PWR:local:3 (A01-core) |
| c1 | /A01/REF5 | A01:J-SIG:middle:1 (A01-middle)<br>A01:C-SIG:middle:1 (A01-middle) | U7104:1 (A01-core) |
| c2 | /A01/REFN5 | A01:J-SIG:middle:3 (A01-middle)<br>A01:C-SIG:middle:2 (A01-middle) | U7104:7 (A01-core) |
| c3 | /A01/IN_BUFFER | A01:J-SIG:middle:4 (A01-middle) | R7117:1 (A01-core) |
| c4 | /A01/OFFSET_BUFFER | A01:J-SIG:middle:5 (A01-middle) | RN7101:3 (A01-core) |
| c5 | /A01/SUM_NEG | A01:J-SIG:middle:6 (A01-middle) | U7105:8 (A01-core) |
| c6 | /A01/IN_REMOTE | A01:C-SIG:middle:3 (A01-middle) | R7113:2 (A01-core) |
| c7 | /A01/Cc045d2_W | A01:C-SIG:middle:4 (A01-middle) | R7115:1 (A01-core) |
| c8 | /A01/C38cac0_W | A01:C-SIG:middle:5 (A01-middle) | R7119:1 (A01-core) |

## DIN-incident edges (34 copper allocations change; 16 mated pairs keep 25 mm)

| Edge | Kind | Net | From → To | Straight S10 → design mm | Allocation S10 → design mm | Δ mm |
|---|---|---|---|---|---|---|
| 42 | DIN_mated_pair | /A01/REF5 | DIN:middle:c1 → DIN:rear:c1 | 19.200 → 19.200 | 25.000 → 25.000 | +0.000 |
| 43 | DIN_mated_pair | /A01/REFN5 | DIN:middle:c2 → DIN:rear:c2 | 19.200 → 19.200 | 25.000 → 25.000 | +0.000 |
| 44 | DIN_mated_pair | /A01/IN_BUFFER | DIN:middle:c3 → DIN:rear:c3 | 19.200 → 19.200 | 25.000 → 25.000 | +0.000 |
| 45 | DIN_mated_pair | /A01/OFFSET_BUFFER | DIN:middle:c4 → DIN:rear:c4 | 19.200 → 19.200 | 25.000 → 25.000 | +0.000 |
| 46 | DIN_mated_pair | /A01/SUM_NEG | DIN:middle:c5 → DIN:rear:c5 | 19.200 → 19.200 | 25.000 → 25.000 | +0.000 |
| 47 | DIN_mated_pair | /A01/IN_REMOTE | DIN:middle:c6 → DIN:rear:c6 | 19.200 → 19.200 | 25.000 → 25.000 | +0.000 |
| 48 | DIN_mated_pair | /A01/Cc045d2_W | DIN:middle:c7 → DIN:rear:c7 | 19.200 → 19.200 | 25.000 → 25.000 | +0.000 |
| 49 | DIN_mated_pair | /A01/C38cac0_W | DIN:middle:c8 → DIN:rear:c8 | 19.200 → 19.200 | 25.000 → 25.000 | +0.000 |
| 50 | DIN_mated_pair | AGND | DIN:middle:b1 → DIN:rear:b1 | 19.200 → 19.200 | 25.000 → 25.000 | +0.000 |
| 51 | DIN_mated_pair | AGND | DIN:middle:b2 → DIN:rear:b2 | 19.200 → 19.200 | 25.000 → 25.000 | +0.000 |
| 52 | DIN_mated_pair | AGND | DIN:middle:b3 → DIN:rear:b3 | 19.200 → 19.200 | 25.000 → 25.000 | +0.000 |
| 53 | DIN_mated_pair | AGND | DIN:middle:b4 → DIN:rear:b4 | 19.200 → 19.200 | 25.000 → 25.000 | +0.000 |
| 54 | DIN_mated_pair | AGND | DIN:middle:b5 → DIN:rear:b5 | 19.200 → 19.200 | 25.000 → 25.000 | +0.000 |
| 55 | DIN_mated_pair | AGND | DIN:middle:b6 → DIN:rear:b6 | 19.200 → 19.200 | 25.000 → 25.000 | +0.000 |
| 56 | DIN_mated_pair | AGND | DIN:middle:b7 → DIN:rear:b7 | 19.200 → 19.200 | 25.000 → 25.000 | +0.000 |
| 57 | DIN_mated_pair | AGND | DIN:middle:b8 → DIN:rear:b8 | 19.200 → 19.200 | 25.000 → 25.000 | +0.000 |
| 58 | middle_copper | /A01/REF5 | A01:J-SIG:middle:1 → DIN:middle:c1 | 121.853 → 50.644 | 159.157 → 68.606 | -90.551 |
| 59 | middle_copper | /A01/REFN5 | A01:J-SIG:middle:3 → DIN:middle:c2 | 120.118 → 54.197 | 157.427 → 72.718 | -84.709 |
| 60 | middle_copper | /A01/IN_BUFFER | A01:J-SIG:middle:4 → DIN:middle:c3 | 118.072 → 56.943 | 155.101 → 76.234 | -78.867 |
| 61 | middle_copper | /A01/OFFSET_BUFFER | A01:J-SIG:middle:5 → DIN:middle:c4 | 116.059 → 59.696 | 152.775 → 79.750 | -73.025 |
| 62 | middle_copper | /A01/SUM_NEG | A01:J-SIG:middle:6 → DIN:middle:c5 | 114.081 → 62.457 | 150.450 → 83.267 | -67.183 |
| 63 | middle_copper | /A01/REF5 | A01:C-SIG:middle:1 → DIN:middle:c1 | 50.493 → 102.096 | 70.399 → 134.876 | +64.477 |
| 64 | middle_copper | /A01/REFN5 | A01:C-SIG:middle:2 → DIN:middle:c2 | 52.296 → 100.503 | 73.046 → 132.550 | +59.504 |
| 65 | middle_copper | /A01/IN_REMOTE | A01:C-SIG:middle:3 → DIN:middle:c6 | 56.866 → 92.562 | 79.323 → 121.462 | +42.138 |
| 66 | middle_copper | /A01/Cc045d2_W | A01:C-SIG:middle:4 → DIN:middle:c7 | 59.075 → 91.191 | 81.971 → 119.136 | +37.165 |
| 67 | middle_copper | /A01/C38cac0_W | A01:C-SIG:middle:5 → DIN:middle:c8 | 61.335 → 89.889 | 84.618 → 116.811 | +32.193 |
| 74 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b1 | 118.734 → 42.595 | 152.090 → 61.539 | -90.551 |
| 75 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b2 | 116.224 → 44.912 | 149.169 → 64.460 | -84.709 |
| 76 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b3 | 113.715 → 47.251 | 146.248 → 67.381 | -78.867 |
| 77 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b4 | 111.208 → 49.610 | 143.327 → 70.302 | -73.025 |
| 78 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b5 | 108.702 → 51.986 | 140.406 → 73.223 | -67.183 |
| 79 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b6 | 106.197 → 54.377 | 137.485 → 76.144 | -61.341 |
| 80 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b7 | 103.695 → 56.781 | 134.564 → 79.065 | -55.499 |
| 81 | middle_AGND_copper | AGND | A01:J-PWR:middle:4 → DIN:middle:b8 | 101.194 → 59.196 | 131.643 → 81.986 | -49.657 |
| 255 | local_transport_branch | /A01/C38cac0_W | R7119:1 → DIN:rear:c8 | 35.959 → 59.120 | 51.529 → 79.764 | +28.235 |
| 271 | local_transport_branch | /A01/Cc045d2_W | R7115:1 → DIN:rear:c7 | 31.985 → 61.038 | 46.910 → 83.654 | +36.744 |
| 274 | local_transport_branch | /A01/IN_BUFFER | R7117:1 → DIN:rear:c3 | 42.389 → 69.138 | 61.102 → 92.319 | +31.217 |
| 276 | local_transport_branch | /A01/IN_REMOTE | R7113:2 → DIN:rear:c6 | 53.660 → 13.629 | 74.720 → 24.755 | -49.964 |
| 280 | local_transport_branch | /A01/OFFSET_BUFFER | RN7101:3 → DIN:rear:c4 | 41.471 → 72.783 | 57.783 → 97.174 | +39.391 |
| 281 | local_transport_branch | /A01/REF5 | U7104:1 → DIN:rear:c1 | 68.416 → 22.701 | 93.152 → 36.142 | -57.010 |
| 285 | local_transport_branch | /A01/REFN5 | U7104:7 → DIN:rear:c2 | 62.245 → 23.502 | 85.746 → 36.789 | -48.956 |
| 287 | local_transport_branch | /A01/SUM_NEG | U7105:8 → DIN:rear:c5 | 35.909 → 63.015 | 52.203 → 85.410 | +33.207 |
| 310 | local_return_join | AGND | A01:K-PWR:local:3 → DIN:rear:b1 | 48.641 → 100.019 | 67.862 → 132.396 | +64.534 |
| 311 | local_return_join | AGND | A01:K-PWR:local:3 → DIN:rear:b2 | 49.181 → 97.795 | 69.071 → 129.475 | +60.404 |
| 312 | local_return_join | AGND | A01:K-PWR:local:3 → DIN:rear:b3 | 49.845 → 95.587 | 70.281 → 126.554 | +56.273 |
| 313 | local_return_join | AGND | A01:K-PWR:local:3 → DIN:rear:b4 | 50.628 → 93.395 | 71.491 → 123.633 | +52.142 |
| 314 | local_return_join | AGND | A01:K-PWR:local:3 → DIN:rear:b5 | 51.524 → 91.222 | 72.701 → 120.712 | +48.011 |
| 315 | local_return_join | AGND | A01:K-PWR:local:3 → DIN:rear:b6 | 52.528 → 89.068 | 73.911 → 117.791 | +43.880 |
| 316 | local_return_join | AGND | A01:K-PWR:local:3 → DIN:rear:b7 | 53.633 → 86.935 | 75.121 → 114.870 | +39.749 |
| 317 | local_return_join | AGND | A01:K-PWR:local:3 → DIN:rear:b8 | 54.834 → 84.825 | 76.331 → 111.949 | +35.618 |

## Signal path allocations that include a changed edge

| Net | From → To | S10 mm | Design mm | Δ mm | Wire cut max mm |
|---|---|---|---|---|---|
| /A01/REF5 | U7104:1 → RV1308:3 | 299.001 | 306.468 | +7.467 | 78 |
| /A01/REF5 | U7104:1 → U7107:3 | 437.373 | 289.811 | -147.561 | 93 |
| /A01/REFN5 | U7104:7 → RV1308:1 | 291.440 | 301.987 | +10.548 | 78 |
| /A01/REFN5 | U7104:7 → U7108:2 | 442.708 | 309.042 | -133.665 | 93 |
| /A01/IN_BUFFER | U7106:1 → R7117:1 | 398.957 | 351.307 | -47.650 | 93 |
| /A01/IN_BUFFER | U7106:1 → U7104:12 | 467.579 | 419.929 | -47.650 | 93 |
| /A01/OFFSET_BUFFER | U7106:7 → RN7101:3 | 388.232 | 354.598 | -33.634 | 93 |
| /A01/SUM_NEG | U7105:8 → RN7102:1 | 370.882 | 336.906 | -33.976 | 93 |
| /A01/IN_REMOTE | R7113:2 → RV1307:3 | 303.982 | 296.156 | -7.826 | 78 |
| /A01/Cc045d2_W | RV1307:2 → R7115:1 | 277.628 | 351.538 | +73.910 | 78 |
| /A01/C38cac0_W | RV1308:2 → R7119:1 | 269.390 | 329.818 | +60.427 | 78 |

Power/return endpoint paths and local endpoint paths contain no DIN-incident copper edge, so they are unchanged. Stage15 lists one explicit path per power endpoint; the 16 changed AGND joins to the DIN b contacts (middle and core) are parallel return branches that no listed path uses.

## Historical files that still carry Stage10 DIN allocations (unchanged bytes)

- `design/architecture-278/implementation/stage10/interfaces-report.json` (33 Stage10 allocation values found by text match)
- `design/architecture-278/implementation/stage14/interfaces-report.json` (33 Stage10 allocation values found by text match)
- `design/architecture-278/implementation/stage15/interfaces-report.json` (34 Stage10 allocation values found by text match)
- `design/architecture-278/implementation/stage15/rebudget-report.json` (1 Stage10 allocation values found by text match)
- `design/architecture-278/implementation/stage16/inputs-report.json` (34 Stage10 allocation values found by text match)
- `design/architecture-278/implementation/stage17/generated/transport-source.json` (34 Stage10 allocation values found by text match)
