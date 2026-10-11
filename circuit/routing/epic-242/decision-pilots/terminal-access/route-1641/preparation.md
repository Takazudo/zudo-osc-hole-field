# F3/two-A execution binding awaiting admission

**Source preparation only. No native execution is admitted.** Parent accepted
the verified F3/K1402 no-improvement result and released reservation1623. Its
empty proposal remains byte-identical and unapplied. All native slots are free.

Prospective admission: `epic242-f3-two-a-route-20261011-1641`.
Prospective execution branch: `integration/epic-242-f3-two-a-access-v1`.
Worker: `f3-two-a-access-v1-<GITHUB_RUN_ID>-1`.
The branch has not been created. Parent must admit the exact orchestration commit
before its one-time branch-creation push. Exact proposed orchestration: `791195aac846841926357c480894421fff562b9e`.
[source-pin.json](source-pin.json) records this immutable admission target; later
integration evidence commits are not substituted for it.

Frozen method: `6f0783335fa23d760877a91db3b63f93c039b4b4`.
Frozen packet SHA256:
`10be49ae32997a36c54436e48226a295678e47dda1fc1c14f4569c72ef4bdd92`.
Two-A fixture-lock SHA256:
`00dd82fa7c42d770204b0177e1f48eb0592a6595696b16bf8f9a76ae4c729f60`.

[request.json](request.json) binds the exact fixture, source hashes, command,
worker and evidence identities. The runner and workflow differ from reviewed
K1402 orchestration `bf671866e73e8d133726090c0e8295ccdd41c5c1` only in the
selected existing two-A case and corresponding branch, admission, worker,
script and evidence identities. The adapter, shared router, guard and packet
are unchanged. Admission1641 is identical in the workflow and runtime check.

## Unchanged comparison and limits

The four demands remain +12V U2309.4–C2331.1, −12V U2309.11–C2332.1,
AGND C2338.2–U2312.5 and BP_INT U2306.5–C2312.1. Both rail demands remain
blocked and explicit. Shared bounds are `[205.15,236.02,246.775,270.91]` mm;
0.1mm raster, 50,000 expansions/search, 6mm window, 0.5/0.3mm rail/signal
widths, 0.25mm clearance and 0.6/0.3mm via diameter/drill remain fixed.

Exactly one worker and 300 seconds including both gated probes and routing;
6GiB memory with no swap, 12GiB global cap, 2GiB free floor and 2.5GiB early
abort. The reviewed host checks, pinned Python dependencies/KiCad image,
complete-history method checkout, 43-minute job cap, first-attempt-only
branch-creation guard, failure retention and cleanup checks are unchanged.
No repeat, retry, fallback, rip-up, cut or increased budget is authorized.

## Source verification

[Independent review](independent-review.json) passed with no findings. The
reviewer compared runner/workflow bytes directly against bf671866 and verified
the exact permitted delta, frozen method/packet/lock and generated route argv.
All70 terminal-access source tests pass, including19 matching two-A orchestration
and inherited receipt regressions; the independent reviewer also reran all19
final binding tests successfully. Native execution is mocked
or forbidden in these tests. Circuit contract, docs/generated-output/TypeScript,
and baseline input preservation checks pass. Component scope is manual68lines,
zero declared placements; schematic/placement binding was not performed.

[Input verification](input-verification.json) rechecks the complete20,195,283-byte
artifact11705755937 from run38148185181, SHA256
`ed8de7933f40369ecefb3ea28f382662923b414298e0cdb72ed5e32578e64e3f`.
All319 CRCs,203 original before/context members,297 fixture files and427
method/control hashes pass. The board, dump and access-plan hashes match the
frozen packet. No saved-board search or fixture regeneration was performed.
Full regeneration is NOT RUN because it invokes native KiCad and this scope
admits source preparation only. No canonical hardware or copper changed.

Actual-host qualification and native execution remain NOT RUN. Apply, settle,
fresh-copy, full-warning audit, adoption, merges and closures remain unadmitted.
