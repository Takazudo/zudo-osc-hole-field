# Corrected matched-demand comparison proposal (#253)

Status: SOURCE PROPOSAL ONLY; NOT ADMITTED, NOT RUN. This is a bounded direct-connectivity diagnostic, not plane-feed completion, a physically realized split, or architecture acceptance. Existing mechanical/power blockers remain independent. The old sample manifests stay as historical evidence; these corrected targets are owned here.

## Frozen comparison

`matching-spec.json` predeclares 12 real demands: both supply polarities, sensitive signal, and return in each of O1/F3/E1. `matched-demands.json` authenticates their exact pad/net IDs, native geometry and BOTH_OPEN state on K and both candidate owners. Full original groups include track/via UUIDs. Remote routing goals are the same two pad masks on every board, never a larger K copper group. All board obstacles remain loaded. Bounds use native PCB coordinates: source/mechanical coordinates +[100,50] mm. No cuts, rip-up, plane fanout, full-board fallback or retry is allowed.

The nine fresh, independent fixtures are:

| Stage | Domain | Boards (separate fixtures) |
| --- | --- | --- |
| 1 | O1 | K1402, two-A |
| 1 | F3 | K1402, two-A |
| 1 | E1 | K1402, two-B |
| 2 | O1 | three-A |
| 2 | F3 | three-B |
| 2 | E1 | three-C |

Stage 2 can reuse stage-1 K evidence only if source/spec/tool/geometry/budget hashes are identical. Do not pick winning samples after results. An incomplete or failing stage remains recorded. These are nine board/domain cases, not nine independent boards. No pooled raw-open count establishes an advantage.

## Exact preparation and transaction

Execute from a clean checkout at the final published integration SHA. Use the existing pinned numerical virtualenv Python (numpy2.2.6/scipy1.15.3/shapely2.1.2 per numerical-requirements.txt), not an arbitrary Python backend. The route adapter checks installed package metadata before numerical imports and records actual versions; source-file hashes alone cannot establish backend equality. Set `P=circuit/routing/epic-242/decision-pilots`, `F=design/partition/core-split/candidates/pilots/generated/253-<domain>-<board>-<admission>`. Replace angle-bracket fields with the actual predeclared case and parent receipt; they are not granted admissions. Artifact directory contains the six full ZIPs in `artifacts.json`.

Source-only preparation:

```sh
python3 "$P/prepare_matched.py" --artifacts /path/to/verified-zips --domain <domain> --board <board> --output "$F"
```

It verifies the baseline, all six full ZIPs, exact board/dump bytes and the matched ledger. `fixture-lock.json` binds source commit, all method/helper hashes and every prepared input. The K library tables alone are rebound to authenticated frozen context. This recovered settle is explicitly historical; subsequent native parity remains required.

Each following native/search command needs a **separate explicit parent admission**, immutable full Git SHA and reviewed `run.sh` SHA256. Wrap its command in `python3 scripts/kicad/native_resource_guard.py --admission-id <receipt> --worker <unique-worker> --sha <published-full-sha> --hook-sha256 <reviewed-run-sha256> --seconds <limit> --evidence <new-evidence-directory> <command>`. Preserve the existing guard's exact command syntax (no standalone `--`). Run sequentially with one worker, 6 GiB; global capacity stays at most two workers /12 GiB with ≥2 GiB free. Existing heavy-guard admission policy also applies. No admission is inferred from this document or an old approval card.

| Step | Command inside guard | Wall limit |
| --- | --- | --- |
| Route exact anchors | `python3 "$P/route_matched.py" --domain <domain> --board <board> --fixture "$F"` | 300 s |
| Apply private proposal | `bash scripts/kicad/run.sh python3 scripts/pcbgen/grid_apply.py "$F/before/osc-core.kicad_pcb" "$F/matched-proposal.json" --output "$F/after/osc-core.kicad_pcb"` | 300 s |
| Settle after | `python3 scripts/partition/core_split_candidates.py settle --board "$F/after/osc-core.kicad_pcb"` | 600 s |
| Prepare fresh copy (source-only, outside guard) | `python3 scripts/partition/core_split_candidates.py fresh-copy --output "$F"` | — |
| Settle independent fresh | `python3 scripts/partition/core_split_candidates.py settle --board "$F/fresh/osc-core.kicad_pcb"` | 600 s |
| Full native warning audit | `python3 scripts/partition/core_split_candidates.py audit-pilot --output "$F"` | 300 s |

The fixed router uses 0.1 mm raster, 0.5 mm rails/AGND, 0.3 mm signal, 0.25 mm clearance, 0.6/0.3 mm vias, 50,000 expansions per search and the common endpoint envelope +6 mm. Native settles require three equal complete signatures within six refills. Pinned KiCad10.0.6 remains mandatory. Record preparation, route, apply, settle and audit wall times separately and the guard's peak/resource evidence. A timeout, OOM, error or missing proof is INCOMPLETE, never a pass. An attempted zero-addition proposal is NO IMPROVEMENT; an unattempted case is NOT EXERCISED. Stop without increasing budgets or retrying. The 300 s audit may be insufficient; that produces incomplete evidence, not relaxed warning coverage.

After saved native proofs exist, source-only replay:

```sh
python3 "$P/evaluate_matched.py" --fixture "$F" > "$F/matched-result.json"
```

The evaluator revalidates exact before/after/fresh bindings, all original pad groups/copper, unchanged nonrouting objects, complete native warning evidence and fresh agreement. The evaluator requires exact after/fresh PCB bytes (no implicit zone or artwork exception), project/rule equality and every locked context file; serialization drift fails closed for review. It then evaluates exact matched closures and every source-connected rail/AGND equivalence in the touched package/bypass closure. Every partition-induced repair earns **zero** K-relative credit. Counts of equivalent pairs are not independent missing wires. Coupled connectivity remains false while any required return/rail debt remains. The four-pair route may leave such debt; that is an informative failure of this minimal diagnostic, not permission to add unbudgeted repairs. Any broader repair comparison needs a separately reviewed predeclared method and equal K budget.

Even coupled connectivity success leaves `accepted=false` and `adopted=false`. The final comparison must attach all raw artifacts, exact command/admission/resource receipts and independent review. A claimed split advantage requires a source-identical difficult demand resolved within the same budget while K does not, a geometric explanation and complete coupled/preservation gates. Physical service/power realization must be resolved before architecture selection. No canonical output, production routing, closure, PR merge, fabrication or energization follows.
