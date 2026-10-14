# Independent numerical and accounting review

Verdict: PASS for the inspected source implementation and bounded synthetic validation, with the production limitations below. This review is independent of the implementation author. It does not qualify production resources, grant execution authority, or certify any real matrix. No retained production artifact was decoded and no real numerical unit or native oracle was executed by this reviewer.

## Reviewed implementation

Read the predecessor reconstruction evidence, original adapter/solver/reporter, new serialized executor, sparse interval checker, robustness enclosure, transport, lifecycle and supervisor sources and relevant tests. The original `finite_adapter.py`, `finite_solve.py`, `finite_units.py`, `resistance_attribution.py`, `numerical_unit_guard.py` and fixture bridge retain their predecessor hashes.

The driver uses the original selected-RHS signs, terminal ordering, SuperLU settings and extended refinement conventions. It discards loaded u0/g before selected reconstruction. Original Assembly numbering, ring-collapse order, all support mappings and complete geometric stiffness are recovered and checked. Copper is streamed by original union tile and consecutive barrel interval; shared member IDs are provenance. Distributed termination stamps remain whole, and each live wire bulk is charged once. The removed-wire fixture retains both end terminations. Partition, nodal currents, free/global KCL, individual held reactions, interface/wire balance, class energies and selected load work must pass before publication.

Maximum absolute global nodal injection remains the current normalization. Class-energy errors use total selected load work, matching the predecessor reporter. The retained comparison reads the original unit-current projection with its selected pad and input bindings, using the unchanged 1e-8 reduction-versus-monolithic comparison criterion. It does not substitute simultaneous-load watts.

## Uniqueness and numerical-error method

`attribution_uniqueness.py` treats finite binary64 sparse coefficients as exact singleton real intervals and rounds every scalar arithmetic result outward with `nextafter`. Positive pivot lower bounds in sparse interval LDL establish positive definiteness by induction. Interval ambiguity, nonfinite arithmetic, exact asymmetry, sparse-fill exhaustion and arithmetic-cap exhaustion fail closed. No production matrix is densified. Successful SuperLU factorization, graph connectivity and a matching hash are not used as proofs.

Board-local bordered elimination retains an interval enclosure of the exact terminal Schur complement, rather than treating the retained approximate basis as exact. Combining those enclosures with the original stored wire conductance and certifying the coupled interval matrix establishes uniqueness of the original assembled free-block network if all gates succeed. This avoids the otherwise missing error bound between the retained reduced matrix and the exact Schur complement. The actually stored reduced coupling is also independently checked.

The checker additionally bounds the inverse infinity norm. For A = L D L^T, comparison forward/backward recurrences bound the infinity norms of L^-1 and L^-T, and the minimum positive pivot lower bound bounds D^-1. Retained factor entries share the same live-entry cap as elimination fill.

For the complete free matrix H, A = diag(A_KA, A_KB), and exact coupled Schur S, block factorization gives the conservative bound

```
||H^-1||inf <= (1 + max_b c_b ||B_b||inf)
              * max(c_KA, c_KB, c_S)
              * (1 + max_b c_b ||B_b^T||inf),
```

where each c bounds its corresponding inverse norm. Symmetry makes the same board inverse bound applicable to the transposed factor. Every product and sum is rounded upward.

`attribution_resolution.py` evaluates the residual of the original Af/B/D/wire free operator at the reconstructed field with outward arithmetic. Multiplying its residual bound by the full inverse bound bounds the voltage error without another load solve. Long-double field values are enclosed before binary64 interval calculations. Held potentials remain exact zero. Local component quadratic forms and source reaction functionals are then enclosed without pruning zero/small components or clamping uncertain negative lower bounds. The Stage C screen supports the mechanism only when the barrel-share interval is entirely at least 10% and the TP990026 reaction interval excludes zero. A resolved adverse share rejects it; overlapping/unresolved intervals remain INCONCLUSIVE.

These are proofs about exact stored operators and explicitly evaluated functionals, conditional on the authenticated original artifacts and construction bindings. They are not physical-model validation or a claim of forward accuracy based solely on a residual threshold.

## Findings and closure

- An early driver normalized each class-energy error by that class's energy. It now uses total selected work, preserving the predecessor criterion.
- Initial serialized fixtures omitted barrels and removed-wire coverage. The final fixtures exercise consecutive original barrel intervals, complete sheet coverage, and a connected two-wire/one-removed state through the actual serialization/accounting pipeline.
- An initial certificate cap conflated full CSR nnz and upper-triangle/fill entries. Separate input, retained-factor/fill and update caps now expose those distinct resources. They remain unqualified for real matrices.
- The initial resource description understated original Assembly replay and retained array lifetimes. Assembly makes eight mesh passes and accounting a ninth; its CSR construction retains value arrays from earlier decoded chunks. These costs must be included in production qualification.
- Success-terminal serialization initially could consume failure-receipt headroom. The final transport retains a separate failure reserve and revokes late successes.
- Supervisor log-finalization or worker-marker-rename errors initially escaped before a negative terminal receipt. The final supervisor records these failures and attempts a truthful terminal receipt; focused fault tests pass.
- A residual-only nonzero-reaction screen was not sufficient. The final source implements the inverse/residual/functional enclosures above; no residual-only threshold is relabeled as forward-error evidence.

