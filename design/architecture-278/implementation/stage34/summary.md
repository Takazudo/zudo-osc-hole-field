# Stage34 whole-arch retention and wire/current evidence (generated)

Design study only. Calculations on planning geometry and stated inputs; nothing is measured, and a clear envelope is not physical non-interference.

## Result

R33 + RG34: **CONDITIONAL_PENDING_REGISTRATION_AND_MEASUREMENT**. RG34 bounds the whole arch under the stated assumptions (BOUNDED_WITHIN_STATED_ASSUMPTIONS); inter-carrier registration, the mock-up measurements and the wire stay open. Nothing is adopted.

| Criterion | Result |
|---|---|
| T1_captive_closed_parts | yes |
| T2_single_end_states_inside_RG34 | yes |
| T3_parts_clear_K4 | yes |
| T4_walls_between_cables | yes |
| T5_free_spans_bounded_and_clear | yes |
| T6_rear_cover | yes |
| T7_grip_fan_in_and_s_bend | yes |
| T8_strength_planning_load | yes |
| T9_slack_follows_without_buckling | yes |
| T10_both_ends_withdrawal_blocked | yes |
| T11_access_columns_clear | yes |

Stage33 ideal-plane criteria re-run: CONDITIONAL_PENDING_RETENTION (failed: S3_lateral_retention); RG34 replaces the missing lateral retention.

## Results by class

| Result | Class |
|---|---|
| R33 ideal-plane criteria S1-S12 (Stage33 re-run; S3 lateral retention still fails without RG34) | CONDITIONAL |
| RG34 escape: closed lids and sleeves, closure gap below half the smallest OD | FEASIBLE_WITHIN_STATED_ASSUMPTIONS |
| RG34 out-of-plane and rotation bound inside the channel (guide play) | FEASIBLE_WITHIN_STATED_ASSUMPTIONS |
| Free spans exit-to-sleeve with all slack (inextensible cable, cut tolerance, bow, registration allowance) | FEASIBLE_WITHIN_STATED_ASSUMPTIONS |
| J-PWR to core: channel wall on the rear carrier (inter-carrier registration out of this chain) | FEASIBLE_WITHIN_STATED_ASSUMPTIONS |
| J-SIG / J-PWR shared gap: walls between the channels and free-span pairs | FEASIBLE_WITHIN_STATED_ASSUMPTIONS |
| Every single-end 2.45-15 mm withdrawal at constant length inside RG34 (fan-in and grip below the block) | FEASIBLE_WITHIN_STATED_ASSUMPTIONS |
| Both ends of one cable withdrawn with RG34 closed | INFEASIBLE |
| Inter-carrier registration within the 1.0 mm requirement | UNKNOWN |
| RG34 strength (post bending at the planning load; joints not evaluated) | CONDITIONAL |
| Sliding friction vs free-span buckling | CONDITIONAL |
| Abrasion over repeated withdrawals | UNKNOWN |
| Finger/tool operability with one sleeve removed | UNKNOWN |
| RG34 outside the reserved RV-ARCH/RV-ACCESS volumes (proposal) | CONDITIONAL |
| Local-leg guide alone as whole-arch retention (negative control) | INFEASIBLE |
| RG34 without its former (negative control) | INFEASIBLE |
| R12 route radius vs 10x OD, inner-surface convention (Stage33) | FEASIBLE_WITHIN_STATED_ASSUMPTIONS |
| R17 / 15x OD with RG34 (cap over the raised arch above the rear cover) | INFEASIBLE |
| R17 / 15x OD geometry without retention (Stage33 scan, preserved) | CONDITIONAL |
| 20x OD radius (Stage33 rear-cover failure, preserved) | INFEASIBLE |
| J-SIG conductor currents (budgeted; conditional maxima, no established maximum) | CONDITIONAL |
| J-PWR conductor currents (A01 budget; conditional maxima, no established maximum) | CONDITIONAL |
| Fault/short current on any conductor (no upstream limiting element) | UNKNOWN |
| Stage33 J-PWR current inputs as an A01 basis (Stage8 X1 values) | INFEASIBLE |
| AWG28/AWG30 GH contact current (no JST rating; not a demonstrated failure) | UNKNOWN |
| Wire selection | UNKNOWN |
| F33 front-face large radius (Stage33, preserved) | UNKNOWN |
| B32 5 mm bends with every identified wire (Stage32/33, preserved) | INFEASIBLE |
| B32 uniform 1.282 mm bow (Stage32, preserved) | INFEASIBLE |

