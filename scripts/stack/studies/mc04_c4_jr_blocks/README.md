# Task C step 4: all six JR ICs fit on K with their small parts, for +16 JR–K signals against 75 unused positions

```sh
python3 -B blocks.py --output new-result.json   # about 1 minute
```

JR cannot hold its six unplaced OPA4196 packages. Step 1's joint first-fit placed only 3 of 6, and
no link move frees room there (step 2b). This study asks whether each IC can go to K, the board
with the most free area, together with its functional block. A block is the IC, its declared
decouplers and its one-hop passive and diode signal neighbours that sit on JR, as in the MC02
analog remedy brief. Panel hardware and other ICs stay where they are.

**Packing on K.** Greedy raster packing at 0.25 mm in the cumulative MC04-R1 scene. Each IC goes on
the K face where it lands nearest its original x/y (JR and K share the stack x/y frame). Each member
then goes nearest the IC on the same face, and every placed part blocks later ones with 0.35 mm.

**Signals.** A non-power net crosses JR–K when it has members on both boards. The baseline count is
106, which matches the 106 signals on the seven JR links.

Result (`result.json`, SHA-256 `f53a37a8b2b3de0c1f50ee3c1c5329a29df7084c6db1844a0491d554c17de7c5`):

| IC (function) | Parts | K face | IC shift mm | Max member distance on K / on JR mm | Extra JR–K nets alone |
| --- | --- | --- | --- | --- | --- |
| U4346 (E3 inputs) | 10 | F | 24.9 | 9.6 / 51.9 | +3 |
| U4347 (E3 outputs) | 11 | F | 21.5 | 12.1 / 30.1 | +2 |
| U4348 (E3 indicators) | 13 | F | 4.5 | 14.7 / 26.1 | +4 |
| U8314 (M4A inputs) | 11 | F | 30.5 | 10.6 / 66.3 | 0 |
| U8318 (M4A indicators) | 23 | F | 12.6 | 31.6 / 37.6 | +6 |
| U8417 (M4B mixed) | 16 | B | 16.0 | 12.4 / 33.1 | +4 |

All six blocks pack without a missing part. Moving all of them adds 16 crossing nets, against
75 unused positions on the seven JR links.

On room, this is the first remedy that resolves JR. It is a partition change, so it must go through
the design authority:

- **Sensitive signals over the cable.** U4346 and U8314 are high-impedance input buffers. Moving them
  means unbuffered jack signals travel over the cable to K. The brief's isolation tests
  (ENV_STORAGE, the mix4 protected input set and OTA_CURRENT) and the coupling class of each new
  crossing net must be reviewed.
- **Allocation not run.** The class and ground rules are not applied to the 16 extra nets. Per-link
  capacity (JR-L06 has 1 spare position, JR-L02, L04 and L07 have 17 each) decides which links take them.
- **Placement not confirmed.** Positions are raster-only, not exact-predicate confirmed. Rotation is
  not tried, and nothing is routed.
- **No canonical change** was made.
