# Ground repairs on the rejected D7504 candidate

Native run37927714132 joined D7504 but split R7505.2 and R7530.2 AGND. This screen uses that immutable rejected native142 dump, not an accepted board. It tries bounded12mm additive plane fanouts and direct links for each isolated pad at0.025mm and0.0125mm, unchanged0.3mm ground width/0.6mm via/0.25mm clearance. All eight cases found zero routes; guarded run passed in25s. No repair proposal, native retry or adoption resulted. The original accepted141 native memberships would remain the acceptance baseline for any eventual combined replay.

Run `bash "$HOME/.codex/scripts/heavy-guard.sh" -- .circuit-cache/route-venv/bin/python circuit/routing/issue189/jr-d7504-ground-repair/screen.py` from repository root after extracting artifact11614927392 into the path in the script.
