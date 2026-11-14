# OSC A/B readiness matrix (2026-10-31)

**Status vocabulary:** PASS / FAIL / BLOCKED / NOT RUN (with reason) / UNKNOWN. Every schematic
and PCB here is an unvalidated draft. Nothing is validated, qualified or released, and this
file creates no fabrication or order output.

- **A** means the design is complete.
- **B** means the technical conditions for a prototype order are met.

Evidence is at commit `25c60c40` unless a row names this commit. The "Needs" column uses
**U** (user decision), **N** (native KiCad run), **P** (physical work), **E** (evidence or
access) and **R** (independent review).

## A: design complete. Not met: 6 FAIL, 2 BLOCKED, 2 NOT RUN, 1 UNKNOWN

| # | Gate | Status | Evidence | Blocker | Needs |
| --- | --- | --- | --- | --- | --- |
| A1 | Schematic generated from source, no drift | PASS | `regen-all.sh --check` exit 0 at 25c60c40 (phase-11 run); `design/reports/master-audit.json` | — | — |
| A2 | Schematic design content complete | FAIL | `design/power/proposals-59/README.md` | #59 protection is not in the schematic. P59-A rev 2 is awaiting adoption. P59-B/C are held as records, so output injection while off (R-INJ) and the ADG enable gap (R-ADG) stay open | U |
| A3 | Instrument and board ERC | PASS (0 errors) | `design/reports/master-erc-warning-baseline.json` (228 warnings); `design/reports/board-erc.json` (10 boards, 0 errors, 673 warnings) | Warnings are retained and classified (phase 4), not suppressed | — |
| A4 | PCB zone fill on the #293 topology | PASS (fill completes; disposable copies) | `circuit/candidates/s2b-tmux-20261101/adoption/pcb-gate.json` (2026-11-01, adopted S2b design `9b0d7ef3`, local 4 CPU, 900 s budget): osc-core 649 s, 2277 MiB peak; jack boards 44 s and 54 s. Earlier run 39793075070 (frozen `fa16c6f`) was killed at its 223 s deadline | Completion only. The filled copies are synced drafts with DRC errors and are not committed | N |
| A5 | DRC: osc-core | FAIL (routing incomplete) | `boards/osc-core/reports/routing.json` + raw `drc.json` (2026-11-03, KiCad 10.0.6, isolated settled refill of adopted `dda33a25`, output bytes identical): 0 errors, 0 parity, 3409 native open edges (AGND 22, rails 63, other 3324), agreeing with the adopted `rail-links` receipt. `silk_overlap`/`silk_over_copper` reach the 199 cap, so the warning list is INCOMPLETE | Routing is incomplete; complete warning evidence for the standalone state NOT RUN | N |
| A6 | DRC: jack boards | FAIL (routing incomplete) | `boards/osc-jack-{left,right}/reports/routing.json` + raw `drc.json` (2026-11-03, KiCad 10.0.6, isolated settled refill of adopted `6bd6e153`/`dd41af2d`, output bytes identical): 0 errors, 0 parity; JL 268 open edges (AGND 3), JR 312 (AGND 8), agreeing with the adopted `analog-precision` receipts. Silk warning types capped (INCOMPLETE) | Routing of both jack boards is incomplete; RB4413 pilot remains BLOCKED by its netlist guard | N |
| A7 | DRC: octave ×5, panel, stage-optical | PASS for the retained reports | `boards/osc-octave-{1..5}/reports/drc.json` and `boards/panel/...`: 0 violations, 0 unconnected; `osc-stage-optical`: 0 unconnected, 289 warnings | The reports are 2026-10-02/03. A current-input rerun is NOT RUN (explicit permission) | N |
| A8 | OPA4196 loop and headroom (U110/U210 bridge) | UNKNOWN | `circuit/candidates/opa4196-compact-20261029/` (`verify_record.py` PASS in this run). Model screen: PM 47.5–122.1°, headroom ≥ 1.62 V, 170/170 runs; 0 °C clean; at 40 °C, 48 of 960 AC points did not converge | Only a model screen against PROPOSED criteria. No temperature range is specified, layout parasitics are open (2.5° margin at 20/20 pF), and the candidate is unadopted | U, R, P |
| A9 | Assembly land (U110/U210 SOIC-14) | BLOCKED | `circuit/proposals/opa4196-assembly-review-20261029/`; paste-aperture proposal 1a0563a | Paste policy: 1:1 or inner trim. The JLC part record is not retained: MSL handling, reflow profile, library class | U, E |
| A10 | BOM identity and evidence | FAIL | `design/readiness/bom-readiness.json`; `bom-cost-evidence.json`; research page `osc-passive-identity-candidates` (phase 13) | 1739 of 5916 placements per unit have no exact MPN (6 power flags no longer counted). Phase 13 proposes UNADOPTED candidates covering 1582 of them. 157 stay UNKNOWN: 14 non-E-series precision values, 10 nF C0G 0603, and 1 µF / 4.7 µF on the C0G symbol, all design decisions. CL10A105KB8NNNC and RC0603FR-072K2L still need Workflow B records | E, U |
| A11 | Supply contract and source | BLOCKED | `design/architecture-278/integration/power-contract/pd-interface-20v.md` | The PD B20 draft is not built. The PD-side start-skew time form FAILS (SIM). The no-load start-up exception is recorded as owner decision E21 (2026-11-14), as a current limit | U, P |
| A12 | Independent review of the complete design | NOT RUN | `worker-reviews/` (stage-scoped reviews only) | Prerequisites A2, A4–A6 and A10 are open | R |
| A13 | Repository Python test suite | FAIL (receipts) / NOT RUN (dependencies) | This run: 1808 tests in 28 roots. See the "Runnable gates" section | Hash-bound receipts are stale against main `02d69fbd`. scipy, shapely and playwright are missing here | E |
| A14 | Physical fit (panel, stack, harness) | NOT RUN | `design/architecture-278/GATE.md` | No hardware. 14 transport allocations exceed 300 mm. P59-B fit conflict on JR. JL header sites are full | P, U |

