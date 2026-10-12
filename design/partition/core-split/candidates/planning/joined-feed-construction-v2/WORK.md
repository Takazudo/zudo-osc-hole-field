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
