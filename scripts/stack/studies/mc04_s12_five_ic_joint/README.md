# MC04-S12: one joint link search for U1415, U5110, U8409, U5209 and U5210 (DS-151)

Study only, one run. It produces candidate scenes and evidence and adopts nothing. Every board and schematic stays an
unvalidated draft. Brief: `circuit/orchestration/campaigns/osc-stack-20261114/mc04-s12-five-ic-joint-search-brief-20261127.md`
(Revision 2). Report: `mc04-s12-report-20261127.md` in the same folder.

```sh
PY=/home/user/venv312/bin/python
timeout 6h $PY guard.py <summary.json> -- $PY joint_search.py --run   # the driver (stages as sequential children)
$PY joint_search.py --check            # verification, no search re-run
$PY joint_search.py --verify-scene N   # rows-only replay, A1 to A12 and the digest of candidates/scene-N.json
$PY -m unittest test_s12               # pinned outcomes and mutations M1 to M12
```

## Files

| File | Content |
| --- | --- |
| `s12.py` | library: snapshot context, rules 1 to 6, the scene checker (A1 to A11), locality (Ruling 1), full replay |
| `joint_search.py` | driver: arm 0, pilot, stages 1 to 4, outputs, `--check`, `--verify-scene` |
| `guard.py` | memory and time guard: tree RSS every 5 s (budget 8 GiB) and a `MemAvailable` floor of 7 GiB |
| `census.json` | stage 1: per link and grid, the counts after each rule, rejection tallies, T1 tallies, accepted candidates |
| `checkpoints/` | one JSON per finished stage, the run log with the fingerprint, and the hold files of the full replays |
| `result.json` | the run: fingerprint, arm 0, census summary, stage logs, verdicts per IC, candidate digests |
| `candidates/scene-N.json` | written candidate scenes (none when no scene passes A1 to A12) |

## Method in one paragraph

Inputs are read from `6e5716e7` through a git archive of the snapshot paths (`replacement.SNAPSHOT_PATHS`) in a
temporary directory; the model is the S9 class (`slot_moves.S9`) at that snapshot. Stage 1 enumerates every slot of the
eight links (and L07 as a 26-way) on the 2.0, 0.5 and 0.25 mm grids within 35 mm with `links_gate.candidate`, every
other searched link left out of `placed`, and applies rules 2 to 6 in order (class distances, riders, cable and
compliance from `slot_moves.Arm1.accept_for`; radius; the five-IC courtyards from `slot_moves_a2.Arm1A2.accept_for`;
the protected preflights T1 and T2). Stage 2 keeps the cheapest candidate per direction and 2.0 mm cell (at most 60) plus
the recorded slot, and screens each by one rows-only replay (`links_gate_part2.replace_all`). Stage 3 searches the
West, South and East clusters best-first; stage 4 joins the clean cluster scenes, applies the overlay rules (A7 to
A11, ported from `overlay.py`) and one full gate replay per scene with slot holds in a scratch root (A12).

Every result is courtyard level on unvalidated drafts. c6, checks 2 to 4, threading, routing, DRC, coupling under
tails and every electrical acceptance are NOT RUN here.
