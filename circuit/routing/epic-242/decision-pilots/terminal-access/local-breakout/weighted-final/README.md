# Final weighted attempt: invalid complete chain; case retired

The one authorized final source experiment found a graph path for the original
C2312.1 → U2306.5 demand, then failed the unchanged emitted-chain new-via spacing
gate. **No candidate was emitted. The unchanged-placement case is retired.**
No further heuristic variant, budget increase, native execution or adoption
follows this receipt. This is not proof that placement is physically impossible
or that moving components is necessary to fix this particular rejected path.

## Exact execution and rejection

Execution source: `f5626849b368fb17cf11ccb729a6460dae43b4e0` on the integration
branch. [Prelaunch intent](intent.json) is historical: its NOT YET EXECUTED
status is superseded by [execution receipt](execution-source.json) and
[terminal result](result.json), retained byte-for-byte. Connectivity was
confirmed with successful shell and GitHub remote reads at 17:46:51 UTC,
2026-10-11; local and remote checkpoint were both `5357a4dab249f12d61c9f309d6e4c6054eabafb9`.
The experiment source was committed and pushed before the only execution.

Fixed weight 2, higher-positive-g tie breaking, then deterministic node order;
unchanged graph, geometry, original goals, layer/via rules and shared caps:
50,000 expansions / 250,000 exact checks. The 300-second bound is the existing
soft feasibility-search wall check, not a whole-process watchdog.

| Measure | Result |
|---|---:|
| Expansions | 15,607 |
| Discovered states | 7,164 |
| Exact checks | 26,251 |
| Measured method interval | 4.544200353 seconds |
| Graph / stitched nodes | 272 / 277 |
| Diagnostic-only emitted rows / vias | 74 / 3 |
| Candidate / native execution / adoption | None / None / None |

Reopening explains expansions exceeding distinct discovered states. The retained
[graph path](graph-path.json) is invalid diagnostic data, never proposal copper.
It uses an original B.Cu C2312 source alternative, not the added In2-only
breakout at `(216.8,263.3)` mm.

The new grid via at `(241.4,254.5)` mm and the goal attachment via at
`(241.094427,254.188854)` mm are **0.436103992 mm apart**, below the unchanged
**0.700001 mm** minimum by **0.263897008 mm**. Their UUIDs and complete rows
are in [rejection geometry](new-via-rejection.json) and the
[independent review](independent-review.json). The third via at
`(224.5,261.1)` mm does not form the offending pair. Full cumulative-fill
validation was **NOT RUN** because the emitted-chain gate rejected first.

The source and input hashes in the execution receipt, raw result and independent
review match. Original dump SHA256:
`613a358b340962e2d1fb13cd898fe8a9558edcbf1a5d69cb93b6d2bd7629e97c`.
Result SHA256:
`9ac4d889383104907f2594c9bd0ec672251ad380c80106785e2322ace6f4c296`.
The original dump recovery instructions remain in the
[prior region receipt](../region-stop/README.md); no local-only fixture is
represented as a durable artifact. The source command was:

```sh
PYTHONPATH=/tmp/epic242-numerical-deps python3 circuit/routing/epic-242/decision-pilots/terminal-access/weighted_transition_candidate.py \
  --candidate design/partition/core-split/candidates/pilots/generated/f3-two-a-c2312-breakout-v1-reviewed \
  --output /tmp/epic242-f3-repair/weighted-final-attempt
```

This records the consumed attempt; it is not a request to replay it. No
`source-candidate.json` exists. Independent review reconstructed only the
retained stitch/rows and offending pair, without another search.

## Next candidate recommendation

Use [the concrete placement handoff](placement-recommendation.md) for a new,
separately assigned #245 candidate under Epic #242, then return its evidence to
#253. It specifies a bounded F3 integrator-cluster placement task, original pad
identities, a 24-reference sensitive/bypass closure, preserved copper accounting
and pre-native exit gates. It does not apply a placement or start another lane.

All four original demands remain unresolved as a set. U2309 rail escapes and
AGND are unchanged. No architecture winner, fresh native closure, DRC/parity,
refill, full-warning audit, eligibility or hardware acceptance is claimed.
Fixed panel, circuit intent, harness IDs/Refs/full pin order, noncore poses and
accepted copper remain unchanged. All native slots are free.

## Verification

PASS: 101 terminal-access source tests (including seven weighted-order tests),
`pnpm circuit:check`, `pnpm check`, frozen baseline verification and independent
source/result review. [Test output](tests.txt) and [project checks](pnpm-check.txt)
are retained. Baseline verification covers 1,881 frozen original inputs plus two
reviewed tool replacements, 195 harnesses / 390 endpoint references and original
pin maps/poses. JL117/JR129/core1402 and DRC/parity0/0 are inherited evidence,
not fresh native results. Component scope remains manual68lines/zero declared
placements, with no schematic/placement binding. Full regeneration is NOT RUN
because it includes unadmitted native operations. Peak memory was not measured.
