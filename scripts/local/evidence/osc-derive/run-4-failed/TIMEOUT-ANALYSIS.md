# Source-only analysis of the derive run 4 timeout (chained AGND B.Cu + In1.Cu)

Requested by coordinator instruction `osc-moya-timeout-source-analysis-f641e0ca`.
Inputs: the saved run-4 traces (`receipt.json`, `zone.json`, wrapper log), the
comparable saved runs (derive runs 1, 2, 3; candidate run 2), and the tooling
source at commit a89bb69d. No native code was run; no engine source is
accessible in this environment (the pinned image ships KiCad 10.0.6 binaries
only), so engine behaviour below is cited from the wrapper source and the traces,
and marked as hypothesis where the engine's internals would be needed.

## Measured facts (run 4)

| fact | value | source |
| --- | --- | --- |
| worker start to `load` complete | 14.0 s (61.3 MB parent with the F.Cu fill cache) | zone.json `worker_substages.zone.rows` |
| `identity` + `before` (ownership check, zone table, connectivity build, pair clusters) | 8.3 s; `fill` start at 22.3 s | same |
| fill | started 22.3 s, no `complete` row; worker SIGKILLed at 282.4 s (fill group 260.1 s) | zone.json `command` |
| payload / controller / wall | 294.6 / 296.9 / 297 s; outer stop 600 s not reached | receipt, wrapper log |
| memory | cgroup peak 1,770,110,976 B (1.65 GiB); current at the failure frame 79.6 MB; OOM events 0 | zone.json `memory_telemetry` |
| parent verification | `reusable: true`; ownership on input = F.Cu zone 601e02b2 with 236 outlines only | zone.json `parent` |
| what reached the fill | both zones in one `ZONE_FILLER.Fill(selection, False)` call | `osc_derived_fill_payload.py:153-157` |
| what was exported | nothing (no `after/`, no manifest, no classification) | output directory empty |

Comparable single-zone fills, same image, same 1 CPU / 2 GiB container:

| run | input | zone(s) | fill | result | peak |
| --- | --- | --- | --- | --- | --- |
| candidate run 2 | source (47.5 MiB, unfilled) | +12V In4.Cu | 57.9 s | complete | - |
| derive run 1 | source | AGND In1.Cu | 131.9 s | complete | 1.47 GiB |
| derive run 2 | source | AGND F.Cu | > 260 s | killed at the cap | 1.07 GiB |
| derive run 3 | source | AGND F.Cu | 150.8 s | complete | 1.58 GiB |
| derive run 4 | run-3 copy (61.3 MB, F.Cu filled) | AGND B.Cu + In1.Cu | > 260 s | killed at the cap | 1.65 GiB |

No B.Cu fill has ever been measured. Runs 2 and 3 show that the same zone on the
same input can take 150.8 s or more than 260 s on this host; that variance is
unexplained by the saved traces (no CPU-time or host-load sampling exists in the
telemetry), so no single-zone number can be treated as a stable cost.

## What the traces evidence, and what they do not

- Evidenced: the time went into the single `Fill` call that covers both zones.
  Everything before it (load, ownership check, before-fill connectivity) took
  22.3 s, within the 60 s prepare cap. Nothing after it ran.
- Evidenced: memory was not the limit (1.65 GiB peak, 0 OOM, cap 2 GiB); the peak
  being above run 2's 1.07 GiB at its kill, and close to the completed single-zone
  runs, is consistent with the fill having done substantial polygon work, but the
  trace cannot say which zone or which phase.
- Not evidenced: which of the two zones, or which engine phase (clearance
  knockout, polygon boolean ops, thermal spokes, island removal, connectivity
  rebuild) consumed the time. The payload records one `fill` stage for the whole
  selection (`osc_derived_fill_payload.py:153-158`); there is no per-zone timing,
  no progress reporter, and no cgroup `cpu.stat` sampling (`osc_frozen_fill.py:115`
  samples memory counters only). Whether the fill was close to finishing is
  unknown.
- Not evidenced: whether the loaded F.Cu fill cache (236 outlines) slowed the
  other two fills. The engine's own treatment of existing fills on other layers
  during a selective fill is not readable from accessible source; this remains a
  hypothesis.

Therefore the saved traces cannot locate a bottleneck without a rerun, and a rerun
of the same shape would only reproduce the cap.

## Is the two-zone batching required for correctness?

