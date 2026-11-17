# MC02 analog-function remedy preparation brief

Task `MC02-R-ANALOG16`, preparation attempt `20261117-source-1`. **PREPARATION ONLY; geometry/hardware execution NOT ADMITTED.**

Engineering source `2c53715d49a4a7639723595590d1fd4eeb3a3c1f`; prepared in an isolated worktree from `9cf26f4f81e3e5ed31756c3fbb2b73f84e26fb7b`. This covers exactly the 16 unplaced OPA4196IDR packages. U1518 and U4341 have separate precision briefs; the eight logic packages are outside this document. All listed ICs remain unplaced.

## Source extraction and proposed review boundary

`replacement.footprints` determines the unplaced set and board; `physical_packages` supplies exact retained project MPN/instance and declared `decouples_ref`; `package_units` supplies unit roles and pin-net anchors. All project assignments are source facts, not new sourcing qualification. Signal anchors below omit only +12V, −12V, +5V and AGND; supply pin 4=+12V and pin 11=−12V and complete units 1–5 remain obligations.

The companion column lists same-instance passive/diode references sharing at least one printed IC signal net, plus separately listed declared decouplers. This is a reproducible one-hop review boundary, not a complete stability model or an approved relocation set. It deliberately does not traverse rails or repeatedly expand the connected graph. Fixed panel endpoints and other active packages may lie beyond the boundary and must not be moved by inference. Blank MPNs in companions remain unresolved.

## Complete 16-package inventory

