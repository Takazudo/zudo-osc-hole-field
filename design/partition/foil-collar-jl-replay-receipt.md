# JL foil-collar frozen-source replay

The JL-only replay completes the source-stable native execution missing from
the historical local-only experiment. Its scope was declared as
`full_refill_draft_epoch` before measurement. This is an **unselected native
draft**, not electrical, material or physical acceptance.

The run uses the unchanged constructor and exact archived board, definition,
schematics, rules and libraries. The heavy guard and pinned KiCad 10.0.6 finish
with exit 0 in 98 seconds. All 331 frozen producer files are unchanged after
execution. A separate host audit verifies 198 copied input files and all 12
native result artifacts. Exact paths and hashes are in the companion JSON.

| Check | Recorded result |
| --- | --- |
| Native rule errors / schematic parity issues | 0 / 0 |
| Complete named open edges / open nets | 1,063 / 642, unchanged |
| AGND open edges | 0 |
| Reported warnings | 507, complete records unchanged |
| Existing physical connectivity partitions | Unchanged |
| Prior AGND members connected | All 3,172 |
| New paid dogleg/via | Connected |
| Full dry section | 0.200 × 0.760 mm, no endpoint trimming |
| Preserved footprints / unretired explicit copper blocks | 1,099 / 3,714 |

The candidate SHA-256 is
`4a290a7753f99ab1e966bcc760fa58322359c8d57130c972055dc265cae47795`.
It is byte-identical to the historical JL candidate. The new execution provides
fresh source-stability and declared-scope evidence; it does not retroactively
turn the old failed execution into a pass.

The local-only criterion still fails. Filled-copper changes outside the declared
local windows are approximately 3.007404 mm² on B.Cu, 0.222180 mm² on F.Cu and
0.000000490199 mm² on In2.Cu; In1.Cu has none. The collar has 8.8809e-8 mm² of
source-polygon excess, with zero intersection of the complete dry-neck guard.
Display values are rounded; the JSON preserves the native diagnostic values.
No area or displacement tolerance is used to waive these findings. The entire
refilled conductor belongs to this candidate and must be used by any new
electrical witness.

Both historical native receipts remain byte-for-byte unchanged. K was not
rerun and retains its original global proposal hash. The current JL/K proposal
does not rebind K or any historical electrical result to a new source epoch.

## Reproduction and next electrical step

From the repository root, use a new ignored destination:

```sh
python3 -m scripts.pcbgen.reconstruct_foil_collar --prepare worktrees/38-jack-halves --cache .circuit-cache/foil-collar-jl-replay-fresh
bash "$HOME/.codex/scripts/heavy-guard.sh" -- bash scripts/kicad/run.sh python3 -m scripts.pcbgen.reconstruct_foil_collar --cache .circuit-cache/foil-collar-jl-replay-fresh --run-board JL
```

Freeze producer sources before execution and verify their hashes afterwards.
Existing destinations are refused. Preserve
`.circuit-cache/foil-collar-jl-replay-v1` and the original recovery worktree;
missing artifacts mean actual native revalidation is **NOT RUN**.

The next electrical construction must consume this complete geometry export,
use the full collar cut, and pay for the JL flare, dogleg, via, annular transfer
and In1 spreading. The corresponding K-side access costs remain separate.
Neither an old pad-source field nor a nominal neck resistance can replace those
matched current/potential witnesses. Fixture isolation, remated contact-state
coverage, finite material/process classes and joined current allocation remain
open. The 0.5 mΩ common-ground, 0.5 A/contact, 1 mΩ rail, 20 mV distribution and
0.20 V full-path limits are unchanged. Issue #38 remains open.
