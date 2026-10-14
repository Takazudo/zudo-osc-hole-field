# Independent E16 resistance-attribution review

Reviewer: math_plan_review subagent. Scope: resistance_attribution.py, test_resistance_attribution.py, existing finite_adapter.py / finite_solve.py. No production extraction, native execution, retained pickle reads, geometry writes or numerical baseline.

## Initial review evidence

The first implementation passed 22 tiny tests using /home/takazudo/.cache/zudo-e16-numerical-venv/bin/python -m unittest test_resistance_attribution -v. Green tests did not establish correctness: independent adversarial examples found three defects.

1. Observation UUID could equal a held source-pad UUID while supplied observation nodes differed; the result incorrectly passed. This matters directly to TP990026. Main subsequently added UUID rejection and retained source/config checks.
2. A 1e-200 A normalization underflowed current**2 and produced nonfinite resistance and an uncaught ZeroDivisionError. Main subsequently added scale and finite-output checks.
3. Graph connectivity did not establish uniqueness for distributed rank-one stamps. A component with weights [-1,.5,.5], resistance .001 ohm, held node 0, voltages [0,.001,.001], injection [0,.5,.5] and observation support [.5,.5] passed despite free matrix [[250,250],[250,250]] being singular. Main is adding bounded explicit small-matrix validation and independently bound external-check provenance for larger matrices.
4. Duplicate indices inside one source-pad node list would double its reported source current, although the global fixed-node set was deduplicated. Main notified to reject duplicate per-pad node indices.

## Mathematical assessment

The core energy calculation v-transpose M v, unit-current normalization E/I-squared, complete-operator reconciliation, original-node-current reconciliation and separate loaded-watt reporting are appropriate. Distributed terminations use the existing rank-one convention; both termination ends and bulk wires are independently owned. Copper-only and complete-path resistance must remain distinct.

Union sheet groups/tiles preserve overlapping member identities without claiming per-member additive shares. The Assembly map includes group identity, rounded coordinates and merged bore nodes. This is the correct reuse of existing geometry/assembly. A tiny real Assembly regression covers bore-ring mapping, but direct interface adapter and explicit tiled-boundary tests improve coverage.

Expected binding manifests must be pinned independently. Their equality to packet content is integrity checking, not approval, true geometry proof, source extraction proof or permission to consume campaign resources.

## Status

Final follow-up below supersedes this initial pending status.

## Final independent follow-up

Disposition: no remaining blocking finding for this source-only increment at the hashes below. This is not approval for real-data diagnostic B, geometry/native stage D, incorporation into shared integration, or hardware acceptance.

Re-ran `/home/takazudo/.cache/zudo-e16-numerical-venv/bin/python -m unittest test_resistance_attribution -v`: 32 tests passed in 0.609 seconds. Independently regenerated the retained synthetic result in memory from synthetic-detail.json plus synthetic-expected.json: exact parsed-JSON equality with synthetic-result.json, status PASS_MODELED_SOLUTION_ACCOUNTING_ONLY. No production solve, reconstruction, native execution or retained pickle load occurred.

Verified fixes: observation UUID cannot name a held source; duplicate held nodes are rejected; extreme current scales fail explicitly; singular rank-one connected controls fail a bounded tiny positive-definiteness check; larger operators without exact external matrix/held-node/return receipt bindings fail. Receipt digest format and mismatches have regressions. Direct distributed-interface and real tiled-Assembly regressions now exercise the extraction adapters.

The reporter initially selected the older root coupled-network-config.json; final CONFIG selects the retained continuation-20261013b configuration (f5146d0c1d77e0626a455df308f52bf953ace9806861c25438adcdf90914c107). This preserves the attempt-5 load-ledger/scenario binding. Retained packets now cross-check exact configured source identities and live bulk/end-termination scope against their return state.

Read final protocol, README, transfer-experiment.json and transfer-experiment.md. The specification preserves TP990026 as a held source and selects exact KB U7105.4 UUID e97b2d02-463a-5a6d-ab37-748ce29d7cf8 for nominal +12V/all-present observation. It binds the exact existing barrel and sole added via at (141,175), preserves all three source supports and original objects, distinguishes local ideal estimates from measured results, keeps +5V work separate, and declares B–D not executable/adopted. Proposed resource caps are explicitly unproven ceilings; no baseline slot is charged. The 10% energy-share and 1%/0.01-milliohm improvement criteria are clearly engineering screens, not sensitivities or forward-error bounds. Affected antipads, all process cases and applicable AGND return obligations remain gates.

The predecessor input index false entry for compressed request bytes is explicitly explained alongside the separately verified decompressed request identity. Negative evidence and incomplete mappings/caps do not become permission to expand geometry or accept hardware.