| Board | Ref | Instance / source family | Source unit roles | Declared decouplers | Same-instance passive/diode signal neighbours |
| --- | --- | --- | --- | --- | --- |
| JL | `U1216` | O2 / oscillator | 1: high_impedance_input:A; 2: high_impedance_input:A; 3: high_impedance_input:A; 4: general_output:A | C1250 C1251 | DO1202 DO1203 DO1204 R1208 R1212 R1216 R1221 R1227 R1256 RB1201 RB1202 |
| K | `U1415` | O4 / oscillator_tssop | 1: oscillator:SINE_DIFF; 2: oscillator:SINE_GAIN; 3: oscillator:unused grounded follower; 4: oscillator:unused grounded follower | C1448 C1449 | R1495 R1496 R1497 R1498 R1499 RB1401 RVO1411 |
| JL | `U1416` | O4 / oscillator_tssop | 1: high_impedance_input:A; 2: high_impedance_input:A; 3: high_impedance_input:A; 4: general_output:A | C1450 C1451 | DO1402 DO1403 DO1404 R1408 R1412 R1416 R1421 R1427 R1456 RB1401 RB1402 |
| JL | `U1417` | O4 / oscillator_tssop | 1: general_output:A; 2: general_output:A; 3: general_output:A; 4: oscillator:unused grounded follower | C1452 C1453 | R1477 R1481 R1487 R1489 RB1404 RB1406 RB1408 |
| JL | `U2119` | F1 / filter | 1: magnitude_indicator:A; 2: magnitude_indicator:A; 3: magnitude_indicator:A; 4: magnitude_indicator:A | C2151 C2152 | D2125 D2126 D2127 D2128 D2130 D2131 D2132 D2133 D2135 D2136 D2137 D2138 D2140 D2141 D2142 D2143 R2125 R2133 R2141 R2156 R2174 RB2114 RB2115 RB2116 RB2117 |
| JL | `U2218` | F2 / filter | 1: general_output:A; 2: general_output:A; 3: general_output:A; 4: general_output:A | C2249 C2250 | R2258 R2259 R2261 R2262 R2266 R2270 RB2205 RB2206 RB2208 RB2210 RB2212 |
| JR | `U4346` | E3 / envelope_tssop_e3 | 1: high_impedance_input:A; 2: high_impedance_input:A; 3: high_impedance_input:A; 4: general_output:A | C4372 C4373 | D4301 D4302 D4303 R4308 R4312 R4316 R4317 R4352 R4369 R4385 R4387 R4399 RB4305 RB4316 RB4322 |
| JR | `U4347` | E3 / envelope_tssop_e3 | 1: general_output:A; 2: general_output:A; 3: general_output:A; 4: magnitude_indicator:A | C4374 C4375 | D4307 D4308 D4309 D4310 R4317 RB4303 RB4307 RB4309 RB4311 RB4313 |
| JR | `U4348` | E3 / envelope_tssop_e3 | 1: magnitude_indicator:A; 2: magnitude_indicator:A; 3: envelope:unused grounded follower; 4: envelope:unused grounded follower | C4376 C4377 | D4312 D4313 D4314 D4315 D4317 D4318 D4319 D4320 R4352 R4369 RB4314 RB4315 |
| K | `U5110` | W2 / wavefolder | 1: wavefolder:F1; 2: wavefolder:F2; 3: wavefolder:F3; 4: wavefolder:F4 | C5136 C5137 | D5106 D5107 D5108 D5109 D5110 D5111 D5112 D5113 R5152 R5153 R5154 R5155 R5156 R5157 R5158 R5159 R5160 R5161 R5162 R5163 |
| K | `U5209` | W1 / wavefolder_tssop | 1: wavefolder:CURRENT_SERVO; 2: wavefolder:PRE_GAIN; 3: wavefolder:DRIVE_SUM; 4: wavefolder:DRIVE_INVERT | C5234 C5235 | C5207 D5205 R5236 R5237 R5238 R5245 R5246 R5247 R5248 R5249 R5250 R5251 R5252 R5253 RV5205 |
| K | `U5210` | W1 / wavefolder_tssop | 1: wavefolder:F1; 2: wavefolder:F2; 3: wavefolder:F3; 4: wavefolder:F4 | C5236 C5237 | D5206 D5207 D5208 D5209 D5210 D5211 D5212 D5213 R5252 R5253 R5254 R5255 R5256 R5257 R5258 R5259 R5260 R5261 R5262 R5263 |
| JR | `U8314` | M4A / mix4_vca | 1: high_impedance_input:A; 2: high_impedance_input:A; 3: high_impedance_input:A; 4: high_impedance_input:A | C8344 C8345 | D8308 D8309 D8310 D8311 R8308 R8313 R8318 R8323 R8328 R8333 R8338 R8343 |
| JR | `U8318` | M4A / mix4_vca | 1: magnitude_indicator:A; 2: magnitude_indicator:A; 3: magnitude_indicator:A; 4: magnitude_indicator:A | C8348 C8349 | C8308 C8310 D8323 D8324 D8325 D8326 D8327 D8328 D8329 D8330 D8331 D8332 D8333 D8334 D8335 D8336 D8337 D8338 R8334 R8344 R8347 R8348 R8358 R8380 R8385 R8386 R8387 R8388 |
| K | `U8409` | M4B / mix4_vca | 1: remote_buffer:A; 2: bipolar_attenuverter:A; 3: remote_buffer:A; 4: bipolar_attenuverter:A | C8434 C8435 | C8403 C8404 C8405 C8406 R8409 R8410 R8411 R8412 R8413 R8414 R8419 R8420 R8421 R8422 R8423 R8424 R8445 R8446 |
| JR | `U8417` | M4B / mix4_vca | 1: high_impedance_input:A; 2: general_output:A; 3: magnitude_indicator:A; 4: magnitude_indicator:A | C8446 C8447 | C8404 C8406 D8412 D8415 D8416 D8417 D8418 D8419 D8420 D8421 D8422 R8414 R8424 R8445 R8446 R8453 R8458 R8480 R8481 R8483 R8484 |

All 16 project MPNs are `OPA4196IDR`; all retain whole SOIC-14 packages. The table identifies 32 declared decouplers. Family counts: envelope_tssop_e3=3, filter=2, mix4_vca=4, oscillator=1, oscillator_tssop=3, wavefolder=1, wavefolder_tssop=2.

