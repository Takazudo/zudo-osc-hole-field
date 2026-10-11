# Epic 242 complete-set settle comparison — measured, not selected

All five sealed candidate boards have **settle-only** receipts. The three new sequential 600-second jobs and full artifact identities are in [`settle-batch-600-results.json`](settle-batch-600-results.json); two-A is in [`two-a-600-run38133584276-ledger.json`](two-a-600-run38133584276-ledger.json), and three-A is run 38130450410/artifact 11698474605. The new jobs ran at the same immutable source SHA `65d44bc571052a05abe55db150e728570045f701`, each under a separate parent admission, one exclusive native worker, 6 GiB worker/12 GiB aggregate/2 GiB free floor and a 600-second watchdog. All three new artifacts passed ZIP CRC, 294 input snapshot hashes, 291 portable fixture seals, 14 full-container-ID ACK/membership/exit-0 chains, zero OOM, final owned-workload absence, settled board/DRC/dump hash bindings and zero schematic parity. The unchanged source algorithm requires three consecutive identical full island signatures; intermediate signatures are not separately retained for replay. Each successful job logged three equal edge counts and a settled receipt. This is not a full-warning or copper-preservation pass.

## Common source domain and measured connectivity

The reference is accepted K1402's settled board `b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66`, from run 38011194282/artifact 11658776367, full ZIP SHA-256 `1ed58a9cd4c5796654a9e3e5c9b6e1c1129c353f3451e04c990b95032012479f`. Its `.circuit-cache/osc-core-grid-189-compact-refill/dump.json` binds to that board. For K and each candidate, the same dump schema computes open edges as the sum, over nets, of `max(0, island component count − 1)`. Every candidate pad UUID resolves to the **same Ref, pad number and net** in K. In each complete option, the union covers all 13,406 unique K pad UUIDs with no missing or new pad identity. The 199 blank-net mechanical NPTH pads are copied onto every candidate board: 199 excess pad records in the two-board set, 398 in the three-board set. They are not extra electrical endpoints.

| Complete set | Board dump open edges | Raw board sum | Unique K-identical pad IDs | Exclusive-net open edges | Shared-rail open edges |
| --- | --- | ---: | ---: | ---: | ---: |
| Accepted K1402 | K: 1,402 | 1,402 | 13,406 | 1,029 | 373 |
| Two-board option | A: 903; B: 1,839 | 2,742 | 13,406 | 1,029 | 1,713 |
| Three-board option | A: 538; B: 558; C: 1,651 | 2,747 | 13,406 | 1,029 | 1,718 |

There are 3,553 electrical nets owned by exactly one board in either option. On those *same pad/net domains*, the sum of candidate native open-edge deficits (`max(groups − 1, 0)` per net) is 1,029, exactly the K count; for every exclusive net recorded as open, the full island member groups also match K. Four electrical nets span candidate boards: `+12V`, `+5V`, `-12V` and `AGND`. Their per-board islands are separately counted by the native dump, while K has one whole-board connectivity domain. This difference means the raw board sums **cannot** be ranked against K1402's 1,402 as route quality or architecture feasibility.

| Shared net | K1402 | Two-board A + B | Three-board A + B + C |
| --- | ---: | ---: | ---: |
| `+12V` | 80 | 288 + 291 = 579 | 174 + 183 + 221 = 578 |
| `+5V` | 0 | 37 + 509 = 546 | 54 + 0 + 491 = 545 |
| `-12V` | 80 | 219 + 191 = 410 | 121 + 151 + 137 = 409 |
| `AGND` | 213 | 74 + 104 = 178 | 45 + 43 + 98 = 186 |

The board partitions add explicit feed, return, connector and protection obligations that a per-board settle does not join. Matching net names do not physically connect boards. Even `AGND`'s lower per-board subtotal proves no return continuity or noise performance. The equality on exclusive open nets shows no measured connectivity improvement there; most numerical difference is concentrated in shared rails and returns, where the domains differ. The dump omits connected nets from its island table and does not census isolated zone-only copper, so it is an open-island diagnostic, not a complete copper or physical-route-cost metric. A full normalized claim needs interface endpoint pairs, connector current and impedance, cross-board rail/return paths, plane continuity and physical routing corridors measured with the same ownership map. Record those identities before deduplicating or joining any edge obligations. If K's retained extraction lacks a required field, mark that metric **INCOMPARABLE** rather than infer it from capped DRC lists.

## Remaining gates

Candidate raw DRC reports list 801/813/800/754/812 warnings for two-A/two-B/three-A/three-B/three-C respectively, and exactly 499 unconnected items for each. Those item lists are capped; neither their lengths nor the listed warnings establish full native open-edge or uncapped warning totals. The settled reports contain no DRC error or schematic parity item, but complete uncapped warning identity, original-copper retention/migration eligibility and full hardware acceptance are **NOT RUN**.

Before architecture selection, #246 must close same/opposing-face clearances, drilled-body/tail/shaft/tool access and stack Z; #247 must close +12 V/−12 V/+5 V/AGND feed, current, impedance, return and protection budgets; #248 must close panel/cable/interface and installed service access. The 40 strict-gap shortfalls, connector reservations and load lands remain open. Accepted JL117/JR129/K1402, fixed panel/harness identities and canonical copper remain unchanged. No route, adoption, merge, fabrication, order or energization follows from these settle measurements.
