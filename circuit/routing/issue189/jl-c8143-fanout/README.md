# C8143 ground fanout

Pinned additive proposal on accepted JL125: one0.3mm AGND segment and one0.6mm via into In1.Cu, no removals. prepare.py checks exact source/proposal hashes and emits a disposable native delta. Dispatch routing-benchmark.yml with board=osc-jack-left,replay_jl=true,jl_replay=c8143-fanout on a dedicated worker branch. Full settled native connectivity, original pad groups, warnings, DRC/parity, independent fresh copy and retained-copper gates remain mandatory. No other JL writer is active.
