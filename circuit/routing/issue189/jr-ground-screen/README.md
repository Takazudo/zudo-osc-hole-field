# Surface-ground screening reassessment

The optional F.Cu AGND guard rejects the known nine-object D7504 proposal as fill_guard_disconnection, then finds no alternate route. This is a local saved-input result, not native adoption.

A five-case check of exact saved proposals against F.Cu/B.Cu/In1.Cu AGND partitions shows why blanket enforcement is not enabled: both known rejected cases are flagged, but each of three native-accepted controls is also flagged on at least one surface layer. Existing cross-layer ground connections are not represented by independent per-layer partitions. This approximate screen is therefore not a valid replacement for whole-board native connectivity. Existing native acceptance remains unchanged.

crosscheck.json records per-case immutable input hashes, bounds and outcomes. The guarded check passed in31s. Reproduce with `bash "$HOME/.codex/scripts/heavy-guard.sh" -- .circuit-cache/route-venv/bin/python circuit/routing/issue189/jr-ground-screen/crosscheck.py` after restoring referenced artifacts.