## Existing executable preservation constraints

- `test_oscillator.py::test_sine_pair_and_complete_amplifier_packages` checks complete amplifier units 1–5 and source sine-pair wiring; `test_primary_core_pin_identity_and_local_timing` protects the AS3340 timing-cap island, which is an external boundary rather than permission to move the core. Input protection and fixed panel binding tests remain applicable to O2/O4 interface functions.
- `test_filter.py::test_four_otas_and_local_integrator_nodes` preserves BP_INT/LP_INT core isolation and no panel sensitive-net contact; `test_G06_dry_gain_does_not_feed_filter_loop` preserves dry-path separation. U2119 indicators and U2218 outputs do not acquire permission to reroute the core because they are outside that core.
- `test_envelope.py::test_sensitive_storage_never_reaches_panel_or_lamps` preserves six-contact ENV_STORAGE isolation and prevents indicator/panel contact; `test_values_and_output_scaling` retains existing source arithmetic and values. U4346/47/48 must retain their input/output/indicator distinctions.
- `test_wavefolder.py::test_four_feed_forward_reflection_cells` explicitly binds each F1–F4 amplifier output/inverting/noninverting input to OUT/SUM/CLIP, the 10 kΩ clip-feed and 100 kΩ input/feedback values and oppositely oriented diode pair. `test_ac_storage_and_remote_controls` preserves sensitive AC storage off the panel. These are source topology constraints, not parasitic/stability margins for U5110/U5209/U5210.
- `test_mixers.py::test_mix4_cv_only_and_ota_termination` preserves protected input set, 50 kΩ summing feedback, CV-only control relationships, OTA termination and sensitive OTA_CURRENT. The source input/remote-buffer/output/indicator roles of U8314/U8318/U8417/U8409 must not be flattened into an undifferentiated courtyard move.
- These tests were inspected, not rerun by this documentation task. Their existence does not establish real PCB loading, noise, stability, thermal/current maxima or assembled access.

## Missing acceptance conditions and prepared next work

The proposed remedy is a source-bound comparison of function-boundary alternatives, not a position proposal. For each package, a later reviewer must identify stationary panel/protection/core endpoints, associated complete packages and feedback/return/decoupler obligations. Indicator roles alone are not evidence of electrical insensitivity. Shared external nets and neighbouring active functions require review beyond the one-hop passive list.

No allowable added trace length, via count, R/L/C, feedback phase margin, summed error/noise, output-load envelope, thermal margin or mounted service envelope is assigned here. Exact source-defined operating conditions and any quantitative requirement must be cited before a later geometry task. A nominal component value or ideal model pass cannot fill these missing physical budgets. DS-88 search radii are not expanded; DS-97 function-group review and DS-06 holds remain effective.

## Authority, execution boundary and recovery

Campaign `osc-stack-20261114`, parent #362/#365/#367; DS-88/DS-97/DS-133. The x0x WSL coordinator thread `01a1e7fb-e191-7382-8c35-5f76d36934fa` performs Moya's role. This author owns only this new document in branch `wsl/mc02-analog-brief-20261117`; the logic and precision briefs have separate owners. Original source files and fixed hardware are unchanged.

Allowed next work is source-only comparison/verification of this table and proposed review boundaries. Geometry, part/MPN adoption, search expansion, copper routing, native KiCad, DRC/fill, formal gate approval and manufacturing are excluded. The candidate-before-main sequencing proposal is pending and not presumed approved. Existing final-source and independent-design requirements still apply to later admission.

A future source-review job may be proposed with one isolated checkout, one CPU, 512 MiB memory, zero swap, 64 PIDs and setup60s/analysis480s/cleanup60s (600s total), no automatic retry or paid expansion. These are draft ceilings only: no launch, measured capacity or native admission is claimed. Dispatcher, exact command, final source binding and independent design reviewer remain pre-admission fields. Use the shared machine-wide guard for any later heavy transaction and actual per-run limits/cleanup; do not infer resource isolation from worktrees.

