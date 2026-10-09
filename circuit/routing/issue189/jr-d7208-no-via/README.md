# D7208 without vias

Prepared from the accepted JR141 native dump after terminal rejection of the D7504 worker.26 F.Cu segments and zero vias/cuts. The earlier D7208 signal proposal split the -12V C7221.1 island; this different single-layer path must pass unchanged full native connectivity/DRC/parity/warning gates. No native run yet.

Reproduce screen: `bash "$HOME/.codex/scripts/heavy-guard.sh" -- .circuit-cache/route-venv/bin/python circuit/routing/issue189/jr141-no-via-alternatives/screen.py`.

`prepare.py` validates exact accepted board/proposal hashes and refuses removals. Dispatch the routing-benchmark workflow with `board=osc-jack-right replay_jr=true jr_replay=d7208-no-via` on an isolated retained worker branch containing this change. Do not dispatch another JR writer concurrently. Review actual artifact, groups, fresh count, warnings, parity and retained serialized copper before adopting.
