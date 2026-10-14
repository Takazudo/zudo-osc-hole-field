# Joined feed construction v2

Current E16 state and resumption: [technical acceptance checkpoint](#e16-current-checkpoint).
Operating scope: [ongoing WSL agreement](#ongoing-wsl-coordination--2026-10-14).
Earlier checkpoints below remain historical evidence; their next actions are not
fresh execution authority.

Construct one disposable load-side candidate using the existing six-wire interface and three AGND returns. Materialize uniquely identified terminals, inclined solder contacts, board-side access, insulation and a complete carrier. Source design and collision evidence are distinct from physical qualification and native acceptance.

Input HEAD: `8b2384a927fbd3c58669614fb40c7e722b78974e`. No original copper, fixed panel, non-core poses, harness identities or canonical boards change. No native run, F3 placement trial, adoption or merge is authorized by this packet.

The latest parent instruction supersedes the previous incomplete-source stop: ordinary unconstructed work must be implemented, not presented as an external blocker. Independent electrical and mechanical design reviews precede the construction. Repository precheck passed.


## V15 (historical; exact inputs unrecoverable)

V15 left KA 58 / KB 217 unresolved physical pads (110 direct, 165 supplemental) using staged micro/buried vias. Its receipts remain valid records, but their inputs were never retained: the normalized boards (`/tmp/feed-v2-K?-filtered-v15-supp-*.json`) and the normalize/clip/access helper (`/tmp/feed-v2-board-access.py`, SHA-256 `18b4daeb…`) existed only in a Codex Cloud `/tmp`. A hash search of all 5,912 historical py/json/gz blobs on every branch, plus Actions artifacts and releases, found none of them. The rejected v9 epoch, its 76-pad subset and the V14/V15 staged model stay negative evidence. E16 counts are a new denominator and are not comparable to V15.

## E16 — current epoch (2026-10-12)

Branch `integration/epic-242-core-routing`, parent `7e07b979`. Canonical `boards/` and `design/grid/placements.lock.json` are untouched. Native calls: 0. Electrical acceptance, manufacturing qualification and adoption: false.

**Construction.** `evidence/e16-construction-contract.json` records the published HDI capability check. The staged model's 0.05 mm dielectric under 2 oz foils, its 2 oz microvia layers, and the 0.075/0.15 mm fixture microvia contradict published limits (PCBWay, JLCPCB, Würth, NCAB), so E16 uses no staged vias. Access uses 0.3/0.6 mm through vias (filled and capped only for via-in-pad), 0.25/0.2 mm face traces and 0.25 mm clearances, all within published and board rules. Plating minimum and cap thickness are unpublished; finite barrel bounds should use 18 µm.

**Chain.** `construct.py` (replays candidate05 byte-for-byte: KA `ba6202f8…`, KB `05ce8d2b…`) → `normalize_board.py` (rail-pad set must equal the 3,849 reviewed ports; direct loads from `mandatory-physical-ports-review.json`: KA 1,031, KB 1,490) → `evaluate_access.py` with `clip_sheets.py` (caps → clip → graph → census) → `construct_access.py` rounds → full re-evaluation after every round. `replay_e16.sh PYTHON OUTDIR` rebuilds everything from tracked files. Hashes, commands, times and memory are in `evidence/e16/index.json` (packed by `package_e16.py`); final residual identities are `evidence/e16/K?-r3-port-obligations.json`. Replay status at this checkpoint: KA content reproduced exactly; KB rounds NOT RUN (the replay hit the 180 s clip bound under machine load, and the guarded rerun was stopped by the host for low memory). Superseded on 2026-10-13: both boards now replay independently; see below.

| Round | Method | KA unresolved (direct / supp) | KB unresolved (direct / supp) | Newly disconnected |
| --- | --- | --- | --- | --- |
| base | no access | 1,557 (1,026 / 531) | 2,275 (1,490 / 785) | — |
| r1 | first legal via site on a 0.25 mm grid within 2 mm, straight trace | 425 (328 / 97) | 816 (583 / 233) | 0 / 0 |
| r2 | face maze route to feed-connected same-net copper | 293 (213 / 80) | 624 (451 / 173) | 0 / 0 |
| r3 | maze route to a new legal via site, with cumulative sheet-severance guard | 226 (166 / 60) | 521 (372 / 149) | 0 / 0 |

Representative direct load: KA `U1107` pad 11 (AGND, B.Cu, pad `0ab0435b…`). Every via site within 2 mm was blocked by U1105/U1107 face pads and signal vias, and the straight path to feed-connected pin 9 crossed no-connect pin 10. A 3-segment 0.25 mm route (2.34 mm) around pin 10's outer tip closed it in the full KA census (425 → 424 unresolved, direct 328 → 327, 0 newly disconnected). r2 applies the same method to every residual.

**Remaining blockers (r3 reasons).** Most residuals have no feed-connected same-net copper and no legal via site in the 3 mm window (KA 81, KB 349). The rest have no clear path (dense IC pin rows), or their target is blocked. A first r3 attempt without the guard severed one -12V (KA) and one +5V (KB, 19 pads) sheet neck; the cumulative guard removed that regression.

**Panel provenance.** Re-ran the retained native panel review with the pinned 10.0.6 oracle: 0 DRC findings, 438/438 lock centres, render reviewed. The CI Python suite passes locally (1,558 tests); its retained-artifact integration step is NOT RUN.

**Not done.** Signed-load finite electrical proof (contact/cap/barrel/sheet/wire, separate AGND return incidences) is not started for E16. No native fill/DRC of the E16 access copper. KEEP_K1402_INCUMBENT stands.

**Next continuation (2026-10-12, done 2026-10-13).** Re-run `construct_access.py --method route --planes …` on the r3 output, add a two-face option, then start the finite network. See the continuation below.

## E16 continuation — 2026-10-13

Same branch, same epoch and denominators. Canonical `boards/`, `placements.lock.json` and `decision.json` are untouched. Native calls: 0. Electrical acceptance, process qualification and adoption: false.

**Resumable replay.** `replay_e16.sh PYTHON OUTDIR` still rebuilds everything fresh. It now runs `replay_steps.py`, which also takes `--board`, `--through ROUND` and `--resume`. Each step writes `steps/<step>.json` with the SHA-256 of its inputs, methods and outputs. A resumed step is reused only when all three still match. A stale, partial or failed output is moved to `rejected/` (never deleted), and that step and every dependent step rerun. The 2026-10-12 base–r3 execution receipts stay unchanged.

**KB replay done.** Both boards were replayed from tracked files through t2, serialized under the host heavy-run guard. Base–r3 is an independent replay of the 2026-10-12 execution; r4, t1 and t2 have one execution each, so they are reproducible from tracked files but not yet independently replayed. Every step stayed within 180 s / 2 GiB; the longest was 104.8 s and the peak RSS 1.39 GiB. `compare_replay.py` checks, for both boards:
- per-round counts are equal;
- the normalized objects stay an exact prefix in every round;
- the added objects equal the retained r3 delta;
- the r3 graph, physical ports and complete census are equal once the seal fields alone are removed.

All four checks pass, and every round's object ids are unique. Clipped sheets and caps are not retained as files, so they are compared only through graph/census equality. The comparisons are in `evidence/e16/replay/20261013-r4-t2/`. The new seals carry this run's absolute paths and are retained as such; no retained hash was rewritten.

| Round | Method | KA unresolved (direct / supp) | KB unresolved (direct / supp) | Closed (KA / KB) | Newly disconnected |
| --- | --- | --- | --- | --- | --- |
| r3 | as above | 226 (166 / 60) | 521 (372 / 149) | — | 0 / 0 |
| r4 | r3 method repeated; r3 closures are new targets | 218 (161 / 57) | 511 (363 / 148) | 8 / 10 | 0 / 0 |
| t1 | shared access via, one representative pin per board | 217 (160 / 57) | 510 (362 / 148) | 1 / 1 | 0 / 0 |
| t2 | the same mechanism on every residual | 196 (144 / 52) | 486 (343 / 143) | 21 / 24 | 0 / 0 |

r4 closed only 18 pads, so a further same-method round was not run. Every round keeps all prior objects byte-identical, and all new UUIDs are unique. The cumulative severance guard stays on, with its -12V/+5V neck regressions. The full closed and residual identities are in `evidence/e16/index.json` and `K?-t2-port-obligations.json`.

**Two-face: precise negative.** `two_face.py` routes the pad to an existing same-net through via or hole, then on the opposite face to feed-connected copper or a legal new via. It needs:
- an intact barrel wall;
- positive copper contact outside the bore on both faces;
- hole clearance from every other drill;
- the cumulative sheet-severance guard.

Only 24 r4 residuals (KA 5, KB 19) have a same-net through object in the window that is not already feed-connected. For all 24, the opposite face near that transition has neither feed copper nor a legal via site, so the mechanism resolves none. That is why those transitions are orphaned.

**Shared access via: the demonstrated mechanism.** 115 residuals have a feed-connected same-net through object in the window, mostly a neighbouring pad's E16 access via. r2–r4 could not reach these targets because `local_route` keeps hole clearance even from the target via's own bore. `two_face.py --use-fed-transitions` exempts only that one bore, as a track ending on its via does, and keeps every other rule.

Representatives:
- KB `U4122` pin 7, AGND on B.Cu: r4 reported `feed_target_blocked`. The only feed copper in the window is C4136.2's r1 via, 3.05 mm away. U4119/U4122 pins and a signal via block every new via site. A 1.97 mm, 0.25 mm route onto that via closed the pin in the full census: 511 → 510, direct 363 → 362.
- KA `U2316` pin 5, AGND on B.Cu: r4 reported `no_clear_path`. A 1.39 mm route onto U2316.3's via closed it: 218 → 217.

t2 applied the mechanism to every residual: 21/21 and 24/24 proposals were credited, with 0 newly disconnected. 9 of the 45 routes land on a neighbouring pad's same-net via-in-pad. A transition whose bore centre is shared with any other drilled object is refused (`transition_bore_shared`). This is a single-face route to the inner sheet, not a two-face route.

**Process assumptions corrected.** The corrections are in `evidence/e16-construction-contract.json` under `corrections_2026_10_13`; the original findings are kept.
- JLCPCB advertises 2 oz inner copper. No 2 oz 6-layer stackup row is published.
- 18 µm is the published average hole plating, not a minimum. The finite model therefore treats plating as a parameter (`evidence/e16/process-cases.json`).
- Open: the 2 oz annular ring of ≥0.254 mm versus the 0.15 mm access-via ring.
- Open: whether the filled-via limits refer to the hole or the pad.
- Open: no published cap thickness or minimum wall.

The 0.025 mm wall in `connectivity.py` is a geometric test band. It is monotone-conservative for contact, so the graph keeps one configuration. The through-via stack is unchanged.

**Finite network: begun, partial.** `finite_network.py` models one board net on t2 copper:
- raster sheet cells wholly inside feed-connected pieces;
- face segments as resistors;
- barrel legs at the full 1.6 mm;
- the CS247 terminals with wire plus termination;
- the three AGND returns as separate incidences.

Each sheet edge, segment and barrel leg is one resistor, so no copper is shared between elements. Barrel legs are deliberately overcharged at the full thickness, and joins are ideal. The model is therefore neither an upper nor a lower bound: a value above a budget means "not shown within budget". A barrel attaches only to the sheet piece containing its centre. `run_finite_network.sh` covers both boards, four nets, three process cases, the seven AGND return states and a pitch pair. All 34 runs stay within 180 s / 2 GiB; the longest, KB AGND with seven return states, took 174.1 s, close to the bound. Results are in `evidence/e16/finite-network-t2.json`. At nominal-average and 0.5 mm:
- Maximum port resistance including the wire: KA 8.5 / 14.9 / 8.9 / 13.2 mΩ and KB 9.8 / 22.2 / 19.5 / 16.0 mΩ (+12V / -12V / +5V / AGND).
- The worst ports are dominated by local traces and barrels.
- AGND return shares are unequal: up to 0.37 with all three returns, 0.53 with one removed and 1.0 with two removed.
- The model drop figure ΣI × max R uses the planning totals. It is computed only where every port has a finite path: KA +12V 5.9 mV, KB +12V 7.3 mV and KB AGND 25.0 mV. KB AGND is therefore not shown within 20 mV. The figure is null for KA AGND (1 port without a path) and for every +5V/-12V net.

Coverage gaps:
- At 0.5 mm, the fragmented +5V/-12V sheets leave KA 21/146 and KB 306/78 structurally connected ports without a finite path.
- 1.0 mm loses far more. 0.25 mm was NOT RUN because it would exceed 2 GiB.
- Per-pad signed currents are not established.
- The partner board, the KA main-hub incidence and the far-end AGND copper are not modelled.

This is not electrical compliance (`evidence/e16/gate-status.json`).

**Review.** An independent review confirmed:
- the replay comparison;
- prefix preservation and unique ids for every round;
- the unchanged original receipts;
- census crediting of every t2 route.

It also found defects, now fixed:
- the model figures were overstated as bounds, and the drop figure was reported with unsolved ports;
- barrels could attach to an adjacent sheet piece;
- the resume log was not retained;
- a ledger/output name collision in `rejected/`: the moved stale KB r2/r3 sources were replaced by their ledgers. Their hashes equal the rebuilt files, so no content was lost;
- the packager overwrote the original `replay_e16.sh` hash in `index.json`;
- coaxial bores could be exempted;
- the JLCPCB filled-via quote mixed two processes.

**Checks.** See the PR #260 checkpoint comment for the commands and results of this commit.

**Next continuation.**
1. Resolve the +5V/-12V finite coverage, using exact-polygon neck conductances or an adaptive mesh within 2 GiB, before adding currents.
2. Solve KA and KB jointly through the six wires, with the KA main-hub incidence.
3. Assign per-pad signed currents from the module planning rows, as a conditional class.
4. For access: the remaining residuals (KA 196, KB 486) mostly have no feed copper and no legal via site in the 6 mm window. Further progress needs changed geometry or a new reachable target, not a wider search.

## E16 continuation — 2026-10-13 (second session)

Same branch and epoch. Plan: [#253 continuation comment](https://github.com/Takazudo/zudo-osc-hole-field/issues/253#issuecomment-6130087762). Canonical `boards/`, `placements.lock.json`, `decision.json`, original copper and the retained t2 receipts are untouched. Native calls: 0. KEEP_K1402_INCUMBENT stands; no adoption, qualification or merge. The dated evidence index is `evidence/e16/continuation-20261013/index.json`.

### Replay: independently reproduced through t2

`compare_replay.py` was repaired. It now composes the r1–r3 and r4–t2 delta bundles once each and checks, per round:
- the exact residual pad identities, from that round's own retained evidence (access-report inputs, r3/t2 obligations, cumulative closed identities);
- the full access report;
- an append-only prefix with unique ids;
- the round's added objects against its own retained bundle.

Each span must be reproduced exactly. Base copper must equal the content digest retained by the first base–r3 replay, and the final graph and census must match. Any mismatch or missing file exits nonzero. Only documented run seals are excluded, plus the exact r1/r2 report fields that later `construct_access.py` revisions added (`index.json` `method_note`). Twelve regressions cover same-count identity swaps, altered base and added copper, rewritten prior objects, missing/duplicate/cross-span deltas, newly disconnected pads, changed reports and the CLI status.

A fresh replay of both boards through t2 ran serialized under the host guard: 29 steps, the longest 102.1 s, peak RSS 1.34 GiB. It is content-equal to the retained evidence on both boards (`evidence/e16/replay/20261013-t2-independent/`). r4, t1 and t2 now have two executions each. The first execution's directory also passes the repaired comparator.

### Process evidence refreshed (no supplier contact)

`evidence/e16/process-evidence-20261013.json` keeps verbatim quotes, the section labels and the process each applies to. The superseded statements are corrected in `e16-construction-contract.json` `corrections_2026_10_13_process_refresh`; the earlier text is kept.
- The guide's ≤0.5 mm limit is a **hole** limit that also covers epoxy-filled vias; E16's 0.3 mm hole is inside it.
- "Hole surface copper ≥5 µm" belongs to the filled-and-capped column, but the page does not say whether it is the cap or the wall. It is not a barrel-wall minimum.
- Open:
  - whether a six-layer order fills every via by default;
  - whether the 2 oz PTH ring ≥0.254 mm applies to vias;
  - the minimum plating;
  - a published 2 oz six-layer stack;
  - drill versus finished hole.

`process-cases.json` is unchanged, because the historical finite receipts bind its hash.

### Current ledger: conditional, nonzero, KCL-consistent

`load_ledger.py` writes `evidence/e16/load-ledger-20261013.json.gz`. It has one record per rail pad per scenario: 3,849 pads including the 12 terminals. Each record carries:
- a signed current and its operating condition;
- the physical owner, source and provenance class.

Scenario `normal-typ-v1` injects only two kinds of current:
- datasheet-supported OPA4196/OPA4197 quiescent current at 25 °C: ±147.84 mA on KA, ±177.92 mA on KB;
- conditional SN74HC14/HC74 static ICC: +5V 0.10 / 2.32 mA, returning through AGND.

Device KCL is exactly zero; ±12 V op-amps carry no AGND current. Planning totals are never divided among pads. Each board's remainder is a pad-less allowance (KA +12V 553.9 mA; KB +12V 566.6 mA). The 70/50/50 mA EL ceiling is a separate external demand: the worksheet charges EL LEDs at 0.55 mA, and how the two relate is unresolved (review finding, fixed). Most fitted ICs are unmapped (KA 34, KB 160 unmapped; KB 62 partial). Full-scope budget acceptance is therefore false.

### Finite coverage: complete at t2 (zero model-only omissions)

The earlier raster model's 552 omissions are now diagnosed, each with a witness. `diagnose_omissions.py` rebuilds that model at component level, and first must reproduce all 552 exactly. Results (`evidence/e16/omissions/`):
- KA: −12V 146, +5V 21, AGND 1.
- KB: −12V 78, +5V 306.

| Cause | Pads |
| --- | ---: |
| The pad's island attaches only to raster cells cut off by sheet necks narrower than one 0.5 mm cell | 546 |
| A barrel has no whole raster cell within reach in its own sheet piece | 6 |
| Whole-object filter, or anything else | 0 |

None is a structural-census defect.

New adapter (`fragments.py`, `finite_adapter.py`, `finite_units.py`, `run_finite_e16.py`):
- **Fragments match the graph.** It rebuilds the structural graph's drilled per-layer fragments and must reproduce `object_connections` identity by identity before meshing.
- **One conductor per group.** Fed fragments joined by positive-area edges become one group, so overlapping copper is owned once. Tangent-only contacts inside a group are cut with a 2 µm slit, so, as in the graph, they do not conduct.
- **Exact meshing.** Each group is meshed by `scripts/pcbgen/sheet_mesh.Sheet` on the exact clipped copper (P1, conforming) at 1 mm inner and 0.25 mm face cells. Large groups are tiled on one aligned grid and merged by coordinate within the group only.
- **Barrels.** Each tap's bore boundary is one ring node. Consecutive taps are joined once by the annular interval at declared depths. Through vias also tap their non-functional annuli, and the intervals partition F→B exactly once.
- **Pads and lands.** A pad is a uniform-current finite support (consistent FE load vector). A held source land fixes only the mesh nodes inside its copper.

Coverage criterion: a pad counts only when its whole support lies in a finite component that holds a feed terminal. Result (`evidence/e16/finite-coverage-t2.json` and `-rows.json.gz`):
- **Census unchanged:** 3,849 pads, 3,837 originals, 682 residuals listed, 3,155 source-connected, 12 terminals.
- **Coverage:** every source-connected pad and every terminal has a finite path; the 552 old omissions are all covered.
- **Mesh:** each board net forms one finite component. The largest has 1.87 M nodes and 2.78 M triangles; area error is ≤1.8e-7 mm² per net.
- **Resources:** every unit ran within 180 s and 2 GiB.

Two review findings changed the meshes before the final run: tangent contacts used to conduct inside a group, and held lands spilled past their copper. A third run failed because the host guard's 30 min max-run expired; it was resumed. The superseded runs are kept outside the repository.

### Residual atlas and new-target pilots: KB pilot credited (6 pads), KA has no legal corridor within its limits

`residual_atlas.py` covers all 196 KA and 486 KB residuals (`evidence/e16/K?-t2-residual-atlas.json.gz`). An independent spot check of 10 rows agrees with the census, the graph and the recomputed distances. Each row lists:
- the class (direct/supplemental, ledger class) and the disconnected component;
- every orphan-component identity and pad;
- the existing transitions;
- the nearest fed copper per face and on the sheet layer;
- the straight-corridor obstruction identities and drills at the access rules;
- the r4/t2 rejection reasons.

`pilot_preflight.py` searches one additive face corridor per plan target: 0.25 then 0.2 mm width, 0.25 mm to other-net copper and other-net drills, rule areas and outline respected. Both orphan components match the plan exactly. The independent pilot review found a defect in the first two preflights: they applied hole clearance to **same-net** drills, including the orphan's own vias. Copper-to-hole clearance is a different-net rule, so the tool was fixed and both boards were re-preflighted under the same limits (preflight c). The 12 mm window / 30 mm length / 10-segment limits were set after KA's 6 mm attempt failed (not pre-sealed). They then applied unchanged to both boards.

- **KB U4320.14 (+5V): sealed, reviewed, constructed once, credited.**
  - The corridor is F.Cu, 0.25 mm wide, 7.493 mm long, 3 segments, from orphan via `d23658ae` to fed +5V via `e52b5e9d` (`pilot/KB-seal.json`).
  - An independent geometry review found 0.2517 mm minimum to other-net copper and 0.402 mm to other-net drills, positive overlap at both ends, and no forbidden rule area: PASS (`KB-seal-review.md`).
  - One construction (`pilot_construct.py`) added only those segments and re-ran caps → clipped sheets → graph → complete census. It closed exactly the 6 orphan pads — U4320.14 (direct), C4337.1, R4334.1, U4336.4, C4353.1 and U4336.10 — with **0 newly disconnected**. KB went 486 → 480 (343/143 → 342/138).
  - The result is the separate post-t2 record `pilot/KB-p1/`. The t2 receipts and models are unchanged. Native DRC/connectivity: NOT RUN. The end contacts sit 13–16 µm inside the via copper.
  - The affected electrical case was rerun on P1: KB +5V coverage, then the coupled +5V, nominal, all returns present (`pilot/KB-p1/electrical-rerun.json`).
    - Coverage: all 405 obligated pads, including the 6 new ones, have finite paths.
    - Resistance: the 6 new pads reach the source through 28.8–31.3 mΩ of copper. This is structural closure without a usable resistance; the 1 mΩ requirement is far exceeded.
    - Currents are unchanged, because U4320's supply current is unmapped.
    - Other P1 nets and cases are NOT RUN.
- **KA U2314.11 (−12V): no legal corridor within the sealed limits on either face**, so no construction (`pilot/KA-pilot-outcome.json`). The review found a legal B.Cu route only outside those limits (0.2 mm, 23.5 mm, 16 segments, needing a 20 mm window); it was not built.
- **Dimensioned future changes for KA.** The orphan's own access vias sit in an unfed In3 island (6.88 mm², 0.277 mm from the fed sheet). Any of these would connect it:
  - Remove the non-functional In3 annulus of AGND via `1e1b90ef`; the independent re-clip joins the island on its own (0.813 ≥ 0.75 mm).
  - Move that via ≥0.087 mm.
  - Take the longer B.Cu route.

  Rerouting only the two named In3 trace segments does not join it. Every option is outside this pilot's rules and needs full re-evaluation.

### Coupled KA–KB network: conditional reduced study, copper requirement not met

`finite_solve.py` and `run_coupled_e16.py` (config `evidence/e16/coupled-network-config.json`) reuse the joined-power identities: W1…W6 per `power/joined/interfaces.json`, three separate AGND returns with distinct landings, and KA as the load-side star.
- **Wires.** Each wire's bulk (85 mm × 13 mΩ/m = 1.105 mΩ) is charged once. Each termination (0.038 mΩ per end, half of the "both ends" 0.0760 mΩ in `electrical-design.json`) is charged once, on its own board, as a distributed stamp over the terminal pad. The old per-board 1.181 mΩ lump would have charged both twice.
- **Source support.** This is conditional: each net's fed KA main lands are held at one potential over their interior copper, standing in for the unimplemented load-side star. TP990036 is excluded because it is unresolved. No upstream AWG14 section and no raw/load bridge is modelled.
- **Solve method.** Each board is factored alone (SuperLU, iteratively refined) and reduced onto its terminal nodes. Every return state is then solved on the small interface system and back-substituted. A small monolithic reference matches to 1e-8 (`test_finite_adapter`).
- **Memory.** Solver units are bounded by a kernel 2 GiB no-swap memory scope (`MemoryMax=2G`, `MemorySwapMax=0`), verified inside each unit. SuperLU's address-space reservation made the old `RLIMIT_AS` cap reject factorisations whose resident peak is 1.24 GiB (KB AGND, 1.87 M nodes). The largest per-step peak RSS in the coupled run is 1.68 GiB.

Scope is the KA–KB subnetwork only. All 412 KA/KB ends of inherited rail/AGND conductors map to census pads: 376 AGND harness returns, of which 62 are unresolved; 18 EL rail pads; 18 KA main lands. The inherited 380 GH-return conductors reconcile exactly: 376 have a KA/KB end, and 4 are JL–P conductors with no core end. None has a supported current operator, so all are named external boundaries. GH 0.5 A compliance is **NOT EVALUATED**, and patch sleeves are not returns.

Matrix: three process cases × seven KA–KB return states, all executed (21). All-three-open is classified per case: KB AGND floats, and fault obligations stay with #59 and the GH-return analysis. `evidence/e16/coupled-matrix-t2.json` gives per-entry results:
- pad potentials, local-ground displacement and the signed rail-minus-local-ground error, with an additive screen;
- wire and source currents;
- KCL and energy checks;
- class energies;
- driving-point and copper-share resistance per pad;
- the KA trunk resistance.

| Case | Max \|rail − local ground\| (any state) | Pads over 20 mV | Pads over copper requirement | KA trunk to terminal, +12V / −12V / +5V / AGND (mΩ) |
| --- | ---: | ---: | ---: | --- |
| nominal-average | 0.574 mV | 0 / 1,294 | all 525 / 347 / 422 / 1,844 | 1.160 / 1.488 / 1.999 / 0.58–0.68 |
| sensitivity-thin | 0.780 mV | 0 / 1,294 | all | 1.874 / 2.242 / 2.896 / 0.83–0.96 |
| legacy-conditional | 0.592 mV | 0 / 1,294 | 524/525, then all | 1.134 / 1.521 / 2.089 / 0.61–0.72 |

What this means:
- **20 mV: within budget only for this lower-load study.** The worst rail-minus-local-ground error over the 1,294 evaluated rail pads with a referenced part is ≤0.78 mV. The study injects only supported op-amp quiescent current and conditional logic ICC: +12V 235 mA from the source. Unsupported and EL demand are not injected, so this is not a worst case.
- **Unserved load.** Supported current on structurally unresolved pads cannot be delivered: +12V 90.8 mA, −12V 101.0 mA, +5V 0.64 mA, AGND 0.88 mA (nominal). The ledger's per-device KCL is exact, but the currents actually injected are not balanced device by device. One supply pin of a device can be served while its other pin is not (served +5V 1.78 mA vs AGND 1.54 mA), so each net is solved with its own served set.
- **Copper requirement: not met.** The 1 mΩ rail and 0.5 mΩ common-AGND requirements are charged once along the whole source-to-pad path. They fail at every evaluated pad in the nominal-average and sensitivity-thin cases. One +12V pad passes in the legacy-conditional case (524/525 fail). The shared KA trunk alone, from the source lands to the CS247 terminal support, already exceeds the whole allowance on every net and case.
- **Dominant contributors** (all-present, nominal):
  - +12V: KA barrels 40% of dissipation, inner copper 21%, wire 24%;
  - −12V: KA inner sheet 44%, KA barrels 24%;
  - +5V and AGND: inner sheets on both boards, then the wire bulk.
- **Remedies to quantify next:** more parallel access vias at the main lands and CS247 terminals, or wider face pours there.
- **Source-support sensitivity** (`evidence/e16/coupled-source-sensitivity-t2.json`, nominal-average, all seven return states; other cases NOT RUN). The default holds all fed main lands of a net at one potential, an ideal tie between lands that the plan forbids as a physical claim. Holding only each net's JL-branch land (TP990002/004/006/008) instead:
  - raises the KA trunk to +12V 2.34, −12V 5.97, +5V 9.81 and AGND 1.12–1.22 mΩ (default: 1.16 / 1.49 / 2.00 / 0.58–0.68);
  - raises the worst error to 1.55 mV, still 0 pads over 20 mV.

  The default tie is therefore optimistic. The copper conclusion only strengthens, and the actual load-side star geometry decides the real value.
- **Return removal.** Removing returns barely changes the voltages at this load (W6 alone carries 1.46 mA). It does change copper-share resistance slightly.
- **History.** The historical KB AGND 25.027 mV figure stays in `finite-network-t2.json` as a conditional partial-model finding with its own schema. It is not comparable: different loads (planning total × max port R), no partner board, and a lumped wire.

Numerical checks, against tolerances declared before results:
- **Met:**
  - global KCL ≤1e-9 in all 20 net×case files;
  - energy minus load work ≤1e-9 except one case;
  - nonnegative class energies;
  - wire/terminal current balance ≤1e-14 A;
  - reduction reciprocity ~1e-11;
  - monolithic-reference agreement 1e-8.
- **Not met:** energy minus load work reaches 1.64e-9 against the declared 1e-9 in the legacy-conditional +5V case, all seven states. The refined driving-point solves, which give every copper-resistance figure, leave a relative residual ≤5.0e-9; no tolerance was declared for it.
- **Not met:** node-level KCL relative to the largest injected node current. `verify_kcl.py` (`evidence/e16/node-kcl-audit-t2.json`, input and method hashes bound) measures it two ways:
  - across the 40 board reductions: 1.7e-9 to 5.2e-8;
  - across all 100 published coupled board-states, rebuilt from the reductions and the interface solves: 1.5e-8 to 1.8e-7.

  Both are against the declared 1e-9. The cause is the evaluation floor:
  - **Per-row residual:** every row's residual is ≤3.9e-15 of that row's own current magnitude (≤17.5 machine epsilons; 69 rows lie between 10 and 17.5 ε). That is the double-precision floor for a row sum of about ten terms.
  - **Why the floor is high:** relative to the largest load current, the floor itself reaches 7.9e-7, because the 2 µm slit and skinny elements carry conductances up to 8.8e8 S.
  - **Reduction solves:** the normwise backward error is ≤1.4e-16.

  The declared criterion stays NOT MET; it is unattainable in double precision on this mesh.

Mesh sensitivity on real copper (`evidence/e16/mesh-sensitivity-K?-*.json`; same fragments, pad supports and source lands; only the cell grid changes; tolerances declared before results):
- **Half pitch** (0.5 mm inner, 0.125 mm face) raises single-board driving-point resistances by a median 2.9% (KA +5V, 24 pads) and 2.5% (KB −12V, 146 pads), at most 4.2%. Conforming P1 approaches from below, so the reported resistances slightly understate the copper, which only strengthens the copper-requirement failure.
- **A grid origin shifted** by (0.37, 0.21) mm changes them by at most 1.1%.
- Both are within the declared 5% report tolerance. Two meshes are not a convergence proof.

Stack-depth sensitivity (nominal-average, all returns present; `evidence/e16/coupled-depth-sensitivity-t2.json`):

| Stack | KA trunk to terminal, +12V / −12V / +5V / AGND (mΩ) | Max pad copper resistance, +12V / AGND (mΩ) | Barrel share of +12V dissipation |
| --- | --- | --- | ---: |
| uniform-dielectric (default) | 1.160 / 1.488 / 1.999 / 0.58–0.68 | 6.48 / 15.66 | 42% |
| staged-caps-bands (rejected staged stack) | 1.222 / 1.624 / 1.780 / 0.56–0.66 | 6.77 / 15.73 | 45% |
| barrel-upper-1p6-per-interval (each interval's upper bound) | 3.202 / 3.152 / 3.454 / 1.01–1.11 | 14.70 / 18.93 | 79% |

The copper-requirement conclusion does not depend on the unknown stack. The trunk exceeds the allowance in every case.

### Checks and gates (this continuation)

| Check | Result |
| --- | --- |
| `pnpm circuit:check` before edits (8ca91b4) and after (0ad49dd) | PASS (manual inventory, 68 lines; schematic/placement binding not performed) |
| Start-of-task `scripts/checks/regen-all.sh` | Exit 0 with no tracked changes, so there was no pre-task regeneration to commit |
| `bash scripts/checks/run-python-tests.sh` (pinned numerical venv plus `scripts/checks/python-test-requirements.txt`, as CI installs) at 0ad49dd | PASS, 1,620 tests |
| `pnpm check` at 0ad49dd | PASS |
| `regen-all.sh --check` at 0ad49dd, clean tree before and after | PASS, no tracked changes; panel receipt bound inputs unchanged |
| Native fill/DRC/connectivity of E16 copper, retained-artifact integration, CI at this head (`[skip ci]`) | NOT RUN (no admission; descriptor prepared only) |

An earlier `regen-all.sh --check` failed only because WORK.md and `gate-status.json` were edited while it ran. The first full Python run stopped on two kicad tests that import PyYAML, which the venv lacked; both were resolved before the runs above.

Gates: G1 open (unchanged); G2 OPEN (`evidence/e16/gate-status.json`); G3/G4 NOT RUN / NOT ADMITTED; G5 unchanged; G6 NOT RUN. KEEP_K1402_INCUMBENT. Delivery issues stay open.

**Next continuation:**
1. A materializer for fresh-copy native validation of t2 (or P1), then an admission request based on the descriptor.
2. Main-land and CS247-terminal trunk remedies (parallel vias or pours), quantified on the coupled model.
3. The KA future changes and the remaining 196/480 residuals, using the atlas.
4. Supported currents for the unmapped ICs, before any full-scope budget claim.

## E16 continuation — 2026-10-13 (third session)

Owner plan: [PR #260 continuation](https://github.com/Takazudo/zudo-osc-hole-field/pull/260#issuecomment-6140608021). Refreshed PR #260, #253 and integration branch at `dd3ef71`; no newer matching implementation was discarded. Current evidence is `evidence/e16/continuation-20261013b/`. Historical receipts below remain immutable. KEEP_K1402_INCUMBENT; canonical boards, placements and decision remain unchanged. No native execution, architecture adoption or merge.

**Materialization.** `materialize_e16.py` authenticates candidate05, the two retained delta spans, normalized content and terminal process records. It adds every t2 segment/through via once and four unfilled internal rail zones, preserves the original native bytes and UUIDs, and copies matching project/rule sidecars. KA t2, KB t2 and KB P1 are separate outputs. All 15 output files repeat byte-identically. Fresh t2 graph/census content equals retained KA196/KB486; fresh KB P1 equals its retained KB480 record. This does not reopen the completed independent replay or 552-omission work. Selective per-layer annulus removal is unsupported by this adapter; that is not a claim that KiCad 10 lacks custom via padstacks.

**Source and feed bounds.** The physical source dependency is negative: CN301/XB301 remain abstract, have empty footprints and no physical raw/load bridge. Fixed P-to-KA receiving lands do not become a source inlet. `feed_remedies.py` seals an unchanged baseline and exactly three predeclared local variants: twelve additional through-via proposals, two 1 mm face-copper proposals, and their exact combination. Seven vias pass local geometry; all other proposals are rejected with exact witnesses. Combined equals parallel-vias; wider-face equals baseline. The first run exceeded 2 GiB while building a repeated-geometry JSON report; it is retained as FAIL. Streaming reports and compact, input-bound sheet witnesses allow the unchanged experiment to finish within the same limit. No new source geometry, ideal star, extra variant or process qualification is inferred. Complete source-to-pad copper resistance remains unestablished; the 1 mOhm rail / 0.5 mOhm AGND allowances apply once to complete paths.

**Loads and numerics.** The old solve could drop one disconnected supply pin while energizing its partner. The new service manifest binds the ledger/configuration, all eight board/net coverage files and methods; reduction includes all declared supply/return pins of an eligible device or excludes the entire device. Missing eligible local support fails closed. Coupling and driving-point chunks reject stale process, source-support, method or service bindings. The current ledger separates typical, 25 C maximum and full-temperature maximum scenarios, preserves exact MPN/package/source/condition evidence, and makes supply-voltage application caveats explicit. At retained t2, 151 complete groups (116 OPA, 35 conditional logic) are eligible, 59 partial, 21 unserved and 194 unmapped. Typical included totals are +12 V +0.1716 A, -12 V -0.1716 A, +5 V +0.00124 A, AGND -0.00124 A: zero signed residual. These are quiescent subset currents, not full scope. Variant service must be recomputed from its actual coverage. All 380 GH conductors retain null currents and NOT EVALUATED compliance; no nearest-ground assignment or planning ceiling is injected as a device current.

Mixed-precision residual evaluation improves a small independently checked cancellation regression without changing equations, loads, three refinement steps or tolerances. Production node-KCL/energy criteria are **not closed**: the old 1.821e-7 load-relative node residual and 1.643e-9 energy failure remain evidence. Production re-solves are NOT RUN because this environment lacks the required user-systemd 2 GiB/no-swap scope. No guard was bypassed and no fixture pass is promoted to production acceptance.

**Residuals.** The exact U2314.11 annulus proposal cannot be represented by the current source adapter. The documented longer additive B.Cu alternative was selected under fixed new limits (20 mm window, 30 mm length, 20 segments, 0.2 mm width). Independent analytic clearance review passes the resulting 23.554 mm, 15-segment path. Its isolated-strip screen is 34.7 mOhm, not a solved complete-path result or a formal bound; resistance remains a serious failure concern. KB P1's six-pad geometric credit remains separate and its 28.8–31.3 mOhm result remains failed. Full census construction closes U2314.11 and C2342.1 (KA196 → 194), preserving all 73,699 prior objects and adding exactly 15 segments, with zero newly disconnected. The seven-via feed variant keeps the exact KA196 residual identities and all old objects. The first KA construction wrote a proposal but failed before evaluation because the input was already cap-materialized; raw-source equality was independently checked and the unchanged path resealed before the successful run. No geometric credit implies electrical acceptance.

**Native packet.** The new descriptor/request implementation stages exact materialized inputs and graphs, then defines one guarded fill, full-severity DRC without refill, and exhaustive UUID-based pad/feed/peer reconciliation on the same preserved filled board. It uses pinned KiCad 10.0.6 and existing resource guards. Parent approval must bind the exact run, attempt, source SHA, reviewed hook and request digest; preparation is not admission. Native status: **NOT RUN / NOT ADMITTED**. No previous receipt is reused. Full regeneration (which includes native phases), retained-artifact integration and CI are NOT RUN in this session; source checks are recorded separately in `checks.json` and the final PR checkpoint.

Remaining work is physical source/protection definition, complete signed load evidence and actual variant coverage, production numerical correction/validation in a supported guarded environment, resistance closure and exact-run native admission. Delivery issues and G1/G2/G3/G4/G6 remain open.

**Final source checks at `e215b9eb3f9695d74cd9dfc9de182e0882bebcd7`:** 1,681 source-only tests PASS, with one oracle-backed test explicitly deferred (two discovery occurrences; repository assertions unchanged). `pnpm circuit:check`, `pnpm check`, guarded `pnpm build`, and `pnpm check:site` PASS; 539 protected files match their initial hashes. The unchanged aggregate suite failed when a real oracle test downloaded its image and exhausted disk before Docker could start; a duplicate-discovery retry was stopped. The final source-only environment blocks native binaries, with no blocked invocation. Exact attempts, cleanup, selector and logs are retained. These results do not constitute a full-suite/native pass.

## E16 WSL continuation — 2026-10-13

Refreshed all three owner checkpoint comments, #253 and draft #260. The clean existing `worktrees/e16-r4` integration checkout fast-forwarded from dd3ef71 to f1650bba; implementation source e215b9eb remains unchanged. See `evidence/e16/continuation-20261013-wsl/README.md` and its indexed receipts. No unrelated local work was changed.

Fresh source-only materialization and complete census reproduce KA-t2 196, KB-t2 486 and separate KB-p1 480. Fifteen materializer outputs repeat byte-identically. The distinct prior KA long-B result remains 194 with zero newly disconnected identities; it was not substituted for the baseline. Protected canonical boards, placements and decision hashes remain unchanged.

The WSL user-systemd scope now proves 2 GiB/no-swap settings from inside a live scope; the pinned numerical venv and Docker image exist and Linux/container storage have about 409.7 GB free. Native runner qualification is still incomplete: `sudo -n systemctl show --property=Version --value` fails because a password is required, and the current native startup handshake has no newly admitted qualification. No security/service/WSL changes were made. Native KiCad/ngspice probes and the single deferred oracle test remain NOT RUN / NOT ADMITTED.

Fresh WSL descriptor and separate single-test recovery request were prepared with exact source/input/hook hashes. The current guard requires an actual GitHub run identity and separate parent/operator admission; none was fabricated. The final-head packet is regenerated after this evidence commit and linked in the PR/#253 checkpoint. Production numerical validation also remains NOT RUN pending its separate admission despite the now-working user scope. Physical source/load evidence, copper and numerical acceptance remain unresolved. KEEP_K1402_INCUMBENT; PR remains draft/unmerged.

## Local WSL admission implementation — 2026-10-13

The owner separately authorized source development of a local admission path after the WSL runner checkpoint; this did not authorize native execution. `scripts/kicad/local_native_admission.py` now prepares exact local requests, records separate operator attestations, and executes only the fixed startup checks, the single deferred oracle unittest or one of the three existing E16 targets. Local run nonces never masquerade as GitHub run IDs. Existing CI admission, Docker wrapper and resource guard are unchanged.

Requests bind clean HEAD, checkout/UID, run/attempt, exact operation, inputs/methods, shared guard configuration and output paths. Execution claims a persistent single-use worker identity, preserves driver logs, rechecks after queueing in the actual guarded service, and checks immutable inputs again after execution. Local E16 host/native authority retains the existing cgroup, read-only gate, exact-command, deadline and filled-board hash-chain checks. Native entry accepts the host-bound SHA only after real gate proof, avoiding an inaccessible WSL-worktree Git pointer in the container. Startup success and intentional-failure requests are separately admitted and reuse the complete lifecycle receipt verifier.

Independent source review PASS; reviewer independently ran 27 admission/startup tests using mocked launches. No approval receipt, native process, system service, security configuration or sudo policy was created or changed. Requests will be freshly prepared after the final evidence commit. Privileged runner access, actual control/startup qualification, exact-run operator approval and production numerical/native/electrical acceptance remain pending. Counts and physical design are unchanged: KA-t2 196, KB-t2 486, separate KB-p1 480, prior KA long-B 194. KEEP_K1402_INCUMBENT; draft #260 remains unmerged. See `scripts/kicad/README.md` for the operator procedure and same-account attestation limits.

Local admission source verification at `587b5e41a312c1e2dcea4c90c95199dd10a4afe1`: 125 source tests PASS (91 guard/admission/startup plus 34 E16/materialization/analytic); circuit/check/build/site PASS; 550 protected files unchanged. Independent reviewer ran 27 source tests and returned PASS. Evidence: `evidence/e16/local-admission-20261013/index.json`. No real approval or native execution.

Final replay-ledger hardening source: `f70e458a2197ad51ebb96ca9d2eb08804daaef1d`. Account-home lookup fixes the persistent claim directory even if HOME changes; arbitrary ledger relocation is refused. Independent delta review PASS; 126 source tests and circuit/doc checks PASS at this commit. Earlier dbad84f request packets remain saved but are stale. Fresh final-head preparation includes the exact separately approvable harmless-control qualification request as the next operator step.

## Operator terminal correction — 2026-10-13

The first owner-run harmless-control qualification failed before all phases: sudo system-manager probe exit 1, shared guard FAIL after 3 seconds with 10,370 MB minimum available memory. Previous advice authenticated before the shared guard's setsid boundary; that credential did not apply in its detached session. Original failure/request/approval are retained under `evidence/e16/operator-terminal-20261013/`.

Source `26cfc65d5699b7e5c2edbd4957c1f4e231de4e1c` adds operator-only PTY authentication inside the unchanged shared guard, no password/transcript recording, bounded noninteractive ticket refresh, and signal-safe entry to the harmless qualifier's existing owned cleanup. Requests seal authentication mode and helper methods; changed source requires fresh exact approval. Source-only tests PASS (102 + 34), circuit/doc/build checks PASS, independent review findings resolved, 550 protected files unchanged. Actual native/resource qualification is still incomplete. No sudo policy, service, WSL setting, guard limit, native hook or CI admission changed. Final-head packet and exact command are linked in the PR/#253 checkpoint. KA196 / KB486 / separate KB-P1 480 and prior KA long-B194 remain distinct; native and production electrical acceptance remain NOT RUN / NOT ADMITTED.

## Matched WSL native runs — 2026-10-13

All native runs were separately owner-admitted at clean head093f14b55c8a85d5d14be26f20868df2551d3b14. Retained requests/approvals/raw receipts/logs are indexed in `evidence/e16/native-wsl-20261013/`. Harmless controls PASS, startup-success PASS (KiCad10.0.6), intentional startup-failure qualification PASS with original failure preserved, and the single deferred oracle unittest PASS (one test,2.562s; no aggregate rediscovery).

KA-t2, KB-t2 and separate KB-p1 each completed fill, full-severity DRC and complete native pad/feed/peer reconciliation on the same preserved filled board with matching sidecars. Zero reconciliation differences across1568/2281/2281 pads; source/native unresolved identities remain196/486/480. All-net native open edges are479/1220/1219. Guard membership, no-swap limits, cleanup and post-run input integrity PASS. All550 protected files unchanged; three sudo renewals passed per board.

Board acceptance FAIL/NOT ACCEPTED. DRC reports813/815/815 warnings and479/499/499 unconnected-item errors, but these are capped findings, not exhaustive totals: pinned KiCad10.0.6 hard-caps ordinary categories at199 and clearance/unconnected at499. All three hit four warning caps; KB truncation is proven by the complete native census. Five configured ignored checks remain explicit. No guard, severity, toolchain or canonical board was changed. Independent evidence review PASS, with full DRC enumeration marked INCOMPLETE.

The prior KA long-B194 remains distinct and untested natively. Production numerical reduction/coupling/variants remain NOT RUN / NOT ADMITTED. Physical source/load and full-path resistance remain unresolved. Next numerical approval will be one exact bounded batch, not repeated per-command chat handoffs. PR260 stays draft/unmerged and253 open.

## Production numerical attempt and candidate correction — 2026-10-13

Owner approved exact requestbeb7f4d8...beeca4 at4bde7e8. With332 hashes verified, the batch ran under the shared guard and live user-systemd2GiB/no-swap scopes. Service census reproduced151 supported/59 partial/21 unserved/194 unmapped. Nominal +12V reductions failed the unchanged1e-9 load-relative residual criterion: KA1.449931603e-9; KB1.227478632e-9, although both processes exited0. Three KA driving-point chunks passed their checks. The active KB chunk was intentionally stopped(-15) under stop-on-failure after the failed diagnostics; no coupled result exists. Six steps completed; all original outputs/logs/approval/scope observations are retained under `evidence/e16/numerical-wsl-20261013/`. Inputs unchanged at shutdown; no OOM/timeout claimed.

Source `c8b2db34e7501b5ae5adb46e7b24710b1f3559cb` adds explicit numerical acceptance gates with preserved hash-bound verdicts and validates both reductions before any driving-point work. A fixture-backed candidate preserves the single load solution in extended precision through coupled/independent-KCL reconstruction, keeping multi-RHS storage and interface solve compatibility bounded. No tolerance, equation, load or resource limit changed. Independent source review PASS; production accuracy/memory and full coupled acceptance remain UNVERIFIED pending a freshly approved request. The old failure is not overwritten or relabeled. Native counts remain KA196 / KB486 / separate KB-P1 480, prior KA long-B194 distinct; physical/electrical gates stay open.

## Bounded diagnostic follow-up

The owner subsequently explicitly chose “Stop and diagnose the accuracy failure,” confirming that direction. Final review rejected the unadmitted broad retry request05dfbe7f...f74635a:111 chunks could take several hours, beyond the unchanged shared guard1800s whole-command limit. That request was never approved or run; it remains retained as superseded. No resource limit was increased.

Source `fc1800fd8af5647ed51588be01732ebcbbf8a411` adds reviewed `--reductions-only` mode. The next request is explicitly only+12V / nominal-average / uniform-dielectric: service plus KA and KB reductions, at most three180s units, then stop. No driving-point chunks, coupled solve or variant is included. This fits the unchanged1800s shared guard. Future full numerical scheduling must likewise fit existing guards; no full multi-hour batch is currently authorized. The candidate production accuracy and memory remain UNVERIFIED until this short fresh request is admitted and run.

## Admitted short production recheck — 2026-10-13

Owner “k” approved exact request8f8d104e...ab9665 at execution head `a73249c9f98f8fa9fd5d27aed85265062c74a907` (executable source `fc1800fd8af5647ed51588be01732ebcbbf8a411`). Exactly service plus KA/KB +12V nominal-average uniform-dielectric reductions ran. All three steps PASS; load-relative residuals now2.9803321747950843e-12 /1.309884394382926e-12 versus unchanged1e-9. Original failures1.4499316030378085e-9 /1.227478631500586e-9 remain preserved. No driving-point or coupled work followed.

Shared guard PASS,91s,minimum available8612MB. Actual solver scopes enforce2GiB/no-swap; sampled peak1,668,386,816bytes, no observed OOM, both inactive afterward. All334 request inputs and550 protected files match. Independent completed-run review PASS. Retained request/approval/claim/commands/versions/logs/verdicts and large-output hashes: `evidence/e16/numerical-short-wsl-20261013/`.

These production reductions establish the scoped accuracy correction only. Full coupled/node-KCL/energy and variant numerical validation remain NOT RUN on current source; source/load/full-path electrical acceptance remains open. Counts unchanged: KA196/KB486/separate KB-P1 480/prior distinct KA long-B194. Next prepare bounded serialized numerical scheduling within the unchanged shared guard, independently review it and obtain separate exact-request admission before further production execution. KEEP_K1402_INCUMBENT; draft PR260 unmerged; issue253 open.

Evidence/doc delta checks: circuit before/after, documentation/type/generated checks, shared-guard build and strict site checks PASS; existing link allowlist unchanged. Manual inventory68 lines; no schematic/placement binding. Final evidence/doc review PASS with no blocking findings. No executable source changed after fc1800f.

## Per-unit shared numerical guard — 2026-10-13

Executable source `2238c1ee0ea230b65e4e54419453f76ad2998653` schedules each serialized numerical unit through the unchanged shared guard, so the parent does not place a multi-hour batch inside one1800s guard. Each unit still has180s timeout and verified user-systemd2GiB/no-swap. Queue time is outside its timeout. Guard ownership/lock proof refuses bypass/nesting; complete streams are retained and content-checked, including interrupted orphan streams. The reviewed execution recipe requires separate exact admission and fails on changed source/input/request/approval bindings. No production execution or approval occurred.

Independent source/recipe review PASS after preserving orphan logs and failing closed on postrun binding drift. Next request: baseline four nets, three process cases, one uniform depth, whole-device normal-typ-v1 subset; <=148units including111 driving-point chunks, expected several hours. One owner approval of the final request digest covers the fixed serialized batch, stopping on first failure. No resume, native rerun, remedy variants, changed loads/tolerances, finite replay or guard override. Evidence `evidence/e16/unit-guard-wsl-20261013/`; final-head packet/checkpoint follows. Counts and physical/electrical gaps unchanged.

Final scheduling source checks at2238c1e:55 affected tests PASS; circuit/doc/build/site PASS; existing link allowlist unchanged;550 protected files unchanged. Source/recipe review PASS. Production scheduling NOT RUN pending exact-request approval.


## Approved baseline numerical batch — 2026-10-14 WSL

One execution of owner-approved request `7daa746001d8965891df6135be0b08054e5ca0c7dc9981798429be2919b729e8` at frozen HEAD `0dab96a0fb6434da41765cb181bc8807544f0a7e`, run `19563d44a548466bbe43723a69ece2fe`, attempt3, stopped at its first numerical failure. Actual user instruction recorded; admission consumed. No retry/resume or production solver edit.

Nine units PASS: whole-device service, both +12V nominal-average uniform-dielectric reductions, and six driving-point chunks (KA275/KB250 pads). First all-present coupled unit FAIL: free-node KCL KA1.515200877665821e-8 /KB7.277530568849482e-9 exceeds unchanged1e-9. Global KCL8.349850854768625e-11, energy2.4892459643435285e-12 and worst driving-point residual2.850814388399312e-10 pass. Remaining nets/cases/states NOT RUN after stop. Provisional failed-state electrical values are not acceptance; AGND/local-ground error is not newly evaluated.

Exact hook exit1 after874.011s. Per-unit shared guard retained180s timeouts and2GiB/no-swap scopes; nine guardPASS receipts, final numerical exit1 propagated as guardFAIL. Nine observed solver scopes had zero sampled memory events, peak1,717,420,032bytes, all inactive/absent after shutdown; no workload/guard owner remains. Service scope was too short for independent sampling. Before any tracked edit, all337 inputs, request/approval/source and550 protected files matched. Independent read-only preflight/terminal evidence review PASS; numerical batch remains FAIL.

Retained `evidence/e16/numerical-baseline-wsl-20261014/` includes exact commands, request/approval/claim, raw streams, failed result, verdicts, resources, integrity and review. Eight pickle outputs totaling50,087,109bytes stay in original ignored WSL storage with sizes/hashes/transfer instructions. Existing native qualification, single oracle, fill/census and finite coverage were not repeated. KEEP_K1402_INCUMBENT, canonical boards/accepted copper/fixed placements/decision unchanged; PR260 draft/unmerged, issue253 open.

Next: separately approve an isolated +12V reconstruction residual diagnostic against the preserved reductions/operators. Float64 interface reconstruction is a plausible precision seam, not proven root cause; identify worst nodes and decompose load/interface/reconstruction/operator residuals before a production change or fresh batch. Source/protection, complete loads/GH currents, full-path resistance, connectivity196/486 (separate480/prior194), capped DRC enumeration and physical/bench qualification remain open.


## Interface precision diagnosis and correction — 2026-10-14

After the failed baseline checkpoint, the owner explicitly authorized diagnose/fix/review/new-request preparation. Two guarded read-only diagnostics reproduce the exact KA/KB +12V failures; direct and reduced operator residuals agree. Widening only reconstruction multiplication remains failed (6.00835e-9/4.32262e-9). The stored float64 interface-basis error dominates the remaining load-relative residual. Recomputing only Y with extended accumulation while holding original vt/u0 fixed passes at1.7881993048770505e-11/8.233559050406965e-12 against unchanged1e-9.

Source9341dfb2eac826769e1c17a3831c081d60b72357 retains extended precision in the small interface basis, with unchanged3corrections/global normalization and float64 small-system S/g and driving-point batches. Final nonfinite residual refusal is separately tested.48 targeted tests PASS; independent reviewer ran26fixture tests then7final refinement tests. Four isolated diagnostics stayed within existing180s/2GiB/no-swap/per-unit shared guard; all guardPASS, scopes inactive,550protected files unchanged. Original consumed attempt3 and its failed outputs remain byte-preserved. Evidence: `evidence/e16/interface-precision-wsl-20261014/`.

This is isolated diagnostic/source evidence, not a fresh production coupled PASS. Prepare a new attempt4 request at final clean HEAD for the unchanged full baseline148-unit maximum, obtain exact approval, then use the reviewed hook once with stop-on-first-failure. No production batch/native/finite regeneration ran in this correction. KEEP_K1402_INCUMBENT and all physical/electrical gaps unchanged; draft PR260 unmerged and issue253 open.


## Standing-authorized WSL campaign — intermediate terminal checkpoint

The owner authorized a bounded sustained campaign (at most three full baselines including attempt4, plus24 guarded production-input diagnostic units), including fresh exact request review and honestly delegated authorization receipts. Attempt4 at9f69cd8 stopped after55 successful units on KB +5V nominal driving-point residual1.1208868656596437e-9 >unchanged1e-9. All six ±12V case coupled units passed. The earlier interface precision correction is supported by actual coupled results. Five diagnostics locate the new failure in pads16:32, distinguish float64 accumulator loss from batch width, prove extended accumulation, and pass the actual corrected96-pad +5V unit at1.1103386484989042e-12. The largest AGND96-pad unit then times out at180s with no numerical result. All terminal integrity/resource cleanup reviews PASS; no containment breach or OOM claimed. Budget1/3 full,5/24 diagnostic; next source-only performance diagnosis precedes a new exact production diagnostic.

PR272 andPR273 are cherry-picked with provenance into the isolated combined candidate, not merged PRs or published staging source. Combined1763 source tests PASS with two exact oracle identity exclusions;22 browser source tests and read-only mechanical generation checks PASS. All61 Mac retained hashes and19 receipt input bindings match. The Mac committed checker and supplemental Playwright runs remain distinct, including original negative scroll evidence; browser rendering is not installed fit. No new native/oracle/coverage work ran.

Completed nominal+12V numerical results support a negative copper-resistance finding: all525 evaluated paths exceed1mΩ. Partial load groups, source/protection and full return paths,380GH conductor currents, capped DRC enumeration and physical qualification remain open. The exact U2314.11/C2342.1 short In3 reconnection investigation is defined as a separate future source-owned intervention; no variant geometry or numerical job is adopted or launched. Compact campaign requests/receipts/reviews/results and engineering scope are retained under `evidence/e16/campaign-wsl-20261014/`; large outputs remain in indexed persistent WSL cache storage. KEEP_K1402_INCUMBENT, canonical copper/boards/panel and decision.json unchanged; PR260 draft/unmerged,253open.


### AGND runtime diagnosis and bounded CSC correction

Diagnostic6 at9a68f1a profiles the actual16-pad production CLI under the unchanged guard and scope; numericalPASS1.609516e-13. Of40.04s, residual evaluation takes26.57s including17.00s in searchsorted. Reviewed source492d0e2 uses bounded existing compiled CSC accumulation with identical stored-entry arithmetic;49focused tests and102independent synthetic equivalence checks PASS, then1768selected source tests PASS (same2exactoracle exclusions). The actual96-pad KBAGND diagnostic7 passes at1.6892033503601012e-13 in157.69solver seconds; all341bindings including exactSciPykernel binary and539protected files match, scopecleanupPASS. Budget1/3full,7/24diagnostics. Original180s timeout remains negative evidence. Guardeddocbuild301pages/16s and strictsitePASS, unchangedallowlist. A synthetic scalar-index dtype allocation finding is being narrowed before the next exactrequest; no further productionrun is implied here.


### Final bounded runtime check before the next baseline

Typed-index source59a3a371 preserves exact boundary queries while avoiding the measured full-index temporary allocation; independent review and50focused tests PASS, complete source selection1769PASS with2exact oracle exclusions. At clean execution2eb12a78804e04797c3e9cf0a49307117e8f63e3, diagnostic8 actualKBAGND96unit passes the identical1.6892033503601012e-13 residual in80.48solver seconds, versus157.69s before the typed-query correction.341bindings,539protected files, actual2GiB/no-swap scopes, zero memory events and owned cleanup PASS; sampledpeak1,593,425,920bytes. Budget1/3full and8/24diagnostics consumed. Next publish reviewed source/evidence to staging, then prepare/review and execute a fresh full-baseline request within standing delegated authority. No numerical result is reused against a changed method or HEAD.


## Corrected full baseline and source integration — 2026-10-14 terminal checkpoint

Attempt 5 consumed request `ef0213b3b38f4de23804ad192043b082d8e1b2be3086c5e20e4343afea4052d6` once at frozen execution source `852ffac7f85aff4bb436eb25f7ce993cee48146b`. All 148 units (service 1, reductions 24, driving-point chunks 111, coupled units 12) and 147 reported numerical verdicts PASS. All four nets, three cases and 30 finite states completed at uniform-dielectric depth; three all-return-open cases remain floating, not finite PASS. Maximum driving-point residual is 1.847027216349672e-12, node KCL 4.445863746242618e-11, global KCL 6.063664705315578e-10 and energy error 9.971994768291669e-10 against unchanged 1e-9. The energy result has narrow margin and remains tied to the exact pinned toolchain.

Per-unit shared guard, 180 seconds, 2 GiB/no-swap and serialized execution were unchanged. Hook exit 0 after 7891.043 seconds; maximum ledger unit 93.564 seconds. Independent observations cover 146 scopes, peak 2,082,783,232 bytes, zero memory events and concurrency one. Two short coupled scopes were unsampled; all guard/self-verification receipts remain. All 339 bound inputs, 539 candidate and 550 original protected files match; owned processes/scopes/locks are absent after independently verified cleanup. Checkout freeze ended only after this audit. Budget used: 2/3 full baselines and 8/24 diagnostics. Attempt-4 numerical failure and diagnostic-5 timeout remain preserved.

PR272/PR273 source and Mac evidence were published by provenance-preserving cherry-picks at 852ffac7; both topic PRs are closed, not merged. Issue263 is closed/completed after review and staging incorporation. Combined source tests PASS: 1769 selected, two exact oracle exclusions; 50 focused numerical and 22 browser source tests also pass. Numerical/native work was not repeated for evidence-only publication; current documentation/check receipts and unchanged numerical/browser binding audits are retained with the final report. New oracle/native/retained-artifact jobs are NOT RUN in this campaign, and skipped CI is not PASS.

Complete report: `evidence/e16/campaign-wsl-20261014/result-summary/attempt5-final/engineering.md`. Every evaluated loaded pad exceeds its applicable copper budget in every completed state. Service remains 151 supported / 59 partial / 21 unserved / 194 unmapped; physical source/protection, full-path resistance, GH conductors, capped DRC enumeration and physical qualification remain unresolved. The exact U2314.11/C2342.1 In3 follow-up is prepared, not executed or adopted; preserve the U2314.10 AGND barrel/functional annuli and validate capability before separately admitted native/variant work. KEEP_K1402_INCUMBENT, canonical boards/copper/panel and decision.json remain unchanged. PR260 remains draft/unmerged and issue253 open.

## Selective-annulus source continuation — 2026-10-14

Task-owned topic `topic/e16-selective-annulus`, based on verified integration `5af0e7b6`; no integration/canonical writes. Source fixtures now represent exactly the named U2314.10 AGND via's In3 outer-land omission, retaining the modeled 0.025 mm barrel wall and every other annulus. Full-object/contact bindings and layer-aware clipping/graph/finite fragment consumers fail closed on unsupported edits. Native materialization explicitly refuses this policy: pinned KiCad 10.0.6 has no established durable exact per-layer no-flash encoding. The custom 0.35 mm In3 diameter is a separate negative characterization control, not an accepted substitute. No production candidate, native fixture or changed-geometry numerical execution occurred. See `evidence/e16/selective-annulus-20261014/` for final tests, independent reviews and the exact pending admission packet.

Read-only retained analysis ranks 1536 loaded observations across 302 pads. It demonstrates TP990026's sole F-to-In4 transfer barrel and proposes the exact additional 0.6/0.3 mm via at (141,175) as the next separately scoped resistance experiment. Ideal local barrel term halves 1.405→0.703 mΩ nominal, but 2.891→1.445 mΩ thin remains above the shared 1 mΩ rail allowance; whole-network improvement is unproven. No seven-via or long-B acceptance is claimed. DRC reporting now explicitly separates command/reconciliation/completeness/acceptance/adoption; retained capped findings remain INCOMPLETE.

Recorded KA 196 / KB 486 and 151 supported / 59 partial / 21 unserved / 194 unmapped remain unchanged. Campaign ledger stays 2/3 full and 8/24 diagnostic; no native/numerical unit was consumed. KEEP_K1402_INCUMBENT, accepted copper, fixed panel, main and decision.json unchanged; PR260 remains draft/unmerged and253 open. Source-only success does not establish native/electrical/physical acceptance.

## Resistance attribution source continuation — 2026-10-14

Follow-up branch `topic/e16-resistance-attribution` stacks on PR274 at `a811c2dd`, not on the unassigned shared integration branch. `resistance_attribution.py` accounts for already computed solutions using original union-sheet tiles, UUID/layer barrel intervals and existing distributed termination/wire stamps. It reconciles original operators, currents, class/total energy and work at unchanged tolerances; unit-current E/I² is distinct from simultaneous-load watts. Overlapping sheet members receive no duplicate allocation. Missing identity/detail/scope, unsupported bindings, singular return states and failed reconciliation block results; no output accepts hardware.

TP990026 is a held source land, so the bounded proposal uses it as a transfer mechanism and names KB U7105.4 as the +12V unit-current observation while preserving all three source supports. The exact additional 0.6/0.3 mm via at (141,175) remains a specification only. Real object extraction (B), independent evidence review (C) and separately authorized fresh geometry/native/changed-operator comparison (D) remain distinct gates. No production solve, unpickling, candidate materialization or native execution occurred; no baseline restarted. See `evidence/e16/resistance-attribution-wsl-20261014/` for protocol, synthetic example, independent reviews, exact experiment, actual checks and preservation audit.

Campaign remains terminal at 2/3 full baselines and 8/24 diagnostics. The native fixture remains unadmitted at frozen `b27391de`, request `f8da55c709fa59ba3221806f1c10cc4d25462fe8bf9d8c50acf313b0d3fdf4e3`; separate approval/reservation/qualification are absent. Source consistency is not electrical compliance. Canonical boards/copper/hardware/decision.json unchanged; KEEP_K1402_INCUMBENT, PR260 draft/unmerged and issue253 open.

## Ongoing WSL coordination — 2026-10-14

### Operating agreement and objective

Owner instruction in this WSL session delegates persistent planning, ordinary
in-scope source development, verification, independent technical review and
evidence-based continuation to the local coordinating agent. Reuse this work note
and existing evidence directories; do not create a competing status system.
Inspect evidence, select a bounded useful increment, implement, verify/review,
record the actual result, then select and carry out the next justified increment.
A passed test, commit, pushed draft or completed slice is a checkpoint, not a
reason to return to an external planner. Earlier workflow-only external-planner
handoffs are superseded by this instruction.

Immediate objective: resolve actual E16 signing/delegation ownership with the
user here, then prepare and follow a genuinely admitted complete selected
resource-qualification operation through terminal acceptance, accounting and
cleanup. Qualification success requires independent resource review and a signed
report before preparing a separate fresh production request. Production needs
its own authority and live reservation. The engineering outcome is an honestly
resolved selected diagnostic/Stage C disposition or a specific evidence-backed
failure and next intervention; source readiness alone is not numerical progress.

Ordinary planning/source choices are delegated. Exact-request authorization,
independent signer/trust and review requirements, exclusive reservation, shared
scheduling, resource caps and single-use accounting are not waived. Do not create
keys, signatures, grants or reservations under this coordination instruction.
No merge/rebase/stack integration, canonical geometry/copper or decision.json
change, adoption, native work, global host/dependency/guard change, deployment,
procurement, fabrication, energization or Cloud launch is authorized. Preserve
KEEP_K1402_INCUMBENT and the separate +5V/native-negative-control lanes.

Check durable decisions before asking the owner. Ask only the missing decision,
explain its source and consequences, recommend a concrete resolution and record
the answer here. Do not repeat it without changed scope or facts. A technical
reviewer agent is not an independent signing authority. Continue other useful
authorized work while a lane is blocked; do not invent work or rerun unchanged
checks merely to avoid the external boundary.

Stop only for completion of the authorized objective, an indispensable owner
decision/capability, exhausted limits, unresolved ownership/safety/accounting/
cleanup, or a session boundary. At a boundary, retain enough evidence and exact
next action for replacement WSL recovery. Never claim unstarted work is running
or promise unattended continuation. Failures retain their evidence; no automatic
replay, cap increase or weakened acceptance.

### Refreshed ownership, evidence and claim state

- Reused clean worktree `/home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-attribution-executor`,
  branch `topic/e16-attribution-executor`, local/refreshed remote head
  `781a028845cf20d991a79dbdfe96d1eed9546b97` before this documentation increment.
  The commit containing this section is its successor; recover the actual current
  head with `git rev-parse HEAD` and compare PR #277 before any packet preparation.
  Worktree records, processes and the `osc:0.0` tmux transcript identify the current
  local coordination session. No competing executor or E16 operation was observed.
  This is continuation ownership, not integration ownership or a resource reservation.
- PR #277 remains open/draft against `topic/e16-attribution-reconstruction` at
  `dec36940e2691e384b9d8d499675761078d64308`. PR #260 remains open/draft at
  `5af0e7b675123b40367078ee605a1355bae49a62`; #253 and epic #242 remain open.
  Main remains `65cefd41fc39e064d38319115ad96016a1c6b71c`.
- Reviewed containment implementation is complete at `781a028`:
  [process/resource contract and real tiny fixtures](evidence/e16/attribution-admission-wsl-20261014/containment/README.md),
  [independent review](evidence/e16/attribution-admission-wsl-20261014/containment/review.md),
  [exact retained checks](evidence/e16/attribution-admission-wsl-20261014/containment/checks/summary.json).
  Historical 70 focused tests and host-mechanism evidence are not a qualification.
  No demonstrated containment defect justifies repeating that increment.
- Numerical [resource plan](evidence/e16/attribution-admission-wsl-20261014/resource-plan.md)
  remains applicable with its explicit containment supersession. Fixed caps:
  180 seconds from actual guard entry, 2 GiB aggregate, zero operation swap,
  64 MiB aggregate output, one diagnostic/unit/selected RHS/attempt;
  worker 1216 MiB. Root 1984 MiB plus external 64 MiB reserve remains unqualified
  for the full operation, including attributable shared-service/bootstrap costs.
- Original input bindings remain in the reviewed [inventory](evidence/e16/attribution-reconstruction-wsl-20261014/resource-inventory.json),
  SHA-256 `8cfcf5fac5bd749dcd58313b4df8eb1a9080723a5c5d34d80c548098c2d60b18`.
  Exact experiment/identities/tolerances are in the [owner handoff](evidence/e16/attribution-admission-wsl-20261014/owner-handoff.md).
  All original inputs and prior negative evidence are preserved; no numerical
  artifact was opened/deserialized in this coordination increment.
- Live canonical accounting file is
  `/home/takazudo/.cache/zudo-e16-runs/campaign-20261014/campaign-note.json`, SHA-256
  `94aafb6d13f754fdbde718a5b44c5071d946897e798a8eebf1cd4b86c0731ffb`.
  Actual use: 2/3 baselines, 8/24 diagnostics; remaining allowance 1 and 16,
  respectively, is not execution authorization. Attempt 5 is terminal,
  `live_owned_work=false`; this increment consumes zero. Preserve this ledger;
  use only the existing accounting owner/path for future claims.
- `systemctl --user list-units 'e16-*' --all` reports zero loaded units.
  Fixed trust `/home/takazudo/.config/zudo-e16/attribution.allowed_signers` and
  production state `/home/takazudo/.local/state/zudo-e16-attribution` are absent.
  No active claim, request freeze, numerical process or task cleanup is pending.
  Qualification/production request digests, run IDs and artifact IDs remain null.
  Neither operation admitted; Stage C NOT RUN; no via or board acceptance.

### Pending owner decision and next local increment

Current [signing requirements and actual commands](evidence/e16/attribution-admission-wsl-20261014/containment/signing.md)
require externally controlled trust and separately signed operator/controller/
resource-reviewer messages. Actual people and designated public keys are not
recorded. The old campaign's standing delegation in its retained authority source
does not satisfy `attribution_admission.verify_for_host()` for this new selected
operation; that function explicitly rejects substitution of old campaign delegation.

Pending question in this WSL session: is the user the sole actual authority, or
do separate human signers exist? Recommendation if sole owner: prepare a specific
owner-controlled policy amendment, preserving owner key custody, separate exact
decisions and independent technical review; obtain approval before applying it.
This recommendation is **not approved policy**, a key designation or run approval.
Do not assume unrelated existing SSH keys or fictional operators. Record the
answer here, prepare the concrete arrangement for review, and continue locally.

Before preparing any execution packet, finish/review/commit all instruction or
source changes and refresh the clean final head. Then, only after genuine trust
setup is resolved, use the existing compiler from the source directory (not
`evidence/e16`):

```sh
cd /home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-attribution-executor
git fetch origin
git status --short --branch
git rev-parse HEAD
gh pr view 277 --json state,isDraft,headRefName,headRefOid,baseRefName
cd design/partition/core-split/candidates/planning/joined-feed-construction-v2
```

The signing handoff supplies the exact `describe`, `seal-qualification`, signing
and verification commands with genuinely assigned fresh paths. Do not seal now:
the trust file is absent and policy/identity decisions are pending. No placeholder
packet is executable. Once sealed, freeze its bound source; a change invalidates
the packet and requires fresh preparation/review, never digest substitution.

After actual qualification authorization and reservation pass existing gates,
use the existing `attribution_host.py --launch` interface and follow the service
to completion. Launch exit zero is submission only. Inspect `accepted_result`,
immutable terminal journal, envelope receipt, exact durable shared-guard row,
output inventory, campaign accounting and owned cleanup together. A claimed
qualification consumes one diagnostic even on failure. Incomplete accounting or
cleanup requires reconciliation before any new request. On success obtain the
required independent resource review/signature, then separately prepare and admit
production. No external planning prompt is required at either transition.

### Coordination increment verification

Pre/post `pnpm circuit:check` PASS (manual inventory: 68 lines, zero declared
placements; no schematic/placement binding; pin-asset check performed).
`git diff --check`, added local link resolution and unchanged ledger digest PASS.
Only AGENTS.md and this work note change; numerical/containment source, original
inputs, campaign ledger, protected boards/copper and decision.json are untouched.
No unchanged source suite, host fixture, numerical/native workload, aggregate
regeneration or broad build was repeated; those are NOT RUN in this documentation
increment. CI is intentionally skipped, not passed.

Independent read-only review by `/root/coordination_review`: PASS, no blocking
findings. Code enforces separate principals/namespaces/signatures, not distinct
humans or key fingerprints; that fact does not authorize role consolidation.
The reviewer verified the operating scope, pending policy decision and recovery
instructions, and supplied no signing authority. No execution packet was created.


## Owner decision: single-owner local delegation — 2026-10-14

**Signing ownership resolved.** Takazudo expressly selects single-owner, locally
delegated E16 development authorization. The [verbatim decision](evidence/e16/attribution-admission-wsl-20261014/owner-decision-20261014.txt)
is bound by SHA-256 `dd57d82b5c062613fe139ae68c2cf12c303f3c3df30bbe5c276c968f8dad25ec`.
It supersedes the pending question and earlier bans on dedicated local signing
setup, external human signers and personal per-digest approval. It does not apply
retroactively. The WSL coordinator is the operator/controller delegate; real
separate technical review remains required. A locally delegated resource signature
attests that retained review; it is not independent external approval.

Authorized: dedicated E16-only keys/trust under this user's permissions, exact
request preparation/signing/verification, complete real-data qualification,
evidence-backed corrections and bounded diagnostics, and selected numerical
production attribution only after successful qualification and actual separate
technical review. Access original retained inputs only through reviewed guarded
verification/execution. No additional full baseline. Preserve all 180s/2GiB/
zero-swap/64MiB caps, 1216MiB worker, original identities/scope/tolerances, complete
accounting, single-use state, live exclusive locks/shared scheduling and cleanup.
No host/privilege changes, merges/integration, canonical geometry/copper adoption,
Stage D, hardware/deployment actions or acceptance claims.

Private signing bytes must stay outside Git/reports/artifacts/logs with restrictive
permissions; do not inspect unrelated credentials or overwrite existing key/trust
ownership. Signature validation stays real. New requests and grants bind the
exact owner-delegation policy; future digests are locally authorized by delegation,
not personally reviewed by Takazudo. The updated [signing procedure](evidence/e16/attribution-admission-wsl-20261014/containment/signing.md)
records the actual schema and separate-review requirement.

Next increment: finish minimal policy/source tests and independent review, provision
dedicated trust, commit the clean source, compile a fresh qualification packet,
review/sign its exact grants and enter the existing guarded path. Follow actual
terminal receipts, original ledger and cleanup. No packet is sealed while source
is changing. A failure remains charged and requires diagnosis before a fresh
eligible attempt. Do not ask again who owns authorization or request another plan.


### Delegation implementation and setup checkpoint

The minimal source change and dedicated local setup have separate technical
[review PASS](evidence/e16/attribution-admission-wsl-20261014/delegation-review.md);
95 focused tests and pre/post circuit checks PASS. The initial test run exposed
one old operation-digest fixture missing the new policy field; its fixture was
updated, and the complete focused selection passed. Numerical code/containment
and original inputs remain unchanged. No baseline or diagnostic consumed yet.
The actual [public trust identity and setup modes](evidence/e16/attribution-admission-wsl-20261014/delegation-setup.json)
are retained; private material is outside Git/evidence. Signing-owner blocker is
cleared; combined qualification and production admission remain unproved.

Source freeze starts only after this commit. Prepare fresh absolute local packet
paths under `~/.cache/zudo-e16-runs/`, run the existing compiler `describe` and
`seal-qualification`, retain independent exact-packet review, and sign real grant
JSONs containing the request's exact authorization_policy plus all existing
request/kind/run/operation/limits/host/ledger/time bindings. Local grant issuance
is delegated authority, not a personal owner digest review. Follow the async
service through actual terminal evidence before another increment. Do not edit
bound source while a packet is live.


### First admitted qualification: terminal startup failure and diagnosed correction

At clean frozen `c0b3197b550f9fd8050d978ca2356cd66aed5940`, genuine locally
delegated grants and exact-packet technical review admitted qualification request
`50bb226328d0addf41be8854611180cfda95c9da1328ef8e935fb8806ad75ddf`, run
`fdde325e32a54f56b08b8c926b2785e1`. Packet directory:
`~/.cache/zudo-e16-runs/attribution-qualification-2wvkvrl8/`; exact request and
description remain there. Output:
`~/.cache/zudo-e16-runs/attribution-fdde325e32a54f56b08b8c926b2785e1/`.
[Index, signed grants, failure log and terminal evidence](evidence/e16/attribution-admission-wsl-20261014/qualification-attempt1/index.json)
and [independent audit](evidence/e16/attribution-admission-wsl-20261014/qualification-attempt1/review.md)
are retained. The operation was claimed and failed before original decoding:
inside the private user namespace, ancestor `/proc/.../fd/200` access was denied.
The unchanged shared guard intentionally closes fd200 for its workload, so simple
inheritance cannot repair the proof. No worker-start or numerical result exists.

Ledger now2/3 baselines and9/24 diagnostics (15 diagnostics remain, zero additional
baselines authorized); live_owned_work=false and exactly one terminal charge.
Independent integrity/cleanup audit PASS; all actual resources released. Peak
50,933,760 bytes,1.278683 seconds, swap0; this failure does not qualify the pipeline.
Historical incomplete output manifest is preserved; raw log is separately indexed.
No source freeze remains for this consumed request. Do not replay it.

The narrowly diagnosed correction uses a bounded socketpair/SCM_RIGHTS transfer
from the envelope's actual pidfd-acquired guard OFD, then explicit descriptor
inheritance through namespace and worker. Peer credentials, exact request/run and
actual guard PID/start are checked. Kernel fdinfo must show an exclusive whole-file
flock on the expected inode/device; a fresh open of that inode is insufficient.
Guard/controller ancestry and lock contention checks remain. No shared guard,
host permissions, numerical source or caps change. Surviving negative logs now
bind into the failure journal after owned cleanup, without upgrading failure.

A serialized real fixture at192MiB/zero-swap/6s+1s/48tasks/1MiBtmpfs/<64KiBoutput
proved actual transfer, namespace+nestedworker proof, reopened-descriptor rejection,
retention and complete cleanup. Peak79,880,192 bytes, elapsed0.394292 seconds,
zero swap, noOOM. [Raw fixture command/result](evidence/e16/attribution-admission-wsl-20261014/containment/checks/namespace-lock-transfer.txt).
107 focused source/crypto/host/supervisor tests PASS; fixture authority remains
separate from the real local delegation. Next: final independent source review,
commit corrected bindings, seal/review/sign a fresh qualification and follow its
actual terminal evidence. Production remains unprepared/unadmitted; Stage C NOT RUN.


### Second qualification: Git bootstrap failure, bounded command correction

Fresh reviewed/signed request`ba4ed340fff33b524c15082f0081460ee1d113eb095555246f9335e74be1f6ba`,
run`19650aca554a4f12b9134a6d77a75d78`, source`0eccf0667f07dc6f96c21d4415e2036e68295d40`
passed actual namespace lock custody, then failed full admission before original
reads/worker startup. [Exact packet/output/terminal index](evidence/e16/attribution-admission-wsl-20261014/qualification-attempt2/index.json)
and [independent terminal review plus diagnosis](evidence/e16/attribution-admission-wsl-20261014/qualification-attempt2/review.md)
are retained. Local packet directory`~/.cache/zudo-e16-runs/attribution-qualification-ewjg3z87/`.
No original inputs changed; immutable first/second journals preserved.

The clean checkout's Git status command failed under the unchanged bootstrap
thread/address-space bounds. A tiny actual namespace fixture captured exit128
and threaded-lstat allocation failure. Explicit per-command serial Git options
passed under the same limits; no global/repository config change or gate removal.
The source now distinguishes commandfailure fromdirtycheckout.108focusedtestsPASS;
real diagnostic fixture transcripts preserve both outcomes and ownedcleanup.

Budget now2/3 baselines,10/24diagnostics;14diagnostics remain, no additional baseline
permitted. Both operations terminal, live_owned_work=false, cleanup/accounting
independentlyPASS. Secondpeak56,426,496B/1.358537s/zero-swap. No qualification or
production accepted; StageCNOTRUN. Next: independently review/commit the narrow
Git correction, then prepare a freshly bound qualification; never replay either
consumed request or alter its original retained receipts.


### Third qualification reaches original operator and fails exact reciprocity

Request`29202f704140afc2797ee1d0c2d13507d3892d275a6c0b7129f4477f5cd0de53`,
run`43ecd963144648ac9e275db550baf19e`, clean source
`5c1fde39b2d9696bcf3ed646341b5bef6b4753ff`; exact packet remains in
`~/.cache/zudo-e16-runs/attribution-qualification-he4qwbk6/`.
[Retained output/index](evidence/e16/attribution-admission-wsl-20261014/qualification-attempt3/index.json)
and [independent audit/diagnosis](evidence/e16/attribution-admission-wsl-20261014/qualification-attempt3/review.md)
record actual authenticated original-input verification/decoding and worker startup.
The KA free operator is not bit-exact symmetric as required by the current SPD
certificate. No selected solve/component accounting or Stage C result follows.

Actual rootpeak1,163,087,872B,workerpeak1,046,597,632B; envelope11.318091s and
separate guardraw14s; zero swap/noOOM. Supervisor64MiB maxevents339 reflect real
limit pressure. Qualification remains failed, not merely an absent signature.
Accounting/cleanup independentlyPASS: three terminalcharges, no livework/resources,
budget2/3baseline11/24diagnostics (13diagnostics remaining; no additional baseline).
Freeze ended after terminal audit; this consumed identity cannot be replayed.

Next justified increment is bounded exact mismatch characterization, not another
unchanged retry. Source diagnostic keeps rejection and original operator bytes,
limits output to four exact value witnesses and metadata, and avoids another full
floating sparse difference.136focusedtestsPASS. After review/commit, prepare an
explicitly diagnostic fresh qualification-kind request under existing local
delegation; its claim would consume diagnostic12. Do not sign RESOURCE_QUALIFIED
or prepare production from that expected negative result. Choose any subsequent
certificate correction only from the actual retained evidence and separate proof
review, without changing solver/refinement, tolerances or physical scope.


### Fourth diagnostic and reviewed original-operator certificate correction

Current completed request`6bd7c5d97f30863ed7d9c6ce39c593a53193474555c8dc6304722be25a531009`,
run`f068281e8fc349ce804cb3f7a804174f`, source`b5b47f90fca893c6f51b5057ee53d97ecc85758a`.
[Exact retained identities and terminal evidence](evidence/e16/attribution-admission-wsl-20261014/qualification-attempt4/index.json),
[independent cleanup/accounting audit](evidence/e16/attribution-admission-wsl-20261014/qualification-attempt4/review.md).
Packet remains`~/.cache/zudo-e16-runs/attribution-qualification-t_7i82on/`.
Actual KA order1513837, storednnz7818329, mismatchentries15252. Four bounded
hexadecimal witnesses differ by1–2ULP; no global skew bound or SPD follows.
Rootpeak845373440B,elapsed6.936201578s,zero swap/noOOM; four terminal charges,
2/3 baselines and12/24 diagnostics,12 diagnostics remain,zero additional baseline
allowed. LedgerSHAe1edfda81de7006f5c53a38a6ca1f11fd73f447222e29f10ed628e898b0459ea.
No live work; unit/root/locks released; six retained outputs6272B match journals.
Stage C NOT RUN, qualificationNOT_QUALIFIED,productionNOT_ADMITTED.

An independently [reviewed reference coercivity proof](evidence/e16/attribution-admission-wsl-20261014/reference-certificate/review.md)
now addresses actual asymmetry without changing the original numerical solve,
RHS, matrix bytes or tolerances. A conservative global inverse bound uses only
analysis-reference H positivity; original SPD is not asserted.140focusedtestsPASS.
Memory feasibility remains unproven. Constant-auxiliary reference preflight counts
initial structure before Python dictionaries and preserves the existing4M cap.

Next executable action after this clean commit: compile a NEW description and
qualification request with existing attribution_request.py, obtain exact-packet
technical review, issue delegated exact grants, verify metadata then run existing
attribution_host.py --launch under genuine live admission. This FULL conditional
qualification first tests reference structure capacity, then continues the complete
pipeline if preflight passes. A capfailure reports only the first exceeding prefix.
Dictionary/fill/runtime failure remains possible, charged and terminally reviewed.
No new numerical baseline, production request or RESOURCE_QUALIFIED report exists.
Never replay prior identities or change bound source while this next packet is live.


### Fifth qualification: actual certificate storage blocker; source-only investigation

Clean source`18147148ef72511109e674430db1c2b53f650355`, request
`6dc8a01d5e3c8827eac8f8b5b9c98a2fd29f6c796b7b1501c1fb5900574e8728`,
run`aa824d1cecf9483592979343a219a0fb`, operation
`c36ada446d556faffdc7066075de7bf6034a586130c0cc3f3a02284f47355310`.
[Retained failure/index](evidence/e16/attribution-admission-wsl-20261014/qualification-attempt5/index.json)
and [independent complete audit](evidence/e16/attribution-admission-wsl-20261014/qualification-attempt5/review.md).
Original packet`~/.cache/zudo-e16-runs/attribution-qualification-vdjgr_6v/`.
Preflight count4000002 exceeded unchanged4M cap before any certificate row allocation.
This is a prefix lowerbound, not the wholematrix count. Rootpeak904990720B,
elapsed14.465692866s,zerooperation swap/noOOM; complete cleanup and durableguardFAIL.
Ledger now2/3baselines13/24diagnostics,11diagnostics remain,zero newbaselinepermission,
SHAa84cd8c3532e9df448ad020600eeaad637961939d5100d1986f76e0397710df6.
Five terminalcharges/statusINCOMPLETE,livefalse; sourcefreezeended.539topic/550original
protected files rechecked with no differences; originalsource/decision preserved.

No unchanged retry. The independently recommended next source increment is a tiny
lazy/frontier interval LDL prototype preserving exact arithmetic/order and counting
all simultaneously live updated entries, pivotrows and retained inverse-bound
factors. It changes storage lifetimes, not the4M cap. Prototype path under this
same worktree:`__inbox/e16-frontier/repro.py` (ignored, no original inputs).
Do not claim fit from it; full original fill,20Mupdates,1216MiB and180s remain gates.
Stage C NOT RUN; qualificationNOT_QUALIFIED;productionNOT_ADMITTED.


### Reviewed lazy certificate storage correction

[Proof, prototype findings, resource accounting and checks](evidence/e16/attribution-admission-wsl-20261014/frontier-certificate/review.md)
record the evidence-backed correction to attempt5. Original interval arithmetic,
pivot order and all retained inverse-bound factors remain; only row lifetimes
change. All live entries/factors stay under4M with pre-insertion checks, and the
same Work preserves20Mupdates acrossboards. Explicit storagebinding requires a
fresh packet. A prototype aliasfinding and canonical-transpose defect were fixed;
actual-object lifetime tests and147focusedtestsPASS. Originalsolve/RHS/tolerances,
sharedguard/hostcaps, campaign state and canonicalgeometry remain unchanged.

Next locally owned step: after cleancommit and final resource review, use the
existing compiler to describe/seal a fresh FULL qualification. Obtain exact-packet
technical review and issue delegated exact grants; verify then existing guarded
launch. This tests original lazy frontier/factor storage plus the entire remaining
pipeline, not just a count. RetainedCSR lifetime and accumulatedfactors may still
fail the unchangedworker/time/fill/interval gates. No sourcechanges whilelive;
follow complete terminalaccounting/cleanup and diagnose anyfailure beforeanother
fresh request. No RESOURCE_QUALIFIED or production authority exists yet.


### Sixth qualification: storage progresses; arithmetic budget is now the blocker

Clean source`cba807a8f61bea7eed6c789f400039bf4f55b855`, request
`8bd9a54704a2c3fb608cfa4c262305857c92e1575ebc9275a3c5d3834c5c0e7d`,
run`0c94c1920a7f447d974e7101b9176e10`, operation
`9894cf70c0b26d21f744db02e21001587143d61a9b25250fac448a2c0f149c25`.
[Retained evidence/index](evidence/e16/attribution-admission-wsl-20261014/qualification-attempt6/index.json)
and [independent audit](evidence/e16/attribution-admission-wsl-20261014/qualification-attempt6/review.md).
Exactpacket`~/.cache/zudo-e16-runs/attribution-qualification-jcet9zqn/`.
KAfrontiercertification rejected requestedupdate20000001 against unchanged20M.
Rootpeak845197312B,envelope60.5104132865s,separateguardraw64s,zero swap/noOOM.
Allsixterminalcharges/retainedhashes/journals/guard agree; ownedresourcesgone,
locksfree,livefalse. Ledger2/3baselines14/24diagnostics,10diagnosticsremaining,
SHA6ba3f0b11df4d810d7123bcd43cf843ba91b5a7e5e36ecca40bceac310adeb50.
No additionalbaselinepermission. Sourcefreezeended afteractualterminalaudit.

A missing environment value in a mocked boundarytest was repaired only after
terminalaudit.164focusedtests nowpass without fixtureenvironment overrides.
No realauthority bypass or originalinput mutation. The next local source-only
investigation is a single deterministic symmetric analysis ordering, tested with
B permuted consistently and originalsolverMMD/refinement unchanged. Tiny RCM
prototype demonstrates both reductions and a worse smallgridcase; it is no
resourceguarantee. No newrealrequest before reviewedcorrectiveimplementation.
StageCNOTRUN,qualificationNOT_QUALIFIED,productionNOT_ADMITTED.


### Reviewed fixed analysis ordering correction

[Proof, actual prototype evidence, resource overlap and independent reviews](evidence/e16/attribution-admission-wsl-20261014/ordered-certificate/review.md)
support one fixed analysis-only RCM ordering, with both freeoperator andB permuted,
D/terminalorder unchanged and originalmatrix identity preserved. Only ownedanalysis
copies change; originalsolverMMD/refinement/RHS/tolerances/physicalscope remain.
No search/fallback, capincrease or automaticretry. Actualpermutationhash and
newrequestorderingcontract are bound; previousrequests cannotselectit.
170focusedtestsPASS withoutenv overrides; circuit/diffPASS; independentmath and
resource/admissionreviewsPASS. Source-onlyprototypehasbothbetterandworse cases,
so originalresourcefit is unknown; copy/graph/B/transposeoverlaps are explicit.

Next executable action by this WSLdelegate: cleancommit, newcompilerdescription
and qualificationpacket, separate exactpacketreview, genuine delegatedgrants,
metadataverification thenexistingguardedlaunch. Fullconditionalqualification may
stillfailfill/20Mupdates/intervalresolution/memory/deadline; followterminaljournal,
ledger,guardreceipt,retention andcleanup before changingboundsource or replanning.
Currently14/24diagnostics used,10remain;2/3baselineunchanged/noadditionalbaseline.
No RESOURCE_QUALIFIED report or productionrequest exists; StageCNOTRUN.


### Seventh qualification: technical acceptance unresolved; numerical attempts stopped

Clean executedsource`5aec693549a9e380d7e7832a430f5294dacbaf05`, request
`3d42c2dc48e1b44c743626231437683ee4c25be50bc0ed6bd4b5edf29ff94b9d`,
run`6ba68bb77ec944e0963ad6524570c23d`, operation
`60fcd4dc1f630d7877d09239f06321c73a030683d40e7e50bcc9c75d1dcc6a78`.
[Exactretainedindex](evidence/e16/attribution-admission-wsl-20261014/qualification-attempt7/index.json)
and [independentterminal/acceptancereview](evidence/e16/attribution-admission-wsl-20261014/qualification-attempt7/review.md).
Packet`~/.cache/zudo-e16-runs/attribution-qualification-4o576ztz/`; output
`~/.cache/zudo-e16-runs/attribution-6ba68bb77ec944e0963ad6524570c23d/`.
FixedRCMalso exceeded20M beforecompletingKA; actualpermutationhashretained.
Rootpeak844124160B/envelope61.0558727597s/guardraw62s,zero swap/noOOM.
Allsevencharges/retention/immutablejournals/durableguardfailure agree; complete
ownedcleanup,unit/root/processes/locksabsent,livefalse. Ledger15/24diagnostics,
2/3baselines,9diagnosticsremain,zeroadditionalbaselinepermission;
SHA533ca512fc06ae6742e6e02dce3cc1a8aee83ec49fc13ebabf691a6b0c4cc4f5.
No qualificationreport or productionrequest exists. StageCNOTRUN.

Signingownership is RESOLVED: Takazudo owns authorization and this WSLcoordinator
is the recordeddelegate. Currentblocker is a rigorouscertificate within20Mwork,
not missingapproval or hostswap. Do not ask again forsigningownership/digestapproval.
Do not issueanotherrealpacket forunchangedretry or blindthirdordering. The latest
request is consumed, notlive; sourcefreezeended afterindependentterminalaudit.
Currentrealresourceacceptance remainsNOT_QUALIFIED;productionNOT_ADMITTED.

The next locally owned lane is a short source-only mathematicalfeasibility study:
can originalconstruction provide quantitativecoercivity for the completejoined
symmetricreference, including groundedKA/floatingKB/wires, allstoredrounding and
ausefulinversebound, with exhaustivelyverifiablehypotheses underexistingcaps?
Do not buildanotherchecker before that theorem/costargument exists. Existing
aggregatewitnesses alone cannot provide the missingmargin/roundingbound. Separate
math/resource reviewers require that evidence beforeanothercampaignclaim.


<a id="e16-current-checkpoint"></a>

### Recoverable stopping checkpoint — actual technical acceptance boundary

The [construction feasibility study](evidence/e16/attribution-admission-wsl-20261014/qualification-attempt7/feasibility-review.md)
is complete. It found a conditional theorem but no applicable quantitative
certificate: original retained tile aggregates lack bound element-level witnesses;
no usable grounding margin alpha or exhaustive stored-coefficient error epsilon
is established. Distributed terminations cannot be replaced by independent edges.
No verification-cost argument fits the unchanged full operation budget yet.
This is a real technical acceptance blocker, not an unresolved signer/owner choice.
No further numerical request is prepared or eligible at this checkpoint.

**Current objective:** independently qualify the complete existing selected
attribution pipeline, then separately admit production only after qualification
and actual technical review. Completion still requires full numerical/output gates,
original mesh/accounting passes, durable terminal/guard agreement and owned cleanup.
Qualification remains NOT_QUALIFIED; production NOT_PREPARED/NOT_ADMITTED/NOT_RUN;
Stage C NOT RUN. KEEP_K1402_INCUMBENT and all hardware acceptance gates stay open.

**Ownership and exact state:** continue this existing worktree
`/home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-attribution-executor`,
branch `topic/e16-attribution-executor`, draft PR277. Latest executed source is
`5aec693549a9e380d7e7832a430f5294dacbaf05`; subsequent evidence commits do not
retroactively rebind that consumed request. Obtain the current evidence HEAD with
`git rev-parse HEAD` and refresh remote/worktree ownership before any future edit.
Base remains reconstruction `dec36940e2691e384b9d8d499675761078d64308`; no integration
ownership. Main, PR260 draft/unmerged and issue253 open remain preserved.

**Actual verification:**170 focused source/crypto/interval/lifecycle tests passed
without environment overrides; pre/post circuit checks and independent source,
mathematics, resource, exact-packet and terminal reviews are retained. Seven real
qualification-kind claims since the owner decision all ended INCOMPLETE. Latest
ledger is15/24 diagnostics and2/3 baselines, delta+7 diagnostics/+0 baselines from
the pre-delegation checkpoint. Nine diagnostics remain; no additional baseline is
authorized. Live work is false; no operation-owned unit, process, cgroup or lock
remains. Private signing bytes remain outside Git/reports/artifacts/logs; the current owner
delegation and numerical limits are retained. Native/aggregate checks and CI remain NOT RUN or
skipped under the narrow authorization, never reported as passed.

**Next local action, owned by this coordinator:** review the five explicit witness
and cost gaps in feasibility-review.md and derive a concrete proof-and-witness
proposal for the exact stored operator before writing an alternative certificate.
It must supply a usable positive alpha-epsilon and bounded exhaustive verification;
the present evidence cannot establish either. Obtain genuine separate technical
review of that proposal. Do not seal/sign another qualification merely to test an
unreviewed ordering or repeat the known20M failure. A future justified correction
requires a clean committed source, fresh compiler packet, actual technical review,
delegated exact signatures and live admission. Production remains a separate step.
No outside ChatGPT plan or repeat signing-owner answer is needed.

Source-only local verification command, if a new change justifies rerunning it:

```sh
cd /home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-attribution-executor/design/partition/core-split/candidates/planning/joined-feed-construction-v2
/home/takazudo/.cache/zudo-e16-numerical-venv/bin/python -B -m unittest test_attribution_executor test_attribution_resolution test_attribution_ordering test_attribution_admission test_attribution_host test_attribution_worker test_attribution_containment test_attribution_supervisor test_numerical_unit_guard test_attribution_interval_oracle test_attribution_boundary_review test_attribution_lifecycle -q
```

All exact packet/output/artifact locators, grants, claim journals, negative worker
receipts and cleanup evidence are indexed in qualification-attempt1 through7.
Do not replay those identities. Source-only prototypes remain ignored at
`__inbox/e16-frontier/repro.py` and `__inbox/e16-frontier/ordering.py`; permanent
regressions and review conclusions are committed. No job is left running and no
unattended continuation is promised at this stopping checkpoint.
