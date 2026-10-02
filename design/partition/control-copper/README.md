# Control-board copper after paired-header reassignment

This is a **partially routed, unvalidated draft**. The current source has 1682
track segments, 458 through vias and 189 complete native open edges. It keeps
all 344 ground contacts and sixteen local IC/bypass rail pairs connected after
independent refill. The current four-layer, 2 oz, 1.6 mm stack is a proposal.

The connector-locality source permutes 123 complete K/P pairs among existing
identical sites. Every panel control, non-header component, connector reference
and pin map remains unchanged. All modeled cable spans and service-hole
locations are preserved as sets. The 123 header labels follow their new sites.

The earlier 257-edge routing checkpoint remains in git history. Its header
routes are not valid at the new terminal positions. This source retains only
compatible local links and six main-terminal arrays. Seventy-two short
In1.Cu segments connect the three rail via arrays on a second layer. The
453-edge seed was reduced to 270 edges by selectively adopting partial routes
from a bounded, timed-out autorouter run. Native-checked local links then
reduced it through 246, 222, 199, 194 and 190 to 189 edges. Every adopted
batch preserved all 344 ground contacts and sixteen bypass pairs. The
timeout remains a failed full-routing attempt; its partial copper has separate
native checks.

`copper.json` owns explicit integer-nanometre copper geometry. The constructor
replays it on the current labelled base without changing any other source
geometry. The native gate checks every source pad and drill, all main-array
members, all ground contacts, the sixteen bypass pairs, complete per-net
connectivity before/after refill, exact project rules and source immutability.
The full ratsnest and front/back preview hashes are retained alongside it.

Run the native gate through the shared heavy guard:

```sh
bash scripts/kicad/run.sh python3 scripts/pcbgen/check_control_copper.py
```

The paired-header seed passed source regeneration, the full 484-test PCB suite,
the 285-test source/check suite, the connector-transition negative test and CI.
Each later routing batch passed native DRC/parity and independent refill;
the final combined source replay, 42 targeted tests, documentation build and
publication checks passed in 89 seconds. The existing single workbench-link
exception remains explicit. Both native layer previews were visually inspected.
Integrated CI for the final routing revision is pending. K's native comparison preserves all 13,406
pad identities and pin/net assignments, all non-header component pads and the
occupied ground geometry. Its two bare-board drafts each have 9,650 open
edges, zero reported DRC errors or parity findings and 477 reported annotation
warnings (some categories are capped). K annotation and routing remain incomplete.

Actual conductor resistance/current, complete rail distribution, protection,
manufacturing and physical fit remain open. No previous electrical receipt is
rebound. No fabrication or order files are generated.
