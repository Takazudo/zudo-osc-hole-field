# One source-only F3 integrator-cluster pose

Parent authorized one bounded candidate placement pilot on 2026-10-11, following
the retired weight-2 routing attempt. Its rejected via pair is a path-dependent
conflict, not proof that placement must change. The 10 mm proximity target is
an engineering objective, not an owner constraint.

Input integration checkpoint: `8b82fabd546cae859deade6c05ae110c4d0090b2`.
`pose-epoch.json` is immutable and is checked against its hard-coded SHA256.
It contains all 24 sensitive/bypass references with explicit old/new physical
poses. Seven move: U2312/U2313, their four bypass capacitors, and C2312. U2306
and all other references remain fixed. The two ICs reuse the existing SOIC14
body sites. U2312's bypasses retain their relative placement; U2313's bypasses
reuse the vacated U2312 sites with positive/negative supply identities retained.
The C2312 vertical pose targets the channel beside U2306. This is one authored
candidate, with no pose sweep, optimizer, route search or partial path output.

Original BP_INT terminals remain C2312.1 → U2306.5; original AGND terminals
remain C2338.2 → U2312.5. C2312.1 ↔ U2312.12 is an already-connected original
group whose copper requires explicit accounting after either endpoint moves.
The source checker authenticates every accepted copper-index object against
the actual accepted PCB source, including all 133,551 segments/vias, and records
exact old pad contacts, new foreign-copper conflicts and complete net recheck
selectors. Those selectors never authorize deletion. All accepted bytes stay
unchanged. Zone refill and native connected groups remain later obligations.

Before edits, `pnpm circuit:check` passed (manual68lines/zero declared placements;
no schematic/placement binding). `regen-all.sh` is NOT RUN: its schematic exports,
native monitor checks and KiCad invocation conflict with this explicit source-only
scope. No oracle substitution is used. No native slot is admitted or reserved.

The checker evaluates the sealed pose's actual transformed courtyards against
all candidate neighbors, 0.35 mm same-face separation, 0.30 mm board-edge
allocation and frozen service/support reservations. It distinguishes old same-ref
and old whole-cluster reservation occupancy from the proposed occupancy. Exact
analytic circle distance is separately used for service holes. Retained source
geometry screens are not native DRC or installed fit.

On a fit failure, retain its dimensions/owners and report the smallest justified
next scope. Do not automatically move a neighboring group, evaluate another pose,
or claim that one failure proves the complete 24-ref scope impossible. U2309's
own-pad positive/negative rail blockers remain unchanged. Complete combined
signal/return geometry, whole-chain/cross-path checks, fill and all native gates
are NOT RUN unless their prerequisites actually pass.
