# JL125 via-free search

On immutable accepted JL125, select the first24 nearest native signal-component pairs. Search each using only F.Cu or only B.Cu,0.025mm lattice, weight1 and300000 expansions per bounded attempt, unchanged electrical constraints. All48 cases found no path. Guarded run completed with PASS in142s; that means the diagnostic executed successfully, not that connectivity improved. No copper proposal or native adoption resulted. Input/router hashes, frames and per-case diagnostics are preserved in result.json.

Reproduce from repository root with `bash "$HOME/.codex/scripts/heavy-guard.sh" -- .circuit-cache/route-venv/bin/python circuit/routing/issue189/jl125-no-via/screen.py` after restoring the pinned artifact dump referenced by the script. Full native memberships are retained throughout the search.
