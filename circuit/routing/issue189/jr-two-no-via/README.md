# Two via-free JR140 proposals

U5213.3:45 B.Cu segments; R8487.1:27 B.Cu segments. Both proposals were screened independently against immutable accepted nativeJR140; their copper stays23.519825200030525mm apart. Zero vias/removals. select_proposal.py deterministically selects only returned paths without vias and verifies the exact canonical input hash. prepare.py checks board/proposal hashes and serializes a disposable native delta. Whole-board native DRC/parity, settled/fresh membership, warning and retained-copper gates remain required.

No competing JR writer is active: the preceding run37929676316 is accepted and reconciled. Dispatch workflow routing-benchmark.yml with board=osc-jack-right,replay_jr=true,jr_replay=two-no-via on a dedicated retained worker branch. Do not human-push to that worker while it runs.