## RG34 geometry

One slot channel per arch, on the rear carrier (post on crossmember:rear:0). Coordinates in each arch plane: s along the arch from the local exit, n out of plane, z.

| Cable | Play c (mm) | Wall (mm) | Free span: exit → sleeve bottom z (local / middle) | Sleeve to block entry z | Former top (set range) | Cap / top z | Slack with set former / fixed former (mm) |
|---|---|---|---|---|---|---|---|
| J-SIG | 0.30 | 1.20 | 43.90 → 59.98 / 57.30 → 73.38 | 77.29 / 90.69 | 89.72–90.86 | 102.16 / 103.36 | 0.50 / 2.28 |
| J-PWR | 0.30 | 1.20 | 43.90 → 56.43 / 57.30 → 69.83 | 73.81 / 87.21 | 86.60–87.74 | 98.45 / 99.65 | 0.50 / 2.28 |

- Each sleeve bottom leaves the fan-in plus an S-bend length (5.69 / 5.62 mm) for a carrier registration error of 1.00 mm at the maker radius (11.75 / 11.46 mm).
- Each block entry sits the 15 mm travel + fan-in + 8.00 mm grip above its exit, so a withdrawn housing's fan-in and the gripping fingers stay below RG34.
- The middle sleeves contain the lower part of bend 2 (5.77 mm in-plane offset); their inner face follows the former arc.
- Outer gap between the J-SIG and J-PWR channels 0.85 mm (bridged by the channel joint); interior hulls 3.40 mm apart in plan, enough for both walls.
- Closure gap ≤ 0.20 mm, below half of the smallest wire OD 0.76 mm: no conductor can enter or pass a parting line.

## Movement budget

Inside RG34 every point of a cable stays within the play c of its plane (walls), above the former and below the cap; rotation of the arch is bounded by the same walls. Between each housing exit and its sleeve the cable is free; the bound is the spheroid of every point a span of its length + all the slack can reach (inextensible cable), inflated by c + registration + RG34 tolerances + bundle radius.

| Cable | Span | Chord (mm) | Length with slack (mm) | Reach (semi-minor, mm) | Inflation (mm) | Tightest against | Robust spare (mm) |
|---|---|---|---|---|---|---|---|
| J-SIG | local | 16.08 | 16.58 | 2.02 | 3.25 | foreign-depth:RV1201 | 0.99 |
| J-SIG | middle | 16.08 | 16.58 | 2.10 | 3.25 | board:A01-middle:0 | 0.54 |
| J-PWR | local | 12.53 | 13.03 | 1.79 | 2.96 | board:A01-middle:0 | 0.49 |
| J-PWR | middle | 12.53 | 13.03 | 1.87 | 2.96 | board:A01-middle:0 | 0.83 |

During a single-end withdrawal the arch top floats above the former, so up to J-SIG 15.00 mm of slack (opposite free span reach 13.30 mm); J-PWR 15.00 mm of slack (opposite free span reach 12.26 mm) is held only by the operator: NOT bounded.

## Clearances of RG34

