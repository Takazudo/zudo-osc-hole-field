# First F3/two-A route: no improvement

[Run38156907050](https://github.com/Takazudo/zudo-osc-hole-field/actions/runs/38156907050),
job114521653053, attempt1 completed once under admission
`epic242-f3-two-a-route-20261011-1641`. It produced **zero additions, cuts or links**;
all four original demands remain unresolved. No proposal was applied.
Independent evidence review passed. The worker has exited and cleanup is verified;
parent receipt review and reservation1641 release remain pending.

Orchestration: `791195aac846841926357c480894421fff562b9e`.
Method: `6f0783335fa23d760877a91db3b63f93c039b4b4`.
Fixture-lock SHA256:
`00dd82fa7c42d770204b0177e1f48eb0592a6595696b16bf8f9a76ae4c729f60`.
Worker: `f3-two-a-access-v1-38156907050-1`.
Execution branch `integration/epic-242-f3-two-a-access-v1` is frozen at the admitted
orchestration. Do not push it again, reset, recreate, retry or rerun it.

## Matched bounded result

| Original demand | K1402 portals first/second | Two-A portals first/second | Result on both |
|---|---:|---:|---|
| +12V U2309.4 → C2331.1 | 0/6 | 0/12 | No valid saved access; original demand retained |
| −12V U2309.11 → C2332.1 | 0/3 | 0/6 | No valid saved access; original demand retained |
| AGND C2338.2 → U2312.5 | 3/3 | 3/3 | Search exhausted after149 expansions |
| BP_INT U2306.5 → C2312.1 | 3/3 | 6/3 | Search exhausted after1,077 expansions |

The same four demands, bounds, search windows and50,000-expansion caps were used.
Two-A's additional signal landing portals did not yield a complete path. Both
cases produced zero additions; this finite method establishes neither physical
impossibility nor an architecture winner. Rail and return debt remain explicit.
K1402 reservation1623 was released by the parent; its empty proposal is unchanged.

The two-A adapter reported38.427836002seconds, including its geometry/validation
work; this is not pure A* timing. The last guard sample was43.234602684seconds
within the unchanged300-second phase including both gated probes. No timeout,
repeat, retry, larger budget, changed target, fallback, rip-up or cut occurred.

## Complete retained evidence

[Full artifact11709240803](https://github.com/Takazudo/zudo-osc-hole-field/actions/runs/38156907050/artifacts/11709240803):
17,573,972bytes, SHA256
`552347595d8d0dd2bcca5437cbf83cb31ce92ea96cb8a395598faaa493240040`.
All317 ZIP CRCs and extracted-byte comparisons pass. Complete fixture boards
remain in the authenticated artifact and ignored local storage; no LFS.
Connected GitHub transport recovered the full artifact and decoded job log.

[Result ledger](result-ledger.json), [execution verification](execution-verification.json)
and [independent execution review](independent-execution-review.json) bind the
raw proposal, diagnostics, fixture/access plan, source/input/control receipts,
full resource guard, container records, cleanup and complete decoded logs
retained here. Original [preparation](preparation.md), submitted [request](request.json)
and its [source review](independent-review.json) remain historical records;
[admission.json](admission.json) records the subsequently admitted execution.

Actual host provisioning and exact history/source/packet/image checks passed.
Python3.11.17 with pinned numpy2.2.6/scipy1.15.3/shapely2.1.2 used the retained
absolute executable and binary digest. The complete recovery artifact,
427source/control hashes and all297 fixture files authenticate before/after;
all203 original before/context members match the prior artifact byte-for-byte.

Both probes have full container identities, matching gate ACK, live PID/cgroup
membership and retained exit0. Kernel worker peak was **323,182,592bytes**;
minimum sampled free memory was **15,322,365,952bytes** across42 samples. All
memory-limit/OOM counters stayed0. Worker6GiB/no-swap, aggregate12GiB,
2GiB free floor,2.5GiB early abort and the43-minute job cap remained unchanged.
Guard and driver exits were0. Final containers were empty; all three owned units
were not-found/inactive/settled, with no errors or cleanup failures.

No native board closure, fresh DRC/parity, full-warning or eligibility gates
were run. Fixed panel,circuits,harness identities/fullpinorder,non-core poses,
successful copper and accepted JL117/JR129/K1402 remain unchanged.
**Stop for parent receipt review.** Apply, settle, fresh-copy, full-warning audit,
adoption, further routes, merges and closures remain unadmitted.

Post-run circuit/docs/generated-output/TypeScript and frozen baseline checks pass.
The70 prelaunch source tests remain applicable; no routing source changed.
Component validation scope is manual68lines,zero declaredplacements, with no
schematic/placement binding. These checks do not add native acceptance evidence.
