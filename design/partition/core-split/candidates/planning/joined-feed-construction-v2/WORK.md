# Joined feed construction v2

Construct one disposable load-side candidate using the existing six-wire interface and three AGND returns. Materialize uniquely identified terminals, inclined solder contacts, board-side access, insulation and a complete carrier. Source design and collision evidence are distinct from physical qualification and native acceptance.

Input HEAD: `8b2384a927fbd3c58669614fb40c7e722b78974e`. No original copper, fixed panel, non-core poses, harness identities or canonical boards change. No native run, F3 placement trial, adoption or merge is authorized by this packet.

The latest parent instruction supersedes the previous incomplete-source stop: ordinary unconstructed work must be implemented, not presented as an external blocker. Independent electrical and mechanical design reviews precede the construction. Repository precheck passed.


## V15 (historical; exact inputs unrecoverable)

V15 left KA 58 / KB 217 unresolved physical pads (110 direct, 165 supplemental) using staged micro/buried vias. Its receipts remain valid records, but their inputs were never retained: the normalized boards (`/tmp/feed-v2-K?-filtered-v15-supp-*.json`) and the normalize/clip/access helper (`/tmp/feed-v2-board-access.py`, SHA-256 `18b4daeb…`) existed only in a Codex Cloud `/tmp`. A hash search of all 5,912 historical py/json/gz blobs on every branch, plus Actions artifacts and releases, found none of them. The rejected v9 epoch, its 76-pad subset and the V14/V15 staged model stay negative evidence. E16 counts are a new denominator and are not comparable to V15.

## E16 — current epoch (2026-10-12)

Branch `integration/epic-242-core-routing`, parent `7e07b979`. Canonical `boards/` and `design/grid/placements.lock.json` are untouched. Native calls: 0. Electrical acceptance, manufacturing qualification and adoption: false.

**Construction.** `evidence/e16-construction-contract.json` records the published HDI capability check. The staged model's 0.05 mm dielectric under 2 oz foils, its 2 oz microvia layers, and the 0.075/0.15 mm fixture microvia contradict published limits (PCBWay, JLCPCB, Würth, NCAB), so E16 uses no staged vias. Access uses 0.3/0.6 mm through vias (filled and capped only for via-in-pad), 0.25/0.2 mm face traces and 0.25 mm clearances, all within published and board rules. Plating minimum and cap thickness are unpublished; finite barrel bounds should use 18 µm.

**Chain.** `construct.py` (replays candidate05 byte-for-byte: KA `ba6202f8…`, KB `05ce8d2b…`) → `normalize_board.py` (rail-pad set must equal the 3,849 reviewed ports; direct loads from `mandatory-physical-ports-review.json`: KA 1,031, KB 1,490) → `evaluate_access.py` with `clip_sheets.py` (caps → clip → graph → census) → `construct_access.py` rounds → full re-evaluation after every round. `replay_e16.sh PYTHON OUTDIR` rebuilds everything from tracked files. Hashes, commands, times and memory are in `evidence/e16/index.json`.

| Round | Method | KA unresolved (direct / supp) | KB unresolved (direct / supp) | Newly disconnected |
| --- | --- | --- | --- | --- |
| base | no access | 1,557 (1,026 / 531) | 2,275 (1,490 / 785) | — |
| r1 | first legal via site on a 0.25 mm grid within 2 mm, straight trace | 425 (328 / 97) | 816 (583 / 233) | 0 / 0 |
| r2 | face maze route to feed-connected same-net copper | 293 (213 / 80) | 624 (451 / 173) | 0 / 0 |
| r3 | maze route to a new legal via site, with cumulative sheet-severance guard | 226 (166 / 60) | 521 (372 / 149) | 0 / 0 |

Representative direct load: KA `U1107` pad 11 (AGND, B.Cu, pad `0ab0435b…`). Every via site within 2 mm was blocked by U1105/U1107 face pads and signal vias, and the straight path to feed-connected pin 9 crossed no-connect pin 10. A 3-segment 0.25 mm route (2.34 mm) around pin 10's outer tip closed it in the full KA census (425 → 424 unresolved, direct 328 → 327, 0 newly disconnected). r2 applies the same method to every residual.

**Remaining blockers (r3 reasons).** Most residuals have no feed-connected same-net copper and no legal via site in the 3 mm window (KA 81, KB 349). The rest have no clear path (dense IC pin rows), or their target is blocked. A first r3 attempt without the guard severed one -12V (KA) and one +5V (KB, 19 pads) sheet neck; the cumulative guard removed that regression.

**Not done.** Signed-load finite electrical proof (contact/cap/barrel/sheet/wire, separate AGND return incidences) is not started for E16. No native fill/DRC of the E16 access copper. KEEP_K1402_INCUMBENT stands.

**Next continuation.** Re-run `construct_access.py --method route --planes …` on the r3 output: pads closed in r3 become new targets. Then add a two-face option (route on the opposite face through an existing same-net through-hole or via) for the pin-row residuals. After that, start the finite network on the E16 copper.