## B: prototype order. Not met: 2 FAIL, 2 BLOCKED, 4 NOT RUN, 2 UNKNOWN, 1 open

| # | Gate | Status | Evidence | Blocker | Needs |
| --- | --- | --- | --- | --- | --- |
| B1 | All A gates | FAIL | Section A above | A2, A4–A6 and A10 | — |
| B2 | BOM availability (stock, lifecycle) | FAIL | `bom-cost-evidence.json` (JLC catalog, 2026-10-31) | Stock below a 5-unit lot: ADG5412FBRUZ 0 of 550, PTV09A-4020F-B504 0, B104 4 of 240, B103 125 of 255, C0603C101J5GACTU 42 of 335, RC1210FR-07499RL 281 of 840, LM13700 54 of 80, LF398 5 of 10, RT0603BRD0710ML 0. Six lines have no part offer. Lifecycle is UNKNOWN | E, U |
| B3 | BOM cost, per unit and per 5-unit lot | UNKNOWN (partial) | `bom-cost-evidence.json` | Known part subtotal: $3232.47 per unit and $15453.96 per lot (JLC tiers, 2026-10-31). Unpriced: BAS16GW-QX ×464, WQP518MA ×180, APHHS1005QWF/D ×104, 2MS3T1B1M2QES, AS3340D, NOISE2, plus 157 UNKNOWN passives | E |
| B4 | PCB fabrication and assembly cost | UNKNOWN | — | No routed board set, and quoting is an outward action | U, E |
| B5 | DFM (JLC capability, panel, stencil, THT) | NOT RUN | Stage24 JLC capability/stencil sources; Stage50 assembly specification | No routed final revision to check | N |
| B6 | Residual-risk register accepted | BLOCKED | `pd-interface-20v.md`, `proposals-59/README.md`, `GATE.md` | Covered under "Residual risks" below | U |
| B7 | Bench acceptance tests defined | BLOCKED | `GATE.md`; `doc/src/content/docs/project/index.mdx` | The source specifies no quantity, budget, temperature range or prototype acceptance criteria. Defined targets: 20-minute warm-up, six trims, five-octave tracking, 5 cents at 25 °C, 2 mV adjacent steps, and 0.015–20,000 Hz as characterization only | U |
| B8 | Bench acceptance tests run | NOT RUN | — | No hardware | P |
| B9 | Safe energization procedure (rail order, faults) | NOT RUN | `pd-interface-20v.md` §5–§7 | Depends on B20 and P59 | P, U |
| B10 | Order and export package parity (ERC, DRC, BOM/CPL from one revision) | NOT RUN | — | No final revision. No order files are produced here | N |
| B11 | Lot size | Open | — | The coordinator's 5-unit lot is a planning figure, not a user decision | U |