On changed bytes, ambiguous identity or contradictory role/net evidence, preserve the discrepancy and return it to the coordinator; do not retry unchanged or rewrite evidence to fit a desired group. No CAD checkpoint or background job is created by this brief. Runtime/model usage is unknown; any hard-design authority must be recorded from actual selection evidence rather than this text.

## Preparation acceptance and result

The exact set equals the 16 OPA4196IDR entries in the retained 26-unplaced set, all units and signal anchors match the pinned source, and all 32 declared decouplers reproduce. Association and proposed group boundaries remain separate. Pre/post `pnpm circuit:check` has manual-inventory scope; it is not a placement/physical acceptance result. Source fingerprints, generated table consistency and Markdown diff checks are recorded for this preparation. Native/model regeneration/placement/routing/DRC/fill: NOT RUN. No engineering input changed and unchanged aggregate evidence is not repeated. Independent review and final commit receipt remain with the coordinator.

## Immutable fingerprints

- `design/reports/io-partition.json`: SHA-256 `37a773282d723d7f689d1e6cf009e4edd1947827a5ee45f0051e42cd4e907a0b`.
- `design/stack/geometry/links/link-gate.json`: SHA-256 `1c091c1d6d4b9c000f770a0e604cb986d5c55e44cb77ea22083249afbf5cdb0d`.
- `design/spec/modules/test_oscillator.py`: SHA-256 `9a2794c664167da9d42e61af07d1220f771a5941440b49f9d06188671a9eb31f`.
- `design/spec/modules/test_filter.py`: SHA-256 `3176b25d2c14d1ea0173892b51f3c585d1104ea52b13f4deede3d778e3108b9c`.
- `design/spec/modules/test_envelope.py`: SHA-256 `f7fd81ad2902c32d0951c4c7f08ef7a963a3dfb5b54a0768fd38d5e3ab682dfb`.
- `design/spec/modules/test_wavefolder.py`: SHA-256 `dd5ae6ff42e804eba05a2a7a5f540c8c1fc155e41e20bce9397649f9d5ba7675`.
- `design/spec/modules/test_mixers.py`: SHA-256 `69dcfbd366c3883afa256b4e54d560cd2a7cebb5ad8b2b9103e107542218b74d`.

## Complete per-unit signal anchors

### U1216 — O2

- Unit 1 `high_impedance_input:A`: 1→`/O2/FM_BUFFER`, 2→`/O2/FM_BUFFER`, 3→`/O2/C3f1879_SENSE`.
- Unit 2 `high_impedance_input:A`: 7→`/O2/PWM_BUFFER`, 6→`/O2/PWM_BUFFER`, 5→`/O2/C1b3f1d_SENSE`.
- Unit 3 `high_impedance_input:A`: 8→`/O2/SYNC_BUFFER`, 9→`/O2/SYNC_BUFFER`, 10→`/O2/Cc44f2e_SENSE`.
- Unit 4 `general_output:A`: 14→`/O2/C70dbdb_DRIVE`, 13→`/O2/C70dbdb_DRIVE`, 12→`/O2/SIN_SCALED`.

### U1415 — O4

- Unit 1 `oscillator:SINE_DIFF`: 1→`/O4/SINE_DIFF`, 2→`/O4/SINE_MINUS`, 3→`/O4/SINE_PLUS`.
- Unit 2 `oscillator:SINE_GAIN`: 7→`/O4/SIN_SCALED`, 6→`/O4/SINE_GAIN_SUM`.
- Unit 3 `oscillator:unused grounded follower`: 8→`/O4/PACK_OPA4196IDR_3_IO_UNUSED3`, 9→`/O4/PACK_OPA4196IDR_3_IO_UNUSED3`.
- Unit 4 `oscillator:unused grounded follower`: 14→`/O4/PACK_OPA4196IDR_3_IO_UNUSED4`, 13→`/O4/PACK_OPA4196IDR_3_IO_UNUSED4`.

