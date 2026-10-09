# Read-only R7609 placement comparison

R7609 is source-marked movable and not a bypass cluster. This bounded screen tests288translations in0.1mm increments within±0.8mm, preserving side/orientation and every existing copper object. It uses0.35mm courtyard separation,0.25mm foreign-copper clearance and an additive0.2mm signal landing bridge. Three shifts pass the exact source-outline inset and conservative courtyard check; all three conflict with retained signal segment638c8d71-8db4-5871-a197-ea0ffd3d7075. No static candidate survives. No placement, board or source floorplan was changed; no native check is claimed. This rules out only this particular no-cut local translation scope, not all possible placement solutions. The original copper and physical constraints remain authoritative.

Reproduce from the hash-verified JR37953998528 artifact using `bash "$HOME/.codex/scripts/heavy-guard.sh" -- .circuit-cache/route-venv/bin/python circuit/routing/issue189/jr-r7609-placement-screen/screen.py`. The saved result pins the board, dump and source floorplan hashes. The guarded run passed in1s.

The initial screen used the broader panel envelope. Its preliminary output is retained as pre-outline-result.json and is superseded by result.json, which pins the exact source JR outline and0.30mm inset. No preliminary candidate was applied or submitted.