No outstanding numerical-method or accounting defect was found in the final inspected source scope. Exact symmetry remains an explicit in-run requirement: a production matrix with even tiny stored skew is refused, not silently symmetrized. Likewise, conservative interval widening or overflow can refuse a physically reasonable model. These are real qualification gates, not evidence of successful production operation.

## Independent validation

From the E16 source directory:

```sh
/home/takazudo/.cache/zudo-e16-numerical-venv/bin/python -m unittest test_attribution_interval_oracle test_attribution_resolution test_attribution_executor test_attribution_lifecycle test_attribution_supervisor test_attribution_reconstruction test_resistance_attribution
```

Final result: **119 tests PASS**, 5.306 seconds. This is the reviewer's focused run, not the full E16 suite count. It supersedes the earlier 118-test review run.

The final supervisor delta adds an actual synthetic packet through the single-use lifecycle, numerical pipeline, component output and supervisor terminal validation. Its consumed claim is included in the supervisor inventory. The subprocess uses a fixed 384-MiB address-space cap to accommodate numerical-library imports, 2 CPU seconds, 4 MiB per file and 64 descriptors; the original small geometry/node ceilings remain unchanged. This is synthetic subprocess validation, not a real cgroup or production-resource test.

The reviewer added `test_attribution_interval_oracle.py` with independent Fraction Gaussian-elimination oracles: 30 random bounded integer positive-definite matrices check exact inverse-norm and bordered-Schur containment; a separate coupled network checks the full inverse bound, selected residual and resulting solution-error bound; subnormal arithmetic and long-double conversion are checked against exact rationals; local energy and held-reaction enclosures include independently evaluated perturbation corners. These tiny tests validate implementation logic, not production evidence or fit.

An earlier standalone reviewer experiment checked 100 additional 5-free/2-terminal exact rational Schur cases successfully. The retained four oracle tests above are the durable regression coverage and are included in the 119-test count.

## Reviewed hashes

| File | SHA-256 |
| --- | --- |
| attribution_uniqueness.py | c913e12e00d9a583631ef826e087efc6fb1cd20b769fe171d120d064b7df0b3c |
| attribution_resolution.py | 02b993fff01a5c848ab751f7cc84a10f61a8ac855bcbeb6398c1df549cabc91e |
| attribution_executor.py | 45033ebe5b5f7a366e31e0c5a6fd01aaaadacc7a13613899354a17c188a587e3 |
| attribution_transport.py | c122e14552447ee495f91840100f9e0dc703bd7cda6ce64d9cb726a246ca0d50 |
| attribution_lifecycle.py | 639b31dbddbee056585ba4af8205e191ff73c4c10a2b70f3a03b8ad78bb58343 |
| attribution_supervisor.py | cd27b2abde547a3ed3d1bb1fa26587d16508fa078b2540c0810f565291671d8c |
| test_attribution_executor.py | 3abf76da3f7917c3128b3236713bdb39f7bc4ce984d7ddebc9071a18844226be |
| test_attribution_resolution.py | 3608fb4c44bcff27d795038ff37e28f2cc574492bc235b33669921f112da38ce |
| test_attribution_interval_oracle.py | 7e9ebb092490a1768d67c7d740ab4de123fabef51af283a913828c0f7b31ddd5 |
| test_attribution_lifecycle.py | f2e7b38321193500fad66a65a0ba4a97a0075753599d065cf5299a896de52d60 |
| test_attribution_supervisor.py | 9255fbfa9f9c4e9cd10f5d1e2657205a99dc54fbeab3ed9ada44a386ef977b6f |

## Production limits

Exact real-matrix certificate evidence: **NOT RUN**. Combined 180-second/2-GiB/zero-swap/64-MiB qualification: **NOT QUALIFIED**. Interval factor storage, residual and functional passes, nine mesh decodes per board, original Assembly allocations, output hashing and supervisor cleanup all require combined qualification; tiny timings and historical individual receipts are insufficient.

The host authority/current-exclusive-reservation verifier and production supervisor/lifecycle integration remain disabled. Source-fixture authority objects are not production grants. There is no complete executable production request, so its digest must remain null. This review creates no reservation or authorization. Stage C on the actual selected observation remains **NOT RUN**. All electrical acceptance, whole-board acceptance and adoption flags remain false.

## Final whitespace and handoff closure

Independently inspected the final supervisor diff against commit `240a14b2`. The only change removes one additional EOF newline; byte comparison confirms every other byte is identical. The final `attribution_supervisor.py` SHA-256 is **b6a030b3e3011fe5df8601a817c2fbf092ee69711b8ee820b14eca45559d36e7**, superseding the supervisor hash in the table above. No executable behavior changed, so the 119-test independent result remains applicable; the implementation author's separate full E16 run is reported in the final check summary rather than substituted for independent review.

Read the final README, resource plan and resource review. They accurately separate implemented numerical/source operations from the disabled host verifier/provisioning/worker-command/cleanup boundary, retain null production request identity, disclose exact-symmetry/fill/interval-resolution gates and the full repeated-pass costs, and report real Stage C and resource qualification as unperformed. No additional numerical/accounting source gap was identified from those handoff documents. Their preservation hash inventories are the author's retained audit evidence, not new artifact-decoding work by this reviewer.