### U1416 — O4

- Unit 1 `high_impedance_input:A`: 1→`/O4/FM_BUFFER`, 2→`/O4/FM_BUFFER`, 3→`/O4/C3f1879_SENSE`.
- Unit 2 `high_impedance_input:A`: 7→`/O4/PWM_BUFFER`, 6→`/O4/PWM_BUFFER`, 5→`/O4/C1b3f1d_SENSE`.
- Unit 3 `high_impedance_input:A`: 8→`/O4/SYNC_BUFFER`, 9→`/O4/SYNC_BUFFER`, 10→`/O4/Cc44f2e_SENSE`.
- Unit 4 `general_output:A`: 14→`/O4/C70dbdb_DRIVE`, 13→`/O4/C70dbdb_DRIVE`, 12→`/O4/SIN_SCALED`.

### U1417 — O4

- Unit 1 `general_output:A`: 1→`/O4/Cc66d82_DRIVE`, 2→`/O4/Cc66d82_DRIVE`, 3→`/O4/TRI_SCALED`.
- Unit 2 `general_output:A`: 7→`/O4/C7b4ed2_DRIVE`, 6→`/O4/C7b4ed2_DRIVE`, 5→`/O4/SAW_SCALED`.
- Unit 3 `general_output:A`: 8→`/O4/Cec1eaa_DRIVE`, 9→`/O4/Cec1eaa_DRIVE`, 10→`/O4/PUL_SCALED`.
- Unit 4 `oscillator:unused grounded follower`: 14→`/O4/PACK_OPA4196IDR_5_IO_UNUSED4`, 13→`/O4/PACK_OPA4196IDR_5_IO_UNUSED4`.

### U2119 — F1

- Unit 1 `magnitude_indicator:A`: 1→`/F1/Cb3d4a2_DRIVE`, 2→`/F1/Cb3d4a2_SENSE`, 3→`/F1/IN_BUFFER`.
- Unit 2 `magnitude_indicator:A`: 7→`/F1/Cb6d8fd_DRIVE`, 6→`/F1/Cb6d8fd_SENSE`, 5→`/F1/FREQ_BUFFER`.
- Unit 3 `magnitude_indicator:A`: 8→`/F1/C9fcdd2_DRIVE`, 9→`/F1/C9fcdd2_SENSE`, 10→`/F1/RES_BUFFER`.
- Unit 4 `magnitude_indicator:A`: 14→`/F1/Cfc4b03_DRIVE`, 13→`/F1/Cfc4b03_SENSE`, 12→`/F1/GAIN_BUFFER`.

### U2218 — F2

- Unit 1 `general_output:A`: 1→`/F2/C5d31c8_DRIVE`, 2→`/F2/C5d31c8_DRIVE`, 3→`/F2/LP_CORE`.
- Unit 2 `general_output:A`: 7→`/F2/C29cc99_DRIVE`, 6→`/F2/C29cc99_DRIVE`, 5→`/F2/BP_CORE`.
- Unit 3 `general_output:A`: 8→`/F2/C2b02f4_DRIVE`, 9→`/F2/C2b02f4_DRIVE`, 10→`/F2/HP_CORE`.
- Unit 4 `general_output:A`: 14→`/F2/C56c9d6_DRIVE`, 13→`/F2/C56c9d6_DRIVE`, 12→`/F2/DRY_CORE`.

### U4346 — E3

