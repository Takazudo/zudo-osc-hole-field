# Original operator coercivity certificate: independent review

Author: wsl-coordinator. Separate mathematics/source reviewer:
`/root/certificate_feasibility`. Separate resource/admission reviewer:
`/root/coordination_review`. Both returned PASS on the final source identities in
source-hashes.json. These are real agent technical reviews, not separate signing
organizations or resource-qualified attestations.

## Demonstrated problem and exact proof

Attempt4 supplies original binary64 Af asymmetry. It cannot satisfy the prior
exact-SPD predicate. Neither a roundoff excuse nor approximate reciprocity proves
uniqueness. New method `original-operator-symmetric-part-coercivity-v1` instead
certifies the analysis reference H=(M+M^T)/2 for the complete original joined
operator M. It does not replace any matrix in the selected solve or residual.
The original Af, borderB/D, stored basis, SuperLU/refinement, wire coefficients,
physical identities, original mesh passes, tolerances and one selected RHS remain.

Reference board half-sums are enclosed outward, including subnormals and finite
extremes. Exact cancellation alone is pruned. Reference board LDL/Schur enclosures
and the live-wire coupled reference certificate prove H positive definite. Their
existing block inverse estimate bounds ||H^-1||inf. For all real x,
x^T M x=x^T H x>=lambda_min(H)||x||2^2, so
||M^-1||inf<=sqrt(N)||M^-1||2<=sqrt(N)||H^-1||2<=sqrt(N)||H^-1||inf.
The implementation multiplies by the exact integer ceil(sqrt(N)), rounded outward,
once for total original free+terminal dimension. It rejects mixed original and
reference certificates. Reference Schur certificates have distinct statuses and
are never labeled the Schur of original nonsymmetric M. Original residuals then
bound original selected-solution error. No assumption about globally small skew
or M-matrix signs is used. No extra physical load is solved.

The method is explicitly bound into the compiler packet and checked by executor,
in addition to source/operation identities. Old requests or qualification reports
cannot authorize this method. A fresh clean commit and exact request are required.

## Verification and resource boundary

140 focused executor/resolution/admission/host/worker/containment/supervisor/guard
tests PASS in3.991s. Exact rational independent oracle:25225 finite half-sum pairs,
five-variable joined network with floating KB, strong skew, removed-wire
singularity, invertible operators with indefinite/semidefinite H. Exact joined
||H^-1||inf=7, ||M^-1||inf=22556/5001; existing block estimate12. Independent reviewer
also tested actual source on25000 rational pairs, explicit stored zeros and input
hash preservation. The retained oracle is synthetic only, not original-data evidence.

Unchanged caps:4M live certificate entries,20M arithmetic updates,16M inputnnz;
180s actual shared-guard deadline,2GiB total/1216MiBworker,zerooperation swap,
64MiB aggregate output. Initial exact reference upper structure plus nonzeroB and
conservative D.size is counted before any row dictionary. Crossing4M fails with
the observed prefixcount, not a claimed complete count. No full floating H is
materialized; merging has constant auxiliary storage per row. For original CSC,
transpose CSR is a view, alongside the existing CSR copy. Later fill caps remain.

Resource fit is NOT QUALIFIED. Around1.5M Python row dictionaries alone cost
hundreds of MiB; interval tuples/keys, factors and original arrays add to that.
Storednnz may include explicitzero and does not establish exact upper count.
Previous rootpeak is not available-live-heap evidence. Preflight passing would
not prove allocation/LDL/runtime or complete pipeline feasibility.

Both reviewers endorse one freshly admitted FULL conditional qualification under
unchanged limits: the first new question is whether initial structure fits4M;
if it passes, the code continues the full existing pipeline. This is NOT a count-
only mode. Kernel limits/watchdogs and existing single-use failure accounting,
negative retention and owned cleanup cover possible allocation/LDL/time failure.
No new cleanup/accounting defect was identified. Failure consumes one diagnostic
and requires a diagnosed change before another request; no automatic retry.