Residual limitations are explicit and appropriate: real extraction bridge and resource feasibility are not implemented/proven; independent manifest generation and external uniqueness evidence remain reviewed-extractor responsibilities. Sheet union members are provenance only; no arbitrary individual overlapping-pad allocation is inferred. External uniqueness receipt binding is not recomputed mathematical proof. Hardware/source-protection/load omissions remain outside modeled accounting, and every acceptance/adoption flag remains false.

## Final reviewed bytes

| Relative E16 path | Bytes | SHA-256 |
| --- | ---: | --- |
| `resistance_attribution.py` | 24212 | `51176637a851de9b75786a98889ae7072f681a2342816f3b6b9dd2723f519385` |
| `test_resistance_attribution.py` | 17137 | `f4a79bffb570109943ffa2300f500519478c30d318c54601d141f2cc971834be` |
| `evidence/e16/resistance-attribution-wsl-20261014/transfer-experiment.json` | 24258 | `a755d4558260f5e9e669855d6464a8d3f54c64cbae44a90ea9bed211aadf7383` |
| `evidence/e16/resistance-attribution-wsl-20261014/transfer-experiment.md` | 5475 | `6feec56508f497be2126ccfe80dfc2a6a65573c37b381ec57a74f93e5d97268c` |
| `evidence/e16/resistance-attribution-wsl-20261014/protocol.md` | 5772 | `39f13d70731e43f8a13ab7f85a0adb0c129968f51dedb71b97fa52296cb731de` |
| `evidence/e16/resistance-attribution-wsl-20261014/synthetic-detail.json` | 3761 | `c910d405f74e30dff418842bf532cd94c086073e59e43eedd98f889da6f92ca5` |
| `evidence/e16/resistance-attribution-wsl-20261014/synthetic-expected.json` | 495 | `88a0b1b409af99d24af5ca2262c4711ce69d2e01966218354265192ec10bb1d8` |
| `evidence/e16/resistance-attribution-wsl-20261014/synthetic-result.json` | 5101 | `5f1cdda19358685c82d802dbbd8b80dd3efe5aebff6f3590d32abbde6be63804` |

## API/CLI scale follow-up (supersedes prior final hashes)

The implementation owner identified the original 100,000-node parser ceiling as incompatible with the retained ~3.06-million-node joined +12V operator. Reviewed the correction: the in-memory sparse parser now permits positive integer orders below 2**31; the JSON CLI still enforces 100,000 nodes on both the network and every component before calling attribute or allocating a sparse matrix. This separates source primitive representability from an admitted production resource budget.

Independent rerun: 34 tests passed in 0.695 seconds. The new API test constructs only a 100,001-order sparse matrix with two entries, not full vectors or a solve. The CLI regressions mock matrix_read and prove oversized network and component records are rejected before matrix allocation. The regenerated synthetic result again exactly equals the retained JSON result.

Read the updated README/protocol: they explicitly retain the unresolved production cost of all component triplets and full node vectors, the need for a reviewed streaming bridge or demonstrated fit within exact caps, and the lack of evidence for 2-GiB/180-second feasibility. No real operator, new factorization or production extraction was executed for this review.

Disposition remains no blocking finding for this source-only increment. The cap change does not make diagnostic B executable or remove the reviewed resource-plan and admission prerequisites.

| Current relative E16 path | Bytes | SHA-256 |
| --- | ---: | --- |
| `resistance_attribution.py` | 24452 | `67c9735f1519b49e69cab61dfaea8947d5f7d9838185cce7f87eca0070deca70` |
| `test_resistance_attribution.py` | 18278 | `fb0630b0b226f94654087a8e1e1ac059dc8845ed68a615cbcf48b0a8dd468848` |
| `evidence/e16/resistance-attribution-wsl-20261014/protocol.md` | 5970 | `44d53bca0f6912dd36bb6bd5a7e149b64f0e3d6031542acefc80f8f0458ae787` |
| `evidence/e16/resistance-attribution-wsl-20261014/README.md` | 10055 | `44ddc567e91eba4eae2ad5c14aa51899d8b413e1d3f863ef77c9654f5a3a2419` |
| `evidence/e16/resistance-attribution-wsl-20261014/synthetic-detail.json` | 3761 | `962d5c7fb7984236743a19b0bfe41ffbf67e2e98f8451d55e5d8474709501e7e` |
| `evidence/e16/resistance-attribution-wsl-20261014/synthetic-expected.json` | 495 | `808c3ae3b0687b65b91adc8f0a01a94cb847a89d34d7f9f66029dded7303e288` |
| `evidence/e16/resistance-attribution-wsl-20261014/synthetic-result.json` | 5101 | `99224ab270727d296955bae14b37665eec00c995f709d9da9653da1b3352f3b9` |
