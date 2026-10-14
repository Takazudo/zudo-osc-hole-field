# Resistance attribution source increment — 2026-10-14 WSL

Published as [draft PR275](https://github.com/Takazudo/zudo-osc-hole-field/pull/275), branch `topic/e16-resistance-attribution`. Source commits `7c79bbde` and `2c74257b`. Source-only follow-up to draft PR274 at `a811c2dddf98b1c253e710eddb9508a8b350dd77`, stacked on `topic/e16-selective-annulus`. Integration remains `5af0e7b675123b40367078ee605a1355bae49a62`; only its assigned owner may incorporate reviewed source with provenance. PR260 stays draft/unmerged and issue253 open. KEEP_K1402_INCUMBENT. All hardware remains an unvalidated draft.

## Delivered capability

`resistance_attribution.py` consumes a complete, already computed solution and attributes its Joule energy to disjoint modeled contributions. It is not another solver. Its CLI reads only bounded JSON and never unpickles, meshes, reconstructs, materializes or launches native work. The predecessor `resistance-report.py.txt` remains unchanged arithmetic over retained JSON/GZIP; neither command runs a production solve.

The in-memory `copper_components` adapter takes an existing `finite_adapter.Assembly` **and its original mesh items**, using the same group/coordinate/ring mapping. Union sheet tiles carry member fragment IDs, layer and spatial region. Overlapping pads, segments, annuli and sheet members do not receive duplicate energy. Individual spreading/access allocation within a union is unsupported; member IDs are provenance, not additive shares. Barrel records retain physical UUID and exact consecutive layer interval. `interface_components` reuses `finite_solve.terminal_stamps`: each distributed termination is one rank-one stamp `(w·v−vt)²/Rt`, and each live wire bulk is charged once globally. Removed wires retain their end terminations as in the original solver.

The reporter reconciles summed operators, complete node currents, free-node/global KCL, class energies, original energy and load work under the existing **1e−9** limits. It does not loosen the solver or modify baseline methods. Tiny free matrices (≤256 nodes) get a bounded positive-definiteness check; larger matrices require an independently pinned external positive-definiteness receipt tied to the exact matrix, held-node set, return state and checking method. That receipt is **bound, not recomputed**. A missing receipt is BLOCKED, not assumed uniqueness. Graph connectivity alone cannot establish uniqueness for rank-one interfaces.

For a selected current I, unit-current contributions are `E/I²` in Ω (also mΩ); arbitrary finite nonzero scaling is supported only where squared normalization and reported quantities remain representable. Total R includes modeled interfaces; copper R excludes them. Simultaneous-load reports contain watts and null resistance fields. No per-load allocation of loaded energy, series-path inference or geometry sensitivity is claimed. A changed bore/antipad requires a new extraction. Zero-energy interfaces already idealized by the original operator are not newly measured contact losses.

Missing detail, identities, scope, bindings, nonfinite quantities, singular states, duplicate ownership and failed reconciliation block the report. AGND all-three-open is explicitly structural/floating even for zero excitation. Every result permanently sets whole-board acceptance, electrical acceptance and adoption to **false**, including complete synthetic controls. Unmodeled physical source/protection, GH paths, unsupported/dynamic loads and physical return obligations remain open.

## Reproduce the synthetic demonstration

From the E16 directory with the retained numerical environment:

```sh
/home/takazudo/.cache/zudo-e16-numerical-venv/bin/python resistance_attribution.py \
  --detail evidence/e16/resistance-attribution-wsl-20261014/synthetic-detail.json \
  --expected evidence/e16/resistance-attribution-wsl-20261014/synthetic-expected.json \
  --output /tmp/e16-synthetic-attribution-fresh.json
```

Output must be a fresh path. The CLI limits each input to 16 MiB and each matrix to 100,000 nodes; production-sized extraction belongs to a separately admitted in-memory diagnostic, not an implicit larger CLI job. [Synthetic result](synthetic-result.json) is a 2 mΩ + 3 mΩ analytic series fixture, not TP990026 evidence. The test suite also exercises parallel/shared-source networks, a distributed termination with unequal support potentials, physical aggregation, normalization/conversion, failed bindings/scope, source relabeling, singular rank-one interfaces, and actual tiny Assembly/ring mapping. [Protocol](protocol.md) documents packet and result semantics.

## Next bounded action

Review [the exact TP990026 experiment](transfer-experiment.md) and [machine-readable specification](transfer-experiment.json). TP990026 is a held source land and cannot be a driving-point observation without changing the problem. B selects KB U7105.4 on +12V, preserving TP990002/014/026. A is this source increment; B requires a separate exact admitted real-data diagnostic; C independently evaluates it; D requires separate disposable-geometry authority and fresh affected-net/native/numerical evidence. No B–D work was performed or admitted here. A +12V via does not solve the worst +5V U4330.14 problem; the same reporter accepts that separately selected target later without another implementation.

A remaining reconstruction bridge must recover one unit-current potential field from retained operators using the existing solver and preserve original tile provenance. Retained scalar driving-point projections alone are insufficient. It must be resource-bounded and independently reviewed before any production execution. Retained reduction receipts report 1,515,457 KA and 1,541,278 KB +12V mesh nodes; a complete joined dense JSON packet is not a feasible production transport. The current API retains all component triplets and evaluates full node vectors, so it has substantial memory/runtime cost at that order. The reconstruction bridge must develop and review streaming extraction/accounting or demonstrate that the existing API fits the exact caps; removing an API order ceiling proves representability only. Do not assume this tiny JSON demonstration scales. The spec's proposed 180-second / 2-GiB diagnostic ceiling is not a demonstrated feasibility result or permission. Missing artifacts are recovered and hash-verified, never recreated with another baseline.

## Native and retained execution state

Independent [state review](review-state.md) found attempt 5 terminal, no live matching workload, and current consumption **2/3 full baselines, 8/24 diagnostics**. This increment consumed **zero** native/numerical campaign units. The 148 completed units / 147 passing numerical assessments remain exact-input historical consistency results; all evaluated loaded observations exceed their copper allowance. Narrowest energy headroom remains 0.28005%, with no PASS transfer to new methods or inputs.

The exact native negative-control request remains SHA-256 `f8da55c709fa59ba3221806f1c10cc4d25462fe8bf9d8c50acf313b0d3fdf4e3`, frozen source `b27391dea630ef60a5613608bcbb6b25458a0d8d`, run `ad8f3b1a33ef4b5eaf638b183708ef64`, attempt 1, checkout `/home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-annulus-fixture-ad8f3b1a`. Only `.circuit-cache/annulus-fixture-ad8f3b1a/request.json` exists. Separate genuine operator approval, exclusive reservation and applicable qualification attestation are missing. No execute/approve command was invoked. A future exact admitted run is one ≤60-second negative control under unchanged pinned KiCad 10.0.6 / native 6-GiB worker / 12-GiB aggregate / no-swap / 8-GiB launch-floor controls. Failure is terminal; no retry identity reuse.

Selective-annulus production serialization still refuses `UNSUPPORTED_NATIVE_SELECTIVE_ANNULUS`. The 0.35 mm residual In3 land is not exact removal. The named AGND barrel/functional contacts stay unchanged. A negative-control success would not establish durable removal, refill, production connectivity, exhaustive DRC or qualification. Historical native command/reconciliation evidence remains separate; findings remain capped/INCOMPLETE and acceptance blocked.

## Preservation, recovery and verification

[Fresh streamed-hash audit](preservation.json) verifies **135 files / 844,803,369 bytes** at `/home/takazudo/.cache/zudo-e16-runs/coupled-approved-852ffac-8262c033`, 539 protected topic files and 550 original-checkout files. The 11 topic-absent UI files are the predeclared original-only untracked files. Preserve directory layout; recover exact bytes using `../campaign-wsl-20261014/attempt5/index.json` and its README, then reverify every size/hash before consumption. No pickle was loaded and no PCB/large solver artifact or Git LFS was introduced. The accompanying audit script is retained for inspection, not an executable command manifest.

The experiment's retained input index preserves the predecessor's `matches_retained_binding:false` for compressed `request.json.gz`: its compressed bytes have their own size/hash; the decompressed original request separately verifies as `ef0213b3b38f4de23804ad192043b082d8e1b2be3086c5e20e4343afea4052d6`. This is not permission to consume mismatched inputs. The independent state review checked that distinction.

All 19 Mac browser input bindings were recalculated and remain unchanged. No browser rerun or WSL substitute is claimed. Canonical boards, accepted copper, decision.json, 438 locked centers, 33 modules, harness IDs/Refs/full pin order, sensitive groups, source/protection and factory-complete assembly stay unchanged. KA196 / KB486, separate KB-P1 480 and prior long-B194 remain distinct; service stays 151 supported / 59 partial / 21 unserved / 194 unmapped, 302 eligible pads.

Actual checks and resource receipts are in `checks/summary.json` and its logs. Aggregate regeneration is NOT RUN because it schedules native work outside admission; permitted source checks are not equivalent. CI publication uses `[skip ci]` to prevent unadmitted native dispatch and is SKIPPED/NOT RUN, never PASS. Source completion does not select architecture, adopt copper or qualify the instrument.
