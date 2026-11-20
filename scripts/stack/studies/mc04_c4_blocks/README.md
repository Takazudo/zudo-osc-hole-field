# Task C step 4: on room, all 26 unplaced ICs pack onto K as functional blocks; JR and JL moves add 24 cable nets

```sh
python3 -B blocks.py --output new-result.json   # about 9 minutes
```

**Blocks.** A block is an unplaced IC, its declared decouplers and its one-hop passive and diode
signal neighbours on the same board, as in the MC02 analog remedy brief. These parts are left out:
- panel hardware and other ICs;
- service trimmers (RV…), which follow `design/stack/trimmers/relocation-plan.json`;
- the off-board `stage_optical` resistors RB4316 and RB4322.

A part shared by two blocks (R5252, R5253) is placed once.

**Packing.** Greedy raster packing at 0.25 mm in the cumulative MC04-R1 scene, with no rotation:
- each IC goes on the target face where it lands nearest its original x/y (all boards share the
  stack x/y frame);
- each member then goes nearest the IC on the same face;
- each placed part blocks later ones with 0.35 mm.

Every recorded position is then re-checked with the scene's exact predicate, setting aside only the
displacement cap, and all pass. Positions are stored in `result.json`.

**Signals.** A non-power net crosses between the source board and K when it has members on both.
The baselines (JR 106, JL 100) equal the link-gate signal net sets of the JR-K and JL-K joints.

Result (`result.json`, SHA-256 `be96eff6fb4a5fc4e047b2c4d109fa8dd87b0bf7a4b3927fc3069233cb8fcab3`):

| Case | All blocks pack | IC shift mm (over 25 mm) | Cable nets newly crossing / no longer crossing / net | Spare positions (joint) |
| --- | --- | --- | --- | --- |
| JR → K (6 blocks) | yes | 4.5–30.5 (U8314) | 31 / 15 / +16 | 75 (JR-K) |
| JL → K (6 blocks) | yes | 0–27.2 (U1518) | 24 / 16 / +8 | 128 (JL-K) |
| JL → JL (6 blocks) | yes | 26–102 (all six) | 0 | — |
| K → K (14 blocks, vacated) | yes | 5.3–49.4 (ten: U1415, U4324, U4417, U4433, U4524, U4526, U4527, U4623, U4635, U8409) | 0 | — |
| **All 26 onto K together** (K, then JR, then JL) | **yes** | 4.5–49.4 (thirteen, including U4346 at 26.7) | +24 | — |

How to read the cable-net figures:

- **Totals are net changes, not unchanged cables.** A block with a net change of 0 moves as many
  nets onto the cable as it takes off.
- **What newly crosses from JR:** 8 `*_PROTECTED` input nets, 5 `*ISO_MID` nets and 18 LED nets.
- **What newly crosses from JL:** 7 `*_PROTECTED` input nets, 9 `*ISO_MID` nets and 8 LED nets.
- **Why `ISO_MID` appears.** An `ISO_MID` net arises when a series isolation pair is split, for
  example RB4307 moved and RB4308 left behind, so the cable lands on the isolation midpoint.

**JR, JL and K.** Step 1's joint first-fit placed only 3 of JR's 6 ICs on JR. That is a lower
bound, not proof that JR cannot hold all six. On room, moving the blocks to K is the first option
found that places all of them. Thirteen ICs in the combined run move more than the retained 25 mm
step limit, from all three boards. DS-88 does not expand search radii, so every such move is a rule
change.

These are all partition or rule changes for the design authority, and none of them can be adopted
without the following:

- **Sensitive nets.** Each new `*_PROTECTED` input net puts an input-protection node on the cable,
  from JR (U4346, U8314) and JL (U1216, U1416, U1518). The `ISO_MID` splits defeat the purpose of
  the series isolation pairs. The brief's isolation and protected-input tests, and the coupling
  class of every new crossing net, must be reviewed.
- **Allocation not run.** Class and ground rules are not applied. Per-link capacity decides actual
  use; JR-L06 has 1 spare position.
- **Not screened.** Rotation, routing, stack-facing heights between K.F and the JR/JL back faces,
  and mirroring of flipped footprints.
- **No electrical review and no canonical change.**
