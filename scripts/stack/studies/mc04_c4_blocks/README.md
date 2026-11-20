# Task C step 4: on room, all 26 unplaced ICs pack onto K as functional blocks; JR and JL moves add 24 cable signals

```sh
python3 -B blocks.py --output new-result.json   # about 2 minutes
```

**Blocks.** A block is an unplaced IC, its declared decouplers and its one-hop passive and diode
signal neighbours on the same board, as in the MC02 analog remedy brief. Panel hardware and other
ICs stay where they are.

**Packing.** Greedy raster packing at 0.25 mm in the cumulative MC04-R1 scene:
- each IC goes on the target face where it lands nearest its original x/y (all boards share the
  stack x/y frame);
- each member then goes nearest the IC on the same face;
- every placed part blocks later ones with 0.35 mm.

**Signals.** A non-power net crosses between the source board and K when it has members on both.
The baselines are 106 nets for JR and 100 for JL; each matches the signal count on that board's links.

Result (`result.json`, SHA-256 `05f5029be574428a9821936b9a1d98686eb32d50a60dbb3b8aed4f1e7cebd82e`):

| Case | All blocks pack | IC shift mm | Extra cable nets | Spare link positions |
| --- | --- | --- | --- | --- |
| JR → K (6 blocks) | yes | 4.5–30.5 | +16 | 75 on JR links |
| JL → K (6 blocks) | yes | 0–27.2 | +8 (all from U2119) | 153 on JL links |
| JL → JL (6 blocks) | yes, but only 26–102 mm away | 26–102 | 0 | — |
| K → K (14 blocks, vacated) | yes | 5.3–49.4 | 0 | — |
| **All 26 onto K together** (K, then JR, then JL) | **yes** | 4.5–49.4 | +24 | — |

On JR the six blocks sit closer together on K than on JR. On JR, members are up to 26–66 mm from
their IC; on K, at most 31.6 mm.

How this reads:

- **JR.** JR cannot hold its six ICs, so moving their blocks to K is the first remedy that resolves it.
- **JL.** JL → K is cheap in signals: five of the six blocks add no cable net. JL → JL needs moves of
  26–102 mm, beyond the retained 25 mm step limit.
- **K.** Seven of K's own blocks move more than the retained 25 mm (U1415, U4324, U4417, U4524,
  U4526, U4623, U4635 and U8409, 28–49 mm). DS-88 does not expand search radii, so using them is a
  rule change for the design authority.

These are all partition or rule changes. None of them can be adopted without the design authority
and the following:

- **Sensitive signals over the cable.** Input buffers moved to K (for example U4346 and U8314)
  carry unbuffered jack signals over the cable. The brief's isolation and protected-input tests, and
  the coupling class of each new crossing net, must be reviewed.
- **Allocation not run.** Class and ground rules are not applied to the 24 extra nets. Per-link
  capacity decides the actual link use; JR-L06 has 1 spare position.
- **Placement not confirmed.** Positions are raster-only, not exact-predicate confirmed. Rotation is
  not tried, and nothing is routed.
- **No electrical review and no canonical change.**
