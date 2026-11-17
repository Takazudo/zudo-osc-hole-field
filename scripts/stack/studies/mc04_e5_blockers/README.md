# E5 blocker attribution diagnostic

This is a frozen source diagnostic for U4524/U4526/U4527, not a placement search
or a simultaneous exchange trial. The historical `replace_all` initialized its
field with **all 438 displaced footprints removed**, then inserted accepted moves
in search order. Consequently, removing these three IC originals cannot by itself
claim novel freedom over the historical failed searches. The earlier Cloud
three-IC exchange suggestion did not establish that causal premise.

This diagnostic reconstructs all 412 accepted transformations and retains all 26
unresolved original bodies as conservative liabilities. Each individual query
excludes only its own target; the other two E5 originals remain obstacles. This
current conservative scene is more constrained by retained bodies than the
historical initial removal field. It is not a reconstruction of the exact
historical per-package search state and does not repeat its acceptance claim.

The finite domain is 2,401 existing ring offsets per target (0.25 mm, 24 directions,
up to 25 mm), three targets on their original B face and original orientation.
Every point records **all simultaneous blockers**, using a content-addressed
registry so repeated obstacle geometry need not be duplicated. Reviewed R1 scene
construction and four-decimal numerical normalization are reused. Courtyard,
complete own-face pads, opposite-face through-hole restrictions, board margin,
fixings, field/slot/tail/latch and retained forbidden constraints are preserved.
The diagnostic never stops at the first blocker and never changes an obstacle.

Classes distinguish fixed link/slot/tail/latch/fixing/outline constraints,
identity-backed fixed panel hardware, stationary bodies, accepted bodies and
unresolved liabilities. Fixed hardware is grounded in the pinned placement lock
and the retained model's panel identity sets. Other bodies have UNKNOWN
movability: "stationary" and "accepted" do not grant an exchange permission.
The source fixing circles are fixed even where no separate mounting footprint
identity is supplied. No fixed object is ranked as an exchange candidate.

C4544 remains at its accepted K/B origin (189.2026,136.8974); C4541 and C4543 remain
stationary. Their geometry is reported as retained evidence, not a chosen move.
The pinned E5 logic receipt supplies all 45 external contacts. Its conditioned
logic timing evidence still supplies no physical layout allowance.

A non-null `all_obstructions_are_named_accepted_bodies` is only a set attribution:
all current predicate hits at that point belong to the listed accepted bodies.
It does not remove them, establish where they could move, compare successfully
with the old search, or prove a simultaneous arrangement. Empty-hit points do not
become selected placements. `selected_placements` and `adopted_placements` remain
empty. There is no candidate score, ranking, best point, first-fit output, domain
widening, field movement, placement adoption or hardware acceptance.

Run the small synthetic tests without loading the actual geometry:

```sh
python3 -B scripts/checks/frozen_studies.py discover scripts/stack/studies/mc04_e5_blockers
```

Actual 7,203-point diagnostics require separate coordinator review/admission:
1 CPU, 1 GiB memory, zero swap, 128 PIDs, total 600 seconds, machine-wide shared
heavy lock covering actual execution, verified termination/cleanup, one attempt
and no automatic retry. This script does not supply those external controls.

```sh
python3 -B scripts/stack/studies/mc04_e5_blockers/study.py --output "$PWD/.circuit-cache/mc04-e5-blockers/result.json"
```

The output is reserved exclusively before analysis within this worktree's ignored
cache; failures retain a diagnostic receipt. Source files and the ignored E5
logic result are pinned in `spec.json`; absence or change fails closed. The
ignored receipt must be retained with an authorized handoff for another checkout.
No native KiCad, placement search, routing, DRC, fill, formal adoption or
manufacturing is performed. Real diagnostic NOT RUN during implementation.
