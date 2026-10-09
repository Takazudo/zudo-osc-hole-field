# Bounded 2mm R7609 placement comparison

This read-only comparison tests1680translations within±2mm in0.1mm steps, preserving side/orientation and every copper object. The exact source JR outline is177.5..314mm by20..164mm; the screen applies the source floorplan0.30mm inset,0.35mm courtyard separation and0.25mm foreign-copper clearance. Only three translations pass outline/courtyard screening; all three collide with retained signal copper. No pad-clear or complete static candidate survives. No placement or board was changed and no native check is claimed.

The preliminary panel-envelope screen found six pad-clear positions at1.7..2mm eastward, all requiring a signal layer transition. Exact source-outline checking ruled those positions out before any routing or board change. Its output is retained as pre-outline-result.json; result.json is authoritative. No boundary or clearance was relaxed.

Reproduce with `bash "$HOME/.codex/scripts/heavy-guard.sh" -- .circuit-cache/route-venv/bin/python circuit/routing/issue189/jr-r7609-placement-2mm/screen.py`. The guarded corrected run passed in2s. Input board/dump/floorplan/partition hashes are recorded. This result applies only to this no-cut translation scope, not every possible local replacement.
