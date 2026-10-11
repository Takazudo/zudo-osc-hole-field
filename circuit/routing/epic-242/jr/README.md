# Issue 251: JR129 source checkpoint

This lane owns only `circuit/routing/epic-242/jr/**`. No canonical copper is changed. This is a source-readiness and negative-diagnostic checkpoint, not completion of issue 251. Only the coordinator can adopt copper or publish an epoch.

## Pinned inputs

- Integration input: `1da1909846dc3255888ecd36c88cee9737c85834`, epoch `epic242-e0`, coordinator PR260.
- Newer integration inspected: `6700ccb1a9a64630cd26bccf751f537f3cc25d42`. Its coordination and trimmer changes leave JR source, router and epoch unchanged. This branch retains the pinned input without discarding those accepted changes.
- Published JR129 PCB SHA256: `9e164f9e8e23a5c3911d117fd08973fc877e5f2f382be20500b8e01040b20a55`.
- Accepted retained fresh dump SHA256: `e90beeadf69cc2210d34c377b000335ea55a6815064772c81e0f925b1cd21e71`.
- [Retained native run 38041389680](https://github.com/Takazudo/zudo-osc-hole-field/actions/runs/38041389680), artifact `11665973838`, original execution source `2a10cae7ef3bd7d4df8e9500c25cada930419432`.
- Whole ZIP: 64,355,646 bytes, SHA256 `09a205f6fad78aabc490ee07124c827a18cacfde575cc1afdb2b8d3bad47f2d1`. GitHub retention expires 2026-11-09; obtain and preserve the exact artifact before expiry. It is deliberately outside Git, with no LFS.
- All 24 retained project-context files match source. Full pad identities and memberships reproduce 3,655 pads, 48,468 tracks, 3,130 vias, 80 disconnected nets and 129 native open edges: 107 signal, 22 AGND, zero rail.

`cases.json` binds every unresolved net to complete stranded-pad UUIDs, references, pad numbers, poses, layers and retained island membership. Categories describe source roles only; legal routing starts, vias, reachability and fresh native evidence remain NOT RUN. Stacked JR130 is rejected as an input.

## Diagnosed cause and prior evidence

`prior-rejections.json` preserves exact source-bound evidence, receipt hashes, artifact identities and failed search budgets. The old JR134 RB4614.2 ground cut improved 134 to 133 but split an originally connected signal group and introduced two dangling-track warning identities. Existing endpoint replay exhausted 4,621 nodes at 0.025 mm and 23,938 at 0.0125 mm; joint repair hit 300,001/300,000 in both orders. Those are different input bytes and cannot be adopted onto JR129. The unrelated stacked JR130/RB4615 no-gain pilot is evidence only.

The proposed first diagnostic changes one cause: cut exactly the same two diagnosed obstruction segments on accepted JR129 and measure current topology before choosing a restoration method. `cut-proposal.json` uses the existing grid-apply proposal schema, is bound to current PCB bytes, contains no added copper and is always ineligible for adoption. All four outside cut boundaries are retained, including the RB4614.1 pad contact that lies inside a pad polygon. The original two signal victims, AGND target, rail and AGND obligations remain mandatory for any later coupled candidate.

This intentionally incomplete cut is a negative diagnostic, not a routing improvement or permission to relax acceptance. No unchanged-budget A* replay is proposed. Parent review should decide whether a current-epoch cut measurement is useful enough to spend a native slot; an alternative is to retain the historical negative without rerunning it. Any new reconnect/routing method requires stronger review first.

## Source replay and checks

From this repository, with the exact retained ZIP stored outside tracked paths:

```bash
python3 circuit/routing/epic-242/jr/prepare_diagnostic.py /workspace/jr251-cache/jr129.zip
python3 circuit/routing/epic-242/jr/test_diagnostic.py /workspace/jr251-cache/jr129.zip
python3 circuit/routing/epic-242/jr/native_diagnostic.py /workspace/jr251-cache/jr129.zip --label 251-rb4614-cut-a1
python3 circuit/routing/epic-242/baseline/verify_inputs.py
pnpm circuit:check
```

Nine focused source tests PASS, including archive corruption, stale JR130, equal-count wrong memberships, pose drift, missing/duplicate cuts, retained pad anchors, deterministic replay and missing native admission. Source preflight PASS; inventory/component contract PASS (68 lines); frozen-input validation PASS (1,883 files and 195 complete harness identities). Shell syntax and Python compilation PASS. Canonical routed inputs were archived and hash-preserved before checks. No regeneration was run: `regen-all.sh` invokes native KiCad and awaits admission. Default heavy CI is deliberately skipped because it can launch four native jobs.

## Exact native command for parent review — NOT RUN

Run only after the parent approves this command and assigns a unique global native slot. Replace `PARENT_ASSIGNED_SLOT` with that assignment, not an invented token:

```bash
bash circuit/routing/epic-242/jr/run_native.sh /workspace/jr251-cache/jr129.zip 251-rb4614-cut-a1 PARENT_ASSIGNED_SLOT
```

The existing machine-wide heavy guard encloses one pinned KiCad Docker container. The entire driver and every native child are capped at 6 GiB RAM, no additional swap, one CPU, 128 PIDs, no container network, and 1,200 seconds. The existing 2 GiB free-memory gate is retained. Parent scheduling must additionally reserve at most two native workers globally (12 GiB aggregate). Do not dispatch the default workflow. Preload the pinned image and verify the existing heavy guard is operational; missing dependencies or admission are blockers, never grounds for unguarded fallback. The image dependency preflight requires numpy, scipy, Shapely 2 and pcbnew; no fallback installation occurs.

The command checks pinned KiCad 10.0.6, independently settles the baseline, compares full retained native memberships and refuses byte drift. It applies the exact cut with existing `grid_apply.py --output`, measures settled and independent fresh topology, records original group splits, native warnings/errors/parity and existing `route_shards.delta`/retention evidence. It never invokes merge or promotion. Workspace names are unique under `.circuit-cache/osc-jack-right-grid-251-*`; existing evidence is never overwritten. Receipts always say adopted=false. Full adoption audit, restoration, improvement, regeneration and new native results remain NOT RUN.

After any execution, return the entire receipt and retained reports to the coordinator. No gain, unsettled/fresh disagreement, context drift or new warnings/errors must trigger adoption. Continue source work or seek stronger review of one diagnosed restoration change; coordinator alone publishes any subsequent epoch.

## Startup provenance

Workspace startup instructions were delivered through the user-supplied AGENTS message; no saved environment startup field was supplied. The read-only personal loader succeeded and its complete output was consumed, verifying the installed Codex/Claude snapshot and personal skill indexes. Runtime bridge restoration was separately rejected by automatic approval review because it could modify the restricted runtime AGENTS path. No installer, profile rebuild or workaround was attempted. Explicit loading does not establish native host discovery.
