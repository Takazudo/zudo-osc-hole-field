# Fixed analysis-only ordering after actual arithmetic exhaustion

Attempt6 reached20M interval updates during KA, with no certificate completed.
One deterministic RCM candidate is now prescribed for board analysis only.
Graph is the Boolean union of original stored nonzero structure and its transpose:
a conservative symmetric structural superset, including some skew-cancelled edges.
RCM is run once; there is no search, fallback or automatic alternate-order retry.
Type, length, range and bijection are validated before indexing. The int64
contiguous permutation is hashed, with method/graph/order metadata retained in
successful certificates and bounded post-ordering ValueError failure diagnostics.
Original matrix hash remains the binding; no permuted hash substitutes for it.

For free-node permutationP, H'=P H P^T and B'=P B, with D and terminal order
unchanged. Positivity, exact borderedSchur and inverse infinity norm are invariant.
The global coercivity bound continues to apply to original M. Owned analysis
copies alone are permuted/sorted. OriginalAf, B, retainedbasis, physicalRHS,
SuperLU MMD_AT_PLUS_A, refinement/residual calculations, tolerances and original
mesh/accounting passes remain unchanged. Interval results can vary by ordering;
eager/frontier bit-equality is asserted only under the SAME permutation.

Independent `/root/certificate_feasibility` rational review: nontrivial
permutation[2,3,1,0] preserves exact reference/originalSchurs and ten-variablejoined
inverse infinity norms, with groundedKA/floatingKB and livewires. Exactoriginal
inverse norm1488583/444530; reference303/85. Incorrectly leavingB unpermuted is
caught by the oracle. Actual independent oracle0.061s under512MiBAS/20CPU/30wall
bounds. Permanent Fraction regression tests retain the essential proof cases.

Ignored prototype`__inbox/e16-frontier/ordering.py` used only tinysynthetic matrices,
512MiBAS/20CPU/30wall,oneprocess/BLASthread,<64KiBoutput; actual0.294s. Updates:
star25:2601→29;star49:19601→53;grid25:295→345(WORSE);grid64:1968→1772;
scrambledgrid64:2383→1756;grid144:10088→7646. This is no universal improvement
claim. The standalone process maxrss field includes process startup/highwater
history and is not task-local cgroup qualification; do not substitute it for
real aggregate observations. Prototype is ignored, meaningfultests are committed.

Resource accounting remains unchanged4Mliveintervalentries/factors,20Mupdates,
16Minputnnz,1216MiBworker/2GiBaggregate,zero swap,180seconds,64MiBoutput.
Account overlappingBoolean graph/transpose/union,RCM scratch,raw/int64permutation,
seenarray, originalAf, original/orderedCSR,row-permuteintermediate/finalcolumncopy,
sort scratch, reorderedtranspose anddenseBcopy. Graph/seenare released before
sparsecopy phase, but originalCSR and reorderedcopies overlap during assignment.
Longer original-input lifetime and orderedtranspose/B copies are real costs, not
available headroom inferred from a previouspeak. Kernel limits and deadlines
remain active; failure still consumes the one claimed diagnostic with owned
cleanup and terminalaccounting. No extra physical RHS or fullbaseline is introduced.

Newrequestfield`certificate_ordering=rcm-original-structural-union-v1` is exactly
compiled, executorchecked and operation/sourcebound. Old sealed packets/reports
cannot reinterpretthisselection.170focusedtestsPASS5.022s includingordering,
Fractionoracles, lifetime/cap/invalidbijection/floatingKB/disconnection/worsegrid,
oldpacketrefusal, admission/host/supervisor/worker/lifecycle andboundarychecks;
circuit/diffPASS. The boundaryfixture owns its mocked descriptorenvironment now.

Independent final source/mathreview `/root/certificate_feasibility`:PASS;
separate source/resource/admissionreview `/root/coordination_review`:PASS on the
sourceidentities in source-hashes.json. Neither reviewer accessedoriginaldata,
keys or grants, changedsource, or issued a signingattestation. No new unbounded
cleanup/accounting path identified. One fresh FULLqualification technically
eligible aftercleancommit/exactpacketreview/genuinesignatures/liveadmission.
Original performance, fill, memory and completepipeline remain NOT_QUALIFIED.
