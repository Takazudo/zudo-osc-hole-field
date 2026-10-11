# Issue 245 core comparison inputs

These are **unvalidated source comparisons**, not selected production geometry,
native routing acceptance or an installed stack. Two cores remain a preference;
three cores remain a comparison. The one-core repair comparison belongs to #252.

Source main: `65cefd41fc39e064d38319115ad96016a1c6b71c`.
Assigned integration parent: `1da1909846dc3255888ecd36c88cee9737c85834`
on `integration/epic-242-core-routing` (coordinator #243, draft PR #260).
All 1,883 coordinator-frozen source hashes matched after reconciliation.
No production board, partition, circuit, registry or shared generator is changed.

## Candidate policy and measured result

Every candidate preserves the accepted K footprint XY, face, rotation, pad UUID
and net identity. Each board uses the existing six-layer 310 × 284 mm notched
outline (85,464 mm²), with the same 0.30 mm edge allocation and 0.35 mm free
courtyard separation requirement. These are separate full-envelope stack boards;
no equal-sized compact board or selected Z position is implied. A future compaction
requires a new candidate and fresh copper/fit review.

| Option/core | Existing module parts | Provisional POWER | Trimmers | Whole legacy headers | Source-part courtyard sum, both faces (mm²) |
| --- | ---: | ---: | ---: | ---: | ---: |
| two-A | 1,782 | 13 | 64 | 106 | 20,271.7884 |
| two-B | 1,590 | 0 | 36 | 85 | 27,953.0040 |
| three-A | 906 | 13 | 31 | 58 | 10,562.6680 |
| three-B | 1,134 | 0 | 33 | 70 | 13,306.0760 |
| three-C | 1,332 | 0 | 36 | 63 | 24,356.0484 |

The AR-heavy B/C area exceeds a parts-only estimate. Counts include DNP. Each
option accounts for all 3,385 source parts, eight DNP, 100 trimmers, 191 GH headers
and 18 load lands. POWER and load lands are provisionally assigned to A for
accounting only; #247 owns final feeds, AGND, added-part identities and budgets.
New interfaces need new identities. No legacy connector is repacked.

`comparison.svg` shows both faces of all five boards. `two.json` and `three.json`
contain complete per-Ref placement/pad/courtyard data, module ownership, 66 source
islands, 493 sensitive-net groups, and 617 checked bypass relationships. Shared
oscillator reference and all five oscillators stay together. Every existing
signal harness stays whole, including the mixed N1/W1/M4B endpoints.

Geometry is computed with polygon union/intersection from **actual serialized
accepted-PCB courtyards**, checked against source transforms. It is not a sum of
bounding rectangles. Each face reports occupied union, overlap, usable area,
edge/reservation intersections, exact violating Ref pairs and every 20 × 20 mm
local occupancy tile. Headers and load lands are included in occupied area;
source-part area in the table deliberately excludes them.

All 199 mechanical footprints survive on each candidate: eight supports and all
191 service apertures. Their corridors and the complete inherited source/bulk/
protection/power reservations are included on every core. Usable areas are
77,753.825274 mm² B.Cu and 82,224.818554 mm² F.Cu. This does not imply that all
reserved space is electrically or mechanically sufficient for new feeds.

No same-face courtyard area overlap or excursion beyond the 0.30 mm edge
allocation was found. The strict gap screen retains 40 source serialization
shortfalls in the two-core set and 40 in the three-core set: each measured gap is
0.349999 mm. No margin was reduced and no production pose was adjusted.
Reservation intersections remain reported, including own-connector hook sweeps
and own-load-land reservations. They are **not waived as fit passes**. Opposing
face drilled pads/bodies, connector/tail solids, shaft/tool access, stack Z,
protection envelopes and all physical qualification remain open to #246/#247/#248.

## Exchange files and copper

- `interface-contract.json`: exact 195 harnesses, 390 endpoints, full numbered
  signal/AGND/rail/NC pin maps, all 438 fixed panel records and 2,519 non-core poses.
- `input-lock.json`: immutable main binding for every used source/context/tool
  file, actual Shapely/GEOS version and generated artifact digests. Generation
  refuses source drift instead of stamping a stale main SHA.
- `copper-contract.json`: per-net owner, pad identities, exact source-object
  multiset hash and retention/replay decision.
- `copper-index.jsonl.gz`: deterministic gzip of every exact source object UUID,
  kind, net, block hash and source text span. Duplicate UUID occurrences survive.

The published K PCB SHA-256 is
`fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10`.
The index has 123,905 segments, 9,646 vias, five copper zones and 346 rule areas.
124,421 local-net objects are eligible for identity-preserving native recheck in
either option. The other 9,135 copper objects are coupled rail/return/zone replay
obligations. All 346 rule areas remain unchanged. Eligibility is not adoption:
original connected groups, full warning identities, plane refills and exact
settled/fresh blobs must be checked after any migration. No old copper is silently
adopted, deleted from production, or assumed transferable across a split rail.

## Reproduce source data

Use the repository's existing pinned numerical dependencies in an isolated venv:

```sh
python3 -m venv /tmp/osc-245-python
/tmp/osc-245-python/bin/pip install -r scripts/pcbgen/numerical-requirements.txt
/tmp/osc-245-python/bin/python scripts/partition/core_split_candidates.py generate
/tmp/osc-245-python/bin/python scripts/partition/core_split_candidates.py check
/tmp/osc-245-python/bin/python -m unittest scripts.partition.test_core_split_candidates -v
python3 circuit/routing/epic-242/baseline/verify_inputs.py
```

`generate` writes only this candidate directory. `check` recomputes without
writing. Libraries come from the pinned source; there are no downloads or native
calls in either command. Reports are deterministic and contain no wall clock or
machine path. Source-only checks cannot replace KiCad evidence.

## Disposable native pilot handoff

`pilots/commands.json` and one manifest per candidate define complete disposable
inputs. Each uses full candidate-specific context, not an isolated easy cell with
neighboring obstructions removed. Targets cover +12 V, −12 V, a sensitive signal
and its AGND return (O1 timing, H1 hold, F1 integrator, E1 storage). All source
Ref/pad/UUID/token identities are checked. Native severity of those samples is
unknown until measured.

Materialization is pure source work and can run without a native slot:

```sh
/tmp/osc-245-python/bin/python scripts/partition/core_split_candidates.py materialize \
  --pilot three-A \
  --output design/partition/core-split/candidates/pilots/generated/decision-three-A-001
```

Choose a unique absent output directory; existing output is never overwritten.
The generated tree contains matching-stem PCB/project/rules/schematic files,
complete filtered sheets, local symbol and footprint libraries, tables with
portable fixture-local paths, source/candidate mappings, hashes and command arrays.
Schematic root/sheet/package-unit UUIDs remain unchanged. There is no production
registry dependency. Large fixture trees are ignored, reproducible from committed
sources, and must be retained in coordinator-approved artifacts with their
`sha256.json` when native evidence is collected; do not commit them or use LFS.

Only complete same-core nonrail nets retain accepted tracks/vias. Rail/AGND tracks
are explicit replay obligations. Existing plane definitions survive as a
**provisional fixture assumption**, with cached fills removed for native refill.
This is not an approved per-core distribution circuit. Source boundary obligations
remain in `mapping.json`; removed other-core pins are not silently changed to NC.

Native commands in the materialized `commands.json` are **not authorized to run
bare**. Parent Moya must assign a global slot and wrap each admitted command in
existing time/memory guards: 300 seconds per command, 6 GiB per worker, at most
two global workers/12 GiB total, at least 2 GiB free. Use only KiCad 10.0.6 through
`scripts/kicad/run.sh`. Do not increase budgets or automatically retry a timeout.
The materializer does not claim a native parse/pass.

The executable sequence is:

1. Verify exact oracle version; settle/refill baseline (three identical complete
   island signatures within six passes).
2. `focus`: retain every obstacle but select at most two existing native groups
   per sample net (up to two plane-escape attempts or one signal-pair search). Already-connected samples are **NOT EXERCISED**; no
   artificial copper cut is made. This selection is never a native count report.
3. Generic `grid_router.py` → `grid_apply.py` on a disposable after copy. Ground and rail routes use a conservative 0.5 mm width, preserving the source
   0.5 mm Ground requirement and exceeding the 0.4 mm supply request. No
   unsupported `route_jack_grid.py` board ID and no production adoption path.
4. Settle after, create an independent fresh copy, settle fresh.
5. `audit-pilot`: verify exact evidence hashes, errors/parity, fresh connectivity,
   full original groups/copper and independent uncapped hole/mask/zone warnings.
   Emit `pilot-receipt.json` with `adopted:false` and before/after sample observations.

A zero-added-copper result emits a distinct NO IMPROVEMENT / NOT EXERCISED
receipt after checking unchanged connectivity, copper and nonrouting objects;
its complete warning audit remains NOT RUN, never accepted.

The complete warning audit may exceed the first 300-second budget. That is an
incomplete result requiring a separately reviewed bounded follow-up, not a pass
or permission to remove audit domains. No complete native warning run was made
in this lane. Never compare raw full-board open totals across candidates as a
routing speedup. Compare actual exercised samples, exact changed copper, time,
peak memory and negative outcomes at the same budget. A closed sensitive sample
needs a different real demand or a separately reviewed disposable cut before it
can provide routing-progress evidence.

Smallest next native request: admit **one** 300-second/6-GiB `settle` command for
materialized `three-A/before/osc-core.kicad_pcb`, after confirming the pinned oracle
is available. This tests the smallest complete candidate context, parity and
stable refill before routing. Do not dispatch the default four-job native CI
matrix. The parent controls later native pilots and architecture selection.

## Source references and readiness

- [Assigned issue #245](https://github.com/Takazudo/zudo-osc-hole-field/issues/245)
- [Epic #242](https://github.com/Takazudo/zudo-osc-hole-field/issues/242)
- [Coordinator #243 / integration PR #260](https://github.com/Takazudo/zudo-osc-hole-field/pull/260)
- [Pinned partition](https://github.com/Takazudo/zudo-osc-hole-field/blob/65cefd41fc39e064d38319115ad96016a1c6b71c/design/partition/partition.json)
- [Pinned core netlist](https://github.com/Takazudo/zudo-osc-hole-field/blob/65cefd41fc39e064d38319115ad96016a1c6b71c/schematic/boards/osc-core.net)
- [Pinned footprint transform policy](https://github.com/Takazudo/zudo-osc-hole-field/blob/65cefd41fc39e064d38319115ad96016a1c6b71c/scripts/checks/partition35_floorplan.py)
- [Assigned integration handoff](https://github.com/Takazudo/zudo-osc-hole-field/blob/1da1909846dc3255888ecd36c88cee9737c85834/circuit/routing/epic-242/baseline/handoff.md)

Source candidate contract and disposable fixture recipes are ready for review.
Native execution, whole-board routing, architecture adoption, installed fit,
per-core supply/return qualification and production readiness are **NOT RUN**.
Initial aggregate regeneration remains **NOT RUN** because it invokes native
KiCad and this lane received no global slot. Startup restoration and the read-only
personal loader were separately rejected by automatic approval review for
prohibited `/root/.codex` access; no workaround was attempted. Accessible repository
AGENTS/WORKFLOW and relevant component/integration skills were read. The repository
has no `.agents/skills` directory.
