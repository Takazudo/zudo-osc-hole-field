# D7208 without vias

Prepared from the accepted JR141 native dump after terminal rejection of the D7504 worker.26 F.Cu segments and zero vias/cuts. The earlier D7208 signal proposal split the -12V C7221.1 island; this different single-layer path must pass unchanged full native connectivity/DRC/parity/warning gates. No native run yet.

Reproduce screen: `bash "$HOME/.codex/scripts/heavy-guard.sh" -- .circuit-cache/route-venv/bin/python circuit/routing/issue189/jr141-no-via-alternatives/screen.py`.

`prepare.py` validates exact accepted board/proposal hashes and refuses removals. Dispatch the routing-benchmark workflow with `board=osc-jack-right replay_jr=true jr_replay=d7208-no-via` on an isolated retained worker branch containing this change. Do not dispatch another JR writer concurrently. Review actual artifact, groups, fresh count, warnings, parity and retained serialized copper before adopting.

## Native accepted result

Run37929676316 adopted JR141→140 with26 F.Cu segments, no vias/cuts. All50,964 prior objects are identical; after count50,990. Native DRC/parity0/0,520 unchanged warnings, no new warning identities or split pad groups, independent fresh-copy agreement. Artifact11616270361 verified against SHA256b014f263a0a8bda0034beaf0831cf0c15eb31af7930da561af44d2a43742b9bd. Published/native-filled board SHA256c2e6f8896869213293239912fefa64915da41fcdfa2094f082d017a88803a087. Replay SHA256d2c5927d764863fb73210a8b77bbe2633a88db078db63f04753f594eeedc4626. Worker publication21965d2f848dda38c12895e7cc3f5bb16e1474ba integrated by reviewed cherry-pick; no older board snapshot copied.