- Unit 1 `high_impedance_input:A`: 1→`/E3/SIG_BUFFER`, 2→`/E3/SIG_BUFFER`, 3→`/E3/C33e306_SENSE`.
- Unit 2 `high_impedance_input:A`: 7→`/E3/RISE_BUFFER`, 6→`/E3/RISE_BUFFER`, 5→`/E3/C2882f4_SENSE`.
- Unit 3 `high_impedance_input:A`: 8→`/E3/FALL_BUFFER`, 9→`/E3/FALL_BUFFER`, 10→`/E3/C7b4897_SENSE`.
- Unit 4 `general_output:A`: 14→`/E3/Cc9f2ea_DRIVE`, 13→`/E3/Cc9f2ea_DRIVE`, 12→`/E3/ENV_BUFFER`.

### U4347 — E3

- Unit 1 `general_output:A`: 1→`/E3/C5dbedd_DRIVE`, 2→`/E3/C5dbedd_DRIVE`, 3→`/E3/BIP_CORE`.
- Unit 2 `general_output:A`: 7→`/E3/Caf802b_DRIVE`, 6→`/E3/Caf802b_DRIVE`, 5→`/E3/EOC`.
- Unit 3 `general_output:A`: 8→`/E3/Ce82060_DRIVE`, 9→`/E3/Ce82060_DRIVE`, 10→`/E3/STAGE_HIGH`.
- Unit 4 `magnitude_indicator:A`: 14→`/E3/Cae74f8_DRIVE`, 13→`/E3/Cae74f8_SENSE`, 12→`/E3/SIG_BUFFER`.

### U4348 — E3

- Unit 1 `magnitude_indicator:A`: 1→`/E3/C8c002f_DRIVE`, 2→`/E3/C8c002f_SENSE`, 3→`/E3/RISE_BUFFER`.
- Unit 2 `magnitude_indicator:A`: 7→`/E3/C9f1934_DRIVE`, 6→`/E3/C9f1934_SENSE`, 5→`/E3/FALL_BUFFER`.
- Unit 3 `envelope:unused grounded follower`: 8→`/E3/LED_PACK_OPA4196IDR_1_IO_UNUSED3`, 9→`/E3/LED_PACK_OPA4196IDR_1_IO_UNUSED3`.
- Unit 4 `envelope:unused grounded follower`: 14→`/E3/LED_PACK_OPA4196IDR_1_IO_UNUSED4`, 13→`/E3/LED_PACK_OPA4196IDR_1_IO_UNUSED4`.

### U5110 — W2

- Unit 1 `wavefolder:F1`: 1→`/W2/F1_OUT`, 2→`/W2/F1_SUM`, 3→`/W2/F1_CLIP`.
- Unit 2 `wavefolder:F2`: 7→`/W2/F2_OUT`, 6→`/W2/F2_SUM`, 5→`/W2/F2_CLIP`.
- Unit 3 `wavefolder:F3`: 8→`/W2/F3_OUT`, 9→`/W2/F3_SUM`, 10→`/W2/F3_CLIP`.
- Unit 4 `wavefolder:F4`: 14→`/W2/F4_OUT`, 13→`/W2/F4_SUM`, 12→`/W2/F4_CLIP`.

### U5209 — W1

- Unit 1 `wavefolder:CURRENT_SERVO`: 1→`/W1/BASE_DRIVE`, 2→`/W1/EMITTER`, 3→`/W1/TARGET`.
- Unit 2 `wavefolder:PRE_GAIN`: 7→`/W1/PRE_GAIN`, 6→`/W1/PRE_GAIN_SUM`.
- Unit 3 `wavefolder:DRIVE_SUM`: 8→`/W1/FOLDER_NEG`, 9→`/W1/FOLDER_SUM`.
- Unit 4 `wavefolder:DRIVE_INVERT`: 14→`/W1/FOLDER_DRIVE`, 13→`/W1/DRIVE_INV_SUM`.

### U5210 — W1

