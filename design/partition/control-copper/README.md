# Control-board copper after paired-header reassignment

This is a **partially routed, unvalidated draft**. The current source has 191
track segments, 188 through vias and 453 complete native open edges. It keeps
all 344 ground contacts and sixteen local IC/bypass rail pairs connected after
independent refill. The current four-layer, 2 oz, 1.6 mm stack is a proposal.

The connector-locality source permutes 123 complete K/P pairs among existing
identical sites. Every panel control, non-header component, connector reference
and pin map remains unchanged. All modeled cable spans and service-hole
locations are preserved as sets. The 123 header labels follow their new sites.

The earlier 278-edge routing checkpoint remains in git history. Its header
routes are not valid at the new terminal positions. This source retains only
compatible local links and six main-terminal arrays. Seventy-two short
In1.Cu segments connect the three rail via arrays on a second layer. The
453-edge result is a rerouting seed, not improved routing completion.

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

Source regeneration and 29 connector/partition tests passed. The new labelled
base passed native replay with zero rule/parity findings and all 418 labels.
The seed has zero native DRC/parity findings; independent refill retains its
453 edges, 344 grounds and sixteen bypass pairs. Combined native replay,
41 targeted tests, documentation build and publication checks passed in
107 seconds, retaining the existing single workbench-link exception. The full
PCB suite passes 484 tests. The source/check suite passed 285 tests, with the
additional connector-transition negative test also passing. Integrated CI
for this source revision is pending.

Actual conductor resistance/current, complete rail distribution, protection,
manufacturing and physical fit remain open. No previous electrical receipt is
rebound. No fabrication or order files are generated.
