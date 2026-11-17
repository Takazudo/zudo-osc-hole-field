# MC04-R1: U4324 and C4341 room-only study

DS-135 admits this isolated, offline rigid-translation experiment. U4324 is
SN74HC00DR and its declared +5V/AGND decoupler C4341 is GRM188R71H104KA93D.
Nothing here modifies a board, canonical placement, generator, net or adopted
part. Native KiCad, DRC, fill, routing, adoption and manufacturing are not run.

`spec.json` freezes the exact engineering source
`2c53715d49a4a7639723595590d1fd4eeb3a3c1f`: whole file hashes (including board
bytes, extraction/predicate sources, partition, fixing and envelope inputs), the
438 replacement records (412 accepted candidates and 26 unresolved), and the
pair's exact identities, units and pin nets. Input checks occur before geometry
loading and again after the study. Missing or changed inputs fail closed.

The scene applies every retained accepted translation/turn/face to complete
courtyards and pads. All stationary parts and all 26 unresolved original bodies
are retained; only the proposed pair is excluded from its own collision tests.
Retired headers are excluded only by the existing pinned GateModel semantics.
The retained Field supplies fixed link/slot/tail/latch regions, fixing circles,
outline margins and forbidden regions. Retained Obstacles supplies courtyard,
hole and opposite-face pad growth. Own-face pads are additionally included,
even beyond a courtyard. No obstacle is removed just to produce a fit.

A conservative union may contain overlaps among frozen objects, including old
unresolved liabilities beneath slots. Such overlap observations are recorded,
not represented as successful assembled placements and not discarded. Missing
identities, changed accepted records, impossible source transforms, malformed
rectangles, nonfinite values and a conflicting source pair fail admission.

A finite causal pass checks whether removing C4341 creates any otherwise valid
U4324 position. Without that evidence, the result is `NO_NEW_OPPORTUNITY` and no
pair pass runs. With evidence, one rigid-pair pass stops at the first valid
candidate or `NO_RIGID_PAIR_FIT`. The retained rings are 0.25 mm / 24 directions,
ascending radius through 12 mm then up to 25 mm (2,401 unique candidates); no
rotation or face flip occurs. Every courtyard and pad of both members is checked.
A `ROOM_WITNESS_ONLY` result leaves all canonical 26 unresolved and proves no
electrical, routing, mounted-height, access or Gate A acceptance.

## Lightweight tests

```sh
python3 -B scripts/checks/frozen_studies.py discover scripts/stack/studies/mc04_r1
pnpm circuit:check
```

## Actual study admission

Do not invoke the actual study until the coordinator verifies effective 1 CPU,
1 GiB RAM, zero swap, 128 PIDs, the same machine-wide heavy lock and total 600 s
(setup 60, analysis 480, cleanup 60), including termination of the complete process
tree before release. One attempt, no automatic retry. This script does not itself
establish those external controls. The admitted launcher can invoke:

```sh
python3 -B scripts/stack/studies/mc04_r1/study.py \
  --output "$PWD/.circuit-cache/mc04-r1/result.json"
```

The result path must be in this worktree's ignored cache and must not already
exist. JSON records exact hashes, frozen-overlap observations, counts, constraint
violations and the narrow result scope. Inputs and outputs must be independently
reviewed before any further geometry step. A negative result cannot authorize a
wider search, another instance, a part substitution or movement of another object.

Implementation work note: pre-edit circuit check PASS (84 manual records, 445
declared placements unverified; pin-asset check performed). Actual study has not
been run during implementation. No regeneration is performed because the admitted
scope forbids native/aggregate runs and canonical outputs; source is unchanged.