| Part | Nearest | Distance (mm) | Across carriers | Stack (mm) | Robust spare (mm) | K4 |
|---|---|---|---|---|---|---|
| RG34-J-PWR-channel-top | core-envelope-40mm | 1.37 | no (rear carrier) | 0.57 | 0.29 | yes |
| RG34-post | board:A01-core | 1.50 | no (rear carrier) | 0.57 | 0.42 | yes |
| RG34-J-PWR-sleeve-local | release:A01:J-SIG:local | 3.87 | yes | 1.48 | 1.89 | yes |
| RG34-J-SIG-channel-middle | tool:A01-middle:M1 | 4.52 | yes | 1.48 | 2.54 | yes |
| RG34-J-SIG-sleeve-middle | tool:A01-middle:M1 | 4.52 | yes | 1.48 | 2.54 | yes |
| RG34-J-SIG-channel-top | tool:A01-middle:M1 | 4.57 | yes | 1.48 | 2.59 | yes |
| RG34-J-SIG-sleeve-local | release:A01:J-PWR:local | 5.25 | yes | 1.48 | 3.27 | yes |
| RG34-J-PWR-channel-local-leg | core-envelope-40mm | 6.22 | no (rear carrier) | 0.57 | 5.14 | yes |
| RG34-J-PWR-channel-top | tool:A01-jack:M4 (service only) | 1.63 | yes | 1.48 | -0.34 | **no**: front jack board removal only; RG34 is removed first |
| RG34-post | tool:A01-jack:M4 (service only) | 2.50 | yes | 1.48 | 0.53 | yes: front jack board removal only; RG34 is removed first |

Rear cover: J-SIG RG34 top z 103.36 + 0.5 margin + 1.0 registration ≤ 105.0 (spare 0.14); J-PWR RG34 top z 99.65 + 0.5 margin + 1.0 registration ≤ 105.0 (spare 3.85).

## States inside RG34 (constant design length)

| Cable | State | Travel (mm) | Top centreline z | Inside RG34 | Blocked by |
|---|---|---|---|---|---|
| J-SIG | installed | 0 | 92.36 | yes | – |
| J-SIG | local | 7.5 | 96.11 | yes | – |
| J-SIG | local | 15 | 99.86 | yes | – |
| J-SIG | middle | 7.5 | 96.11 | yes | – |
| J-SIG | middle | 15 | 99.86 | yes | – |
| J-SIG | both | 15 | 107.36 | **no** | cap |
| J-PWR | installed | 0 | 88.95 | yes | – |
| J-PWR | local | 7.5 | 92.70 | yes | – |
| J-PWR | local | 15 | 96.45 | yes | – |
| J-PWR | middle | 7.5 | 92.70 | yes | – |
| J-PWR | middle | 15 | 96.45 | yes | – |
| J-PWR | both | 15 | 103.95 | **no** | cap |

## Negative controls

| Cable | Control | Bound (mm) | Allowance (mm) | Bounded |
|---|---|---|---|---|
| J-SIG | guide on the local leg only: reach of the rest of the arch / bucket-handle radius | 49.62 / 28.23 | 3.36 | **no** |
| J-SIG | RG34 without the former: local free span reach grows by | 17.34 | 0.99 | **no** |
| J-PWR | guide on the local leg only: reach of the rest of the arch / bucket-handle radius | 55.06 / 28.26 | 1.89 | **no** |
| J-PWR | RG34 without the former: local free span reach grows by | 16.42 | 0.49 | **no** |

Both ends of one cable withdrawn with the lid closed: blocked by the cap in every case (procedure: one end at a time).

## Strength, friction, access

- Post 6 × 5 mm, lever 67.92 mm to the farthest RG34 point: allowable 58.89 N; 5 N meets, 10 N meets, 20 N meets, 50 N meets. Not covered: post-to-crossmember fastening and the crossmember:rear:0 / rail:rear:0 joint; channel walls, lids and sleeves under a load; the J-SIG to J-PWR channel joint; fatigue, vibration, impact.
- Drag upper bound J-SIG 12.6 mN, J-PWR 8.0 mN against free-span buckling ≥ 1.82 N (strands-only Alpha Wire 1851); stiffness is not used for any bound. Abrasion NOT calculated (M34-04).
- With one sleeve removed, the housing column up to the block entry is clear of rigid parts: A01:J-SIG:local 33.39 mm, grip zone z 54.29–62.29; A01:J-SIG:middle 33.39 mm, grip zone z 67.69–75.69; A01:J-PWR:local 29.91 mm, grip zone z 50.81–58.81; A01:J-PWR:middle 29.91 mm, grip zone z 64.21–72.21. Finger operation NOT DETERMINED.

