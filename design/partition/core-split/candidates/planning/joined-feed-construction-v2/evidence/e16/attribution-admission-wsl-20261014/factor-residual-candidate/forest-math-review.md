# Independent mathematics review: verifier-owned one-pass forest

Reviewer `/root/math_review`, separate from implementation,2026-10-15 JST.
Synthetic continuation after2dbab46b. No original input, signer, request, campaign
charge or production operation. Prior negative and intermediate evidence remains.

**PASS for the bounded one-pass forest certificate and interval wrapper.** This
review establishes the stated mathematical implementation, not production cost
eligibility, original structural applicability or physical attribution.

## Why one exhaustive row pass is sufficient

The public certify_forest(a,context,meter) accepts no prebuilt tree, arbitrary row
summary, oracle output or skip-proof flag. Its own exhaustive verifier reads every
stored row and reverse coefficient, computes each exact symmetric-part entry,
and subtracts every absolute off-diagonal from the actual diagonal. Positive,
negative and cancelling entries all remain in the row proof. It retains only the
best positive root margin and maximum negative margin deficit.

For selection, only the i<j triangle is considered. A selected edge comes from a
negative EXACT symmetric entry already read by that verifier. Its finite positive
binary64 conductance c is independently checked <=minus that entry by the compact
conversion routine. There is therefore no caller assertion about an edge to trust.
The selected graph merges only different connected components. Exactly n−1 such
merges establishes a spanning tree on all n original coordinates.

This proves the same premises as the preceding two-pass tree verifier: for T equal
to the selected tree Laplacian plus verified root ground g, S+delta*I−T is SDD.
Removing a second exhaustive row scan and a second proof of the very same privately
computed edge values does not weaken the premise. It changes the certificate's
construction architecture; arbitrary externally produced trees still cannot skip
verification through this API.

Stable input ownership remains required. The original operator and context are
hashed before and after the proof. Persistent mutation refuses. This does not
claim to defeat adversarial transient edits or supply a production admission/input
snapshot protocol. The existing interval wrapper binds its actual replacement
intervals and rechecks operator/context identity after perturbation work.

## Online orientation and heterogeneous edge correctness

The private forest maintains a union-find representative that is also the current
oriented-tree root. To join two components, it reroots the smaller component at its
selected edge endpoint, reverses EACH corresponding parent-edge conductance, and
attaches that endpoint to the endpoint in the larger component. Its union-find
representative then becomes the larger oriented root. Component sizes and root
invariants are checked. The final reroot uses the verified positive-margin root;
union-find is no longer relied on and is released before path arrays are allocated.

For each vertex, participation in a smaller-component reroot makes its component
at least double in size. Such participation happens at most floor(log2(n)) times;
the final reroot adds at most n−1 edge reversals. This supplies a simple bounded
pointer-work rationale, not a scalar-update discount. Memoized parent-path walks
subsequently assign each vertex once; explicit state/depth guards refuse cycles.

The independent oracle forces a bridge between two NONROOT endpoints using
edges(0,4)c2,(1,2)c1/2,(1,3)c4,(2,4)c5/4, then grounds vertex3 by2. Exact maximum
root-path resistance is81/20 and n*rmax is81/4=20.25. A wrong rotation of edge
weights can pass unit-conductance tests but fails this control. An eight-node case
forces multiple such reroots, with unequal conductances, nonsymmetry and a deficit.

## Norm and interval conclusions

From exact margins and selected-edge comparisons, S>=T−delta*I. Let
r>=max_i(T^-1)_ii be the outward root-path resistance maximum and b=up(n*r).
As previously reviewed, trace(T^-1)<=b and the grounded tree inverse is entrywise
nonnegative. Thus, when q=up(delta*b)<1,

    ||A^-1||inf <= up(b/down(1-q)).