Wrapper source: the payload fills every spec zone in one call
(`osc_derived_fill_payload.py:153-157`: `selection = pcbnew.ZONES()`; append each
selected zone; `ZONE_FILLER(board).Fill(selection, False)`). The spec and profile
table allow one to eight zones (`osc_derived_fill.py` `ZONE_LIMIT`); the chained
profile lists two zones because the approval named two zones for one attempt,
not because the engine needs them together. The chained-derivation path already
supports a chain of single-zone runs: the manifest records `parent` zones and the
reuse checks accept identity zones plus ancestor zones
(`osc_derived_fill.py` `manifest_identity`, `verify_derived`;
`osc_derived_fill_payload.py:147-149` requires the input's fill ownership to equal
the declared parent plus ancestor zones and refuses to refill a selected zone
that is already filled, `select_zones(..., must_be_unfilled=True)`). This path is
offline-tested (`test_chained_derivation_and_worker_failure`) but has never been
run natively beyond the one failed attempt.

Zone-interaction dependencies, from accessible facts: the two zones are on
different copper layers (B.Cu, In1.Cu), each is the only copper zone on its
layer, and the board's rule areas allow copper pour everywhere, so the fill
geometry of one cannot depend on the other through same-layer priority or
clearance. The one cross-layer coupling in KiCad's fill is island removal, which
decides whether an island is "connected" using board connectivity across layers
(through vias). The zones' `island_removal_mode` is 0 in the file; whether 0 means
"always remove" or "never remove" is not verifiable from accessible source, and
the two readings differ for a split: under "never", a sequential fill is
identical to a batched one; under "always", an island on the second-filled layer
whose only connection ran through the first-filled layer would be kept in a
sequential run (that layer is already filled) exactly as in a batched run, while
the reverse case (an island on the first-filled layer that only connects through
the second) could be removed in the sequential run and kept in the batched one.
For the question at hand this coupling is not material: U1105.12's F.Cu island
holds no via, so no fill on B.Cu or In1.Cu can connect to it, and the
classification is computed on the final board after the last fill.

Saved-parent reuse semantics: a split keeps the already-filled data. Run A would
take the run-3 copy (F.Cu filled) as parent and fill In1.Cu; its manifest records
parent zones [F.Cu]; run B would take run A's output as parent and fill B.Cu; the
ownership check requires exactly F.Cu + In1.Cu on its input and the final board
carries all three. The pair classification in run B is the intended evaluation
(all AGND zones filled, +12V control still unevaluable).

## Bounded recommendation

Cause: not established. The only evidenced statement is that the batched
two-zone fill on the F.Cu-filled copy exceeds 260 s at 1 CPU; the traces cannot
apportion the time between the zones or engine phases, and single-zone timing on
this host varies by more than the margin the cap leaves.

Smallest useful next action, if the parent still wants the AGND pair's class
decided by the oracle: two chained single-zone runs under the existing
`chained-agnd` numbers (standard time chain, 128 MiB bound, 1 CPU / 2 GiB), each
with its own approval and slot: run A = In1.Cu on the run-3 copy (the only AGND
zone with a measured fill, 131.9 s on the unfilled source); run B = B.Cu on run
A's output. Diagnostic value: run B's result moves C1111.2 <-> U1105.12 to
`OPEN_WITH_ALL_NET_ZONES_FILLED` or `CONNECTED_VIA_SELECTED_FILL`; run A alone
also yields an F.Cu+In1.Cu-filled board but no class change. Exact scope: parent
`ecf170db...` / board `4a55e0c1...` for run A; run A's exported board for run B;
pairs unchanged; no DRC, copper edit, +12V fill or canonical adoption. New items
that would need separate approval: two profile bindings (one per run), the second
of which can only be written after run A's identity exists; and, to make a future
timeout informative, adding cgroup `cpu.stat` sampling to the telemetry (an
implementation change to the payload, offline-testable, no resource change).
Residual risk: B.Cu is unmeasured and may itself exceed 260 s; that would be a
recorded failure under the same no-retry rule.

Alternative with lower cost: no further run. The saved evidence (run 3's island,
the independent review, the diagram) already gives a human reviewer a concrete
target at U1105.12, and the class change would not alter what that reviewer sees.
This analysis makes no recommendation between the two; it is a product decision
about whether the oracle's class is needed before a repair proposal.