- Unit 1 `wavefolder:F1`: 1→`/W1/F1_OUT`, 2→`/W1/F1_SUM`, 3→`/W1/F1_CLIP`.
- Unit 2 `wavefolder:F2`: 7→`/W1/F2_OUT`, 6→`/W1/F2_SUM`, 5→`/W1/F2_CLIP`.
- Unit 3 `wavefolder:F3`: 8→`/W1/F3_OUT`, 9→`/W1/F3_SUM`, 10→`/W1/F3_CLIP`.
- Unit 4 `wavefolder:F4`: 14→`/W1/F4_OUT`, 13→`/W1/F4_SUM`, 12→`/W1/F4_CLIP`.

### U8314 — M4A

- Unit 1 `high_impedance_input:A`: 1→`/M4A/1_BUFFER`, 2→`/M4A/1_BUFFER`, 3→`/M4A/Caeced9_SENSE`.
- Unit 2 `high_impedance_input:A`: 7→`/M4A/2_BUFFER`, 6→`/M4A/2_BUFFER`, 5→`/M4A/C5eb398_SENSE`.
- Unit 3 `high_impedance_input:A`: 8→`/M4A/3_BUFFER`, 9→`/M4A/3_BUFFER`, 10→`/M4A/C7750d4_SENSE`.
- Unit 4 `high_impedance_input:A`: 14→`/M4A/4_BUFFER`, 13→`/M4A/4_BUFFER`, 12→`/M4A/C2be340_SENSE`.

### U8318 — M4A

- Unit 1 `magnitude_indicator:A`: 1→`/M4A/C2169e5_DRIVE`, 2→`/M4A/C2169e5_SENSE`, 3→`/M4A/3_GAIN`.
- Unit 2 `magnitude_indicator:A`: 7→`/M4A/Cf876de_DRIVE`, 6→`/M4A/Cf876de_SENSE`, 5→`/M4A/4_GAIN`.
- Unit 3 `magnitude_indicator:A`: 8→`/M4A/C320656_DRIVE`, 9→`/M4A/C320656_SENSE`, 10→`/M4A/ATTEN_BUFFER`.
- Unit 4 `magnitude_indicator:A`: 14→`/M4A/Cd59875_DRIVE`, 13→`/M4A/Cd59875_SENSE`, 12→`/M4A/SUM_POSTVCA`.

### U8409 — M4B

- Unit 1 `remote_buffer:A`: 1→`/M4B/C797803_DRIVE`, 2→`/M4B/C797803_FB`, 3→`/M4B/1_BUFFER`.
- Unit 2 `bipolar_attenuverter:A`: 7→`/M4B/1_GAIN`, 6→`/M4B/C75c2e7_SUM`, 5→`/M4B/C75c2e7_W_SENSE`.
- Unit 3 `remote_buffer:A`: 8→`/M4B/Cfaa69a_DRIVE`, 9→`/M4B/Cfaa69a_FB`, 10→`/M4B/2_BUFFER`.
- Unit 4 `bipolar_attenuverter:A`: 14→`/M4B/2_GAIN`, 13→`/M4B/Ca1191c_SUM`, 12→`/M4B/Ca1191c_W_SENSE`.

### U8417 — M4B

- Unit 1 `high_impedance_input:A`: 1→`/M4B/ATTEN_BUFFER`, 2→`/M4B/ATTEN_BUFFER`, 3→`/M4B/Cb5ae41_SENSE`.
- Unit 2 `general_output:A`: 7→`/M4B/Cea264a_DRIVE`, 6→`/M4B/Cea264a_DRIVE`, 5→`/M4B/SUM_POSTVCA`.
- Unit 3 `magnitude_indicator:A`: 8→`/M4B/C412fd1_DRIVE`, 9→`/M4B/C412fd1_SENSE`, 10→`/M4B/1_GAIN`.
- Unit 4 `magnitude_indicator:A`: 14→`/M4B/C93bba0_DRIVE`, 13→`/M4B/C93bba0_SENSE`, 12→`/M4B/2_GAIN`.
