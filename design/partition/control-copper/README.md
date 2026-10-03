# Control-board copper after debounce placement correction

This is a **routed, unvalidated draft**. The source has 4140 track
segments, 527 through vias and 0 complete native open edges. Accepted
routing batches retain all 344 ground contacts, all 81 source AGND copper
objects and sixteen local IC/bypass rail pairs after independent refill. The four-layer, 2 oz, 1.6 mm stack remains a proposal.

The source moves ninety envelope debounce passives into thirty complete
triplets beside their existing Texas Instruments SN74HC14DR input pins.
Capacitor-to-input pad distances now have a 7.665 mm maximum, down from
144.626 mm. These are placement distances, not routed lengths. All ICs,
bypass capacitors, headers and fixed panel hardware remain in place; all
pin/net assignments and component identities remain unchanged. The earlier
123-pair K/P header assignment is retained.

The 72-edge checkpoint remains in git history. Moving passive terminals
invalidated affected signal routes; retaining only compatible copper and
removing routes that collided with the new placement produced a checked
199-edge seed. Native-checked back/front signal links and rail links reduce
that seed to 0 edges. Candidate links that break ground connectivity
are rejected individually. The later inner-layer search also considers distant rail islands.
Search distances and connected copper do not establish a resistance bound.
The six main-terminal arrays and local C222 ground stitch remain. Their
current and resistance capability is not qualified.

After the merged 43-edge checkpoint, a protected-copper autorouter run timed
out. Its 30-edge raw import disconnected two grounds and was rejected. Keeping
only seven improved signal nets restored every ground and yielded 36 edges.
Checked inner-layer rail and signal links then reached 23.

From the 23-edge checkpoint, checked multilayer links reached 15 and then 12.
A grid A* router over all four copper layers closed the rest: the +12 V and
-12 V terminal feeds to the op-amp cluster, the remaining +5 V pins, four long
panel-signal links and three boxed IC/resistor pins. The boxed pins needed
rip-up and reroute of four nearby signal nets (X69343E2C6D875EFAA724,
XE3CCFA14F6E3DCF3F5F1, X664ED05EACC39FA0A717 and X69F956D2CD0D8F7D7812);
every other earlier copper object is unchanged. Four added AGND stitching vias
rejoin B.Cu ground-pour islands that new links cut. Each batch passed native
DRC, parity, refill and ground/bypass checks before adoption. Current and
resistance acceptance remain open.

`copper.json` owns explicit integer-nanometre copper geometry. Construction
replays it on the current labelled base without moving other source geometry.
The native gate checks exact source replay, all pads and drills, complete
rules and schematic parity, all main-array members, every ground contact
and source AGND object, sixteen bypass pairs, complete per-net connectivity
before/after refill, and source immutability. The full ratsnest and native
front/back preview hashes are retained alongside it.

Run through the shared heavy guard:

```sh
bash scripts/kicad/run.sh python3 scripts/pcbgen/check_control_copper.py
```

Current-source conductor resistance/current, complete rail distribution,
protection, manufacturing and physical fit remain open. Old electrical
receipts are not rebound. No fabrication or order files are generated.
