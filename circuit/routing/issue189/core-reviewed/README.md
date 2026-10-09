# Core return-preserving recovery pilot

This is a source proposal, not adopted copper. It starts from canonical core
SHA256 `34955f1f1ca3a31d897e54d890f4d2eac1877aacc828961624226366bf3e5382`.
The rejected native run37836277044 reached1391, but split four prior AGND pad
groups and introduced hole-to-hole and dangling-via warning identities. Its
zero errors/parity and independent agreement do not override those failures.

The verified artifact is 11587449567, ZIP SHA256
`1a7493549b401e36fd4d53113a1a8294111708653f253a67260f7844201e2ac0`.
Its before/fresh native dumps identify the detached pads in `fragment-screen.json`.
For each detached fragment, the screen measures distance to newly added signal
copper on the pad's surface layer (through vias apply on every layer). The nearest
net is a bounded rollback hypothesis, not proven causal attribution. Ten new net
transactions are omitted in full, restoring their original canonical copper;
all other recovered source rows, including nine accepted-in-candidate AGND stitch
links, remain byte-identical. The dangling-via net is among the omitted ten.

The new hole warning involved two unchanged vias in an eight-via overlapping
signal cluster at206.3,273.475mm on net X1A3A22F4B289D6F62B00. The original report
already contained multiple hole warnings there; a newly reported pair cannot be
waived. This pilot replaces seven clustered through vias with0.2mm signal-layer
fanout segments to the retained original0.6mm/0.3mm through via. No In1/In4 signal
trace, clearance relaxation, part move, or source zone edit is introduced.
A planar polygon plus through-via graph screen kept every existing track/pad
member connected and found the added copper envelope wholly inside the old via
copper union. This approximate geometry screen is not the native acceptance gate.

`plan.json` binds every original via UUID/coordinate and the exact rejected source
replay hash. `prepare.py` regenerates `copper.json` deterministically and refuses a
changed canonical input. The resulting proposal adds1085/removes29 objects.
`geometry-screen.py` reproduces the approximate graph/envelope screen from the
artifact's `osc-core-grid-shards-start/dump.json`; its SHA256 is pinned in the plan.
Run it from the root after extracting the artifact under
`.circuit-cache/issue189-downloaded/core-repair/`. Source tests verify omission restores whole net transactions, other rows survive
unchanged, and electrical constraints/wrong input are rejected.

```sh
.circuit-cache/route-venv/bin/python circuit/routing/issue189/core-reviewed/prepare.py
gh workflow run 378789207 --ref agent-fix/189-obstacle-transactions \
  -f board=osc-core -f recover_core=true -f core_replay=reviewed
```

Only one serial native writer may run. This fixed replay does not repeat global
AGND stitching. The existing merger settles complete connectivity, checks an
independent fresh copy, requires no lost pad memberships/new warning identities,
and requires strict total improvement. Large publication is additionally gated
on native equivalence after derived fill-cache removal. Any rejection leaves
canonical copper untouched and retains exact evidence. Do not increase global
budgets or relax acceptance if this pilot fails; inspect its remaining fragments.
