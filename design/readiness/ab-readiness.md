# OSC A/B readiness matrix (2026-10-31)

**Status vocabulary:** PASS / FAIL / BLOCKED / NOT RUN (with reason) / UNKNOWN. Every schematic
and PCB here is an unvalidated draft. Nothing is validated, qualified or released, and this
file creates no fabrication or order output.

- **A** means the design is complete.
- **B** means the technical conditions for a prototype order are met.

Evidence is at commit `25c60c40` unless a row names this commit. The "Needs" column uses
**U** (user decision), **N** (native KiCad run), **P** (physical work), **E** (evidence or
access) and **R** (independent review).

## A: design complete. Not met: 3 FAIL, 3 BLOCKED, 3 NOT RUN, 1 UNKNOWN

| # | Gate | Status | Evidence | Blocker | Needs |
| --- | --- | --- | --- | --- | --- |
| A1 | Schematic generated from source, no drift | PASS | `regen-all.sh --check` exit 0 at 25c60c40 (phase-11 run); `design/reports/master-audit.json` | — | — |
| A2 | Schematic design content complete | FAIL | `design/power/proposals-59/README.md` | #59 protection is not in the schematic. P59-A rev 2 is awaiting adoption. P59-B/C are held as records, so output injection while off (R-INJ) and the ADG enable gap (R-ADG) stay open | U |
| A3 | Instrument and board ERC | PASS (0 errors) | `design/reports/master-erc-warning-baseline.json` (228 warnings); `design/reports/board-erc.json` (10 boards, 0 errors, 673 warnings) | Warnings are retained and classified (phase 4), not suppressed | — |
| A4 | PCB zone fill on the #293 topology | FAIL | Run 39793075070 (frozen `fa16c6f`): the fill was killed at the deadline after 223 s, with an empty fill log | A rerun needs a changed input: more CPU/threads, a fill budget based on evidence, a reduced fill workload, or a different frozen source. It must not be rerun unchanged | U, N |
| A5 | DRC: osc-core | FAIL | `boards/osc-core/reports/drc.json` (KiCad 10.0.6, 2026-10-08): 499 unconnected, 620 warnings, parity 0 | Routing is incomplete | N |
| A6 | DRC: jack boards | FAIL | `boards/osc-jack-left/reports/drc.json`: 140 unconnected; `osc-jack-right`: 162 unconnected | Routing is incomplete. The Stage57 trial closes one net (115 → 114) on a disposable copy only | N |
| A7 | DRC: octave ×5, panel, stage-optical | PASS for the retained reports | `boards/osc-octave-{1..5}/reports/drc.json` and `boards/panel/...`: 0 violations, 0 unconnected; `osc-stage-optical`: 0 unconnected, 289 warnings | The reports are 2026-10-02/03. A current-input rerun is NOT RUN (explicit permission) | N |
| A8 | OPA4196 loop and headroom (U110/U210 bridge) | UNKNOWN | `circuit/candidates/opa4196-compact-20261029/` (`verify_record.py` PASS in this run). Model screen: PM 47.5–122.1°, headroom ≥ 1.62 V, 170/170 runs; 0 °C clean; at 40 °C, 48 of 960 AC points did not converge | Only a model screen against PROPOSED criteria. No temperature range is specified, layout parasitics are open (2.5° margin at 20/20 pF), and the candidate is unadopted | U, R, P |
| A9 | Assembly land (U110/U210 SOIC-14) | BLOCKED | `circuit/proposals/opa4196-assembly-review-20261029/`; paste-aperture proposal 1a0563a | Paste policy: 1:1 or inner trim. The JLC part record is not retained: MSL handling, reflow profile, library class | U, E |
| A10 | BOM identity and evidence | FAIL | `design/readiness/bom-readiness.json` (this commit) | 5922 placements per unit, of which 1745 have **no exact MPN**. The scheme leaves differing-value passive MPNs blank (`scripts/schgen/README.md`). 43 exact lines, 16 with an LCSC code. CL10A105KB8NNNC and RC0603FR-072K2L have no owner skill in the inventory. `circuit:check` PASSES for the 68 inventory lines it covers | E, U |
| A11 | Supply contract and source | BLOCKED | `design/architecture-278/integration/power-contract/pd-interface-20v.md` | The PD B20 draft is not built. The PD-side start-skew time form FAILS (SIM). The no-load slope exception needs recording | U, P |
| A12 | Independent review of the complete design | NOT RUN | `worker-reviews/` (stage-scoped reviews only) | Prerequisites A2, A4–A6 and A10 are open | R |
| A13 | Repository Python test suite | FAIL (receipts) / NOT RUN (dependencies) | This run: 1808 tests in 28 roots. See the "Runnable gates" section | Hash-bound receipts are stale against main `02d69fbd`. scipy, shapely and playwright are missing here | E |
| A14 | Physical fit (panel, stack, harness) | NOT RUN | `design/architecture-278/GATE.md` | No hardware. 14 transport allocations exceed 300 mm. P59-B fit conflict on JR. JL header sites are full | P, U |