The implementation pays the actual upward deficit and uses the SAME b in its
denominator; no old trace/square-root premise is silently retained. The complete
interval operator is then bounded with the already reviewed infinity-norm
perturbation inequality K/(1−K*rho). This still supports independently rounded
and nonsymmetric terminal entries. Actual physical accounting remains separate.

## Independent tests and retained evidence

[independent-forest-oracle.py](independent-forest-oracle.py) independently selects
edges using component SETS, builds tiny explicit reference adjacency and computes
Fraction path resistances. It does not reuse the candidate's union-find, pointer
reversal or memoized path algorithm. Dense inverse references are tiny oracle-only
calculations; no oracle output enters the certificate.

103 structural/energy/inverse cases pass: the forced heterogeneous reroot cases
and100 seeded(285) nonsymmetric mixed-sign connected graphs, including actual
small diagonal deficits. Each computed bound encloses the exact selected-tree
bound and the exact original inverse norm. It also remains close to the reference
tree bound, detecting a wrong edge rotation that merely inflates a valid bound.
This closeness comparison is a test regression criterion, not certificate tolerance.

Three complete coupled fixtures (grounded, weak and nonsymmetric) plus all16
terminal-interval corners each supply51 exact full-operator inverse checks:PASS.
Injected persistent operator and context mutations refuse. Instrumentation observes
operator_row calls exactly0..15 once on grid4, and signature inspection confirms
there is no external summary/skip parameter. The four main forest tests independently
pass, observed0.408s; they also check weakref release, failed work retention,
aligned-width accounting and actual synthetic physical dispositions.

[Independent results](independent-forest-results.json) retain exact tree bounds,
reference inverse norms, mutation outcomes and source hashes. All runs use the
established512MiB address-space,20CPU-second,30wall-second and one-thread limits.

## Resource boundary

The proposed contribution ledger is separate from historical primitive Work,
exact kernel/bit envelopes, index visits, byte payloads and measured time/memory.
Counting a verified scalar recurrence according to its maximum aligned width is
a local experiment convention, not an approval to redefine the production cap.
Failed scopes, discarded cycle edges and pointer work remain visible. This
mathematics review does not establish a fit from the proposed contribution total.
A characterization request still requires a resource-eligible implementation and
an explicitly bounded question; none is authorized by this report.

| Reviewed file | SHA256 |
| --- | --- |
| fixture/prototype.py | 0d0c2154e688f365ab16d702cb1552c214544a27d7c7495e9e5832d8c62824da |
| fixture/test_forest.py | b76eca4128833f5ff151348ea328c592172bec4e596a3c282709fbb15edaf843 |
| independent-forest-oracle.py | e0212c62235cfae584451459f1e9a8733a18c1d447f9629279656ffb3a0424b9 |
| independent-forest-results.json | eaeb2660a898f71547ceff4c6710d3edfb8e82bb90d93b06534223e49b5eed63 |

Original attribution, resource qualification and production admission remain
unresolved. No original data was consumed to obtain these synthetic results.

Final accounting follow-through was independently rerun after buffer preallocation,
explicit index-access counts, actual allocated-buffer measurements and failed-run
phase/selected-edge snapshots were added. The mathematical results above remain
unchanged; the table records that actual final rerun rather than an inferred pass.

The final oracle was rerun again after caching the single maximum-path scan,
recording its n reads/comparisons, and exposing witness-hash bytes/input-hash passes.
All103 structural and51 complete interval checks still pass; final table/results
identify source0d0c2154... . These changes do not establish production eligibility.

Accounting-only receipt after the final independent run: small terminal-midpoint
preparation now enters the proposed contribution ledger in addition to its existing
fine floating charges. The representative joined total is42 instead of38, including
four preparation entries. Prototype SHA256 is
738774acdddb70b7e6e88830a450acc19a8c86fa5d8885e66113c67ed7074494.
No numerical operation changed; the coordinator reports all48 tests passing. The
independent result deliberately retains its actual0d0c2154... execution identity.
