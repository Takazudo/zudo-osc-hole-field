# Joined feed construction v2

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
