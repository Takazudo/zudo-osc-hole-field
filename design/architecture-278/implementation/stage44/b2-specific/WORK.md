# Stage44 working scope

Start head:8b95063895a8f728c6ceb69afe8499e9a00c9496. Owner explicitly authorized
B2-specific disposable placement/routing after Stage43 rejection. Preserve B1,
fixed front hardware, physical contact IDs/nets, canonical outputs and history.
Bootstrap was already consumed in this chat; same environment, no reload.
Repository instructions and current PR/issue activity were reread. No competing
push/comment found. Pre-edit circuit check passes (manual68lines/0placements,
no schematic/placement binding; pin-asset check performed). Canonical regeneration
is not run locally under the explicit preservation instruction; exact Stage43
CI39210793513 passed aggregate regeneration and2869 tests.

Smallest repair plan: independently establish removable B2-only supply branches;
retain boundary anchors and foreign copper. Start with common package groupings,
but preserve/revise B2 poses where actual geometry requires it, especially R3209.
Screen placement before new B2 routing. Replace private routes with new paths
against actual obstacles; never reuse the failed translated routes as a solution.
No substitution or broader architecture change is permitted silently. Every
native load/save is checked for net reassignment; first failures stay retained.
Final acceptance requires complete identity/partition, power/return, DRC/refill
and repeated fresh-load checks;117 baseline opens and cappedsilk remain explicit.