## Reserved volumes

- J-SIG: RG34 half-thickness 3.25 mm vs RV-ARCH 2.35 mm (protrudes 0.90 mm); occupies RV-ACCESS-J-SIG-local, RV-ACCESS-J-SIG-middle above the grip zones. PROPOSAL_REQUIRES_OWNER_DECISION.
- J-PWR: RG34 half-thickness 2.96 mm vs RV-ARCH 2.06 mm (protrudes 0.90 mm); occupies RV-ACCESS-J-PWR-local, RV-ACCESS-J-PWR-middle above the grip zones. PROPOSAL_REQUIRES_OWNER_DECISION.

R17 sensitivity: RG34 needs z 110.01 / 106.30 (J-SIG / J-PWR) against the cover at 105: does not fit. The Stage33 R17 geometry without retention stays CONDITIONAL and 20× stays INFEASIBLE.

## Current ledger (A01; replaces the Stage33 X1-derived J-PWR inputs)

Classes: typical / conditional maximum (stated conditions) / established maximum (maker-backed limit). No conductor has an established maximum.

| Cable | Pin | Net | Typical (mA) | Conditional max (mA) | Fault case (mA) | Established | Of 0.5 A project limit |
|---|---|---|---|---|---|---|---|
| J-SIG | 1 | /A01/REF5 | 3.5e-06 | 5e-05 | – | UNKNOWN | 0.00 % |
| J-SIG | 2 | AGND | 3.7 | 12.3 | 36.3 | UNKNOWN | 7.26 % |
| J-SIG | 3 | /A01/REFN5 | 3.5e-06 | 5e-05 | – | UNKNOWN | 0.00 % |
| J-SIG | 4 | /A01/IN_BUFFER | 0.05 | 0.1249 | – | UNKNOWN | 0.03 % |
| J-SIG | 5 | /A01/OFFSET_BUFFER | 0.05 | 0.1349 | – | UNKNOWN | 0.03 % |
| J-SIG | 6 | /A01/SUM_NEG | 0.05 | 0.1349 | – | UNKNOWN | 0.03 % |
| J-SIG | 7 | AGND | 3.7 | 12.3 | 36.3 | UNKNOWN | 7.26 % |
| J-PWR | 1 | +12V | 6.36 | 18.35 | 43 | UNKNOWN | 8.60 % |
| J-PWR | 2 | -12V | 5.56 | 17.15 | 42 | UNKNOWN | 8.40 % |
| J-PWR | 3 | +5V | 0.099 | 0.104 | – | UNKNOWN | 0.02 % |
| J-PWR | 4 | AGND | 3.7 | 12.3 | 36.3 | UNKNOWN | 7.26 % |

Stage33 used +12V 12.87 / -12V 11.67 / +5V 0.099 mA and an AGND bound of 24.64 mA. Stage8 studies X1 (R-STAGE8-SCOPE: A01 implementation forbidden); its J_plus12/J_minus12 values are X1 jack-board currents, so Stage33 mislabelled them as A01-jack. The AGND bound summed rail-to-rail currents and put all return on J-PWR pin 4. Stage33 bytes stay unchanged as history.

Fault: no fuse, PTC, series element or regulator limit exists upstream (R-POWER-SPEC); a short on a J-PWR or AGND conductor is limited only by an unselected source (requirement 2.1 A), above the JST 1.0 A rating: UNKNOWN.

## Wire ledger

Selection: NULL: no identified wire meets every check; the closest leave only UNKNOWN items.

