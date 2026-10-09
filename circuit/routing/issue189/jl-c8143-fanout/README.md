# C8143 ground fanout

Pinned additive proposal on accepted JL125: one0.3mm AGND segment and one0.6mm via into In1.Cu, no removals. prepare.py checks exact source/proposal hashes and emits a disposable native delta. Dispatch routing-benchmark.yml with board=osc-jack-left,replay_jl=true,jl_replay=c8143-fanout on a dedicated worker branch. Full settled native connectivity, original pad groups, warnings, DRC/parity, independent fresh copy and retained-copper gates remain mandatory. No other JL writer is active.

## Accepted native result

Run37932246042 accepted125→124,0DRC/parity,477 unchanged warnings,no split groups/new warning identities,fresh agreement. Artifact11616679678 SHA2568480291e21fc7f591be077f700c53fc15e8e8adc1fd8c0761560fe5e320761f6 verified. All33,220 old objects identical,two added; pad/net,outline,keepout/layer records unchanged. Published/native-filled SHA256f5661fda3b568c82a7a2bef5cd7ef319d5996598995295b05664944f5493cd56. Replayf21597cf0028de8690a81b5c6bfbd14d94e2dd50e0906f5a24550d0b66c644d3. Worker60dac38b271c311e8c152995da470565ceb627ca integrated as2f983dc.
