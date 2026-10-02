# Control-board copper after paired-header reassignment

This is a **partially routed, unvalidated draft**. The current source has 3016
track segments, 565 through vias and 72 complete native open edges. It keeps
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
native checks. A subsequent continuation protected every one of those 2,140
existing copper objects and reached 114 edges after removing ground-sensitive
additions. Front-layer grid paths reduced this to 102 and 96; three accepted
back-layer paths reduced it to 93. Every candidate underwent native DRC,
complete connectivity, ground and bypass checks before adoption. Two further front-layer detours reached 91 edges. A back-layer
link with a local C222 ground stitch reached 90; another protected-copper
continuation reached 72 after restoring a ground-sensitive route. All previous
copper remains exact. Every source AGND segment and via must connect to main
ground both before and after independent refill. The stitch uses the declared
0.3 mm local ground escape and 0.7/0.3 mm via dimensions; electrical current
and resistance capability remain unqualified.

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

The preceding 189-edge checkpoint passed source regeneration, native replay,
42 targeted tests, documentation and publication checks, and integrated CI.
The 93-edge continuation passed full native replay, 42 targeted tests,
documentation build and publication checks in 93 seconds. Both native views
were visually inspected; all 2,140 prior copper objects are unchanged and no
net has regressed. That 93-edge revision passed integrated CI and is merged. The final 72-edge
combined native replay, 43 targeted tests, documentation build and publication
checks passed in 211 seconds. Both layer views were visually inspected; the
existing single workbench-link exception remains explicit. Its integrated CI
is pending. The current remaining connections are retained in the complete native ratsnest.
All prior source copper is retained exactly. K's native comparison preserves
all 13,406 pad identities and pin/net assignments, all non-header component
pads and occupied ground geometry. K still has 9,650 open edges and reported
annotation warnings; its routing and annotation remain incomplete.

Actual conductor resistance/current, complete rail distribution, protection,
manufacturing and physical fit remain open. No previous electrical receipt is
rebound. No fabrication or order files are generated.