| Wire | AWG | OD (mm) | Fails | Unknown (J-PWR) |
|---|---|---|---|---|
| Alpha Wire 1852 | 28 | 0.8382–0.9398 | none | contact_rating, temperature_rise, derating_to_project_limit, service_flex |
| Alpha Wire 1853 | 26 | 0.9398–1.0414 | bend_installed_R12, od_window_full_tolerance | service_flex |
| Alpha Wire 2843/7 | 26 | 0.7366–0.8382 | od_window_full_tolerance, tin_plated_stranded | service_flex |
| Alpha Wire 422607 | 26 | 0.9398–1.0414 | bend_installed_R12, od_window_full_tolerance, temperature | service_flex |
| Alpha Wire 782607 | 26 | 2.0066–2.2098 | bend_installed_R12, od_window_full_tolerance | service_flex |
| Alpha Wire 6710 | 28 | 0.8128–0.9144 | none | contact_rating, temperature_rise, derating_to_project_limit, service_flex |
| Alpha Wire 1851 | 30 | 0.762–0.8636 | none | contact_rating, temperature_rise, derating_to_project_limit, service_flex |
| Alpha Wire 6711 | 26 | 0.9144–1.016 | od_window_full_tolerance | service_flex |
| Thermax M22759/18-26 (26-AMCFZ-1938) | 26 | 0.762–0.8636 | none | bend_installed_R12, service_flex |

