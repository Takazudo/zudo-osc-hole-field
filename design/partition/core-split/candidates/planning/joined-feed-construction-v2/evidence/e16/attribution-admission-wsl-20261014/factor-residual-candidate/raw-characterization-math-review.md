# Independent raw-characterization module review

Reviewer `/root/math_review`, separate from the resource-module author and
admission integrator.2026-10-15 JST. Scope: attribution_characterization.py and
its direct metadata/transport contracts. Only newly generated synthetic pickles
were decoded. No retained original input, signer, grant or campaign request was
opened or consumed. This is NOT a review of live admission or a permit to execute.

**PASS for the module's bounded metadata question, integer formulas, sequential
operator lifetime and inherited output/deadline semantics.** COMPLETE remains
characterization completion; every reported result remains NOT_QUALIFIED.

## Exact question and formulas

For one decoded operator let N be its declared node count, f and i the actual
stored data-array lengths of Kg_face and Kg_inner, b the sum of max(tap_count−1,0)
over its barrel records, and s_j each listed terminal's support-array length.
The module reports

    K_upper=f+i+4*b,
    R_upper=K_upper+sum_j s_j²,
    largest_outer_entries=max_j s_j².

This follows the literal constructor source: each adjacent barrel interval emits
four coordinate triples, and an unfiltered terminal support of length s emits
an outer product of at most s² entries. Stored zeros, duplicate coordinates,
overlapping supports or held-node filtering cannot justify lowering the bound
without inspecting more data. Descriptor-only extraction deliberately reads
stored array sizes instead of .nnz, which can index indptr values.

The named byte allowances match the separately reviewed construction arithmetic:

    coordinate conversion arrays:80*R_upper+8*(N+1),
    active outer/division float buffers:16*max_j s_j²,
    dense B/D:8*N*t+8*t².

All arithmetic uses bounded-size Python integers from validated descriptors.
The output is an envelope for these NAMED arrays only. It excludes complete
operator object graphs, class-matrix construction, masks, native conversion
workspace, allocator overhead, retained physical-pipeline state and other required
terms. The sum is not a complete heap proof or an observed memory peak.

EXCEEDS_RAW_BOUND means this conservative metadata gate is not established. It
is not proof that actual construction must exceed the limit: filtering and
coalescing can make actual tuples smaller. Conversely WITHIN_RAW_BOUND proves
only this raw upper-bound comparison; it does not qualify memory, the numerical
certificate, guard timing or physical attribution. The16M raw ceiling is named
as a separate conservative construction bound, not silently substituted for the
existing stored-input quota.

## Access and binding scope

The module accepts exactly KA and KB binding records. Each bounded canonical
record is hashed into its output; paths themselves are not emitted in component
rows. Existing transport verifies supplied compressed/stored bytes before
interpretation, enforces decoded-byte limits, checks optional decoded identity,
and rechecks the same open file descriptor and content afterward.

This is not authentication against the independent original request. The caller
must establish that the supplied bindings are the approved original bindings
inside the existing guard. Trusted pickle decoding interprets the WHOLE pickle
and reconstructs its object graph; it is not metadata-only IO or safe handling of
untrusted pickle. Only the subsequent descriptor traversal avoids numerical
coefficient, support-weight and node-index reads. Pickle/object allocations still
need the existing enforced worker-memory boundary.

Source hashes cover the module and its direct helper files before and after the
operation. They are source-file identities, not proof of admission, a signature
or a replacement for independently frozen executing sources. No construction,
solve, mesh replay, alternative physical RHS or numerical qualification occurs.

## Lifetime, deadlines and receipts

The caller's Budget instance is reused, including its original started/deadline
and output accounting. No new180-second clock is created. Descriptor checkpoints
are cumulative across both boards with an explicit16M checkpoint ceiling. Decode,
source hashing, output and finalization use the same cooperative budget; an outer
guard must still enforce the process deadline and memory contract.

KA is decoded, reduced to plain integer/tuple metadata, released and garbage-
collected before KB is decoded. _one converts ordinary exception text to bounded
strings instead of retaining traceback frames holding the decoded operator.
No original arrays are copied into the component report. Garbage collection is
not a claim that allocator RSS returns to zero or that unpickling is byte-only.

One contract wording finding was fixed during review: early budget/binding/source
checks and Output construction occur before module-owned failure handling. The
docstring now accurately assigns those early failures to the outer authenticated
host lifecycle. After Output exists, failures produce its INCOMPLETE receipt and
retain a partial stream rather than a complete result. This review does not claim
that the module alone creates a receipt for every possible early failure.

Successful output uses the existing atomic terminal-receipt protocol and binds
component bytes. It explicitly retains electrical_acceptance=false,
whole_board_acceptance=false and adopted=false. NOT_QUALIFIED appears in every
component and the summary. An excessive raw bound may therefore be a COMPLETE
characterization result without being a successful preflight or qualification.

## Independent evidence

[independent-raw-characterization-oracle.py](independent-raw-characterization-oracle.py)
creates every input pickle in a fresh temporary directory and uses descriptor
sentinels which throw on array conversion, numerical indexing or value iteration.
It independently verifies:

- A two-board control with R103/max(s²)49/named bytes9328 and an excessive control
  with R16,008,003/max(s²)16,008,001/named bytes1,536,768,320.
- An extreme metadata-only case R2,048,000,032,000,000 remains bounded output,
  reports EXCEEDS_RAW_BOUND and does not allocate the represented numerical arrays.
- Weakrefs for both CSR descriptors, their arrays and every support array are dead
  before the next decode; the original Budget clock remains unchanged.
- Binding-record digests, complete component-stream SHA256 and checkpoint totals
  agree with independently calculated values.
- A bad KB digest, changed source identity and timeout after metadata each leave
  INCOMPLETE output, no published component stream and matching partial hashes.

[Retained results](independent-raw-characterization-results.json) identify the
actual source hashes. The five author tests were independently rerun:PASS,
observed0.052s; they additionally exercise output/checkpoint caps, cancellation,
metadata failure cleanup and exclusion of unrequested input bindings. All tests
use synthetic descriptors, the established512MiB/20CPU-second/30wall-second bounds
and no original input.

## Decision boundary

This characterization can answer which raw-construction envelope must be developed
next. An excessive upper bound blocks the CURRENT metadata-only admission gate;
a within-bound answer permits further complete-envelope analysis. Neither answer
authorizes a qualification or implies an intervention disposition. Live request
kind, exact delegation/grant binding, accounting, guard entry and terminal cleanup
remain a separate review. This report approves none of those outward actions.

| Reviewed file | SHA256 |
| --- | --- |
| attribution_characterization.py | 1b1d2226bd6702a86153cb3e1281d22e663f96a3e0a8d3fedc0dcb9cc4a8aa2d |
| attribution_preallocation.py | 55d331ef8b535f849f8aab84f5221a570df0d68351553a450b700b8253fcc268 |
| attribution_transport.py | c122e14552447ee495f91840100f9e0dc703bd7cda6ce64d9cb726a246ca0d50 |
| test_attribution_characterization.py | 0a6da862bf43c899b56eff073e95b223ce513faad1702012b1fc97dfc079b930 |
| independent-raw-characterization-oracle.py | b1ee358a6aaf1ee032cc4c46cc9217e8484225d547c7e23c264ea41045847536 |
| independent-raw-characterization-results.json | 05c2fddae3000c0d874259b9ccca0f92fafc204c0094797c4a3ff4d1c7828599 |
