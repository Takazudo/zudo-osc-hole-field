# Stage55 verification record

Start head `e1969027e63dfc22da1dbca07bf64e8778b122dd`. Oracle: KiCad 10.0.6, image
`kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`
through `scripts/kicad/run.sh` (same digest, pulled through the `mirror.gcr.io`
Docker Hub mirror after a Docker Hub 429). Linux cloud container; no Mac or hardware.

## Commands, in order

```sh
pnpm circuit:check                                   # PASS before edits (68 lines)
bash scripts/checks/regen-all.sh                     # exit 0, no tracked change
python3 design/architecture-278/implementation/stage55/idle-quad-cleanup/candidate.py
bash scripts/kicad/run.sh python3 design/.../pcb_cleanup.py \
  .circuit-cache/stage55/baseline/osc-core/osc-core.kicad_pcb \
  .circuit-cache/stage55/candidate/osc-core/osc-core.kicad_pcb \
  .circuit-cache/stage55/pcb-receipt.json .circuit-cache/stage55/schematic-receipt.json
python3 design/.../native.py run                     # ERC+DRC both sides, ~30 min
bash scripts/kicad/run.sh python3 design/.../ratsnest_refilled.py <side PCB> <refilled> <json>  # both sides
bash scripts/kicad/run.sh python3 design/.../rail_clusters.py <side refilled PCB> <json>        # both sides
python3 design/.../native.py check                   # PASS, all 12 gates
python3 design/.../decoupling.py --check             # PASS
python3 -m unittest design/.../test_stage55.py       # 11 tests OK; also with -O
pnpm circuit:check                                   # PASS after edits
```

The baseline PCB copy is the canonical `boards/osc-core/osc-core.kicad_pcb`.
`native.py run` was first executed with an evaluation that compared the truncated
CLI unconnected list and required parity [0, 0]; it printed FAIL. Inspection showed
both CLI lists stop at 499 items (rail opens fell 12 while truncation exposed 12
other items on OSC_REF5/OSC_REFN5, whose copper and pads are identical on both
sides) and the single parity item described in README. First-run gates: parity
[0, 0] false; oracle, ERC, DRC errors, uncapped signatures, truncated rail-unconnected
and removed-item gates true. The evaluation was then changed to the complete native
ratsnest, rail cluster membership and an explicit single-item parity classifier
(tightened after independent review); the raw reports are unchanged and retained.

## Evidence SHA256

| Item | SHA256 |
| --- | --- |
| Baseline PCB (canonical) | `fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10` |
| Candidate PCB (two runs identical) | `ccb68cbb8d07c46ee008812d9e56db32227bca3cc9af24a210625603e5e7baa3` |
| baseline-erc.json | `d2373b25a5463fc73bf05670ade28c26279e22d414968cc9ffff585331659216` |
| candidate-erc.json | `d219f93111474f86ee0a699ac65e24b187f193eda722f7e4d240b6683099fc15` |
| baseline-drc.json | `58627c0185eff4c95b08b560cc6684a7399e905c271508d03ea0349b4d5a982e` |
| candidate-drc.json | `c0903bd2b5ba4d91135b1b7be056e4697aaf21af91abf4b724c1517355d3bf18` |
| Baseline refilled PCB (ratsnest input) | `b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66` |
| Candidate refilled PCB (ratsnest input) | `2667ee52eaff2ab0a7692cbf02107f3f7406d7b697627657b1b163d0fb77ccef` |

Rail cluster files are bound to the refilled boards by `board_sha256`.

Disposable PCBs stay in `.circuit-cache/stage55/` (git-ignored, about 70–100 MB each)
and are reproducible from the canonical board and `pcb_cleanup.py`.

## Status by check

| Check | Status |
| --- | --- |
| ERC, DRC, parity, complete ratsnest, rail clusters, decoupling replay, unit tests | PASS (disposable candidate) |
| Bypass proximity for U101, U107, U207 | OPEN, needs PDN/layout review |
| Capped warning types (hole_to_hole, silk_over_copper, silk_overlap) | NOT ESTABLISHED, KiCad 199 cap |
| PDN impedance, analog behavior, thermal, assembly | NOT RUN |
| Canonical adoption, BOM/worksheet update | NOT RUN, needs owner approval |
| Mac local run, hardware measurement | NOT RUN |
