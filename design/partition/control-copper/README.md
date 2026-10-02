# Control-board copper after debounce placement correction

This is a **partially routed, unvalidated draft**. The source has 2889
track segments, 431 through vias and 43 complete native open edges.
Accepted routing batches retain all 344 ground contacts, all 77 source AGND
copper objects and sixteen local IC/bypass rail pairs after independent
refill. The four-layer, 2 oz, 1.6 mm stack remains a proposal.

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
that seed to 43 edges. Candidate links that break ground connectivity
are rejected individually. Rail-link searches consider pad pairs at most
25 mm apart; this is not a maximum routed length or a resistance bound.
The six main-terminal arrays and local C222 ground stitch remain. Their
current and resistance capability is not qualified.

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
