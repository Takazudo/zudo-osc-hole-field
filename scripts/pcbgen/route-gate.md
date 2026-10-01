# Routing completion gate

`route.py` is an orchestration gate for **unvalidated PCB drafts**. A successful
routing status requires both the full KiCad DRC/parity gate and a fresh native
ratsnest result with zero open edges. Neither is a physical or electrical-function
qualification.

## Fail-closed behavior

- `ROUTED DRAFT`, `UPDATED DRAFT` and `UNCHANGED DRAFT` cannot retain exit 0
  if the native check is missing, malformed, for another board, or reports open
  edges. Unavailable native evidence changes a provisional success to
  `PIPELINE FAILED DRAFT`; positive edges change it to `INCOMPLETE DRAFT`.
- The old `ratsnest.json` is removed before invocation. Counts must be
  nonnegative integers, not strings, floats or booleans. The board path must
  match, and board bytes must remain unchanged during collection. The inspected
  board SHA-256 is recorded in the routing report.
- Existing pipeline/router failures remain failures. Native zero cannot promote
  a timeout, and timeout exit 3 is retained even if native collection also fails.
- After preparing/refilling source copper, rule or schematic-parity errors abort
  before Freerouting. Open connections alone may proceed; warnings stay reported
  without being promoted to errors. Preparation can still repair earlier issues.
- `--refresh-ratsnest-only` is diagnostic, not a full routing recheck. It records
  the previous routing status separately and uses `RATSNEST ONLY DRAFT` for a
  successful zero-edge refresh. DRC/parity are explicitly `NOT RUN` for that
  operation. Open edges return 2 with `INCOMPLETE DRAFT`; a missing/invalid native
  result returns 2 with `PIPELINE FAILED DRAFT`. It does not retain a stale success
  badge or route the board.

The schema remains version 1 with additive receipt fields. Consumers must not
interpret `RATSNEST ONLY DRAFT` or `native_gate_status=ZERO OPEN EDGES` as complete
routing approval. Net names taken from DRC JSON remain samples. The issue-38
native collector separately supplies complete per-net cluster counts; the gate
checks their sum against the native total, their count against the named-net
count, and the collector's board hash against the inspected bytes. It preserves
these complete names and the original DRC sample separately. Failed refreshes
clear old native names and counts as well as the old success status.

## Tests

```sh
python3 -m unittest scripts.pcbgen.test_route_gate -v
```

The tests execute the real `route.main()` and its file handling against temporary
fixtures. Only external KiCad/router process calls are simulated. They cover
freshness, wrong-board/malformed data, board mutation, completion/unchanged paths,
prepared DRC failures, refresh-only status and timeout preservation. They do not
run the native oracle or prove real board connectivity.

Before accepting this change into the active issue-38 worktree, reconcile its
uncommitted orchestration edits rather than replacing that worktree wholesale.
Run the project regeneration/evidence checks, existing Python suite, and the
pinned KiCad 10.0.6 fixture/native checks through the existing guards. New physical
routing or hardware acceptance must use the actual current board sources and
receipts; old numerical solver epochs are not made current by this code fix.