## B: prototype order. Not met: 2 FAIL, 3 BLOCKED, 3 NOT RUN, 2 UNKNOWN, 1 open

| # | Gate | Status | Evidence | Blocker | Needs |
| --- | --- | --- | --- | --- | --- |
| B1 | All A gates | FAIL | Section A above | A2, A4–A6 and A10 | — |
| B2 | BOM availability (stock, lifecycle) | UNKNOWN | Owner-bundle procurement facts: 26 UNVERIFIED, 3 "LISTED; stock UNVERIFIED", the rest open | No retained stock record. Reading distributor stock is not done here | E |
| B3 | BOM cost, per unit and per 5-unit lot | UNKNOWN | `design/readiness/bom-readiness.json` | Covered under "BOM cost" below | E |
| B4 | PCB fabrication and assembly cost | UNKNOWN | — | No routed board set, and quoting is an outward action | U, E |
| B5 | DFM (JLC capability, panel, stencil, THT) | NOT RUN | Stage24 JLC capability/stencil sources; Stage50 assembly specification | No routed final revision to check | N |
| B6 | Residual-risk register accepted | BLOCKED | `pd-interface-20v.md`, `proposals-59/README.md`, `GATE.md` | Covered under "Residual risks" below | U |
| B7 | Bench acceptance tests defined | BLOCKED | `GATE.md`; `doc/src/content/docs/project/index.mdx` | The source specifies no quantity, budget, temperature range or prototype acceptance criteria. Defined targets: 20-minute warm-up, six trims, five-octave tracking, 5 cents at 25 °C, 2 mV adjacent steps, and 0.015–20,000 Hz as characterization only | U |
| B8 | Bench acceptance tests run | NOT RUN | — | No hardware | P |
| B9 | Safe energization procedure (rail order, faults) | NOT RUN | `pd-interface-20v.md` §5–§7 | Depends on B20 and P59 | P, U |
| B10 | Order and export package parity (ERC, DRC, BOM/CPL from one revision) | NOT RUN | — | No final revision. No order files are produced here | N |
| B11 | Lot size | Open | — | The coordinator's 5-unit lot is a planning figure, not a user decision | U |

## BOM cost: only one line has a price, under 5 cents per unit

**Per unit (CALCULATED):**

- Known: CL10A105KB8NNNC / C15849, 3 per unit × $0.0146 (JLC tier 1–499) = **$0.044**.
  - Source: the PD worker's JLC parts API read of 2026-10-31. It is uncommitted and is not
    OSC evidence.
- UNKNOWN: the other 42 exact lines (4174 placements) and all 1745 value-only placements.

**Per 5-unit lot:** 15 × $0.0146 = **$0.219** known. Everything else is UNKNOWN.

**Total:** UNKNOWN. No retained OSC evidence prices any other line. The Stage36 IDC
connector snapshot ($1.80 / $1.32) is a dated observation for parts that are not in this
BOM.

**Largest quantities per unit, which matter most for cost once prices are known:**

| Part | Per unit |
| --- | --- |
| GRM188R71H104KA93D | 1132 |
| RT0603BRD07100KL | 651 |
| BAS16GW-QX | 464 |
| RC0603FR-07100KL | 210 |
| WQP518MA | 180 |
| OPA4196IDR | 174 |
| RC1210FR-07499RL | 168 |
| BAT54S | 125 |
| ADG5412FBRUZ | 110 |
| APHHS1005QWF/D | 104 |

For a 5-unit lot, multiply by 5. The full list is in `bom-readiness.json`.

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