- contact_rating: JST 1.0 A at AWG #26 only (S-JST-EGH); not transferred to AWG #28/#30
- temperature_rise: JST range -40 to +105 C includes temperature rise at the rated current (AWG #26)
- derating: project limit 0.5 A per contact (R-STAGE10-CONTACT-LIMIT), half the JST AWG #26 rating
- conductor_ampacity: generic chart only (S-REMINGTON-AMPACITY, not a candidate maker); shown, not used as a check
- service_flex: no candidate maker states a repeated-flex radius; RG34 also slides the cable through its guides at each withdrawal
- crimp_process: JST applicator and crimp height for every wire: NOT RUN (process item)

Smallest questions or measurements:

1. Amphenol CIT / Thermax: minimum bend radius (installation and repeated flexing) for M22759/18-26 and confirmation that the .030-.034 in OD range is current
2. JST: SSHL-002T-P0.2 current rating or temperature-rise curve with AWG #28 and #30, and any insulation restriction for mPPE, PVC or ETFE
3. Measurement: OD of an M22759/18-26 sample against the 0.76 mm floor (stated minimum 0.762 mm leaves 0.002 mm)
4. Measurement: unpowered repeated-withdrawal flex and abrasion test of the chosen wire at R12 through RG34 (M34-04)

## Two-sided assembly and re-routing (implications only)

- **A01-middle**: gains GH header pads on its rear face: a second SMT side (or hand soldering) with its own stencil, placement and reflow pass; the GH headers would ride the second reflow on the first-side parts or the reverse order; process, fixture and cost UNCONFIRMED
- **copper**: nets and pin identities unchanged; the pads move to the rear face (largest move A01:J-PWR:middle 14.4 mm, A01:J-SIG:middle 21.3 mm); each net needs a via or a rear-side route to the new pads; routed copper is null in the draft and KiCad regeneration is NOT RUN
- **courtyard**: rear-face courtyards must clear the rear-side obstacles (header sweeps already clear the DIN body and the mounts in Stage33); DRC NOT RUN
- **carriers**: RG34 adds a post and fastening on crossmember:rear:0 (rear carrier change, proposal); the enclosure cleats must hold the inter-carrier registration within the allowance

## Assumptions

- the cable is inextensible and stays within its bundle envelope (JST maximum OD + 0.25 mm dressing)
- cut length within +/- 0.5 mm of the design length
- A01-middle bow up to the uniform 1.282 mm case
- inter-carrier registration within 1 mm (requirement)
- RG34 profile and mounting tolerances 0.1 / 0.1 mm
- lids and sleeves closed on their stops; only one end of a cable withdrawn at a time

## Unresolved degrees of freedom

- actual inter-carrier registration (enclosure cleats undesigned)
- arch shape during service while a sleeve is removed (operator-held, not bounded)
- actual free-span excursion under handling (bound computed, not measured)
- cable length after crimping
- abrasion and drag over repeated withdrawals
- finger access with one sleeve removed

**RG34 assembly**

1. Fit carriers, boards and the core as in Stage10; fit the RG34 post on crossmember:rear:0 (proposal).
2. From the rear (cover off): mate J-PWR at both ends, dress it into one arch and lay it into the J-PWR channel; set the J-PWR former (lower it, raise it until the top leg rests on it, gap <= former_setting_resolution_mm, lock it); close the J-PWR lid and both J-PWR sleeves.
3. Mate J-SIG at both ends, fit the J-SIG channel to the J-PWR channel, lay J-SIG in, set its former the same way, close its lid and both sleeves.
4. Check that each lid and sleeve sits on its stop (closure gap <= guide_closure_gap_max_mm) with no conductor in a parting line; refit the rear cover.

**Connector service (one end at a time)**

1. Power off; remove the rear cover. The core may stay installed.
2. Open and remove only the sleeve of the end to be serviced; the channel, its lid and the other sleeve stay closed.
3. Press the latch, hold the bundle in the grip zone above the fan-in and pull within 15 degrees of +z; the cable slides through the channel and the opposite sleeve and the arch rises inside the channel (cap above the single-end raised top).
4. Re-mate along -z, pulling the arch back down onto the former; refit the sleeve and check its stop.
5. Never withdraw both ends of one cable with the lid closed: the raised arch would hit the cap (blocked by design). For harness replacement open the lid and both sleeves first.

**Core service (unchanged order)**

1. Power off; remove the rear cover.
2. Disconnect K-PWR, release the four core screws and withdraw the core 40 mm along +z. RG34 and both arches stay in place; the J-PWR channel wall, not the cable, faces the core volume.

**Harness replacement**

1. Power off; remove the rear cover; open both lids and all four sleeves.
2. Unmate the middle ends, then the local ends, from the rear; lift each cable out of its channel. No board, carrier or the core is removed.
3. Fit the new harness as in RG34 assembly, setting both formers again.

**Front jack board removal**

1. Power off; remove the rear cover; open both lids and all four sleeves; unmate both middle ends and lift both cables out of their channels.
2. Remove RG34 (J-SIG channel from the J-PWR channel, then the J-PWR channel and post from crossmember:rear:0): the A01-jack M3/M4 screwdriver columns are used only with RG34 removed (the J-PWR channel is within K4 of the M4 column).
3. Lift each free middle end back over the A01-middle edge to x < 232 and remove the front panel assembly as in Stage10 with the cables attached to A01-jack.

## Measurements still NOT RUN (minimal unpowered mock-up plan)

- **M34-01** Unpowered mock-up of R33 + RG34 (printed or machined channels on a carrier dummy): both arches at the design lengths, lids and sleeves closed; lateral position at the bend apexes and free spans in six enclosure orientations, before and after a defined handling push.
- **M34-02** Free-span excursion on the mock-up: largest lateral displacement of each exit-to-sleeve span with the arch top pushed onto the former (all slack driven into one span), against the computed spheroid semi-minor axes.
- **M34-03** Cut length after crimping of each harness (M-09) against +/- cut_length_tolerance_mm, and the arch top gap to the former when installed.
- **M34-04** Repeated single-end 15 mm withdrawals through RG34: pull and push force, sliding drag, insulation abrasion at the sleeve and channel entries, fan-in shape after cycling (M-12).
- **M34-05** RG34 post, joint and wall stiffness/strength under a hand load; post fastening to crossmember:rear:0.
- **M34-06** Inter-carrier registration between the rear carrier and the jack/middle carriers on the enclosure cleats, against registration_allowance_mm.
- **M34-07** Latch press and bundle grip at each housing with only that sleeve removed (finger or tool), and lid/sleeve refit with no conductor in a parting line.
- **M34-08** Selected wire: OD sample, maker bend radius (installation and repeated flexing), JST contact rating at its gauge (M33-01 carried forward).