## BOM cost: known part subtotal $3232.47 per unit, total UNKNOWN

Phase 13 read the public JLC catalog on 2026-10-31 (read-only). The detail is in
`bom-cost-evidence.json` and `doc/.../research/osc-passive-identity-candidates.mdx`.

| Set | Per unit | Per 5-unit lot |
| --- | --- | --- |
| Exact lines | $3195.45 | $15292.22 |
| Value-only candidates | $37.02 | $161.74 |

The largest costs per unit are ADG5412FBRUZ $1490, OPA4197IPWR $974 and OPA4196IDR $448.
The total stays UNKNOWN because 6 exact lines and 157 passive placements have no offer.
PCB, assembly, tax and shipping are excluded.

## Residual risks (open, not accepted)

| Risk | Source |
| --- | --- |
| VEE5 bound depends on P59-A adoption. The BAT54S cold VF and AS3340 current come from typical data only | proposals-59 P59-A rev 2 |
| Output injection while off (R-INJ); P59-B is held | proposals-59 |
| ADG IN high before ±5 V supplies (R-ADG); P59-C is held | proposals-59; pd-interface-20v.md |
| Supply limiter, reverse blocking, all-rail shutdown and start skew in B20 | pd-interface-20v.md |
| Temperature corners are undefined | project index |
| 14 transport allocations > 300 mm; contact and joint resistance | GATE.md |
| OPA4196 layout parasitics; the AS3340 negative-lead limit is 0.69 ms | phase-1/9 records |

## Runnable gates run in this session (no user decision needed)

| Check | Result |
| --- | --- |
| `check_ic_evidence.py`, `check_catalogue_publication.py` | PASS |
| `check_ic_units.sh`, `design/spec/cells/check_harness.sh` (native ERC) | PASS, 0 errors (6 documented LED pin-type warnings) |
| `monitor_permit_native.py --check`, `monitor_permit_rc.py --check` | PASS |
| Native `check_courtyard_minimum.py`, `check_wrl_dimensions.py --check`, `check_feature_mutations.py` | PASS |
| OPA4196 `verify_record.py` | PASS (record consistency only) |
| `bom_readiness.py --check` (new) | PASS |
| Python unit tests, all 28 roots | 1808 tests ran |
| — failures, receipts stale against main `02d69fbd` | `filter.py` and `block-contracts.json` changed after the Stage36/37/54 receipts were bound (stage36 whole-layout-review, stage37 family-reuse, stage54 power-cleanup, `scripts/architecture278` ledger) |
| — failures, retained-checkpoint binding (phase 8) | `architecture_history.py` |
| — NOT RUN: missing modules | scipy, shapely and playwright are absent |
| `test_route.sh --dense` | NOT RUN: `$HOME/.codex/scripts/heavy-guard.sh` is absent on this machine |
| DRC on any board, #293 fill, stage-optical/control copper checks (they run DRC) | NOT RUN: explicit permission or a changed input is required |
