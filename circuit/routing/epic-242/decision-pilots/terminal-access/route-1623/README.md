# First F3/K1402 route: no improvement

[Run 38155571727](https://github.com/Takazudo/zudo-osc-hole-field/actions/runs/38155571727),
job114517741476, attempt1 completed successfully under admission
`epic242-f3-k1402-route-20261011-1623`. It produced **zero additions, cuts or links**.
No copper was applied. The worker has exited with complete retained cleanup
evidence; parent receipt review and reservation release remain pending.

Orchestration: `bf671866e73e8d133726090c0e8295ccdd41c5c1`.
Method: `6f0783335fa23d760877a91db3b63f93c039b4b4`.
Worker: `f3-k1402-access-v1-38155571727-1`.
The execution branch `integration/epic-242-f3-k1402-access-v1` is frozen and must
not be pushed again, reset, recreated or rerun.

| Original F3 demand | Verified portals, first / second | Outcome |
|---|---:|---|
| +12V U2309.4 → C2331.1 | 0 / 6 | No valid saved access; original demand retained |
| −12V U2309.11 → C2332.1 | 0 / 3 | No valid saved access; original demand retained |
| AGND C2338.2 → U2312.5 | 3 / 3 | Search exhausted after 149 expansions |
| BP_INT U2306.5 → C2312.1 | 3 / 3 | Search exhausted after 1,077 expansions |

The original 50,000-expansion cap, shared bounds, widths, clearance, via rules,
obstacles and successful copper remain unchanged. Three saved candidate signal
launches were rejected against retained −12V via
`0f9ff359-2b0a-56f9-94e7-82b2c291d170`. The adapter reported 73.588016983 seconds;
the last guard sample was at 78.837426401 seconds within the 300-second phase,
including both gated probes. This bounded K1402 result establishes neither
physical impossibility nor an architecture winner. Both rail debts remain open.

## Retained evidence

[Full artifact11708068429](https://github.com/Takazudo/zudo-osc-hole-field/actions/runs/38155571727/artifacts/11708068429):
33,392,129 bytes, SHA256
`3076bfacc28b76e663fe111c3faa6c62c5c98f328656929a16b1627eb271fd32`.
All 317 ZIP members passed CRC and exact extracted-byte checks. The complete
boards remain in the authenticated artifact and ignored local storage; no LFS.
Direct signed-blob downloads returned403; connected GitHub transport recovered
the full artifact and decoded job log without creating credentials.

Raw proposal, diagnostics, exact fixture lock/access plan, initial/final input
hashes, host/image/source/artifact receipts, full guard/probe/cleanup evidence and
complete decoded logs are retained beside this file. The
[result ledger](result-ledger.json) summarizes their bindings.

The actual host used Python3.11.17, numpy2.2.6, scipy1.15.3 and shapely2.1.2, with
the reviewed binary identity and pinned KiCad image. Historical cohort bytes
from191a4db3 were available and authenticated. All426 method hashes plus the outer
dispatch wrapper and all297 fixture files are unchanged; all203 recovered
before/context members match the authenticated original artifact.

Both full container identities have matching gate ACK, observed live PID/cgroup
membership and retained exit0. Kernel worker peak was **581,754,880 bytes**;
minimum free memory across76 samples was **15,066,083,328 bytes**. All memory
limit/OOM events remained0. The guard retained6GiB/no-swap worker and12GiB
aggregate caps,2GiB free floor and2.5GiB early abort. Driver exit was0 before and
after cleanup. Final containers were empty; all three owned units were
inactive/not-found/settled, with no final-state errors or cleanup failures.

No native board closure, fresh DRC/parity, full-warning or eligibility acceptance
was performed. Canonical hardware and accepted JL117/JR129/K1402 are unchanged.
**Stop for parent receipt review.** Two-A, apply, settlement, fresh-copy and audit
remain unadmitted. There is no repeat dispatch, retry, budget increase, hardware
adoption, architecture-success claim, merge or closure.
